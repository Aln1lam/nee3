<template>
  <div class="system-settings">
    
    <div class="settings-card">
      
      <div class="form-group">
        <label>平台名称</label>
        <input 
          v-model="settings.site_name" 
          class="form-input"
          placeholder="例如：NEEPU CTF"
        />
        <p class="help-text">平台的显示名称，用于网站标题和页面展示</p>
      </div>

      <div class="form-group">
        <label>平台URL</label>
        <input 
          v-model="settings.site_url" 
          class="form-input"
          placeholder="例如：https://ctf.neepu.edu.cn"
        />
        <p class="help-text">平台的访问地址，用于邮件链接和分享</p>
      </div>

      <div class="form-group">
        <label>API地址</label>
        <input 
          v-model="settings.api_url" 
          class="form-input"
          placeholder="例如：https://api.ctf.neepu.edu.cn"
        />
        <p class="help-text">后端API服务器地址</p>
      </div>

      <div class="form-group">
        <label>平台描述</label>
        <textarea 
          v-model="settings.site_description"
          class="form-textarea"
          placeholder="平台的简介描述..."
          rows="3"
        ></textarea>
        <p class="help-text">用于SEO和平台介绍</p>
      </div>
    </div>

    <div class="settings-card">
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="settings.maintenance_mode" />
          启用维护模式
        </label>
        <p class="help-text">启用后，只有管理员可以访问平台</p>
      </div>

      <div class="form-group">
        <label>维护提示</label>
        <textarea 
          v-model="settings.maintenance_message"
          class="form-textarea"
          placeholder="输入维护期间显示给用户的提示信息..."
          rows="2"
        ></textarea>
        <p class="help-text">当平台处于维护模式时显示此信息</p>
      </div>

      <div class="form-group">
        <label>首页公告</label>
        <textarea 
          v-model="settings.announcement"
          class="form-textarea"
          placeholder="输入平台公告..."
          rows="3"
        ></textarea>
        <p class="help-text">显示在首页的重要公告</p>
      </div>
    </div>

    <div class="settings-card">
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="settings.allow_registration" />
          允许用户注册
        </label>
        <p class="help-text">关闭后新用户无法注册账号</p>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="settings.allow_teams" />
          启用团队功能
        </label>
        <p class="help-text">控制用户是否可以创建和加入团队</p>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="settings.allow_games" />
          启用竞赛功能
        </label>
        <p class="help-text">启用平台的CTF竞赛功能</p>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="settings.require_email_verification" />
          需要邮箱验证
        </label>
        <p class="help-text">用户注册时需要验证邮箱才能登录</p>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="settings.captcha_required" />
          登录/注册验证码
        </label>
        <p class="help-text">开启后登录与注册必须填写图形验证码（也可由环境变量 NEPU_CAPTCHA_REQUIRED 强制）</p>
      </div>
    </div>

    <div class="settings-card">
      
      <div class="form-row">
        <div class="form-group half">
          <label>SMTP服务器</label>
          <input 
            v-model="settings.mail_server" 
            class="form-input"
            placeholder="smtp.qq.com"
          />
        </div>
        <div class="form-group half">
          <label>SMTP端口</label>
          <input 
            v-model="settings.mail_port" 
            class="form-input"
            placeholder="465"
          />
        </div>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="settings.mail_use_ssl" />
          使用SSL加密
        </label>
        <p class="help-text">大多数邮箱服务商需要开启</p>
      </div>

      <div class="form-row">
        <div class="form-group half">
          <label>邮箱账号</label>
          <input 
            v-model="settings.mail_username" 
            class="form-input"
            placeholder="your-email@qq.com"
          />
        </div>
        <div class="form-group half">
          <label>邮箱密码/授权码</label>
          <input 
            type="password"
            v-model="settings.mail_password" 
            class="form-input"
            placeholder="SMTP授权码"
          />
        </div>
      </div>

      <div class="form-group">
        <label>发件人名称</label>
        <input 
          v-model="settings.mail_sender_name" 
          class="form-input"
          placeholder="NEEPU CTF"
        />
        <p class="help-text">收件人看到的发件人显示名称</p>
      </div>

      <div class="form-group">
        <label>发件人邮箱</label>
        <input
          v-model="settings.mail_sender_email"
          class="form-input"
          placeholder="no-reply@neepu.edu.cn"
        />
        <p class="help-text">用于邮件头的发件人地址（例如 no-reply@neepu.edu.cn）</p>
      </div>

      <button class="btn-test" @click="testEmail">📤 发送测试邮件</button>
    </div>

    <div class="settings-actions">
      <button class="btn-primary" @click="saveSettings" :disabled="saving">
        {{ saving ? '保存中...' : '💾 保存设置' }}
      </button>
      <button class="btn-secondary" @click="loadSettings">🔄 重新加载</button>
    </div>

    <div v-if="saveStatus" :class="['status-message', saveStatus.type]">
      {{ saveStatus.message }}
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted } from 'vue'

