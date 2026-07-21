/** Filter out E2E / API-probe competitions that leaked into the public list. */

const EPHEMERAL_TITLE_RE = /(流量捕获|容器生命周期|E2E\s*全链路|CaptureTest|AutoTest|API\s*Test\s*Game|EndpointSweep|Signup容器|全链路测试)/i
const TIMESTAMP_SUFFIX_RE = /(?:\s|_)\d{6,}$/

export function isEphemeralTestTitle(title) {
  const t = String(title || '').trim()
  if (!t || t.length <= 2) return true
  if (EPHEMERAL_TITLE_RE.test(t)) return true
  if (TIMESTAMP_SUFFIX_RE.test(t)) return true
  return false
}

export function isEphemeralTestGame(g) {
  return isEphemeralTestTitle(g?.title)
}

export function filterPublicGames(list) {
  return (list || []).filter((g) => !isEphemeralTestGame(g))
}
