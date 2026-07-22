<template>
  <div class="container-challenge">
    <!-- 题目信息卡片 -->
    <div class="card challenge-info">
      <h3>{{ challenge.title }}</h3>
      <div class="meta">
        <span class="category">{{ challenge.category }}</span>
        <span class="points">{{ challenge.original_points }} 分</span>
        <span class="solved">{{ solvedCount }} 队已解</span>
      </div>
      <div class="description" v-html="safeDescription"></div>
    </div>

    <!-- 容器管理区域 -->
    <div class="card container-management">
      <h4 class="docker-heading"><DockerWhaleIcon class="docker-heading-ico" /> 容器实例</h4>
      
      <!-- 加载中 -->
      <div v-if="loadingStatus" class="loading-state">
        <div class="spinner"></div>
        <p>检查容器状态中...</p>
      </div>

      <!-- 无容器 - 显示"开启容器"按钮 -->
      <div v-else-if="!hasContainer" class="no-instance">
        <div class="no-container-icon">🚀</div>
        <p>点击下方按钮启动容器实例</p>
        <button class="btn-primary" @click="startContainerAction" :disabled="isStarting || isCreatingContainer">
          {{ isCreatingContainer ? '启动中...' : '🚀 开启容器' }}
        </button>
        <p class="hint" v-if="isCreatingContainer">正在初始化容器，请稍候...</p>
      </div>

      <!-- 容器已运行 - 显示"查看容器"和操作选项 -->
      <div v-else-if="hasContainer && containerData" class="instance-info">
        <div class="container-header">
          <div class="status-badge">
            <span class="status-dot running"></span>
            <span>容器运行中</span>
          </div>
          <div class="time-remaining" v-if="timeRemaining > 0">
            ⏱️ 剩余时间: {{ formatTimeRemaining(timeRemaining) }}
          </div>
        </div>

        <div class="info-row">
          <label>容器ID:</label>
          <code>{{ containerData.container_id?.substring(0, 12) }}</code>
        </div>
        <div class="info-row">
          <label>访问地址:</label>
          <a :href="containerData.connection_url" target="_blank" class="link">{{ containerData.connection_url }}</a>
        </div>
        <div class="info-row">
          <label>端口:</label>
          <code>{{ containerData.port }}</code>
        </div>
        <div class="info-row">
          <label>状态:</label>
          <span class="status" :class="containerData.status">{{ statusLabel(containerData.status) }}</span>
        </div>
        <div class="info-row" v-if="containerData.expires_at">
          <label>过期时间:</label>
          <span>{{ formatTime(containerData.expires_at) }}</span>
        </div>

        <!-- 管理操作按钮 -->
        <div class="actions">
          <button class="btn-action btn-extend" @click="showExtendConfirm" :disabled="isExtending" v-if="canExtend">
            <span class="icon">⏱️</span>
            {{ isExtending ? '延时中...' : '延时1小时' }}
          </button>
          <button class="btn-action btn-destroy" @click="showDestroyConfirm" :disabled="isDestroying">
            <span class="icon">🗑️</span>
            {{ isDestroying ? '销毁中...' : '销毁容器' }}
          </button>
          <button class="btn-action btn-copy" @click="copyUrl">
            <span class="icon">📋</span>
            复制地址
          </button>
        </div>
      </div>
    </div>

    <!-- Flag提交区域 -->
    <div class="card flag-submission">
      <h4>🚩 提交Flag</h4>
      <div class="form-group">
        <input 
          v-model="flagInput" 
          type="text" 
          placeholder="flag{...}"
          class="form-input"
          @keyup.enter="submitFlag"
          :disabled="!hasContainer"
        />
        <p v-if="!hasContainer" class="hint">需要先启动容器</p>
      </div>
      <button class="btn-primary" @click="submitFlag" :disabled="isSubmitting || !flagInput || !hasContainer">
        {{ isSubmitting ? '提交中...' : '提交' }}
      </button>
      
      <!-- 提交历史 -->
      <div v-if="submissions.length > 0" class="submission-history">
        <h5>📝 提交历史</h5>
        <div v-for="(sub, idx) in submissions" :key="idx" class="submission-item" :class="{ correct: sub.is_correct }">
          <span class="time">{{ formatTime(sub.submitted_at) }}</span>
          <span class="flag">{{ sub.answer }}</span>
          <span class="result" :class="sub.is_correct ? 'success' : 'error'">
            {{ sub.is_correct ? '✅ 正确' : '❌ 错误' }}
          </span>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message" class="message" :class="messageType">
      {{ message }}
    </div>

    <!-- 确认对话框 - 延时 -->
    <div v-if="showExtendDialog" class="modal-overlay" @click="showExtendDialog = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>⏱️ 延时容器</h3>
          <button class="close-btn" @click="showExtendDialog = false">✕</button>
        </div>
        <div class="modal-body">
          <p>确定要延时1小时吗？</p>
          <p class="info">容器将额外运行1小时</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showExtendDialog = false">取消</button>
          <button class="btn-primary" @click="extendContainer">确认延时</button>
        </div>
      </div>
    </div>

    <!-- 确认对话框 - 销毁 -->
    <div v-if="showDestroyDialog" class="modal-overlay" @click="showDestroyDialog = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>🗑️ 销毁容器</h3>
          <button class="close-btn" @click="showDestroyDialog = false">✕</button>
        </div>
        <div class="modal-body">
          <p>确定要销毁容器吗？</p>
          <p class="warning">销毁后无法恢复，需要重新启动</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDestroyDialog = false">取消</button>
          <button class="btn-danger" @click="destroyContainer">确认销毁</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { parseMarkdownSafe } from '../utils/markdown'
