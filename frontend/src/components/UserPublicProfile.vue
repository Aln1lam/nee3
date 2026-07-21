<template>
  <MatrixShell
    prompt=""
    title="用户档案"
    subtitle="USER · PROFILE"
    :page-prompt="pagePrompt"
    :page-title="user?.nickname || '用户档案'"
    page-desc="生涯数据 · 参与赛事 · 个人介绍"
  >
    <template #sidebar>
      <p class="sidebar-prompt">选手主页</p>
      <h2 class="matrix-sidebar-title">USR</h2>
      <p class="sidebar-desc">PUBLIC · PROFILE</p>
      <div class="user-card">
        <n-avatar :size="72" :src="avatarUrl" v-if="avatarUrl">{{ '' }}</n-avatar>
        <n-avatar :size="72" v-else color="var(--primary)">{{ initial }}</n-avatar>
        <h3>{{ user?.nickname || '神秘黑客' }}</h3>
        <p class="user-id">{{ user?.username }}#{{ hexId }}</p>
        <a v-if="user?.email" :href="'mailto:' + user.email" class="user-email">{{ user.email }}</a>
        <n-tag size="small" round>{{ user?.school || '无组织' }}</n-tag>
        <n-tag size="small" :type="user?.email_verified ? 'success' : 'default'" round>
          {{ user?.email_verified ? '已验证' : '基础' }}
        </n-tag>
        <p class="join-date">注册于 {{ formatDate(user?.created_at) }}</p>
      </div>
    </template>

    <section class="profile-section matrix-panel">
      <div class="section-head">
        <div class="matrix-section-head">
          <span class="link-code">STA</span>
          <h3>生涯数据</h3>
        </div>
        <n-select
          v-if="participations.length"
          v-model:value="selectedGame"
          :options="gameFilterOptions"
          size="small"
          placeholder="全部赛事"
          clearable
          style="width: 160px"
        />
      </div>
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-num">{{ stats.participations || 0 }}</div>
          <div class="stat-label">参赛次数</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">{{ stats.solves || 0 }}</div>
          <div class="stat-label">解题</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">{{ stats.teams || 0 }}</div>
          <div class="stat-label">所在队</div>
        </div>
      </div>
      <div class="charts-row">
        <div ref="categoryChartRef" class="chart-box"></div>
        <div ref="timelineChartRef" class="chart-box"></div>
      </div>
    </section>

    <section class="profile-section matrix-panel">
      <div class="matrix-section-head">
        <span class="link-code">EVT</span>
        <h3>参与赛事</h3>
      </div>
      <div v-if="!participations.length" class="empty">生命不息，探索不止…</div>
      <ul v-else class="timeline">
        <li v-for="p in filteredParticipations" :key="p.id">
          作为 <strong>{{ p.team_name || '个人' }}</strong> 成员参与了 <strong>{{ p.game_title }}</strong>          <time>{{ formatDate(p.joined_at) }}</time>
        </li>
      </ul>
    </section>

    <section class="profile-section matrix-panel">
      <div class="matrix-section-head">
        <span class="link-code">BIO</span>
        <h3>个人介绍</h3>
      </div>
      <div class="bio markdown-body" v-html="bioHtml"></div>
    </section>
  </MatrixShell>
</template>

<script>
import { ref, computed, inject, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NAvatar, NTag, NSelect } from 'naive-ui'
import { MatrixShell } from '@/components/shared'
import * as echarts from 'echarts'

