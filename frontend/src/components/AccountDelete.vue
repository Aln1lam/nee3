<template>
  <div class="account-page">
    <header class="matrix-page-head">
      <p class="matrix-page-prompt">账号注销</p>
      <h2 class="matrix-page-title">注销账号</h2>
      <p class="matrix-page-desc">不可恢复的软删除 · 请谨慎操作</p>
    </header>

    <div class="account-panel delete-page">
      <n-alert type="warning" :bordered="false" class="warn">
        注销后邮箱将被作废，无法再用当前账号登录。提交记录等历史数据会保留关联完整性。
      </n-alert>
      <n-form label-placement="top" class="delete-form">
        <n-form-item label="当前密码">
          <n-input v-model:value="password" type="password" show-password-on="click" placeholder="输入密码确认身份" />
        </n-form-item>
        <n-form-item label="确认文案">
          <n-input v-model:value="confirm" placeholder="输入 DELETE 或「删除」" />
        </n-form-item>
      </n-form>
      <n-space justify="center">
        <n-button @click="$router.push('/account/settings/info')">取消</n-button>
        <n-button type="error" :loading="submitting" :disabled="!canSubmit" @click="doDelete">
          确认注销
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NAlert, NForm, NFormItem, NInput, NButton, NSpace, useMessage } from 'naive-ui'
import axios from 'axios'
import { logout } from '@/services/auth'
import { apiErrorMessage } from '@/utils/apiError'

export default {
  name: 'AccountDelete',
  components: { NAlert, NForm, NFormItem, NInput, NButton, NSpace },
  setup() {
    const router = useRouter()
    const message = useMessage()
    const password = ref('')
    const confirm = ref('')
    const submitting = ref(false)

    const canSubmit = computed(() =>
      !!password.value && ['DELETE', '删除', '注销'].includes(confirm.value.trim()),
    )

    async function doDelete() {
      if (!canSubmit.value || submitting.value) return
      submitting.value = true
      try {
        const { data } = await axios.post('/api/auth/delete-account', {
          password: password.value,
          confirm: confirm.value.trim(),
        })
        if (data?.code === 200) {
          message.success(data.msg || '账号已注销')
          await logout()
          router.replace('/auth')
        } else {
          message.error(data?.msg || '注销失败')
        }
      } catch (e) {
        message.error(apiErrorMessage(e, '注销失败'))
      } finally {
        submitting.value = false
      }
    }

    return { password, confirm, submitting, canSubmit, doDelete }
  },
}
</script>

<style scoped>
.account-panel {
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
  padding: 20px;
  max-width: 420px;
  margin: 0 auto;
}
.delete-page { text-align: left; }
.warn { margin-bottom: 16px; }
.delete-form { margin-bottom: 16px; }
</style>
