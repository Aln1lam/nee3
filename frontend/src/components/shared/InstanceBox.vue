<template>
  <n-popover trigger="click" placement="bottom-end" :width="360" @update:show="onShow">
    <template #trigger>
      <button class="instance-btn" aria-label="容器实例" :class="{ active: hasActiveContainer }">
        <span class="instance-icon"><DockerWhaleIcon :active="hasActiveContainer" :size="20" /></span>
        <span v-if="runningCount" class="instance-badge">{{ runningCount }}</span>
      </button>
    </template>
    <div class="instance-panel">
      <div class="panel-title">容器实例</div>
      <p class="panel-hint">启动题目环境后，直接连接下方公网地址（IP:端口 或 http://IP:端口）</p>
      <n-spin :show="loading">
        <div v-if="loadError" class="empty error">加载失败，请关闭后重试</div>
        <div v-else-if="!instances.length" class="empty">暂无运行中的实例</div>
        <ul v-else class="instance-list">
          <li v-for="inst in instances" :key="inst.id" class="instance-item">
            <div class="inst-head">
              <span class="inst-status" :class="statusClass(inst)">{{ statusLabel(inst) }}</span>
              <span class="inst-id">#{{ inst.id }}</span>
            </div>
            <div v-if="inst.challenge_title" class="inst-challenge">{{ inst.challenge_title }}</div>
            <div class="inst-url">{{ inst.connection_url || '—' }}</div>
            <div v-if="inst.remaining_seconds != null" class="inst-remain">
              剩余 {{ formatRemain(inst.remaining_seconds) }}
            </div>
            <div class="inst-actions">
              <n-button size="tiny" quaternary @click="copyUrl(inst.connection_url)">复制</n-button>
              <n-button
                v-if="inst.is_running"
                size="tiny"
                quaternary
                :loading="extending === inst.id"
                :disabled="!!extending || !!stopping"
                @click="extendInstance(inst)"
              >延期</n-button>
              <n-button
                v-if="inst.is_running"
                size="tiny"
                type="error"
                quaternary
                :loading="stopping === inst.id"
                :disabled="!!extending || !!stopping"
                @click="stopInstance(inst)"
              >销毁</n-button>
            </div>
          </li>
        </ul>
      </n-spin>
    </div>
  </n-popover>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NPopover, NSpin, NButton, useMessage } from 'naive-ui'
import { fetchSession } from '@/services/auth'
import { listMyInstances, extendContainer, stopContainer } from '@/services/instances'
import { apiErrorMessage } from '@/utils/apiError'
import DockerWhaleIcon from '@/components/icons/DockerWhaleIcon.vue'

export default {
  name: 'InstanceBox',
  components: { NPopover, NSpin, NButton, DockerWhaleIcon },
  setup() {
    const message = useMessage()
    const instances = ref([])
    const loading = ref(false)
    const loadError = ref(false)
    const stopping = ref(null)
    const extending = ref(null)

    const runningCount = computed(() => instances.value.filter(i => i.is_running).length)
    const hasActiveContainer = computed(() => runningCount.value > 0)
    let pollTimer = null

    function statusLabel(inst) {
      if (inst.is_running) return '运行中'
      if (inst.status === 'starting') return '启动中'
      return '已停止'
    }

    function statusClass(inst) {
      if (inst.is_running) return 'running'
      if (inst.status === 'starting') return 'starting'
      return 'stopped'
    }

    function formatRemain(sec) {
      if (sec == null) return '—'
      const m = Math.floor(sec / 60)
      const s = sec % 60
      return `${m}m ${s}s`
    }

    async function load(opts = {}) {
      const silent = !!opts.silent
      if (!(await fetchSession())) { instances.value = []; return }
      if (!silent) loading.value = true
      if (!silent) loadError.value = false
      try {
        const data = await listMyInstances()
        instances.value = data?.data || data || []
        loadError.value = false
      } catch (e) {
        if (!silent) {
          instances.value = []
          loadError.value = true
          message.error(apiErrorMessage(e, '加载实例失败'))
        }
      } finally {
        if (!silent) loading.value = false
      }
    }

    function onShow(show) {
      if (show) load()
    }

    async function extendInstance(inst) {
      if (extending.value || stopping.value) return
      extending.value = inst.id
      try {
        await extendContainer(inst.id)
        message.success('实例已延长')
        await load()
      } catch (e) {
        message.error(apiErrorMessage(e, '延期失败'))
      } finally {
        extending.value = null
      }
    }

    async function stopInstance(inst) {
      if (extending.value || stopping.value) return
      stopping.value = inst.id
      try {
        await stopContainer(inst.id)
        message.success('实例已销毁')
        await load()
      } catch (e) {
        message.error(apiErrorMessage(e, '销毁失败'))
      } finally {
        stopping.value = null
      }
    }

    function copyUrl(url) {
      if (!url) return
      navigator.clipboard?.writeText(url)
        .then(() => message.success('已复制'))
        .catch(() => message.error('复制失败，请手动选择'))
    }

    onMounted(() => {
      load({ silent: true })
      pollTimer = setInterval(() => { load({ silent: true }) }, 30000)
    })
    onUnmounted(() => {
      if (pollTimer) clearInterval(pollTimer)
    })

    return {
      instances, loading, loadError, stopping, extending, runningCount, hasActiveContainer,
      statusLabel, statusClass, formatRemain,
      onShow, extendInstance, stopInstance, copyUrl,
    }
  },
}
</script>

<style scoped>
.instance-btn {
  background: transparent;
  border: 0;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  min-height: 0;
  padding: 0;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  box-shadow: none;
  overflow: visible;
  transition: background 0.3s ease, color 0.3s ease;
}
.instance-btn:hover {
  color: var(--muted);
  background: rgba(148, 163, 184, 0.08);
}
.instance-btn.active {
  color: #2496ED;
  background: rgba(36, 150, 237, 0.1);
}
.instance-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit;
  line-height: 0;
}

.instance-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--primary);
  color: #fff;
  font-size: 10px;
  min-width: 14px;
  height: 14px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}
.panel-title { font-weight: 700; margin-bottom: 4px; }
.panel-hint { font-size: var(--text-xs); color: var(--muted); margin: 0 0 12px; }
.empty { color: var(--muted); font-size: var(--text-sm); padding: 8px 0; }
.empty.error { color: var(--error, #c62828); }
.instance-list { list-style: none; margin: 0; padding: 0; }
.instance-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.inst-head { display: flex; justify-content: space-between; margin-bottom: 4px; }
.inst-status.running { color: var(--success); }
.inst-status.starting { color: var(--warning, #fab005); }
.inst-status.stopped { color: var(--muted); }
.inst-id { font-size: 11px; color: var(--muted); }
.inst-challenge { font-size: var(--text-xs); color: var(--text); margin-bottom: 4px; }
.inst-url {
  font-size: var(--text-xs);
  font-family: monospace;
  word-break: break-all;
  color: var(--primary);
  margin-bottom: 4px;
}
.inst-remain { font-size: 11px; color: var(--muted); margin-bottom: 6px; }
.inst-actions { display: flex; gap: 4px; flex-wrap: wrap; }
</style>
