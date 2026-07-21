/**
 * 页面运行时监控：console.error、pageerror、未处理 Promise 拒绝、失败请求。
 */
export function attachPageMonitor(page, label = 'page') {
  const state = {
    label,
    consoleErrors: [],
    pageErrors: [],
    promiseRejections: [],
    failedRequests: [],
  }

  page.on('console', (msg) => {
    if (msg.type() !== 'error') return
    state.consoleErrors.push({
      text: msg.text(),
      location: msg.location(),
      time: new Date().toISOString(),
    })
  })

  page.on('pageerror', (err) => {
    state.pageErrors.push({
      message: err?.message || String(err),
      stack: err?.stack || '',
      time: new Date().toISOString(),
    })
  })

  page.on('requestfailed', (req) => {
    const failure = req.failure()
    state.failedRequests.push({
      url: req.url(),
      method: req.method(),
      errorText: failure?.errorText || 'unknown',
      time: new Date().toISOString(),
    })
  })

  page.addInitScript(() => {
    window.addEventListener('unhandledrejection', (event) => {
      const reason = event.reason
      const message =
        reason && typeof reason === 'object' && 'message' in reason
          ? String(reason.message)
          : String(reason)
      window.__e2eUnhandledRejections = window.__e2eUnhandledRejections || []
      window.__e2eUnhandledRejections.push({
        message,
        time: new Date().toISOString(),
      })
    })
  })

  return {
    state,
    async flushPromiseRejections() {
      const remote = await page.evaluate(() => {
        const list = window.__e2eUnhandledRejections || []
        window.__e2eUnhandledRejections = []
        return list
      }).catch(() => [])
      state.promiseRejections.push(...remote)
      return remote
    },
    snapshot() {
      return {
        label: state.label,
        consoleErrors: [...state.consoleErrors],
        pageErrors: [...state.pageErrors],
        promiseRejections: [...state.promiseRejections],
        failedRequests: [...state.failedRequests],
      }
    },
    hasErrors() {
      return (
        state.consoleErrors.length > 0 ||
        state.pageErrors.length > 0 ||
        state.promiseRejections.length > 0
      )
    },
  }
}

/**
 * 检查页面内所有同域/相对链接是否返回 404。
 * 跳过 mailto/tel/javascript/锚点与外链。
 */
export async function checkBrokenLinks(page, { baseURL } = {}) {
  const origin = baseURL || page.url()
  const hrefs = await page.evaluate(() => {
    const anchors = Array.from(document.querySelectorAll('a[href]'))
    return anchors
      .map((a) => ({
        href: a.getAttribute('href') || '',
        text: (a.textContent || '').trim().slice(0, 80),
      }))
      .filter((x) => x.href && x.href !== '#')
  })

  const seen = new Set()
  const broken = []
  const checked = []

  for (const { href, text } of hrefs) {
    const lower = href.toLowerCase()
    if (
      lower.startsWith('mailto:') ||
      lower.startsWith('tel:') ||
      lower.startsWith('javascript:') ||
      lower.startsWith('data:') ||
      href.startsWith('#')
    ) {
      continue
    }

    let absolute
    try {
      absolute = new URL(href, page.url()).toString()
    } catch {
      broken.push({ href, text, status: 'invalid-url', reason: '无法解析 URL' })
      continue
    }

    // 仅检查同站链接，避免扫外网
    try {
      const pageOrigin = new URL(page.url()).origin
      const linkOrigin = new URL(absolute).origin
      if (linkOrigin !== pageOrigin) continue
    } catch {
      continue
    }

    if (seen.has(absolute)) continue
    seen.add(absolute)

    let status = 0
    try {
      const res = await page.request.get(absolute, {
        maxRedirects: 5,
        timeout: 15_000,
        failOnStatusCode: false,
      })
      status = res.status()
    } catch (err) {
      broken.push({
        href,
        absolute,
        text,
        status: 0,
        reason: err?.message || 'request failed',
      })
      continue
    }

    checked.push({ href, absolute, text, status })
    if (status === 404) {
      broken.push({ href, absolute, text, status, reason: 'HTTP 404' })
    }
  }

  return { checked, broken, origin }
}
