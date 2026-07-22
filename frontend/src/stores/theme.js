import { ref, computed } from 'vue'

/** 平台固定 Dark Obsidian，不提供浅色切换 */
const theme = ref('dark')
const followSystem = ref(false)

export function applyTheme(_name) {
  theme.value = 'dark'
  const link = document.getElementById('theme-css')
  if (link) link.href = '/themes/dark.css'
  document.documentElement.setAttribute('data-theme', 'dark')
  document.documentElement.classList.add('theme-dark-locked')
  try {
    localStorage.setItem('neepu_theme', 'dark')
    localStorage.setItem('neepu_theme_follow', '0')
  } catch { /* ignore */ }
}

export function setTheme(_name) {
  applyTheme('dark')
}

export function setFollowSystem(_enabled) {
  followSystem.value = false
  applyTheme('dark')
}

export function initTheme() {
  try {
    localStorage.removeItem('neepu_htb_dark_v1')
    localStorage.setItem('neepu_theme', 'dark')
    localStorage.setItem('neepu_theme_follow', '0')
  } catch { /* ignore */ }
  applyTheme('dark')
}

export function useThemeStore() {
  const isDark = computed(() => true)
  const label = computed(() => '深色模式')
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
