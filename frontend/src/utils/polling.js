/**
 * 统一短轮询间隔与可见性感知轮询（F10）
 * 页面隐藏时暂停 tick，恢复可见时立刻补一次。
 */

export const POLL_INTERVALS = Object.freeze({
  hammer: 15000,
  adminChat: 15000,
  container: 30000,
  notices: 20000,
  blood: 20000,
})

/**
 * @param {() => void|Promise<void>} fn
 * @param {number} intervalMs
 * @returns {{ start: () => void, stop: () => void, tick: () => void }}
 */
export function createVisibilityPoll(fn, intervalMs) {
  let timer = null
  let running = false

  const tick = () => {
    if (typeof document !== 'undefined' && document.hidden) return
    try {
      const r = fn()
      if (r && typeof r.catch === 'function') r.catch(() => {})
    } catch (_) { /* ignore */ }
  }

  const onVisibility = () => {
    if (!running) return
    if (!document.hidden) tick()
  }

  const start = () => {
    stop()
    running = true
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', onVisibility)
    }
    timer = setInterval(tick, intervalMs)
  }

  const stop = () => {
    running = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }

  return { start, stop, tick }
}
