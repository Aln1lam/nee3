/** 题目分类 → 二次元 chip / 色条（稳定哈希，深浅主题通用） */

const PALETTE = [
  { stripe: '#EC4899', chipBg: 'rgba(236, 72, 153, 0.16)', chipText: 'var(--gradient-tag-text, #9D174D)' },
  { stripe: '#2DB58A', chipBg: 'rgba(45, 181, 138, 0.16)', chipText: '#15803D' },
  { stripe: '#60A5FA', chipBg: 'rgba(96, 165, 250, 0.16)', chipText: '#1D4ED8' },
  { stripe: '#F97316', chipBg: 'rgba(249, 115, 22, 0.16)', chipText: '#C2410C' },
  { stripe: '#A855F7', chipBg: 'rgba(168, 85, 247, 0.16)', chipText: '#7E22CE' },
  { stripe: '#14B8A6', chipBg: 'rgba(20, 184, 166, 0.16)', chipText: '#0F766E' },
]

function hashKey(name) {
  const key = (name || 'misc').toLowerCase()
  let h = 0
  for (let i = 0; i < key.length; i += 1) {
    h = ((h << 5) - h) + key.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h)
}

export function getCategoryStyle(name) {
  return PALETTE[hashKey(name) % PALETTE.length]
}
