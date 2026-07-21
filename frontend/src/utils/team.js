/** 统一解析 /api/teams/me 响应（兼容扁平结构与 { team } 包装） */
export function unwrapTeamResponse(payload) {
  if (!payload || typeof payload !== 'object') return null
  const team = payload.team ?? payload.data?.team ?? payload
  if (!team || typeof team !== 'object') return null
  if (!team.id && !team.name) return null
  return team
}

/** 解析创建队伍响应中的邀请码 */
export function unwrapTeamInvite(payload) {
  if (!payload || typeof payload !== 'object') return ''
  return (
    payload.invite_code
    || payload.data?.invite_code
    || payload.data?.inviteCode
    || ''
  )
}
