/**
 * 从 JSON body / 字符串提取业务错误文案（fetch 场景）
 */
export function apiErrorFromPayload(payload, fallback = '请求失败') {
  if (payload == null || payload === '') return fallback
  if (typeof payload === 'string') {
    const t = payload.trim()
    return t || fallback
  }
  const msg = payload.msg || payload.message || payload.error
  if (typeof msg === 'string' && msg.trim()) return msg.trim()
  try {
    const s = JSON.stringify(payload)
    if (s && s !== '{}' && s !== 'null') return s.length > 200 ? `${s.slice(0, 200)}…` : s
  } catch (_) { /* ignore */ }
  return fallback
}

/**
 * 统一解析后端错误（限流 / 敏感词 / 业务 msg）
 */
export function apiErrorMessage(err, fallback = '请求失败') {
  const status = err?.response?.status
  const data = err?.response?.data
  const msg =
    data?.msg ||
    data?.message ||
    data?.error ||
    (typeof data === 'string' ? data : null)

  if (status === 429 || data?.error === 'rate_limit_exceeded' || data?.error === 'submission_rate_limit_exceeded') {
    return msg || '操作过于频繁，请稍后再试'
  }
  if (status === 501) {
    return msg || '该功能尚未开放'
  }
  if (status === 401) {
    return msg || '登录已过期，请重新登录'
  }
  if (status === 403) {
    return msg || '需要管理员权限或登录已过期，请重新登录'
  }
  return msg || err?.message || fallback
}

export function isRateLimited(err) {
  const status = err?.response?.status
  const data = err?.response?.data
  return status === 429 || String(data?.error || '').includes('rate_limit')
}
