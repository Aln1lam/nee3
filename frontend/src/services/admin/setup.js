/**
 * 管理员引导 / 调试 API (/api/admin)
 * 仅用于首次安装、身份检查等 bootstrap 场景。
 */
import axios from 'axios'

const http = axios.create({
  baseURL: '/api/admin',
  withCredentials: true,
})

const setupAdmin = {
  checkCurrentUser() {
    return http.get('/check-current-user')
  },

  setFirstUserAdmin() {
    return http.post('/set-admin-first-user')
  },

  searchUser(nickname) {
    return http.get(`/search-user/${encodeURIComponent(nickname)}`)
  },

  /** 遗留 PATCH 路径，新代码优先用 platformAdmin.updateUser */
  setUserAdmin(userId, isAdmin = true) {
    return http.patch(`/users/${userId}`, { is_admin: isAdmin })
  },
}

export default setupAdmin
