<template>
  <div class="forgot-password-page" :style="bgStyle">
    <div class="forgot-card">
      <div class="logo">🏁 NEEPU CTF</div>
      <h2>忘记密码</h2>
      <p class="subtitle">输入你的注册邮箱，我们将发送密码重置链接</p>
      
      <form @submit.prevent="handleSubmit" v-if="!sent">
        <div class="form-group">
          <label>邮箱地址</label>
          <input 
            type="email" 
            v-model="email" 
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
        <h3>邮件已发送</h3>
        <p>如果该邮箱已注册，你将收到一封包含密码重置链接的邮件。</p>
        <p class="note">请检查你的收件箱和垃圾邮件文件夹。</p>
        <button @click="sent = false" class="btn-secondary">重新发送</button>
      </div>
      
      <div class="links">
        <router-link to="/auth">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject, computed } from 'vue'

export default {
  name: 'ForgotPassword',
  setup() {
    const axios = inject('axios')
    
    // 使用与主页相同的背景
    const bgUrl = 'https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/banner.svg'
    const bgStyle = computed(() => ({
      backgroundImage: `url(${bgUrl})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center center'
    }))
    
    const email = ref('')
    const loading = ref(false)
    const sent = ref(false)
    const error = ref('')
    
    const handleSubmit = async () => {
      if (!email.value) return
      
      loading.value = true
      error.value = ''
      
      try {
        await axios.post('/api/auth/forgot-password', { email: email.value })
        sent.value = true
      } catch (e) {
        error.value = '发送失败，请稍后重试'
      } finally {
        loading.value = false
      }
    }
    
    return { email, loading, sent, error, handleSubmit, bgStyle }
  }
}
</script>

<style scoped>
.forgot-password-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  padding: 20px;
}

.forgot-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  max-width: 420px;
  width: 100%;
  text-align: center;
  box-shadow: 0 4px 24px rgba(0,0,0,0.1);
}

.logo {
  font-size: 28px;
  font-weight: bold;
  color: #00c48c;
  margin-bottom: 24px;
}

h2 {
  margin: 0 0 8px;
  color: #333;
}

.subtitle {
  color: #666;
  margin: 0 0 32px;
  font-size: 14px;
}

.form-group {
  text-align: left;
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #00c48c;
}

.btn-primary, .btn-secondary {
  width: 100%;
  padding: 14px;
  border-radius: 8px;
  border: none;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #00c48c;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #00a86b;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
  margin-top: 16px;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.error-msg {
  color: #ff4757;
  margin-top: 12px;
  font-size: 14px;
}

.success-state {
  padding: 20px 0;
}

.success-state .icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.success-state h3 {
  margin: 0 0 12px;
  color: #333;
}

.success-state p {
  color: #666;
  margin: 0 0 8px;
}

.success-state .note {
  font-size: 13px;
  color: #888;
  margin-bottom: 20px;
}

.links {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}

.links a {
  color: #00c48c;
  text-decoration: none;
}

.links a:hover {
  text-decoration: underline;
}
</style>
