<template>
  <MatrixShell
    class="challenge-workspace-matrix"
    sidebar-width="280px"
    :show-sidebar="true"
    :bleed="false"
    :collapsible="!embedded"
    :storage-key="embedded ? 'neepu_training_ws_sidebar' : 'neepu_challenge_sidebar_collapsed'"
    content-class="challenge-workspace-page"
    :page-prompt="shellPagePrompt"
    :page-title="shellPageTitle"
    :page-desc="shellPageDesc"
  >
    <template #sidebar>
      <aside class="tree-panel tree-panel--matrix">
      <div class="tree-panel-head">
        <div class="tree-title-row">
          <h2 class="tree-panel-title">{{ displayGameTitle }}</h2>
          <span v-if="mode === 'training'" class="status-chip status-chip--open">永久开放</span>
          <n-tag v-else-if="gameStatus" size="small" :type="gameStatusType" round>{{ gameStatus }}</n-tag>
        </div>
      </div>

      <div class="tree-body">
        <UiLoadingTips v-if="challengesLoading && !challenges.length" />
        <div v-else-if="!challengeTree.length" class="tree-empty">
          <template v-if="challengesLoadError">加载失败，请重新进入页面重试</template>
          <template v-else>{{ mode === 'competition' ? '暂无任务' : '暂无题目' }}</template>
        </div>
        <div v-for="group in challengeTree" :key="group.category" class="tree-group">
          <button type="button" class="tree-cat" @click="toggleCategory(group.category)">
            <span class="tree-cat-icon">{{ isCategoryExpanded(group.category) ? '▼' : '▶' }}</span>
            <span class="tree-cat-name">{{ group.category }}</span>
          </button>
          <ul v-show="isCategoryExpanded(group.category)" class="tree-items">
            <li
              v-for="ch in group.items"
              :key="ch.id"
              class="tree-item"
              :class="{
                active: selectedChallenge?.id === ch.id,
                solved: isSolved(ch.id),
                disabled: adminActive && ch.is_enabled === false,
              }"
              @click="selectChallenge(ch)"
            >
              <span class="tree-item-title">{{ ch.title }}</span>
              <span v-if="isSolved(ch.id)" class="tree-item-mark" title="已解出">✓</span>
              <UiPopover v-if="adminActive" trigger="click">
                <template #trigger>
                  <button class="tree-item-menu" type="button" @click.stop aria-label="题目上下架">⋯</button>
                </template>
                <div class="admin-popover">
                  <p class="admin-popover__hint">{{ ch.is_enabled === false ? '已下架' : '已上架' }}</p>
                  <UiButton
                    size="small"
                    :variant="ch.is_enabled === false ? 'primary' : 'secondary'"
                    :loading="!!ch._toggling"
                    @click="toggleChallengeEnabled(ch)"
                  >{{ ch.is_enabled === false ? '上架' : '下架' }}</UiButton>
                </div>
              </UiPopover>
            </li>
          </ul>
        </div>
      </div>

      <div v-if="$slots['tree-footer']" class="tree-footer">
        <slot name="tree-footer" />
      </div>
    </aside>
    </template>

    <!-- embedded（训练内嵌）时 footer 由外层 Training 统一提供，禁止双套堆叠 -->
    <template v-if="!embedded" #sidebar-footer>
      <template v-if="mode === 'training'">
        <router-link to="/training" class="sidebar-link">
          <span class="link-code">BAK</span>
          <span>训练中心</span>
        </router-link>
        <div class="sidebar-footer-copy" style="margin-top: 10px;">
          © 2022-2026
          <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">东北电力大学</a>
        </div>
      </template>
      <template v-else>
        <router-link :to="`/games/${gameId}`" class="sidebar-link">
          <span class="link-code">GME</span>
          <span>赛事详情</span>
        </router-link>
        <router-link to="/games" class="sidebar-link">
          <span class="link-code">CTF</span>
          <span>赛事列表</span>
        </router-link>
        <router-link :to="`/games/${gameId}/scoreboard`" class="sidebar-link">
          <span class="link-code">SB</span>
          <span>排行榜</span>
        </router-link>
        <router-link
          :to="selectedChallenge
            ? { path: '/submissions', query: { challenge: String(selectedChallenge.id), game: String(gameId) } }
            : '/submissions'"
          class="sidebar-link"
        >
          <span class="link-code">SUB</span>
          <span>我的提交</span>
        </router-link>
      </template>
    </template>

    <div
      class="challenge-workspace workspace-dock"
      :class="[`mode-${mode}`, { 'admin-tools-on': adminActive }]"
    >
    <section class="workspace-stage">
      <div v-if="isAdmin && mode !== 'training'" class="stage-admin-bar">
        <n-tag v-if="adminActive" size="small" type="warning" round>管理视图</n-tag>
        <n-button size="tiny" :type="showAdminTools ? 'warning' : 'default'" @click="toggleAdminTools">
          {{ showAdminTools ? '选手视图' : '管理视图' }}
        </n-button>
      </div>

      <template v-if="selectedChallenge">
        <div class="stage-content">
          <div class="stage-brief">
            <div class="brief-main">
              <div class="brief-header">
                <div class="brief-title-row">
                  <h3>{{ selectedChallenge.title }}</h3>
                  <span class="brief-solves">{{ solveCount }} solves</span>
                  <span
                    class="cat-chip"
                    :style="categoryChipStyle(selectedChallenge.category)"
                  >{{ selectedChallenge.category }}</span>
                </div>
                <div class="points-board" aria-label="题目分值">
                  <span class="points-board__num">{{ challengePoints }}</span>
                  <span class="points-board__unit">PTS</span>
                </div>
              </div>
              <div v-if="selectedChallenge.tags?.length" class="tag-row">
                <n-tag v-for="t in selectedChallenge.tags" :key="t" size="small">{{ t }}</n-tag>
              </div>
              <Article :content="descriptionContent" class="brief-desc" />

              <!-- 附件题：仅下载附件（challenge_type 0/2） -->
              <div v-if="showAttachmentBar" class="challenge-actions-bar">
                <a
                  v-if="attachmentUrl"
                  class="action-btn action-btn--mint action-btn--lg"
                  :href="attachmentUrl"
                  target="_blank"
                  rel="noopener"
                >
                  <span class="link-code chip-cut">DL</span>
                  <span>下载附件</span>
                </a>
                <button
                  v-else
                  type="button"
                  class="action-btn action-btn--ghost action-btn--lg"
                  disabled
                >
                  <span class="link-code chip-cut">DL</span>
                  <span>暂无附件</span>
                </button>
              </div>

              <!-- 容器题：行内轻量化环境条 -->
              <div v-if="isContainerChallenge" class="inline-env-bar">
                <template v-if="!instance">
                  <span class="inline-env-hint">▶ 题目可开启在线环境</span>
                  <button
                    type="button"
                    class="inline-env-start"
                    :disabled="containerBusy"
                    @click="startContainer"
                  >▶ {{ containerLoading ? '启动中…' : '启动！' }}</button>
                </template>
                <template v-else>
                  <span class="inline-env-hint is-live">
                    <i class="inline-env-dot" aria-hidden="true"></i>
                    环境运行中
                    <code
                      v-if="endpointDisplay"
                      class="inline-env-endpoint"
                      :title="instance.connection_url"
                      @click="openEnvironment"
                    >{{ endpointDisplay }}</code>
                  </span>
                  <div class="inline-env-actions">
                    <button
                      type="button"
                      class="inline-env-link"
                      :disabled="!instance.connection_url"
                      @click="openEnvironment"
                    >打开</button>
                    <button
                      type="button"
                      class="inline-env-link"
                      :disabled="!instance.connection_url"
                      @click="copyConn"
                    >复制</button>
                    <button
                      type="button"
                      class="inline-env-link"
                      :disabled="containerBusy"
                      @click="extendContainer"
                    >{{ extending ? '延时中' : '延时' }}</button>
                    <button
                      type="button"
                      class="inline-env-link is-danger"
                      :disabled="containerBusy"
                      @click="destroyContainer"
                    >{{ destroying ? '销毁中' : '销毁' }}</button>
                    <span v-if="remainingLabel" class="inline-env-ttl">{{ remainingLabel }}</span>
                  </div>
                </template>
                <p v-if="queueStatus" class="inline-env-queue">{{ queueStatus }}</p>
              </div>

              <!-- 标准 Flag 提交面板（禁止终端交 Flag） -->
              <div class="flag-submit-panel flag-submit-panel--dock">
                <div class="flag-submit-head">
                  <span class="link-code chip-cut">FLG</span>
                  <span>提交 Flag</span>
                  <span v-if="challengeSolved" class="flag-solved-badge">已解出</span>
                </div>
                <div class="flag-submit-row">
                  <input
                    v-model="flagInput"
                    class="flag-submit-input"
                    type="text"
                    placeholder="请输入 flag{...}"
                    :disabled="challengeSolved || submitting"
                    @keydown.enter.prevent="submitFlag"
                  />
                  <button
                    type="button"
                    class="flag-submit-btn"
                    :disabled="challengeSolved || submitting || !flagInput.trim()"
                    @click="submitFlag"
                  >{{ challengeSolved ? '已解锁' : (submitting ? '提交中…' : '提交 Flag') }}</button>
                </div>
                <p v-if="flagResult" class="flag-submit-result" :class="flagResult.ok ? 'is-ok' : 'is-err'">
                  {{ flagResult.msg }}
                </p>
              </div>
            </div>
          </div>

        </div>
      </template>

      <div v-else class="stage-empty stage-empty--canvas" aria-hidden="true"></div>
    </section>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, computed, watch, inject, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NTag, NButton, useMessage } from 'naive-ui'
