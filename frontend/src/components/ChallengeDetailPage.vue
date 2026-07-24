<template>
  <div class="challenge-page">
    <div class="challenge-shell">
      <div class="top-bar">
        <n-button text @click="goBack">返回</n-button>
        <div class="crumb">题目 / {{ challenge?.title || '加载中' }}</div>
      </div>

      <div class="layout">
        <section class="main-col">
          <n-card class="panel" :bordered="false">
            <template #header>
              <div class="title-row">
                <div class="title">{{ challenge?.title || '题目详情' }}</div>
                <div class="points">{{ challenge?.points || 0 }} 分值</div>
              </div>
            </template>

            <div v-if="loading" class="muted">加载中...</div>
            <div v-else-if="!challenge" class="muted">题目不存在或无权限访问</div>
            <div v-else>
              <div class="meta-row">
                <n-tag size="small">{{ challenge.category || '未分类' }}</n-tag>
                <span class="muted">解出人数: {{ stats?.unique_solvers || 0 }}</span>
              </div>

              <div class="desc" v-html="safeDescription"></div>
            </div>
          </n-card>

          <n-card class="panel" :bordered="false" title="提交">
            <n-input-group>
              <n-input
                v-model:value="answer"
                placeholder="flag{...}"
                :disabled="submitting || solved"
                @keydown.enter="submitFlag"
              />
              <n-button
                type="primary"
                @click="submitFlag"
                :loading="submitting"
                :disabled="!challenge || solved"
              >
                {{ solved ? '已解出' : '提交' }}
              </n-button>
            </n-input-group>
            <div class="tip" v-if="solved">该题已被你解出，不需要重复提交。</div>
          </n-card>

          <n-card class="panel" :bordered="false" title="提交记录">
            <div v-if="history.length === 0" class="muted">暂无提交记录</div>
            <div v-else class="history-list">
              <div v-for="item in history" :key="item.id || item.submitted_at" class="history-item">
                <span :class="item.is_correct ? 'ok' : 'bad'">{{ item.is_correct ? '正确' : '错误' }}</span>
                <span class="muted">{{ formatTime(item.submitted_at) }}</span>
              </div>
            </div>
          </n-card>
        </section>

        <aside class="side-col">
          <!-- 容器信息 -->
          <div v-if="challenge?.docker_image" class="container-card">
            <div class="container-header">终端</div>
            
            <!-- 加载中 -->
            <div v-if="containerLoading" class="container-body">
              <div class="info-line muted">加载中...</div>
            </div>

            <!-- 错误信息 -->
            <div v-else-if="containerError" class="container-body error">
              <div class="info-line error-msg">{{ containerError }}</div>
              <div style="margin-top: 12px;">
                <n-button 
                  type="primary" 
                  size="small" 
                  @click="loadContainerInstance"
                  style="width: 100%"
                >
                  重试
                </n-button>
              </div>
            </div>

            <!-- 未启动状态 -->
            <div v-else-if="!instance" class="container-body">
              <div class="info-line muted">暂未启动容器</div>
              <div style="margin-top: 12px;">
                <n-button 
                  type="primary" 
                  size="small" 
                  @click="startContainer"
                  :loading="containerLoading"
                  style="width: 100%"
                >
                  启动容器
                </n-button>
              </div>
            </div>

            <!-- 容器运行状态 -->
            <div v-else class="container-body">
              <div class="info-line">
                <span class="label">状态:</span>
                <span :class="instanceStatus === 'running' ? 'status-running' : 'status-stopped'">
                  {{ instanceStatusText }}
                </span>
              </div>

              <div v-if="instance?.port" class="service-header">
                Service-1 (TCP)
                <span class="port">{{ instance?.port }}</span>
              </div>

              <div class="service-address-box">
                {{ instance?.connection_url || '-' }}
              </div>

              <div v-if="instanceStatus === 'running'" class="info-line">
                <span class="label">剩余时间:</span>
                <span :class="remainingTime && remainingTime < 300 ? 'status-warning' : 'time-display'">
                  {{ remainingTimeFormatted }}
                </span>
              </div>

              <div class="button-group">
                <n-button 
                  text
                  type="primary"
                  @click="copyToClipboard"
                  style="width: 48%"
                >
                  复制访问
                </n-button>
                <n-button 
                  text
                  type="error"
                  @click="stopContainer"
                  :loading="containerLoading"
                  style="width: 48%"
                >
                  停止容器
                </n-button>
              </div>
            </div>
          </div>

          <n-card class="panel" :bordered="false" title="附件">
            <div v-if="challenge?.attachment_id">
              <a class="dl" :href="`/api/resources/${challenge.attachment_id}/content`" target="_blank">下载附件</a>
            </div>
            <div v-else class="muted">暂无附件</div>
          </n-card>

          <n-card class="panel" :bordered="false" title="题目统计">
            <div class="muted">通过率: {{ stats?.solve_rate || '0%' }}</div>
            <div class="muted">提交次数: {{ challenge?.submission_count || 0 }}</div>
          </n-card>
        </aside>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted, watch, computed, onUnmounted} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NInput, NButton, NInputGroup, NTag, useMessage } from 'naive-ui'