import {
  getContainerStatus,
  startContainer as apiStartContainer,
  stopContainer as apiStopContainer,
  extendContainer as apiExtendContainer,
  pickRunningInstance,
} from '@/services/container'

import DockerWhaleIcon from '@/components/icons/DockerWhaleIcon.vue'

export default {
  name: 'ContainerChallenge',
  components: { DockerWhaleIcon },
  props: {
    challengeId: {
      type: Number,
      required: true
    },
    challenge: {
      type: Object,
      required: true
    },
    teamId: {
      type: Number,
      default: null
    }
  },
  data() {
    return {
      // 容器状态
      loadingStatus: true,
      hasContainer: false,
      containerData: null,
      timeRemaining: 0,
      
      // 操作状态
      isStarting: false,
      isCreatingContainer: false,
      isExtending: false,
      isDestroying: false,
      isSubmitting: false,
      
      // Flag提交
      flagInput: '',
      submissions: [],
      solvedCount: 0,
      
      // 弹窗显示
      showExtendDialog: false,
      showDestroyDialog: false,
      
      // 消息
      message: '',
      messageType: 'info',
      
      // 定时器
      timeRemainingInterval: null
    }
  },
  computed: {
    safeDescription() {
      return parseMarkdownSafe(this.challenge?.description || '')
    },
    canExtend() {
      // 检查是否可以继续延期
      if (!this.containerData) return false
      const startTime = new Date(this.containerData.started_at)
      const currentExpire = new Date(this.containerData.expires_at)
      const maxExpire = new Date(startTime.getTime() + 4 * 60 * 60 * 1000) // 4小时
      return currentExpire < maxExpire
    }
  },
  methods: {
    // ========== 容器状态查询 ==========
    async checkContainerStatus() {
      try {
        this.loadingStatus = true
        const payload = await getContainerStatus(this.challengeId)
        const running = pickRunningInstance(payload)
        this.hasContainer = !!running
        this.containerData = running
        if (running) this.startTimeRemainingTimer()
      } catch (error) {
        console.error('检查容器状态失败:', error)
        this.showMessage('检查状态失败：' + (error.response?.data?.msg || error.message), 'error')
      } finally {
        this.loadingStatus = false
      }
    },

    // ========== 容器启动 ==========
    async startContainerAction() {
      if (this.isCreatingContainer || this.isStarting) return
      try {
        this.isCreatingContainer = true
        const payload = await apiStartContainer(this.challengeId, { asyncMode: false })
        const running = pickRunningInstance(payload)
        if (running || payload?.code === 200 || payload?.success) {
          this.hasContainer = true
          this.containerData = running || (await this._refreshRunning())
          this.startTimeRemainingTimer()
          this.showMessage('✅ 容器启动成功！开始捕获流量...', 'success')
        } else {
          this.showMessage(payload?.msg || payload?.message || '启动失败', 'error')
        }
      } catch (error) {
        console.error('启动容器失败:', error)
        this.showMessage('启动失败：' + (error.response?.data?.msg || error.message), 'error')
      } finally {
        this.isCreatingContainer = false
      }
    },

    async _refreshRunning() {
      const payload = await getContainerStatus(this.challengeId)
      const running = pickRunningInstance(payload)
      this.hasContainer = !!running
      this.containerData = running
      return running
    },

    // ========== 容器延时 ==========
    showExtendConfirm() {
      this.showExtendDialog = true
    },

    async extendContainer() {
      try {
        this.isExtending = true
        this.showExtendDialog = false
        const id = this.containerData?.instance_id
        const payload = await apiExtendContainer(id)
        const d = payload?.data
        if (payload?.code === 200 || payload?.success || d) {
          if (d?.expires_at && this.containerData) this.containerData.expires_at = d.expires_at
          this.showMessage(payload?.msg || '✅ 容器已延时1小时', 'success')
          this.updateTimeRemaining()
        } else {
          this.showMessage(payload?.msg || payload?.message || '延时失败', 'error')
        }
      } catch (error) {
        console.error('延时容器失败:', error)
        this.showMessage('延时失败：' + (error.response?.data?.msg || error.message), 'error')
      } finally {
        this.isExtending = false
      }
    },

    // ========== 容器销毁 ==========
    showDestroyConfirm() {
      this.showDestroyDialog = true
    },

    async destroyContainer() {
      try {
        this.isDestroying = true
        this.showDestroyDialog = false
        const id = this.containerData?.instance_id
        const payload = await apiStopContainer(id)
        if (payload?.code === 200 || payload?.success !== false) {
          this.hasContainer = false
          this.containerData = null
          this.stopTimeRemainingTimer()
          this.showMessage('✅ 容器已销毁', 'success')
        } else {
          this.showMessage(payload?.msg || payload?.message || '销毁失败', 'error')
        }
      } catch (error) {
        console.error('销毁容器失败:', error)
        this.showMessage('销毁失败：' + (error.response?.data?.msg || error.message), 'error')
      } finally {
        this.isDestroying = false
      }
    },

    // ========== Flag提交 ==========
    async submitFlag() {
      if (this.isSubmitting) return
      if (!this.flagInput.trim()) {
        this.showMessage('请输入Flag', 'error')
        return
      }

      if (!this.hasContainer) {
        this.showMessage('需要先启动容器', 'error')
        return
      }

      try {
        this.isSubmitting = true
        const token = localStorage.getItem('neepu_token')
        
        // 统一主提交路径
        const res = await fetch(`/api/challenges/${this.challengeId}/submit`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            challenge_id: this.challengeId,
            flag: this.flagInput,
            answer: this.flagInput
          })
        })
        
        const data = await res.json()
        const payload = data?.data || data || {}
        const correct = !!(payload.is_correct || payload.correct || data.correct)
        
        if (data.code === 200 || data.success || payload.is_correct != null) {
          // 记录提交
          this.submissions.unshift({
            answer: this.flagInput,
            is_correct: correct,
            submitted_at: new Date().toISOString()
          })
          
          if (correct) {
            const pts = payload.final_score ?? payload.points_earned ?? data.points || 0
            this.showMessage(`✅ 答案正确！获得 ${pts} 分`, 'success')
            this.$emit('flag-submitted', { points: pts })
            
            // 容器已被后端自动销毁
            if (payload.container_closed || data.container_closed) {
              this.hasContainer = false
              this.containerData = null
              this.stopTimeRemainingTimer()
            } else {
              // 备用方案：1秒后刷新容器状态
              setTimeout(() => {
                this.checkContainerStatus()
              }, 1000)
            }
          } else {
            this.showMessage('❌ 答案错误，请重试', 'error')
          }
          
          this.flagInput = ''
        } else {
          this.showMessage(data.message || '提交失败', 'error')
        }
      } catch (error) {
        console.error('提交Flag失败:', error)
        this.showMessage('提交失败：' + error.message, 'error')
      } finally {
        this.isSubmitting = false
      }
    },

    // ========== 辅助方法 ==========
    copyUrl() {
      if (this.containerData && this.containerData.connection_url) {
        navigator.clipboard.writeText(this.containerData.connection_url).then(() => {
          this.showMessage('✅ 已复制到剪贴板', 'success')
        })
      }
    },

    formatTime(timeStr) {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString('zh-CN')
    },

    formatTimeRemaining(seconds) {
      if (seconds <= 0) return '已过期'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      if (hours > 0) {
        return `${hours}小时${minutes}分`
      }
      return `${minutes}分钟`
    },

    statusLabel(status) {
      const labels = {
        'running': '✅ 运行中',
        'stopped': '⚠️ 已停止',
        'error': '❌ 错误'
      }
      return labels[status] || status
    },

    showMessage(msg, type = 'info') {
      this.message = msg
      this.messageType = type
      setTimeout(() => {
        this.message = ''
      }, 4000)
    },

    updateTimeRemaining() {
      if (this.containerData && this.containerData.expires_at) {
        const now = new Date()
        const expireTime = new Date(this.containerData.expires_at)
        this.timeRemaining = Math.max(0, Math.floor((expireTime - now) / 1000))
      }
    },

    startTimeRemainingTimer() {
      this.updateTimeRemaining()
      if (this.timeRemainingInterval) {
        clearInterval(this.timeRemainingInterval)
      }
      this.timeRemainingInterval = setInterval(() => {
        this.updateTimeRemaining()
      }, 1000)
    },

    stopTimeRemainingTimer() {
      if (this.timeRemainingInterval) {
        clearInterval(this.timeRemainingInterval)
        this.timeRemainingInterval = null
      }
    }
  },
  mounted() {
    this.checkContainerStatus()
  },
  beforeUnmount() {
    this.stopTimeRemainingTimer()
  }
}
</script>