import { UiLoadingTips, UiPopover, UiButton } from '@/components/ui'
import { Article, MatrixShell } from '@/components/shared'
import { ctfAdmin } from '@/services/admin'
import { parseJsonResponse } from '@/utils/http'
import { unwrapList } from '../utils/unwrap'
import { fetchSession, isLoggedIn, isAdmin as checkIsAdmin } from '../services/auth'
import { getCategoryStyle } from '../utils/categoryStyle'
import {
  getContainerStatus as apiGetContainerStatus,
  startContainer as apiStartContainer,
  stopContainer as apiStopContainer,
  extendContainer as apiExtendContainer,
  getContainerJob,
  getInstanceLogs,
} from '../services/container'
import { getHints as apiGetHints, accessHint as apiAccessHint } from '../services/challenges'
import { apiErrorMessage } from '@/utils/apiError'
import { createVisibilityPoll, POLL_INTERVALS } from '@/utils/polling'

function categoryStyle(cat) {
  return getCategoryStyle(cat)
}

function categoryChipStyle(cat) {
  const s = getCategoryStyle(cat)
  return { background: s.chipBg, color: s.chipText }
}

export default {
  name: 'ChallengeWorkspace',
  components: { NTag, NButton, UiLoadingTips, UiPopover, UiButton, Article, MatrixShell },
  props: {
    gameId: { type: [Number, String], required: true },
    mode: { type: String, default: 'competition' },
    gameTitle: { type: String, default: '' },
    gameStatus: { type: String, default: '' },
    gameArchived: { type: Boolean, default: false },
    hideGameHeader: { type: Boolean, default: false },
    embedded: { type: Boolean, default: false },
  },
  emits: ['challenge-change', 'hammer-unread'],
  setup(props, { emit }) {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()
    const resolvedGameTitle = ref(props.gameTitle || '')
    const displayGameTitle = computed(() => resolvedGameTitle.value || props.gameTitle || (props.mode === 'training' ? '练习场' : '赛事题目'))

    async function ensureTrainingAccess() {
      if (props.mode !== 'training' || !props.gameId) return
      try {
        await axios.post(`/api/competitions/${props.gameId}/training-join`)
      } catch (e) {
        const status = e?.response?.status
        if (status === 401) {
          message.warning('请先登录后再进入练习场')
          router.push({ name: 'Auth', query: { redirect: route.fullPath } })
        }
      }
    }

    async function loadGameMeta() {
      if (!props.gameId) return
      try {
        const { data } = await axios.get(`/api/competitions/${props.gameId}`)
        const meta = data?.data || data
        if (meta?.title) resolvedGameTitle.value = meta.title
      } catch { /* ignore */ }
    }


    let requestAbort = null
    function beginRequestScope() {
      requestAbort?.abort()
      requestAbort = new AbortController()
      return requestAbort.signal
    }
    function bgConfig(signal) {
      const cfg = { _skipAuthClear: true }
      if (signal) cfg.signal = signal
      return cfg
    }

    const challenges = ref([])
    const challengesLoading = ref(false)
    const challengesLoadError = ref(false)
    const selectedChallenge = ref(null)
    const solvedIds = ref(new Set())
    const bloodMap = ref({})
    const searchQuery = ref('')
    const collapsedCategories = ref(new Set())
    const activeTab = ref('terminal')
    const flagInput = ref('')
    const submitting = ref(false)
    const challengeSolved = ref(false)
    const flagResult = ref(null)
    const hintItems = ref([])
    const auxHintsOpen = ref(false)
    const auxWriteupOpen = ref(false)
    const hintsLoading = ref(false)
    const stats = ref(null)
    const instance = ref(null)
    const containerLoading = ref(false)
    const queueStatus = ref('')
    const instanceLogs = ref('')
    const logsLoading = ref(false)
    const challengeOpenedAt = ref({})
    const extending = ref(false)
    const destroying = ref(false)
    const remainingSeconds = ref(0)
    let remainingTimer = null
    const isAdmin = ref(false)
    const showAdminTools = ref(false)

    const adminActive = computed(() => isAdmin.value && showAdminTools.value)

    const ADMIN_ONLY_TABS = new Set(['stats', 'attachments', 'instances', 'checker', 'settings', 'manage'])
    const LEGACY_ADMIN_TAB_MAP = {
      stats: 'manage',
      attachments: 'manage',
      instances: 'manage',
      checker: 'manage',
      settings: 'manage',
    }

    const gameStatusType = computed(() => {
      if (props.gameStatus === '进行中') return 'success'
      if (props.gameStatus === '报名中') return 'warning'
      return 'default'
    })

    const challengeTypeLabel = computed(() => {
      const map = {
        0: '静态附件',
        1: '静态容器',
        2: '动态附件',
        3: '动态容器',
      }
      return map[challengeTypeNum.value] ?? '静态题'
    })

    const filteredChallenges = computed(() => {
      let list = challenges.value
      const q = searchQuery.value.trim().toLowerCase()
      if (q) {
        list = list.filter(c =>
          (c.title || '').toLowerCase().includes(q) ||
          (c.category || '').toLowerCase().includes(q) ||
          (c.tags || []).some(t => String(t).toLowerCase().includes(q)),
        )
      }
      return list
    })

    const challengeTree = computed(() => {
      const map = new Map()
      for (const ch of filteredChallenges.value) {
        const cat = ch.category || '未分类'
        if (!map.has(cat)) map.set(cat, [])
        map.get(cat).push(ch)
      }
      return [...map.entries()].map(([category, items]) => ({ category, items }))
    })

    function readSolves(obj) {
      if (!obj || typeof obj !== 'object') return null
      const n = obj.solves ?? obj.solved_count ?? obj.solves_count ?? obj.unique_solvers
      if (n === undefined || n === null || n === '') return null
      const v = Number(n)
      return Number.isFinite(v) ? v : null
    }

    const challengePoints = computed(() => {
      const ch = selectedChallenge.value || {}
      const n = ch.current_score ?? ch.original_points ?? ch.points ?? ch.score ?? 0
      const num = Number(n)
      return Number.isFinite(num) ? num : 0
    })

    const solveCount = computed(() => {
      const fromChallenge = readSolves(selectedChallenge.value)
      if (fromChallenge != null) return fromChallenge
      const fromStats = readSolves(stats.value)
      if (fromStats != null) return fromStats
      return 0
    })

    const currentBloodRecords = computed(() => {
      const id = selectedChallenge.value?.id
      return id ? (bloodMap.value[id] || []) : []
    })

    const descriptionContent = computed(() =>
      selectedChallenge.value?.description || selectedChallenge.value?.content || '暂无描述',
    )

    const writeupContent = computed(() => selectedChallenge.value?.writeup || '')

    /** 管理端题目类型：0 静态附件 / 1 静态容器 / 2 动态附件 / 3 动态容器 */
    const challengeTypeNum = computed(() => {
      const t = selectedChallenge.value?.challenge_type
      const n = Number(t)
      return Number.isFinite(n) ? n : 0
    })

    const isContainerChallenge = computed(() => {
      const ch = selectedChallenge.value
      if (!ch) return false
      const ctype = challengeTypeNum.value
      // 严格按管理端类型：1=静态容器 3=动态容器
      if (ctype === 1 || ctype === 3) return true
      // 兼容：明确声明支持容器且带镜像
      if ((ch.supports_container === true || ch.needs_container === true) && ch.docker_image) return true
      if (ch.docker_image && ctype !== 0 && ctype !== 2) return true
      return false
    })

    const isAttachmentChallenge = computed(() => {
      const ctype = challengeTypeNum.value
      return ctype === 0 || ctype === 2
    })

    /** 附件条：附件类题目，或容器题额外挂了附件时也显示下载 */
    const showAttachmentBar = computed(() => {
      if (attachmentUrl.value) return true
      return isAttachmentChallenge.value
    })

    // 兼容旧引用
    const supportsContainer = isContainerChallenge
    const hasContainer = isContainerChallenge

    const isTcpConn = computed(() => {
      const url = String(instance.value?.connection_url || '')
      if (!url) return false
      if (/^https?:\/\//i.test(url)) return false
      return /\bnc\b/i.test(url) || /:\d+$/.test(url) || Boolean(instance.value?.port)
    })

    /** 启动后主展示：优先 host:port */
    const endpointDisplay = computed(() => {
      const url = String(instance.value?.connection_url || '').trim()
      if (!url) return ''
      try {
        if (/^https?:\/\//i.test(url)) {
          const u = new URL(url)
          return u.port ? `${u.hostname}:${u.port}` : u.host
        }
      } catch { /* ignore */ }
      const nc = url.match(/^(?:nc\s+)?([\w.-]+)\s+(\d+)$/i)
      if (nc) return `${nc[1]}:${nc[2]}`
      const hp = url.match(/^([\w.-]+):(\d+)(?:\/.*)?$/)
      if (hp) return `${hp[1]}:${hp[2]}`
      if (instance.value?.port) {
        const host = url.replace(/^https?:\/\//i, '').split(/[/:\s]/)[0]
        return host ? `${host}:${instance.value.port}` : String(instance.value.port)
      }
      return url
    })

    const instanceId = computed(() =>
      instance.value?.instance_id ?? instance.value?.id ?? null,
    )

    const attachmentUrl = computed(() => {
      const id = selectedChallenge.value?.attachment_id
      return id ? ctfAdmin.resourceContentUrl(id) : null
    })

    const containerBusy = computed(() =>
      containerLoading.value || extending.value || destroying.value,
    )

    const remainingLabel = computed(() => {
      const s = remainingSeconds.value
      if (!instance.value || s <= 0) return ''
      const h = Math.floor(s / 3600)
      const m = Math.floor((s % 3600) / 60)
      const sec = s % 60
      if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
      return `${m}:${String(sec).padStart(2, '0')}`
    })

    function isCategoryExpanded(category) {
      return !collapsedCategories.value.has(category)
    }

    function toggleCategory(category) {
      const next = new Set(collapsedCategories.value)
      if (next.has(category)) next.delete(category)
      else next.add(category)
      collapsedCategories.value = next
    }

    function closeChallenge() {
      selectedChallenge.value = null
      const q = { ...route.query }
      delete q.challenge
      delete q.tab
      router.replace({ query: q }).catch(() => {})
    }

    function isSolved(id) { return solvedIds.value.has(id) }
    function bloodRecords(id) { return bloodMap.value[id] || [] }
    function bloodLevelName(level) {
      return ['一血', '二血', '三血'][level] || '首解'
    }
    function bloodLevelShort(level) {
      return ['🩸', '2', '3'][level] || '·'
    }

    async function loadChallenges() {
      if (!props.gameId) return
      challengesLoading.value = true
      challengesLoadError.value = false
      try {
        if (adminActive.value) {
          const res = await ctfAdmin.listAdminChallenges(props.gameId)
          const { ok, data } = await parseJsonResponse(res)
          challenges.value = ok ? unwrapList(data) : []
          if (!ok) challengesLoadError.value = true
        } else {
          const res = await axios.get(`/api/challenges/games/${props.gameId}/challenges`)
          challenges.value = unwrapList(res.data)
        }
        await loadSolvedStatus()
        if (props.mode !== 'training') await checkHammerUnread()
      } catch (e) {
        message.error(apiErrorMessage(e, '加载题目失败'))
        challenges.value = []
        challengesLoadError.value = true
      } finally {
        challengesLoading.value = false
      }
    }

    function sanitizeChallengeDetail(ch, detail) {
      if (!detail) return { ...ch }
      if (adminActive.value) return { ...ch, ...detail }
      const { flag_template, flag, expected_flag, ...safe } = detail
      return { ...ch, ...safe }
    }

    function toggleAdminTools() {
      setAdminTools(!showAdminTools.value)
    }

    function setAdminTools(on) {
      showAdminTools.value = on
      const q = { ...route.query }
      if (on) q.admin = '1'
      else delete q.admin
      if (!on && ADMIN_ONLY_TABS.has(activeTab.value)) {
        activeTab.value = 'terminal'
        q.tab = 'terminal'
      } else if (on && route.query.tab && LEGACY_ADMIN_TAB_MAP[route.query.tab]) {
        activeTab.value = LEGACY_ADMIN_TAB_MAP[route.query.tab]
        q.tab = 'manage'
      }
      router.replace({ query: q }).catch(() => {})
      loadChallenges().then(syncFromRoute)
    }

    function applyAdminQueryFromRoute() {
      if (route.query.admin === '1' && isAdmin.value) {
        showAdminTools.value = true
      }
    }

    async function toggleChallengeEnabled(ch) {
      if (!ch?.id || !adminActive.value) return
      ch._toggling = true
      const nextEnabled = ch.is_enabled === false
      try {
        const res = await ctfAdmin.updateChallenge(props.gameId, ch.id, { is_enabled: nextEnabled })
        const { ok, data } = await parseJsonResponse(res)
        if (!ok) throw new Error(data?.msg || data?.message || '操作失败')
        ch.is_enabled = nextEnabled
        message.success(nextEnabled ? '题目已上架' : '题目已下架')
      } catch (e) {
        message.error(e.message || '操作失败')
      } finally {
        ch._toggling = false
      }
    }

    function goAdminChallenge() {
      router.push({ path: '/admin/ctf', query: { game_id: String(props.gameId), tab: 'challenges' } })
    }

    async function checkHammerUnread() {
      if (!isLoggedIn() || !challenges.value.length) return
      const storageKey = `neepu_hammer_seen_${props.gameId}`
      const lastSeen = parseInt(localStorage.getItem(storageKey) || '0', 10)
      let latest = null

      for (const ch of challenges.value.slice(0, 40)) {
        try {
          const res = await axios.get(
            `/api/challenges/${ch.id}/hammer`,
            bgConfig(requestAbort?.signal),
          )
          const rows = res.data?.data || []
          for (const m of rows) {
            if (!m.is_staff) continue
            const ts = new Date(m.created_at).getTime()
            if (ts > lastSeen && (!latest || ts > latest.ts)) {
              latest = { ts, challengeId: ch.id, challengeTitle: ch.title }
            }
          }
        } catch { /* ignore */ }
      }

      if (latest) {
        emit('hammer-unread', {
          challengeId: latest.challengeId,
          challengeTitle: latest.challengeTitle,
          ts: latest.ts,
        })
      }
    }

    function formatStatTime(t) {
      if (!t) return '—'
      try {
        return new Date(t).toLocaleString('zh-CN', {
          month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
        })
      } catch { return t }
    }

    async function loadSolvedStatus() {
      solvedIds.value = new Set()
      bloodMap.value = {}
      if (!isLoggedIn()) return
      const signal = requestAbort?.signal
      await Promise.all(challenges.value.map(async (ch) => {
        try {
          const res = await axios.get(`/api/challenges/${ch.id}/stats`, bgConfig(signal))
          const d = res.data?.data || res.data
          if (d?.user_solved) solvedIds.value.add(ch.id)
          const n = readSolves(d)
          if (n != null) {
            ch.solves = n
            ch.solved_count = n
            ch.solves_count = n
          }
        } catch { /* ignore */ }
        try {
          const detail = await axios.get(`/api/challenges/${ch.id}`, bgConfig(signal))
          const d = detail.data?.data
          if (d?.is_solved) solvedIds.value.add(ch.id)
          const n = readSolves(d)
          if (n != null) {
            ch.solves = n
            ch.solved_count = n
            ch.solves_count = n
          }
        } catch { /* ignore */ }
      }))
      // 若当前正打开某题，同步刷新其 solves 显示
      if (selectedChallenge.value) {
        const cur = challenges.value.find(c => c.id === selectedChallenge.value.id)
        if (cur) {
          const n = readSolves(cur)
          if (n != null) {
            selectedChallenge.value = {
              ...selectedChallenge.value,
              solves: n,
              solved_count: n,
              solves_count: n,
            }
          }
        }
      }
      await refreshBloodBoard()
    }

    async function refreshBloodBoard() {
      if (!props.gameId || props.mode === 'training') return
      try {
        const res = await axios.get(
          `/api/challenges/games/${props.gameId}/first-solves`,
          bgConfig(requestAbort?.signal),
        )
        const rows = res.data?.data || []
        const grouped = {}
        for (const row of rows) {
          if (row.blood_level == null || row.blood_level > 2) continue
          if (!grouped[row.challenge_id]) grouped[row.challenge_id] = []
          grouped[row.challenge_id].push({
            blood_level: row.blood_level,
            user_name: row.user_name,
            team_name: row.team_name,
            solved_at: row.solved_at,
          })
        }
        for (const cid of Object.keys(grouped)) {
          grouped[cid].sort((a, b) => a.blood_level - b.blood_level)
          bloodMap.value[cid] = grouped[cid]
        }
      } catch { /* ignore */ }
    }

    const bloodPoll = createVisibilityPoll(() => {
      if (activeTab.value === 'blood') refreshBloodBoard()
    }, POLL_INTERVALS.blood)

    // 与 Docker 对账：容器中途退出时，前端不会一直假显示「运行中」
    const containerPoll = createVisibilityPoll(() => {
      if (hasContainer.value && selectedChallenge.value) loadContainerInstance()
    }, POLL_INTERVALS.container)

    async function selectChallenge(ch) {
      selectedChallenge.value = ch
      challengeOpenedAt.value[ch.id] = Date.now()
      if (ch.category) {
        const next = new Set(collapsedCategories.value)
        next.delete(ch.category)
        collapsedCategories.value = next
      }
      challengeSolved.value = isSolved(ch.id)
      flagInput.value = ''
      flagResult.value = null
      hintItems.value = []
      instance.value = null
      stats.value = null

      const query = { ...route.query, challenge: String(ch.id) }
      if (route.query.tab) query.tab = route.query.tab
      router.replace({ query }).catch(() => {})

      try {
        const detailPromise = axios.get(`/api/challenges/${ch.id}`)
        const statsPromise = axios.get(`/api/challenges/${ch.id}/stats`).catch(() => null)
        const [detailRes, statsRes] = await Promise.all([detailPromise, statsPromise])
        const detail = detailRes.data?.data || detailRes.data
        const statsData = statsRes?.data?.data || null
        if (detail) {
          selectedChallenge.value = sanitizeChallengeDetail(ch, detail)
          if (detail.is_solved) {
            challengeSolved.value = true
            solvedIds.value.add(ch.id)
          }
        }
        stats.value = statsData
        // 用 stats 回填 solves，保证列表字段缺失时也能显示
        if (statsData && selectedChallenge.value) {
          const n = readSolves(statsData)
          if (n != null) {
            selectedChallenge.value = {
              ...selectedChallenge.value,
              solves: n,
              solved_count: n,
              solves_count: n,
            }
          }
        }

        if (hasContainer.value) await loadContainerInstance()
        auxHintsOpen.value = false
        auxWriteupOpen.value = false
        await loadHints()
      } catch {
        message.error('加载题目详情失败')
      }
      emit('challenge-change', ch)
    }

    async function loadHints() {
      if (!selectedChallenge.value) return
      hintsLoading.value = true
      hintItems.value = []
      const fallback = selectedChallenge.value.hint
        ? [{ id: 'legacy', text: selectedChallenge.value.hint, penalty: 0, unlocked: true }]
        : []
      try {
        const res = await apiGetHints(selectedChallenge.value.id)
        const rows = res?.data || []
        if (!rows.length) {
          hintItems.value = fallback
          return
        }
        hintItems.value = rows.map(h => ({
          id: h.id,
          text: h.hint_text || h.text || '',
          penalty: h.penalty_points || 0,
          unlocked: props.mode === 'training' || h.is_accessed,
          unlocking: false,
        }))
      } catch {
        hintItems.value = fallback
      } finally {
        hintsLoading.value = false
      }
    }

    async function unlockHint(h) {
      if (!h?.id || h.id === 'legacy') return
      if (h.unlocked) return
      h.unlocking = true
      try {
        const res = await apiAccessHint(h.id)
        const payload = res?.data || res
        const text = payload?.hint?.hint_text || payload?.hint_text || h.text
        const penalty = Number(payload?.penalty ?? payload?.penalty_points ?? h.penalty ?? 0)
        h.text = text
        h.unlocked = true
        h.penalty = penalty
        if (penalty > 0 && props.mode !== 'training') {
          message.success(`提示已解锁，已扣除 ${penalty} 分`)
        } else {
          message.success('提示已解锁')
        }
      } catch (e) {
        message.error(apiErrorMessage(e, '解锁提示失败'))
      } finally {
        h.unlocking = false
      }
    }

    function clearRemainingTimer() {
      if (remainingTimer) {
        clearInterval(remainingTimer)
        remainingTimer = null
      }
    }

    function startRemainingTimer() {
      clearRemainingTimer()
      if (!instance.value || remainingSeconds.value <= 0) return
      remainingTimer = setInterval(() => {
        if (remainingSeconds.value <= 1) {
          remainingSeconds.value = 0
          clearRemainingTimer()
          instance.value = null
          message.warning('容器已到期，请重新开启')
          return
        }
        remainingSeconds.value -= 1
      }, 1000)
    }

    async function loadContainerInstance() {
      if (!selectedChallenge.value) return
      try {
        const payload = await apiGetContainerStatus(selectedChallenge.value.id)
        const d = payload?.data
        if (d?.status === 'running' || d?.has_container) {
          const url = d.connection_url || ''
          instance.value = {
            connection_url: url,
            port: url.match(/:(\d+)/)?.[1],
            instance_id: d.instance_id,
            expires_at: d.expires_at,
          }
          remainingSeconds.value = Number(d.remaining_seconds) || 0
          startRemainingTimer()
          if (!url) {
            message.warning('容器运行中但缺少连接地址，请重新启动')
          }
        } else {
          instance.value = null
          remainingSeconds.value = 0
          clearRemainingTimer()
        }
      } catch {
        instance.value = null
        remainingSeconds.value = 0
        clearRemainingTimer()
      }
    }

    function openEnvironment() {
      const url = instance.value?.connection_url
      if (url) {
        window.open(url, '_blank', 'noopener')
        return
      }
      if (!instance.value) {
        startContainer()
        return
      }
      message.warning('暂无公网连接地址，请尝试重新启动靶机')
    }

    async function startContainer() {
      if (!selectedChallenge.value || containerBusy.value) return
      containerLoading.value = true
      queueStatus.value = ''
      try {
        const payload = await apiStartContainer(selectedChallenge.value.id, { asyncMode: true })
        const d = payload?.data || {}
        if (d.job_id && (payload?.code === 202 || d.queued)) {
          queueStatus.value = `排队中… 位置 ${d.position ?? '-'} / 队列 ${d.queue_length ?? '-'}`
          const done = await pollContainerJob(d.job_id)
          if (!done) {
            message.error('启容器排队失败或超时')
            return
          }
          message.success('容器已启动')
          await loadContainerInstance()
          return
        }
        if (payload?.code === 200 || payload?.success || d.instance_id) {
          message.success('容器已启动')
          await loadContainerInstance()
        } else {
          message.error(payload?.msg || payload?.message || '启动失败')
        }
      } catch (e) {
        message.error(apiErrorMessage(e, '启动失败'))
      } finally {
        containerLoading.value = false
        queueStatus.value = ''
      }
    }

    async function pollContainerJob(jobId) {
      const deadline = Date.now() + 120000
      while (Date.now() < deadline) {
        try {
          const res = await getContainerJob(jobId)
          const st = res?.data || {}
          if (st.status === 'queued' || st.status === 'waiting') {
            queueStatus.value = `排队中… 位置 ${st.position ?? '-'}`
          } else if (st.status === 'running') {
            queueStatus.value = '正在启动容器…'
          } else if (st.status === 'done') {
            queueStatus.value = ''
            return true
          } else if (st.status === 'failed' || st.status === 'timeout') {
            queueStatus.value = ''
            message.error(st.msg || '启动失败')
            return false
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 800))
      }
      return false
    }

    async function loadInstanceLogs() {
      const iid = instance.value?.id || instance.value?.instance_id
      if (!iid) return
      logsLoading.value = true
      try {
        const res = await getInstanceLogs(iid, 200)
        const text = res?.data?.logs ?? res?.logs ?? res?.data?.text ?? ''
        instanceLogs.value = typeof text === 'string' ? text : JSON.stringify(text, null, 2)
      } catch (e) {
        instanceLogs.value = apiErrorMessage(e, '拉取日志失败')
      } finally {
        logsLoading.value = false
      }
    }

    async function extendContainer() {
      const id = instanceId.value
      if (!id || containerBusy.value) return
      extending.value = true
      try {
        const payload = await apiExtendContainer(id)
        const d = payload?.data
        if (payload?.code === 200 || payload?.success || d) {
          if (d?.remaining_seconds != null) remainingSeconds.value = Number(d.remaining_seconds) || remainingSeconds.value
          else remainingSeconds.value += 3600
          if (d?.expires_at && instance.value) instance.value.expires_at = d.expires_at
          startRemainingTimer()
          message.success(payload?.msg || '已延时 1 小时')
        } else {
          message.error(payload?.msg || payload?.message || '延时失败')
        }
      } catch (e) {
        message.error(apiErrorMessage(e, '延时失败'))
      } finally {
        extending.value = false
      }
    }

    async function destroyContainer() {
      const id = instanceId.value
      if (!id || containerBusy.value) return
      destroying.value = true
      try {
        const payload = await apiStopContainer(id)
        if (payload?.code === 200 || payload?.success !== false) {
          instance.value = null
          remainingSeconds.value = 0
          clearRemainingTimer()
          message.success(payload?.msg || '容器已销毁')
        } else {
          message.error(payload?.msg || payload?.message || '销毁失败')
        }
      } catch (e) {
        message.error(apiErrorMessage(e, '销毁失败'))
      } finally {
        destroying.value = false
      }
    }

    function selectConnText(e) {
      const el = e?.currentTarget
      if (!el) return
      const range = document.createRange()
      range.selectNodeContents(el)
      const sel = window.getSelection()
      sel?.removeAllRanges()
      sel?.addRange(range)
    }

    function copyConn() {
      const url = instance.value?.connection_url
      if (!url) {
        message.warning('暂无连接地址可复制')
        return
      }
      // Pwn: 若是 host:port，顺带生成 nc 命令
      let text = url
      const m = url.match(/^(?:nc\s+)?([\w.-]+)\s+(\d+)$/i) || url.match(/^([\w.-]+):(\d+)$/)
      if (m && !/^https?:/i.test(url)) {
        text = `nc ${m[1]} ${m[2]}`
      }
      const done = () => message.success(isTcpConn.value ? '已复制 nc 命令' : '已复制连接地址')
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(() => {
          // fallback: 选中文本提示手动 Ctrl+C
          message.info('自动复制失败，请手动选中地址后 Ctrl+C')
        })
        return
      }
      try {
        const ta = document.createElement('textarea')
        ta.value = text
        ta.setAttribute('readonly', '')
        ta.style.position = 'fixed'
        ta.style.left = '-9999px'
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
        done()
      } catch {
        message.info('请手动选中地址后复制')
      }
    }

    async function submitFlag() {
      if (!selectedChallenge.value || !flagInput.value.trim() || submitting.value) return
      submitting.value = true
      try {
        const body = { answer: flagInput.value.trim(), flag: flagInput.value.trim() }
        const opened = challengeOpenedAt.value[selectedChallenge.value.id]
        if (opened) body.elapsed_ms = Math.max(0, Date.now() - opened)
        const res = await axios.post(
          `/api/challenges/${selectedChallenge.value.id}/submit`,
          body,
        )
        const payload = res.data?.data || res.data
        const correct = payload?.is_correct || payload?.correct || res.data?.correct
        if (correct) {
          const bloodNames = ['一血', '二血', '三血']
          const bloodLevel = payload?.blood_level
          const bloodMsg = bloodLevel != null && bloodLevel < 3
            ? `${bloodNames[bloodLevel]} 获得！`
            : ''
          flagResult.value = { ok: true, msg: '[SUCCESS] Flag accepted! 恭喜解出！' + bloodMsg }
          message.success('Flag 正确！' + bloodMsg)
          challengeSolved.value = true
          solvedIds.value.add(selectedChallenge.value.id)
          // 即时刷新 solves：优先用提交响应，再回拉 /stats
          const solvesFromSubmit = readSolves(payload)
          const applySolves = (n) => {
            if (n == null) return
            selectedChallenge.value = {
              ...selectedChallenge.value,
              solves: n,
              solved_count: n,
              solves_count: n,
            }
            const listItem = challenges.value.find(c => c.id === selectedChallenge.value.id)
            if (listItem) {
              listItem.solves = n
              listItem.solved_count = n
              listItem.solves_count = n
            }
            if (stats.value) {
              stats.value = {
                ...stats.value,
                unique_solvers: n,
                solves: n,
                solved_count: n,
                solves_count: n,
              }
            } else {
              stats.value = { unique_solvers: n, solves: n, solved_count: n, solves_count: n }
            }
          }
          if (solvesFromSubmit != null) {
            applySolves(solvesFromSubmit)
          } else {
            applySolves((readSolves(selectedChallenge.value) || 0) + 1)
          }
          axios.get(`/api/challenges/${selectedChallenge.value.id}/stats`)
            .then((r) => {
              const d = r.data?.data
              const n = readSolves(d)
              if (n != null) applySolves(n)
              if (d) stats.value = { ...(stats.value || {}), ...d }
            })
            .catch(() => {})
          if (bloodLevel != null && bloodLevel <= 2) {
            const cid = selectedChallenge.value.id
            const list = bloodMap.value[cid] ? [...bloodMap.value[cid]] : []
            if (!list.some(r => r.blood_level === bloodLevel)) {
              list.push({
                blood_level: bloodLevel,
                user_name: '你',
                team_name: null,
                solved_at: new Date().toISOString(),
              })
              list.sort((a, b) => a.blood_level - b.blood_level)
              bloodMap.value[cid] = list
            }
          }
        } else {
          flagResult.value = { ok: false, msg: '[FAIL] ' + (res.data?.msg || 'Flag 错误，继续尝试') }
          message.error(res.data?.msg || 'Flag 错误，继续尝试')
        }
      } catch (e) {
        flagResult.value = { ok: false, msg: '[ERROR] ' + apiErrorMessage(e, '提交失败') }
        message.error(apiErrorMessage(e, '提交失败'))
      } finally {
        submitting.value = false
      }
    }

    function onTabChange(tab) {
      router.replace({ query: { ...route.query, tab } }).catch(() => {})
    }

    function syncFromRoute() {
      const chId = route.query.challenge
      const tab = route.query.tab
      const allowed = [
        'terminal', 'hints', 'hammer', 'blood', 'writeup', 'manage',
      ]
      if (tab && LEGACY_ADMIN_TAB_MAP[tab]) {
        activeTab.value = adminActive.value ? LEGACY_ADMIN_TAB_MAP[tab] : 'terminal'
      } else if (tab && allowed.includes(tab)) {
        if (tab === 'manage' && !adminActive.value) {
          activeTab.value = 'terminal'
        } else {
          activeTab.value = tab
        }
      }
      if (chId && challenges.value.length) {
        const ch = challenges.value.find(c => c.id === parseInt(chId, 10))
        if (ch && selectedChallenge.value?.id !== ch.id) selectChallenge(ch)
      }
    }

    function refreshAdminState() {
      const wasAdmin = isAdmin.value
      isAdmin.value = checkIsAdmin()
      if (!isAdmin.value) {
        if (showAdminTools.value) setAdminTools(false)
        showAdminTools.value = false
      } else if (!wasAdmin) {
        applyAdminQueryFromRoute()
      }
    }

    watch(challengeTree, (tree) => {
      if (!tree.length || collapsedCategories.value.size) return
      const next = new Set()
      for (let i = 1; i < tree.length; i += 1) {
        next.add(tree[i].category)
      }
      collapsedCategories.value = next
    }, { immediate: true })

    watch(() => props.gameId, async () => {
      selectedChallenge.value = null
      beginRequestScope()
      await ensureTrainingAccess()
      await loadGameMeta()
      await loadChallenges()
      syncFromRoute()
    })

    watch(() => route.query.challenge, syncFromRoute)

    watch(showAdminTools, (on, prev) => {
      if (on === prev) return
      if (!on && ADMIN_ONLY_TABS.has(activeTab.value)) {
        activeTab.value = 'terminal'
      }
    })

    onMounted(async () => {
      beginRequestScope()
      await fetchSession()
      refreshAdminState()
      applyAdminQueryFromRoute()
      window.addEventListener('neepu_user_refreshed', refreshAdminState)
      await ensureTrainingAccess()
      await loadGameMeta()
      await loadChallenges()
      syncFromRoute()
      bloodPoll.start()
      containerPoll.start()
    })

    onUnmounted(() => {
      requestAbort?.abort()
      requestAbort = null
      clearRemainingTimer()
      bloodPoll.stop()
      containerPoll.stop()
      window.removeEventListener('neepu_user_refreshed', refreshAdminState)
    })


    const shellPath = computed(() =>
      props.mode === 'training' ? `~/training/${props.gameId}` : `~/games/${props.gameId}/challenges`,
    )
    const shellCmd = computed(() => '')
    const shellPagePrompt = computed(() => {
      if (props.embedded) return ''
      const name = displayGameTitle.value || (props.mode === 'training' ? '练习场' : '赛事')
      return props.mode === 'training'
        ? `练习场 · TRAINING / ${name}`
        : `赛事 · CHALLENGES / ${name}`
    })
    const shellPageTitle = computed(() => '')
    const shellPageDesc = computed(() => '')

    return {
      shellPath, shellCmd, shellPagePrompt, shellPageTitle, shellPageDesc, displayGameTitle,
      challenges, challengesLoading, challengesLoadError, selectedChallenge, searchQuery,
      challengeTree, filteredChallenges, activeTab,
      flagInput, submitting, challengeSolved, flagResult, hintItems, hintsLoading, auxHintsOpen, auxWriteupOpen, stats, instance,
      containerLoading, queueStatus, instanceLogs, logsLoading,
      extending, destroying, containerBusy, remainingLabel,
      gameStatusType, descriptionContent, writeupContent,
      hasContainer, supportsContainer, isContainerChallenge, isAttachmentChallenge, showAttachmentBar, isTcpConn, endpointDisplay, instanceId, attachmentUrl, isAdmin, showAdminTools, adminActive,
      challengeTypeLabel, toggleAdminTools, challengePoints, solveCount,
      isCategoryExpanded, toggleCategory, closeChallenge,
      isSolved, bloodRecords, bloodLevelName, bloodLevelShort, currentBloodRecords,
      selectChallenge, submitFlag, startContainer, extendContainer, destroyContainer, openEnvironment, loadChallenges,
      loadInstanceLogs, copyConn, selectConnText, onTabChange, loadHints, unlockHint, toggleChallengeEnabled,
      goAdminChallenge, formatStatTime, categoryStyle, categoryChipStyle,
    }
  },
}
</script>

<style scoped>
.workspace-dock {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  border: var(--dock-border-width, 0) solid var(--gradient-card-border, var(--border));
  border-radius: var(--dock-radius, 0);
  overflow: hidden;
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--dock-shadow, none);
}

