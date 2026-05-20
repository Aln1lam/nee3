<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
      
      <div class="geometric-bg">
        <div class="hex-grid"></div>
      </div>

        <!-- Top navigation with logo and menu (full-width header placed outside centered container) -->

      <header class="top-nav" v-if="!isAdminRoute">
        <div class="nav-inner">
          <div class="brand" @click="$router.push('/home')">
            <img src="/assets/logo.svg" alt="logo" class="brand-logo" v-if="logoExists" />
            <span class="brand-text">NEEPU CTF</span>
          </div>

          <nav class="nav-menu">
            <a v-if="user && user.is_admin" @click.prevent="$router.push('/admin')">仪表盘</a>
            <a @click.prevent="$router.push('/home')">Home</a>
            <a @click.prevent="$router.push('/knowledge')">知识</a>
            <a @click.prevent="$router.push('/ctf')">赛事</a>
            <a @click.prevent="$router.push('/teams')">队伍</a>
            <a @click.prevent="$router.push('/archive')">公告</a>
          </nav>

          <div class="nav-actions">
            <template v-if="user">
              <n-dropdown :options="userMenuOptions" @select="onUserMenuSelect" trigger="click" :key="userKey">
                <template #default>
                  <n-button size="small">
                    <template v-if="user && user.avatar">
                      <n-avatar size="small" style="margin-right:6px" :src="getAvatarUrl(user.avatar)"></n-avatar>
                    </template>
                    <template v-else>
                      <n-avatar size="small" color="var(--avatar-light)" style="margin-right:6px">{{ (user.nickname||'用户').slice(0,1) }}</n-avatar>
                    </template>
                    {{ user.nickname || '用户' }}
                  </n-button>
                </template>
              </n-dropdown>
            </template>
            <template v-else>
              <n-button size="small" @click="openAuthRoute">登录 / 注册</n-button>
            </template>
          </div>
        </div>
      </header>

      <div class="app-container" :class="{ 'admin-mode': isAdminRoute }">

        <!-- (Carousel moved into Home page) -->

        <!-- features removed permanently -->

        <!-- dynamic routed content (pages) -->
        <main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" @logged="onLogged" @open-scoreboard="onOpenScoreboard" @open-games="openGames" />
            </transition>
          </router-view>
        </main>

        <!-- Notifications modal (existing) -->
        <notifications-center v-model:show="showNotifications" v-if="showNotifications" @close="showNotifications=false" />

        <footer class="site-footer">
          <div class="footer-inner">
            <div>© 2022 - 2025 NEEPUSEC • 东北电力大学</div>
            <div class="footer-links"><a @click.prevent="$router.push('/archive')">公告</a> · <a href="#">关于</a></div>
          </div>
        </footer>
      </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script>
import { ref, computed, watch, inject, onMounted, onUnmounted } from 'vue'
import BaseModal from './components/BaseModal.vue'
import { useRouter, useRoute } from 'vue-router'
import { NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider, NButton, NSpace, NDivider, NDropdown, NAvatar } from 'naive-ui'

