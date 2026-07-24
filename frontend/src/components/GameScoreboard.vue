<template>
  <div class="game-scoreboard-page">
    <n-spin :show="loading">
      <div v-if="loadError" class="gsb-empty">
        <p class="matrix-page-prompt">排行榜暂时不可用</p>
        <p class="muted">排行榜加载失败，请刷新重试</p>
        <button type="button" class="gsb-refresh-btn" @click="refresh">刷新</button>
      </div>

      <template v-else>
        <div class="trend-chart-card">
          <div class="trend-chart-head">
            <h3 class="trend-chart-title">
              <span class="link-code">TRD</span>
              <span>积分走势图</span>
            </h3>
            <div class="trend-chart-actions">
              <button type="button" class="gsb-icon-btn" title="刷新" @click="refresh">↻</button>
              <select v-model="chartScope" class="gsb-org-select" title="走势范围">
                <option value="top">TOP 队伍走势</option>
                <option value="mine" :disabled="!myTeamId">仅看本队</option>
              </select>
              <select v-model="orgFilter" class="gsb-org-select">
                <option value="">全部队伍 / 组织</option>
                <option v-for="o in orgOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
            </div>
          </div>
          <div id="score-trend-chart" ref="curveRef" class="chart-container" />
        </div>

        <div class="scoreboard-table-card">
          <div class="table-header">
            <h3 class="table-title">
              <span class="link-code">RNK</span>
              <span>实时排名 (TOP TEAMS)</span>
            </h3>
          </div>

          <div v-if="rankList.length" class="table-scroll">
            <table class="gsb-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>队伍 / 选手</th>
                  <th>解题进度</th>
                  <th class="col-right">总积分</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(team, index) in visibleRankList"
                  :key="team.id || index"
                  :class="{ 'is-mine': myTeamId && team.id === myTeamId }"
                >
                  <td class="col-rank">
                    <span v-if="team.rank === 1" class="rank-badge rank-1">🥇 1</span>
                    <span v-else-if="team.rank === 2" class="rank-badge rank-2">🥈 2</span>
                    <span v-else-if="team.rank === 3" class="rank-badge rank-3">🥉 3</span>
                    <span v-else class="rank-num">{{ team.rank }}</span>
                  </td>
                  <td class="col-team">
                    <span class="team-name">{{ team.name }}</span>
                    <span v-if="myTeamId && team.id === myTeamId" class="team-mine-tag">本队</span>
                    <span v-if="team.school" class="team-school">#{{ team.school }}</span>
                  </td>
                  <td class="col-solved">{{ team.solvedCount || 0 }} 题已解决</td>
                  <td class="col-right col-score">{{ team.score || 0 }} pts</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="gsb-empty compact">
            <p class="muted">{{ items.length ? '当前组织下暂无队伍' : '暂无排行数据' }}</p>
          </div>
          <div v-if="hasMoreRanks" class="gsb-load-more">
            <button type="button" class="gsb-refresh-btn" @click="loadMoreRanks">
              加载更多（已显示 {{ visibleRankList.length }} / {{ rankList.length }}）
            </button>
          </div>
        </div>
      </template>
    </n-spin>
  </div>
</template>

<script>
import { ref, watch, inject, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { createVisibilityPoll, debounce, rafThrottle, POLL_INTERVALS } from '@/utils/polling'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  CanvasRenderer,
])
import { NSpin } from 'naive-ui'

const CHART_COLORS = [
  '#5ED9A8', '#60A5FA', '#FBBF24', '#F472B6',
  '#A78BFA', '#34D399', '#F87171', '#38BDF8',
  '#FB923C', '#2DD4BF',
]

function formatAxisTime(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return String(iso)
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return String(iso)
  }
}

