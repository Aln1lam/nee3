/**
 * 将上传/头像路径解析为可请求的 URL。
 * 开发环境 /api 路径保持相对地址，经 Vite 代理转发并携带 HttpOnly Cookie。
 */
export function normalizeUploadPath(path) {
  if (!path) return ''
  if (path.startsWith('data:')) return path
  if (/^https?:\/\//i.test(path)) {
    try {
      return new URL(path).pathname
    } catch {
      const match = path.match(/\/static\/uploads\/[^?#]+/)
      return match ? match[0] : path
    }
  }
  if (path.startsWith('static/')) return '/' + path
  return path
}

/**
 * @param {string} avatarPath
 * @param {string|number|null} [cacheKey] optional stable bust key (e.g. updated_at).
 *   Do NOT pass Date.now() from computed — that reloads images every re-render.
 */
export function resolveUploadUrl(avatarPath, cacheKey = null) {
  if (!avatarPath) return ''
  if (avatarPath.startsWith('data:')) return avatarPath

  let normalized = normalizeUploadPath(avatarPath)
  if (normalized.startsWith('static/')) normalized = '/' + normalized
  if (normalized.startsWith('/static/uploads/')) {
    normalized = '/api/uploads/serve/' + normalized.slice('/static/uploads/'.length)
  } else if (normalized.startsWith('/uploads/')) {
    normalized = '/api/uploads/serve/' + normalized.slice('/uploads/'.length)
  } else if (normalized.startsWith('uploads/')) {
    normalized = '/api/uploads/serve/' + normalized.slice('uploads/'.length)
  }

  const bust = cacheKey != null && cacheKey !== '' ? `?t=${encodeURIComponent(String(cacheKey))}` : ''

  // 前端 public 静态资源（如头像占位图）走同源，勿拼后端 API 地址
  if (normalized.startsWith('/assets/')) {
    return normalized + bust
  }

  if (normalized.startsWith('/api/')) {
    return normalized + bust
  }

  const assetBase = (import.meta.env?.VITE_API_BASE || '').replace(/\/$/, '')
  if (normalized.startsWith('/')) {
    return (assetBase || '') + normalized + bust
  }
  return normalized + bust
}
