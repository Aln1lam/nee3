import axios from 'axios'

let _user = null
let _sessionPromise = null

export function getUser() {
  return _user
}

export function setUser(user) {
  _user = user || null
  try {
    window.dispatchEvent(new Event('neepu_user_refreshed'))
  } catch { /* ignore */ }
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

/** 从 HttpOnly Cookie 会话拉取当前用户 */
export async function fetchSession({ force = false } = {}) {
  if (!force && _user) return _user
  if (!force && _sessionPromise) return _sessionPromise

  _sessionPromise = axios
    .get('/api/auth/me', { _skipAuthClear: true })
    .then((res) => {
      _user = res.data && !res.data.msg ? res.data : null
      if (_user) {
        try {
          window.dispatchEvent(new Event('neepu_user_refreshed'))
        } catch { /* ignore */ }
      }
      return _user
    })
    .catch(() => {
      _user = null
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
