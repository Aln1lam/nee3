<template>
  <div class="page-wrap profile-edit-page">
    <n-card class="matrix-panel" :bordered="false">
      <template #header>
        <div class="card-title">编辑个人资料</div>
      </template>

      <div class="profile-edit-container">
        <div class="avatar-section">
          <div class="avatar-preview">
            <img :src="getAvatarUrl(form.avatar)" :alt="form.nickname || '用户头像'" />
          </div>
          <div class="avatar-upload">
            <input
              type="file"
              ref="fileInput"
              accept="image/*"
              style="display: none"
              @change="handleAvatarSelect"
            />
            <n-button @click="$refs.fileInput.click()">选择头像</n-button>
            <p class="upload-hint">支持 PNG、JPG、GIF、WebP 格式，最大 5MB</p>
          </div>
        </div>

        <n-form :model="form" ref="formRef" class="profile-form">
          <n-form-item label="昵称" required>
            <n-input v-model:value="form.nickname" />
          </n-form-item>
          <n-form-item label="用户名">
            <n-input v-model:value="form.username" placeholder="可用于登录（可选）" />
          </n-form-item>
          <n-form-item label="邮箱">
            <n-input :value="form.email" disabled />
            <template #feedback>
              <span style="font-size: 12px; color: #888;">邮箱为登录凭证，如需修改请联系管理员</span>
            </template>
          </n-form-item>
          <n-form-item label="名字">
            <n-input v-model:value="form.full_name" />
          </n-form-item>
          <n-form-item label="班级">
            <n-input v-model:value="form.class_name" />
          </n-form-item>
          <n-form-item label="方向">
            <n-input v-model:value="form.direction" />
          </n-form-item>
          <n-form-item label="个人简介">
            <n-input v-model:value="form.bio" type="textarea" rows="4" />
          </n-form-item>
          <n-form-item label="个人签名">
            <n-input v-model:value="form.signature" type="textarea" rows="3" placeholder="这个人很懒，没有个人签名" />
          </n-form-item>

          <div class="form-actions">
            <n-button @click="cancel">取消</n-button>
            <n-button type="primary" @click="saveProfile" :loading="loading">保存</n-button>
          </div>
        </n-form>
      </div>
    </n-card>
  </div>
</template>

<script>
import { ref, onMounted, inject } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton } from 'naive-ui'
import { resolveUploadUrl } from '../utils/uploadUrl'
export default {
  components: { NCard, NForm, NFormItem, NInput, NButton },
  setup() {
    const axios = inject('axios')

    const form = ref({
      nickname: '',
      username: '',
      email: '',
      full_name: '',
      class_name: '',
      direction: '',
      bio: '',
      signature: '',
      avatar: ''
    })
    const loading = ref(false)
    const formRef = ref(null)
    const fileInput = ref(null)
    const selectedFile = ref(null)

    async function load() {
      try {
        // 添加时间戳确保不会被缓存
        const r = await axios.get('/api/auth/me', {
          params: { _t: Date.now() }
        })
        if (r && r.data) {
          // Assign all fields, treating null/undefined as empty strings for display
          form.value.nickname = r.data.nickname || ''
          form.value.username = r.data.username || ''
          form.value.email = r.data.email || ''
          form.value.full_name = r.data.full_name || ''
          form.value.class_name = r.data.class_name || ''
          form.value.direction = r.data.direction || ''
          form.value.bio = r.data.bio || ''
          form.value.signature = r.data.signature || ''
          form.value.avatar = r.data.avatar || '/assets/avatar-placeholder.png'
          console.log('Profile loaded:', form.value)
        }
      } catch (e) { 
        console.warn('load profile failed', e) 
      }
    }

    function handleAvatarSelect(event) {
      const file = event.target.files?.[0]
      if (!file) return

      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('文件大小不能超过 5MB')
        return
      }

      // Preview
      const reader = new FileReader()
      reader.onload = (e) => {
        form.value.avatar = e.target.result
      }
      reader.readAsDataURL(file)

      selectedFile.value = file
    }

    function getAvatarUrl(avatarPath) {
      if (!avatarPath || avatarPath.startsWith('data:')) {
        return avatarPath || '/assets/avatar-placeholder.png'
      }
      return resolveUploadUrl(avatarPath) || '/assets/avatar-placeholder.png'
    }

    async function saveProfile() {
      loading.value = true
      try {
        const formData = new FormData()
        
        // Add text fields
        formData.append('nickname', form.value.nickname)
        if (form.value.username != null) {
          formData.append('username', form.value.username)
        }
        formData.append('full_name', form.value.full_name)
        formData.append('class_name', form.value.class_name)
        formData.append('direction', form.value.direction)
        formData.append('bio', form.value.bio)
        formData.append('signature', form.value.signature)

        // Add avatar file if selected
        if (selectedFile.value) {
          formData.append('avatar', selectedFile.value)
        }

        const r = await axios.put('/api/auth/profile', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        if (r && r.data && r.data.user) {
          const newUser = r.data.user
          
          // Update localStorage with new user data
          try { 
            localStorage.setItem('neepu_user', JSON.stringify(newUser))
          } catch (e) {}
          
          // Update local form state with fresh data
          Object.assign(form.value, newUser)
          
          // Reset file input
          selectedFile.value = null
          if (fileInput.value) {
            fileInput.value.value = ''
          }
          
          // Dispatch event for other components to refresh
          window.dispatchEvent(new Event('neepu_user_refreshed'))
          
          // Show success message
          alert('✓ 个人资料已保存')
        }
      } catch (e) { 
        console.error('save profile failed', e)
        alert('❌ 保存失败：' + (e.response?.data?.msg || e.message))
      } finally { 
        loading.value = false 
      }
    }

    function cancel() {
      try { history.back() } catch (e) {}
    }

    onMounted(() => { load() })

    return { form, loading, saveProfile, cancel, formRef, fileInput, handleAvatarSelect, getAvatarUrl }
  }
}
</script>

<style scoped>
.card-title { font-weight: 700 }

.profile-edit-container {
  display: flex;
  gap: var(--fib-34);
  align-items: flex-start;
}

.avatar-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.avatar-preview {
  width: 140px;
  height: 140px;
  border-radius: var(--card-radius);
  overflow: hidden;
  border: 2px solid var(--border);
  background: var(--hover);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-hint {
  font-size: var(--text-xs);
  color: var(--muted);
  margin: 0;
  text-align: center;
}

.profile-form {
  flex: 1;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .profile-edit-container {
    flex-direction: column;
    align-items: center;
  }

  .profile-form {
    width: 100%;
  }
}</style>