export default {
  components: { 
    NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider, NButton, NSpace, NDivider, NDropdown, NAvatar
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const user = ref(null)
    const logoExists = ref(true)

      // teams dropdown removed — navigation goes directly to /teams
    // 判断是否在管理后台路由
    const isAdminRoute = computed(() => {
      return route.path.startsWith('/admin')
    })

    // 检查用户登录状态
    function checkUser() {
      try { 
        const u = localStorage.getItem('neepu_user')
        user.value = u ? JSON.parse(u) : null
      } catch (e) { user.value = null }
    }
    
    // 监听路由变化，如果去 Auth 页面说明可能登出了，反之检查用户
  watch(() => route.path, () => checkUser(), { immediate: true })

  // 当 main.js 在启动时刷新用户信息后，会 dispatch 一个事件 'neepu_user_refreshed'
  // 我们在这里监听该事件以刷新头部显示（例如 is_admin 标志）
    function onUserRefreshed() { checkUser() }
    onMounted(() => {
      window.addEventListener('neepu_user_refreshed', onUserRefreshed)
    })
  onUnmounted(() => {
    window.removeEventListener('neepu_user_refreshed', onUserRefreshed)
  })

    const userKey = computed(() => {
      try {
        return user.value ? `${user.value.id}|${user.value.avatar||''}` : 'anon'
      } catch (e) { return 'anon' }
    })

    function onLogged() {
      checkUser()
      updateUserMenu() // 登录成功后更新菜单
      router.push('/home') // 登录成功跳去首页
    }

  // notifications feature removed
    // user menu
    const userMenuOptions = ref([
      { label: '个人资料', key: 'profile' },
      { type: 'divider' },
      { label: '退出', key: 'logout' }
    ])

    // 检查是否是管理员，如果是则添加管理后台选项
    function updateUserMenu() {
      const userStr = localStorage.getItem('neepu_user')
      if (userStr) {
        try {
          const userData = JSON.parse(userStr)
          if (userData.is_admin) {
            userMenuOptions.value = [
              { label: '个人资料', key: 'profile' },
              { type: 'divider' },
              { label: '🔧 管理后台', key: 'admin' },
              { type: 'divider' },
              { label: '退出', key: 'logout' }
            ]
            return
          }
        } catch (e) {}
      }
      userMenuOptions.value = [
        { label: '个人资料', key: 'profile' },
        { type: 'divider' },
        { label: '退出', key: 'logout' }
      ]
    }

    // theme switching removed — site uses the light theme only

    const axios = inject('axios')
    function getAvatarUrl(avatarPath) {
      if (!avatarPath) return null
      if (avatarPath.startsWith('data:')) return avatarPath
      if (/^https?:\/\//i.test(avatarPath)) return avatarPath + '?t=' + Date.now()
      try {
        if (avatarPath.startsWith('/')) {
          const assetBase = (import.meta.env && import.meta.env.VITE_API_BASE)
            ? import.meta.env.VITE_API_BASE.replace(/\/$/, '')
            : (import.meta.env && import.meta.env.DEV ? 'http://127.0.0.1:5000' : '')
          if (avatarPath.startsWith('/static/')) {
            return (assetBase ? assetBase : '') + avatarPath + '?t=' + Date.now()
          }
          const base = (axios && axios.defaults && axios.defaults.baseURL) ? axios.defaults.baseURL.replace(/\/$/, '') : ''
          return (base ? base : '') + avatarPath + '?t=' + Date.now()
        }
      } catch (e) {}
      return avatarPath + '?t=' + Date.now()
    }

    

    const pressed = ref(false)
    // theme switching removed

    function logout() {
      localStorage.removeItem('neepu_token')
      localStorage.removeItem('neepu_user')
      user.value = null
      try { router.push('/auth') } catch (e) {}
    }

    // handle dropdown select (naive-ui passes option object or key depending on usage)
    function onUserMenuSelect(option) {
      // option may be { label, key } or just key string
      const key = typeof option === 'string' ? option : (option && option.key)
      if (!key) return
      if (key === 'profile') router.push('/myprofile')
      else if (key === 'admin') router.push('/admin')
      else if (key === 'logout') logout()
    }

    function go(path) {
      router.push(path)
    }

    function onOpenScoreboard(gameId) {
      if (gameId) router.push(`/scoreboard/${gameId}`)
    }

    function openAuthRoute() {
      // 使用路由跳转到 /auth，Auth.vue 会根据路由打开模态
      try { router.push('/auth') } catch (e) { console.warn('router push /auth failed', e) }
    }

    function openGames() {
      try { router.push('/games') } catch (e) { console.warn('openGames push failed', e) }
    }

  // carousel moved into Home.vue
  onMounted(() => {
    checkUser() // 加载用户信息
    updateUserMenu() // 更新菜单
  })

    // UI state
    const showNotifications = ref(false)
  onUnmounted(() => { /* cleanup */ })

    // Use CSS variables for theme overrides so public/themes/*.css controls colors
    const themeOverrides = ref({})
    function readVar(name, fallback) {
      try { const v = getComputedStyle(document.documentElement).getPropertyValue(name); return v ? v.trim() : fallback } catch (e) { return fallback }
    }
    onMounted(() => {
      themeOverrides.value = {
        common: {
          primaryColor: readVar('--primary', '#333333'),
          primaryColorHover: readVar('--primary-hover', '#555555'),
          bodyColor: 'transparent',
          textColorBase: readVar('--text', '#333333')
        },
        Button: {
          textColorText: readVar('--muted', '#555555'),
          textColorTextHover: readVar('--text', '#000000'),
          fontWeight: 'bold'
        },
        Card: {
          borderRadius: '2px',
          borderColor: readVar('--border', '#e0e0e0'),
          color: readVar('--text', '#000000'),
          colorTarget: 'rgba(255, 255, 255, 0.3)',
          colorEmbedded: 'rgba(255, 255, 255, 0.3)'
        }
      }
    })

    return { themeOverrides, user, logout, onLogged, go, router, route, onOpenScoreboard, openAuthRoute, openGames,
      logoExists, isAdminRoute,
      userMenuOptions, onUserMenuSelect, updateUserMenu,
      showNotifications,
      getAvatarUrl, userKey
    }
  }
}
</script>
<style>
/* Load local LxgWenKai font (place ttf files under frontend/public/fonts/) */
@font-face {
  font-family: 'LXGWWenKai';
  src: url('/fonts/LXGWWenKai-Regular.ttf') format('truetype');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'LXGWWenKai';
  src: url('/fonts/LXGWWenKai-Medium.ttf') format('truetype');
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}
/* fallback to system monospace for code areas */
code, pre, .code, .monospace { font-family: 'Fira Code', monospace; }

/* Apply sensible base fonts - use LXGWWenKai for all UI */
html, body, #app { font-family: 'LXGW WenKai', 'Fira Code', 'Helvetica Neue', Arial, sans-serif; }

/* Force the branding/title to use LXGW WenKai so Chinese heading looks correct */
.brand, .bracket-title, .title-text {
  font-family: 'LXGW WenKai', 'Fira Code', sans-serif !important;
  font-weight: 500;
  font-style: normal;
}

/* 1. 柔和绿蓝背景 (仿西电) */
.geometric-bg {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background-color: var(--page-bg);
  z-index: -1;
  /* 使用 CSS 渐变模拟微细纹理 */
  background-image: 
    linear-gradient(var(--grain-1, rgba(255,255,255,0.5)) 2px, transparent 2px),
    linear-gradient(90deg, var(--grain-1, rgba(255,255,255,0.5)) 2px, transparent 2px),
    linear-gradient(var(--grain-2, rgba(255,255,255,0.2)) 1px, transparent 1px),
    linear-gradient(90deg, var(--grain-2, rgba(255,255,255,0.2)) 1px, transparent 1px);
  background-size: 100px 100px, 100px 100px, 20px 20px, 20px 20px;
  background-position: -2px -2px, -2px -2px, -1px -1px, -1px -1px;
  overflow: hidden;
}

/* 校标水印 - 中心固定到屏幕右下角旋转 */
.geometric-bg::before {
  content: '';
  position: fixed;
  width: 2400px;
  height: 2400px;
  right: -1200px;
  bottom: -1200px;
  background-image: url('/assets/055ff5752ef441e4ebe3516f6773fd73.png');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.2;
  pointer-events: none;
  transform-origin: center;
  animation: rotateSchool 120s linear infinite;
}

@keyframes rotateSchool {
  from { transform: rotate(0deg); }
  to { transform: rotate(-360deg); }
}
.nav-item.active {
  color: var(--primary) !important; /* 选中时使用主题主色 */
  font-weight: 900;
}
/* 装饰性六边形 (可选，为了增加科技感) */
.hex-grid {
  position: absolute;
  top: 0; right: 0; bottom: 0; left: 0;
  background: 
    radial-gradient(circle at 10% 20%, var(--radial-accent, rgba(200,220,230,0.3)) 0%, transparent 20%),
    radial-gradient(circle at 90% 80%, var(--radial-accent, rgba(200,220,230,0.3)) 0%, transparent 20%);
}

.app-container {
  max-width: none;
  width: 100%;
  padding: 0 20px;
  box-sizing: border-box;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 管理后台模式：移除padding，让管理面板占满全屏 */
.app-container.admin-mode {
  padding: 0;
  margin: 0;
}

.minimal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--minimal-header-padding);
  /* 无背景色，直接透出底色 */
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--brand-gap);
  font-family: 'Fira Code', monospace;
  font-weight: 700;
  font-size: var(--brand-font-size);
  color: var(--text);
}
.brand .icon { color: var(--primary); }

