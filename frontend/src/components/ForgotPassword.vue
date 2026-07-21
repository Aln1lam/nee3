<template>
  <div class="landing-page auth-aux-page">
    <div class="auth-aux-shell">
      <div class="matrix-panel auth-aux-card">
        <header class="auth-aux-head">
          <p class="matrix-page-prompt">找回密码 · AUTH</p>
          <h1 class="auth-aux-title">忘记密码</h1>
          <p class="auth-aux-desc">输入注册邮箱，我们将发送密码重置链接</p>
        </header>

        <form v-if="!sent" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>邮箱地址</label>
            <input
              v-model="email"
              type="email"
              placeholder="your@email.com"
              required
              :disabled="loading"
            />
          </div>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? '发送中...' : '发送重置链接' }}
          </button>
          <p v-if="error" class="error-msg">{{ error }}</p>
        </form>

        <div v-else class="success-state">
          <div class="icon">📧</div>
          <h2>邮件已发送</h2>
          <p>如果该邮箱已注册，你将收到一封包含密码重置链接的邮件。</p>
          <p class="note">请检查收件箱和垃圾邮件文件夹。</p>
          <button type="button" class="btn-secondary" @click="sent = false">重新发送</button>
        </div>

        <div class="links">
          <router-link to="/auth">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject } from 'vue'

export default {
  name: 'ForgotPassword',
  components: {},
  setup() {
    const axios = inject('axios')
    const email = ref('')
    const loading = ref(false)
    const sent = ref(false)
    const error = ref('')

    async function handleSubmit() {
      if (loading.value || !email.value) return
      loading.value = true
      error.value = ''
      try {
        await axios.post('/api/auth/forgot-password', { email: email.value })
        sent.value = true
      } catch (e) {
        error.value = e.response?.data?.msg || e.response?.data?.error || '发送失败，请稍后重试'
      } finally {
        loading.value = false
      }
    }

    return { email, loading, sent, error, handleSubmit }
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
