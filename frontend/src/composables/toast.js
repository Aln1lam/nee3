import { ref } from 'vue'

const toasts = ref([])
const history = ref([])
let nextId = 1

function addToHistory(entry) {
  history.value.unshift(entry)
  if (history.value.length > 50) history.value.length = 50
}

export function useToast() {
  function push({ level = 'info', message, duration = 5000, accept, reject, acceptLabel = '确定', rejectLabel = '取消' }) {
    const id = nextId++
    const entry = { id, level, message, accept, reject, acceptLabel, rejectLabel }
    toasts.value.push(entry)
    addToHistory({ id, level, message, time: Date.now(), read: false })
    if (duration > 0 && !accept && !reject) {
      setTimeout(() => dismiss(id), duration)
    }
    return id
  }

  function dismiss(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function onAccept(t) {
    if (typeof t.accept === 'function') t.accept()
    dismiss(t.id)
  }

  function onReject(t) {
    if (typeof t.reject === 'function') t.reject()
    dismiss(t.id)
  }

  function info(message, duration) { return push({ level: 'info', message, duration }) }
  function success(message, duration) { return push({ level: 'success', message, duration }) }
  function warning(message, duration) { return push({ level: 'warning', message, duration }) }
  function error(message, duration) { return push({ level: 'error', message, duration }) }
  function confirm(message, { acceptLabel, rejectLabel, onAccept, onReject } = {}) {
    return push({
      level: 'warning',
      message,
      duration: 0,
      accept: onAccept,
      reject: onReject,
      acceptLabel: acceptLabel || '确定',
      rejectLabel: rejectLabel || '取消',
    })
  }

  return { toasts, push, dismiss, onAccept, onReject, info, success, warning, error, confirm }
}

export function useNotificationHistory() {
  function clearHistory() {
    history.value = []
  }

  function markAllRead() {
    history.value.forEach(h => { h.read = true })
  }

  return { history, clearHistory, markAllRead }
}
