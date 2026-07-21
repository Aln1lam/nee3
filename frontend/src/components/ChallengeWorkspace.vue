<template>
  <MatrixShell
    class="challenge-workspace-matrix"
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
        <router-link v-if="backLink" :to="backLink.to" class="tree-back">{{ backLink.label }}</router-link>
        <div class="tree-title-row">
          <h2 class="tree-panel-title">{{ gameTitle || '题目' }}</h2>
          <button type="button" class="tree-refresh" aria-label="刷新题目" :disabled="challengesLoading" @click="loadChallenges">↻</button>
        </div>
        <n-tag v-if="mode === 'training'" size="small" type="success" round>永久开放</n-tag>
        <n-tag v-else-if="gameStatus" size="small" :type="gameStatusType">{{ gameStatus }}</n-tag>
      </div>

      <div class="tree-search">
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索名称或者标签"
          clearable
          size="small"
        />
      </div>

      <div class="tree-body">
        <UiLoadingTips v-if="challengesLoading && !challenges.length" />
        <div v-else-if="!challengeTree.length" class="tree-empty">
          <template v-if="challengesLoadError">加载失败，请点击刷新重试</template>
          <template v-else>{{ mode === 'competition' ? '暂无任务' : '暂无题目' }}</template>
        </div>
        <div v-for="group in challengeTree" :key="group.category" class="tree-group">
          <button type="button" class="tree-cat" @click="toggleCategory(group.category)">
            <span class="tree-cat-icon">{{ isCategoryExpanded(group.category) ? '▼' : '▶' }}</span>
            <span class="tree-cat-name">{{ group.category }}</span>
            <span class="tree-cat-count">{{ group.items.length }}</span>
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

    <template #sidebar-footer>
      <router-link v-if="mode === 'training'" to="/training" class="sidebar-link">
        <span class="link-code">BAK</span>
        <span>练习场列表</span>
      </router-link>
      <router-link v-else :to="`/games/${gameId}`" class="sidebar-link">
        <span class="link-code">GME</span>
        <span>赛事详情</span>
      </router-link>
      <router-link to="/games" class="sidebar-link">
        <span class="link-code">CTF</span>
        <span>赛事列表</span>
      </router-link>
      <router-link v-if="mode !== 'training'" :to="`/games/${gameId}/scoreboard`" class="sidebar-link">
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
        <div class="stage-tabbar">
          <span class="stage-home" aria-hidden="true">⌂</span>
          <div class="stage-tab active">
            <span class="stage-tab-code">&lt;/&gt;</span>
            <span class="stage-tab-label">{{ selectedChallenge.title }}</span>
            <button type="button" class="stage-tab-close" aria-label="关闭题目" @click="closeChallenge">×</button>
          </div>
        </div>

        <div class="stage-content">
          <div class="stage-brief">
            <div class="brief-main">
              <div class="brief-title-row">
                <h3>{{ selectedChallenge.title }}</h3>
                <span v-if="hasContainer" class="brief-env-hint">题目可开启在线环境</span>
              </div>
              <div v-if="selectedChallenge.tags?.length" class="tag-row">
                <n-tag v-for="t in selectedChallenge.tags" :key="t" size="small">{{ t }}</n-tag>
              </div>
              <Article :content="descriptionContent" class="brief-desc" />
              <div v-if="attachmentUrl" class="attachment-row" :class="{ 'attachment-row--primary': !hasContainer }">
                <span>{{ hasContainer ? '附件' : '题目附件' }}</span>
                <a :href="attachmentUrl" target="_blank" rel="noopener" class="attachment-dl">下载附件</a>
              </div>
              <div v-else-if="!hasContainer" class="attachment-row attachment-row--empty">
                <span class="muted">本题无附件可下载</span>
              </div>
              <div v-if="hasContainer" class="container-panel">
                <div class="container-panel-head">
                  <span class="container-panel-title">在线环境</span>
                  <span v-if="instance" class="container-status running">运行中</span>
                  <span v-else class="container-status idle">未启动</span>
                </div>
                <template v-if="instance">
                  <div v-if="!instance.connection_url" class="container-warn">
                    暂无公网连接地址，请勿直连内网端口；点击「重新启动」或联系管理员。
                  </div>
                  <div v-else class="conn-box">
                    <span v-if="instance.port" class="tcp-badge">tcp</span>
                    <code class="conn-url" @click="selectConnText">{{ instance.connection_url }}</code>
                    <n-button text size="tiny" @click="copyConn">复制</n-button>
                  </div>
                  <div v-if="remainingLabel" class="container-ttl">剩余 {{ remainingLabel }}</div>
                  <div v-if="remainingSeconds > 0 && remainingSeconds < 900" class="container-warn">
                    即将到期，请及时延时或保存进度。
                  </div>
                  <div class="container-actions">
                    <n-button size="small" :loading="extending" :disabled="containerBusy" @click="extendContainer">延时 1 小时</n-button>
                    <n-button size="small" type="error" secondary :loading="destroying" :disabled="containerBusy" @click="destroyContainer">销毁</n-button>
                    <n-button size="small" secondary :loading="containerLoading" :disabled="containerBusy" @click="startContainer">重新启动</n-button>
                  </div>
                </template>
                <div v-else class="container-actions">
                  <n-button type="primary" size="small" :loading="containerLoading" :disabled="containerBusy" @click="startContainer">开启容器</n-button>
                </div>
                <div v-if="queueStatus" class="queue-status">{{ queueStatus }}</div>
              </div>
            </div>
            <div class="brief-aside">
              <div class="brief-stat">
                <span class="brief-stat-num">{{ solveCount }}</span>
                <span class="brief-stat-label">solves</span>
              </div>
              <span
                class="cat-chip cat-chip--lg"
                :style="categoryChipStyle(selectedChallenge.category)"
              >{{ selectedChallenge.category }}</span>
              <span v-if="mode !== 'training'" class="brief-points">{{ selectedChallenge.current_score || selectedChallenge.points || 0 }} pts</span>
            </div>
          </div>

          <div class="stage-tools">
            <n-tabs type="line" animated v-model:value="activeTab" class="workspace-tabs" @update:value="onTabChange">
              <n-tab-pane name="terminal" tab="终端">
                <div class="terminal-panel">
                  <div v-if="instance?.connection_url" class="conn-box">
                    <span v-if="instance.port" class="tcp-badge">tcp</span>
                    <code class="conn-url" @click="selectConnText">{{ instance.connection_url }}</code>
                    <n-button text size="tiny" @click="copyConn">复制</n-button>
                  </div>
                  <div v-else-if="instance" class="container-warn">
                    容器已启动但缺少 connection_url，请重新启动或看左侧「在线环境」。
                  </div>
                  <div v-if="instance?.id || instance?.instance_id" class="logs-box">
                    <div class="logs-head">
                      <span>容器日志</span>
                      <n-button text size="tiny" :loading="logsLoading" @click="loadInstanceLogs">刷新</n-button>
                    </div>
                    <pre class="logs-pre">{{ instanceLogs || '点击刷新拉取最近日志（非交互 Shell）' }}</pre>
                  </div>
                  <Terminal
                    v-model="flagInput"
                    :loading="submitting"
                    :disabled="challengeSolved"
                    :result="flagResult"
                    @submit="submitFlag"
                  />
                </div>
              </n-tab-pane>

              <n-tab-pane name="hints" tab="提示">
                <UiLoadingTips v-if="hintsLoading" spin-size="small" />
                <div v-else-if="hintItems.length === 0" class="muted">
                  {{ mode === 'training' ? '本题无提示，训练场提示自动解锁' : '本题无提示，如需提示请联系管理员' }}
                </div>
                <ul v-else class="hint-list">
                  <li v-for="(h, i) in hintItems" :key="h.id || i" class="hint-item">
                    <template v-if="h.unlocked">
                      <div class="hint-head">
                        <strong v-if="hintItems.length > 1">提示 {{ i + 1 }}</strong>
                        <span v-if="h.penalty > 0 && mode !== 'training'" class="penalty-tag">-{{ h.penalty }} pts</span>
                      </div>
                      <p class="hint-text">{{ h.text }}</p>
                    </template>
                    <template v-else>
                      <n-button size="small" :loading="h.unlocking" @click="unlockHint(h)">
                        解锁提示 {{ i + 1 }}{{ h.penalty > 0 ? ` (-${h.penalty} pts)` : '' }}
                      </n-button>
                    </template>
                  </li>
                </ul>
              </n-tab-pane>

              <n-tab-pane name="hammer" tab="🔨 锤子" :disabled="mode === 'training'">
                <HammerPanel
                  v-if="mode !== 'training' && selectedChallenge"
                  :challenge-id="selectedChallenge.id"
                  :game-id="gameId"
                />
              </n-tab-pane>

              <n-tab-pane v-if="adminActive" name="manage" tab="管理">
                <div class="admin-panel admin-panel--manage">
                  <p class="admin-manage-hint">管理视图含统计与配置信息，直播/录屏时请切回选手视图。</p>
                  <section v-if="stats" class="manage-section">
                    <h4 class="manage-section-title">统计</h4>
                    <div class="stat-row"><span>解出人数</span><strong>{{ stats.unique_solvers || 0 }}</strong></div>
                    <div class="stat-row"><span>总提交数</span><strong>{{ stats.total_submissions || 0 }}</strong></div>
                    <div class="stat-row"><span>通过率</span><strong>{{ stats.solve_rate || '0%' }}</strong></div>
                    <div v-if="stats.first_solver" class="stat-row">
                      <span>首解</span>
                      <strong>{{ stats.first_solver.username }} · {{ formatStatTime(stats.first_solver.solved_at) }}</strong>
                    </div>
                  </section>
                  <section v-else class="manage-section muted">正在加载统计…</section>
                  <section class="manage-section">
                    <h4 class="manage-section-title">题目设置</h4>
                    <div class="stat-row"><span>上架状态</span><strong>{{ selectedChallenge.is_enabled === false ? '已下架' : '已上架' }}</strong></div>
                    <div class="stat-row"><span>分类</span><strong>{{ selectedChallenge.category || '无' }}</strong></div>
                    <div class="stat-row"><span>类型</span><strong>{{ challengeTypeLabel }}</strong></div>
                    <div class="stat-row"><span>分值</span><strong>{{ selectedChallenge.current_score || selectedChallenge.points || 0 }}</strong></div>
                    <div v-if="selectedChallenge.flag_template" class="stat-row">
                      <span>Flag 模板</span><strong class="mono">{{ selectedChallenge.flag_template }}</strong>
                    </div>
                    <div class="manage-actions">
                      <UiButton
                        size="small"
                        :variant="selectedChallenge.is_enabled === false ? 'primary' : 'secondary'"
                        :loading="!!selectedChallenge._toggling"
                        @click="toggleChallengeEnabled(selectedChallenge)"
                      >{{ selectedChallenge.is_enabled === false ? '上架题目' : '下架题目' }}</UiButton>
                      <n-button size="small" type="primary" @click="goAdminChallenge">前往靶场管理</n-button>
                    </div>
                  </section>
                  <section class="manage-section">
                    <h4 class="manage-section-title">附件</h4>
                    <p v-if="attachmentUrl">附件 ID: {{ selectedChallenge.attachment_id }}</p>
                    <p v-else class="muted">本题暂无附件</p>
                    <a v-if="attachmentUrl" :href="attachmentUrl" target="_blank" rel="noopener" class="admin-link">下载附件</a>
                  </section>
                  <section v-if="hasContainer" class="manage-section">
                    <h4 class="manage-section-title">实例</h4>
                    <div v-if="instance" class="conn-box">
                      <span v-if="instance.port" class="tcp-badge">tcp</span>
                      {{ instance.connection_url || '无' }}
                    </div>
                    <p v-else class="muted">当前无运行中的实例</p>
                  </section>
                </div>
              </n-tab-pane>

              <n-tab-pane v-if="mode !== 'training'" name="blood" tab="血榜">
                <ul v-if="currentBloodRecords.length" class="blood-list">
                  <li v-for="rec in currentBloodRecords" :key="rec.blood_level" class="blood-list-item">
                    <span class="blood-tag" :class="`blood-tag--${rec.blood_level}`">{{ bloodLevelName(rec.blood_level) }}</span>
                    <span>{{ rec.user_name || '—' }}</span>
                    <span v-if="rec.team_name" class="muted">· {{ rec.team_name }}</span>
                    <span class="muted blood-time">{{ formatStatTime(rec.solved_at) }}</span>
                  </li>
                </ul>
                <div v-else class="muted">暂无首解记录</div>
              </n-tab-pane>

              <n-tab-pane name="writeup" tab="题解" v-if="mode === 'training' || gameArchived || adminActive">
                <div v-if="!selectedChallenge.writeup" class="muted">
                  {{ mode === 'training' ? '暂无题解' : '题解将在归档后开放' }}
                </div>
                <Article v-else :content="writeupContent" :show-toc="true" />
              </n-tab-pane>
            </n-tabs>
          </div>
        </div>
      </template>

      <div v-else class="stage-empty">
        <span class="stage-empty-icon" aria-hidden="true">🎯</span>
        <p>从左侧选择题目开始{{ mode === 'training' ? '练习' : '挑战' }}</p>
      </div>
    </section>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, computed, watch, inject, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NTag, NInput, NButton, NTabs, NTabPane, useMessage } from 'naive-ui'