.nav-item {
  font-size: var(--nav-item-font-size);
  color: var(--muted);
  transition: color 0.3s;
}
.nav-item:hover { color: var(--text); }

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 3. 极简底部 */
.minimal-footer {
  text-align: center;
  padding: 20px;
  font-size: 12px;
  color: var(--muted);
  font-family: sans-serif;
  letter-spacing: 1px;
}
.geometric-bg {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background-color: var(--page-bg);
  z-index: -1;
  background-image: 
    linear-gradient(var(--grain-1, rgba(255,255,255,0.5)) 2px, transparent 2px),
    linear-gradient(90deg, var(--grain-1, rgba(255,255,255,0.5)) 2px, transparent 2px),
    linear-gradient(var(--grain-2, rgba(255,255,255,0.2)) 1px, transparent 1px),
    linear-gradient(90deg, var(--grain-2, rgba(255,255,255,0.2)) 1px, transparent 1px);
  background-size: 100px 100px, 100px 100px, 20px 20px, 20px 20px;
  background-position: -2px -2px, -2px -2px, -1px -1px, -1px -1px;
}
.app-container { max-width: none; width:100%; padding:0 20px; box-sizing:border-box; min-height: 100vh; display: flex; flex-direction: column; }
.minimal-header { display: flex; justify-content: space-between; align-items: center; padding: var(--minimal-header-padding); }
.brand { display: flex; align-items: center; gap: var(--brand-gap); font-family: 'Fira Code', monospace; font-weight: 700; font-size: var(--brand-font-size); color: var(--text); }
.nav-item { font-size: var(--nav-item-font-size); color: var(--muted); transition: color 0.3s; }
.nav-item:hover { color: var(--text); }
.main-content { flex: 1; display: flex; flex-direction: column; }
.minimal-footer { text-align: center; padding: 20px; font-size: 12px; color: var(--muted); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
/* subtle global grain to give the UI more texture */
body::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: -1;
  background-image: radial-gradient(rgba(0,0,0,0.01) 1px, transparent 1px);
  background-size: 18px 18px;
  opacity: 0.6;
}

