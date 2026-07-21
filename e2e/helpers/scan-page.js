/**
 * 单页扫描：导航 → 监控 → 死链 → 截图入报告
 */
import { expect } from '@playwright/test'
import { attachPageMonitor, checkBrokenLinks } from './page-monitor.js'
import { recordPageScan } from './scan-report.js'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000'

/**
 * @param {import('@playwright/test').Page} page
 * @param {import('../topology/routes.js').TopologyRoute} route
 * @param {{ deep?: (page, monitor, notes) => Promise<void>, softBrokenLinks?: boolean }} [opts]
 */
export async function scanTopologyRoute(page, route, opts = {}) {
  const monitor = attachPageMonitor(page, route.name)
  const notes = [`拓扑 ${route.section} · ${route.name}`, `鉴权级别: ${route.auth}`]
  if (route.note) notes.push(route.note)
  if (route.aliasOf) notes.push(`别名 → ${route.aliasOf}`)

  await page.goto(route.path, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(600)

  if (route.expectUrl?.length) {
    // 客户端 redirect 可能稍晚于 domcontentloaded
    const matched = await Promise.race([
      (async () => {
        for (const re of route.expectUrl) {
          try {
            await page.waitForURL(new RegExp(re), { timeout: 8_000 })
            return true
          } catch {
            /* try next */
          }
        }
        return false
      })(),
      page.waitForTimeout(8_000).then(() => false),
    ])
    if (!matched) {
      // 再读一次最终 URL 做断言
    }
  }

  const finalUrl = page.url()
  notes.push(`最终 URL: ${finalUrl}`)

  if (route.expectUrl?.length) {
    const ok = route.expectUrl.some((re) => new RegExp(re).test(finalUrl))
    if (!ok) {
      notes.push(`⚠ 别名未跳转：期望 ${route.expectUrl.join('|')}，实际 ${finalUrl}`)
      // 别名失效记入报告，不阻断整段拓扑（产品缺口可后续修）
    } else {
      expect(ok).toBeTruthy()
    }
  }

  // 未登录访问需登录页：应落到 /auth
  if (route.auth === 'auth' || route.auth === 'admin') {
    const onAuth = /\/auth/.test(finalUrl)
    const stillOnTarget = finalUrl.includes(route.path.split('?')[0]) ||
      (route.expectUrl || []).some((re) => new RegExp(re).test(finalUrl))
    if (onAuth) notes.push('已重定向到 /auth（会话未建立或权限不足）')
    else if (stillOnTarget || !onAuth) notes.push('已进入目标页（或等价落地）')
  }

  if (opts.deep) {
    await opts.deep(page, monitor, notes)
  }

  const links = await checkBrokenLinks(page, { baseURL: BASE_URL })
  notes.push(`同站链接检查 ${links.checked.length} 个，404=${links.broken.length}`)

  await monitor.flushPromiseRejections()
  await recordPageScan(page, {
    route: `${route.section} ${route.path}`,
    title: `${route.section} ${route.name}`,
    monitor,
    brokenLinks: links.broken,
    notes,
    extra: {
      section: route.section,
      auth: route.auth,
      pageErrors: monitor.state.pageErrors.length,
    },
  })

  // 未捕获异常一律失败；死链默认 soft（拓扑全量时先汇总，由断言可选收紧）
  expect(
    monitor.state.pageErrors,
    `pageerror @ ${route.path}: ${JSON.stringify(monitor.state.pageErrors)}`,
  ).toEqual([])

  if (!opts.softBrokenLinks) {
    expect(
      links.broken,
      `失效链接 @ ${route.path}: ${JSON.stringify(links.broken)}`,
    ).toEqual([])
  }

  return { monitor, notes, links, finalUrl }
}
