<template>
  <div ref="chartRef" class="ui-chart" :style="{ height: height }"></div>
</template>

<script>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'UiChart',
  props: {
    option: { type: Object, required: true },
    height: { type: String, default: '280px' },
    theme: { type: String, default: '' },
  },
  emits: ['ready'],
  setup(props, { emit }) {
    const chartRef = ref(null)
    let chart = null
    let ro = null

    function init() {
      if (!chartRef.value) return
      if (chart) chart.dispose()
      chart = echarts.init(chartRef.value, props.theme || undefined)
      chart.setOption(props.option, true)
      emit('ready', chart)
    }

    function resize() {
      chart?.resize()
    }

    onMounted(async () => {
      await nextTick()
      init()
      if (typeof ResizeObserver !== 'undefined' && chartRef.value) {
        ro = new ResizeObserver(resize)
        ro.observe(chartRef.value)
      } else {
        window.addEventListener('resize', resize)
      }
    })

    onUnmounted(() => {
      ro?.disconnect()
      window.removeEventListener('resize', resize)
      chart?.dispose()
      chart = null
    })

    watch(() => props.option, (opt) => {
      if (chart && opt) chart.setOption(opt, true)
      else init()
    }, { deep: true })

    return { chartRef }
  },
}
</script>

<style scoped>
.ui-chart { width: 100%; min-height: 120px; }
</style>