.top-nav { background: var(--nav-bg); border-bottom: 1px solid var(--border); width:100%; position:sticky; top:0; z-index:60; box-shadow: var(--shadow, 0 1px 6px rgba(10,20,40,0.06)); backdrop-filter: blur(6px) }
  .nav-inner { max-width:var(--content-max-width); margin:0 auto; display:flex; align-items:center; justify-content:space-between; padding:var(--nav-inner-padding); min-height:var(--nav-height); }
.brand { display:flex; align-items:center; gap:var(--brand-gap); cursor:pointer }
.brand-logo { height:var(--brand-logo-height) }
.brand-text { font-weight:700; font-size: var(--brand-text-size) }
  .nav-menu { display:flex; gap:var(--nav-gap); align-items:center; font-size: var(--nav-font-size, 0.95rem) }
.nav-menu a { color:var(--text); text-decoration:none; padding:var(--nav-padding-y) var(--nav-padding-x); border-radius:calc(var(--nav-padding-y) * 1.2); font-weight:500; transition: color .15s, background .15s }
.nav-menu a:hover { background: var(--hover, rgba(0,0,0,0.04)); color: var(--text) }
.nav-menu a.active { color: var(--primary); font-weight:700 }
.nav-actions { display:flex; gap:var(--nav-gap-small); align-items:center }
/* tighten action button appearance to match reference */
.nav-actions .icon-btn, .nav-actions .n-button { padding:var(--nav-padding-y) var(--nav-padding-x) }

/* Enforce nav sizing when other styles try to override */
.top-nav, .nav-inner { min-height: var(--nav-height); }
.brand-logo { height: var(--brand-logo-height); }

.hero { padding:18px 0; background: linear-gradient(180deg, var(--page-bg), rgba(255,255,255,0)); }
.carousel { position:relative; max-width:var(--content-max-width); margin:0 auto; overflow:hidden; border-radius:10px }
.slides { display:flex; transition:transform .45s cubic-bezier(.2,.9,.3,1) }
.slide { min-width:100%; position:relative }
.slide img { width:100%; height:320px; object-fit:cover; display:block }
.slide-caption { position:absolute; left:24px; bottom:16px; background: var(--overlay, rgba(0,0,0,0.4)); color: var(--slide-caption-color, #fff); padding:8px 12px; border-radius:6px }
.carousel-prev, .carousel-next { position:absolute; top:50%; transform:translateY(-50%); background:var(--card-bg); border:0; width:36px; height:36px; border-radius:50%; cursor:pointer; box-shadow: var(--shadow-lg, 0 6px 18px rgba(10,20,40,0.08)) }
.carousel-prev { left:12px }
.carousel-next { right:12px }
.carousel-dots { position:absolute; right:12px; bottom:12px; display:flex; gap:6px }
.carousel-dots button { width:8px; height:8px; border-radius:50%; border:0; background: var(--dot-bg, rgba(255,255,255,0.5)); opacity:0.8 }
.carousel-dots button.active { background:var(--primary) }

.features { padding:28px 0 }
.features-inner { max-width:var(--content-max-width); margin:0 auto; display:grid; grid-template-columns:repeat(3, 1fr); gap:18px }
.feature { background:var(--card-bg); padding:18px; border-radius:10px; box-shadow: var(--feature-shadow, 0 8px 20px rgba(20,30,60,0.05)); border:1px solid var(--border) }
.feature-icon { font-size:28px }
.feature-title { margin-top:8px; margin-bottom:8px }
.feature-desc { color:var(--muted) }

.site-footer { margin-top:36px; padding:20px 0; background:transparent; color:var(--muted) }
.footer-inner { max-width:var(--content-max-width); margin:0 auto; display:flex; justify-content:space-between }

/* responsive */
@media (max-width: 900px) {
  .features-inner { grid-template-columns: repeat(2, 1fr) }
}
@media (max-width: 600px) {
  .nav-menu { display:none }
  .features-inner { grid-template-columns: 1fr }
  .slide img { height:180px }
}

/* Theme variables are provided by public/themes/*.css. Minimal fallbacks removed
   so that the linked theme CSS (e.g. public/themes/light.css) controls colors.
*/
</style>