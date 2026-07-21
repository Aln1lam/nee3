<template>
  <div class="landing-page" :style="authBgStyle">
    
    <div class="center-content">
      <div class="bracket-title">
        <span class="bracket">[</span>
        <span class="title-text">NEEPU CTF 终端</span>
        <span class="bracket">]</span>
      </div>
      
      <div class="action-area">
        <n-button 
            color="#ff5252" 
            text-color="#ffffff" 
            class="start-btn" 
            round
            @click.prevent="goGames"
          >
          为世界上所有美好而战
        </n-button>
      </div>
    </div>

  <n-modal v-model:show="showLogin" :class="modalAnimationClass">
      <n-card
        :style="{ width: 'var(--auth-modal-width, 400px)' }"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-tabs default-value="login" size="large" justify-content="space-evenly">
          <n-tab-pane name="login" tab="身份认证">
            <n-form>
              <n-form-item-row label="账号">
                <n-input v-model:value="loginAccount" placeholder="用户名 / 手机号 / 邮箱" />
              </n-form-item-row>
              <n-form-item-row label="口令">
                <n-input type="password" v-model:value="loginPassword" show-password-on="click" />
              </n-form-item-row>
            </n-form>
            <div v-if="captchaRequired" class="auth-captcha">
              <Captcha v-model="loginCaptchaAnswer" v-model:captcha-id="loginCaptchaId" />
            </div>
            <n-button type="primary" block strong @click="login" :loading="loading">
              确认进入系统
            </n-button>
            <div class="auth-links">
              <router-link to="/forgot-password">忘记密码？</router-link>
            </div>
          </n-tab-pane>

          <n-tab-pane name="register" tab="新用户注册">
            <n-form>
              <n-form-item-row label="代号 (Nickname)">
                <n-input v-model:value="nickname" placeholder="显示名称，必填" />
              </n-form-item-row>
              <n-form-item-row label="用户名">
                <n-input v-model:value="regUsername" placeholder="可选，用于登录" />
              </n-form-item-row>
              <n-form-item-row label="邮箱">
                <n-input v-model:value="email" placeholder="必填，需验证" />
              </n-form-item-row>
              <n-form-item-row label="口令">
                <n-input type="password" v-model:value="password" placeholder="设置登录密码" />
              </n-form-item-row>
            </n-form>
            <div v-if="captchaRequired" class="auth-captcha">
              <Captcha v-model="regCaptchaAnswer" v-model:captcha-id="regCaptchaId" />
            </div>
            <n-button type="success" ghost block @click="register" :loading="loading">
              提交注册申请
            </n-button>
            <div v-if="registerSuccess" class="register-success">
              <p>✅ 注册成功！验证邮件已发送至你的邮箱</p>
              <p class="hint">请查收邮件并点击验证链接完成注册</p>
            </div>
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </n-modal>

  </div>
</template>

<script>
import { ref, inject, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NButton, NModal, NCard, NTabs, NTabPane, NForm, NFormItemRow, NInput, useMessage } from 'naive-ui'
import Captcha from '@/components/shared/Captcha.vue'
import { usePlatformStore } from '@/stores/platform'
import { fetchSession, setUser } from '@/services/auth'

