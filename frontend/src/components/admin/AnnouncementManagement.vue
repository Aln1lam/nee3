<template>
  <div class="announcement-management content-management">
    <div class="action-bar">
      <input
        v-model="searchText"
        placeholder="搜索公告（标题、内容）..."
        class="search-input"
        @keyup.enter="applySearch"
      />
      <button type="button" class="btn-primary" @click="applySearch">搜索</button>
      <button type="button" class="btn-secondary" @click="refreshList">刷新</button>
      <button type="button" class="btn-primary" @click="showCreateModal = true">+ 新建公告</button>
    </div>

    <table class="articles-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>标题</th>
          <th>内容预览</th>
          <th>状态</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="6" class="empty-cell">加载中…</td>
        </tr>
        <tr v-else-if="!pagedRows.length">
          <td colspan="6" class="empty-cell">暂无公告</td>
        </tr>
        <tr v-for="row in pagedRows" :key="row.id">
          <td>{{ row.id }}</td>
          <td class="title">{{ row.title }}</td>
          <td class="preview">{{ previewContent(row.content) }}</td>
          <td>
            <span :class="['badge', row.is_active ? 'success' : 'default']">
              {{ row.is_active ? '已发布' : '已下线' }}
            </span>
          </td>
          <td>{{ formatDate(row.created_at) }}</td>
          <td class="actions">
            <button type="button" class="btn-small edit" @click="openEditModal(row)">编辑</button>
            <button type="button" class="btn-small delete" @click="deleteAnnouncement(row.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button type="button" :disabled="currentPage <= 1" @click="currentPage--">上一页</button>
      <span>第 {{ currentPage }} 页</span>
      <button type="button" :disabled="currentPage >= totalPages" @click="currentPage++">下一页</button>
    </div>

    <n-modal
      v-model:show="showCreateModal"
      title="新建公告"
      preset="dialog"
      positive-text="创建"
      negative-text="取消"
      :loading="submitting"
      @positive-click="handleCreateAnnouncement"
    >
      <n-form ref="formRef" :model="newAnnouncement" :rules="formRules">
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

    <n-modal
      v-model:show="showEditModal"
      title="编辑公告"
      preset="dialog"
      positive-text="保存"
      negative-text="取消"
      :loading="submitting"
      @positive-click="handleUpdateAnnouncement"
    >
      <n-form ref="editFormRef" :model="editingAnnouncement" :rules="formRules">
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

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { NModal, NForm, NFormItem, NInput, NSwitch, useMessage } from 'naive-ui'
import platformAdmin from '@/services/admin/platform'

