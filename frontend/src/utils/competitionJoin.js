/**
 * 校内赛 / 公开赛报名约定：
 * - is_public === false → 校内赛：需邀请码；组织固定为东电
 * - is_public === true  → 公开赛：无需码；所属组织必填本校全称
 */

export const CAMPUS_ORG = '东北电力大学'

export function gameNeedsInvite(game) {
  if (!game || typeof game !== 'object') return false
  return game.is_public === false || game.is_public === 0
}

export function gameIsOpenPublic(game) {
  if (!game || typeof game !== 'object') return true
  return game.is_public !== false && game.is_public !== 0
}

export function normalizeOrgForSave(school, { campus } = {}) {
  if (campus) return CAMPUS_ORG
  const s = String(school || '').trim()
  return s
}

export function validateOrgInput(school, { campus } = {}) {
  if (campus) return { ok: true, value: CAMPUS_ORG }
  const s = String(school || '').trim()
  if (!s || s === '无组织') {
    return { ok: false, msg: '公开赛请填写所属大学全称' }
  }
  if (s.length > 128) {
    return { ok: false, msg: '所属组织过长（最多 128 字）' }
  }
  return { ok: true, value: s }
}
