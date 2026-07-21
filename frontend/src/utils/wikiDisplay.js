/** Wiki 列表展示格式化：标签 slug → 可读文案，时间 → 本地格式 */

const TAG_LABELS = {
  'wiki:ics-security': '工控安全',
  'wiki:power-grid-sec': '电力信息安全',
  'wiki:connector': '连接器',
  'wiki:how-to-use': '使用指南',
  'wiki:ctf-roadmap': '学习路线',
  'wiki:writeup': '题解',
  'ics-security': '工控安全',
  'power-grid-sec': '电力信息安全',
  connector: '连接器',
  'how-to-use': '使用指南',
  'ctf-roadmap': '学习路线',
  writeup: '题解',
  web: 'Web',
  pwn: 'Pwn',
  crypto: 'Crypto',
  reverse: 'Reverse',
  misc: 'MISC',
  awd: 'AWD',
  ai: 'AI',
  blockchain: '区块链',
}

export function formatWikiTag(raw) {
  const t = String(raw || '').trim()
  if (!t) return ''
  const key = t.toLowerCase()
  if (TAG_LABELS[key]) return TAG_LABELS[key]
  // wiki:foo-bar → Foo Bar / 去前缀后可读化
  let s = t.replace(/^wiki:/i, '')
  if (TAG_LABELS[s.toLowerCase()]) return TAG_LABELS[s.toLowerCase()]
  s = s.replace(/[-_]+/g, ' ').trim()
  if (!s) return t
  // 纯英文单词：首字母大写
  if (/^[a-z0-9 ]+$/i.test(s)) {
    return s.replace(/\b\w/g, (c) => c.toUpperCase())
  }
  return s
}

export function formatWikiTags(tagsField) {
  if (!tagsField) return []
  const parts = String(tagsField)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  const seen = new Set()
  const out = []
  for (const p of parts) {
    const label = formatWikiTag(p)
    if (!label || seen.has(label)) continue
    seen.add(label)
    out.push(label)
  }
  return out
}

export function formatWikiTime(t) {
  if (!t) return ''
  try {
    return new Date(t).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  } catch {
    return String(t).replace('T', ' ').slice(0, 16)
  }
}
