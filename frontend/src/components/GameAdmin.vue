<template>
  <div class="game-admin">
    <main class="game-admin__main">
      <header class="matrix-page-head">
        <p class="matrix-page-prompt">赛事管理 · {{ sectionLabel }}</p>
        <h2 class="matrix-page-title">{{ sectionLabel }}</h2>
        <p class="matrix-page-desc">{{ sectionDesc }}</p>
        <p v-if="game?.title" class="game-title">{{ game.title }}</p>
      </header>

      <nav class="section-tabs">
        <router-link
          v-for="item in navItems"
          :key="item.section"
          :to="item.section === 'dashboard' ? `/games/${gameId}/admin` : `/games/${gameId}/admin/${item.section}`"
          class="section-tab"
          :class="{ active: activeSection === item.section }"
        >
          <span class="link-code">{{ item.code }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <UiLoadingTips v-if="loading && !game" />

      <template v-else>
        <!-- Dashboard -->
        <section v-if="activeSection === 'dashboard'" class="section">
          <div class="stat-grid">
            <div class="stat-card"><span>参赛队伍</span><strong>{{ stats.teams || 0 }}</strong></div>
            <div class="stat-card"><span>题目</span><strong>{{ stats.challenges || 0 }}</strong></div>
            <div class="stat-card"><span>提交</span><strong>{{ stats.submissions || 0 }}</strong></div>
            <div class="stat-card"><span>状态</span><strong>{{ gameStatusLabel }}</strong></div>
          </div>
          <div class="chat-panel">
            <h3>实时 Hammer 消息</h3>
            <div ref="chatListRef" class="chat-list">
              <div v-if="!chatMessages.length" class="muted">暂无消息</div>
              <div v-for="m in chatMessages" :key="m.id" class="chat-item" :class="{ staff: m.is_staff }">
                <span class="chat-meta">{{ m.is_staff ? '官方' : m.nickname }} · {{ m.challenge_title }}</span>
                <p>{{ m.content }}</p>
                <time>{{ formatTime(m.created_at) }}</time>
              </div>
            </div>
          </div>
        </section>

        <!-- Statistics -->
        <section v-else-if="activeSection === 'statistics'" class="section">
          <ScoreboardChart :series="scoreSeries" :show-toolbar="true" height="360px" @refresh="loadScoreSeries" />
        </section>

        <!-- Edit -->
        <section v-else-if="activeSection === 'edit'" class="section">
          <n-form label-placement="top" class="form-narrow matrix-panel">
            <n-form-item label="赛事名称"><n-input v-model:value="editForm.title" /></n-form-item>
            <n-form-item label="简介"><n-input v-model:value="editForm.description" type="textarea" :rows="4" /></n-form-item>
            <n-form-item label="公开"><n-switch v-model:value="editForm.is_public" /></n-form-item>
            <UiButton variant="primary" :loading="saving" @click="saveGame">保存</UiButton>
          </n-form>
        </section>

        <!-- Rules -->
        <section v-else-if="activeSection === 'rules'" class="section matrix-panel">
          <n-input v-model:value="editForm.rules" type="textarea" :rows="14" placeholder="Markdown 规则" />
          <UiButton variant="primary" class="mt-12" :loading="saving" @click="saveGame">保存规则</UiButton>
        </section>

        <!-- Timeline -->
        <section v-else-if="activeSection === 'timeline'" class="section">
          <p class="muted">修改后同步更新 Timer 与 TimeProgress 显示</p>
          <n-form label-placement="top" class="form-narrow matrix-panel">
            <n-form-item label="开始时间"><n-input v-model:value="editForm.start_time" placeholder="ISO 8601" /></n-form-item>
            <n-form-item label="结束时间"><n-input v-model:value="editForm.end_time" placeholder="ISO 8601" /></n-form-item>
            <n-form-item label="状态">
              <n-select v-model:value="editForm.status" :options="statusOptions" />
            </n-form-item>
            <UiButton variant="primary" :loading="saving" @click="saveGame">保存时间</UiButton>
          </n-form>
        </section>

        <!-- Hammers -->
        <section v-else-if="activeSection === 'hammers'" class="section matrix-panel">
          <div class="chat-list full">
            <div v-for="m in chatMessages" :key="'h-' + m.id" class="chat-item">
              <span class="chat-meta">{{ m.challenge_title }} · {{ m.nickname }}</span>
              <p>{{ m.content }}</p>
              <router-link :to="`/games/${gameId}/challenges?challenge=${m.challenge_id}&tab=hammer`">查看题目</router-link>
            </div>
            <div v-if="!chatMessages.length" class="muted">暂无 Hammer 消息</div>
          </div>
        </section>

        <!-- Teams -->
        <section v-else-if="activeSection === 'teams'" class="section matrix-panel">
          <n-data-table :columns="teamColumns" :data="adminTeams" :loading="teamsLoading" size="small" />
        </section>

        <!-- Captures (PCAP) -->
        <section v-else-if="activeSection === 'captures'" class="section matrix-panel">
          <div class="pcap-toolbar">
            <div>
              <p class="muted">容器流量捕获 PCAP 列表 / 下载 / 删除</p>
              <p v-if="captureMeta" class="muted">
                共 {{ captureMeta.total || 0 }} 条
                <span v-if="captureMeta.enable === false"> · 本赛事未开启流量捕获</span>
                <span v-if="captureMeta.storage_dir"> · {{ captureMeta.storage_dir }}</span>
              </p>
            </div>
            <UiButton size="small" :loading="capturesLoading" @click="loadCaptures">刷新</UiButton>
          </div>
          <div v-if="!capturesLoading && !captures.length" class="pcap-empty muted">暂无 PCAP 记录</div>
          <n-data-table v-else :columns="captureColumns" :data="captures" :loading="capturesLoading" size="small" />
        </section>

        <!-- Delete -->
        <section v-else-if="activeSection === 'delete'" class="section danger-section matrix-panel">
          <p class="danger-text">此操作不可恢复，将删除赛事及所有相关数据</p>
          <n-input v-model:value="deleteConfirm" placeholder="输入赛事名称以确认" />
          <UiButton variant="secondary" :disabled="deleteConfirm !== game?.title" :loading="deleting" @click="deleteGame">
            永久删除
          </UiButton>
        </section>

        <!-- Generic placeholder sections -->
        <section v-else class="section matrix-panel">
          <p class="muted">该模块尚未开放（已从导航隐藏占位入口）。请使用下方快捷入口：</p>
          <div class="quick-links">
            <router-link :to="`/games/${gameId}/scoreboard`">积分</router-link>
            <router-link :to="`/games/${gameId}/teams`">队伍</router-link>
            <router-link :to="`/games/${gameId}/challenges`">题目</router-link>
            <router-link :to="`/games/${gameId}/admin/captures`">流量捕获 PCAP</router-link>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, onUnmounted, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NForm, NFormItem, NInput, NSwitch, NSelect, NDataTable, useMessage } from 'naive-ui'
