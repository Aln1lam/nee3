/**
 * 平台实例列表 + 容器操作（供 InstanceBox / Workspace）
 */
import http from './http'
import {
  getContainerStatus,
  startContainer,
  stopContainer,
  extendContainer,
} from './container'

export async function listMyInstances() {
  const { data } = await http.get('/api/platform/instances')
  return data
}

export {
  getContainerStatus,
  startContainer,
  stopContainer,
  extendContainer,
}

export default {
  listMyInstances,
  getContainerStatus,
  startContainer,
  stopContainer,
  extendContainer,
}
