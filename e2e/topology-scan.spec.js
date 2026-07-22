/**
 * 按 docs/route-architecture-topology.md §2 顺序做前端路由全量 E2E。
 * 流程：自动创建账号 → 登录一次 → 共享会话扫完 2.1→2.5
 */
import { test, expect } from '@playwright/test'
import { scanTopologyRoute } from './helpers/scan-page.js'
import { provisionE2EUser } from './helpers/provision.js'
import { recordPageScan } from './helpers/scan-report.js'
import { attachPageMonitor } from './helpers/page-monitor.js'
import {
  switchAuthTab,
  fillNaiveInput,
  tryLogin,
  discoverGameIds,
} from './helpers/platform.js'
import {
  TOPOLOGY_DOC,
  SECTION_21_LANDING,
  SECTION_22_ACCOUNT,
  SECTION_23_CONTENT,
  SECTION_24_GAMES_STATIC,
  SECTION_25_ADMIN,
  expandGameRoutes,
} from './topology/routes.js'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'

const BOUNDARY_CASES = [
  { name: '空字符串', value: '' },
  { name: '超长字符串', value: 'A'.repeat(2000) },
  { name: 'XSS', value: '<script>alert(1)</script>' },
  { name: 'SQL', value: "' OR '1'='1" },
]

test.describe.configure({ mode: 'serial' })

