<template>
  <div class="user-management">
    <div class="action-bar">
      <input
        v-model="searchText"
        placeholder="搜索用户（昵称、邮箱、姓名）..."
        class="search-input"
        :disabled="loading"
        @keyup.enter="loadUsers"
      />
      <button class="btn-primary" :disabled="loading" @click="loadUsers">
        {{ loading ? '加载中…' : '搜索' }}
      </button>
      <button class="btn-secondary" :disabled="loading" @click="loadUsers">刷新</button>
    </div>

    <div v-if="loadError" class="state-msg error">加载失败，请重试</div>
    <div v-else-if="loading && !users.length" class="state-msg">加载中…</div>
    <div v-else-if="!users.length" class="state-msg">暂无用户</div>

    <table v-else class="users-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>昵称</th>
          <th>邮箱</th>
          <th>姓名</th>
          <th>身份</th>
          <th>团队</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.nickname }}</td>
          <td class="email">{{ user.email }}</td>
          <td>{{ user.full_name || '-' }}</td>
          <td>
            <span v-if="user.is_admin" class="badge admin">管理员</span>
            <span v-else-if="user.is_moderator" class="badge mod">协管</span>
            <span v-else class="badge user">用户</span>
          </td>
          <td>{{ user.team_id || '-' }}</td>
          <td>{{ formatDate(user.created_at) }}</td>
          <td class="actions">
            <button class="btn-small edit" :disabled="busy" @click="editUser(user)">编辑</button>
            <button class="btn-small delete" :disabled="busy" @click="deleteUser(user.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button @click="prevPage" :disabled="currentPage <= 1 || loading">上一页</button>
      <span>第 {{ currentPage }} 页</span>
      <button @click="nextPage" :disabled="loading || users.length === 0">下一页</button>
    </div>

    <div v-if="showEditModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>编辑用户</h3>
        <div class="form-group">
          <label>昵称</label>
          <input v-model="editForm.nickname" class="form-input" :disabled="saving" />
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="editForm.email" class="form-input" disabled />
        </div>
        <div class="form-group">
          <label>姓名</label>
          <input v-model="editForm.full_name" class="form-input" :disabled="saving" />
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" v-model="editForm.is_admin" :disabled="saving" />
            管理员权限
          </label>
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" v-model="editForm.is_moderator" :disabled="saving" />
            协管（Moderator：可审作弊/看统计）
          </label>
        </div>
        <div class="form-actions">
          <button class="btn-primary" :disabled="saving" @click="saveUser">
            {{ saving ? '保存中…' : '保存' }}
          </button>
          <button class="btn-cancel" :disabled="saving" @click="closeModal">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { apiErrorMessage } from '@/utils/apiError'
import platformAdmin from '@/services/admin/platform'

export default {
  name: 'UserManagement',
  setup() {
    const message = useMessage()

    const users = ref([])
    const loading = ref(false)
    const loadError = ref(false)
    const saving = ref(false)
    const deleting = ref(false)
    const searchText = ref('')
    const currentPage = ref(1)
    const showEditModal = ref(false)
    const editForm = ref({})
    const busy = computed(() => loading.value || saving.value || deleting.value)

    async function loadUsers() {
      if (loading.value) return
      loading.value = true
      loadError.value = false
      try {
        const res = await platformAdmin.listUsers({
          page: currentPage.value,
          search: searchText.value,
        })
        users.value = res.data?.items || res.data?.users || []
      } catch (e) {
        users.value = []
        loadError.value = true
        message.error(apiErrorMessage(e, '加载用户失败'))
      } finally {
        loading.value = false
      }
    }

    function editUser(user) {
      editForm.value = { ...user }
      showEditModal.value = true
    }

    function closeModal() {
      if (saving.value) return
      showEditModal.value = false
      editForm.value = {}
    }

    async function saveUser() {
      if (saving.value || !editForm.value?.id) return
      saving.value = true
      try {
        await platformAdmin.updateUser(editForm.value.id, editForm.value)
        message.success('保存成功')
        closeModal()
        await loadUsers()
      } catch (e) {
        message.error(apiErrorMessage(e, '保存失败'))
      } finally {
        saving.value = false
      }
    }

    async function deleteUser(userId) {
      if (deleting.value) return
      if (!confirm('确定删除此用户吗？删除后不可恢复。')) return
      deleting.value = true
      try {
        await platformAdmin.deleteUser(userId)
        message.success('删除成功')
        await loadUsers()
      } catch (e) {
        message.error(apiErrorMessage(e, '删除失败'))
      } finally {
        deleting.value = false
      }
    }

    function formatDate(dateStr) {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    function prevPage() {
      if (currentPage.value <= 1) return
      currentPage.value -= 1
    }

    function nextPage() {
      currentPage.value += 1
    }

    watch(currentPage, () => {
      loadUsers()
    })

    onMounted(() => {
      loadUsers()
    })

    return {
      users,
      loading,
      loadError,
      saving,
      busy,
      searchText,
      currentPage,
      showEditModal,
      editForm,
      loadUsers,
      editUser,
      closeModal,
      saveUser,
      deleteUser,
      formatDate,
      prevPage,
      nextPage,
    }
  },
}
</script>

<style scoped>
.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.state-msg {
  padding: 24px;
  text-align: center;
  color: var(--muted, #888);
  margin-bottom: 16px;
}
.state-msg.error { color: #c62828; }

.search-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  font-size: 14px;
}

.btn-primary, .btn-secondary {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all .2s ease;
}
.btn-primary:disabled, .btn-secondary:disabled, .btn-small:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--card-accent);
  color: white;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--card-shadow);
  margin-bottom: 20px;
}

.users-table thead {
  background: rgba(0,196,140,0.1);
  border-bottom: 2px solid rgba(0,196,140,0.2);
}

.users-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  font-size: 13px;
}

.users-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  font-size: 13px;
}

.email {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.badge.admin { background: #e3f2fd; color: #1976d2; }
.badge.mod { background: #fff3e0; color: #ef6c00; }
.badge.user { background: #f3e5f5; color: #7b1fa2; }

.actions { display: flex; gap: 8px; }

.btn-small {
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-small.edit { background: #2196f3; color: white; }
.btn-small.delete { background: #f44336; color: white; }

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 12px;
  border: 1px solid var(--card-accent);
  border-radius: 4px;
  background: var(--gradient-card-bg, var(--card-bg));
  color: var(--card-accent);
  cursor: pointer;
}
.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--gradient-card-bg, var(--card-bg));
  padding: 25px;
  border-radius: 10px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.form-group { margin-bottom: 15px; }
.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
  font-size: 13px;
}
.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  box-sizing: border-box;
}
.form-input:disabled { background: #f5f5f5; }
.form-actions { display: flex; gap: 10px; margin-top: 20px; }
.btn-cancel {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  background: #999;
  color: white;
  cursor: pointer;
  flex: 1;
}
</style>