.challenge-workspace.admin-tools-on {
  outline: 1px solid rgba(217, 119, 6, 0.35);
  outline-offset: 2px;
}

/* ── 左栏：题目树 ── */
.tree-panel {
  --tree-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: transparent;
  font-family: var(--tree-font);
  font-size: 13px;
  font-weight: 400;
  line-height: 1.45;
  -webkit-font-smoothing: antialiased;
}

.tree-panel,
.tree-panel .tree-cat,
.tree-panel .tree-cat-name,
.tree-panel .tree-item,
.tree-panel .tree-item-title,
.tree-panel .tree-panel-title,
.tree-panel .tree-empty,
.tree-panel .status-chip {
  font-family: var(--tree-font) !important;
}

.tree-panel--matrix {
  border-top: 1px solid var(--border);
}

.tree-panel-head {
  padding: 14px 16px 12px;
  border-bottom: 1px solid var(--border);
}

.tree-title-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: 10px;
  min-height: 28px;
  width: 100%;
}

.tree-title-row .tree-panel-title {
  flex: 0 1 auto;
  min-width: 0;
  max-width: calc(100% - 96px);
  width: auto;
  display: block;
}

.tree-title-row .status-chip,
.tree-title-row .n-tag {
  flex: 0 0 auto;
}

.status-chip {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  line-height: 1;
  white-space: nowrap;
  border: 1px solid transparent;
}

