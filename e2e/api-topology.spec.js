/**
 * 按路由拓扑探测前后端 API 契约：主路径可达、已下线路径 410、误用路径不成功。
 */
import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { provisionE2EUser } from './helpers/provision.js'
import { tryLogin, discoverGameIds } from './helpers/platform.js'
import { API_PROBES, statusMatchesExpect } from './topology/api-catalog.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'
const REPORT_DIR = path.join(__dirname, 'e2e-report')
const REPORT_FILE = path.join(REPORT_DIR, 'api-topology-report.json')

// 共享登录会话；单条失败不阻断后续探测
test.describe.configure({ mode: 'serial' })

test.describe('API 拓扑契约 · docs/route-architecture-topology.md', () => {
  /** @type {import('@playwright/test').BrowserContext | null} */
  let context = null
  /** @type {import('@playwright/test').Page | null} */
  let page = null
  /** @type {Record<string, any> | null} */
  let provisioned = null
  /** @type {{ gameId: string|null, challengeId: string|null }} */
  let ctx = { gameId: null, challengeId: null }
  /** @type {Array<Record<string, any>>} */
  const results = []

  test.beforeAll(async ({ browser, request }) => {
    const res = await request.get(BASE_URL, { failOnStatusCode: false, timeout: 10_000 }).catch(() => null)
    if (!res) throw new Error(`无法连接 ${BASE_URL}。请先启动 frontend + backend。`)

    provisioned = provisionE2EUser({ admin: true, prefix: 'e2eapi' })
    if (!provisioned?.ok) throw new Error(`创建账号失败: ${JSON.stringify(provisioned)}`)

    process.env.E2E_USER = provisioned.account
    process.env.E2E_PASSWORD = provisioned.password

    context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL })
    page = await context.newPage()

    const loggedIn = await tryLogin(page)
    if (!loggedIn) throw new Error(`登录失败: ${provisioned.account}`)

    const gameIds = await discoverGameIds(page, { limit: 3 })
    ctx.gameId = gameIds[0] || process.env.E2E_GAME_ID || null

    if (ctx.gameId) {
      const pickChallengeId = (body) => {
        const list =
          body?.data?.challenges ||
          body?.data?.items ||
          body?.data ||
          body?.challenges ||
          body?.items ||
          []
        const arr = Array.isArray(list) ? list : []
        const first = arr.find((c) => c?.id != null)
        return first ? String(first.id) : null
      }

      // 管理端列表优先（未参赛时选手列表可能为空）
      const adminList = await page.request.get(
        `/api/admin/challenges/games/${ctx.gameId}/challenges-list`,
        { failOnStatusCode: false },
      )
      if (adminList.ok()) {
        ctx.challengeId = pickChallengeId(await adminList.json().catch(() => ({})))
      }
      if (!ctx.challengeId) {
        const chalRes = await page.request.get(`/api/challenges/games/${ctx.gameId}/challenges`, {
          failOnStatusCode: false,
        })
        if (chalRes.ok()) {
          ctx.challengeId = pickChallengeId(await chalRes.json().catch(() => ({})))
        }
      }
      // 换一场有题的比赛
      if (!ctx.challengeId && gameIds.length > 1) {
        for (const gid of gameIds.slice(1)) {
          const r = await page.request.get(`/api/admin/challenges/games/${gid}/challenges-list`, {
            failOnStatusCode: false,
          })
          if (!r.ok()) continue
          const cid = pickChallengeId(await r.json().catch(() => ({})))
          if (cid) {
            ctx.gameId = gid
            ctx.challengeId = cid
            break
          }
        }
      }
    }

    console.log(
      `[api-topology] user=${provisioned.account} gameId=${ctx.gameId} challengeId=${ctx.challengeId}`,
    )
  })

  test.afterAll(async () => {
    fs.mkdirSync(REPORT_DIR, { recursive: true })
    const summary = {
      baseURL: BASE_URL,
      user: provisioned?.account,
      gameId: ctx.gameId,
      challengeId: ctx.challengeId,
      total: results.length,
      passed: results.filter((r) => r.ok).length,
      failed: results.filter((r) => !r.ok && !r.skipped).length,
      skipped: results.filter((r) => r.skipped).length,
      mismatches: results.filter((r) => !r.ok && !r.skipped),
      results,
      generatedAt: new Date().toISOString(),
    }
    fs.writeFileSync(REPORT_FILE, JSON.stringify(summary, null, 2), 'utf8')
    console.log(`[api-topology] report → ${REPORT_FILE}`)
    console.log(
      `[api-topology] ${summary.passed}/${summary.total} passed, failed=${summary.failed}, skipped=${summary.skipped}`,
    )
    await context?.close()
  })

  test('0. 会话与赛题上下文就绪', async () => {
    expect(page).toBeTruthy()
    expect(provisioned?.account).toBeTruthy()
    const me = await page.request.get('/api/auth/me', { failOnStatusCode: false })
    expect(me.status(), 'Cookie 会话应能访问 /api/auth/me').toBe(200)
  })

  for (const probe of API_PROBES) {
    test(`${probe.section} ${probe.method} ${probe.id}`, async () => {
      const needsGame = typeof probe.path === 'function' && String(probe.path).includes('gameId')
      const needsChal =
        typeof probe.path === 'function' && String(probe.path).includes('challengeId')

      // 更可靠：解析实际 path
      let url
      try {
        url = typeof probe.path === 'function' ? probe.path(ctx) : probe.path
      } catch {
        results.push({
          id: probe.id,
          ok: false,
          skipped: true,
          reason: 'path build failed',
          expect: probe.expect,
        })
        test.skip(true, '无法构建 path')
        return
      }

      if (url.includes('null') || url.includes('undefined')) {
        results.push({
          id: probe.id,
          method: probe.method,
          path: url,
          ok: false,
          skipped: true,
          reason: '缺少 gameId/challengeId',
          expect: probe.expect,
          note: probe.note,
        })
        test.skip(!ctx.gameId || (needsChal && !ctx.challengeId), '缺少运行时 ID')
        return
      }

      const body =
        typeof probe.body === 'function' ? probe.body(ctx) : probe.body
      const opts = { failOnStatusCode: false }
      if (body !== undefined) opts.data = body

      const method = probe.method.toLowerCase()
      /** @type {import('@playwright/test').APIResponse} */
      let res
      if (method === 'get') res = await page.request.get(url, opts)
      else if (method === 'post') res = await page.request.post(url, opts)
      else if (method === 'put') res = await page.request.put(url, opts)
      else if (method === 'patch') res = await page.request.patch(url, opts)
      else if (method === 'delete') res = await page.request.delete(url, opts)
      else throw new Error(`unsupported method ${probe.method}`)

      const status = res.status()
      const text = await res.text().catch(() => '')
      let json = null
      try {
        json = text ? JSON.parse(text) : null
      } catch {
        /* non-json */
      }

      const ok = statusMatchesExpect(status, probe.expect)
      const row = {
        id: probe.id,
        section: probe.section,
        method: probe.method,
        path: url,
        expect: probe.expect,
        status,
        ok,
        skipped: false,
        note: probe.note || '',
        msg: json?.msg || json?.message || text.slice(0, 160),
      }
      results.push(row)

      expect.soft(
        ok,
        `${probe.id} ${probe.method} ${url} → ${status} (expect=${probe.expect}) ${row.msg}`,
      ).toBeTruthy()
    })
  }

  test('页面拓扑：管理端关键页不应出现 /api 404|410', async () => {
    const routes = [
      '/admin/dashboard',
      '/admin/users',
      '/admin/ctf',
      '/admin/settings',
      '/admin/carousel',
      '/games',
      ctx.gameId ? `/games/${ctx.gameId}/challenges` : null,
      ctx.gameId ? `/games/${ctx.gameId}/scoreboard` : null,
    ].filter(Boolean)

    const bad = []
    for (const route of routes) {
      const apiHits = []
      const onResp = (response) => {
        const u = response.url()
        if (!u.includes('/api/')) return
        const st = response.status()
        if (st === 404 || st === 410 || st >= 500) {
          apiHits.push({ url: u, status: st, route })
        }
      }
      page.on('response', onResp)
      await page.goto(route, { waitUntil: 'domcontentloaded' })
      await page.waitForTimeout(1200)
      page.off('response', onResp)
      bad.push(...apiHits)
    }

    results.push({
      id: 'page_api_scan',
      ok: bad.length === 0,
      skipped: false,
      bad,
      expect: 'no-404-410-5xx',
    })

    expect(bad, `页面触发的坏 API: ${JSON.stringify(bad, null, 2)}`).toEqual([])
  })
})
