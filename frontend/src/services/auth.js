import axios from 'axios'

let _user = null
let _sessionPromise = null

function userKey(user) {
  if (!user || user.id == null) return ''
  return `${user.id}:${user.is_admin ? 1 : 0}:${user.nickname || ''}:${user.avatar || ''}`
}

function emitUserRefreshed() {
  try {
    window.dispatchEvent(new Event('neepu_user_refreshed'))
  } catch { /* ignore */ }
}

export function getUser() {
  return _user
}

export function setUser(user) {
  const prev = userKey(_user)
  _user = user || null
  if (userKey(_user) !== prev) emitUserRefreshed()
}

export function clearUser() {
  _user = null
  try {
    window.dispatchEvent(new Event('neepu_auth_expired'))
  } catch { /* ignore */ }
}

export function isLoggedIn() {
  return !!_user
}

/** 以 HttpOnly Cookie 为准判断是否已登录（必要时请求 /me） */
export async function hasSession() {
  return !!(await fetchSession())
}

export function isAdmin() {
  return !!(_user && _user.is_admin)
}

/**
 * 从 HttpOnly Cookie 会话拉取当前用户。
 * - 并发请求合并为一次（含 force）
 * - 用户信息未变化时不广播 neepu_user_refreshed，避免监听方连环 force 刷新
 */
export async function fetchSession({ force = false } = {}) {
  if (!force && _user) return _user
  if (_sessionPromise) return _sessionPromise

  const prevKey = userKey(_user)

  _sessionPromise = axios
    .get('/api/auth/me', { _skipAuthClear: true })
    .then((res) => {
      const next = res.data && !res.data.msg ? res.data : null
      _user = next
      if (userKey(next) !== prevKey) emitUserRefreshed()
      return _user
    })
    .catch(() => {
      const hadUser = !!_user
      _user = null
      if (hadUser) {
        try {
          window.dispatchEvent(new Event('neepu_auth_expired'))
        } catch { /* ignore */ }
      }
      return null
    })
    .finally(() => {
      _sessionPromise = null
    })

  return _sessionPromise
}

export async function logout() {
  try {
    await axios.post('/api/auth/logout')
  } catch { /* ignore */ }
  try {
    localStorage.removeItem('neepu_token')
    localStorage.removeItem('token')
  } catch { /* ignore */ }
  clearUser()
}
