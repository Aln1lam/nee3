/**
 * 平台运维 API — 唯一入口 (/api/admin/platform)
 * 组件请通过本模块或 @/services/admin/platform 访问，勿硬编码路径。
 */
import axios from 'axios'

const http = axios.create({
  baseURL: '/api/admin/platform',
  withCredentials: true,
})

const platformAdmin = {
  getDashboard() {
    return http.get('/dashboard')
  },

  getArticlesDistribution() {
    return http.get('/stats/articles-distribution')
  },

  getTopActiveUsers() {
    return http.get('/stats/top-active-users')
  },

  listUsers(params) {
    return http.get('/users', { params })
  },

  updateUser(id, data) {
    return http.patch(`/users/${id}`, data)
  },

  deleteUser(id) {
    return http.delete(`/users/${id}`)
  },

  listArticles(params) {
    return http.get('/articles', { params })
  },

  updateArticle(id, data) {
    return http.patch(`/articles/${id}`, data)
  },

  deleteArticle(id) {
    return http.delete(`/articles/${id}`)
  },

  getLogs(params) {
    return http.get('/logs', { params })
  },

  getLogsStats() {
    return http.get('/logs/stats')
  },

  deleteLog(id) {
    return http.delete(`/logs/${id}`)
  },

  deleteLogsByMonths(startMonth, endMonth, dryRun = false) {
    return http.post('/logs/delete-by-months', {
      start_month: startMonth,
      end_month: endMonth,
      dry_run: dryRun,
    })
  },

  getLogMonths() {
    return http.get('/logs/months')
  },

  getConfig() {
    return http.get('/config')
  },

  updateConfig(data) {
    return http.patch('/config', data)
  },

  getUiConfig() {
    return http.get('/config/ui')
  },

  updateUiConfig(data) {
    return http.patch('/config/ui', data)
  },

  getEnv() {
    return http.get('/env')
  },

  updateEnv(updates) {
    return http.post('/env', { updates })
  },

  initConfig() {
    return http.post('/config/init')
  },

  testEmail(email) {
    return http.post('/test-email', { email })
  },

  getAnnouncements() {
    return http.get('/announcements')
  },

  createAnnouncement(data) {
    return http.post('/announcements', data)
  },

  updateAnnouncement(id, data) {
    return http.patch(`/announcements/${id}`, data)
  },

  deleteAnnouncement(id) {
    return http.delete(`/announcements/${id}`)
  },

  getCarousel() {
    return http.get('/carousel')
  },

  createCarouselSlide(data) {
    return http.post('/carousel', data)
  },

  updateCarouselSlide(id, data) {
    return http.patch(`/carousel/${id}`, data)
  },

  deleteCarouselSlide(id) {
    return http.delete(`/carousel/${id}`)
  },

  /** 图片上传（轮播等），配合 n-upload with-credentials 使用 */
  uploadImageUrl: '/api/uploads/upload-image/',
}

export default platformAdmin
