<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
        <CircuitBackground />
        <div class="gradient-page-bg" aria-hidden="true" />
        <div
          class="bg-overlay"
          :class="{ 'landing-overlay': isLandingRoute, 'app-overlay': !isLandingRoute }"
        />

        <TitleBar
          :user="user"
          @logout="logout"
        />

        <div
          class="app-shell"
          :class="{
            'admin-mode': isAdminRoute,
            'landing-mode': isLandingRoute,
            'immersive-mode': isImmersiveRoute,
            'full-height-mode': isFullHeightRoute,
          }"
        >
          <main class="main-content">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" @logged="onLogged" />
              </transition>
            </router-view>
          </main>

          <footer v-if="showFooter" class="site-footer">
            <div class="footer-inner">
              <span>© {{ footerYears }} {{ footerOrg }}</span>
              <div class="footer-links">
                <a :href="footerUrl" target="_blank" rel="noopener">{{ footerOrg }}</a>
                <template v-if="footerIcp">
                  · <a :href="footerIcpUrl" target="_blank" rel="noopener">{{ footerIcp }}</a>
                </template>
              </div>
            </div>
          </footer>
        </div>

        <div v-if="showEmailVerifyBanner" class="email-verify-banner">
          <span>邮箱尚未验证，部分功能可能受限。</span>
          <button type="button" class="email-verify-btn" @click="resendVerification" :disabled="resendingVerify">
            {{ resendingVerify ? '发送中…' : '重发验证邮件' }}
          </button>
          <router-link class="email-verify-link" to="/account">去账户设置</router-link>
          <button type="button" class="email-verify-dismiss" @click="dismissEmailBanner">稍后</button>
        </div>

        <div v-if="showMaintenanceOverlay" class="maintenance-overlay">
          <div class="maintenance-box">
            <p class="maintenance-code">503 · MAINTENANCE</p>
            <h2>平台维护中</h2>
            <p>{{ maintenanceMessage }}</p>
            <button type="button" class="maintenance-btn" @click="router.push('/auth')">管理员登录</button>
          </div>
        </div>

        <ToastContainer />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider,
} from 'naive-ui'
import CircuitBackground from './components/CircuitBackground.vue'
import TitleBar from './components/TitleBar.vue'
import ToastContainer from './components/ToastContainer.vue'
import { loadPlatform, usePlatformStore } from './stores/platform'
import { fetchPlatformVersion } from './services/platform'
import { useToast } from './composables/toast'
import { useThemeStore } from './stores/theme'
import { getUser, fetchSession, logout as authLogout } from './services/auth'

