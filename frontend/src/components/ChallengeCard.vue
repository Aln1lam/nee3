<template>
  <div class="challenge-card-container">
    <!-- 题目卡片 -->
    <n-card hoverable class="minimal-card challenge-card">
      <!-- 分值徽章 -->
      <div class="score-badge" :class="{ dynamic: isDynamic }">
        {{ challenge.points || challenge.original_points || 100 }} PTS
        <span v-if="isDynamic" class="dynamic-label">血液</span>
      </div>

      <!-- 题目内容 -->
      <div class="chal-content">
        <h4>{{ challenge.title }}</h4>
        <p class="category">
          <span v-if="isContainerChallenge" class="docker-icon">🐳</span>
          {{ getChallengeType() }}
        </p>
        <div v-if="isContainerChallenge && instance" class="instance-status">
          <span class="status-dot running"></span>
          容器运行中
        </div>
      </div>

      <!-- 题目操作 -->
      <template #action>
        <!-- 非容器题目：直接Flag输入 -->
        <template v-if="!isContainerChallenge">
          <ChallengeModal :challenge="challenge" :joined="joined" />
        </template>

        <!-- 容器题目：容器管理 -->
        <template v-else>
          <div class="container-control">
            <!-- 容器未启动 -->
            <template v-if="!instance">
              <n-button
                block
                type="primary"
                @click="launchContainer"
                :loading="launching"
                :disabled="!joined || launching || (game && game.archived_at)"
              >
                {{ game && game.archived_at ? '已归档' : '🚀 启动容器' }}
              </n-button>
            </template>

            <!-- 容器已启动 -->
            <template v-else>
              <n-space vertical :size="8" style="width: 100%;">
                <!-- 容器信息 -->
                <div class="instance-info">
                  <div class="info-row">
                    <span class="label">地址:</span>
                    <a :href="instance.connection_url" target="_blank" class="link">
                      {{ instance.connection_url }}
                    </a>
                  </div>
                  <div class="info-row">
                    <span class="label">端口:</span>
                    <code>{{ instance.port }}</code>
                  </div>
                  <div class="info-row">
                    <span class="label">过期:</span>
                    <span :class="{ 'expiring-soon': isExpiringSoon() }">
                      {{ formatExpireTime() }}
                    </span>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <n-space>
                  <n-button
                    text
                    type="primary"
                    size="small"
                    @click="copyUrl"
                  >
                    📋 复制
                  </n-button>
                  <n-button
                    text
                    type="warning"
                    size="small"
                    @click="extendContainer"
                    :loading="extending"
                  >
                    ⏱ 延时
                  </n-button>
                  <n-button
                    text
                    type="error"
                    size="small"
                    @click="destroyContainer"
                    :loading="destroying"
                  >
                    🗑️ 销毁
                  </n-button>
                </n-space>

                <!-- Flag 输入框 -->
                <n-input-group>
                  <n-input
                    v-model:value="flag"
                    type="text"
                    placeholder="flag{...}"
                    size="small"
                    @keyup.enter="submitFlag"
                    :disabled="game && game.archived_at"
                  />
                  <n-button
                    type="success"
                    size="small"
                    @click="submitFlag"
                    :loading="submitting"
                    :disabled="game && game.archived_at"
                  >
                    {{ game && game.archived_at ? '已归档' : '提交' }}
                  </n-button>
                </n-input-group>
              </n-space>
            </template>
          </div>
        </template>
      </template>
    </n-card>

    <!-- Flag提交历史 Modal -->
    <n-modal
      v-model:show="showFlagHistory"
      title="提交历史"
      preset="dialog"
      size="small"
    >
      <div v-if="flagHistory.length > 0" class="flag-history">
        <div v-for="(item, idx) in flagHistory" :key="idx" class="history-item" :class="{ correct: item.is_correct }">
          <div class="history-time">{{ formatTime(item.submitted_at) }}</div>
          <div class="history-flag">{{ item.flag_submitted }}</div>
          <div class="history-result">
            <span v-if="item.is_correct" class="badge success">✓ 正确</span>
            <span v-else class="badge error">✗ 错误</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-history">还未提交过 Flag</div>
    </n-modal>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue'
import {
  NCard, NButton, NSpace, NInput, NInputGroup, NModal, useMessage
} from 'naive-ui'
import Challenge from './Challenge.vue'