import { UiButton, UiLoadingTips } from '@/components/ui'
import { ScoreboardChart } from '@/components/shared'
import { GAME_ADMIN_LABELS } from '@/router'
import { ctfAdmin } from '@/services/admin'
import { parseJsonResponse } from '@/utils/http'
import { createVisibilityPoll, POLL_INTERVALS } from '@/utils/polling'

const PLACEHOLDER_DESC = {
  policies: '配置报名访问策略、邀请码与分组限制',
  organize: '管理组织架构与学校范围',
  monitor: '实时监控提交与容器状态',
  events: '查看赛事事件与审计日志',
  git: 'Git 仓库集成与题目同步',
  traffic: '流量分析与 Rune 脚本',
  lifecycle: '归档、迁移与赛事生命周期管理',
}

export default {
  name: 'GameAdmin',
  components: { NForm, NFormItem, NInput, NSwitch, NSelect, NDataTable, UiButton, UiLoadingTips, ScoreboardChart },
  props: {
    id: { type: [String, Number], default: null },
    section: { type: String, default: 'dashboard' },
  },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()

    const game = ref(null)
    const loading = ref(true)
    const saving = ref(false)
    const deleting = ref(false)
    const deleteConfirm = ref('')
    const stats = ref({})
    const chatMessages = ref([])
    const scoreSeries = ref([])
    const adminTeams = ref([])
    const teamsLoading = ref(false)
    const captures = ref([])
    const capturesLoading = ref(false)
    const editForm = ref({ title: '', description: '', rules: '', start_time: '', end_time: '', status: 'ongoing', is_public: true })
    const chatPoll = createVisibilityPoll(() => {
      if (['dashboard', 'hammers'].includes(activeSection.value)) loadChat()
    }, POLL_INTERVALS.adminChat)

    const gameId = computed(() => parseInt(props.id || route.params.id, 10))
    const activeSection = computed(() => {
      const p = route.path
      if (p.endsWith('/admin') || p.endsWith('/admin/')) return 'dashboard'
      const m = p.match(/\/admin\/([^/]+)$/)
      return m?.[1] || props.section || 'dashboard'
    })

    const SECTION_CODES = {
      dashboard: 'DSH', statistics: 'STA', edit: 'EDT', rules: 'RUL', policies: 'POL',
      organize: 'ORG', hammers: 'HAM', teams: 'TEA', monitor: 'MON', events: 'EVT',
      git: 'GIT', traffic: 'TRF', lifecycle: 'LFC', captures: 'CAP', timeline: 'TML', delete: 'DEL',
    }

    /** 仅展示已接后端的分区；占位模块不进导航（F11） */
    const IMPLEMENTED_SECTIONS = new Set([
      'statistics', 'edit', 'rules', 'hammers', 'teams', 'captures', 'timeline', 'delete',
    ])
    const navItems = computed(() => [
      { section: 'dashboard', label: '概览', code: 'DSH' },
      ...Object.entries(GAME_ADMIN_LABELS)
        .filter(([section]) => IMPLEMENTED_SECTIONS.has(section))
        .map(([section, label]) => ({
          section,
          label,
          code: SECTION_CODES[section] || section.slice(0, 3).toUpperCase(),
        })),
    ])

    const sectionLabel = computed(() => GAME_ADMIN_LABELS[activeSection.value] || activeSection.value)
    const sectionDesc = computed(() => PLACEHOLDER_DESC[activeSection.value] || '该模块配置界面'

    const gameStatusLabel = computed(() => {
      if (!game.value) return '-'
      const now = Date.now()
      const start = game.value.start_time ? new Date(game.value.start_time).getTime() : 0
      const end = game.value.end_time ? new Date(game.value.end_time).getTime() : Infinity
      if (game.value.status === 'archived') return '已归档'
      if (now < start) return '未开始'
      if (now < end) return '进行中'
      return '已结束'
    })

    const statusOptions = [
      { label: '未开始', value: 'not_started' },
      { label: '进行中', value: 'ongoing' },
      { label: '已结束', value: 'ended' },
      { label: '已归档', value: 'archived' },
    ]

    const teamColumns = [
      { title: 'ID', key: 'id', width: 60 },
      { title: '队名', key: 'name' },
      { title: '成员', key: 'members_count', width: 80 },
      { title: '分数', key: 'total_points', width: 80 },
    ]

    const captureMeta = ref(null)
    const captureColumns = computed(() => [
      { title: 'ID', key: 'id', width: 60 },
      { title: '队伍', key: 'team_name' },
      { title: '题目', key: 'challenge_title' },
      { title: '选手', key: 'user_nickname', width: 100 },
      { title: '大小', key: 'file_size', width: 90, render: r => formatSize(r.file_size) },
      { title: '文件', key: 'file_exists', width: 70, render: r => h('span', r.file_exists ? '有' : '缺') },
      { title: '时间', key: 'created_at', width: 160, render: r => formatTime(r.created_at) },
      {
        title: '操作',
        key: 'actions',
        width: 160,
        render: (r) => h('div', { class: 'pcap-actions' }, [
          h(UiButton, {
            size: 'tiny',
            disabled: !r.file_exists,
            onClick: () => downloadCapture(r),
          }, { default: () => '下载' }),
          h(UiButton, {
            size: 'tiny',
            variant: 'danger',
            onClick: () => deleteCapture(r),
          }, { default: () => '删除' }),
        ]),
      },
    ])

    function formatTime(t) {
      if (!t) return '-'
      try { return new Date(t).toLocaleString('zh-CN', { hour12: false }) } catch { return t }
    }

    async function loadGame() {
      loading.value = true
      try {
        const { data } = await axios.get(`/api/competitions/${gameId.value}`)
        game.value = data?.data || data
        editForm.value = {
          title: game.value?.title || '',
          description: game.value?.description || '',
          rules: game.value?.rules || game.value?.description || '',
          start_time: game.value?.start_time || '',
          end_time: game.value?.end_time || '',
          status: game.value?.status || 'ongoing',
          is_public: game.value?.is_public !== false,
        }
      } catch {
        game.value = null
      } finally {
        loading.value = false
      }
    }

    async function loadStats() {
      try {
        const [sb, ch] = await Promise.all([
          axios.get(`/api/ctf/games/${gameId.value}/scoreboard`),
          axios.get(`/api/challenges/games/${gameId.value}/challenges`),
        ])
        stats.value = {
          teams: sb.data?.data?.total || sb.data?.data?.rankings?.length || 0,
          challenges: (ch.data?.data || []).length,
          submissions: 0,
        }
      } catch { stats.value = {} }
    }

    async function loadChat() {
      try {
        const { data: chRes } = await axios.get(`/api/challenges/games/${gameId.value}/challenges`)
        const challenges = chRes.data?.data || []
        const msgs = []
        for (const ch of challenges.slice(0, 20)) {
          try {
            const { data } = await axios.get(`/api/challenges/${ch.id}/hammer`)
            for (const m of (data?.data || []).slice(-3)) {
              msgs.push({ ...m, challenge_title: ch.title, challenge_id: ch.id })
            }
          } catch { /* ignore */ }
        }
        msgs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        chatMessages.value = msgs.slice(0, 50)
      } catch {
        chatMessages.value = []
      }
    }

    async function loadScoreSeries() {
      try {
        const { data } = await axios.get(`/api/ctf/games/${gameId.value}/scoreboard/timeline`)
        scoreSeries.value = (data?.data?.series || []).map(s => ({
          name: s.team_name,
          data: (s.data || []).map(p => [p.time, p.points]),
        }))
      } catch { scoreSeries.value = [] }
    }

    async function loadTeams() {
      teamsLoading.value = true
      try {
        const { data: sb } = await axios.get(`/api/ctf/games/${gameId.value}/scoreboard`)
        adminTeams.value = (sb.data?.data?.rankings || []).map(r => ({
          id: r.team_id,
          name: r.team_name,
          members_count: r.members_count,
          total_points: r.total_points,
        }))
      } catch { adminTeams.value = [] }
      finally { teamsLoading.value = false }
    }

    function formatSize(n) {
      const b = Number(n) || 0
      if (b < 1024) return b + ' B'
      if (b < 1048576) return (b / 1024).toFixed(1) + ' KB'
      return (b / 1048576).toFixed(1) + ' MB'
    }

    async function loadCaptures() {
      capturesLoading.value = true
      try {
        const res = await ctfAdmin.listTrafficCaptures(gameId.value, true)
        const { data: body, ok } = await parseJsonResponse(res)
        if (!ok) {
          captures.value = []
          captureMeta.value = null
          message.error(body?.msg || '加载流量包失败')
          return
        }
        const payload = body?.data || {}
        captures.value = payload.items || []
        captureMeta.value = {
          total: payload.total,
          storage_dir: payload.storage_dir,
          enable: payload.game?.enable_traffic_capture,
        }
      } catch (e) {
        captures.value = []
        captureMeta.value = null
        message.error(e.message || '加载流量包失败')
      } finally {
        capturesLoading.value = false
      }
    }

    async function downloadCapture(row) {
      if (!row?.id) return
      try {
        const res = await ctfAdmin.downloadTrafficCapture(row.id)
        if (!res.ok) {
          const { data } = await parseJsonResponse(res)
          message.error(data?.msg || '下载失败')
          return
        }
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = (row.file_path || `capture_${row.id}.pcap`).split('/').pop()
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      } catch (e) {
        message.error(e.message || '下载失败')
      }
    }

    async function deleteCapture(row) {
      if (!row?.id) return
      if (!window.confirm(`确认删除 PCAP #${row.id}？`)) return
      try {
        const res = await ctfAdmin.deleteTrafficCapture(row.id)
        const { data: body, ok } = await parseJsonResponse(res)
        if (!ok) {
          message.error(body?.msg || '删除失败')
          return
        }
        message.success(body?.msg || '已删除')
        await loadCaptures()
      } catch (e) {
        message.error(e.message || '删除失败')
      }
    }

    async function saveGame() {
      saving.value = true
      try {
        await axios.put(`/api/competitions/admin/${gameId.value}/update`, editForm.value)
        message.success('已保存')
        await loadGame()
      } catch (e) {
        message.error(e.response?.data?.msg || '保存失败')
      } finally {
        saving.value = false
      }
    }

    async function deleteGame() {
      deleting.value = true
      try {
        await axios.delete(`/api/competitions/admin/${gameId.value}/delete`)
        message.success('赛事已删除')
        router.push('/games')
      } catch (e) {
        message.error(e.response?.data?.msg || '删除失败')
      } finally {
        deleting.value = false
      }
    }

    function loadSectionData() {
      const s = activeSection.value
      if (s === 'dashboard') { loadStats(); loadChat() }
      if (s === 'statistics') loadScoreSeries()
      if (s === 'hammers') loadChat()
      if (s === 'teams') loadTeams()
      if (s === 'captures') loadCaptures()
    }

    watch(activeSection, loadSectionData)
    watch(gameId, () => { loadGame(); loadSectionData() })

    onMounted(async () => {
      await loadGame()
      loadSectionData()
      chatPoll.start()
    })

    onUnmounted(() => chatPoll.stop())

    return {
      game, gameId, loading, saving, deleting, deleteConfirm, stats, chatMessages,
      scoreSeries, adminTeams, teamsLoading, captures, capturesLoading, captureMeta, captureColumns,
      editForm, activeSection, navItems, sectionLabel, sectionDesc,
      gameStatusLabel, statusOptions, teamColumns,
      formatTime, saveGame, deleteGame, loadScoreSeries, loadCaptures,
    }
  },
}
</script>

