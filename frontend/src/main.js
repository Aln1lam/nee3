import { createApp } from 'vue'

import App from './App.vue'

import axios from 'axios'

import router from './router'



import 'vfonts/FiraCode.css'

import './assets/global.css'

import './assets/typography.css'

import './assets/layout-proportions.css'

import './assets/fullcalendar-theme.css'

import './assets/components.css'

import './assets/neepu-matrix.css'

import './assets/linux-ui.css'

import './assets/admin-matrix.css'

import './assets/gradient-system.css'

import './assets/collapsible-sidebar.css'

import './assets/fullwidth-layout.css'

import './assets/ret2shell-v3.css'

import './assets/golden-ratio.css'   // φ layout last — wins over theme chrome

import 'vditor/dist/js/icons/material.js'



import { initTheme } from './stores/theme'

import { loadPlatform } from './stores/platform'

import { clearUser, fetchSession } from './services/auth'



initTheme()



axios.defaults.baseURL = import.meta.env.DEV

    ? ''

    : (import.meta.env.VITE_API_BASE || '')



axios.defaults.withCredentials = true

try {
  delete axios.defaults.headers.common['Authorization']
} catch { /* ignore */ }

function readCookie(name) {
  const hit = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))
  if (!hit) return ''
  return decodeURIComponent(hit.split('=').slice(1).join('='))
}

axios.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrf = readCookie('csrf_access_token')
    if (csrf) {
      config.headers = config.headers || {}
      config.headers['X-CSRF-TOKEN'] = csrf
    }
  }
  return config
})



function clearAuthState() {

    clearUser()

}



const PUBLIC_ROUTE_NAMES = new Set([

    'Landing', 'Auth', 'VerifyEmail', 'ForgotPassword', 'ResetPassword',

    'Wiki', 'WikiArticle', 'Archive', 'Bulletin', 'GamesHub', 'GameDetail',

    'Training', 'TrainingGame', 'HttpError',

    'BulletinDetail', 'UserList', 'UserProfile', 'GameScoreboard',

])



function routeRequiresAuth() {

    const route = router?.currentRoute?.value

    if (!route) return false

    if (route.meta?.requiresAuth) return true

    return route.name ? !PUBLIC_ROUTE_NAMES.has(route.name) : false

}



axios.interceptors.response.use(

    resp => resp,

    err => {

        const status = err.response?.status

        if (status === 401) {

            const cfg = err.config || {}

            const skipClear = cfg._skipAuthClear === true

            const authCritical = cfg._authCritical === true



            if (!skipClear && (authCritical || routeRequiresAuth())) {

                clearAuthState()

                const path = router?.currentRoute?.value?.path || ''

                if (routeRequiresAuth() && path && !path.startsWith('/auth') && !path.startsWith('/account')) {

                    if (router) router.push({ path: '/auth', query: { redirect: path } })

                    else window.location.href = '/auth'

                }

            }

        } else if (status === 502) {

            if (router) router.push('/error/502')

        } else if (status === 503) {

            try {

                const msg = err.response?.data?.msg || err.response?.data?.message

                window.dispatchEvent(new CustomEvent('neepu_maintenance', {
                    detail: { status, maintenance_message: msg },
                }))

            } catch { /* ignore */ }

        }

        return Promise.reject(err)

    }

)



const app = createApp(App)



app.use(router)

app.provide('axios', axios)

app.mount('#app')

loadPlatform().catch(() => null)
fetchSession().catch(() => null)


