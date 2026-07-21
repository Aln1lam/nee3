<template>
  <n-popover trigger="click" placement="bottom-end" :width="320" @update:show="onShow">
    <template #trigger>
      <button class="notif-btn" aria-label="通知消息" :class="{ unread: hasUnread }">
        <span class="notif-icon">{{ hasUnread ? '🔔' : '🔕' }}</span>
      </button>
    </template>
    <div class="notif-panel">
      <div class="notif-header">通知消息</div>
      <div v-if="!history.length" class="notif-empty">暂无消息</div>
      <ul v-else class="notif-list">
        <li v-for="item in history" :key="item.id" :class="['notif-item', item.level]">
          <span class="notif-level">{{ levelLabel(item.level) }}</span>
          <span class="notif-msg">{{ item.message }}</span>
          <time class="notif-time">{{ formatTime(item.time) }}</time>
        </li>
      </ul>
      <button v-if="history.length" class="clear-btn" @click="clearAll">清空</button>
    </div>
  </n-popover>
</template>

<script>
import { computed } from 'vue'
import { NPopover } from 'naive-ui'
import { useNotificationHistory } from '@/composables/toast'

export default {
  name: 'UiNotificationBox',
  components: { NPopover },
  setup() {
    const { history, clearHistory, markAllRead } = useNotificationHistory()

    const hasUnread = computed(() => history.value.some(h => !h.read))

    function levelLabel(level) {
      const map = { info: '信息', warning: '警告', error: '错误', success: '成功' }
      return map[level] || level
    }

    function formatTime(ts) {
      try {
        return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      } catch { return '' }
    }

    function onShow(show) {
      if (show) markAllRead()
    }

    function clearAll() {
      clearHistory()
    }

    return { history, hasUnread, levelLabel, formatTime, onShow, clearAll }
  },
}
</script>

<style scoped>
.notif-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: 32px;
  height: 32px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.notif-btn.unread { border-color: var(--primary); }
.notif-btn.unread::after {
  content: '';
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
}
.notif-icon { font-size: 14px; }
.notif-panel { max-height: 360px; overflow-y: auto; }
.notif-header { font-weight: 700; margin-bottom: 8px; color: var(--text); }
.notif-empty { color: var(--muted); font-size: 13px; padding: 12px 0; }
.notif-list { list-style: none; margin: 0; padding: 0; }
.notif-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
.notif-item.warning .notif-level { color: #fab005; }
.notif-item.error .notif-level { color: var(--accent-red, #f83030); }
.notif-item.info .notif-level { color: var(--primary); }
.notif-level { font-size: 11px; font-weight: 600; margin-right: 6px; }
.notif-msg { color: var(--text); }
.notif-time { display: block; font-size: 11px; color: var(--muted); margin-top: 2px; }
.clear-btn {
  margin-top: 8px;
  width: 100%;
  padding: 6px;
  border: 1px solid var(--border);
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
  color: var(--muted);
}
.clear-btn:hover { background: var(--hover); }
</style>