function mulberry32(seed) {
  let a = seed >>> 0
  return function () {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** 开发预览：每队独立散乱解题时间戳 → [[ts, score], ...] */
function buildMockStepChartData(rankTeams) {
  const endTime = Date.now()
  const startTime = endTime - 5 * 3600 * 1000
  const duration = endTime - startTime

  const names = (rankTeams || []).slice(0, 5).map((t, i) => t.name || ('Mock Team ' + (i + 1)))
  while (names.length < 5) names.push('Mock Team ' + (names.length + 1))

  const profiles = [
    { seed: 0x51a7e01, solvesMin: 10, solvesMax: 14 },
    { seed: 0x62b8f12, solvesMin: 8, solvesMax: 13 },
    { seed: 0x73c9023, solvesMin: 7, solvesMax: 12 },
    { seed: 0x84da134, solvesMin: 6, solvesMax: 11 },
    { seed: 0x95eb245, solvesMin: 6, solvesMax: 10 },
  ]

  const teams = names.map((name, ti) => {
    const profile = profiles[ti]
    const rnd = mulberry32(profile.seed)
    const color = CHART_COLORS[ti % CHART_COLORS.length]
    const solveCount = profile.solvesMin + Math.floor(rnd() * (profile.solvesMax - profile.solvesMin + 1))

    const stamps = []
    for (let i = 0; i < solveCount; i++) {
      const offset = Math.floor((0.04 + rnd() * 0.92) * duration)
      stamps.push(startTime + offset + Math.floor(rnd() * 50000))
    }
    stamps.sort((a, b) => a - b)

    let pts = 0
    const timeSeriesData = [[startTime, 0]]
    let prev = -1
    for (let i = 0; i < stamps.length; i++) {
      let ts = stamps[i]
      if (ts <= prev) ts = prev + 60 * 1000 + Math.floor(rnd() * 30 * 1000)
      prev = ts
      const gain = 100 + Math.floor(rnd() * 201)
      pts += gain
      timeSeriesData.push([ts, pts])
    }
    timeSeriesData.push([endTime, pts])
    if (ti === 0 && timeSeriesData.length >= 5) {
      const mid = Math.floor(timeSeriesData.length / 2)
      const anchor = timeSeriesData[mid]
      const dipTs = anchor[0] + 90 * 1000
      const dipPts = Math.max(0, Math.round(anchor[1] * 0.78))
      timeSeriesData.splice(mid + 1, 0, [dipTs, dipPts])
      for (let k = mid + 2; k < timeSeriesData.length; k++) {
        timeSeriesData[k][1] = Math.max(dipPts, Math.round(timeSeriesData[k][1] * 0.92))
      }
    }
    return { name, timeSeriesData, color }
  })

  return {
    teams,
    isBaseline: false,
    isMock: true,
  }
}

/**
 * ret2shell maintain_score 余弦衰减（与后端 ScoringService.calculate_ret2shell_score 对齐）
 * difficulty 字段 = decay（到达最低分所需解题队数，2–50）
 */
function calcDynamicScore(originalPoints, n, minScoreRate = 0.25, difficulty = 10) {
  const initial = Number(originalPoints) || 0
  let rate = Number(minScoreRate)
  if (!Number.isFinite(rate)) rate = 0.25
  rate = Math.max(0, Math.min(1, rate))
  const minimum = Math.floor(initial * rate)
  let decay = Math.round(Number(difficulty))
  if (!Number.isFinite(decay)) decay = 10
  decay = Math.max(2, Math.min(50, decay))
  const N = Number(n) || 0
  if (N < 1) return initial
  if (N >= decay) return minimum
  const relativeRatio = (N - 1) / (decay - 1)
  const cosTheta = Math.cos(relativeRatio * Math.PI)
  const normalized = (cosTheta + 1) / 2
  return Math.round(minimum + (initial - minimum) * normalized)
}

/**
 * 西电 ECharts/ZRender 式 Timeline 前端重演。
 * 每个事件时刻 T：按当时 N(c,T) 重算全场动态分，再对每队 Σ Score(c,T)。
 * 他队解出同题 → Score 下降 → 折线垂直下挫。严禁历史分累加。
 *
 * @returns {Record<string|number, Array<[number, number]>>} teamId → [[tsMs, totalScore], ...]
 */
function buildStepTimelineData(submissions, challenges, teams) {
  const subs = (Array.isArray(submissions) ? submissions : [])
    .map((s) => ({
      team_id: s.team_id ?? s.teamId,
      challenge_id: s.challenge_id ?? s.challengeId,
      created_at: s.created_at || s.submitted_at || s.time,
    }))
    .filter((s) => s.team_id != null && s.challenge_id != null && s.created_at)

  const challengeList = (Array.isArray(challenges) ? challenges : []).map((c) => ({
    id: c.id,
    original_points: Number(c.original_points ?? c.points ?? 0) || 0,
    min_score_rate: c.min_score_rate != null ? Number(c.min_score_rate) : 0.25,
    difficulty: c.difficulty != null ? Number(c.difficulty) : 10,
  }))

  const teamList = (Array.isArray(teams) ? teams : []).map((t) => ({
    id: t.id ?? t.team_id,
    name: t.name || t.team_name || `Team #${t.id ?? t.team_id}`,
  })).filter((t) => t.id != null)

  const seriesMap = {}
  teamList.forEach((t) => { seriesMap[t.id] = [] })

  if (!subs.length || !challengeList.length || !teamList.length) {
    return seriesMap
  }

  // 1) 事件时间戳升序（同一时刻只算一次）
  const timestamps = Array.from(new Set(subs.map((s) => String(s.created_at)))).sort(
    (a, b) => new Date(a).getTime() - new Date(b).getTime(),
  )

  // 增量状态（等价于每次 filter(created_at <= T)，O(事件)）
  const challengeSolvers = {} // cid → Set(teamId)
  const teamSolved = {} // tid → Set(cid)
  teamList.forEach((t) => { teamSolved[t.id] = new Set() })

  const byTime = new Map()
  for (const s of subs) {
    const key = String(s.created_at)
    if (!byTime.has(key)) byTime.set(key, [])
    byTime.get(key).push(s)
  }

  timestamps.forEach((T) => {
    const batch = byTime.get(T) || []
    for (const s of batch) {
      const tid = s.team_id
      const cid = s.challenge_id
      if (!teamSolved[tid]) teamSolved[tid] = new Set()
      if (teamSolved[tid].has(cid)) continue
      teamSolved[tid].add(cid)
      if (!challengeSolvers[cid]) challengeSolvers[cid] = new Set()
      challengeSolvers[cid].add(tid)
    }

    // Score(c, T)
    const challengeScoreAtT = {}
    challengeList.forEach((c) => {
      const N = challengeSolvers[c.id] ? challengeSolvers[c.id].size : 0
      challengeScoreAtT[c.id] = calcDynamicScore(
        c.original_points,
        N,
        c.min_score_rate,
        c.difficulty,
      )
    })

    const tsMs = new Date(T).getTime()
    if (Number.isNaN(tsMs)) return

    // TotalScore_team,T = Σ Score(c,T) for c in Solved_T
    teamList.forEach((team) => {
      const solved = teamSolved[team.id]
      let totalScoreAtT = 0
      if (solved && solved.size) {
        solved.forEach((cid) => {
          totalScoreAtT += challengeScoreAtT[cid] || 0
        })
      }
      if (!seriesMap[team.id]) seriesMap[team.id] = []
      const hist = seriesMap[team.id]
      // 跳过同刻同分重复
      if (hist.length && hist[hist.length - 1][0] === tsMs && hist[hist.length - 1][1] === totalScoreAtT) {
        return
      }
      hist.push([tsMs, totalScoreAtT])
    })
  })

  return seriesMap
}

/**
 * aa26239 满意版：后端 Snapshot Replay 的 series / timeline_data 原样入图。
 * 严禁 Math.max 防降分；允许分数下降形成垂直断崖。
 * 端点：[[game_start|first, 0], ...points, [now|end, final]]
 */
function mapSeriesPoints(raw, globalStart, finalScore = null, endTs = null) {
  const points = (Array.isArray(raw) ? raw : [])
    .map((p) => {
      if (Array.isArray(p)) {
        const ts = new Date(p[0]).getTime()
        const score = Number(p[1])
        return [ts, Number.isFinite(score) ? score : 0]
      }
      const ts = new Date(p.changed_at || p.time || p[0]).getTime()
      const score = Number(p.score ?? p.points ?? p[1])
      return [ts, Number.isFinite(score) ? score : 0]
    })
    .filter((pair) => !Number.isNaN(pair[0]))
    .sort((a, b) => a[0] - b[0])

  const start = Number.isFinite(globalStart) ? globalStart : (points[0]?.[0] ?? Date.now())
  const series = [[start, 0], ...points]
  const lastScore = Number.isFinite(finalScore)
    ? finalScore
    : (points.length ? points[points.length - 1][1] : 0)
  const tip = Number.isFinite(endTs) ? endTs : Date.now()
  const lastTs = series[series.length - 1]?.[0] ?? start
  if (tip > lastTs) series.push([tip, lastScore])
  return series
}

function buildChartData(replayPayload, rankTeams, forceMock, focusTeamId = null) {
  if (forceMock && !focusTeamId) return buildMockStepChartData(rankTeams)

  const backendSeries = Array.isArray(replayPayload?.series) ? replayPayload.series : []
  const timelineData = replayPayload?.timeline_data || {}
  const teamsMeta = Array.isArray(replayPayload?.teams) ? replayPayload.teams : []
  const gameStartTs = replayPayload?.game_start
    ? new Date(replayPayload.game_start).getTime()
    : NaN
  const gameEndTs = replayPayload?.game_end
    ? new Date(replayPayload.game_end).getTime()
    : NaN
  const endCap = Number.isFinite(gameEndTs)
    ? Math.min(Date.now(), gameEndTs)
    : Date.now()

  let chartTeams = []

  if (backendSeries.length) {
    let globalStart = Number.isFinite(gameStartTs) ? gameStartTs : Infinity
    if (!Number.isFinite(gameStartTs)) {
      for (const s of backendSeries) {
        const raw = s.points || s.data || []
        for (const p of raw) {
          const ts = Array.isArray(p)
            ? new Date(p[0]).getTime()
            : new Date(p.time || p[0]).getTime()
          if (!Number.isNaN(ts) && ts < globalStart) globalStart = ts
        }
      }
    }
    if (!Number.isFinite(globalStart)) globalStart = Date.now() - 3600 * 1000

    let picked = backendSeries
    if (focusTeamId) {
      picked = backendSeries.filter((s) => Number(s.team_id) === Number(focusTeamId))
      if (!picked.length) {
        const meta = teamsMeta.find((t) => Number(t.id) === Number(focusTeamId))
        const raw = timelineData[String(focusTeamId)] || []
        if (meta || raw.length) {
          picked = [{
            team_id: focusTeamId,
            team_name: meta?.name || '本队',
            points: raw,
            final_points: raw.length
              ? Number(Array.isArray(raw[raw.length - 1]) ? raw[raw.length - 1][1] : 0)
              : 0,
          }]
        }
      }
    } else {
      picked = backendSeries.slice(0, 10)
    }

    chartTeams = picked.map((s, si) => {
      const name = s.team_name || s.name || 'team'
      const raw = s.points || s.data || timelineData[String(s.team_id)] || []
      const finalPts = s.final_points != null
        ? Number(s.final_points)
        : (Array.isArray(raw) && raw.length
          ? Number(Array.isArray(raw[raw.length - 1]) ? raw[raw.length - 1][1] : raw[raw.length - 1].points)
          : 0)
      return {
        name,
        // 原样映射：不做 Math.max / 不做累加
        timeSeriesData: mapSeriesPoints(raw, globalStart, finalPts, endCap),
        color: CHART_COLORS[si % CHART_COLORS.length],
      }
    })
  } else if (
    (replayPayload?.submissions || []).length
    && (replayPayload?.challenges || []).length
    && teamsMeta.length
  ) {
    const seriesMap = buildStepTimelineData(
      replayPayload.submissions,
      replayPayload.challenges,
      teamsMeta,
    )
    let ranked = teamsMeta
      .map((t) => {
        const pts = seriesMap[t.id] || []
        return { id: t.id, name: t.name, final: pts.length ? pts[pts.length - 1][1] : 0 }
      })
      .sort((a, b) => b.final - a.final)
    if (focusTeamId) {
      ranked = ranked.filter((t) => Number(t.id) === Number(focusTeamId))
    } else {
      ranked = ranked.slice(0, 10)
    }

    let globalStart = Number.isFinite(gameStartTs) ? gameStartTs : Infinity
    if (!Number.isFinite(gameStartTs)) {
      ranked.forEach((t) => {
        const pts = seriesMap[t.id] || []
        if (pts.length && pts[0][0] < globalStart) globalStart = pts[0][0]
      })
    }
    if (!Number.isFinite(globalStart)) globalStart = Date.now() - 3600 * 1000

    chartTeams = ranked.map((t, si) => ({
      name: t.name,
      timeSeriesData: mapSeriesPoints(seriesMap[t.id] || [], globalStart, t.final, endCap),
      color: CHART_COLORS[si % CHART_COLORS.length],
    }))
  }

  if (!chartTeams.length) {
    const now = Date.now()
    return {
      teams: [{
        name: 'Baseline',
        timeSeriesData: [[now - 3600 * 1000, 0], [now, 0]],
        color: CHART_COLORS[0],
      }],
      isBaseline: true,
    }
  }

  return {
    teams: chartTeams,
    isBaseline: false,
    algorithm: replayPayload?.algorithm || 'ret2shell_snapshot_replay',
  }
}

export default {
  name: 'GameScoreboard',
  components: { NSpin },
  props: { gameId: { type: [String, Number], required: true } },
  setup(props) {
    const axios = inject('axios')
    const items = ref([])
    const orgFilter = ref('')
    const chartScope = ref('top')
    const myTeamId = ref(null)
    const curveRef = ref(null)
    let curveChart = null
    let resizeObserver = null
    const loading = ref(false)
    const loadError = ref(false)
    const PAGE_SIZE = 50
    const visibleCount = ref(PAGE_SIZE)
    /** /timeline 完整 payload：submissions + challenges + teams → 前端重演 */
    const timelinePayload = ref({
      series: [],
      submissions: [],
      challenges: [],
      teams: [],
    })

    function schoolLabel(it) {
      const s = it?.team_school || it?.school || ''
      if (!s || s === '无组织') return ''
      return String(s).replace(/^#/, '')
    }

    const orgOptions = computed(() => {
      const set = new Set()
      for (const it of items.value) {
        const s = schoolLabel(it)
        if (s) set.add(s)
      }
      return [...set].sort().map((s) => ({ label: s, value: s }))
    })

    const filtered = computed(() => {
      if (!orgFilter.value) return items.value
      return items.value.filter((it) => schoolLabel(it) === orgFilter.value)
    })

    const rankList = computed(() =>
      filtered.value.map((it, idx) => ({
        id: it.team_id || idx,
        name: it.team_name || it.username || 'Unknown',
        school: schoolLabel(it),
        solvedCount: Number(it.solved_challenges) || 0,
        score: Number(it.total_points) || 0,
        rank: Number(it.rank) || idx + 1,
      })),
    )

    const visibleRankList = computed(() => rankList.value.slice(0, visibleCount.value))
    const hasMoreRanks = computed(() => visibleCount.value < rankList.value.length)
    function loadMoreRanks() {
      visibleCount.value = Math.min(visibleCount.value + PAGE_SIZE, rankList.value.length)
    }

    const chartData = computed(() => {
      const payload = { ...timelinePayload.value }
      const focusId = chartScope.value === 'mine' ? myTeamId.value : null
      if (orgFilter.value && !focusId) {
        const allowed = new Set(filtered.value.map((t) => t.team_name || t.username))
        const allowedIds = new Set(filtered.value.map((t) => t.team_id).filter(Boolean))
        // 仅过滤「画哪几队」；submissions 保留全场，N(c,T) 必须全局统计
        payload.teams = (payload.teams || []).filter(
          (t) => allowed.has(t.name || t.team_name) || allowedIds.has(t.id),
        )
        payload.series = (payload.series || []).filter(
          (s) => allowed.has(s.team_name || s.name) || allowedIds.has(s.team_id),
        )
      }
      const noRealScore = !rankList.value.length || rankList.value.every((t) => !t.score)
      const hasReplay = (payload.submissions || []).length > 0
        && (payload.challenges || []).length > 0
        && (Array.isArray(timelinePayload.value.teams) ? timelinePayload.value.teams : []).length > 0
      return buildChartData(payload, rankList.value, noRealScore && !hasReplay && !focusId, focusId)
    })

    async function loadMyTeam() {
      myTeamId.value = null
      if (!props.gameId) return
      try {
        const { data } = await axios.get('/api/teams/me', { params: { game_id: props.gameId } })
        const team = data?.team || null
        myTeamId.value = team?.id || null
        if (!myTeamId.value && chartScope.value === 'mine') chartScope.value = 'top'
      } catch {
        myTeamId.value = null
        if (chartScope.value === 'mine') chartScope.value = 'top'
      }
    }

    async function load(opts = {}) {
      if (!props.gameId) return
      const silent = !!opts.silent
      if (!silent) {
        loading.value = true
        loadError.value = false
      }
      try {
        const { data } = await axios.get(`/api/ctf/games/${props.gameId}/scoreboard`)
        items.value = data.data?.rankings || data?.rankings || []
        if (!silent) loadError.value = false
      } catch (e) {
        console.error('Failed to load scoreboard:', e)
        if (!silent) {
          items.value = []
          loadError.value = true
        }
      } finally {
        if (!silent) loading.value = false
      }
    }

    async function loadTimeline() {
      try {
        const { data } = await axios.get(`/api/ctf/games/${props.gameId}/scoreboard/timeline`)
        const payload = data?.data || data || {}
        timelinePayload.value = {
          series: Array.isArray(payload.series) ? payload.series : [],
          timeline_data: payload.timeline_data || {},
          submissions: Array.isArray(payload.submissions) ? payload.submissions : [],
          challenges: Array.isArray(payload.challenges) ? payload.challenges : [],
          teams: Array.isArray(payload.teams) ? payload.teams : [],
          algorithm: payload.algorithm,
          game_start: payload.game_start || null,
          game_end: payload.game_end || null,
        }
      } catch {
        timelinePayload.value = { series: [], submissions: [], challenges: [], teams: [] }
      }
      await renderChart()
    }

    function ensureChart() {
      const el = curveRef.value || document.getElementById('score-trend-chart')
      if (!el) return null
      if (!curveChart) {
        curveChart = echarts.init(el, 'dark')
        if (typeof ResizeObserver !== 'undefined') {
          resizeObserver = new ResizeObserver(rafThrottle(() => {
            try { curveChart?.resize() } catch { /* ignore */ }
          }))
          resizeObserver.observe(el)
        }
        window.addEventListener('resize', onResize)
      }
      return curveChart
    }

    function buildOption(data) {
      const isBaseline = !!data.isBaseline
      // 对齐 ret2shell scoreboard Chart option
      return {
        backgroundColor: 'transparent',
        color: CHART_COLORS,
        animation: false,
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(18, 24, 27, 0.92)',
          borderColor: 'transparent',
          textStyle: { color: '#e5e7eb', fontSize: 12 },
          axisPointer: {
            type: 'line',
            snap: true,
            label: { precision: 0 },
          },
          formatter(params) {
            const list = Array.isArray(params) ? params : [params]
            if (!list.length) return ''
            const axis = list[0].axisValueLabel || list[0].axisValue || ''
            const seen = new Set()
            const lines = [`<div style="margin-bottom:4px">${axis}</div>`]
            for (let i = list.length - 1; i >= 0; i--) {
              const p = list[i]
              const name = p.seriesName || ''
              if (seen.has(name)) continue
              seen.add(name)
              const val = Array.isArray(p.value) ? p.value[1] : p.value
              lines.push(
                `${p.marker || ''}<span style="margin-right:8px">${name}</span>`
                + `<b>${val ?? '-'} pts</b>`,
              )
            }
            return lines.join('<br/>')
          },
        },
        legend: { show: false },
        toolbox: {},
        grid: {
          left: 72,
          right: 24,
          top: 48,
          bottom: 80,
        },
        xAxis: {
          type: 'time',
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: (value) => {
            if (!value || value.max < 100) return 100
            return Math.ceil(value.max + value.max * 0.1)
          },
          axisLabel: {
            fontFamily: 'Reverier Mono, JetBrains Mono, monospace',
          },
        },
        dataZoom: [
          { type: 'inside', filterMode: 'none', start: 0, end: 100 },
          {
            type: 'slider',
            filterMode: 'none',
            show: !isBaseline,
          },
        ],
        series: (data.teams || []).map((team, i) => {
          const color = team.color || CHART_COLORS[i % CHART_COLORS.length]
          return {
            name: team.name,
            type: 'line',
            // aa26239 / ret2shell：阶梯线 → 直角断崖；密衰减远看像斜锯齿
            step: 'end',
            symbol: 'circle',
            symbolSize: isBaseline ? 0 : 5,
            showSymbol: !isBaseline,
            smooth: false,
            connectNulls: false,
            data: team.timeSeriesData || [],
            lineStyle: {
              width: isBaseline ? 1.25 : 2,
              type: isBaseline ? 'dashed' : 'solid',
              color,
              opacity: isBaseline ? 0.55 : 1,
            },
            itemStyle: { color },
          }
        }),
      }
    }

    async function renderChart() {
      await nextTick()
      const chart = ensureChart()
      if (!chart) return
      chart.setOption(buildOption(chartData.value), true)
      await nextTick()
      try { chart.resize() } catch { /* ignore */ }
    }

    const debouncedRenderChart = debounce(() => { renderChart() }, 150)

    const scoreboardPoll = createVisibilityPoll(() => {
      if (loading.value) return
      return load({ silent: true }).then(() => loadTimeline())
    }, POLL_INTERVALS.scoreboard)

    const onResize = rafThrottle(() => {
      try { curveChart?.resize() } catch { /* ignore */ }
    })

    function refresh() {
      load().then(() => loadTimeline())
    }

    onMounted(() => {
      // DOM 就绪后尝试挂载（数据随后由 watch 灌入）
      nextTick(() => renderChart())
      scoreboardPoll.start()
    })

    watch(() => props.gameId, () => {
      orgFilter.value = ''
      chartScope.value = 'top'
      visibleCount.value = PAGE_SIZE
      loadMyTeam().then(() => load().then(() => loadTimeline()))
    }, { immediate: true })

    watch(orgFilter, () => { visibleCount.value = PAGE_SIZE })
    watch(chartScope, () => { debouncedRenderChart() })
    watch([orgFilter, chartData], () => { debouncedRenderChart() })
    watch(loading, async (v) => {
      if (!v && !loadError.value) {
        await nextTick()
        await renderChart()
      }
    })

    onUnmounted(() => {
      scoreboardPoll.stop()
      debouncedRenderChart.cancel()
      onResize.cancel?.()
      window.removeEventListener('resize', onResize)
      try { resizeObserver?.disconnect() } catch { /* ignore */ }
      resizeObserver = null
      try { curveChart?.dispose() } catch { /* ignore */ }
      curveChart = null
    })

    return {
      items,
      loading,
      loadError,
      refresh,
      curveRef,
      orgFilter,
      chartScope,
      myTeamId,
      orgOptions,
      rankList,
      visibleRankList,
      hasMoreRanks,
      loadMoreRanks,
    }
  },
}
</script>

<style scoped>
.game-scoreboard-page {
  height: 100%;
  max-height: 100%;
  overflow-x: hidden;
  overflow-y: auto !important;
  /* 默认密度对齐「浏览器 80% 缩放」观感，100% 即可一眼看完走势+排名 */
  padding: 16px 18px;
  box-sizing: border-box;
  width: 100%;
}

.gsb-empty {
  padding: var(--fib-34, 34px);
  text-align: center;
  color: var(--muted);
}
.gsb-empty.compact {
  padding: var(--fib-21, 21px);
}
.gsb-load-more {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

.gsb-refresh-btn,
.gsb-icon-btn {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text, #e8ecf2);
  border-radius: 8px;
  cursor: pointer;
}
.gsb-refresh-btn {
  margin-top: 12px;
  padding: 8px 16px;
  font-size: 13px;
}
.gsb-icon-btn {
  width: 28px;
  height: 28px;
  font-size: 14px;
  line-height: 1;
}
.gsb-icon-btn:hover,
.gsb-refresh-btn:hover {
  border-color: rgba(var(--primary-rgb, 94, 217, 168), 0.45);
  color: #5ED9A8;
}

.trend-chart-card,
.scoreboard-table-card {
  background: rgba(18, 24, 27, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 14px 16px;
  box-sizing: border-box;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.trend-chart-card:hover,
.scoreboard-table-card:hover {
  border-color: rgba(var(--primary-rgb), 0.42);
  box-shadow: var(--gradient-card-shadow-hover);
}

.trend-chart-card {
  margin-bottom: 14px;
}

.trend-chart-head,
.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.trend-chart-title,
.table-title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #e5e7eb;
}

.trend-chart-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gsb-org-select {
  min-width: 140px;
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid rgba(94, 217, 168, 0.35);
  background: rgba(0, 0, 0, 0.4);
  color: #d1d5db;
  font-size: 11px;
  outline: none;
}
.gsb-org-select:focus {
  border-color: rgba(94, 217, 168, 0.65);
}

.chart-container {
  width: 100%;
  /* ret2shell: aspect-video；略收高度以兼顾排名表 */
  aspect-ratio: 16 / 9;
  height: auto;
  min-height: 240px;
  max-height: 380px;
}

.table-scroll {
  width: 100%;
  overflow-x: auto;
}

.gsb-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 12px;
  color: #d1d5db;
}

.gsb-table thead {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: #9ca3af;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.gsb-table th {
  padding: 8px 12px;
  font-weight: 600;
}

.gsb-table tbody tr {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.15s ease;
}
.gsb-table tbody tr.is-mine {
  background: rgba(16, 185, 129, 0.08);
}
.team-mine-tag {
  display: inline-flex;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #a7f3d0;
  background: rgba(16, 185, 129, 0.14);
  border: 1px solid rgba(16, 185, 129, 0.3);
  vertical-align: middle;
}
.gsb-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.05);
}

.gsb-table td {
  padding: 9px 12px;
  vertical-align: middle;
}

.col-right {
  text-align: right;
}

.col-rank {
  font-weight: 700;
  font-family: var(--font-mono, ui-monospace, monospace);
  white-space: nowrap;
}

.rank-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
}
.rank-1 {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}
.rank-2 {
  background: rgba(203, 213, 225, 0.15);
  color: #cbd5e1;
  border: 1px solid rgba(203, 213, 225, 0.3);
}
.rank-3 {
  background: rgba(180, 83, 9, 0.2);
  color: #d97706;
  border: 1px solid rgba(180, 83, 9, 0.3);
}
.rank-num {
  color: #9ca3af;
  padding-left: 6px;
}

.col-team {
  font-weight: 500;
  color: #f3f4f6;
}
.team-name {
  display: block;
}
.team-school {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  font-weight: 400;
  color: rgba(var(--primary-rgb, 94, 217, 168), 0.9);
}

.col-solved {
  color: #9ca3af;
  font-family: var(--font-mono, ui-monospace, monospace);
  white-space: nowrap;
}

.col-score {
  font-weight: 700;
  font-size: 13px;
  color: #5ED9A8;
  font-family: var(--font-mono, ui-monospace, monospace);
  white-space: nowrap;
}

@media (max-width: 720px) {
  .game-scoreboard-page {
    padding: 12px;
  }
  .trend-chart-card,
  .scoreboard-table-card {
    padding: 12px;
  }
  .trend-chart-head {
    flex-direction: column;
    align-items: stretch;
  }
  .gsb-org-select {
    width: 100%;
  }
  .chart-container {
    aspect-ratio: 16 / 10;
    min-height: 200px;
    max-height: 280px;
  }
}
</style>
