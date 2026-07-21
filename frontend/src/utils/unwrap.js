/**
 * 统一解析后端多种响应格式：
 * - { code: 200, data: [...] }
 * - { code: 0, data: { items: [...] } }
 * - { data: { rankings: [...] } }
 * - 裸数组 / 裸对象
 */

export function unwrapData(payload) {
  if (payload == null) return null
  if (Array.isArray(payload)) return payload
  if (typeof payload !== 'object') return payload

  if (Object.prototype.hasOwnProperty.call(payload, 'data')) {
    const inner = payload.data
    if (inner == null) return null
    if (typeof inner === 'object' && !Array.isArray(inner)) {
      if (Array.isArray(inner.items)) return inner.items
      if (Array.isArray(inner.rankings)) return inner.rankings
      if (Array.isArray(inner.series)) return inner.series
    }
    return inner
  }

  if (Array.isArray(payload.items)) return payload.items
  if (Array.isArray(payload.rankings)) return payload.rankings
  return payload
}

export function unwrapList(payload) {
  const data = unwrapData(payload)
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items
    if (Array.isArray(data.rankings)) return data.rankings
  }
  return []
}

export function unwrapObject(payload) {
  const data = unwrapData(payload)
  if (data && typeof data === 'object' && !Array.isArray(data)) return data
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const { data: _d, code: _c, msg: _m, message: _msg, ...rest } = payload
    if (Object.keys(rest).length) return rest
  }
  return null
}