.status-chip--open {
  color: #5ED9A8;
  border-color: rgba(94, 217, 168, 0.35);
  background: rgba(94, 217, 168, 0.1);
}

.tree-panel-title {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 700;
  line-height: 1.35;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-body {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0 12px;
  min-height: 0;
}

.tree-empty {
  padding: 20px 14px;
  font-size: var(--text-sm);
  color: var(--muted);
  text-align: center;
}

.tree-group { margin-bottom: 2px; }

.tree-cat {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 14px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  text-align: left;
}

.tree-cat:hover { background: var(--hover); }

.tree-cat-icon {
  width: 12px;
  font-size: var(--text-xs);
  color: var(--muted);
}

.tree-cat-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-items {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px 8px 32px;
  font-size: 13px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--text);
  cursor: pointer;
  transition: background 0.12s;
}

.tree-item:hover { background: var(--hover); }

.tree-item.active {
  background: rgba(var(--primary-rgb), 0.12);
  color: var(--primary);
  font-weight: 600;
}

.tree-item.solved .tree-item-title { color: var(--success, #16A34A); }
.tree-item.disabled { opacity: 0.5; }

.tree-item-title {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-item-mark {
  flex-shrink: 0;
  font-size: var(--text-xs);
  color: var(--success);
}

.tree-item-menu {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 0 2px;
  font-size: var(--text-sm);
}

.tree-footer {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
}

/* ── 右栏：工作区 ── */
.workspace-stage {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  height: 100%;
  width: 100%;
  background: var(--gradient-card-bg, var(--card-bg));
}

.stage-admin-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 16px 0;
}

.stage-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  padding: 20px 24px 28px;
  overflow-y: auto;
}

.stage-brief {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  gap: 0;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 0;
  border-bottom: none;
  max-height: none;
  overflow: visible;
  min-height: 0;
  box-sizing: border-box;
}

.brief-title-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}

