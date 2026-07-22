import { ref, computed } from 'vue'

const theme = ref('dark')
const followSystem = ref(false)
let mediaListener = null

function readStorage() {
  try {
    theme.value = localStorage.getItem('neepu_theme') || 'dark'
    followSystem.value = localStorage.getItem('neepu_theme_follow') === '1'
  } catch { /* ignore */ }
}

export function applyTheme(name) {
  const next = name === 'light' ? 'light' : 'dark'
  theme.value = next
  const link = document.getElementById('theme-css')
  if (link) link.href = `/themes/${next}.css`
  document.documentElement.setAttribute('data-theme', next)
  document.documentElement.classList.remove('theme-dark-locked')
  if (!followSystem.value) {
    try { localStorage.setItem('neepu_theme', next) } catch { /* ignore */ }
  }
}

export function setTheme(name) {
  followSystem.value = false
  try { localStorage.setItem('neepu_theme_follow', '0') } catch { /* ignore */ }
  applyTheme(name)
}

export function setFollowSystem(enabled) {
  followSystem.value = !!enabled
  try { localStorage.setItem('neepu_theme_follow', enabled ? '1' : '0') } catch { /* ignore */ }
  if (enabled) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme(prefersDark ? 'dark' : 'light')
  }
}

export function initTheme() {
  readStorage()
  try {
    localStorage.removeItem('neepu_htb_dark_v1')
  } catch { /* ignore */ }
  if (followSystem.value) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme(prefersDark ? 'dark' : 'light')
  } else {
    applyTheme(theme.value)
  }
  if (mediaListener) {
    window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', mediaListener)
  }
  mediaListener = (e) => {
    if (followSystem.value) applyTheme(e.matches ? 'dark' : 'light')
  }
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', mediaListener)
}

export function useThemeStore() {
  const isDark = computed(() => theme.value === 'dark')
  const label = computed(() => (isDark.value ? '深色模式' : '浅色模式'))
  return {
    theme,
    followSystem,
    isDark,
    label,
    applyTheme,
    setTheme,
    setFollowSystem,
    initTheme,
  }
}