<style scoped>
.container-challenge {
  max-width: 1000px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  padding: var(--fib-21);
}

.card {
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 8px;
  padding: var(--fib-21);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #eee;
}

.card h3 {
  margin: 0 0 15px 0;
  font-size: 24px;
  color: #333;
}

.card h4 {
  margin: 0 0 15px 0;
  font-size: 18px;
  color: #333;
}

.meta {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.meta span {
  padding: 6px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.meta .points {
  background: #fff3cd;
  color: #856404;
}

.meta .solved {
  background: #d4edda;
  color: #155724;
}

.description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 10px;
}

/* ========== 加载状态 ========== */
.loading-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.spinner {
  display: inline-block;
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ========== 无容器 ========== */
.no-instance {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.no-container-icon {
  font-size: 48px;
  margin-bottom: 15px;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.no-instance p {
  margin: 10px 0;
  color: #666;
}

.no-instance .hint {
  font-size: 12px;
  color: #999;
  margin-top: 10px;
}

/* ========== 容器信息 ========== */
.instance-info {
  padding: 10px 0;
}

.container-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #f0f8ff;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #155724;
}

.status-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-dot.running {
  background: #52c41a;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.time-remaining {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.info-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row label {
  min-width: 100px;
  font-weight: 600;
  color: #333;
}

.info-row code {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 12px;
}

.info-row .link {
  color: #1890ff;
  text-decoration: none;
  word-break: break-all;
}

.info-row .link:hover {
  text-decoration: underline;
}

.status {
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
}

.status.running {
  background: #d4edda;
  color: #155724;
}

.status.stopped {
  background: #f8d7da;
  color: #721c24;
}

/* ========== 操作按钮 ========== */
.actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  flex-wrap: wrap;
}

.btn-action {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  background: var(--gradient-card-bg, var(--card-bg));
  transition: all 0.2s;
}

.btn-action .icon {
  font-size: 16px;
}

.btn-extend {
  border-color: #faad14;
  color: #856404;
  background: #fffbe6;
}

.btn-extend:hover:not(:disabled) {
  background: #fff7e6;
  border-color: #f59e0b;
}

.btn-destroy {
  border-color: #f5222d;
  color: #721c24;
  background: #fff1f0;
}

.btn-destroy:hover:not(:disabled) {
  background: #ffebe9;
  border-color: #f5222d;
}

.btn-copy {
  border-color: #1890ff;
  color: #0050b3;
  background: #e6f7ff;
}

.btn-copy:hover:not(:disabled) {
  background: #bae7ff;
  border-color: #1890ff;
}

/* ========== Flag提交 ========== */
.form-group {
  margin-bottom: 15px;
}

.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.form-input:disabled {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.form-group .hint {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.submission-history {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.submission-history h5 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #333;
}

.submission-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 12px;
  align-items: center;
}

.submission-item.correct {
  background: #f0f9ff;
  border-left: 3px solid #52c41a;
}

.submission-item .time {
  color: #999;
  min-width: 150px;
  font-size: 11px;
}

.submission-item .flag {
  flex: 1;
  font-family: monospace;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
}

.submission-item .result {
  font-weight: 600;
  min-width: 60px;
  text-align: right;
}

.submission-item .result.success {
  color: #52c41a;
}

.submission-item .result.error {
  color: #f5222d;
}

/* ========== 按钮样式 ========== */
.btn-primary, .btn-secondary, .btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0050b3;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover:not(:disabled) {
  background: #e0e0e0;
}

.btn-danger {
  background: #f5222d;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #cf1322;
  box-shadow: 0 2px 8px rgba(245, 34, 45, 0.3);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ========== 消息提示 ========== */
.message {
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
  text-align: center;
  font-weight: 500;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.message.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.message.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

/* ========== 模态框 ========== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  max-width: 400px;
  width: 90%;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--fib-21);
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: var(--fib-21);
  color: #666;
}

.modal-body p {
  margin: 0 0 10px 0;
}

.modal-body .info {
  font-size: 12px;
  color: #999;
}

.modal-body .warning {
  font-size: 12px;
  color: #f5222d;
  font-weight: 500;
}

.modal-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: var(--fib-21);
  border-top: 1px solid #eee;
}

.modal-footer .btn-primary,
.modal-footer .btn-secondary,
.modal-footer .btn-danger {
  margin: 0;
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .container-challenge {
    padding: 10px;
    gap: 15px;
  }

  .card {
    padding: 15px;
  }

  .container-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .actions {
    flex-direction: column;
  }

  .btn-action {
    width: 100%;
    justify-content: center;
  }

  .modal {
    width: 95%;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-footer .btn-primary,
  .modal-footer .btn-secondary,
  .modal-footer .btn-danger {
    width: 100%;
  }
}
.docker-heading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.docker-heading-ico {
  width: 18px !important;
  height: 18px !important;
  color: var(--primary);
}
</style>
