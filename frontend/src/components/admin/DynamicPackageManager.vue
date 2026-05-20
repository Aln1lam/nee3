<template>
  <div class="dynamic-package-manager">
    <div class="manager-header">
      <h3>📦 动态附件管理</h3>
      <button class="btn-primary" @click="showUploadModal = true">上传 ZIP 包</button>
    </div>

    <!-- 题目选择 -->
    <div class="section">
      <label>选择题目：</label>
      <select v-model="selectedChallengeId" @change="loadPackages">
        <option value="">-- 请选择题目 --</option>
        <option v-for="c in challenges" :key="c.id" :value="c.id">
          {{ c.title }} (ID: {{ c.id }}) - {{ getChallengeTypeName(c.challenge_type) }}
        </option>
      </select>
    </div>

    <!-- 包列表 -->
    <div v-if="selectedChallengeId" class="section">
      <h4>已上传的包 ({{ packages.length }})</h4>
      
      <table v-if="packages.length > 0" class="package-table">
        <thead>
          <tr>
            <th>变体 ID</th>
            <th>文件名</th>
            <th>哈希值</th>
            <th>大小</th>
            <th>Flag</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pkg in packages" :key="pkg.id" :class="{ inactive: !pkg.is_active }">
            <td>{{ pkg.variant_id }}</td>
            <td>{{ pkg.filename }}</td>
            <td class="code">{{ pkg.file_hash }}</td>
            <td>{{ formatSize(pkg.file_size) }}</td>
            <td class="code">
              <input 
                v-model="pkg.flag" 
                class="flag-input"
                placeholder="flag{...}"
                @change="updatePackageFlag(pkg)"
              >
            </td>
            <td>
              <span :class="['badge', pkg.is_active ? 'badge-success' : 'badge-danger']">
                {{ pkg.is_active ? '✓ 启用' : '✗ 禁用' }}
              </span>
            </td>
            <td>
              <button 
                v-if="pkg.is_active"
                class="btn-small btn-danger"
                @click="deletePackage(pkg.id)"
              >
                删除
              </button>
              <button 
                v-else
                class="btn-small btn-success"
                @click="enablePackage(pkg.id)"
              >
                启用
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty-state">
        还没有上传任何包
      </div>
    </div>

    <!-- 分配统计 -->
    <div v-if="selectedChallengeId" class="section">
      <h4>分配统计</h4>
      <div v-if="distributionStats" class="stats-grid">
        <div v-for="stat in Object.values(distributionStats)" :key="stat.variant_id" class="stat-card">
          <div class="stat-label">{{ stat.variant_id }}</div>
          <div class="stat-value">{{ stat.assigned_count }} 队已分配</div>
          <div class="stat-detail">{{ stat.downloaded_count }} 队已下载</div>
        </div>
      </div>
    </div>

    <!-- 上传模态框 -->
    <div v-if="showUploadModal" class="modal-overlay" @click="showUploadModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h4>上传动态包</h4>
          <button class="btn-close" @click="showUploadModal = false">×</button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>选择题目：</label>
            <select v-model="uploadChallengeId">
              <option value="">-- 请选择题目 --</option>
              <option v-for="c in challenges" :key="c.id" :value="c.id">
                {{ c.title }} (ID: {{ c.id }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>选择 ZIP 文件：</label>
            <input 
              type="file" 
              ref="fileInput"
              accept=".zip"
              @change="onFileSelected"
            >
            <div v-if="selectedFile" class="file-info">
              📄 {{ selectedFile.name }} ({{ formatSize(selectedFile.size) }})
            </div>
          </div>

          <div class="form-group">
            <label>Flag 配置（JSON）：</label>
            <textarea 
              v-model="flagConfig"
              placeholder='{"variant_001": "flag{...}", "variant_002": "flag{...}"}'
              rows="4"
            ></textarea>
            <small>可选：为不同的包指定 Flag。如果不指定，将使用默认值。</small>
          </div>

          <div v-if="uploading" class="progress">
            <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
            <span>{{ uploadProgress }}%</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="showUploadModal = false" :disabled="uploading">
            取消
          </button>
          <button 
            class="btn-primary" 
            @click="uploadPackage"
            :disabled="!uploadChallengeId || !selectedFile || uploading"
          >
            {{ uploading ? '上传中...' : '上传' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'DynamicPackageManager',
  setup() {
    const challenges = ref([])
    const packages = ref([])
    const distributionStats = ref({})
    
    const selectedChallengeId = ref('')
    const uploadChallengeId = ref('')
    const selectedFile = ref(null)
    const flagConfig = ref('')
    
    const showUploadModal = ref(false)
    const uploading = ref(false)
    const uploadProgress = ref(0)

    // 加载题目列表
    const loadChallenges = async () => {
      try {
        const response = await axios.get('/api/challenges/list')
        challenges.value = response.data.data.filter(c => c.challenge_type === 2) // 只显示动态附件题目
      } catch (error) {
        console.error('加载题目失败:', error)
      }
    }

    // 加载包列表
    const loadPackages = async () => {
      if (!selectedChallengeId.value) return

      try {
        const response = await axios.get(
          `/api/admin/dynamic-packages/challenges/${selectedChallengeId.value}/packages`
        )
        packages.value = response.data.packages || []
        
        // 加载分配统计
        const gameId = new URLSearchParams(window.location.search).get('game_id')
        if (gameId) {
          loadDistributionStats(gameId)
        }
      } catch (error) {
        console.error('加载包列表失败:', error)
      }
    }

    // 加载分配统计
    const loadDistributionStats = async (gameId) => {
      try {
        const response = await axios.get(
          `/api/admin/dynamic-packages/statistics/package-distribution/${gameId}`
        )
        distributionStats.value = {}
        response.data.packages.forEach(pkg => {
          distributionStats.value[pkg.variant_id] = pkg
        })
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    }

    // 文件选择
    const onFileSelected = (event) => {
      selectedFile.value = event.target.files[0]
    }

    // 上传包
    const uploadPackage = async () => {
      if (!uploadChallengeId.value || !selectedFile.value) {
        alert('请选择题目和文件')
        return
      }

      uploading.value = true
      uploadProgress.value = 0

      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)

        // 添加 Flag 配置
        if (flagConfig.value.trim()) {
          try {
            const flags = JSON.parse(flagConfig.value)
            Object.entries(flags).forEach(([variantId, flag]) => {
              formData.append(`flags[${variantId}]`, flag)
            })
          } catch (e) {
            alert('Flag 配置 JSON 格式错误')
            uploading.value = false
            return
          }
        }

        const response = await axios.post(
          `/api/admin/dynamic-packages/challenges/${uploadChallengeId.value}/upload`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
              uploadProgress.value = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              )
            }
          }
        )

        alert(`成功上传 ${response.data.packages.length} 个包`)
        
        // 刷新列表
        selectedChallengeId.value = uploadChallengeId.value
        await loadPackages()
        
        // 重置表单
        showUploadModal.value = false
        selectedFile.value = null
        flagConfig.value = ''
        uploadProgress.value = 0

      } catch (error) {
        alert('上传失败：' + (error.response?.data?.error || error.message))
      } finally {
        uploading.value = false
      }
    }

    // 更新包的 Flag
    const updatePackageFlag = async (pkg) => {
      try {
        await axios.put(
          `/api/admin/dynamic-packages/packages/${pkg.id}`,
          { flag: pkg.flag }
        )
        alert('Flag 已更新')
      } catch (error) {
        alert('更新失败：' + (error.response?.data?.error || error.message))
        loadPackages() // 刷新重置
      }
    }

    // 删除包
    const deletePackage = async (packageId) => {
      if (!confirm('确定要删除此包吗？')) return

      try {
        await axios.delete(`/api/admin/dynamic-packages/packages/${packageId}`)
        alert('包已删除')
        loadPackages()
      } catch (error) {
        alert('删除失败：' + (error.response?.data?.error || error.message))
      }
    }

    // 启用包
    const enablePackage = async (packageId) => {
      try {
        await axios.put(
          `/api/admin/dynamic-packages/packages/${packageId}`,
          { is_active: true }
        )
        loadPackages()
      } catch (error) {
        alert('启用失败：' + (error.response?.data?.error || error.message))
      }
    }

    // 辅助方法
    const formatSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    }

    const getChallengeTypeName = (type) => {
      const types = {
        0: '静态附件',
        1: '静态容器',
        2: '动态附件',
        3: '动态容器'
      }
      return types[type] || '未知'
    }

    onMounted(() => {
      loadChallenges()
    })

    return {
      challenges,
      packages,
      distributionStats,
      selectedChallengeId,
      uploadChallengeId,
      selectedFile,
      flagConfig,
      showUploadModal,
      uploading,
      uploadProgress,
      loadPackages,
      onFileSelected,
      uploadPackage,
      updatePackageFlag,
      deletePackage,
      enablePackage,
      formatSize,
      getChallengeTypeName
    }
  }
}
</script>

