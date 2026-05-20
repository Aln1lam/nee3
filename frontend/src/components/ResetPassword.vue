<template>
  <div class="reset-password-page" :style="bgStyle">
    <div class="reset-card">
      <div class="logo">🏁 NEEPU CTF</div>
      
      <div v-if="success" class="success-state">
        <div class="icon">✅</div>
        <h2>密码重置成功</h2>
        <p>你的密码已更新，现在可以使用新密码登录了。</p>
        <button @click="goLogin" class="btn-primary">前往登录</button>
      </div>
      
      <template v-else>
        <h2>设置新密码</h2>
        <p class="subtitle">请输入你的新密码</p>
        
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>新密码</label>
            <input 
              type="password" 
              v-model="password" 
              placeholder="至少6个字符"
              required
              minlength="6"
              :disabled="loading"
            />
          </div>
          
          <div class="form-group">
            <label>确认密码</label>
            <input 
              type="password" 
              v-model="confirmPassword" 
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
      </template>
      
      <div class="links">
        <router-link to="/auth">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'ResetPassword',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const axios = inject('axios')
    
    // 使用与主页相同的背景
    const bgUrl = 'https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/banner.svg'
    const bgStyle = computed(() => ({
      backgroundImage: `url(${bgUrl})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center center'
    }))
    
    const password = ref('')
    const confirmPassword = ref('')
    const loading = ref(false)
    const success = ref(false)
    const error = ref('')
    
    const isValid = computed(() => {
      return password.value.length >= 6 && password.value === confirmPassword.value
    })
    
    const handleSubmit = async () => {
      if (!isValid.value) {
        if (password.value !== confirmPassword.value) {
          error.value = '两次输入的密码不一致'
        } else {
          error.value = '密码至少需要6个字符'
        }
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
        await axios.post('/api/auth/reset-password', {
          token,
          password: password.value
        })
        success.value = true
      } catch (e) {
        const msg = e.response?.data?.msg || '重置失败'
        if (msg === 'token expired') {
          error.value = '重置链接已过期，请重新申请'
        } else if (msg === 'invalid token') {
          error.value = '无效的重置链接'
        } else {
          error.value = msg
        }
      } finally {
        loading.value = false
      }
    }
    
    const goLogin = () => router.push('/auth')
    
    return { password, confirmPassword, loading, success, error, isValid, handleSubmit, goLogin, bgStyle }
  }
}
</script>

<style scoped>
.reset-password-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  padding: 20px;
}

.reset-card {
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

.btn-primary {
  width: 100%;
  padding: 14px;
  border-radius: 8px;
  border: none;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
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

.error-msg {
  color: #ff4757;
  margin-top: 12px;
  font-size: 14px;
}

.success-state {
  padding: 20px 0;
}

.success-state .icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.success-state p {
  color: #666;
  margin: 0 0 24px;
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
