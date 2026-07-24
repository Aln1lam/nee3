/**
 * 容器实例 API（主路径优先，兼容旧 /api/container/*）
 * 对照 docs/ret2shell-adoption-checklist.md · B01 / F06
 *
 * 主路径：/api/challenges/* · 兼容回退：/api/container/*（将弃用）
 */
import http from './http'

/** 从 status / start 响应中取出运行中的实例；无实例则返回 null */
export function pickRunningInstance(payload) {
  const d = payload?.data ?? payload ?? {}
  if (d.has_container === false || d.status === 'no_container' || d.status === 'expired') {
    return null
  }
  if (payload?.success && payload?.data && !d.status) {
    return payload.data
  }
  if (d.has_container || d.status === 'running' || d.instance_id || d.id) {
    return {
      ...d,
      instance_id: d.instance_id ?? d.id,
    }
  }
  return null
}

export async function getContainerStatus(challengeId) {
  const { data } = await http.get(`/api/challenges/${challengeId}/container-status`)
  return data
}

export async function startContainer(challengeId, { asyncMode = true } = {}) {
  try {
    const { data } = await http.post(`/api/challenges/${challengeId}/start-container`, { async: asyncMode })
    return data
  } catch (e) {
    // 202 Accepted 也算成功（axios 默认把 2xx 当成功；若拦截器特殊处理则回退）
    if (e?.response?.status === 202) return e.response.data
    try {
      const { data } = await http.post(`/api/container/start/${challengeId}`)
      return data
    } catch (e2) {
      throw e2
    }
  }
}

export async function getContainerJob(jobId) {
  const { data } = await http.get(`/api/challenges/container-jobs/${jobId}`)
  return data
}

export async function getInstanceLogs(instanceId, tail = 200) {
  const { data } = await http.get(`/api/challenges/instances/${instanceId}/logs`, { params: { tail } })
  return data
}

export async function stopContainer(instanceId) {
  try {
    const { data } = await http.post(`/api/challenges/instances/${instanceId}/stop`)
    return data
  } catch {
    const { data } = await http.post(`/api/container/stop/${instanceId}`)
    return data
  }
}

export async function extendContainer(instanceId) {
  try {
    const { data } = await http.post(`/api/challenges/instances/${instanceId}/extend`)
    return data
  } catch {
    const { data } = await http.post(`/api/container/extend/${instanceId}`)
    return data
  }
}

export default {
  getContainerStatus,
  startContainer,
  stopContainer,
  extendContainer,
  pickRunningInstance,
}
