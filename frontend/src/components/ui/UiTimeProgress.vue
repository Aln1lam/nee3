<template>
  <div class="ui-time-progress" :class="{ permanent }">
    <span class="ui-tp__label">{{ label }}</span>
    <div class="ui-tp__bar">
      <div
        class="ui-tp__fill"
        :style="{ transform: `scaleX(${fillRatio})` }"
      />
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

export default {
  name: 'UiTimeProgress',
  props: {
    startTime: { type: String, default: null },
    endTime: { type: String, default: null },
    permanent: { type: Boolean, default: false },
    labelOverride: { type: String, default: '' },
  },
  setup(props) {
    const now = ref(Date.now())
    let timer = null

    const label = computed(() => {
      if (props.labelOverride) return props.labelOverride
      if (props.permanent) return '永久开放'
      if (!props.startTime && !props.endTime) return ''
      const t = now.value
      const start = props.startTime ? new Date(props.startTime).getTime() : 0
      const end = props.endTime ? new Date(props.endTime).getTime() : Infinity
      if (t < start) return '距开始'
      if (t >= start && t < end) return '进行中'
      return '已结束'
    })

    const fillRatio = computed(() => {
      if (props.permanent) return 1
      if (!props.startTime || !props.endTime) return 0
      const start = new Date(props.startTime).getTime()
      const end = new Date(props.endTime).getTime()
      const total = end - start
      if (total <= 0) return 0
      const elapsed = now.value - start
      return Math.min(1, Math.max(0, elapsed / total))
    })

    onMounted(() => {
      if (!props.permanent) timer = setInterval(() => { now.value = Date.now() }, 1000)
    })
    onUnmounted(() => { if (timer) clearInterval(timer) })
    watch(() => [props.startTime, props.endTime], () => { now.value = Date.now() })

    return { label, fillRatio }
  },
}
</script>

<style scoped>
.ui-time-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  min-width: 72px;
}
.ui-tp__label { font-size: 10px; color: var(--muted); white-space: nowrap; }
.ui-tp__bar {
  width: 72px;
  height: 2px;
  background: var(--border);
  border-radius: 0;
  overflow: hidden;
}
.ui-tp__fill {
  height: 100%;
  width: 100%;
  background: var(--primary);
  transform-origin: left center;
  will-change: transform;
  transition: transform 1s linear;
}
.ui-time-progress.permanent .ui-tp__fill { background: var(--success, #51cf66); }
.ui-time-progress.permanent .ui-tp__label { color: var(--success, #51cf66); }
</style>
