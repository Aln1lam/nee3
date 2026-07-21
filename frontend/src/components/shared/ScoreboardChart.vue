<template>
  <div class="scoreboard-chart">
    <div v-if="showToolbar" class="scoreboard-chart__toolbar">
      <slot name="toolbar-left" />
      <UiButton size="small" variant="secondary" @click="$emit('refresh')">刷新</UiButton>
      <UiButton size="small" variant="secondary" @click="exportXlsxFile">导出 (xlsx)</UiButton>
      <UiSelect
        v-if="organizations.length"
        v-model="orgFilter"
        :options="orgOptions"
        placeholder="选择组织..."
        clearable
        style="min-width: 160px"
        @update:modelValue="onOrgChange"
      />
      <slot name="toolbar-right" />
    </div>
    <UiChart :option="chartOption" :height="height" @ready="onChartReady" />
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { UiChart, UiButton, UiSelect } from '@/components/ui'
import { exportXlsx } from '@/utils/exportXlsx'

export default {
  name: 'ScoreboardChart',
  components: { UiChart, UiButton, UiSelect },
  props: {
    series: { type: Array, default: () => [] },
    /** [{ name, data: [[time, score], ...] }] */
    height: { type: String, default: '360px' },
    organizations: { type: Array, default: () => [] },
    showToolbar: { type: Boolean, default: true },
    title: { type: String, default: '积分走势' },
  },
  emits: ['refresh', 'filter-org', 'ready'],
  setup(props, { emit }) {
    const orgFilter = ref(null)
    let chartInstance = null

    const orgOptions = computed(() =>
      props.organizations.map(o => ({
        label: typeof o === 'string' ? o : o.label,
        value: typeof o === 'string' ? o : o.value,
      })),
    )

    const chartOption = computed(() => ({
      title: { text: props.title, left: 'center', textStyle: { fontSize: 14, color: 'var(--text)' } },
      tooltip: { trigger: 'axis' },
      legend: { type: 'scroll', bottom: 0 },
      grid: { left: 48, right: 24, top: 48, bottom: 48 },
      xAxis: { type: 'time' },
      yAxis: { type: 'value', name: 'pts' },
      series: (props.series || []).map(s => ({
        name: s.name,
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: s.data || [],
      })),
    }))

    function onChartReady(chart) {
      chartInstance = chart
      emit('ready', chart)
    }

    function onOrgChange(val) {
      emit('filter-org', val)
    }

    function exportXlsxFile() {
      const rows = [['队伍', '时间', '积分']]
      for (const s of props.series || []) {
        for (const point of s.data || []) {
          const t = Array.isArray(point) ? point[0] : ''
          const v = Array.isArray(point) ? point[1] : ''
          rows.push([s.name, t, v])
        }
      }
      if (rows.length === 1) {
        rows.push(['（暂无数据）', '', ''])
      }
      exportXlsx(rows, 'scoreboard.xlsx', '积分走势')
    }

    watch(() => props.series, () => chartInstance?.resize(), { deep: true })

    return {
      orgFilter, orgOptions, chartOption,
      onChartReady, onOrgChange, exportXlsxFile,
    }
  },
}
</script>

<style scoped>
.scoreboard-chart__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}
</style>