export default {
  components: {
    NCard, NButton, NSpace, NInput, NInputGroup, NModal, Challenge,
    ChallengeModal: Challenge  // 别名兼容
  },
  props: {
    challenge: {
      type: Object,
      required: true
    },
    joined: {
      type: Boolean,
      default: false
    },
    teamId: {
      type: Number,
      default: null
    },
    game: {
      type: Object,
      default: null
    }
  },
  setup(props) {
    const axios = inject('axios')
    const message = useMessage()

    // 状态
    const instance = ref(null)
    const flag = ref('')
    const launching = ref(false)
    const destroying = ref(false)
    const extending = ref(false)
    const submitting = ref(false)
    const flagHistory = ref([])
    const showFlagHistory = ref(false)
    const refreshTimer = ref(null)

    // 计算属性
    const isContainerChallenge = computed(() => {
      return props.challenge.challenge_type === 1 || props.challenge.challenge_type === 3
    })

    const isDynamic = computed(() => {
      return props.challenge.challenge_type === 2 || props.challenge.challenge_type === 3
    })

    // 方法
    const getChallengeType = () => {
      const types = {
        0: '静态文件题',
        1: '共享容器题',
        2: '动态文件题',
        3: '动态容器题'
      }
      return types[props.challenge.challenge_type] || '未知题目'
    }

    const launchContainer = async () => {
      if (!props.joined) {
        message.warning('请先加入竞赛')
        return
      }

      try {
        launching.value = true
        const response = await axios.post(`/api/container/start/${props.challenge.id}`, {
          team_id: props.teamId
        })

        if (response.data.success) {
          instance.value = response.data.data
          message.success('✓ 容器已启动')
          startRefreshTimer()
        } else {
          message.error(response.data.message || '启动失败')
        }
      } catch (error) {
        message.error(error.response?.data?.message || error.message)
      } finally {
        launching.value = false
      }
    }

    const destroyContainer = async () => {
      if (!window.confirm('确定要销毁这个容器吗？')) return

      try {
        destroying.value = true
        const response = await axios.post(`/api/container/stop/${instance.value.instance_id}`)

        if (response.data.success) {
          instance.value = null
          message.success('✓ 容器已销毁')
          stopRefreshTimer()
        } else {
          message.error(response.data.message || '销毁失败')
        }
      } catch (error) {
        message.error(error.response?.data?.message || error.message)
      } finally {
        destroying.value = false
      }
    }

    const extendContainer = async () => {
      try {
        extending.value = true
        // 延时2小时
        const response = await axios.post(`/api/container/extend/${instance.value.instance_id}`, {
          hours: 2
        })

        if (response.data.success) {
          instance.value.expires_at = response.data.data.expires_at
          message.success('✓ 容器已延时 2 小时')
        } else {
          message.error(response.data.message || '延时失败')
        }
      } catch (error) {
        message.error(error.response?.data?.message || error.message)
      } finally {
        extending.value = false
      }
    }

    const submitFlag = async () => {
      if (!flag.value.trim()) {
        message.warning('请输入 Flag')
        return
      }

      try {
        submitting.value = true
        const response = await axios.post('/api/container/submit-flag', {
          challenge_id: props.challenge.id,
          flag: flag.value,
          team_id: props.teamId
        })

        if (response.data.success) {
          if (response.data.correct) {
            message.success(`✓ 答案正确！获得 ${response.data.points} 分`)
            flag.value = ''
            // Flag正确时，后端会销毁容器，需要清空前端状态
            if (response.data.container_closed) {
              instance.value = null
              stopRefreshTimer()
            }
          } else {
            message.error('✗ 答案错误，请重试')
          }
        } else {
          message.error(response.data.message || '提交失败')
        }
      } catch (error) {
        message.error(error.response?.data?.message || error.message)
      } finally {
        submitting.value = false
      }
    }

    const copyUrl = () => {
      if (instance.value?.connection_url) {
        navigator.clipboard.writeText(instance.value.connection_url).then(() => {
          message.success('✓ 已复制到剪贴板')
        })
      }
    }

    const formatExpireTime = () => {
      if (!instance.value?.expires_at) return '未知'
      const expire = new Date(instance.value.expires_at)
      const now = new Date()
      const diff = expire - now
      const minutes = Math.floor(diff / 60000)

      if (minutes < 0) return '已过期'
      if (minutes < 1) return '即将过期'
      if (minutes < 60) return `${minutes} 分钟后`
      return new Date(instance.value.expires_at).toLocaleTimeString('zh-CN')
    }

    const isExpiringSoon = () => {
      if (!instance.value?.expire_time) return false
      const expire = new Date(instance.value.expire_time)
      const now = new Date()
      const minutes = Math.floor((expire - now) / 60000)
      return minutes < 15 && minutes >= 0
    }

    const formatTime = (timeStr) => {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString('zh-CN')
    }

    const startRefreshTimer = () => {
      // 每30秒刷新一次容器信息
      if (refreshTimer.value) clearInterval(refreshTimer.value)
      refreshTimer.value = setInterval(async () => {
        if (instance.value) {
          try {
            const response = await axios.get(`/api/container/instance/${instance.value.instance_id}`)
            if (response.data.success) {
              instance.value = response.data.data
            } else {
              // 容器已销毁或不存在，清空实例
              instance.value = null
              stopRefreshTimer()
            }
          } catch (error) {
            console.error('Failed to refresh container status:', error)
          }
        }
      }, 30000)
    }

    const stopRefreshTimer = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
        refreshTimer.value = null
      }
    }

    // 生命周期
    onMounted(async () => {
      // 容器题目需要检查是否有已运行的实例
      if (isContainerChallenge.value) {
        try {
          const response = await axios.get(`/api/container/instance/${props.challenge.id}`)
          if (response.data.success && response.data.data) {
            instance.value = response.data.data
            startRefreshTimer()
          }
        } catch (error) {
          // 没有运行的容器实例，保持为null
          console.log('No running container instance')
        }
      }
    })

    onUnmounted(() => {
      stopRefreshTimer()
    })

    return {
      instance,
      flag,
      launching,
      destroying,
      extending,
      submitting,
      flagHistory,
      showFlagHistory,
      isContainerChallenge,
      isDynamic,
      getChallengeType,
      launchContainer,
      destroyContainer,
      extendContainer,
      submitFlag,
      copyUrl,
      formatExpireTime,
      isExpiringSoon,
      formatTime
    }
  }
}
</script>

