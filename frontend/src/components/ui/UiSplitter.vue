<template>
  <div ref="rootRef" class="ui-splitter" :class="[`ui-splitter--${direction}`]">
    <div class="ui-splitter__pane ui-splitter__pane--first" :style="paneStyle(0)">
      <slot name="first" />
    </div>
    <div
      class="ui-splitter__handle"
      :class="{ dragging: dragging }"
      role="separator"
      :aria-orientation="direction === 'vertical' ? 'horizontal' : 'vertical'"
      @mousedown="onDragStart"
    />
    <div class="ui-splitter__pane ui-splitter__pane--second" :style="paneStyle(1)">
      <slot name="second" />
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { rafThrottle } from '@/utils/polling'

export default {
  name: 'UiSplitter',
  props: {
    direction: { type: String, default: 'vertical' }, // vertical = 上下 | horizontal = 左右
    ratio: { type: Number, default: 0.5 },
    minRatio: { type: Number, default: 0.2 },
    maxRatio: { type: Number, default: 0.8 },
  },
  emits: ['update:ratio'],
  setup(props, { emit }) {
    const rootRef = ref(null)
    const localRatio = ref(props.ratio)
    const dragging = ref(false)

    let moveHandler = null
    let upHandler = null

    function paneStyle(index) {
      const r = localRatio.value
      const size = index === 0 ? `${r * 100}%` : `${(1 - r) * 100}%`
      // flex-basis 避免反复改 height/width 触发整页 reflow 链
      return props.direction === 'vertical'
        ? { flexBasis: size, height: size, width: '100%' }
        : { flexBasis: size, width: size, height: '100%' }
    }

    function unbindDrag() {
      if (moveHandler) {
        window.removeEventListener('mousemove', moveHandler)
        moveHandler = null
      }
      if (upHandler) {
        window.removeEventListener('mouseup', upHandler)
        upHandler = null
      }
      dragging.value = false
    }

    function onDragStart(e) {
      unbindDrag()
      dragging.value = true
      const rect = rootRef.value.getBoundingClientRect()
      moveHandler = rafThrottle((ev) => {
        const pos = props.direction === 'vertical'
          ? (ev.clientY - rect.top) / rect.height
          : (ev.clientX - rect.left) / rect.width
        localRatio.value = Math.min(props.maxRatio, Math.max(props.minRatio, pos))
        emit('update:ratio', localRatio.value)
      })
      upHandler = () => {
        moveHandler?.cancel?.()
        unbindDrag()
      }
      window.addEventListener('mousemove', moveHandler)
      window.addEventListener('mouseup', upHandler)
      e.preventDefault()
    }

    onMounted(() => { localRatio.value = props.ratio })
    watch(() => props.ratio, (v) => { localRatio.value = v })
    onUnmounted(() => {
      moveHandler?.cancel?.()
      unbindDrag()
    })

    return { rootRef, dragging, paneStyle, onDragStart }
  },
}
</script>

<style scoped>
.ui-splitter {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 120px;
  overflow: hidden;
  contain: layout;
}
.ui-splitter--vertical { flex-direction: column; }
.ui-splitter--horizontal { flex-direction: row; }
.ui-splitter__pane {
  overflow: auto;
  min-width: 0;
  min-height: 0;
}
.ui-splitter__handle {
  flex-shrink: 0;
  background: var(--border);
  transition: background 0.15s;
  z-index: 2;
}
.ui-splitter--vertical .ui-splitter__handle {
  height: 6px;
  width: 100%;
  cursor: row-resize;
}
.ui-splitter--horizontal .ui-splitter__handle {
  width: 6px;
  height: 100%;
  cursor: col-resize;
}
.ui-splitter__handle:hover,
.ui-splitter__handle.dragging {
  background: var(--primary);
}
</style>
