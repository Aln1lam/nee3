/** 赛事展示相关的通用格式化与状态判断 */

export function getGameEmoji(g) {
  const t = (g?.title || '').toLowerCase()
  if (t.includes('web')) return '🌐'
  if (t.includes('pwn') || t.includes('binary')) return '💣'
  if (t.includes('crypto')) return '🔐'
  if (t.includes('awd')) return '⚔️'
  if (t.includes('工控') || t.includes('ics')) return '⚡'
  return '🏁'
}

export function getGameCoverTheme(g) {
  const h = (g?.title || '').length
  return h % 2 === 0 ? 'theme-stars' : 'theme-suzume'
}

export function getGameStatusLabel(g) {
  if (!g) return ''
  const now = Date.now()
  const start = g.start_time ? new Date(g.start_time).getTime() : 0
  const end = g.end_time ? new Date(g.end_time).getTime() : Infinity
  if (g.status === 'archived') return '已归档'
  if (now < start) return '报名中'
  if (now >= start && now < end) return '进行中'
  return '已结束'
}

export function getGameStatusVariant(g) {
  const label = getGameStatusLabel(g)
  if (label === '进行中') return 'success'
  if (label === '报名中') return 'warning'
  if (label === '已归档') return 'info'
  return 'default'
}

export function getGameStatusDotClass(g) {
  const label = getGameStatusLabel(g)
  if (label === '进行中') return 'dot-live'
  if (label === '报名中') return 'dot-soon'
  return 'dot-ended'
}

export function formatGameTime(t) {
  if (!t) return '-'
  try {
    return new Date(t).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return t
  }
}

export function formatGameTimeRange(g) {
  if (!g) return ''
  return `${formatGameTime(g.start_time)} ~ ${formatGameTime(g.end_time)}`
}

export function getGamePosterPath(g) {
  if (!g) return ''
  if (g.poster_url) return g.poster_url
  if (g.cover_url) return g.cover_url
  if (g.poster) return g.poster
  // 简介 / 规则 Markdown 内嵌图均可作为海报
  return extractPosterPath(g.description) || extractPosterPath(g.rules)
}

export function extractPosterPath(text) {
  if (!text) return ''
  const md = text.match(/!\[[^\]]*\]\(([^)]+)\)/)
  if (md?.[1]) return md[1]
  const html = text.match(/<img[^>]+src=["']([^"']+)["']/i)
  if (html?.[1]) return html[1]
  return ''
}

export function getGameSubtitle(g) {
  if (g?.summary?.trim()) return g.summary.trim()
  const raw = (g?.description || '').trim()
  if (!raw) return '东北电力大学网络安全竞赛'
  const line = raw
    .replace(/^#+\s+/gm, '')
    .replace(/!\[[^\]]*\]\([^)]+\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[*_`>#-]/g, '')
    .split('\n')
    .map(s => s.trim())
    .find(Boolean)
  return line ? line.slice(0, 96) : '东北电力大学网络安全竞赛'
}