<style scoped>
.game-admin {
  margin: 0;
  min-height: calc(100vh - var(--nav-height, 56px));
}
.game-admin__main {
  flex: 1;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 24px 28px;
  overflow: auto;
}
.game-title {
  font-size: var(--text-xs);
  color: var(--muted);
  margin: 8px 0 0;
  line-height: 1.4;
}
.section-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 20px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.section-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid transparent;
  border-radius: var(--card-radius);
  color: var(--muted);
  text-decoration: none;
  font-size: var(--text-sm);
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.section-tab:hover,
.section-tab.active {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}
.section-tab:hover .link-code,
.section-tab.active .link-code { color: var(--primary); }
.section { max-width: none; width: 100%; }
.stat-card {
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-card span { font-size: var(--text-xs); color: var(--muted); }
.stat-card strong { font-size: 1.5rem; color: var(--primary); }
.chat-panel { border: 1px solid var(--border); border-radius: var(--card-radius); padding: 16px; background: var(--card-bg); }
.chat-panel h3 { margin: 0 0 12px; font-size: 14px; }
.chat-list { max-height: 320px; overflow-y: auto; }
.chat-list.full { max-height: 480px; }
.chat-item { padding: 10px 0; border-bottom: 1px solid var(--border); font-size: var(--text-sm); }
.chat-item.staff { border-left: 3px solid var(--primary); padding-left: 8px; }
.chat-meta { font-size: 11px; color: var(--muted); }
.chat-item p { margin: 4px 0; }
.chat-item time { font-size: 11px; color: var(--muted); }
.form-narrow { max-width: 520px; }
.mt-12 { margin-top: 12px; }
.muted { color: var(--muted); font-size: 14px; }
.danger-section .danger-text { color: var(--accent-red, #f83030); margin-bottom: 16px; }
.quick-links { display: flex; gap: 16px; margin-top: 16px; }
.quick-links a { color: var(--primary); }

.pcap-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.pcap-actions { display: flex; gap: 6px; }
.pcap-empty { padding: 28px 0; text-align: center; }
</style>
