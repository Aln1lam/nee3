<template>
  <div class="admin-setup">
    <div class="setup-card">
      <h2>🔧 管理员设置助手</h2>
      
      <!-- 检查当前用户 -->
      <div class="section">
        <h3>📍 当前用户信息</h3>
        <button class="btn-primary" @click="checkCurrentUser" :disabled="checking">
          {{ checking ? '检查中...' : '检查我的管理员身份' }}
        </button>
        
        <div v-if="currentUser" class="user-info">
          <div class="info-item">
            <span class="label">昵称:</span>
            <span class="value">{{ currentUser.nickname }}</span>
          </div>
          <div class="info-item">
            <span class="label">ID:</span>
            <span class="value">{{ currentUser.id }}</span>
          </div>
          <div class="info-item">
            <span class="label">邮箱:</span>
            <span class="value">{{ currentUser.email }}</span>
          </div>
          <div class="info-item" :class="{ admin: currentUser.is_admin }">
            <span class="label">管理员:</span>
            <span class="value badge" :class="{ 'badge-success': currentUser.is_admin, 'badge-danger': !currentUser.is_admin }">
              {{ currentUser.is_admin ? '✅ 是' : '❌ 否' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 快速设置第一个用户为管理员 -->
      <div class="section">
        <h3>⚡ 快速设置</h3>
        <button class="btn-danger" @click="setFirstUserAdmin" :disabled="setting">
          {{ setting ? '设置中...' : '设置第一个用户为管理员' }}
        </button>
        <p class="tip">⚠️ 这会将数据库中第一个用户设置为管理员</p>
      </div>

      <!-- 搜索用户 -->
      <div class="section">
        <h3>🔍 搜索用户</h3>
        <div class="search-box">
          <input 
            v-model="searchNickname" 
            placeholder="输入用户昵称（如：11）" 
            @keyup.enter="searchUser"
            class="search-input"
          />
          <button class="btn-primary" @click="searchUser" :disabled="searching">
            {{ searching ? '搜索中...' : '搜索' }}
          </button>
        </div>

        <div v-if="searchResult" class="user-info">
          <div class="info-item">
            <span class="label">昵称:</span>
            <span class="value">{{ searchResult.nickname }}</span>
          </div>
          <div class="info-item">
            <span class="label">ID:</span>
            <span class="value">{{ searchResult.id }}</span>
          </div>
          <div class="info-item">
            <span class="label">邮箱:</span>
            <span class="value">{{ searchResult.email }}</span>
          </div>
          <div class="info-item" :class="{ admin: searchResult.is_admin }">
            <span class="label">管理员:</span>
            <span class="value badge" :class="{ 'badge-success': searchResult.is_admin, 'badge-danger': !searchResult.is_admin }">
              {{ searchResult.is_admin ? '✅ 是' : '❌ 否' }}
            </span>
          </div>
          
          <button 
            v-if="!searchResult.is_admin"
            class="btn-primary" 
            @click="setUserAdmin(searchResult.id)"
            :disabled="settingUser"
          >
            {{ settingUser ? '设置中...' : '设置此用户为管理员' }}
          </button>
        </div>

        <div v-if="searchError" class="error-msg">
          {{ searchError }}
        </div>
      </div>

      <!-- 信息提示 -->
      <div class="info-box">
        <h4>💡 设置后的步骤：</h4>
        <ol>
          <li>刷新浏览器页面</li>
          <li>检查用户下拉菜单，应该出现 "🔧 管理后台" 选项</li>
          <li>点击进入管理后台管理系统</li>
        </ol>
      </div>

      <!-- 消息提示 -->
      <div v-if="message" :class="['message', message.type]">
        {{ message.text }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject } from 'vue'

export default {
  name: 'AdminSetup',
  setup() {
    const axios = inject('axios')
    
    const checking = ref(false)
    const setting = ref(false)
    const searching = ref(false)
    const settingUser = ref(false)
    
    const currentUser = ref(null)
    const searchNickname = ref('11')
    const searchResult = ref(null)
    const searchError = ref('')
    
    const message = ref(null)

    async function checkCurrentUser() {
      checking.value = true
      try {
        const token = localStorage.getItem('neepu_token')
        if (!token) {
          message.value = { type: 'error', text: '❌ 未登录' }
          return
        }

        const res = await axios.get('/api/admin/check-current-user', {
          headers: { Authorization: `Bearer ${token}` }
        })
        currentUser.value = res.data
        
        if (res.data.is_admin) {
          message.value = { type: 'success', text: `✅ ${res.data.nickname} 已经是管理员了！` }
        } else {
          message.value = { type: 'error', text: `⚠️ ${res.data.nickname} 还不是管理员` }
        }
      } catch (e) {
        message.value = { type: 'error', text: `❌ 检查失败: ${e.message}` }
      } finally {
        checking.value = false
      }
    }

    async function setFirstUserAdmin() {
      setting.value = true
      try {
        const res = await axios.post('/api/admin/set-admin-first-user')
        message.value = { type: 'success', text: `✅ ${res.data.message}` }
        setTimeout(() => {
          window.location.reload()
        }, 1500)
      } catch (e) {
        message.value = { type: 'error', text: `❌ 设置失败: ${e.response?.data?.error || e.message}` }
      } finally {
        setting.value = false
      }
    }

    async function searchUser() {
      if (!searchNickname.value.trim()) {
        searchError.value = '请输入用户昵称'
        return
      }

      searching.value = true
      searchError.value = ''
      searchResult.value = null

      try {
        const token = localStorage.getItem('neepu_token')
        const res = await axios.get(`/api/admin/search-user/${searchNickname.value}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        searchResult.value = res.data
      } catch (e) {
        searchError.value = `找不到用户 "${searchNickname.value}"`
      } finally {
        searching.value = false
      }
    }

    async function setUserAdmin(userId) {
      settingUser.value = true
      try {
        const token = localStorage.getItem('neepu_token')
        const res = await axios.patch(`/api/admin/users/${userId}`, 
          { is_admin: true },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        message.value = { type: 'success', text: `✅ 用户已设置为管理员！` }
        if (searchResult.value) {
          searchResult.value.is_admin = true
        }
        setTimeout(() => {
          window.location.reload()
        }, 1500)
      } catch (e) {
        message.value = { type: 'error', text: `❌ 设置失败: ${e.message}` }
      } finally {
        settingUser.value = false
      }
    }

    return {
      checking, setting, searching, settingUser,
      currentUser, searchNickname, searchResult, searchError,
      message,
      checkCurrentUser, setFirstUserAdmin, searchUser, setUserAdmin
    }
  }
}
</script>

<style scoped>
.admin-setup {
  min-height: 100vh;
  background: var(--light-page-bg);
  padding: 40px 20px;
}

.setup-card {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: var(--card-shadow);
}

.setup-card h2 {
  margin-top: 0;
  color: var(--card-accent);
  border-bottom: 3px solid var(--card-accent);
  padding-bottom: 12px;
  margin-bottom: 25px;
}

.section {
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.section:last-of-type {
  border-bottom: none;
}

.section h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
  font-size: 16px;
}

.btn-primary, .btn-danger {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all .2s ease;
  font-size: 14px;
}

.btn-primary {
  background: var(--card-accent);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  background: #ff6b6b;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-2px);
}

.user-info {
  background: #f5f5f5;
  border-left: 4px solid var(--card-accent);
  padding: 15px;
  border-radius: 6px;
  margin-top: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 14px;
}

.info-item .label {
  font-weight: 600;
  color: #666;
  min-width: 80px;
}

.info-item .value {
  color: #333;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

.badge-success {
  background: #4caf50;
  color: white;
}

.badge-danger {
  background: #f44336;
  color: white;
}

.search-box {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.search-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: var(--card-accent);
  box-shadow: 0 0 0 3px rgba(0, 196, 140, 0.1);
}

.error-msg {
  color: #f44336;
  padding: 10px;
  background: rgba(244, 67, 54, 0.1);
  border-radius: 6px;
  margin-top: 10px;
}

.info-box {
  background: rgba(0, 196, 140, 0.1);
  border-left: 4px solid var(--card-accent);
  padding: 15px;
  border-radius: 6px;
  margin-top: 20px;
}

.info-box h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #333;
}

.info-box ol {
  margin: 0;
  padding-left: 20px;
}

.info-box li {
  margin-bottom: 6px;
  color: #666;
  font-size: 13px;
}

.message {
  margin-top: 20px;
  padding: 12px 15px;
  border-radius: 6px;
  font-weight: 500;
  text-align: center;
}

.message.success {
  background: #4caf50;
  color: white;
}

.message.error {
  background: #f44336;
  color: white;
}

.tip {
  font-size: 12px;
  color: #f44336;
  margin-top: 8px;
}
</style>