test.describe(`拓扑扫描 · ${TOPOLOGY_DOC}`, () => {
  /** @type {import('@playwright/test').BrowserContext | null} */
  let context = null
  /** @type {import('@playwright/test').Page | null} */
  let page = null
  /** @type {Record<string, any> | null} */
  let provisioned = null
  /** @type {string[]} */
  let gameIds = []

  test.beforeAll(async ({ browser, request }) => {
    const res = await request.get(BASE_URL, { failOnStatusCode: false, timeout: 10_000 }).catch(() => null)
    if (!res) {
      throw new Error(`无法连接 ${BASE_URL}。请先启动 frontend(3000) + backend(5000)。`)
    }

    provisioned = provisionE2EUser({ admin: true, prefix: 'e2e' })
    if (!provisioned?.ok) throw new Error(`创建账号失败: ${JSON.stringify(provisioned)}`)

    process.env.E2E_USER = provisioned.account
    process.env.E2E_PASSWORD = provisioned.password

    context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL })
    page = await context.newPage()

    const loggedIn = await tryLogin(page)
    if (!loggedIn) throw new Error(`新账号登录失败: ${provisioned.account}`)

    gameIds = await discoverGameIds(page, { limit: 2 })
    console.log(
      `[e2e] provisioned=${provisioned.account} admin=${provisioned.is_admin} games=${gameIds.join(',') || '(none)'}`,
    )
  })

  test.afterAll(async () => {
    await context?.close()
  })

  test('0. 创建账号并登录（覆盖完整拓扑）', async () => {
    expect(provisioned?.account).toBeTruthy()
    expect(page).toBeTruthy()

    const monitor = attachPageMonitor(page, 'provision')
    await page.goto('/home', { waitUntil: 'domcontentloaded' })
    await recordPageScan(page, {
      route: '0 /provision+login',
      title: '0 创建账号并登录',
      monitor,
      brokenLinks: [],
      notes: [
        `username=${provisioned.username}`,
        `email=${provisioned.email}`,
        `user_id=${provisioned.user_id}`,
        `is_admin=${provisioned.is_admin}`,
        `via=${provisioned.via}`,
        `games=${gameIds.join(',')}`,
        '共享 BrowserContext，避免重复登录触发限流',
      ],
    })
  })

  // ───────── §2.1 落地 / 公共 ─────────
  for (const route of SECTION_21_LANDING) {
    test(`2.1 ${route.path} · ${route.name}`, async () => {
      await scanTopologyRoute(page, route, { softBrokenLinks: true })
    })
  }

  // ───────── §2.2 账号 / 认证 ─────────
  test('2.2 /auth · 登录注册表单 + 边界输入', async () => {
    await scanTopologyRoute(page, { path: '/auth', name: 'AuthDeep', section: '2.2', auth: 'public' }, {
      softBrokenLinks: true,
      deep: async (p, _m, notes) => {
        await p.waitForSelector('[role="dialog"]', { timeout: 20_000 })
        await switchAuthTab(p, 'login')

        // 用刚创建的账号做一次 UI 登录探测
        await fillNaiveInput(p, '用户名 / 手机号 / 邮箱', provisioned.account)
        await p.locator('[role="dialog"] input[type="password"]').first().fill(provisioned.password)
        const okLoginP = p.waitForResponse(
          (r) => r.url().includes('/api/auth/login') && r.request().method() === 'POST',
          { timeout: 12_000 },
        ).catch(() => null)
        await p.getByRole('button', { name: '确认进入系统' }).click()
        const okLogin = await okLoginP
        if (okLogin) notes.push(`新账号 UI 登录 API: ${okLogin.status()}`)
        await p.waitForTimeout(800)

        await p.goto('/auth', { waitUntil: 'domcontentloaded' })
        await p.waitForSelector('[role="dialog"]', { timeout: 15_000 })
        await switchAuthTab(p, 'login')
        await fillNaiveInput(p, '用户名 / 手机号 / 邮箱', 'e2e_probe_user')
        await p.locator('[role="dialog"] input[type="password"]').first().fill('WrongPass!123')
        const badLoginP = p.waitForResponse(
          (r) => r.url().includes('/api/auth/login') && r.request().method() === 'POST',
          { timeout: 12_000 },
        ).catch(() => null)
        await p.getByRole('button', { name: '确认进入系统' }).click()
        const badLogin = await badLoginP
        if (badLogin) {
          notes.push(`错误密码登录 API: ${badLogin.status()}`)
          expect([200, 400, 401, 403, 422, 429]).toContain(badLogin.status())
        }

        for (const c of BOUNDARY_CASES) {
          await fillNaiveInput(p, '用户名 / 手机号 / 邮箱', c.value || ' ')
          await p.locator('[role="dialog"] input[type="password"]').first().fill(c.value || 'x')
          await p.getByRole('button', { name: '确认进入系统' }).click()
          await p.waitForTimeout(200)
          notes.push(`登录边界「${c.name}」`)
        }

        await switchAuthTab(p, 'register')
        await expect(p.getByPlaceholder('显示名称，必填')).toBeVisible({ timeout: 10_000 })
        await fillNaiveInput(p, '显示名称，必填', 'e2e_nick')
        await fillNaiveInput(p, '可选，用于登录', `e2e_${Date.now()}`)
        await fillNaiveInput(p, '必填，需验证', 'not-an-email')
        await fillNaiveInput(p, '设置登录密码', 'short')
        const regRespP = p.waitForResponse(
          (r) => r.url().includes('/api/auth/register') && r.request().method() === 'POST',
          { timeout: 12_000 },
        ).catch(() => null)
        await p.getByRole('button', { name: /提交注册申请/ }).click()
        const regResp = await regRespP
        if (regResp) {
          notes.push(`注册 API: ${regResp.status()}`)
          expect([200, 201, 400, 409, 422, 429, 500]).toContain(regResp.status())
        }

        // 边界测完后重新 API 登录，恢复会话
        process.env.E2E_USER = provisioned.account
        process.env.E2E_PASSWORD = provisioned.password
        await tryLogin(p)
      },
    })
  })

  for (const route of SECTION_22_ACCOUNT.filter((r) => r.path !== '/auth')) {
    test(`2.2 ${route.path} · ${route.name}`, async () => {
      await scanTopologyRoute(page, route, { softBrokenLinks: true })
    })
  }

  // ───────── §2.3 公告 / Wiki / 用户 ─────────
  for (const route of SECTION_23_CONTENT) {
    test(`2.3 ${route.path} · ${route.name}`, async () => {
      await scanTopologyRoute(page, route, { softBrokenLinks: true })
    })
  }

  test('2.3 动态详情 · bulletin / wiki / users', async () => {
    const picks = []

    await page.goto('/bulletin', { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    const bulletinHref = await page.locator('a[href*="/bulletin/"]').evaluateAll((as) => {
      const hit = as.map((a) => a.getAttribute('href')).find((h) => h && /\/bulletin\/\d+/.test(h))
      return hit || null
    })
    if (bulletinHref) picks.push({ path: bulletinHref, name: 'BulletinDetail', section: '2.3', auth: 'public' })

    await page.goto('/wiki', { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    const wikiHref = await page.locator('a[href*="/wiki/"]').evaluateAll((as) => {
      const hit = as.map((a) => a.getAttribute('href')).find((h) => h && /\/wiki\/[^/]+/.test(h) && h !== '/wiki')
      return hit || null
    })
    if (wikiHref) picks.push({ path: wikiHref, name: 'WikiArticle', section: '2.3', auth: 'public' })

    await page.goto('/users', { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    const userHref = await page.locator('a[href*="/users/"]').evaluateAll((as) => {
      const hit = as.map((a) => a.getAttribute('href')).find((h) => h && /\/users\/\d+/.test(h))
      return hit || null
    })
    if (userHref) picks.push({ path: userHref, name: 'UserProfile', section: '2.3', auth: 'public' })

    for (const route of picks) {
      await scanTopologyRoute(page, route, { softBrokenLinks: true })
    }
  })

  // ───────── §2.4 训练 / 赛事 ─────────
  for (const route of SECTION_24_GAMES_STATIC) {
    test(`2.4 ${route.path} · ${route.name}`, async () => {
      await scanTopologyRoute(page, route, { softBrokenLinks: true })
    })
  }

  test('2.4 动态赛事路由 · detail/challenges/scoreboard/teams', async () => {
    if (!gameIds.length) gameIds = await discoverGameIds(page, { limit: 2 })
    test.skip(!gameIds.length, '无可用赛事 ID')

    for (const gid of gameIds) {
      for (const route of expandGameRoutes(gid)) {
        await scanTopologyRoute(page, route, {
          softBrokenLinks: true,
          deep: route.name === 'GameChallenges'
            ? async (p, _m, notes) => {
                if (/\/auth/.test(p.url())) {
                  notes.push('challenges 需登录，已跳过深度交互')
                  return
                }
                await p.waitForSelector('.tree-item, .tree-empty, .challenge-workspace', { timeout: 25_000 }).catch(() => null)
                const cats = p.locator('.tree-cat')
                const catN = await cats.count()
                for (let c = 0; c < Math.min(catN, 6); c++) {
                  await cats.nth(c).click().catch(() => {})
                  await p.waitForTimeout(150)
                }
                const items = p.locator('.tree-item:visible')
                const n = await items.count()
                notes.push(`题目树可见 ${n} 项`)
                for (let i = 0; i < Math.min(n, 8); i++) {
                  const item = items.nth(i)
                  if (!(await item.isVisible().catch(() => false))) continue
                  await item.click({ timeout: 5_000 }).catch(() => {})
                  await p.waitForTimeout(400)
                  const startBtn = p.getByRole('button', { name: /开启容器|启动容器|重新启动/ })
                  if (await startBtn.count()) {
                    const btn = startBtn.first()
                    if (!(await btn.isDisabled().catch(() => true))) {
                      const respP = p.waitForResponse(
                        (r) => /\/api\/(container|instances|challenges)/.test(r.url()) && r.request().method() === 'POST',
                        { timeout: 15_000 },
                      ).catch(() => null)
                      await btn.click()
                      const resp = await respP
                      if (resp) {
                        notes.push(`启动 API ${resp.status()}`)
                        expect(resp.status()).toBeLessThan(500)
                      }
                      break
                    }
                  }
                }
              }
            : route.name === 'GameScoreboard'
              ? async (p, _m, notes) => {
                  const panel = p.locator('.scoreboard-panel, .scoreboard-table, .empty-state, .scoreboard-layout')
                  await expect(panel.first()).toBeVisible({ timeout: 25_000 })
                  const curveBtn = p.getByRole('button', { name: /积分曲线/ })
                  if (await curveBtn.count()) {
                    await curveBtn.first().click()
                    await p.waitForTimeout(800)
                    const curve = p.locator('.score-curve')
                    if (await curve.count()) {
                      notes.push(`曲线 canvas=${await curve.locator('canvas').count()}`)
                    }
                  }
                }
              : undefined,
        })
      }
    }
  })

  // ───────── §2.5 管理后台 ─────────
  for (const route of SECTION_25_ADMIN) {
    test(`2.5 ${route.path} · ${route.name}`, async () => {
      await scanTopologyRoute(page, route, { softBrokenLinks: true })
    })
  }

  test('汇总 · 拓扑扫描完成', async () => {
    expect(provisioned?.account).toBeTruthy()
    console.log(`[e2e] done as ${provisioned.account}`)
  })
})
