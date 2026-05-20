import axios from 'axios'

function getAuthHeaders() {
  const token = localStorage.getItem('neepu_token') || localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const api = axios.create({
  baseURL: '/api/admin/platform'
})

export default {
    
  getDashboard() {
    return api.get('/dashboard', { headers: getAuthHeaders() })
  },

  listUsers(params) {
    return api.get('/users', { params, headers: getAuthHeaders() })
  },

  updateUser(id, data) {
    return api.patch(`/users/${id}`, data, { headers: getAuthHeaders() })
  },

  deleteUser(id) {
    return api.delete(`/users/${id}`, { headers: getAuthHeaders() })
  },

  listArticles(params) {
    return api.get('/articles', { params, headers: getAuthHeaders() })
  },

  updateArticle(id, data) {
    return api.patch(`/articles/${id}`, data, { headers: getAuthHeaders() })
  },

  deleteArticle(id) {
    return api.delete(`/articles/${id}`, { headers: getAuthHeaders() })
  },

  getLogs(params) {
    return api.get('/logs', { params, headers: getAuthHeaders() })
  },

  getLogsStats() {
    return api.get('/logs/stats', { headers: getAuthHeaders() })
  },

  deleteLog(id) {
    return api.delete(`/logs/${id}`, { headers: getAuthHeaders() })
  },

  deleteLogsByMonths(startMonth, endMonth, dryRun = false) {
    return api.post('/logs/delete-by-months', { start_month: startMonth, end_month: endMonth, dry_run: dryRun }, { headers: getAuthHeaders() })
  },

  getLogMonths() {
    return api.get('/logs/months', { headers: getAuthHeaders() })
  },

  getConfig() {
    return api.get('/config')
  },

  updateConfig(data) {
    return api.patch('/config', data, { headers: getAuthHeaders() })
  },

  initConfig() {
    return api.post('/config/init', null, { headers: getAuthHeaders() })
  },

  testEmail(email) {
    return api.post('/test-email', { email }, { headers: getAuthHeaders() })
  },

  getAnnouncements() {
    return api.get('/announcements', { headers: getAuthHeaders() })
  },

  createAnnouncement(data) {
    return api.post('/announcements', data, { headers: getAuthHeaders() })
  },

  updateAnnouncement(id, data) {
    return api.patch(`/announcements/${id}`, data, { headers: getAuthHeaders() })
  },

  deleteAnnouncement(id) {
    return api.delete(`/announcements/${id}`, { headers: getAuthHeaders() })
  },

  distributeTodos(data) {
    return api.post('/distribute-todos', data, { headers: getAuthHeaders() })
  },

  getCarousel() {
    return api.get('/carousel', { headers: getAuthHeaders() })
  },

  createCarouselSlide(data) {
    return api.post('/carousel', data, { headers: getAuthHeaders() })
  },

  updateCarouselSlide(id, data) {
    return api.patch(`/carousel/${id}`, data, { headers: getAuthHeaders() })
  },

  deleteCarouselSlide(id) {
    return api.delete(`/carousel/${id}`, { headers: getAuthHeaders() })
  }
}