export default {
  name: 'UserPublicProfile',
  components: { NAvatar, NTag, NSelect, MatrixShell },
  props: { id: { type: [String, Number], default: null } },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const user = ref(null)
    const stats = ref({})
    const participations = ref([])
    const recentSolves = ref([])
    const selectedGame = ref(null)
    const categoryChartRef = ref(null)
    const timelineChartRef = ref(null)
    let categoryChart = null
    let timelineChart = null

    const userId = computed(() => props.id || route.params.id)
    const pagePrompt = computed(() => `cat /users/${userId.value}`)
    const hexId = computed(() => '0x' + (parseInt(userId.value, 10) || 0).toString(16).padStart(6, '0'))
    const initial = computed(() => (user.value?.nickname || 'U').slice(0, 1).toUpperCase())
    const avatarUrl = computed(() => {
      const av = user.value?.avatar
      if (!av) return null
      if (av.startsWith('data:') || /^https?:\/\//i.test(av)) return av
      return av
    })
    const bioHtml = computed(() => {
      const raw = user.value?.bio || user.value?.signature || '这位神秘的黑客什么也没有留下...'
      try { return parseMarkdownSafe(raw) } catch { return '' }
    })

    const gameFilterOptions = computed(() =>
      participations.value.map(p => ({ label: p.game_title, value: p.game_id }))
    )

    const filteredParticipations = computed(() => {
      if (!selectedGame.value) return participations.value
      return participations.value.filter(p => p.game_id === selectedGame.value)
    })

    function formatDate(d) {
      if (!d) return '-'
      try { return new Date(d).toLocaleDateString('zh-CN') } catch { return d }
    }

    function renderCharts() {
      const catStats = stats.value.category_stats || []
      if (categoryChartRef.value) {
        if (!categoryChart) categoryChart = echarts.init(categoryChartRef.value)
        categoryChart.setOption({
          title: { text: '解题分类', left: 'center', textStyle: { fontSize: 13, color: 'var(--muted)' } },
          tooltip: { trigger: 'item' },
          series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            data: catStats.length
              ? catStats.map(c => ({ name: c.category, value: c.count }))
              : [{ name: '暂无数据', value: 1 }],
            label: { fontSize: 11 },
            color: ['#2DB58A', '#D97706', '#16A34A', '#DC2626', '#722ed1', '#13c2c2'],
          }],
        })
      }

      const solves = recentSolves.value.slice().reverse()
      if (timelineChartRef.value) {
        if (!timelineChart) timelineChart = echarts.init(timelineChartRef.value)
        timelineChart.setOption({
          title: { text: '近期解题', left: 'center', textStyle: { fontSize: 13, color: 'var(--muted)' } },
          tooltip: { trigger: 'axis' },
          grid: { left: 40, right: 16, top: 40, bottom: 30 },
          xAxis: {
            type: 'category',
            data: solves.map(s => {
              const d = s.submitted_at ? new Date(s.submitted_at) : null
              return d ? `${d.getMonth() + 1}/${d.getDate()}` : '-'
            }),
            axisLabel: { fontSize: 10 },
          },
          yAxis: { type: 'value', name: 'pts', minInterval: 1 },
          series: [{
            type: 'line',
            smooth: true,
            data: solves.map(s => s.points || 0),
            areaStyle: { opacity: 0.15 },
            itemStyle: { color: '#2DB58A' },
          }],
        })
      }
    }

    function onResize() {
      categoryChart?.resize()
      timelineChart?.resize()
    }

    async function load() {
      if (!userId.value) return
      try {
        const { data } = await axios.get(`/api/auth/users/${userId.value}`)
        user.value = data?.user || data
        stats.value = data?.stats || {}
        participations.value = data?.participations || []
        recentSolves.value = data?.recent_solves || []
        await nextTick()
        renderCharts()
      } catch {
        user.value = null
      }
    }

    onMounted(() => {
      load()
      window.addEventListener('resize', onResize)
    })
    onUnmounted(() => {
      window.removeEventListener('resize', onResize)
      categoryChart?.dispose()
      timelineChart?.dispose()
    })
    watch(userId, load)

    return {
      user, stats, participations, recentSolves, selectedGame, gameFilterOptions,
      filteredParticipations, hexId, initial, avatarUrl, bioHtml, formatDate,
      categoryChartRef, timelineChartRef, pagePrompt,
    }
  },
}
</script>

<style scoped>
.user-card {
  margin-top: 12px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  text-align: center;
  background: var(--card-bg);
}
.user-card h3 { margin: 12px 0 4px; font-size: 1rem; }
.user-id { font-size: var(--text-xs); color: var(--muted); font-family: monospace; margin: 0 0 8px; }
.user-email { display: block; font-size: var(--text-sm); color: var(--primary); margin-bottom: 8px; }
.join-date { font-size: var(--text-xs); color: var(--muted); margin-top: 12px; }
.profile-section { margin-bottom: 16px; }
.section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-head h3, .profile-section h3 { margin: 0; color: var(--primary); font-size: 1rem; }
.stat-box { text-align: center; background: var(--hover); border-radius: var(--card-radius); }
.stat-num { font-size: 1.5rem; font-weight: 700; color: var(--primary); }
.stat-label { font-size: var(--text-xs); color: var(--muted); margin-top: 4px; }
.chart-box { height: 220px; min-width: 0; }
.empty { color: var(--muted); font-style: italic; }
.timeline { list-style: none; margin: 0; padding: 0; }
.timeline li { padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.timeline time { display: block; font-size: var(--text-xs); color: var(--muted); margin-top: 4px; }
.bio { line-height: 1.7; color: var(--text); }

</style>
