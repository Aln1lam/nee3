import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'      
import router from './router' 

// 引入字体
import 'vfonts/Lato.css'
import 'vfonts/FiraCode.css'
// 全局样式：提供 rem 基准和 box-sizing
import './assets/global.css'
// FullCalendar theme overrides
import './assets/fullcalendar-theme.css'
// Global theme switch overrides removed — app uses single light theme
// Component-level utilities (edge-avatar, edge-tag, btn-neon, etc.)
import './assets/components.css'
// 在应用入口全局注入 Vditor 的 svg icons sprite，保证 <symbol id="vditor-icon-..."> 在组件挂载前可用
import 'vditor/dist/js/icons/material.js'

// 设置后端地址
// 开发环境使用相对路径走 Vite 代理，生产环境可通过 VITE_API_BASE 指定
axios.defaults.baseURL = import.meta.env.DEV
    ? ''
    : (import.meta.env.VITE_API_BASE || '')

// Allow sending cookies (for cookie-based auth / SSE)
axios.defaults.withCredentials = true

// Token 处理：每次刷新页面，自动从 localStorage 读取 Token 放到请求头里
const savedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('neepu_token') : null
if (savedToken) {
    axios.defaults.headers.common['Authorization'] = 'Bearer ' + savedToken
}

// Ensure every request includes Authorization header from localStorage (in case it changes at runtime)
axios.interceptors.request.use(config => {
    try {
        const t = localStorage.getItem('neepu_token')
        if (t) config.headers = config.headers || {}, config.headers['Authorization'] = 'Bearer ' + t
    } catch (e) {}
    return config
}, err => Promise.reject(err))

// 通知应用：鉴权头已在启动时设置（供组件在需要时监听）
try { window.dispatchEvent(new Event('neepu_auth_ready')) } catch (e) {}

// 初始化通知服务（SSE 或轮询） — 在 axios 已有鉴权头后启动
// notifications service removed: feature deprecated and cleaned up

// 拦截器：Token 失效(401)时自动跳回登录页
axios.interceptors.response.use(
    resp => resp,
    err => {
        if (err.response && err.response.status === 401) {
            try {
                // 清除过期 Token
                localStorage.removeItem('neepu_token')
                localStorage.removeItem('neepu_user')
            } catch (e) {}
            
            // 核心修改：使用 router 跳转，而不是暴力刷新页面
            // 这样能保持页面状态，体验更丝滑
            if (router) {
                router.push('/auth')
            } else {
                window.location.href = '/auth'
            }
        }
        return Promise.reject(err)
    }
)

const app = createApp(App)

app.use(router) // 3. 关键：挂载路由！没有这一行 App.vue 里的 <router-view> 就会报错
app.provide('axios', axios) // 全局注入 axios
app.mount('#app')

// 如果页面刷新时已经有 token，尝试刷新用户信息（以确保 is_admin 等字段是最新的）
try {
    const saved = localStorage.getItem('neepu_user')
    const savedToken = localStorage.getItem('neepu_token')
    if (savedToken && saved) {
        try {
            const parsed = JSON.parse(saved)
            const uid = parsed && parsed.id
            if (uid) {
                // 请求后端最新的用户信息并写回 localStorage
                axios.get('/api/auth/me', { params: { id: uid } }).then(r => {
                    if (r && r.data) {
                        // r.data contains user details
                        localStorage.setItem('neepu_user', JSON.stringify(r.data))
                        // optional: reload app state by dispatching a custom event
                        window.dispatchEvent(new Event('neepu_user_refreshed'))
                    }
                }).catch(() => {/* ignore */})
            }
        } catch (e) { /* ignore json parse */ }
    }
} catch (e) { /* ignore storage errors */ }