import { parseMarkdownSafe } from '../utils/markdown'

export default {
  name: 'ChallengeDetailPage',
  components: { NCard, NInput, NButton, NInputGroup, NTag },
  setup() {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()

    const loading = ref(false)
    const submitting = ref(false)
    const challenge = ref(null)
    const stats = ref(null)
    const answer = ref('')
    const history = ref([])

    // 容器相关
    const instance = ref(null)
    const containerLoading = ref(false)
    const containerError = ref(null)
    const remainingTime = ref(0)
    let timerIntervalId = null

    const solved = computed(() => history.value.some(s => s && s.is_correct))

    const instanceStatus = computed(() => {
      if (!instance.value) return 'unknown'
      if (instance.value.status === 'running') return 'running'
      if (instance.value.status === 'expired') return 'expired'
      return 'stopped'
    })

    const safeDescription = computed(() => {
      const raw = challenge.value?.description || challenge.value?.content || '暂无题目描述'
      return parseMarkdownSafe(raw)
    })

    const instanceStatusText = computed(() => {
      const status = instanceStatus.value
      if (status === 'running') return '运行中'
      if (status === 'expired') return '已过期'
      return '已停止'
    })

    const remainingTimeText = computed(() => {
      if (!remainingTime.value || remainingTime.value <= 0) return '已过期'
      const hours = Math.floor(remainingTime.value / 3600)
      const minutes = Math.floor((remainingTime.value % 3600) / 60)
      const seconds = remainingTime.value % 60
      if (hours > 0) return `${hours}时 ${minutes}分 ${seconds}秒`
      if (minutes > 0) return `${minutes}分 ${seconds}秒`
      return `${seconds}秒`
    })

    // 格式化为 HH:MM:SS
    const remainingTimeFormatted = computed(() => {
      if (!remainingTime.value || remainingTime.value <= 0) return '已过期'
      const hours = Math.floor(remainingTime.value / 3600)
      const minutes = Math.floor((remainingTime.value % 3600) / 60)
      const seconds = remainingTime.value % 60
      const pad = (n) => String(n).padStart(2, '0')
      return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
    })

    function formatTime(t) {
      if (!t) return '-'
      try {
        return new Date(t).toLocaleString('zh-CN')
      } catch (e) {
        return String(t)
      }
    }

    // 加载容器实例
    async function loadContainerInstance() {
      const id = route.params.id
      if (!id) return

      containerLoading.value = true
      containerError.value = null
      try {
        const res = await axios.get(`/api/challenges/${id}/container-status`)
        if (res.data?.data?.status === 'running' || res.data?.data?.has_container) {
          instance.value = {
            instance_id: res.data.data.instance_id,
            challenge_id: id,
            connection_url: res.data.data.connection_url,
            port: res.data.data.connection_url?.split(':')[1] || '',
            created_at: res.data.data.created_at,
            expires_at: res.data.data.expires_at,
            remaining_seconds: res.data.data.remaining_seconds || 0,
            status: res.data.data.status
          }
          remainingTime.value = instance.value.remaining_seconds || 0
          // 开始更新倒计时
          if (timerIntervalId) clearInterval(timerIntervalId)
          timerIntervalId = setInterval(() => {
            if (remainingTime.value > 0) {
              remainingTime.value--
            } else {
              clearInterval(timerIntervalId)
            }
          }, 1000)
        } else {
          instance.value = null
          if (timerIntervalId) clearInterval(timerIntervalId)
        }
      } catch (e) {
        instance.value = null
        if (timerIntervalId) clearInterval(timerIntervalId)
        const errMsg = e.response?.data?.msg || e.message || '加载容器状态失败'
        containerError.value = errMsg
        console.error('Container load error:', errMsg)
      } finally {
        containerLoading.value = false
      }
    }

    async function startContainer() {
      const id = challenge.value?.id
      if (!id || containerLoading.value) return

      containerLoading.value = true
      containerError.value = null
      try {
        const res = await axios.post(`/api/challenges/${id}/start-container`)
        if (res.data?.code === 200) {
          message.success('容器启动成功')
          await loadContainerInstance()
        } else {
          containerError.value = res.data?.msg || '启动失败'
          message.error(containerError.value)
        }
      } catch (e) {
        const errMsg = e.response?.data?.msg || '启动容器失败'
        containerError.value = errMsg
        message.error(errMsg)
      } finally {
        containerLoading.value = false
      }
    }

    async function stopContainer() {
      if (!instance.value?.instance_id || containerLoading.value) return

      containerLoading.value = true
      containerError.value = null
      try {
        const res = await axios.post(`/api/challenges/instances/${instance.value.instance_id}/stop`)
        if (res.data?.code === 200) {
          message.success('容器已停止')
          instance.value = null
          if (timerIntervalId) clearInterval(timerIntervalId)
        } else {
          const errMsg = res.data?.msg || '停止失败'
          containerError.value = errMsg
          message.error(errMsg)
        }
      } catch (e) {
        const errMsg = e.response?.data?.msg || '停止容器失败'
        containerError.value = errMsg
        message.error(errMsg)
      } finally {
        containerLoading.value = false
      }
    }

    function copyToClipboard() {
      if (!instance.value?.connection_url) return
      const text = instance.value.connection_url
      navigator.clipboard.writeText(text).then(() => {
        message.success('已复制到剪贴板')
      }).catch(() => {
        message.error('复制失败，请手动复制')
      })
    }

    async function loadDetail() {
      const id = route.params.id
      if (!id) return
      loading.value = true
      try {
        const res = await axios.get(`/api/challenges/${id}`)
        challenge.value = res.data?.data || null
        history.value = challenge.value?.submissions || []

        const statRes = await axios.get(`/api/challenges/${id}/stats`)
        stats.value = statRes.data?.data || null

        // 如果是容器题，加载容器实例
        if (challenge.value?.docker_image) {
          await loadContainerInstance()
        }
      } catch (e) {
        challenge.value = null
        history.value = []
        stats.value = null
        message.error(e.response?.data?.msg || '加载题目失败')
      } finally {
        loading.value = false
      }
    }

    async function submitFlag() {
      if (!challenge.value || submitting.value) return
      if (!answer.value.trim()) {
        message.warning('请输入 flag')
        return
      }
      submitting.value = true
      try {
        const res = await axios.post(`/api/challenges/${challenge.value.id}/submit`, {
          answer: answer.value.trim()
        })
        const payload = res.data || {}
        const isCorrect = !!payload?.data?.is_correct

        if (isCorrect) {
          message.success('答案正确')
        } else {
          message.error(payload.msg || '答案错误')
        }

        answer.value = ''
        await loadDetail()
      } catch (e) {
        message.error(e.response?.data?.msg || '提交失败')
      } finally {
        submitting.value = false
      }
    }

    function goBack() {
      if (challenge.value?.game_id) {
        router.push(`/games/${challenge.value.game_id}/challenges`)
      } else {
        router.push({ name: 'Contests' })
      }
    }

    onMounted(() => {
      loadDetail()
    })

    onUnmounted(() => {
      if (timerIntervalId) {
        clearInterval(timerIntervalId)
        timerIntervalId = null
      }
    })

    watch(() => route.params.id, () => {
      if (timerIntervalId) clearInterval(timerIntervalId)
      loadDetail()
    })

    return {
      loading,
      submitting,
      challenge,
      safeDescription,
      stats,
      answer,
      history,
      solved,
      formatTime,
      submitFlag,
      goBack,
      // 容器相关
      instance,
      containerLoading,
      containerError,
      instanceStatus,
      instanceStatusText,
      remainingTime,
      remainingTimeText,
      remainingTimeFormatted,
      loadContainerInstance,
      startContainer,
      stopContainer,
      copyToClipboard
    }
  }
}
</script>

