<template>
  <div class="todo-distribution">
    <div class="section-header">
    </div>

    <n-card class="distribution-card">
      <n-form :model="form" :rules="formRules" ref="formRef">
        <!-- 选择用户 -->
        <n-form-item label="选择用户" path="user_ids">
          <div class="user-selection">
            <!-- 搜索框 -->
            <n-input
              v-model:value="userSearchText"
              placeholder="搜索用户（昵称或邮箱）"
              clearable
              style="margin-bottom: 12px;"
            />

            <!-- 全选复选框 -->
            <div style="margin-bottom: 12px;">
              <n-checkbox
                :checked="allSelected"
                :indeterminate="partialSelected"
                @update:checked="toggleSelectAll"
              >
                {{ allSelected ? '取消全选' : '全选' }}
              </n-checkbox>
            </div>

            <!-- 用户列表 -->
            <div class="user-list">
              <n-checkbox-group v-model:value="form.user_ids">
                <div v-for="user in filteredUsers" :key="user.id" class="user-item">
                  <n-checkbox :value="user.id" />
                  <span class="user-name">{{ user.nickname }}</span>
                  <span class="user-email">{{ user.email }}</span>
                </div>
              </n-checkbox-group>
            </div>

            <div class="selection-info">
              已选择 {{ form.user_ids.length }} / {{ users.length }} 个用户
            </div>
          </div>
        </n-form-item>

        <!-- 代办内容 -->
        <n-form-item label="代办内容" path="text">
          <n-input
            v-model:value="form.text"
            type="textarea"
            placeholder="输入要分发的代办任务内容"
            :rows="5"
            show-count
            maxlength="500"
          />
        </n-form-item>

        <!-- 操作按钮 -->
        <n-form-item>
          <n-space>
            <n-button type="primary" @click="handleDistribute" :loading="submitting">
              分发代办
            </n-button>
            <n-button @click="resetForm">重置</n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 分发历史 -->
    <n-card title="最近分发" class="history-card">
      <n-spin :show="historyLoading">
        <div v-if="distributionHistory.length === 0" class="empty-state">
          <p>暂无分发记录</p>
        </div>
        <n-list v-else>
          <n-list-item v-for="record in distributionHistory" :key="record.id">
            <div class="history-item">
              <div class="history-header">
                <span class="history-text">分发给 {{ record.count }} 个用户</span>
                <span class="history-time">{{ formatTime(record.created_at) }}</span>
              </div>
              <div v-if="record.recipients && record.recipients.length" class="history-recipients">
                分发给：{{ record.recipients.map(r => r.nickname || r.email).slice(0,10).join(', ') }}
                <span v-if="record.recipients.length > 10"> ... 等 {{ record.recipients.length }} 人</span>
              </div>
              <div class="history-content">{{ record.text }}</div>
            </div>
          </n-list-item>
        </n-list>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  NForm,
  NFormItem,
  NInput,
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NCard,
  NSpace,
  NList,
  NListItem,
  NSpin,
  useMessage
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const historyLoading = ref(false)
const formRef = ref(null)
const users = ref([])
const distributionHistory = ref([])
const userSearchText = ref('')

const form = ref({
  user_ids: [],
  text: ''
})

const formRules = {
  user_ids: {
    type: 'array',
    required: true,
    message: '必须至少选择一个用户',
    trigger: 'change'
  },
  text: {
    required: true,
    message: '代办内容不能为空',
    trigger: 'blur'
  }
}

const filteredUsers = computed(() => {
  if (!userSearchText.value) return users.value
  const keyword = userSearchText.value.toLowerCase()
  return users.value.filter(
    (u) => u.nickname.toLowerCase().includes(keyword) || u.email.toLowerCase().includes(keyword)
  )
})

const allSelected = computed(() => {
  return form.value.user_ids.length === filteredUsers.value.length && filteredUsers.value.length > 0
})

const partialSelected = computed(() => {
  return form.value.user_ids.length > 0 && form.value.user_ids.length < filteredUsers.value.length
})

const toggleSelectAll = () => {
  if (allSelected.value) {
    form.value.user_ids = []
  } else {
    form.value.user_ids = filteredUsers.value.map((u) => u.id)
  }
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('neepu_token') || localStorage.getItem('token')
    const res = await axios.get('/api/admin/platform/users', {
      headers: { Authorization: `Bearer ${token}` }
    })
    users.value = res.data.items || res.data.users || res.data
  } catch (err) {
    message.error('加载用户列表失败: ' + (err.response?.data?.error || err.message))
  } finally {
    loading.value = false
  }
}

const fetchDistributionHistory = async () => {
  historyLoading.value = true
  try {
    const token = localStorage.getItem('neepu_token') || localStorage.getItem('token')
    // 从日志 API 获取最近的分发记录（API 返回 { items: [...] }）
    const res = await axios.get('/api/admin/platform/logs', {
      headers: { Authorization: `Bearer ${token}` }
    })
    // 筛选代办相关的日志
    const items = res.data.items || res.data || []
    const todoLogs = items.filter((log) => log.action && log.action.includes('todo'))
    // 将日志条目映射为前端需要的字段：{ id, count, text, created_at }
    distributionHistory.value = todoLogs.slice(0, 5).map((log) => {
      let meta = null
      try {
        meta = log.meta ? JSON.parse(log.meta) : null
      } catch (e) {
        meta = null
      }
      return {
        id: log.id,
        count: (meta && meta.count) || null,
        text: log.target_name || (meta && meta.text) || '',
        recipients: (meta && meta.recipients) || null,
        created_at: log.created_at
      }
    })
  } catch (err) {
    console.warn('加载分发历史失败:', err)
  } finally {
    historyLoading.value = false
  }
}

const handleDistribute = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    const token = localStorage.getItem('neepu_token') || localStorage.getItem('token')
    const response = await axios.post(
      '/api/admin/platform/distribute-todos',
      {
        user_ids: form.value.user_ids,
        text: form.value.text
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )

    message.success(response.data.message)
    resetForm()
    fetchDistributionHistory()
  } catch (err) {
    if (err.response?.data?.error) {
      message.error(err.response.data.error)
    } else {
      message.error('分发失败: ' + err.message)
    }
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    user_ids: [],
    text: ''
  }
  userSearchText.value = ''
  formRef.value?.restoreValidation()
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchUsers()
  fetchDistributionHistory()
})
</script>

<style scoped>
.todo-distribution {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.section-header {
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.distribution-card {
  margin-bottom: 20px;
}

.user-selection {
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  padding: 12px;
  background-color: #fafafa;
  max-height: 400px;
  overflow-y: auto;
}

.user-list {
  margin: 12px 0;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.user-item:last-child {
  border-bottom: none;
}

.user-name {
  font-weight: 500;
  flex: 1;
}

.user-email {
  color: #999;
  font-size: 12px;
  flex: 0 0 auto;
}

.selection-info {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.history-card {
  flex: 1;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.history-item {
  padding: 12px 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-text {
  font-weight: 500;
  color: #333;
}

.history-time {
  font-size: 12px;
  color: #999;
}

.history-content {
  color: #666;
  font-size: 14px;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
  word-break: break-word;
}

.history-recipients {
  font-size: 13px;
  color: #444;
  margin-bottom: 6px;
}
</style>
