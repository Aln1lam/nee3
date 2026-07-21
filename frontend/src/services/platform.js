import axios from 'axios'

/** API 不可用时的最小占位（避免硬编码运营文案） */
export const PLATFORM_FALLBACK = {
  name: 'CTF 平台',
  subtitle: '',
  brand_desc: '',
  tagline_link: '/wiki',
  site_description: '',
  maintenance_message: '',
  nav: [],
  footer: {
    org_name: '',
    org_url: '',
    copyright_years: `2022-${new Date().getFullYear()}`,
    icp: null,
    icp_url: 'https://beian.miit.gov.cn/',
  },
  loading_tips: [],
  oauth_providers: [],
  maintenance: false,
  features: {
    allow_registration: true,
    allow_teams: true,
    allow_games: true,
    require_email_verification: true,
  },
}

/** 与后端 platform:info TTL（120s）对齐，略短以避免陈旧数据 */
const CACHE_TTL_MS = 90_000

let cached = null
let cachedAt = 0

export function applyPlatformMeta(info) {
  if (!info || typeof document === 'undefined') return
  const title = info.name || PLATFORM_FALLBACK.name
  if (title) document.title = title
  const desc = info.site_description || info.brand_desc || ''
  if (desc) {
    let meta = document.querySelector('meta[name="description"]')
    if (!meta) {
      meta = document.createElement('meta')
      meta.setAttribute('name', 'description')
      document.head.appendChild(meta)
    }
    meta.setAttribute('content', desc)
  }
}

export async function fetchPlatformInfo({ force = false } = {}) {
  const now = Date.now()
  if (!force && cached && now - cachedAt < CACHE_TTL_MS) return cached
  try {
    const { data } = await axios.get('/api/platform/info')
    cached = { ...PLATFORM_FALLBACK, ...data }
    cachedAt = now
    applyPlatformMeta(cached)
    return cached
  } catch {
    return { ...PLATFORM_FALLBACK }
  }
}

export async function fetchPlatformVersion() {
  try {
    const { data } = await axios.get('/api/platform/version')
    return data
  } catch {
    return { version: 'unknown' }
  }
}

export function clearPlatformCache() {
  cached = null
  cachedAt = 0
}
