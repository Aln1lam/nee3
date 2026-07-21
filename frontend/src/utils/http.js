/** fetch 默认携带 Cookie 会话（配合 HttpOnly JWT） */
export function authFetch(url, options = {}) {
  const { headers, credentials, ...rest } = options
  return fetch(url, {
    credentials: credentials ?? 'include',
    headers: headers ?? {},
    ...rest,
  })
}

/** 安全解析 Response：只读取 body 一次，避免 json/text 重复消费 */
export async function parseJsonResponse(res) {
  const text = await res.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { raw: text }
    }
  }
  return { ok: res.ok, status: res.status, data, text }
}

/** 判断业务层是否成功（兼容 code: 200 / 0 与纯 HTTP 200） */
export function isApiSuccess({ ok, data }) {
  if (!ok) return false
  const code = data?.code
  if (code == null) return true
  return code === 200 || code === 0
}