export default {
  components: {
    NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider,
    CircuitBackground, TitleBar, ToastContainer,
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const toast = useToast()
    const user = ref(null)
    const { isDark, initTheme } = useThemeStore()

    const footerOrg = ref('东北电力大学')
    const footerUrl = ref('https://www.neepu.edu.cn/')
    const footerYears = ref('2022-2026')
    const footerIcp = ref('')
    const footerIcpUrl = ref('https://beian.miit.gov.cn/')

    const { platform } = usePlatformStore()
    const maintenanceMessage = ref('系统正在维护中，请稍后再试')
    const forceMaintenance = ref(false)
    const emailBannerDismissed = ref(sessionStorage.getItem('neepu_email_banner_dismissed') === '1')
    const resendingVerify = ref(false)

    const isAdminRoute = computed(() => route.path.startsWith('/admin'))
    const isLandingRoute = computed(() => route.path === '/')
    const isImmersiveRoute = computed(() => {
      const p = route.path
      if (/^\/games\/\d+\/challenges/.test(p)) return true
      if (/^\/training\/\d+/.test(p)) return true
      return false
    })
    const isFullHeightRoute = computed(() => (
      !isLandingRoute.value && !isAdminRoute.value
    ))
    const showFooter = computed(() => (
      !isLandingRoute.value
      && !isAdminRoute.value
      && !isImmersiveRoute.value
      && !showMaintenanceOverlay.value
    ))
    const showMaintenanceOverlay = computed(() => {
      if (isAdminRoute.value) return false
      if (user.value?.is_admin) return false
      return !!(forceMaintenance.value || platform.value?.maintenance)
    })
    const showEmailVerifyBanner = computed(() => {
      if (!user.value || user.value.is_admin) return false
      if (user.value.email_verified !== false) return false
      if (emailBannerDismissed.value) return false
      if (route.path.startsWith('/auth') || route.path.startsWith('/verify-email')) return false
      return true
    })
    function dismissEmailBanner() {
      emailBannerDismissed.value = true
      sessionStorage.setItem('neepu_email_banner_dismissed', '1')
    }
    async function resendVerification() {
      resendingVerify.value = true
      try {
        const axios = (await import('axios')).default
        await axios.post('/api/auth/resend-verification', { email: user.value?.email })
        toast.success('验证邮件已发送，请查收邮箱')
      } catch (e) {
        toast.error(e?.response?.data?.msg || e?.response?.data?.message || '发送失败')
      } finally {
        resendingVerify.value = false
      }
    }

    async function checkUser() {
      user.value = await fetchSession()
    }

    function onUserRefreshed() { user.value = getUser() }
    function onAuthExpired() { user.value = null }

    function onLogged() {
      checkUser()
      const redirect = route.query.redirect
      if (redirect && typeof redirect === 'string' && redirect.startsWith('/')) {
        router.push(redirect)
      } else {
        router.push('/home')
      }
    }

    async function logout() {
      await authLogout()
      user.value = null
      router.push('/auth')
    }

    function onMaintenance(e) {
      const msg = e?.detail?.maintenance_message
        || platform.value?.maintenance_message
        || '平台正在升级维护，请稍后重试'
      if (msg) maintenanceMessage.value = msg
      forceMaintenance.value = true
      toast.warning(msg, 8000)
    }

    function syncFooterFromPlatform(info) {
      if (!info?.footer) return
      footerOrg.value = info.footer.org_name || footerOrg.value
      footerUrl.value = info.footer.org_url || footerUrl.value
      footerYears.value = info.footer.copyright_years || footerYears.value
      footerIcp.value = info.footer.icp || ''
      footerIcpUrl.value = info.footer.icp_url || footerIcpUrl.value
      if (info.maintenance_message) {
        maintenanceMessage.value = info.maintenance_message
      }
    }

    function onPlatformUpdated(e) {
      const info = e?.detail
      if (info) syncFooterFromPlatform(info)
    }

    // Debounce session check — every nav used to hit /api/auth/me and felt janky.
    let authCheckTimer = null
    watch(() => route.path, () => {
      if (authCheckTimer) clearTimeout(authCheckTimer)
      authCheckTimer = setTimeout(() => { checkUser() }, 120)
    }, { immediate: true })

    onMounted(async () => {
      initTheme()
      window.addEventListener('neepu_user_refreshed', onUserRefreshed)
      window.addEventListener('neepu_auth_expired', onAuthExpired)
      window.addEventListener('neepu_maintenance', onMaintenance)
      window.addEventListener('neepu_platform_updated', onPlatformUpdated)
      checkUser()

      const info = await loadPlatform()
      syncFooterFromPlatform(info)

      if (info.maintenance) {
        toast.warning(info.maintenance_message || '平台正在维护中，部分功能可能不可用')
      }

      const ver = await fetchPlatformVersion()
      const cachedVer = localStorage.getItem('neepu_frontend_version')
      if (cachedVer && ver.version && cachedVer !== ver.version) {
        toast.warning('前后端版本不一致，建议刷新页面')
      }
      if (ver.version) localStorage.setItem('neepu_frontend_version', ver.version)

      try {
        const u = getUser()
        if (u && u.email_verified === false) {
          toast.warning('邮箱尚未验证，请前往用户设置完成验证', 6000)
        }
      } catch { /* ignore */ }

      if (!localStorage.getItem('neepu_cookie_notice')) {
        toast.info('本站使用 Cookie 维持登录状态与会话', 8000)
        localStorage.setItem('neepu_cookie_notice', '1')
      }
    })

    onUnmounted(() => {
      window.removeEventListener('neepu_user_refreshed', onUserRefreshed)
      window.removeEventListener('neepu_auth_expired', onAuthExpired)
      window.removeEventListener('neepu_maintenance', onMaintenance)
      window.removeEventListener('neepu_platform_updated', onPlatformUpdated)
    })

    const themeOverrides = computed(() => {
      if (isDark.value) {
        return {
          common: {
            primaryColor: '#5ED9A8',
            primaryColorHover: '#7EE8C0',
            bodyColor: 'transparent',
            textColor1: '#E2E8F0',
            textColor2: '#9CA8C4',
            textColor3: '#9CA8C4',
            cardColor: '#232838',
            modalColor: '#232838',
            popoverColor: '#232838',
            inputColor: '#232838',
            tableColor: '#232838',
            borderColor: 'rgba(94, 217, 168, 0.22)',
            borderRadius: '12px',
            fontSize: '16px',
            fontSizeMini: '12px',
            fontSizeTiny: '12px',
            fontSizeSmall: '14px',
            fontSizeMedium: '16px',
            fontSizeLarge: '18px',
            fontSizeHuge: '20px',
            fontFamily: "'M PLUS Rounded 1c', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei UI', sans-serif",
            fontFamilyMono: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
          },
          Button: {
            textColorPrimary: '#0F172A',
            textColorHover: '#FFFFFF',
            textColorPressed: '#FFFFFF',
            textColorFocus: '#FFFFFF',
            border: '1px solid rgba(94, 217, 168, 0.28)',
            borderHover: '1px solid rgba(94, 217, 168, 0.55)',
            color: 'rgba(94, 217, 168, 0.12)',
            colorHover: 'rgba(94, 217, 168, 0.22)',
            colorPressed: 'rgba(94, 217, 168, 0.28)',
          },
          Input: {
            color: '#232838',
            colorFocus: '#2A3144',
            textColor: '#E2E8F0',
            placeholderColor: 'rgba(156, 168, 196, 0.75)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderHover: '1px solid rgba(94, 217, 168, 0.45)',
            borderFocus: '1px solid rgba(94, 217, 168, 0.7)',
            caretColor: '#5ED9A8',
          },
          Card: {
            color: '#232838',
            textColor: '#E2E8F0',
            borderColor: 'rgba(255, 255, 255, 0.08)',
          },
        }
      }
      return {
        common: {
          primaryColor: '#2DB58A',
          primaryColorHover: '#249E76',
          bodyColor: 'transparent',
          textColor1: '#0F172A',
          textColor2: '#64748B',
          textColor3: '#64748B',
          cardColor: '#FFFFFF',
          borderColor: 'rgba(45, 181, 138, 0.18)',
          borderRadius: '12px',
          fontSize: '16px',
          fontSizeMini: '12px',
          fontSizeTiny: '12px',
          fontSizeSmall: '14px',
          fontSizeMedium: '16px',
          fontSizeLarge: '18px',
          fontSizeHuge: '20px',
          fontFamily: "'M PLUS Rounded 1c', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei UI', sans-serif",
          fontFamilyMono: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        },
      }
    })

    return {
      user, themeOverrides, isAdminRoute, isLandingRoute, isImmersiveRoute, isFullHeightRoute, showFooter,
      footerOrg, footerUrl, footerYears, footerIcp, footerIcpUrl,
      showMaintenanceOverlay, maintenanceMessage, router, showEmailVerifyBanner, resendVerification, dismissEmailBanner, resendingVerify,
      onLogged, logout,
    }
  },
}
</script>