export default {
  name: 'SystemSettings',
  setup() {
    const axios = inject('axios')
    
    const settings = ref({
      // 平台基本信息
      site_name: 'NEEPU CTF',
      site_url: 'http://localhost:5173',
      api_url: 'http://localhost:5000',
      site_description: 'NEEPU 网络安全竞赛平台',
      
      // 平台状态
      maintenance_mode: false,
      maintenance_message: '系统正在维护中，敬请期待...',
      announcement: '欢迎来到 NEEPU CTF 平台！',
      
      // 功能开关
      allow_registration: true,
      allow_teams: true,
      allow_games: true,
      require_email_verification: true,
      captcha_required: false,
      
      // 邮件配置
      mail_server: 'smtp.qq.com',
      mail_port: '465',
      mail_use_ssl: true,
      mail_username: '',
      mail_password: '',
      mail_sender_name: 'NEEPU CTF',
      mail_sender_email: ''
    })
    
    const saveStatus = ref(null)
    const saving = ref(false)

    // 将字符串 'true'/'false' 转为布尔值
    function parseConfig(data) {
      const boolKeys = ['maintenance_mode', 'allow_registration', 'allow_teams', 'allow_games', 'require_email_verification', 'captcha_required', 'mail_use_ssl']
      const result = { ...data }
      for (const key of boolKeys) {
        if (key in result) {
          result[key] = result[key] === 'true' || result[key] === true
        }
      }
      return result
    }

    function mapEnvToSettings(env) {
      const out = {}
      if (!env) return out
      if (env.NEEPU_SITE_NAME) out.site_name = env.NEEPU_SITE_NAME
      if (env.NEEPU_SITE_DESCRIPTION) out.site_description = env.NEEPU_SITE_DESCRIPTION
      if (env.FRONTEND_URL) out.site_url = env.FRONTEND_URL
      if (env.API_URL) out.api_url = env.API_URL
      if (env.MAIL_SERVER) out.mail_server = env.MAIL_SERVER
      if (env.MAIL_PORT) out.mail_port = env.MAIL_PORT
      if (env.MAIL_USE_SSL) out.mail_use_ssl = env.MAIL_USE_SSL === 'true' || env.MAIL_USE_SSL === true
      if (env.MAIL_USERNAME) out.mail_username = env.MAIL_USERNAME
      if (env.MAIL_PASSWORD) out.mail_password = env.MAIL_PASSWORD
      if (env.MAIL_DEFAULT_SENDER) out.mail_sender_email = env.MAIL_DEFAULT_SENDER
      if (env.MAIL_SENDER_NAME) out.mail_sender_name = env.MAIL_SENDER_NAME
      if (env.NEEPU_ALLOW_REGISTRATION) out.allow_registration = env.NEEPU_ALLOW_REGISTRATION === 'true'
      if (env.NEEPU_ALLOW_TEAMS) out.allow_teams = env.NEEPU_ALLOW_TEAMS === 'true'
      if (env.NEEPU_ALLOW_GAMES) out.allow_games = env.NEEPU_ALLOW_GAMES === 'true'
      if (env.NEEPU_REQUIRE_EMAIL_VERIFICATION) out.require_email_verification = env.NEEPU_REQUIRE_EMAIL_VERIFICATION === 'true'
      return out
    }

    async function loadSettings() {
      try {
        const token = localStorage.getItem('neepu_token')
        // 获取 env 绑定的值
        const envRes = await axios.get('/api/admin/platform/env', { headers: { Authorization: `Bearer ${token}` } })
        const envVars = (envRes && envRes.data && envRes.data.vars) || {}
        // 获取运行时配置（DB 存储）
        const cfgRes = await axios.get('/api/admin/platform/config', { headers: { Authorization: `Bearer ${token}` } })
        const cfg = cfgRes && cfgRes.data ? cfgRes.data : {}

        settings.value = {
          ...settings.value,
          ...parseConfig(cfg),
          ...mapEnvToSettings(envVars)
        }
        showStatus('success', '设置已加载')
      } catch (e) {
        console.error('加载设置失败:', e)
        showStatus('error', '加载设置失败')
      }
    }

    async function saveSettings() {
      if (saving.value) return
      saving.value = true
      try {
        const token = localStorage.getItem('neepu_token')
        // 1) 写入 .env（管理员可编辑的键）
        const updates = {
          'NEEPU_SITE_NAME': settings.value.site_name,
          'NEEPU_SITE_DESCRIPTION': settings.value.site_description,
          'FRONTEND_URL': settings.value.site_url,
          'API_URL': settings.value.api_url,
          'MAIL_SERVER': settings.value.mail_server,
          'MAIL_PORT': settings.value.mail_port,
          'MAIL_USE_SSL': settings.value.mail_use_ssl ? 'true' : 'false',
          'MAIL_USERNAME': settings.value.mail_username,
          'MAIL_PASSWORD': settings.value.mail_password,
          'MAIL_DEFAULT_SENDER': settings.value.mail_sender_email,
          'MAIL_SENDER_NAME': settings.value.mail_sender_name,
          'NEEPU_ALLOW_REGISTRATION': settings.value.allow_registration ? 'true' : 'false',
          'NEEPU_ALLOW_TEAMS': settings.value.allow_teams ? 'true' : 'false',
          'NEEPU_ALLOW_GAMES': settings.value.allow_games ? 'true' : 'false',
          'NEEPU_REQUIRE_EMAIL_VERIFICATION': settings.value.require_email_verification ? 'true' : 'false'
        }
        await axios.post('/api/admin/platform/env', { updates }, { headers: { Authorization: `Bearer ${token}` } })

        // 2) 仍然更新数据库中的运行时配置（保持 SystemConfig 同步）
        await axios.patch('/api/admin/platform/config', settings.value, { headers: { Authorization: `Bearer ${token}` } })
        showStatus('success', '设置保存成功（已写入 .env 并同步运行时配置）')
      } catch (e) {
        console.error('保存设置失败:', e)
        const detail = e.response?.data?.error || e.response?.data?.msg || e.message
        showStatus('error', detail ? `保存设置失败：${detail}` : '保存设置失败')
      } finally {
        saving.value = false
      }
    }

    async function testEmail() {
      try {
        const token = localStorage.getItem('neepu_token')
        const email = prompt('请输入测试邮件接收地址：')
        if (!email) return
        
        showStatus('info', '正在发送测试邮件...')
        await axios.post('/api/admin/platform/test-email',
          { email },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        showStatus('success', '测试邮件已发送，请检查收件箱')
      } catch (e) {
        console.error('发送测试邮件失败:', e)
        showStatus('error', '发送测试邮件失败：' + (e.response?.data?.msg || '未知错误'))
      }
    }

    function showStatus(type, message) {
      saveStatus.value = { type, message }
      setTimeout(() => {
        saveStatus.value = null
      }, 3000)
    }

    onMounted(() => {
      loadSettings()
    })

    return {
      settings,
      saveStatus,
      saving,
      saveSettings,
      loadSettings,
      testEmail
    }
  }
}
</script>

<style scoped>

h3.page-title, h2 {
  margin-top: 0;
  color: #333;
  border-bottom: 3px solid var(--card-accent);
  padding-bottom: 12px;
  margin-bottom: 20px;
}

h3 {
  margin-top: 0;
  color: #444;
  font-size: 16px;
  border-bottom: 2px solid rgba(0,196,140,0.2);
  padding-bottom: 10px;
  margin-bottom: 15px;
}

.settings-card {
  background: var(--gradient-card-bg, var(--card-bg));
  padding: var(--fib-21);
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: var(--card-shadow);
  border: 1px solid rgba(0,0,0,0.06);
}

.form-group {
  margin-bottom: 20px;
}

.form-group.half {
  flex: 1;
}

.form-row {
  display: flex;
  gap: 20px;
}

label:not(.checkbox-label) {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
  font-size: 13px;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  box-sizing: border-box;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: var(--card-accent);
  box-shadow: 0 0 0 3px rgba(255,107,107,0.1);
}

.form-textarea {
  resize: vertical;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
  color: #333;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.help-text {
  margin: 6px 0 0 0;
  font-size: 12px;
  color: #999;
}

.settings-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid rgba(0,0,0,0.1);
}

.btn-primary, .btn-secondary {
  padding: 12px 20px;
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
  flex: 1;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.status-message {
  padding: 12px 15px;
  border-radius: 6px;
  margin-top: 15px;
  font-size: 13px;
  font-weight: 500;
}

.status-message.success {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.status-message.error {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.status-message.info {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #90caf9;
}

.btn-test {
  padding: 8px 16px;
  border: 1px solid #1976d2;
  border-radius: 6px;
  background: var(--gradient-card-bg, var(--card-bg));
  color: #1976d2;
  cursor: pointer;
  font-size: 13px;
  transition: all .2s ease;
}

.btn-test:hover {
  background: #e3f2fd;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
