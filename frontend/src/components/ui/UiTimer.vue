<template>
  <div v-if="visible" class="ui-timer">
    <span v-if="phaseLabel" class="ui-timer__label">{{ phaseLabel }}</span>
    <span class="ui-timer__value">{{ display }}</span>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

function pad(n) {
  return String(n).padStart(2, '0')
}

function formatMs(ms) {
  if (ms <= 0) return '00:00:00'
  const s = Math.floor(ms / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${pad(h)}:${pad(m)}:${pad(sec)}`
}

export default {
  name: 'UiTimer',
  props: {
    /** ISO 目标时间，倒计时到该时刻*/
    targetTime: { type: String, default: null },
    /** 距开始的开始时间*/
    startTime: { type: String, default: null },
    /** 距结束的结束时间 */
    endTime: { type: String, default: null },
    /** 直接秒数倒计时*/
    seconds: { type: Number, default: null },
    label: { type: String, default: '' },
  },
  emits: ['finish'],
  setup(props, { emit }) {
    const now = ref(Date.now())
    const tickSeconds = ref(props.seconds)
    let timer = null
    let finished = false

    const phaseLabel = computed(() => {
      if (props.label) return props.label
      if (props.seconds != null) return '倒计时'
      if (props.targetTime) return '倒计时'
      if (!props.startTime && !props.endTime) return ''
      const t = now.value
      const start = props.startTime ? new Date(props.startTime).getTime() : 0
      const end = props.endTime ? new Date(props.endTime).getTime() : Infinity
      if (t < start) return '距开始'
      if (t < end) return '距结束'
      return '已结束'
    })

    const remainingMs = computed(() => {
      if (props.seconds != null) return Math.max(0, (tickSeconds.value || 0) * 1000)
      if (props.targetTime) {
        return Math.max(0, new Date(props.targetTime).getTime() - now.value)
      }
      const t = now.value
      const start = props.startTime ? new Date(props.startTime).getTime() : 0
      const end = props.endTime ? new Date(props.endTime).getTime() : Infinity
      if (t < start) return start - t
      if (t < end) return end - t
      return 0
    })

    const display = computed(() => formatMs(remainingMs.value))
    const visible = computed(() => !!(props.targetTime || props.startTime || props.endTime || props.seconds != null))

    function checkFinish() {
      if (!finished && remainingMs.value <= 0) {
        finished = true
        emit('finish')
      }
    }

    onMounted(() => {
      timer = setInterval(() => {
        now.value = Date.now()
        if (props.seconds != null && tickSeconds.value > 0) {
          tickSeconds.value -= 1
        }
        checkFinish()
      }, 1000)
    })

    onUnmounted(() => { if (timer) clearInterval(timer) })

    watch(() => props.seconds, (v) => {
      tickSeconds.value = v
      finished = false
    })

    watch(remainingMs, checkFinish)

    return { phaseLabel, display, visible }
  },
}
</script>

<style scoped>
.ui-timer {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  min-width: 90px;
}
.ui-timer__label { font-size: 10px; color: var(--muted); }
.ui-timer__value {
  font-size: var(--text-sm);
  font-weight: 700;
  font-family: var(--font-hacker);
  color: var(--primary);
}
</style>