.brief-title-row h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 700;
}

.brief-env-hint {
  font-size: var(--text-xs);
  color: var(--muted);
}

.brief-desc {
  line-height: 1.7;
  font-size: var(--text-sm);
  color: var(--text);
}

.brief-desc :deep(pre) {
  background: var(--code-bg);
  padding: 10px 12px;
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.brief-aside {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  flex-shrink: 0;
  min-width: var(--workspace-action-width, 96px);
}

.brief-stat {
  text-align: right;
}

.brief-stat-num {
  display: block;
  font-size: var(--text-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--text);
  line-height: 1.2;
}

.brief-stat-label {
  font-size: var(--text-xs);
  color: var(--muted);
}

.brief-launch {
  min-width: 88px;
  font-weight: 600;
}

.brief-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px 24px;
  margin-bottom: 8px;
  width: 100%;
}

.brief-header .brief-title-row {
  flex: 1 1 auto;
  min-width: 0;
  margin-bottom: 0;
}

.points-board {
  flex: 0 0 auto;
  display: flex;
  align-items: baseline;
  gap: 5px;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  line-height: 1;
  user-select: none;
}

.points-board__num {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
  font-size: clamp(26px, 2.8vw, 32px);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
  color: #9af0c0;
  text-shadow: none;
}

.points-board__unit {
  font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: rgba(160, 176, 192, 0.72);
  transform: translateY(-1px);
}