<style scoped>
.challenge-card-container {
  width: 100%;
}

.minimal-card {
  position: relative;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 1px solid rgba(255, 82, 82, 0.3);
  border-radius: 8px;
}

.score-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: linear-gradient(135deg, #ff5252 0%, #ff1744 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.score-badge.dynamic {
  background: linear-gradient(135deg, #ff9100 0%, #ff6f00 100%);
}

.dynamic-label {
  font-size: 10px;
  opacity: 0.8;
}

.chal-content {
  padding-bottom: 20px;
}

.chal-content h4 {
  margin: 0 0 8px 0;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.chal-content .category {
  margin: 0;
  color: #aaa;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.docker-icon {
  font-size: 14px;
}

.instance-status {
  margin-top: 8px;
  padding: 8px;
  background: rgba(76, 175, 80, 0.1);
  border-left: 2px solid #4caf50;
  border-radius: 4px;
  font-size: 12px;
  color: #4caf50;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.running {
  background: #4caf50;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0.5; }
}

.container-control {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.instance-info {
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
  color: #ccc;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  line-height: 1.4;
}

.info-row .label {
  color: #999;
  min-width: 50px;
}

.info-row .link {
  color: #64b5f6;
  text-decoration: none;
  word-break: break-all;
}

.info-row .link:hover {
  text-decoration: underline;
}

.info-row code {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 2px;
  font-family: monospace;
  color: #81c784;
}

.info-row .expiring-soon {
  color: #ff9800;
  font-weight: 600;
}

.flag-history {
  max-height: 400px;
  overflow-y: auto;
}

.history-item {
  padding: 10px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-left: 3px solid #ff5252;
  border-radius: 4px;
  font-size: 12px;
}

.history-item.correct {
  border-left-color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
}

.history-time {
  color: #999;
  font-size: 11px;
  margin-bottom: 4px;
}

.history-flag {
  color: #ccc;
  font-family: monospace;
  word-break: break-all;
  margin-bottom: 4px;
}

.history-result {
  display: flex;
  justify-content: flex-end;
}

.badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 2px;
  font-weight: 600;
}

.badge.success {
  background: #4caf50;
  color: white;
}

.badge.error {
  background: #ff5252;
  color: white;
}

.empty-history {
  text-align: center;
  color: #999;
  padding: 20px;
  font-size: 12px;
}
</style>