export default {
  components: { NButton, NModal, NCard, NTabs, NTabPane, NForm, NFormItemRow, NInput, Captcha },
  setup(_, { emit }) {
    const axios = inject('axios')
    const message = useMessage()
    // 同源 CSS 背景，避免外链 SVG 被 ORB 拦截导致控制台报错
    const authBgStyle = computed(() => ({}))

    // Choose one of three Material Design inspired micro-interaction classes:
    // 'md-fade-scale' (default), 'md-slide-up', 'md-shared-axis'
    const modalAnimationClass = ref('md-fade-scale')

    const showLogin = ref(false)
    const loading = ref(false)
  const router = useRouter()
  const route = useRoute()

    // Form data
    const loginAccount = ref('')
    const loginPassword = ref('')
    const email = ref('')
    const password = ref('')
    const nickname = ref('')
    const regUsername = ref('')
    
    const registerSuccess = ref(false)
    const { platform } = usePlatformStore()
    const captchaRequired = computed(() => !!(platform.value?.captcha_required || platform.value?.features?.captcha_required))
    const loginCaptchaId = ref('')
    const loginCaptchaAnswer = ref('')
    const regCaptchaId = ref('')
    const regCaptchaAnswer = ref('')

    async function login() {
      if (loading.value) return
      loading.value = true
      try {
        const { data } = await axios.post('/api/auth/login', {
          account: loginAccount.value,
          password: loginPassword.value,
          captcha_id: loginCaptchaId.value,
          captcha_answer: loginCaptchaAnswer.value,
        })
        // 现网：JWT 只在 HttpOnly Cookie；body 通常只有 user，没有 access_token
        if (data?.access_token) {
          try {
            localStorage.setItem('neepu_token', data.access_token)
            localStorage.setItem('token', data.access_token)
            axios.defaults.headers.common['Authorization'] = 'Bearer ' + data.access_token
          } catch (e) { /* ignore */ }
        }
        if (data?.user) {
          try { localStorage.setItem('neepu_user', JSON.stringify(data.user)) } catch (e) { /* ignore */ }
          setUser(data.user)
        } else if (!data?.access_token) {
          message.error('验证失败: 服务器未返回会话')
          return
        }
        await fetchSession({ force: true })
        message.success('身份验证通过')
        try { window.dispatchEvent(new Event('neepu_user_refreshed')) } catch (e) { /* ignore */ }
        emit('logged')
        const redirect = typeof route.query.redirect === 'string' && route.query.redirect
          ? route.query.redirect
          : '/home'
        await router.replace(redirect)
      } catch (e) {
        message.error('验证失败: ' + (e.response?.data?.msg || '请检查输入'))
      } finally { loading.value = false }
    }

    async function register() {
      if (loading.value) return
      loading.value = true
      registerSuccess.value = false
      try {
        const res = await axios.post('/api/auth/register', { 
          email: email.value, 
          password: password.value, 
          nickname: nickname.value,
          username: regUsername.value || undefined,
          captcha_id: regCaptchaId.value,
          captcha_answer: regCaptchaAnswer.value,
        })
        if (res.data?.need_verify) {
          registerSuccess.value = true
          message.success('注册成功！请查收验证邮件')
        } else {
          message.success('注册成功，请登录')
        }
      } catch (e) {
        message.error('注册失败: ' + (e.response?.data?.msg || '未知错误'))
      } finally { loading.value = false }
    }

    function goGames() {
      // go to games list instead of opening modal from the big start button
      router.push('/games')
    }

    // If other code dispatches open-auth-modal, navigate to /auth so URL and modal stay in sync
    function onOpenAuth() {
      // Open auth modal as an overlay on the current page (do not change route),
      // so the background remains the current page. If someone navigates to /auth
      // directly, the route watcher below will also open the modal.
      showLogin.value = true
    }
    onMounted(() => window.addEventListener('open-auth-modal', onOpenAuth))
    // cleanup listener when component unmounts
    onUnmounted(() => window.removeEventListener('open-auth-modal', onOpenAuth))

    // Open modal when route is /auth (direct navigation), close when leaving
    onMounted(() => {
      if (route.path === '/auth') showLogin.value = true
    })
    watch(() => route.path, (p) => {
      if (p === '/auth') showLogin.value = true
      else if (route.path !== '/auth' && showLogin.value === true && p !== '/auth') {
        // If route changes away from /auth, do not forcibly open modal. Only
        // close modal if the route left /auth and it was opened by route.
        showLogin.value = false
      }
    })

    // When modal closes by user action, if URL is /auth then navigate back / replace
    watch(showLogin, (val) => {
      // If modal was closed and the current URL is /auth (user navigated directly),
      // go back in history to restore previous page. If the modal was opened as an
      // overlay (no route change), just close it without navigating.
      if (!val && route.path === '/auth') {
        try {
          if (window.history.length > 1) router.back()
          else router.replace('/home')
        } catch (e) {
          try { router.replace('/home') } catch (e2) { /* swallow */ }
        }
      }
    })

    return { 
      showLogin, loading, login, register,
      loginAccount, loginPassword, email, password, nickname, regUsername,
      goGames, registerSuccess,
      captchaRequired, loginCaptchaId, loginCaptchaAnswer, regCaptchaId, regCaptchaAnswer,
      authBgStyle, modalAnimationClass
    }
  }
}
</script>