@media (max-width: 720px) {
  .brief-header {
    flex-wrap: wrap;
  }
  .points-board {
    margin-left: auto;
  }
  .points-board__num {
    font-size: 24px;
  }
}

.cat-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.4;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-chip--lg {
  max-width: none;
  font-size: var(--text-xs);
  padding: 4px 12px;
}


.stage-empty--canvas {
  flex: 1 1 auto;
  width: 100%;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  background: transparent;
}

.tag-row { display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap; }

.attachment-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  font-size: var(--text-sm);
}

.attachment-row a,
.attachment-dl { color: var(--primary); font-weight: 600; }

.attachment-row--primary {
  padding: 10px 12px;
  border: 1px solid rgba(var(--primary-rgb), 0.35);
  border-radius: var(--card-radius, 12px);
  background: rgba(var(--primary-rgb), 0.08);
}

.attachment-row--empty {
  opacity: 0.75;
}

.container-panel {
  margin-top: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius, 12px);
  background: var(--code-bg, rgba(0, 0, 0, 0.04));
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.container-panel-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.container-panel-title {
  font-weight: 700;
  font-size: var(--text-sm);
}

.container-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
}

.container-status.running {
  color: var(--success, #16a34a);
  background: rgba(22, 163, 74, 0.12);
}

.container-status.idle {
  color: var(--muted);
  background: rgba(128, 128, 128, 0.12);
}

.container-ttl {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 13px;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}

.container-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.queue-status {
  margin-top: 8px;
  font-size: 12px;
  color: var(--primary, #D97706);
}




.conn-box {
  padding: 10px 12px;
  background: var(--term-bg, var(--page-bg));
  color: var(--term-fg, var(--primary));
  border-radius: var(--radius-md);
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: var(--text-sm);
  word-break: break-all;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.conn-url {
  flex: 1;
  min-width: 0;
  cursor: text;
  user-select: all;
}

.container-warn {
  margin: 0 0 8px;
  padding: 8px 10px;
  font-size: var(--text-xs);
  line-height: 1.5;
  color: var(--warning, #D97706);
  background: rgba(217, 119, 6, 0.1);
  border-radius: var(--radius-sm);
}

.tcp-badge {
  font-size: var(--text-xs);
  padding: 1px 6px;
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
}

.hint-list { list-style: none; margin: 0; padding: 0; }
.hint-item { padding: 10px 0; border-bottom: 1px solid var(--border); }
.hint-item:last-child { border-bottom: none; }
.hint-head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.penalty-tag { font-size: var(--text-xs); color: var(--accent-red, #f83030); }
.hint-text { margin: 0; line-height: 1.7; font-size: var(--text-sm); }

.blood-tag {
  font-size: var(--text-xs);
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
}
.blood-tag--0 { color: #ef4444; background: rgba(239, 68, 68, 0.12); }
.blood-tag--1 { color: #f97316; background: rgba(249, 115, 22, 0.12); }
.blood-tag--2 { color: #eab308; background: rgba(234, 179, 8, 0.12); }

.blood-list { list-style: none; padding: 0; margin: 0; }
.blood-list-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: var(--text-sm);
}
.blood-time { margin-left: auto; font-size: var(--text-xs); }

.admin-manage-hint {
  margin: 0 0 12px;
  padding: 8px 10px;
  font-size: var(--text-xs);
  color: var(--warning, #D97706);
  background: rgba(217, 119, 6, 0.08);
  border-radius: var(--radius-sm);
}

.manage-section {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.manage-section:last-child { border-bottom: none; margin-bottom: 0; }
.manage-section-title {
  margin: 0 0 8px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
}
.manage-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }

.admin-popover { display: flex; flex-direction: column; gap: 8px; min-width: 120px; }
.admin-popover__hint { margin: 0; font-size: var(--text-sm); color: var(--muted); }

.admin-panel { display: flex; flex-direction: column; gap: 10px; font-size: var(--text-sm); }
.admin-link { color: var(--primary); font-size: var(--text-sm); }
.admin-panel .stat-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}
.admin-panel .stat-row:last-child { border-bottom: none; }
.mono { font-family: monospace; font-size: var(--text-xs); word-break: break-all; }
.muted { color: var(--muted); }

@media (max-width: 900px) {
  /* G26: 窄屏关键路径不被侧栏/工具条挡住 */
  .tree-body { max-height: 180px; }
  .stage-brief {
    grid-template-columns: 1fr;
    max-height: none;
  }
  .brief-aside {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    justify-content: flex-start;
  }
  .container-actions,
  .stage-tabs {
    position: sticky;
    bottom: 0;
    z-index: 5;
    background: var(--panel-bg, rgba(20, 24, 36, 0.96));
    padding-bottom: env(safe-area-inset-bottom, 8px);
  }
  .conn-box { font-size: 12px; }
}

@media (prefers-reduced-motion: reduce) {
  .tree-item { transition: none; }
}

/* 顶栏压缩为单行面包屑 */
.challenge-workspace-matrix :deep(.matrix-page-head) {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  margin: 0 !important;
  padding: 8px 16px !important;
  min-height: 36px !important;
  border-bottom: 1px solid var(--border) !important;
}
.challenge-workspace-matrix :deep(.matrix-page-prompt) {
  margin: 0 !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.04em !important;
  color: var(--muted) !important;
  line-height: 1.2 !important;
}
.challenge-workspace-matrix :deep(.matrix-page-title),
.challenge-workspace-matrix :deep(.matrix-page-desc) {
  display: none !important;
}

.stage-brief {
  display: flex !important;
  flex-direction: column !important;
  flex: 1 1 auto !important;
  grid-template-columns: none !important;
  max-width: none !important;
  width: 100% !important;
  margin: 0 !important;
  max-height: none !important;
  border-bottom: none !important;
}

.stage-content {
  padding: 20px 24px 28px !important;
}

.tree-title-row {
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  gap: 10px !important;
}

.brief-title-row {
  align-items: center !important;
  gap: 10px !important;
}

.brief-solves {
  font-family: var(--font-mono, "JetBrains Mono", monospace);
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.challenge-actions-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 12px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-ui);
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s, transform 0.15s, color 0.15s;
  color: inherit;
  background: transparent;
}
.action-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.action-btn:not(:disabled):hover {
  transform: translateY(-1px);
}
.action-btn--mint {
  color: #5ED9A8;
  border-color: rgba(94, 217, 168, 0.35);
  background: rgba(94, 217, 168, 0.1);
}
.action-btn--mint:not(:disabled):hover {
  border-color: rgba(94, 217, 168, 0.55);
  background: rgba(94, 217, 168, 0.18);
}
.action-btn--docker {
  color: #2496ED;
  border-color: rgba(36, 150, 237, 0.4);
  background: rgba(36, 150, 237, 0.12);
}
.action-btn--docker:not(:disabled):hover {
  border-color: rgba(36, 150, 237, 0.6);
  background: rgba(36, 150, 237, 0.2);
}
.action-btn--danger {
  color: #FB7185;
  border-color: rgba(251, 113, 133, 0.35);
  background: rgba(251, 113, 133, 0.08);
}
.action-btn--danger:not(:disabled):hover {
  border-color: rgba(251, 113, 133, 0.55);
  background: rgba(251, 113, 133, 0.14);
}
.action-btn--ghost {
  color: var(--muted);
  border-color: rgba(255, 255, 255, 0.1);
}

.env-runtime {
  margin: 0 0 12px;
  padding: 10px 12px;
  border: 1px solid rgba(36, 150, 237, 0.22);
  border-radius: 8px;
  background: rgba(36, 150, 237, 0.06);
}

.flag-submit-panel {
  margin: 4px 0 8px;
  padding: 20px;
  border: 1px solid rgba(94, 217, 168, 0.32);
  border-radius: 12px;
  background: rgba(94, 217, 168, 0.05);
}
.flag-submit-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.flag-solved-badge {
  margin-left: auto;
  font-size: 11px;
  color: #5ED9A8;
  font-family: var(--font-mono, monospace);
}
.flag-submit-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.flag-submit-input {
  flex: 1;
  min-width: 0;
  height: 52px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.28);
  color: var(--text);
  font-size: 15px;
  font-family: var(--font-mono, "JetBrains Mono", monospace);
  outline: none;
}
.flag-submit-input:focus {
  border-color: rgba(94, 217, 168, 0.45);
}
.flag-submit-input:disabled {
  opacity: 0.55;
}
.flag-submit-btn {
  flex-shrink: 0;
  height: 52px;
  min-width: 140px;
  padding: 0 22px;
  border-radius: 10px;
  border: 1px solid rgba(94, 217, 168, 0.55);
  background: rgba(94, 217, 168, 0.28);
  color: #5ED9A8;
  font-size: 15px;
  font-weight: 800;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
}
.flag-submit-btn:hover:not(:disabled) {
  background: rgba(94, 217, 168, 0.28);
  border-color: rgba(94, 217, 168, 0.65);
}
.flag-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.flag-submit-result {
  margin: 8px 0 0;
  font-size: 12px;
  font-family: var(--font-mono, monospace);
}
.flag-submit-result.is-ok { color: #5ED9A8; }
.flag-submit-result.is-err { color: #FB7185; }


/* cockpit: Flag docked bottom, enlarged */
.brief-main {
  width: 100%;
  max-width: none;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.flag-submit-panel,
.flag-submit-panel--dock {
  margin-top: auto;
  margin-bottom: 0;
  width: 100%;
  max-width: none;
  padding: 20px 20px 18px;
  border: 1px solid rgba(94, 217, 168, 0.32);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(94, 217, 168, 0.08), rgba(0, 0, 0, 0.22));
  box-sizing: border-box;
}

.flag-submit-panel--dock .flag-submit-head {
  margin-bottom: 14px;
  font-size: 15px;
  font-weight: 700;
}

.flag-submit-panel--dock .flag-submit-row {
  gap: 12px;
  align-items: stretch;
}

.flag-submit-panel--dock .flag-submit-input {
  height: 52px;
  padding: 14px 16px;
  font-size: 15px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.35);
}

.flag-submit-panel--dock .flag-submit-input:focus {
  border-color: rgba(94, 217, 168, 0.55);
  box-shadow: 0 0 0 3px rgba(94, 217, 168, 0.12);
}

.flag-submit-panel--dock .flag-submit-btn {
  height: 52px;
  min-width: 140px;
  padding: 0 22px;
  border-radius: 10px;
  border: 1px solid rgba(94, 217, 168, 0.55);
  background: rgba(94, 217, 168, 0.28);
  color: #5ED9A8;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.02em;
  box-shadow: 0 4px 16px rgba(94, 217, 168, 0.15);
  transition: background 0.15s, border-color 0.15s, transform 0.15s, box-shadow 0.15s;
}

.flag-submit-panel--dock .flag-submit-btn:hover:not(:disabled) {
  background: rgba(94, 217, 168, 0.42);
  border-color: rgba(94, 217, 168, 0.75);
  color: #E8FFF5;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(94, 217, 168, 0.22);
}

.flag-submit-panel--dock .flag-submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.flag-submit-panel--dock .flag-submit-result {
  margin-top: 12px;
  font-size: 13px;
}


/* Inline Env Bar — 行内轻量化靶机条 */
.inline-env-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin: 10px 0 14px;
  padding: 0;
  background: transparent;
  border: none;
  min-height: 32px;
}

.inline-env-hint {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.01em;
}

.inline-env-hint.is-live {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: rgba(232, 255, 245, 0.78);
}

.inline-env-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #5ED9A8;
  box-shadow: 0 0 8px rgba(94, 217, 168, 0.55);
  flex-shrink: 0;
}

.inline-env-endpoint {
  font-family: var(--font-mono, "JetBrains Mono", monospace);
  font-size: 13px;
  font-weight: 600;
  color: #5ED9A8;
  cursor: pointer;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(94, 217, 168, 0.2);
  background: rgba(94, 217, 168, 0.06);
}

.inline-env-endpoint:hover {
  border-color: rgba(94, 217, 168, 0.45);
  background: rgba(94, 217, 168, 0.12);
}

.inline-env-start {
  flex-shrink: 0;
  height: 30px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid rgba(94, 217, 168, 0.4);
  background: rgba(94, 217, 168, 0.08);
  color: #5ED9A8;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-ui, inherit);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
}

.inline-env-start:hover:not(:disabled) {
  background: rgba(94, 217, 168, 0.16);
  border-color: rgba(94, 217, 168, 0.6);
  transform: translateY(-1px);
}

.inline-env-start:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.inline-env-actions {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 2px;
  margin-left: auto;
}

.inline-env-link {
  height: 28px;
  padding: 0 10px;
  border: none;
  background: transparent;
  color: #5ED9A8;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-ui, inherit);
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.12s, color 0.12s;
}

.inline-env-link:hover:not(:disabled) {
  background: rgba(94, 217, 168, 0.1);
}

.inline-env-link:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.inline-env-link.is-danger {
  color: #FB7185;
}

.inline-env-link.is-danger:hover:not(:disabled) {
  background: rgba(251, 113, 133, 0.1);
}

.inline-env-ttl {
  margin-left: 6px;
  font-family: var(--font-mono, monospace);
  font-size: 11px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

.inline-env-queue {
  flex-basis: 100%;
  margin: 0;
  font-size: 12px;
  color: rgba(94, 217, 168, 0.7);
}



</style>
