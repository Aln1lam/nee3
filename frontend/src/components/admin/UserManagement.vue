<template>
  <div class="user-management">
    

    <div class="action-bar">
      <input 
        v-model="searchText" 
        placeholder="搜索用户（昵称、邮箱、姓名）..." 
        class="search-input"
        @keyup.enter="loadUsers"
      />
      <button class="btn-primary" @click="loadUsers">搜索</button>
      <button class="btn-secondary" @click="loadUsers">刷新</button>
    </div>

    <table class="users-table">
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
            <span v-if="user.is_admin" class="badge admin">🔧 管理员</span>
            <span v-else class="badge user">👤 用户</span>
          </td>
          <td>{{ user.team_id || '-' }}</td>
          <td>{{ formatDate(user.created_at) }}</td>
          <td class="actions">
            <button class="btn-small edit" @click="editUser(user)">编辑</button>
            <button class="btn-small delete" @click="deleteUser(user.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 分页 -->
    <div class="pagination">
      <button @click="currentPage--" :disabled="currentPage <= 1">上一页</button>
      <span>第 {{ currentPage }} 页</span>
      <button @click="currentPage++">下一页</button>
    </div>

    <!-- 编辑模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>编辑用户</h3>
        <div class="form-group">
          <label>昵称</label>
          <input v-model="editForm.nickname" class="form-input" />
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="editForm.email" class="form-input" disabled />
        </div>
        <div class="form-group">
          <label>姓名</label>
          <input v-model="editForm.full_name" class="form-input" />
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" v-model="editForm.is_admin" />
            管理员权限
          </label>
        </div>
        <div class="form-actions">
          <button class="btn-primary" @click="saveUser">保存</button>
          <button class="btn-cancel" @click="closeModal">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted } from 'vue'

export default {
  name: 'UserManagement',
  setup() {
    const axios = inject('axios')
    
    const users = ref([])
    const searchText = ref('')
    const currentPage = ref(1)
    const showEditModal = ref(false)
    const editForm = ref({})

    async function loadUsers() {
      try {
        const token = localStorage.getItem('neepu_token')
        const res = await axios.get('/api/admin/platform/users', {
          params: {
            page: currentPage.value,
            search: searchText.value
          },
          headers: { Authorization: `Bearer ${token}` }
        })
        users.value = res.data.items
      } catch (e) {
        console.error('加载用户失败:', e)
        alert('加载用户失败')
      }
    }

    function editUser(user) {
      editForm.value = { ...user }
      showEditModal.value = true
    }

    function closeModal() {
      showEditModal.value = false
      editForm.value = {}
    }

    async function saveUser() {
      try {
        const token = localStorage.getItem('neepu_token')
        await axios.patch(`/api/admin/platform/users/${editForm.value.id}`, 
          editForm.value,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        alert('保存成功')
        closeModal()
        loadUsers()
      } catch (e) {
        console.error('保存失败:', e)
        alert('保存失败')
      }
    }

    async function deleteUser(userId) {
      if (!confirm('确定删除此用户吗？删除后不可恢复。')) return
      
      try {
        const token = localStorage.getItem('neepu_token')
        await axios.delete(`/api/admin/platform/users/${userId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        alert('删除成功')
        loadUsers()
      } catch (e) {
        console.error('删除失败:', e)
        alert('删除失败')
      }
    }

    function formatDate(dateStr) {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    onMounted(() => {
      loadUsers()
    })

    return {
      users,
      searchText,
      currentPage,
      showEditModal,
      editForm,
      loadUsers,
      editUser,
      closeModal,
      saveUser,
      deleteUser,
      formatDate
    }
  }
}
</script>

<style scoped>
h2 {
  margin-top: 0;
  color: #333;
  border-bottom: 3px solid var(--card-accent);
  padding-bottom: 12px;
  margin-bottom: 20px;
}

.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

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

.btn-primary {
  background: var(--card-accent);
  color: white;
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

.users-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
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

.users-table tbody tr:hover {
  background: rgba(0,196,140,0.03);
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

.badge.admin {
  background: #e3f2fd;
  color: #1976d2;
}

.badge.user {
  background: #f3e5f5;
  color: #7b1fa2;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn-small {
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all .2s ease;
}

.btn-small.edit {
  background: #2196f3;
  color: white;
}

.btn-small.delete {
  background: #f44336;
  color: white;
}

.btn-small:hover {
  opacity: 0.9;
  transform: scale(1.05);
}

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
  background: white;
  color: var(--card-accent);
  cursor: pointer;
  transition: all .2s ease;
}

.pagination button:hover:not(:disabled) {
  background: var(--card-accent);
  color: white;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 25px;
  border-radius: 10px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.form-group {
  margin-bottom: 15px;
}

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

.form-input:disabled {
  background: #f5f5f5;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-cancel {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  background: #999;
  color: white;
  cursor: pointer;
  flex: 1;
}

.btn-cancel:hover {
  opacity: 0.9;
}
</style>
