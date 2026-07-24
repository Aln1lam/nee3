/**
 * 共享 Axios 客户端：CSRF + 401/403/429 统一处理
 * 业务 service（container/challenges/teams…）应使用本实例，勿再 axios.create 裸奔。
 */
import axios from 'axios'

function readCookie(name) {
  if (typeof document === 'undefined') return ''
  const hit = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))
  if (!hit) return ''
  return decodeURIComponent(hit.split('=').slice(1).join('='))
}

export const http = axios.create({
  withCredentials: true,
  timeout: 60_000,
})

http.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrf = readCookie('csrf_access_token')
    if (csrf) {
      config.headers = config.headers || {}
      config.headers['X-CSRF-TOKEN'] = csrf
    }
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (err) => {
    const status = err?.response?.status
    const data = err?.response?.data
    const msg =
      data?.msg ||
      data?.message ||
      data?.error ||
      err?.message ||
      '请求失败'

    if (status === 401) {
      try {
        window.dispatchEvent(
          new CustomEvent('neepu_http_error', {
            detail: { status, msg: msg || '登录已过期，请重新登录' },
          }),
        )
      } catch { /* ignore */ }
    } else if (status === 403) {
      try {
        window.dispatchEvent(
          new CustomEvent('neepu_http_error', {
            detail: { status, msg: msg || '没有权限执行此操作' },
          }),
        )
      } catch { /* ignore */ }
    } else if (status === 429) {
      try {
        window.dispatchEvent(
          new CustomEvent('neepu_http_error', {
            detail: { status, msg: msg || '操作过于频繁，请稍后再试' },
          }),
        )
      } catch { /* ignore */ }
    }

    return Promise.reject(err)
  },
)

export default http
