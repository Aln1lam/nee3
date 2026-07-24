/**
 * 题目侧 API — hints / hammer / submit（与 container.js 同层）
 */
import http from './http'

export async function getHints(challengeId) {
  const { data } = await http.get(`/api/challenges/${challengeId}/hints`)
  return data
}

/** hintId 为提示主键，非题目 id */
export async function accessHint(hintId) {
  const { data } = await http.post(`/api/challenges/${hintId}/access-hint`)
  return data
}

export async function getHammer(challengeId) {
  const { data } = await http.get(`/api/challenges/${challengeId}/hammer`)
  return data
}

export async function postHammer(challengeId, content) {
  const { data } = await http.post(`/api/challenges/${challengeId}/hammer`, { content })
  return data
}

export async function submitFlag(challengeId, flag, extra = {}) {
  const { data } = await http.post(`/api/challenges/${challengeId}/submit`, {
    flag,
    answer: flag,
    ...extra,
  })
  return data
}

/** 当前用户（或队伍）在某题的提交历史 */
export async function getMySubmissions(challengeId) {
  const { data } = await http.get(`/api/challenges/${challengeId}/submissions`)
  return data
}

export default {
  getHints,
  accessHint,
  getHammer,
  postHammer,
  submitFlag,
  getMySubmissions,
}
