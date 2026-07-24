<template>
  <div
    ref="rootRef"
    class="ui-virtual-list"
    :style="{ height: typeof height === 'number' ? `${height}px` : height }"
    @scroll.passive="onScroll"
  >
    <div class="ui-virtual-list__spacer" :style="{ height: `${totalHeight}px` }">
      <div
        class="ui-virtual-list__window"
        :style="{ transform: `translate3d(0, ${offsetY}px, 0)` }"
      >
        <div
          v-for="item in visibleItems"
          :key="keyOf(item.data, item.index)"
          class="ui-virtual-list__row"
          :style="{ height: `${itemSize}px` }"
        >
          <slot :item="item.data" :index="item.index" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { rafThrottle } from '@/utils/polling'

/**
 * 轻量虚拟列表：DOM 节点数 ≈ 可视区 + overscan，避免长列表卡顿。
 * 固定行高；超过 threshold 才启用窗口化，否则直接渲染（小列表零开销）。
 */
export default {
  name: 'UiVirtualList',
  props: {
    items: { type: Array, default: () => [] },
    itemSize: { type: Number, default: 56 },
    height: { type: [Number, String], default: 360 },
    overscan: { type: Number, default: 6 },
    /** 低于此数量不走虚拟化，直接全量渲染 */
    threshold: { type: Number, default: 80 },
    itemKey: { type: [String, Function], default: 'id' },
  },
  setup(props) {
    const rootRef = ref(null)
    const scrollTop = ref(0)
    const viewportH = ref(360)

    const useVirtual = computed(() => (props.items?.length || 0) >= props.threshold)
    const totalHeight = computed(() => (props.items?.length || 0) * props.itemSize)

    const range = computed(() => {
      const len = props.items?.length || 0
      if (!useVirtual.value) return { start: 0, end: len }
      const start = Math.max(0, Math.floor(scrollTop.value / props.itemSize) - props.overscan)
      const visible = Math.ceil(viewportH.value / props.itemSize) + props.overscan * 2
      const end = Math.min(len, start + visible)
      return { start, end }
    })

    const offsetY = computed(() => (useVirtual.value ? range.value.start * props.itemSize : 0))

    const visibleItems = computed(() => {
      const list = props.items || []
      const { start, end } = range.value
      const out = []
      for (let i = start; i < end; i++) {
        out.push({ index: i, data: list[i] })
      }
      return out
    })

    function keyOf(data, index) {
      if (typeof props.itemKey === 'function') return props.itemKey(data, index)
      if (data && props.itemKey && data[props.itemKey] != null) return data[props.itemKey]
      return index
    }

    const measure = () => {
      if (!rootRef.value) return
      viewportH.value = rootRef.value.clientHeight || 360
    }

    const onScroll = rafThrottle(() => {
      if (!rootRef.value) return
      scrollTop.value = rootRef.value.scrollTop
    })

    let ro = null
    onMounted(() => {
      measure()
      if (typeof ResizeObserver !== 'undefined' && rootRef.value) {
        ro = new ResizeObserver(rafThrottle(measure))
        ro.observe(rootRef.value)
      }
    })
    onUnmounted(() => {
      onScroll.cancel?.()
      ro?.disconnect()
      ro = null
    })

    watch(() => props.items?.length, () => {
      if (rootRef.value && rootRef.value.scrollTop > totalHeight.value) {
        rootRef.value.scrollTop = 0
        scrollTop.value = 0
      }
    })

    return {
      rootRef,
      totalHeight,
      offsetY,
      visibleItems,
      onScroll,
      keyOf,
    }
  },
}
</script>

<style scoped>
.ui-virtual-list {
  position: relative;
  overflow: auto;
  width: 100%;
  contain: strict;
  -webkit-overflow-scrolling: touch;
}
.ui-virtual-list__spacer {
  position: relative;
  width: 100%;
}
.ui-virtual-list__window {
  will-change: transform;
  contain: layout style;
}
.ui-virtual-list__row {
  box-sizing: border-box;
  width: 100%;
}
</style>