<style scoped>
.landing-page {
  height: 100%;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: var(--font-ui);
  /* Follow theme tokens — do NOT hardcode cyber black */
  background:
    var(--gradient-page-glow, none),
    var(--page-bg, var(--gradient-page-base, #F0FBF6));
  background-attachment: fixed;
}

.center-content {
  text-align: center;
  margin-bottom: var(--auth-center-margin-bottom, 100px); /* 视觉上稍微偏上一点，符合西电的设计 */
}

/* 1. 大标题样式 */
.bracket-title {
  font-size: var(--auth-title-size, 3rem);
  font-weight: 700;
  color: var(--text);
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  gap: var(--auth-title-gap, 20px);
}

.bracket {
  font-weight: 300;
  color: var(--muted, #64748B);
}

/* 2. 红色小按钮区域 */
.action-area {
  margin-top: var(--auth-action-margin-top, 40px);
}

.start-btn {
  padding: var(--auth-start-btn-padding, 0 30px);
  font-size: var(--auth-start-btn-font-size, 0.9rem);
  letter-spacing: 1px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--auth-start-btn-hover-shadow, 0 4px 12px rgba(255, 82, 82, 0.3));
}

/* 移动端适配 */
@media (max-width: 768px) {
  .bracket-title { font-size: 1.5rem; gap: 10px; }
  .action-area { margin-top: 30px; }
}

/* --- Material Design micro-interactions --- */

/* 1) Fade + Scale (Entrance) - subtle elevation and fade */
@keyframes md-fade-scale-in {
  0% { opacity: 0; transform: translateY(8px) scale(0.98); filter: blur(2px); }
  60% { opacity: 1; transform: translateY(0) scale(1.02); filter: blur(0); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
.md-fade-scale .n-modal__card {
  animation: md-fade-scale-in 260ms cubic-bezier(.4,0,.2,1) both;
}

/* 2) Slide Up + Shadow (Material 'container transform' variant) */
@keyframes md-slide-up-in {
  0% { opacity: 0; transform: translateY(24px); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  100% { opacity: 1; transform: translateY(0); box-shadow: 0 10px 30px rgba(0,0,0,0.12); }
}
.md-slide-up .n-modal__card {
  animation: md-slide-up-in 300ms cubic-bezier(.2,.8,.2,1) both;
}

/* 3) Shared Axis (scale + translate on Y for 'depth' feel) */
@keyframes md-shared-axis-in {
  0% { opacity: 0; transform: translateY(12px) scale(0.96); }
  60% { opacity: 1; transform: translateY(-6px) scale(1.02); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
.md-shared-axis .n-modal__card {
  animation: md-shared-axis-in 360ms cubic-bezier(.25,.46,.45,.94) both;
}

/* Backdrop transition (fade) - applied to Naive UI modal mask */
@keyframes md-backdrop-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Auth links */
.auth-links {
  margin-top: 16px;
  text-align: center;
}
.auth-links a {
  color: #00c48c;
  font-size: 14px;
  text-decoration: none;
}
.auth-links a:hover {
  text-decoration: underline;
}

/* Register success message */
.register-success {
  margin-top: 16px;
  padding: 16px;
  background: #e8f5e9;
  border-radius: 8px;
  text-align: center;
}
.register-success p {
  margin: 0;
  color: #2e7d32;
}
.register-success .hint {
  margin-top: 8px;
  font-size: 13px;
  color: #558b2f;
}

/* Utility: smaller dialog on mobile */
@media (max-width: 520px) {
  .n-modal__card { width: calc(100vw - var(--auth-mobile-modal-offset, 32px)) !important; }
}
.auth-captcha { margin: 12px 0; }

/* anime-ui: auth contrast */
.n-card :deep(.n-button--default-type) {
  background: var(--gradient-btn-fill, var(--primary)) !important;
  color: var(--on-primary-text, #fff) !important;
  border: none !important;
}
.n-card :deep(.n-button--default-type:hover) {
  background: var(--gradient-btn-fill-hover, var(--primary-hover)) !important;
}
.n-card :deep(.n-input) {
  --n-border: 1px solid var(--border) !important;
  --n-border-hover: 1px solid rgba(var(--primary-rgb), 0.45) !important;
  --n-border-focus: 1px solid rgba(var(--primary-rgb), 0.7) !important;
}

</style>

<style>
.auth-r2s .n-input {
  --n-height: 48px !important;
  --n-border-radius: 8px !important;
  font-family: var(--font-ui) !important;
}
.auth-r2s .n-button {
  --n-height: 48px !important;
  --n-border-radius: 8px !important;
  font-weight: 700 !important;
}
.auth-r2s .n-form-item-label {
  font-family: var(--font-ui) !important;
}
.auth-icon-slot {
  width: 48px;
  height: 48px;
}

/* Modal mask is teleported to body — must be unscoped */
.n-modal-mask,
.n-modal__mask {
  background-color: rgba(15, 23, 42, 0.14) !important;
}
</style>