import { UiLoadingTips, UiPopover, UiButton } from '@/components/ui'
import { Article, Terminal, HammerPanel, MatrixShell } from '@/components/shared'
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
  components: { NTag, NInput, NButton, NTabs, NTabPane, UiLoadingTips, UiPopover, UiButton, Terminal, HammerPanel, Article, MatrixShell },
  props: {
    gameId: { type: [Number, String], required: true },
    mode: { type: String, default: 'competition' },
    gameTitle: { type: String, default: '' },
    gameStatus: { type: String, default: '' },
    gameArchived: { type: Boolean, default: false },
    hideGameHeader: { type: Boolean, default: false },
    backLink: { type: Object, default: null },
    embedded: { type: Boolean, default: false },
  },
  emits: ['challenge-change', 'hammer-unread'],
  setup(props, { emit }) {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()

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
      const t = selectedChallenge.value?.challenge_type
      const map = {
        0: '静态附件',
        1: '静态容器',
        2: '动态附件',
        3: '动态容器',
      }
      return map[t] ?? '静态题'
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

    const solveCount = computed(() =>
      selectedChallenge.value?.solved_count || stats.value?.unique_solvers || 0,
    )

    const currentBloodRecords = computed(() => {
      const id = selectedChallenge.value?.id
      return id ? (bloodMap.value[id] || []) : []
    })

    const descriptionContent = computed(() =>
      selectedChallenge.value?.description || selectedChallenge.value?.content || '暂无描述',
    )

    const writeupContent = computed(() => selectedChallenge.value?.writeup || '')

    const hasContainer = computed(() =>
      !!(selectedChallenge.value?.docker_image ||
        selectedChallenge.value?.challenge_type === 1 ||
        selectedChallenge.value?.challenge_type === 3),
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
        } catch { /* ignore */ }
        try {
          const detail = await axios.get(`/api/challenges/${ch.id}`, bgConfig(signal))
          if (detail.data?.data?.is_solved) solvedIds.value.add(ch.id)
        } catch { /* ignore */ }
      }))
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
        const statsPromise = adminActive.value
          ? axios.get(`/api/challenges/${ch.id}/stats`).catch(() => null)
          : Promise.resolve(null)
        const [detailRes, statsRes] = await Promise.all([detailPromise, statsPromise])
        const detail = detailRes.data?.data || detailRes.data
        if (detail) {
          selectedChallenge.value = sanitizeChallengeDetail(ch, detail)
          if (detail.is_solved) {
            challengeSolved.value = true
            solvedIds.value.add(ch.id)
          }
        }
        stats.value = adminActive.value
          ? (statsRes?.data?.data || null)
          : null

        if (hasContainer.value) await loadContainerInstance()
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
      const id = instance.value?.instance_id
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
      const id = instance.value?.instance_id
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
      const done = () => message.success('已复制连接地址')
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(url).then(done).catch(() => {
          // fallback: 选中文本提示手动 Ctrl+C
          message.info('自动复制失败，请手动选中地址后 Ctrl+C')
        })
        return
      }
      try {
        const ta = document.createElement('textarea')
        ta.value = url
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

    watch(() => props.gameId, () => {
      selectedChallenge.value = null
      beginRequestScope()
      loadChallenges().then(syncFromRoute)
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
      await loadChallenges()
      syncFromRoute()
      bloodPoll.start()
    })

    onUnmounted(() => {
      requestAbort?.abort()
      requestAbort = null
      clearRemainingTimer()
      bloodPoll.stop()
      window.removeEventListener('neepu_user_refreshed', refreshAdminState)
    })


    const shellPath = computed(() =>
      props.mode === 'training' ? `~/training/${props.gameId}` : `~/games/${props.gameId}/challenges`,
    )
    const shellCmd = computed(() => '')
    const shellPagePrompt = computed(() => {
      if (props.embedded) return ''
      return props.mode === 'training'
        ? '练习场 · TRAINING'
        : '赛事题目 · CHALLENGES'
    })
    const shellPageTitle = computed(() => {
      if (props.embedded) return ''
      return props.gameTitle || (props.mode === 'training' ? '练习场' : '赛事题目')
    })
    const shellPageDesc = computed(() => {
      if (props.embedded) return ''
      if (props.mode === 'training') return '永久开放 · 无时间限制 · 不计入正式积分'
      return props.gameStatus || '选择左侧题目开始挑战'
    })

    return {
      shellPath, shellCmd, shellPagePrompt, shellPageTitle, shellPageDesc,
      challenges, challengesLoading, challengesLoadError, selectedChallenge, searchQuery,
      challengeTree, filteredChallenges, activeTab,
      flagInput, submitting, challengeSolved, flagResult, hintItems, hintsLoading, stats, instance,
      containerLoading, queueStatus, instanceLogs, logsLoading,
      extending, destroying, containerBusy, remainingLabel,
      gameStatusType, descriptionContent, writeupContent,
      hasContainer, attachmentUrl, isAdmin, showAdminTools, adminActive,
      challengeTypeLabel, toggleAdminTools, solveCount,
      isCategoryExpanded, toggleCategory, closeChallenge,
      isSolved, bloodRecords, bloodLevelName, bloodLevelShort, currentBloodRecords,
      selectChallenge, submitFlag, startContainer, extendContainer, destroyContainer, loadChallenges,
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
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: transparent;
}

.tree-panel--matrix {
  border-top: 1px solid var(--border);
}

.tree-panel-head {
  padding: var(--panel-padding-lg, 24px) var(--panel-padding, 16px) var(--panel-padding, 16px);
  border-bottom: 1px solid var(--border);
}

.tree-back {
  display: inline-block;
  margin-bottom: 8px;
  font-size: var(--text-xs);
  color: var(--primary);
  text-decoration: none;
}

.tree-back:hover { text-decoration: underline; }

.tree-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
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

.tree-refresh {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card-bg);
  color: var(--muted);
  cursor: pointer;
  font-size: var(--text-sm);
  line-height: 1;
  transition: color 0.15s, border-color 0.15s;
}

