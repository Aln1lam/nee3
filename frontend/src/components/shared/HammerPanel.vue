<template>
  <div class="hammer-panel">
    <div v-if="disabled" class="hammer-disabled">
      ⚠️ 锤子服务在训练场中不可用，请通过赛事入口联系官方。
    </div>
    <template v-else>
      <div class="hammer-hint">
        与官方/选手实时沟通，可直接索要 flag 提示或你卡住的步骤即可。      </div>

      <n-spin :show="loading">
        <div ref="listRef" class="hammer-messages">
          <div v-if="!messages.length && !loading" class="empty">暂无消息，有问题请在此提</div>
          <div
            v-for="msg in visibleMessages"
            :key="msg.id"
            class="hammer-msg"
            :class="{ staff: msg.is_staff, mine: msg.user_id === currentUserId }"
          >
            <div class="msg-head">
              <span class="msg-author">{{ msg.is_staff ? '裁判' : (msg.nickname || '选手') }}</span>
              <time class="msg-time">{{ formatTime(msg.created_at) }}</time>
            </div>
            <p class="msg-body">{{ msg.content }}</p>
          </div>
        </div>
      </n-spin>

      <div class="hammer-input">
        <n-input
          v-model:value="draft"
          type="textarea"
          placeholder="输入你的问题..."
          :rows="2"
          :disabled="sending"
          @keydown.ctrl.enter="send"
        />
        <n-button type="primary" :loading="sending" :disabled="!draft.trim()" @click="send">
          发送
        </n-button>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { NInput, NButton, NSpin, useMessage } from 'naive-ui'
import { getHammer, postHammer } from '@/services/challenges'
import { apiErrorMessage } from '@/utils/apiError'
import { createVisibilityPoll, POLL_INTERVALS } from '@/utils/polling'
import { getUser } from '@/services/auth'
import { useToast } from '@/composables/toast'

export default {
  name: 'HammerPanel',
  components: { NInput, NButton, NSpin },
  props: {
    challengeId: { type: [Number, String], required: true },
    gameId: { type: [Number, String], default: null },
    disabled: { type: Boolean, default: false },
  },
  setup(props) {
    const message = useMessage()
    const toast = useToast()

    const messages = ref([])
    const loading = ref(false)
    const sending = ref(false)
    const draft = ref('')
    const listRef = ref(null)
    const currentUserId = ref(null)
    const poll = createVisibilityPoll(() => load(true), POLL_INTERVALS.hammer)
    // 长会话只渲染最近 120 条，避免消息 DOM 无限膨胀
    const visibleMessages = computed(() => {
      const list = messages.value || []
      return list.length > 120 ? list.slice(-120) : list
    })

    function getUserId() {
      const u = getUser() || {}
      currentUserId.value = u.id || null
      return u.id
    }

    function formatTime(t) {
      if (!t) return ''
      try {
        return new Date(t).toLocaleString('zh-CN', {
          month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
        })
      } catch { return t }
    }

    async function scrollBottom() {
      await nextTick()
      const el = listRef.value
      if (el) el.scrollTop = el.scrollHeight
    }

    async function load(silent = false) {
      if (!props.challengeId || props.disabled) return
      if (!silent) loading.value = true
      try {
        const data = await getHammer(props.challengeId)
        const rows = data?.data || []
        const prevLen = messages.value.length
        messages.value = rows
        if (rows.length > prevLen && prevLen > 0) {
          const last = rows[rows.length - 1]
          if (last?.is_staff) {
            toast.info(`锤子回复：${(last.content || '').slice(0, 40)}`)
            try {
              window.dispatchEvent(new CustomEvent('neepu_hammer_message', {
                detail: { challengeId: props.challengeId, message: last },
              }))
            } catch { /* ignore */ }
          }
        }
        await scrollBottom()
      } catch (e) {
        if (!silent) message.error(apiErrorMessage(e, '加载消息失败'))
      } finally {
        if (!silent) loading.value = false
      }
    }

    async function send() {
      const text = draft.value.trim()
      if (!text || sending.value) return
      sending.value = true
      try {
        await postHammer(props.challengeId, text)
        draft.value = ''
        await load(true)
        message.success('已发送')
      } catch (e) {
        message.error(apiErrorMessage(e, '发送失败'))
      } finally {
        sending.value = false
      }
    }

    function startPoll() {
      poll.stop()
      if (props.disabled) return
      poll.start()
    }

    watch(() => props.challengeId, () => {
      messages.value = []
      load()
      startPoll()
    })

    watch(() => props.disabled, (d) => {
      if (d) poll.stop()
      else startPoll()
    })

    onMounted(() => {
      getUserId()
      if (!props.disabled) {
        load()
        startPoll()
      }
    })

    onUnmounted(() => poll.stop())

    return {
      messages, visibleMessages, loading, sending, draft, listRef, currentUserId,
      formatTime, send,
    }
  },
}
</script>

<style scoped>
.hammer-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 200px;
}
.hammer-disabled {
  padding: 24px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
}
.hammer-hint {
  font-size: var(--text-xs);
  color: var(--muted);
  padding: 8px 10px;
  background: var(--hover);
  border-radius: var(--radius-md);
}
.hammer-messages {
  max-height: 280px;
  overflow-y: auto;
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.empty { color: var(--muted); font-size: var(--text-sm); text-align: center; padding: 24px; }
.hammer-msg {
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  background: var(--card-bg);
  border: 1px solid var(--border);
  max-width: 92%;
}
.hammer-msg.mine { align-self: flex-end; border-color: rgba(0, 120, 214, 0.3); }
.hammer-msg.staff {
  align-self: flex-start;
  border-color: rgba(81, 207, 102, 0.35);
  background: rgba(81, 207, 102, 0.06);
}
.msg-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 11px;
}
.msg-author { font-weight: 700; color: var(--primary); }
.hammer-msg.staff .msg-author { color: var(--success, #51cf66); }
.msg-time { color: var(--muted); }
.msg-body { margin: 0; font-size: var(--text-sm); line-height: 1.5; white-space: pre-wrap; }
.hammer-input {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.hammer-input :deep(.n-input) { flex: 1; }
</style>
