/**
 * 平台路由映射：用户口语路径 → 实际前端路由。
 *
 * /login, /register  → /auth（弹窗内 Tab）
 * /challenges        → /games/:id/challenges
 * /scoreboard        → /games/:id/scoreboard
 */

export const AUTH_LOGIN = '/auth'
export const AUTH_REGISTER_ALIAS = '/account/register'
export const AUTH_LOGIN_ALIAS = '/account/login'

export function challengesPath(gameId) {
  return `/games/${gameId}/challenges`
}

export function scoreboardPath(gameId) {
  return `/games/${gameId}/scoreboard`
}

/**
 * 通过公开 API 发现可用赛事 ID；失败则从 /games 页面抓取。
 */
function collectIdsFromPayload(body, ids) {
  const list =
    body?.data?.items ||
    body?.data?.games ||
    body?.data?.competitions ||
    body?.data ||
    body?.games ||
    body?.items ||
    body?.competitions ||
    []
  const arr = Array.isArray(list) ? list : []
  for (const g of arr) {
    if (g?.id != null) ids.add(String(g.id))
  }
}

export async function discoverGameIds(page, { limit = 5 } = {}) {
  const ids = new Set()
  const endpoints = [
    '/api/competitions/?exclude_training=true',
    '/api/competitions/',
    '/api/competitions/?game_type=training',
  ]

  for (const url of endpoints) {
    try {
      const res = await page.request.get(url, { failOnStatusCode: false })
      if (res.ok()) collectIdsFromPayload(await res.json(), ids)
    } catch {
      /* try next */
    }
    if (ids.size >= limit) break
  }

  if (ids.size === 0) {
    await page.goto('/games', { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    const fromDom = await page.evaluate(() => {
      const found = new Set()
      for (const a of document.querySelectorAll('a[href*="/games/"]')) {
        const m = a.getAttribute('href')?.match(/\/games\/(\d+)/)
        if (m) found.add(m[1])
      }
      for (const btn of document.querySelectorAll('[data-game-id], .r2s-games__list-btn')) {
        const id = btn.getAttribute('data-game-id')
        if (id) found.add(id)
      }
      return [...found]
    })
    fromDom.forEach((id) => ids.add(id))
  }

  const envId = process.env.E2E_GAME_ID
  const ordered = []
  if (envId) ordered.push(String(envId))
  for (const id of ids) {
    if (!ordered.includes(String(id))) ordered.push(String(id))
  }
  return ordered.slice(0, limit)
}

export async function switchAuthTab(page, mode = 'login') {
  const label = mode === 'register' ? '新用户注册' : '身份认证'
  const dialog = page.locator('[role="dialog"]')
  await dialog.waitFor({ state: 'visible', timeout: 20_000 })

  // naive-ui tabs 不一定暴露 role=tab，优先点 .n-tabs-tab
  const tab = dialog.locator('.n-tabs-tab').filter({ hasText: label })
  if (await tab.count()) {
    await tab.first().click()
  } else {
    await dialog.getByText(label, { exact: true }).first().click()
  }
  await page.waitForTimeout(300)
}

export async function openAuthModal(page, { mode = 'login' } = {}) {
  const path = mode === 'register' ? AUTH_REGISTER_ALIAS : AUTH_LOGIN_ALIAS
  await page.goto(path, { waitUntil: 'domcontentloaded' })
  // 实际会落到 /auth，并弹出 modal
  await page.waitForSelector('[role="dialog"], .n-modal, .n-card', { timeout: 20_000 })
  await switchAuthTab(page, mode)
}

export async function fillNaiveInput(page, placeholderOrLabel, value) {
  // 优先 placeholder（含 password 的 aria/placeholder）
  const byPlaceholder = page.getByPlaceholder(placeholderOrLabel)
  if (await byPlaceholder.count()) {
    await byPlaceholder.first().fill(value)
    return
  }
  const byCss = page.locator(`.n-input__input-el[placeholder="${placeholderOrLabel}"]`)
  if (await byCss.count()) {
    await byCss.first().fill(value)
    return
  }
  // 退而求其次：标签行附近的 input
  const labeled = page.locator('.n-form-item, .n-form-item-row').filter({
    hasText: placeholderOrLabel,
  }).locator('.n-input__input-el, input')
  if (await labeled.count()) {
    await labeled.first().fill(value)
    return
  }
  throw new Error(`找不到输入框: ${placeholderOrLabel}`)
}

/**
 * 可选登录。需要环境变量 E2E_USER / E2E_PASSWORD。
 * 优先走 API + Cookie 会话（现网 login 可能不返回 access_token）。
 */
export async function tryLogin(page) {
  const account = process.env.E2E_USER
  const password = process.env.E2E_PASSWORD
  if (!account || !password) return false

  // 1) API 登录（与页面共享 Cookie jar）
  try {
    const res = await page.request.post('/api/auth/login', {
      data: { account, password },
      failOnStatusCode: false,
    })
    if (res.ok()) {
      const me = await page.request.get('/api/auth/me', { failOnStatusCode: false })
      if (me.ok()) {
        await page.goto('/home', { waitUntil: 'domcontentloaded' })
        await page.waitForTimeout(500)
        if (!/\/auth/.test(page.url())) return true
      }
    }
  } catch {
    /* fall through to UI login */
  }

  // 2) UI 登录兜底
  await openAuthModal(page, { mode: 'login' })
  await fillNaiveInput(page, '用户名 / 手机号 / 邮箱', account)
  await page.locator('[role="dialog"] input[type="password"]').first().fill(password)
  await page.getByRole('button', { name: '确认进入系统' }).click()
  await page.waitForTimeout(1500)

  const token = await page.evaluate(() => localStorage.getItem('neepu_token') || localStorage.getItem('token'))
  if (token) return true
  if (/\/home|\/games|\/training|\/myprofile|\/admin/.test(page.url())) return true

  const me2 = await page.request.get('/api/auth/me', { failOnStatusCode: false }).catch(() => null)
  return !!(me2 && me2.ok())
}

/** 当前浏览器上下文是否已登录 */
export async function isLoggedIn(page) {
  const me = await page.request.get('/api/auth/me', { failOnStatusCode: false }).catch(() => null)
  return !!(me && me.ok())
}
