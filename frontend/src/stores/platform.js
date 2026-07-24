import { shallowRef, readonly } from 'vue'
import { fetchPlatformInfo, clearPlatformCache, PLATFORM_FALLBACK, applyPlatformMeta } from '@/services/platform'

const platform = shallowRef({ ...PLATFORM_FALLBACK })
const loaded = shallowRef(false)
const loading = shallowRef(false)

export async function loadPlatform(options = {}) {
  if (loading.value && !options.force) return platform.value
  loading.value = true
  try {
    const info = await fetchPlatformInfo({ force: options.force })
    platform.value = { ...PLATFORM_FALLBACK, ...info }
    loaded.value = true
    applyPlatformMeta(platform.value)
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('neepu_platform_updated', { detail: platform.value }))
    }
    return platform.value
  } finally {
    loading.value = false
  }
}

export async function reloadPlatform() {
  clearPlatformCache()
  return loadPlatform({ force: true })
}

export function usePlatformStore() {
  return {
    platform: readonly(platform),
    loaded: readonly(loaded),
    loading: readonly(loading),
    loadPlatform,
    reloadPlatform,
  }
}
