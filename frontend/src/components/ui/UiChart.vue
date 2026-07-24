<template>
  <div ref="chartRef" class="ui-chart" :style="{ height: height }"></div>
</template>

<script>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { rafThrottle } from '@/utils/polling'

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  CanvasRenderer,
])

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
    let lastTheme = props.theme || ''

    function ensureChart() {
      if (!chartRef.value) return null
      // 仅在首次或 theme 变更时 init；数据更新一律 setOption，禁止频繁 dispose/re-init
      if (!chart) {
        chart = echarts.init(chartRef.value, props.theme || undefined)
        lastTheme = props.theme || ''
        emit('ready', chart)
      } else if ((props.theme || '') !== lastTheme) {
        chart.dispose()
        chart = echarts.init(chartRef.value, props.theme || undefined)
        lastTheme = props.theme || ''
        emit('ready', chart)
      }
      return chart
    }

    function applyOption(opt) {
      const c = ensureChart()
      if (!c || !opt) return
      c.setOption(opt, { notMerge: true, lazyUpdate: true })
    }

    const resize = rafThrottle(() => {
      try { chart?.resize() } catch { /* ignore */ }
    })

    onMounted(async () => {
      await nextTick()
      applyOption(props.option)
      if (typeof ResizeObserver !== 'undefined' && chartRef.value) {
        ro = new ResizeObserver(resize)
        ro.observe(chartRef.value)
      } else {
        window.addEventListener('resize', resize)
      }
    })

    onUnmounted(() => {
      resize.cancel?.()
      ro?.disconnect()
      ro = null
      window.removeEventListener('resize', resize)
      try { chart?.dispose() } catch { /* ignore */ }
      chart = null
    })

    watch(() => props.option, (opt) => {
      applyOption(opt)
    }, { deep: true })

    watch(() => props.theme, () => {
      applyOption(props.option)
    })

    return { chartRef }
  },
}
</script>

<style scoped>
.ui-chart {
  width: 100%;
  min-height: 120px;
  contain: layout paint;
}
</style>
