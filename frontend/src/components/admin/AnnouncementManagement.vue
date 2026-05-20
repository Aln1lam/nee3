<template>
  <div class="announcement-management">
    <div class="section-header">
      <n-button type="primary" @click="showCreateModal = true" class="btn-create">
        + 新建公告
      </n-button>
    </div>

    <!-- 公告列表 -->
    <n-data-table
      :columns="columns"
      :data="announcements"
      :loading="loading"
      :pagination="pagination"
      :scroll-x="800"
      striped
    />

    <!-- 创建/编辑公告弹窗 -->
    <n-modal
      v-model:show="showCreateModal"
      title="新建公告"
      preset="dialog"
      positive-text="创建"
      negative-text="取消"
      @positive-click="handleCreateAnnouncement"
      :loading="submitting"
    >
      <n-form :model="newAnnouncement" :rules="formRules" ref="formRef">
        <n-form-item label="标题" path="title">
          <n-input v-model:value="newAnnouncement.title" placeholder="输入公告标题" />
        </n-form-item>
        <n-form-item label="内容" path="content">
          <n-input
            v-model:value="newAnnouncement.content"
            type="textarea"
            placeholder="输入公告内容"
            :rows="6"
          />
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- 编辑公告弹窗 -->
    <n-modal
      v-model:show="showEditModal"
      title="编辑公告"
      preset="dialog"
      positive-text="保存"
      negative-text="取消"
      @positive-click="handleUpdateAnnouncement"
      :loading="submitting"
    >
      <n-form :model="editingAnnouncement" :rules="formRules" ref="editFormRef">
        <n-form-item label="标题" path="title">
          <n-input v-model:value="editingAnnouncement.title" placeholder="输入公告标题" />
        </n-form-item>
        <n-form-item label="内容" path="content">
          <n-input
            v-model:value="editingAnnouncement.content"
            type="textarea"
            placeholder="输入公告内容"
            :rows="6"
          />
        </n-form-item>
        <n-form-item label="状态" path="is_active">
          <n-switch v-model:value="editingAnnouncement.is_active" />
          <span style="margin-left: 8px;">{{ editingAnnouncement.is_active ? '已发布' : '已下线' }}</span>
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSwitch, useMessage } from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const announcements = ref([])
const showCreateModal = ref(false)
const showEditModal = ref(false)
const formRef = ref(null)
const editFormRef = ref(null)

const newAnnouncement = ref({
  title: '',
  content: ''
})

const editingAnnouncement = ref({
  id: null,
  title: '',
  content: '',
  is_active: true
})

const formRules = {
  title: {
    required: true,
    message: '标题不能为空',
    trigger: 'blur'
  },
  content: {
    required: true,
    message: '内容不能为空',
    trigger: 'blur'
  }
}

const pagination = ref({
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  prefix: (info) => `共 ${info.itemCount} 条`
})

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 60
  },
  {
    title: '标题',
    key: 'title',
    ellipsis: true
  },
  {
    title: '内容预览',
    key: 'content',
    width: 200,
    ellipsis: true,
    render: (row) => {
      const preview = row.content.substring(0, 50)
      return preview + (row.content.length > 50 ? '...' : '')
    }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row) => row.is_active ? '已发布' : '已下线'
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString('zh-CN')
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center',
    fixed: 'right',
    render: (row) => [
      h(NButton, {
        type: 'primary',
        secondary: true,
        size: 'small',
        onClick: () => openEditModal(row)
      }, { default: () => '编辑' }),
      h(NButton, {
        type: 'error',
        secondary: true,
        size: 'small',
        style: { marginLeft: '8px' },
        onClick: () => deleteAnnouncement(row.id)
      }, { default: () => '删除' })
    ]
  }
]

const fetchAnnouncements = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('neepu_token')
    const res = await axios.get('/api/admin/platform/announcements', {
      headers: { Authorization: `Bearer ${token}` }
    })
    announcements.value = res.data
  } catch (err) {
    message.error('加载公告失败: ' + (err.response?.data?.error || err.message))
  } finally {
    loading.value = false
  }
}

const handleCreateAnnouncement = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    const token = localStorage.getItem('neepu_token')
    await axios.post('/api/admin/platform/announcements', newAnnouncement.value, {
      headers: { Authorization: `Bearer ${token}` }
    })
    message.success('公告创建成功')
    showCreateModal.value = false
    newAnnouncement.value = { title: '', content: '' }
    fetchAnnouncements()
  } catch (err) {
    if (err.response?.data?.error) {
      message.error(err.response.data.error)
    }
  } finally {
    submitting.value = false
  }
}

const openEditModal = (row) => {
  editingAnnouncement.value = {
    id: row.id,
    title: row.title,
    content: row.content,
    is_active: row.is_active
  }
  showEditModal.value = true
}

const handleUpdateAnnouncement = async () => {
  try {
    await editFormRef.value?.validate()
    submitting.value = true
    const token = localStorage.getItem('neepu_token')
    await axios.patch(
      `/api/admin/platform/announcements/${editingAnnouncement.value.id}`,
      editingAnnouncement.value,
      { headers: { Authorization: `Bearer ${token}` } }
    )
    message.success('公告更新成功')
    showEditModal.value = false
    fetchAnnouncements()
  } catch (err) {
    if (err.response?.data?.error) {
      message.error(err.response.data.error)
    }
  } finally {
    submitting.value = false
  }
}

const deleteAnnouncement = async (id) => {
  if (!confirm('确定要删除这条公告吗？')) return
  try {
    const token = localStorage.getItem('neepu_token')
    await axios.delete(`/api/admin/platform/announcements/${id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    message.success('公告已删除')
    fetchAnnouncements()
  } catch (err) {
    message.error('删除失败: ' + (err.response?.data?.error || err.message))
  }
}

import { h } from 'vue'

onMounted(() => {
  fetchAnnouncements()
})
</script>

<style scoped>
.announcement-management {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.btn-create {
  min-width: 120px;
}

:deep(.n-data-table) {
  flex: 1;
}
</style>
