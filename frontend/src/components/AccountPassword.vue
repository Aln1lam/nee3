<template>
  <div class="account-page">
    <header class="matrix-page-head">
      <p class="matrix-page-prompt">安全设置</p>
      <h2 class="matrix-page-title">修改密码</h2>
      <p class="matrix-page-desc">8–40 位 · 含大小写字母与数字</p>
    </header>

    <div class="account-panel">
      <n-form label-placement="top" class="account-form">
        <n-form-item label="当前密码">
          <n-input v-model:value="oldPassword" type="password" show-password-on="click" placeholder="输入当前密码" />
        </n-form-item>
        <n-form-item label="新密码">
          <n-input v-model:value="newPassword" type="password" show-password-on="click" placeholder="8-40位含大小写+数字" />
        </n-form-item>
        <n-form-item label="确认新密码">
          <n-input v-model:value="confirmPassword" type="password" show-password-on="click" placeholder="再次输入新密码" @keydown.enter="submit" />
        </n-form-item>
        <div class="form-actions">
          <n-button type="primary" :loading="loading" @click="submit">保存密码</n-button>
        </div>
      </n-form>
    </div>
  </div>
</template>

<script>
import { ref, inject } from 'vue'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'

function validatePassword(pw) {
  if (!pw || pw.length < 8 || pw.length > 40) return '密码长度需 8-40 位'
  if (!/[a-z]/.test(pw) || !/[A-Z]/.test(pw) || !/\d/.test(pw)) return '密码需包含大小写字母和数字'
  return null
}

export default {
  name: 'AccountPassword',
  components: { NForm, NFormItem, NInput, NButton },
  setup() {
    const axios = inject('axios')
    const message = useMessage()
    const oldPassword = ref('')
    const newPassword = ref('')
    const confirmPassword = ref('')
    const loading = ref(false)

    async function submit() {
      const err = validatePassword(newPassword.value)
      if (err) {
        message.warning(err)
        return
      }
      if (newPassword.value !== confirmPassword.value) {
        message.warning('两次输入的新密码不一致')
        return
      }
      loading.value = true
      try {
        await axios.post('/api/auth/change-password', {
          old_password: oldPassword.value,
          new_password: newPassword.value,
        })
        message.success('密码已更新')
        oldPassword.value = ''
        newPassword.value = ''
        confirmPassword.value = ''
      } catch (e) {
        message.error(e.response?.data?.msg || '修改失败')
      } finally {
        loading.value = false
      }
    }

    return { oldPassword, newPassword, confirmPassword, loading, submit }
  },
}
</script>

<style scoped>
.account-panel {
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
}
.account-form { max-width: 100%; }
.form-actions { margin-top: 8px; }
</style>
