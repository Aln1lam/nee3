<template>
  <div class="landing-page auth-aux-page">
    <div class="auth-aux-shell">
      <div class="matrix-panel auth-aux-card">
        <header class="auth-aux-head">
          <p class="matrix-page-prompt">重置密码 · AUTH</p>
          <h1 class="auth-aux-title">设置新密码</h1>
          <p v-if="!success" class="auth-aux-desc">请输入你的新密码</p>
        </header>

        <div v-if="success" class="success-state">
          <div class="icon">✅</div>
          <h2>密码重置成功</h2>
          <p>你的密码已更新，现在可以使用新密码登录。</p>
          <button type="button" class="btn-primary" @click="goLogin">前往登录</button>
        </div>

        <form v-else @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>新密码</label>
            <input
              v-model="password"
              type="password"
              placeholder="至少6个字符"
              required
              minlength="6"
              :disabled="loading"
            />
          </div>
          <div class="form-group">
            <label>确认密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="再次输入新密码"
              required
              :disabled="loading"
            />
          </div>
          <button type="submit" class="btn-primary" :disabled="loading || !isValid">
            {{ loading ? '重置中...' : '重置密码' }}
          </button>
          <p v-if="error" class="error-msg">{{ error }}</p>
        </form>

        <div class="links">
          <router-link to="/auth">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'ResetPassword',
  components: {},
  setup() {
    const axios = inject('axios')
    const router = useRouter()
    const route = useRoute()
    const password = ref('')
    const confirmPassword = ref('')
    const loading = ref(false)
    const success = ref(false)
    const error = ref('')
    const isValid = computed(() => password.value.length >= 6 && password.value === confirmPassword.value)

    async function handleSubmit() {
      if (loading.value) return
      if (!isValid.value) {
        error.value = password.value !== confirmPassword.value
          ? '两次输入的密码不一致'
          : '密码至少需要6个字符'
        return
      }
      const token = route.query.token
      if (!token) {
        error.value = '无效的重置链接'
        return
      }
      loading.value = true
      error.value = ''
      try {
        await axios.post('/api/auth/reset-password', { token, password: password.value })
        success.value = true
      } catch (e) {
        const msg = e.response?.data?.msg || '重置失败'
        if (msg === 'token expired') error.value = '重置链接已过期，请重新申请'
        else if (msg === 'invalid token') error.value = '无效的重置链接'
        else error.value = msg
      } finally {
        loading.value = false
      }
    }

    function goLogin() { router.push('/auth') }

    return { password, confirmPassword, loading, success, error, isValid, handleSubmit, goLogin }
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
