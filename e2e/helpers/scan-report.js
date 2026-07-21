import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPORT_ROOT = path.resolve(__dirname, '..', 'e2e-report')
const STATE_FILE = path.join(REPORT_ROOT, '_scan-state.json')

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true })
}

export function resetScanState() {
  ensureDir(REPORT_ROOT)
  ensureDir(path.join(REPORT_ROOT, 'screenshots'))
  const state = {
    startedAt: new Date().toISOString(),
    pages: [],
    summary: {
      pages: 0,
      consoleErrors: 0,
      pageErrors: 0,
      promiseRejections: 0,
      brokenLinks: 0,
      screenshots: 0,
    },
  }
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf8')
  return state
}

export function loadScanState() {
  if (!fs.existsSync(STATE_FILE)) return resetScanState()
  return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'))
}

export function saveScanState(state) {
  ensureDir(REPORT_ROOT)
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf8')
}

/**
 * 记录单页扫描结果并保存截图。
 */
export async function recordPageScan(page, {
  route,
  title,
  monitor,
  brokenLinks = [],
  notes = [],
  extra = {},
} = {}) {
  ensureDir(path.join(REPORT_ROOT, 'screenshots'))
  const safe = String(route || 'page')
    .replace(/[^\w.-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80) || 'page'
  const stamp = Date.now()
  const filename = `${safe}-${stamp}.png`
  const screenshotPath = path.join(REPORT_ROOT, 'screenshots', filename)

  await monitor?.flushPromiseRejections?.()
  await page.screenshot({ path: screenshotPath, fullPage: true }).catch(async () => {
    await page.screenshot({ path: screenshotPath }).catch(() => null)
  })

  const snap = monitor?.snapshot?.() || {
    consoleErrors: [],
    pageErrors: [],
    promiseRejections: [],
    failedRequests: [],
  }

  const entry = {
    route,
    title: title || route,
    url: page.url(),
    time: new Date().toISOString(),
    screenshot: `screenshots/${filename}`,
    consoleErrors: snap.consoleErrors,
    pageErrors: snap.pageErrors,
    promiseRejections: snap.promiseRejections,
    failedRequests: snap.failedRequests,
    brokenLinks,
    notes,
    ...extra,
  }

  const state = loadScanState()
  state.pages.push(entry)
  state.summary.pages = state.pages.length
  state.summary.consoleErrors += entry.consoleErrors.length
  state.summary.pageErrors += entry.pageErrors.length
  state.summary.promiseRejections += entry.promiseRejections.length
  state.summary.brokenLinks += brokenLinks.length
  state.summary.screenshots += 1
  saveScanState(state)
  return entry
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderList(items, mapper) {
  if (!items?.length) return '<p class="ok">无</p>'
  return `<ul>${items.map((it) => `<li>${mapper(it)}</li>`).join('')}</ul>`
}

/**
 * 根据累积状态写出独立 HTML 报告。
 */
export function writeHtmlReport() {
  const state = loadScanState()
  state.finishedAt = new Date().toISOString()
  saveScanState(state)

  const pagesHtml = state.pages
    .map((p, idx) => {
      const errCount =
        p.consoleErrors.length +
        p.pageErrors.length +
        p.promiseRejections.length +
        (p.brokenLinks?.length || 0)
      const badge = errCount
        ? `<span class="badge bad">${errCount} 问题</span>`
        : `<span class="badge ok">通过</span>`

      return `
<section class="page-card" id="page-${idx}">
  <header>
    <h2>${esc(p.title)} ${badge}</h2>
    <p class="meta"><code>${esc(p.route)}</code> · <a href="${esc(p.url)}" target="_blank">${esc(p.url)}</a></p>
    <p class="meta">${esc(p.time)}</p>
  </header>
  <figure>
    <img src="${esc(p.screenshot)}" alt="screenshot ${esc(p.route)}" loading="lazy" />
  </figure>
  <div class="grid">
    <div>
      <h3>console.error (${p.consoleErrors.length})</h3>
      ${renderList(p.consoleErrors, (e) => `<code>${esc(e.text)}</code>`)}
    </div>
    <div>
      <h3>未捕获异常 (${p.pageErrors.length})</h3>
      ${renderList(p.pageErrors, (e) => `<code>${esc(e.message)}</code>`)}
    </div>
    <div>
      <h3>未处理 Promise 拒绝 (${p.promiseRejections.length})</h3>
      ${renderList(p.promiseRejections, (e) => `<code>${esc(e.message)}</code>`)}
    </div>
    <div>
      <h3>失效链接 404 (${p.brokenLinks?.length || 0})</h3>
      ${renderList(p.brokenLinks, (e) => `${esc(e.text || e.href)} → <code>${esc(e.absolute || e.href)}</code> (${esc(e.status)})`)}
    </div>
  </div>
  ${p.notes?.length ? `<div class="notes"><h3>备注</h3>${renderList(p.notes, (n) => esc(n))}</div>` : ''}
</section>`
    })
    .join('\n')

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>NEEPU CTF E2E 扫描报告</title>
  <style>
    :root {
      --bg: #0f1419;
      --panel: #1a222c;
      --text: #e7ecf1;
      --muted: #8b9aab;
      --ok: #3dd68c;
      --bad: #ff6b6b;
      --accent: #5b9fd4;
      --border: #2a3542;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: linear-gradient(160deg, #0b1016, #15202b 50%, #0f1419);
      color: var(--text);
      line-height: 1.5;
    }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 32px 20px 64px; }
    h1 { margin: 0 0 8px; font-size: 1.8rem; }
    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin: 24px 0 36px;
    }
    .stat {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
    }
    .stat .n { font-size: 1.6rem; font-weight: 700; }
    .stat .l { color: var(--muted); font-size: 0.85rem; }
    .page-card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .page-card h2 { margin: 0 0 6px; font-size: 1.25rem; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .meta { color: var(--muted); margin: 2px 0; font-size: 0.9rem; }
    .meta a { color: var(--accent); }
    figure { margin: 16px 0; }
    figure img {
      width: 100%;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: #000;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }
    h3 { margin: 0 0 8px; font-size: 0.95rem; color: var(--accent); }
    ul { margin: 0; padding-left: 18px; }
    li { margin: 4px 0; word-break: break-word; }
    code { font-family: Consolas, "Fira Code", monospace; font-size: 0.85rem; }
    .badge {
      font-size: 0.75rem;
      padding: 2px 8px;
      border-radius: 999px;
      font-weight: 600;
    }
    .badge.ok { background: rgba(61, 214, 140, 0.15); color: var(--ok); }
    .badge.bad { background: rgba(255, 107, 107, 0.15); color: var(--bad); }
    .ok { color: var(--ok); margin: 0; }
    .notes { margin-top: 14px; }
    footer { color: var(--muted); margin-top: 28px; font-size: 0.85rem; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>NEEPU CTF E2E 全量扫描报告</h1>
    <p class="meta">开始：${esc(state.startedAt)} · 结束：${esc(state.finishedAt)}</p>
    <div class="summary">
      <div class="stat"><div class="n">${state.summary.pages}</div><div class="l">扫描页面</div></div>
      <div class="stat"><div class="n">${state.summary.consoleErrors}</div><div class="l">console.error</div></div>
      <div class="stat"><div class="n">${state.summary.pageErrors}</div><div class="l">页面异常</div></div>
      <div class="stat"><div class="n">${state.summary.promiseRejections}</div><div class="l">Promise 拒绝</div></div>
      <div class="stat"><div class="n">${state.summary.brokenLinks}</div><div class="l">失效链接</div></div>
      <div class="stat"><div class="n">${state.summary.screenshots}</div><div class="l">截图</div></div>
    </div>
    ${pagesHtml || '<p>暂无页面结果</p>'}
    <footer>
      同时可查看 Playwright 内置报告：<code>npx playwright show-report</code>
    </footer>
  </div>
</body>
</html>`

  const out = path.join(REPORT_ROOT, 'index.html')
  fs.writeFileSync(out, html, 'utf8')
  return out
}