<style scoped>
.challenge-page {
  min-height: 100%;
}

.challenge-shell {
  width: 100%;
  margin: 0;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.crumb {
  color: #6b7280;
  font-size: 14px;
}


.panel {
  margin-bottom: 16px;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 28px;
  font-weight: 700;
}

.points {
  color: #22c55e;
  font-size: 30px;
  font-weight: 700;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.desc {
  white-space: pre-wrap;
  line-height: 1.7;
}

.tip {
  margin-top: 10px;
  color: #6b7280;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.ok { color: #16a34a; font-weight: 600; }
.bad { color: #dc2626; font-weight: 600; }
.muted { color: #6b7280; }

.dl {
  color: #2563eb;
  text-decoration: none;
}

/* 容器终端风格 */
.container-card {
  margin-bottom: 16px;
  background: #1e1e1e;
  border: 1px solid #3a3a3a;
  border-radius: 6px;
  overflow: hidden;
}

.container-header {
  background: #2d2d2d;
  padding: 10px 14px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  border-bottom: 1px solid #3a3a3a;
}

.container-body {
  padding: 14px;
  color: #e0e0e0;
  font-size: 13px;
  font-family: var(--font-ui);
  line-height: 1.6;
}

.container-body.error {
  color: #ff6b6b;
}

.error-msg {
  color: #ff6b6b;
  word-break: break-word;
}

.info-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.info-line .label {
  color: #a0a0a0;
  margin-right: 8px;
}

.info-line .status-running {
  color: #22c55e;
  font-weight: 600;
}

.info-line .status-stopped {
  color: #a0a0a0;
  font-weight: 600;
}

.info-line .status-warning {
  color: #ffb74d;
  font-weight: 600;
}

.info-line .time-display {
  color: #e0e0e0;
  font-weight: 600;
  letter-spacing: 1px;
}

.service-header {
  color: #a0a0a0;
  font-size: 12px;
  margin-top: 10px;
  margin-bottom: 6px;
}

.service-header .port {
  color: #e0e0e0;
  margin-left: 8px;
}

.service-address-box {
  background: #2d2d2d;
  border: 1px solid #3a3a3a;
  padding: 8px 10px;
  border-radius: 4px;
  color: #22c55e;
  word-break: break-all;
  user-select: text;
  cursor: text;
  font-size: 12px;
  margin-bottom: 10px;
}

.button-group {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #3a3a3a;
}

.button-group :deep(.n-button) {
  font-size: 12px !important;
}

@media (max-width: 960px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>