.tree-refresh:hover:not(:disabled) {
  color: var(--primary);
  border-color: rgba(var(--primary-rgb), 0.4);
}

.tree-search {
  padding: var(--panel-padding, 16px) var(--panel-padding, 16px);
  border-bottom: 1px solid var(--border);
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

.tree-cat-count {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--muted);
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
  padding: 7px 14px 7px 32px;
  font-size: var(--text-sm);
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
  min-width: 0;
  min-height: 0;
  background: var(--gradient-card-bg, var(--card-bg));
}

.stage-admin-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 16px 0;
}

.stage-tabbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 16px 0;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.stage-home {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: var(--text-base);
  color: var(--muted);
}

.stage-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: calc(var(--layout-space, 0.25rem) * 64);
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  background: var(--hover);
  font-size: var(--text-sm);
}

.stage-tab.active {
  background: var(--card-bg);
  border-color: var(--border);
  color: var(--text);
  font-weight: 600;
}

.stage-tab-code {
  font-size: var(--text-xs);
  color: var(--primary);
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
}

.stage-tab-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stage-tab-close {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: var(--text-base);
  line-height: 1;
  padding: 0 2px;
}

.stage-tab-close:hover { color: var(--text); }

.stage-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.stage-brief {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: calc(var(--layout-space, 0.25rem) * 5);
  padding: var(--panel-padding, 16px) var(--panel-padding-lg, 24px);
  border-bottom: 1px solid var(--border);
  max-height: var(--workspace-brief-max-height, min(40vh, 320px));
  overflow-y: auto;
  flex-shrink: 0;
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

.brief-points {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--primary);
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

.stage-tools {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0 var(--panel-padding, 16px) var(--panel-padding, 16px);
}

.workspace-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.workspace-tabs :deep(.n-tabs-nav) {
  flex-shrink: 0;
}

.workspace-tabs :deep(.n-tabs-pane-wrapper),
.workspace-tabs :deep(.n-tab-pane) {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.stage-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--muted);
  font-size: var(--text-sm);
}

.stage-empty-icon { font-size: 40px; opacity: 0.85; }

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

.logs-box {
  margin: 10px 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}

.logs-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}

.logs-pre {
  margin: 0;
  max-height: 180px;
  overflow: auto;
  padding: 8px 10px;
  font-size: 11px;
  line-height: 1.45;
  font-family: var(--font-hacker, ui-monospace, monospace);
  background: var(--code-bg, rgba(0,0,0,0.04));
  white-space: pre-wrap;
  word-break: break-all;
}

.terminal-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: var(--workspace-tools-min-height, 320px);
  flex: 1;
}

.conn-box {
  padding: 10px 12px;
  background: var(--term-bg, #1A1D2E);
  color: var(--term-fg, #5ED9A8);
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
  .tree-item, .tree-refresh, .stage-tab-close { transition: none; }
}
</style>
