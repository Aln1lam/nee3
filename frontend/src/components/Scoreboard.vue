<template>
  <MatrixShell
    prompt=""
    title="积分排行"
    subtitle="SCORE · BOARD"
    page-prompt="积分排行"
    page-title="赛事排行榜"
    page-desc="实时积分 · 解题数 · 最后提交"
    :items="navItems"
  >
    <template #sidebar-footer>
      <router-link :to="`/games/${gameId}`" class="sidebar-link">
        <span class="link-code">GME</span>
        <span>返回赛事</span>
      </router-link>
      <router-link to="/games" class="sidebar-link">
        <span class="link-code">CTF</span>
        <span>赛事列表</span>
      </router-link>
    </template>

    <div class="scoreboard-layout">
      <div class="matrix-panel scoreboard-panel matrix-data-panel">
        <div class="scoreboard-toolbar">
          <div>
            <span class="link-code">SB</span>
            <strong>Game #{{ gameId }}</strong>
          </div>
          <div class="toolbar-actions">
            <n-button size="small" :type="showCurve ? 'primary' : 'default'" @click="toggleCurve">积分曲线</n-button>
            <n-button size="small" @click="refresh">刷新</n-button>
            <n-button size="small" quaternary @click="goBack">返回</n-button>
          </div>
        </div>
        <div v-if="showCurve" ref="curveRef" class="score-curve"></div>
        <n-spin :show="loading">
          <table v-if="items.length" class="scoreboard-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>队伍</th>
                <th>得分</th>
                <th>解题</th>
                <th>人数</th>
                <th>最后提交</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(it, idx) in items"
                :key="it.team_id || idx"
                class="scoreboard-row"
                :class="{ top3: idx < 3 }"
              >
                <td>{{ it.rank || idx + 1 }}</td>
                <td>{{ it.team_name }}</td>
                <td>{{ it.total_points }}</td>
                <td>{{ it.solved_challenges }}</td>
                <td>{{ it.members_count }}</td>
                <td>{{ formatTime(it.last_submission_time) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">
            <p class="matrix-page-prompt">{{ loadError ? '排行榜暂时不可用' : '暂无排行数据' }}</p>
            <p class="muted">{{ loadError ? '排行榜加载失败，请刷新重试' : '暂无排行数据' }}</p>
          </div>
        </n-spin>
      </div>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, watch, inject, computed, nextTick, onUnmounted } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])
import { useRouter } from 'vue-router'
import { NButton, NSpin } from 'naive-ui'
import { MatrixShell } from '@/components/shared'

export default {
  name: 'Scoreboard',
  components: { MatrixShell, NButton, NSpin },
  props: { gameId: { type: [String, Number], required: true } },
  setup(props) {
    const axios = inject('axios')
    const router = useRouter()
    const items = ref([])
    const showCurve = ref(false)
    const curveRef = ref(null)
    let curveChart = null
    const loading = ref(false)
    const loadError = ref(false)
    const navItems = computed(() => [{ code: 'SB', label: '排行榜', active: true }])

    function formatTime(timeStr) {
      if (!timeStr) return '-'
      try {
        return new Date(timeStr).toLocaleString('zh-CN')
      } catch {
        return timeStr
      }
    }

    async function load() {
      if (!props.gameId) return
      loading.value = true
      loadError.value = false
      try {
        const { data } = await axios.get(`/api/ctf/games/${props.gameId}/scoreboard`)
        items.value = data.data?.rankings || data?.rankings || []
      } catch (e) {
        console.error('Failed to load scoreboard:', e)
        items.value = []
        loadError.value = true
      } finally {
        loading.value = false
      }
    }

    function toggleCurve() {
      showCurve.value = !showCurve.value
      if (showCurve.value) loadTimeline()
    }

    async function loadTimeline() {
      try {
        const { data } = await axios.get(`/api/ctf/games/${props.gameId}/scoreboard/timeline`)
        const payload = data?.data || data || {}
        const series = payload.series || []
        await nextTick()
        if (!curveRef.value) return
        if (!curveChart) curveChart = echarts.init(curveRef.value)
        curveChart.setOption({
          tooltip: { trigger: 'axis' },
          legend: { type: 'scroll', top: 0 },
          grid: { left: 48, right: 16, top: 36, bottom: 28 },
          xAxis: { type: 'time' },
          yAxis: { type: 'value', name: 'pts' },
          series: (Array.isArray(series) ? series : []).slice(0, 8).map((s) => ({
            name: s.team_name || s.name || 'team',
            type: 'line',
            showSymbol: false,
            data: (s.data || s.points || []).map((p) => [p.time || p[0], p.points ?? p[1]]),
          })),
        })
      } catch {
        /* empty timeline ok */
      }
    }

    function refresh() {
      load()
      if (showCurve.value) loadTimeline()
    }
    function goBack() { router.push(`/games/${props.gameId}`) }

    watch(() => props.gameId, load, { immediate: true })
    onUnmounted(() => { try { curveChart?.dispose() } catch { /* ignore */ } })

    return { items, loading, loadError, navItems, refresh, goBack, formatTime, showCurve, curveRef, toggleCurve }
  },
}
</script>

<style scoped>
.toolbar-actions {
  display: flex;
  gap: var(--fib-8);
}

.empty-state {
  padding: var(--fib-34);
  text-align: center;
  color: var(--muted);
}
.score-curve { width: 100%; height: 260px; margin-bottom: 12px; }
</style>
