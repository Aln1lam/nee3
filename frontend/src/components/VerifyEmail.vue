<template>
  <div class="verify-email-page" :style="bgStyle">
    <div class="verify-card">
      <div class="logo">🏁 NEEPU CTF</div>
      
      <div v-if="loading" class="status loading">
        <div class="spinner"></div>
        <p>正在验证邮箱...</p>
      </div>
      
      <div v-else-if="success" class="status success">
        <div class="icon">✅</div>
        <h2>邮箱验证成功！</h2>
        <p>你的邮箱 <strong>{{ email }}</strong> 已验证</p>
        <button @click="goLogin" class="btn-primary">前往登录</button>
      </div>
      
      <div v-else class="status error">
        <div class="icon">❌</div>
        <h2>验证失败</h2>
        <p>{{ errorMsg }}</p>
        <button @click="goHome" class="btn-secondary">返回首页</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, inject, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'VerifyEmail',
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
    
    const loading = ref(true)
    const success = ref(false)
    const email = ref('')
    const errorMsg = ref('')
    
    onMounted(async () => {
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
    })
    
    const goLogin = () => router.push('/auth')
    const goHome = () => router.push('/home')
    
    return { loading, success, email, errorMsg, goLogin, goHome, bgStyle }
  }
}
</script>

<style scoped>
.verify-email-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  padding: 20px;
}

.verify-card {
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
  margin-bottom: 32px;
}

.status { padding: 20px 0; }

.icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #00c48c;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

h2 {
  margin: 0 0 12px;
  color: #333;
}

p {
  color: #666;
  margin: 0 0 24px;
}

.btn-primary, .btn-secondary {
  padding: 12px 32px;
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

.btn-primary:hover {
  background: #00a86b;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}
</style>