export default {
  name: 'AnnouncementManagement',
  components: { NModal, NForm, NFormItem, NInput, NSwitch },
  setup() {
    const message = useMessage()
    const loading = ref(false)
    const submitting = ref(false)
    const announcements = ref([])
    const searchText = ref('')
    const query = ref('')
    const currentPage = ref(1)
    const pageSize = 10
    const showCreateModal = ref(false)
    const showEditModal = ref(false)
    const formRef = ref(null)
    const editFormRef = ref(null)

    const newAnnouncement = ref({ title: '', content: '' })
    const editingAnnouncement = ref({
      id: null,
      title: '',
      content: '',
      is_active: true,
    })

    const formRules = {
      title: { required: true, message: '标题不能为空', trigger: 'blur' },
      content: { required: true, message: '内容不能为空', trigger: 'blur' },
    }

    const filteredRows = computed(() => {
      const q = query.value.trim().toLowerCase()
      const list = announcements.value || []
      if (!q) return list
      return list.filter((row) => {
        const t = String(row.title || '').toLowerCase()
        const c = String(row.content || '').toLowerCase()
        return t.includes(q) || c.includes(q)
      })
    })

    const totalPages = computed(() =>
      Math.max(1, Math.ceil(filteredRows.value.length / pageSize) || 1),
    )

    const pagedRows = computed(() => {
      const start = (currentPage.value - 1) * pageSize
      return filteredRows.value.slice(start, start + pageSize)
    })

    watch(query, () => { currentPage.value = 1 })
    watch(filteredRows, () => {
      if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
    })

    function applySearch() {
      query.value = searchText.value
    }

    function previewContent(content) {
      const text = String(content || '')
      return text.length > 50 ? `${text.slice(0, 50)}…` : text
    }

    function formatDate(dateStr) {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    async function fetchAnnouncements() {
      loading.value = true
      try {
        const res = await platformAdmin.getAnnouncements()
        announcements.value = res.data || []
      } catch (err) {
        message.error('加载公告失败: ' + (err.response?.data?.error || err.message))
      } finally {
        loading.value = false
      }
    }

    async function refreshList() {
      await fetchAnnouncements()
    }

    async function handleCreateAnnouncement() {
      try {
        await formRef.value?.validate()
        submitting.value = true
        await platformAdmin.createAnnouncement(newAnnouncement.value)
        message.success('公告创建成功')
        showCreateModal.value = false
        newAnnouncement.value = { title: '', content: '' }
        await fetchAnnouncements()
      } catch (err) {
        if (err.response?.data?.error) message.error(err.response.data.error)
      } finally {
        submitting.value = false
      }
    }

    function openEditModal(row) {
      editingAnnouncement.value = {
        id: row.id,
        title: row.title,
        content: row.content,
        is_active: row.is_active,
      }
      showEditModal.value = true
    }

    async function handleUpdateAnnouncement() {
      try {
        await editFormRef.value?.validate()
        submitting.value = true
        await platformAdmin.updateAnnouncement(
          editingAnnouncement.value.id,
          editingAnnouncement.value,
        )
        message.success('公告更新成功')
        showEditModal.value = false
        await fetchAnnouncements()
      } catch (err) {
        if (err.response?.data?.error) message.error(err.response.data.error)
      } finally {
        submitting.value = false
      }
    }

    async function deleteAnnouncement(id) {
      if (!confirm('确定要删除这条公告吗？')) return
      try {
        await platformAdmin.deleteAnnouncement(id)
        message.success('公告已删除')
        await fetchAnnouncements()
      } catch (err) {
        message.error('删除失败: ' + (err.response?.data?.error || err.message))
      }
    }

    onMounted(() => {
      fetchAnnouncements()
    })

    return {
      loading,
      submitting,
      searchText,
      currentPage,
      totalPages,
      pagedRows,
      showCreateModal,
      showEditModal,
      formRef,
      editFormRef,
      newAnnouncement,
      editingAnnouncement,
      formRules,
      applySearch,
      refreshList,
      previewContent,
      formatDate,
      handleCreateAnnouncement,
      openEditModal,
      handleUpdateAnnouncement,
      deleteAnnouncement,
    }
  },
}
</script>

<style scoped>
/* 与 ContentManagement 共用 class 名；此处补齐公告页差异 */
.announcement-management {
  width: 100%;
}

.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  flex: 1 1 220px;
  min-width: 200px;
  max-width: 420px;
  height: 36px;
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  background: rgba(20, 26, 33, 0.72);
  color: #f3f4f6;
  box-sizing: border-box;
}

.btn-primary,
.btn-secondary {
  flex: 0 0 auto !important;
  width: auto !important;
  padding: 8px 18px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  transition: background 0.15s, border-color 0.15s;
}

.btn-primary {
  background: rgba(16, 185, 129, 0.18);
  border-color: rgba(16, 185, 129, 0.4);
  color: #10b981;
}

.btn-primary:hover {
  background: rgba(16, 185, 129, 0.28);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
  color: #e5e7eb;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
}

.articles-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(20, 26, 33, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 20px;
}

.articles-table thead {
  background: rgba(16, 185, 129, 0.06);
  border-bottom: 1px solid rgba(16, 185, 129, 0.18);
}

.articles-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #9ca3af;
  font-size: 13px;
}

.articles-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 13px;
  font-weight: 500;
  color: #e5e7eb;
}

.articles-table tbody tr:hover {
  background: rgba(16, 185, 129, 0.04);
}

.title {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #e5e7eb;
  font-weight: 500;
}

.preview {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #9ca3af;
}

.empty-cell {
  text-align: center !important;
  color: #9ca3af !important;
  padding: 36px 12px !important;
}

.badge {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid transparent;
}

.badge.success {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.badge.default {
  background: rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
  border-color: rgba(148, 163, 184, 0.28);
}

.actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.btn-small.edit {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.28);
}

.btn-small.edit:hover {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.btn-small.delete {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.28);
}

.btn-small.delete:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  color: #e5e7eb;
  font-weight: 500;
}

.pagination button {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  color: #e5e7eb;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