<style scoped>
.dynamic-package-manager {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #ddd;
}

.manager-header h3 {
  margin: 0;
  font-size: 18px;
}

.section {
  background: white;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

select, input[type="file"], textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  margin-bottom: 10px;
}

textarea {
  resize: vertical;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.file-info {
  background: #f0f0f0;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.package-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.package-table th {
  background: #f0f0f0;
  padding: 10px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #ddd;
}

.package-table td {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.package-table tr.inactive {
  opacity: 0.6;
  background: #fafafa;
}

.code {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #666;
}

.flag-input {
  width: 100%;
  padding: 4px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.badge-success {
  background: #d4edda;
  color: #155724;
}

.badge-danger {
  background: #f8d7da;
  color: #721c24;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.stat-card {
  background: #f9f9f9;
  padding: 12px;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.stat-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  color: #007bff;
  font-weight: 700;
}

.stat-detail {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #999;
  font-style: italic;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.modal-header h4 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 16px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  margin-bottom: 6px;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}

.progress {
  background: #f0f0f0;
  border-radius: 4px;
  height: 24px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 10px 0;
  position: relative;
}

.progress-bar {
  background: #007bff;
  height: 100%;
  transition: width 0.3s ease;
}

.progress span {
  position: absolute;
  color: #333;
  font-size: 12px;
  font-weight: 600;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px;
  border-top: 1px solid #eee;
}

.btn-primary, .btn-secondary, .btn-small, .btn-danger, .btn-success {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-small {
  padding: 4px 8px;
  font-size: 11px;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #1e7e34;
}
</style>
