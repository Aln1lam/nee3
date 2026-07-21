<template>
  <div class="landing-page auth-aux-page">
    <div class="auth-aux-shell">
      <div class="matrix-panel auth-aux-card">
        <header class="auth-aux-head">
          <p class="matrix-page-prompt">邮箱验证 · AUTH</p>
          <h1 class="auth-aux-title">邮箱验证</h1>
        </header>

        <div v-if="loading" class="status">
          <n-spin size="medium" />
          <p>正在验证邮箱...</p>
        </div>

        <div v-else-if="success" class="success-state">
          <div class="icon">✅</div>
          <h2>邮箱验证成功</h2>
          <p>你的邮箱 <strong>{{ email }}</strong> 已验证</p>
          <button type="button" class="btn-primary" @click="goLogin">前往登录</button>
        </div>

        <div v-else class="status">
          <div class="icon">❌</div>
          <h2>验证失败</h2>
          <p>{{ errorMsg }}</p>
          <button type="button" class="btn-secondary" @click="goHome">返回首页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NSpin } from 'naive-ui'

export default {
  name: 'VerifyEmail',
  components: { NSpin },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const axios = inject('axios')
    const loading = ref(true)
    const success = ref(false)
    const email = ref('')
    const errorMsg = ref('')

    async function verify() {
      const token = route.query.token
      if (!token) {
        loading.value = false
        errorMsg.value = '缺少验证令牌'
        return
      }
      try {
        const res = await axios.post('/api/auth/verify-email', { token })
        success.value = true
        email.value = res.data.email || ''
      } catch (e) {
        const msg = e.response?.data?.msg || '验证失败'
        if (msg === 'token expired') {
          errorMsg.value = '验证链接已过期，请重新注册或请求新的验证邮件'
        } else if (msg === 'invalid token') {
          errorMsg.value = '无效的验证链接'
        } else {
          errorMsg.value = msg
        }
      } finally {
        loading.value = false
      }
    }

    onMounted(verify)
    function goLogin() { router.push('/auth') }
    function goHome() { router.push('/home') }

    return { loading, success, email, errorMsg, goLogin, goHome }
  },
}
</script>

<style scoped>
form {
  display: flex;
  flex-direction: column;
  gap: var(--fib-13);
}
.note {
  font-size: var(--text-xs);
  color: var(--muted);
}
.icon {
  font-size: 2rem;
}
</style>
