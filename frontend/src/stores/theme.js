import { computed } from 'vue'

/**
 * Dark Obsidian — 全站唯一主题。
 * 无切换、无 localStorage、无跟随系统。
 */
export function applyTheme() {
  const link = document.getElementById('theme-css')
  if (link) link.href = '/themes/dark.css'
  document.documentElement.setAttribute('data-theme', 'dark')
  document.documentElement.classList.add('theme-dark-locked')
}

/** @deprecated 保留空实现以免旧调用报错 */
export function setTheme() {
  applyTheme()
}

/** @deprecated */
export function setFollowSystem() {
  applyTheme()
}

export function initTheme() {
  applyTheme()
  try {
    localStorage.removeItem('neepu_theme')
    localStorage.removeItem('neepu_theme_follow')
    localStorage.removeItem('neepu_htb_dark_v1')
  } catch { /* ignore */ }
}

export function useThemeStore() {
  return {
    theme: computed(() => 'dark'),
    followSystem: computed(() => false),
    isDark: computed(() => true),
    label: computed(() => '深色模式'),
    applyTheme,
    setTheme,
    setFollowSystem,
    initTheme,
  }
}
