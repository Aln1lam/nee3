/**
 * 统一短轮询、可见性感知轮询、防抖 / 节流（全局性能基建）
 */

export const POLL_INTERVALS = Object.freeze({
  hammer: 15000,
  adminChat: 15000,
  container: 30000,
  notices: 20000,
  blood: 20000,
  scoreboard: 30000,
})

/**
 * 尾触发防抖
 * @param {(...args: any[]) => void} fn
 * @param {number} waitMs
 */
export function debounce(fn, waitMs = 120) {
  let timer = null
  const wrapped = (...args) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      fn(...args)
    }, waitMs)
  }
  wrapped.cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }
  return wrapped
}

/**
 * 节流：leading + trailing
 * @param {(...args: any[]) => void} fn
 * @param {number} waitMs
 */
export function throttle(fn, waitMs = 100) {
  let last = 0
  let timer = null
  let pendingArgs = null

  const wrapped = (...args) => {
    const now = Date.now()
    const remain = waitMs - (now - last)
    pendingArgs = args
    if (remain <= 0) {
      if (timer) {
        clearTimeout(timer)
        timer = null
      }
      last = now
      pendingArgs = null
      fn(...args)
      return
    }
    if (!timer) {
      timer = setTimeout(() => {
        last = Date.now()
        timer = null
        const a = pendingArgs
        pendingArgs = null
        if (a) fn(...a)
      }, remain)
    }
  }
  wrapped.cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    pendingArgs = null
  }
  return wrapped
}

/**
 * rAF 合并高频事件（mousemove / resize / scroll）
 * @param {(...args: any[]) => void} fn
 */
export function rafThrottle(fn) {
  let locked = false
  let pendingArgs = null
  const wrapped = (...args) => {
    pendingArgs = args
    if (locked) return
    locked = true
    requestAnimationFrame(() => {
      locked = false
      const a = pendingArgs
      pendingArgs = null
      if (a) fn(...a)
    })
  }
  wrapped.cancel = () => {
    pendingArgs = null
    locked = false
  }
  return wrapped
}

/**
 * @param {() => void|Promise<void>} fn
 * @param {number} intervalMs
 * @returns {{ start: () => void, stop: () => void, tick: () => void }}
 */
export function createVisibilityPoll(fn, intervalMs) {
  let timer = null
  let running = false
  let inFlight = false

  const tick = () => {
    if (typeof document !== 'undefined' && document.hidden) return
    if (inFlight) return
    try {
      const r = fn()
      if (r && typeof r.then === 'function') {
        inFlight = true
        Promise.resolve(r)
          .catch(() => {})
          .finally(() => {
            inFlight = false
          })
      }
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