<style>
.app-shell {
  max-width: none;
  width: 100%;
  padding: 0;
  box-sizing: border-box;
  min-height: calc(100vh - var(--nav-height, 72px));
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 0;
}
.app-shell.admin-mode,
.app-shell.landing-mode {
  padding: 0;
}
.app-shell.admin-mode {
  overflow-x: hidden;
}
.app-shell.admin-mode .main-content {
  padding: 0;
  overflow-x: hidden;
  box-sizing: border-box;
}
.app-shell > .main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.app-shell > .main-content > * {
  flex: 1 1 auto;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.main-content > * {
  flex: 1 1 auto;
  width: 100%;
  min-width: 0;
}
.app-shell:not(.admin-mode):not(.landing-mode) .main-content {
  padding: 0;
  box-sizing: border-box;
}

/* 非首页 / 非管理：顶栏以下占满视口高度 */
.app-shell.full-height-mode {
  min-height: calc(100vh - var(--nav-height, 72px));
}
.app-shell.full-height-mode .main-content {
  flex: 1;
  min-height: 0;
}

/* 题目 / 训练工作台：顶栏以下全屏，无页脚 */
.app-shell.immersive-mode {
  height: calc(100vh - var(--nav-height, 72px));
  min-height: calc(100vh - var(--nav-height, 72px));
  overflow: hidden;
}
.app-shell.immersive-mode .main-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.app-shell.immersive-mode .main-content > * {
  height: 100%;
  min-height: 0;
  flex: 1 1 auto;
}

.bg-overlay {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}

.bg-overlay.app-overlay {
  background: var(--bg-layer);
}

.bg-overlay.landing-overlay {
  background: var(--landing-mask);
}

.site-footer {
  margin-top: auto;
  padding: 20px 24px 28px;
  color: var(--muted);
  font-size: 14px;
  width: 100%;
  box-sizing: border-box;
  border: none;
}
.footer-inner {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.footer-links a {
  color: var(--primary);
  text-decoration: none;
}
.footer-links a:hover { text-decoration: underline; }

.email-verify-banner {
  position: sticky;
  top: 0;
  z-index: 40;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: center;
  padding: 8px 14px;
  background: rgba(217, 119, 6, 0.14);
  color: #b45309;
  font-size: 13px;
  border-bottom: 1px solid rgba(217, 119, 6, 0.25);
}
.email-verify-btn, .email-verify-dismiss {
  border: 1px solid currentColor;
  background: transparent;
  color: inherit;
  border-radius: 6px;
  padding: 2px 8px;
  cursor: pointer;
}
.email-verify-link { color: inherit; text-decoration: underline; }
.maintenance-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 12, 18, 0.82);
  backdrop-filter: blur(6px);
  padding: 24px;
}
.maintenance-box {
  max-width: 480px;
  width: 100%;
  padding: 28px 32px;
  border: 1px solid rgba(45, 181, 138, 0.25);
  background: var(--card-bg, #12141d);
  text-align: center;
}
.maintenance-code {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: var(--muted);
  margin: 0 0 12px;
}
.maintenance-box h2 {
  margin: 0 0 12px;
  font-size: 22px;
}
.maintenance-box p {
  margin: 0 0 20px;
  color: var(--muted);
  line-height: 1.6;
}
.maintenance-btn {
  border: 1px solid var(--primary);
  background: transparent;
  color: var(--primary);
  padding: 10px 18px;
  cursor: pointer;
  font: inherit;
}
.maintenance-btn:hover {
  background: rgba(45, 181, 138, 0.12);
}
</style>
