<template>
  <div
    class="training-layout lab-deck layout-with-sidebar"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <aside class="training-sidebar sidebar-rail">
      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/training" class="sidebar-title sidebar-rail-title">练习场列表</router-link>
          <n-tag size="small" type="success" :bordered="false">永久开放</n-tag>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">TRAINING · LAB</p>
      </div>

      <div class="sidebar-rail-nav training-nav">
        <div v-for="group in sidebarGroups" :key="group.group" class="sidebar-group">
        <div class="group-label">{{ group.group }}</div>
        <button
          v-for="item in group.items"
          :key="item.id || item.slug"
          class="sidebar-item"
          :class="{ active: isActiveItem(item) }"
          @click="selectItem(item)"
        >
          <span class="item-code">{{ itemCode(item, group.group) }}</span>
          <span class="item-title">{{ item.title }}</span>
          <span v-if="item.challenge_count != null" class="item-count">{{ item.challenge_count }}</span>
        </button>
        </div>
      </div>

      <div class="sidebar-links sidebar-rail-footer">
        <button
          v-if="selectedGame"
          type="button"
          class="sidebar-link"
          @click="showGameInfo = true"
        >
          <span class="link-code">INF</span>
          <span>{{ infoLinkLabel }}</span>
        </button>
        <router-link to="/training" class="sidebar-link">
          <span class="link-code">BAK</span>
          <span>返回列表</span>
        </router-link>
        <router-link to="/games" class="sidebar-link">
          <span class="link-code">CTF</span>
          <span>查看赛事</span>
        </router-link>
      </div>
      <div class="sidebar-rail-footer sidebar-footer sidebar-footer-copy-wrap">
        <div class="sidebar-footer-copy">
          © 2022-2026
          <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">东北电力大学</a>
        </div>
      </div>

    </aside>

    <button
      type="button"
      class="sidebar-collapse-trigger"
      :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
      @click="toggleSidebar"
    >
      <span class="chevron" :class="{ 'is-collapsed': collapsed }">‹</span>
    </button>

    <main class="training-main sidebar-main" :class="{ 'training-main--game': !!selectedGame }">
      <div v-if="!selectedGame" class="welcome-panel">
        <div v-if="showCreateForm" class="create-form-panel matrix-panel">
          <header class="matrix-page-head">
            <h2 class="matrix-page-title">创建练习场</h2>
            <p class="matrix-page-desc">管理员可新建永久开放的训练靶场</p>
          </header>
          <n-form label-placement="top" class="create-form">
            <n-form-item label="练习场名称">
              <n-input v-model:value="createForm.title" placeholder="如：Web 安全审计" />
            </n-form-item>
            <n-form-item label="简介">
              <n-input v-model:value="createForm.description" type="textarea" placeholder="练习场说明（可选）" :rows="3" />
            </n-form-item>
            <div class="create-actions">
              <n-button type="primary" :loading="creating" @click="createPlayground">创建</n-button>
              <n-button @click="showCreateForm = false">取消</n-button>
            </div>
          </n-form>
        </div>
        <template v-else>
          <header class="matrix-page-head r2s-training-empty">
            <h2 class="matrix-page-title text-section">开始今日份的训练！</h2>
            <p class="matrix-page-desc text-muted">练习场永久开放，提交不计入正式赛积分与血榜；容器环境与正式赛相同，适合赛前热身与复盘。</p>
          </header>

          <LoadingTips v-if="loading" />

          <div v-else-if="trainingGames.length" class="game-quick-list">
            <article
              v-for="g in trainingGames"
              :key="g.id"
              class="quick-card"
              @click="openGame(g)"
            >
              <div class="quick-head">
                <span class="quick-code">{{ itemCode(g, '训练') }}</span>
                <span class="quick-meta">{{ g.challenge_count || 0 }} 题</span>
              </div>
              <div class="quick-title">{{ g.title }}</div>
              <span class="quick-link">进入练习 →</span>
            </article>
          </div>

          <div v-else class="empty-panel">
            <p>{{ loadError ? '加载失败，请刷新重试' : '暂无练习场' }}</p>
            <p v-if="!loadError" class="muted">管理员可创建练习场，或运行 <code>python backend/init_ctf.py</code> 初始化示例数据</p>
            <div class="empty-actions">
              <router-link to="/games">查看赛事</router-link>
              <router-link to="/wiki">查看 Wiki</router-link>
            </div>
          </div>

          <button
            v-if="isHost"
            type="button"
            class="create-lab-btn"
            @click="showCreateForm = true"
          >
            <span class="link-code">NEW</span>
            <span>创建练习场</span>
            <span class="row-arrow">→</span>
          </button>
        </template>
      </div>

      <template v-else>
        <section v-if="showTrainingWelcome" class="training-welcome-banner">
          <div class="welcome-md markdown-body" v-html="welcomeHtml"></div>
          <button class="welcome-close" type="button" @click="showTrainingWelcome = false" aria-label="关闭">×</button>
        </section>

        <ChallengeWorkspace
          :game-id="selectedGame.id"
          mode="training"
          :game-title="selectedGame.title"
          embedded
        />
      </template>
    </main>

    <n-modal v-model:show="showGameInfo" preset="card" title="练习场说明" style="max-width: 560px">
      <div class="welcome-md markdown-body" v-html="welcomeHtml"></div>
    </n-modal>
  </div>
</template>

<script>
import { ref, inject, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NTag, NModal, NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import ChallengeWorkspace from './ChallengeWorkspace.vue'
import LoadingTips from './LoadingTips.vue'
import { fetchPlatformInfo } from '../services/platform'
import { isLoggedIn, isAdmin as checkIsAdmin, hasSession } from '../services/auth'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'

export default {
  name: 'Training',
  components: { NTag, NModal, NForm, NFormItem, NInput, NButton, ChallengeWorkspace, LoadingTips },
  setup() {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_training_sidebar_collapsed')

    const loading = ref(false)
    const trainingGames = ref([])
    const loadError = ref(false)
    const archivedGames = ref([])
    const selectedGame = ref(null)
    const showGameInfo = ref(false)
    const showTrainingWelcome = ref(true)
    const showCreateForm = ref(false)
    const isHost = ref(false)
    const creating = ref(false)
    const createForm = ref({ title: '', description: '' })
    const trainingWelcome = ref('')
    const sidebarGroups = ref([
      { group: '训练', items: [] },
      { group: '归档赛事', items: [] },
    ])

    function isActiveItem(item) {
      return item.id && selectedGame.value?.id === item.id
    }

    function normalizeSidebarGroups(groups) {
      return (groups || []).map(g => ({
        ...g,
        group: g.group === '归档赛事' ? '赛事' : g.group,
      }))
    }

    function itemCode(item, group) {
      const title = (item?.title || '').toLowerCase()
      if (title.includes('工控') || title.includes('ics')) return 'ICS'
      if (title.includes('web')) return 'WEB'
      if (title.includes('密码') || title.includes('crypto')) return 'CRY'
      if (title.includes('杂项') || title.includes('misc')) return 'MSC'
      if (title.includes('二进制') || title.includes('pwn')) return 'PWN'
      if (title.includes('逆向') || title.includes('reverse')) return 'REV'
      if (group === '赛事' || group === '归档赛事') return 'ARC'
      return 'TRN'
    }

    async function loadTrainingGames() {
      loading.value = true
      loadError.value = false
      try {
        const sidebarRes = await axios.get('/api/platform/training/sidebar')
        const body = sidebarRes.data || {}
        let training = Array.isArray(body.training) ? body.training : []
        let archived = Array.isArray(body.archived) ? body.archived : []

        // 若 sidebar 接口未返回训练数据，则回退到竞赛 API
        if (!training.length && !archived.length) {
          const [trainRes, archRes] = await Promise.all([
            axios.get('/api/competitions/', { params: { game_type: 'training' } }),
            axios.get('/api/competitions/', { params: { game_type: 'archived' } }),
          ])
          training = trainRes.data?.data || []
          archived = archRes.data?.data || []
        }

        trainingGames.value = training
        archivedGames.value = archived

        const sidebar = Array.isArray(body.sidebar) ? body.sidebar : []
        const hasDbItems = sidebar.some(g =>
          (g.items || []).some(it => it.id),
        )

        if (hasDbItems) {
          sidebarGroups.value = normalizeSidebarGroups(sidebar)
        } else {
          sidebarGroups.value = normalizeSidebarGroups([
            {
              group: '训练',
              items: training.map(g => ({
                id: g.id,
                title: g.title,
                challenge_count: g.challenge_count,
              })),
            },
            {
              group: '赛事',
              items: archived.map(g => ({
                id: g.id,
                title: g.title,
                challenge_count: g.challenge_count,
              })),
            },
          ])
        }
      } catch (e) {
        console.error('加载练习场失败', e)
        trainingGames.value = []
        archivedGames.value = []
        loadError.value = true
      } finally {
        loading.value = false
      }
    }

    async function ensureTrainingJoin(gameId) {
      if (!(await hasSession())) {
        message.warning('请先登录后再进入练习场')
        router.push({ name: 'Auth', query: { redirect: route.fullPath } })
        return false
      }
      try {
        await axios.post(`/api/competitions/${gameId}/training-join`)
        return true
      } catch (e) {
        message.error(e.response?.data?.msg || '进入练习场失败')
        return false
      }
    }

    async function openGame(game) {
      const ok = await ensureTrainingJoin(game.id)
      if (!ok) return
      selectedGame.value = game
      showTrainingWelcome.value = true
      router.replace({ name: 'TrainingGame', params: { gameId: game.id } })
    }

    async function createPlayground() {
      if (!createForm.value.title?.trim()) {
        message.warning('请填写练习场名称')
        return
      }
      creating.value = true
      try {
        const now = new Date()
        const end = new Date(now.getTime() + 3650 * 24 * 3600 * 1000)
        const { data } = await axios.post('/api/competitions/admin/create', {
          title: createForm.value.title.trim(),
          description: createForm.value.description,
          start_time: now.toISOString(),
          end_time: end.toISOString(),
          game_type: 'training',
          is_public: true,
        })
        const game = data?.data
        message.success('练习场创建成功')
        showCreateForm.value = false
        createForm.value = { title: '', description: '' }
        await loadTrainingGames()
        if (game?.id) await openGame(game)
      } catch (e) {
        message.error(e.response?.data?.msg || '创建失败')
      } finally {
        creating.value = false
      }
    }

    function selectItem(item) {
      if (!item.id) return
      const game = [...trainingGames.value, ...archivedGames.value].find(g => g.id === item.id)
      if (game) openGame(game)
    }

    const isArchivedGame = computed(() =>
      selectedGame.value && archivedGames.value.some(g => g.id === selectedGame.value.id),
    )

    const infoLinkLabel = computed(() =>
      isArchivedGame.value ? '查看归档信息' : '查看练习场信息',
    )

    const welcomeHtml = computed(() => {
      const archiveNote = isArchivedGame.value
        ? '\n\n> 本题为**归档赛事**题目，内容已从正式比赛迁移至练习场，仅供学习复盘。'
        : ''
      const raw = trainingWelcome.value || (
        '## 欢迎来到练习场！\n\n'
        + '- 无时间限制、无限重试、不计分\n'
        + '- 提示自动解锁、题解已开放\n'
        + '- 禁止直接抄题，请独立思考\n'
        + '- 🔨 锤子反馈在训练场不可用\n\n'
        + 'TCP 类题目请使用 netcat 连接，更多环境配置请参阅题目说明与部署文档。'
      )
      try { return parseMarkdownSafe(raw + archiveNote) } catch { return '' }
    })

    watch(() => route.params.gameId, async (id) => {
      if (!id) {
        selectedGame.value = null
        return
      }
      const gameId = parseInt(id, 10)
      if (!selectedGame.value || selectedGame.value.id !== gameId) {
        const game = [...trainingGames.value, ...archivedGames.value].find(g => g.id === gameId)
        if (game) {
          const ok = await ensureTrainingJoin(game.id)
          if (ok) selectedGame.value = game
        }
      }
    })

    onMounted(async () => {
      isHost.value = checkIsAdmin()

      if (route.query.create === 'true' && isHost.value) {
        showCreateForm.value = true
      }

      const info = await fetchPlatformInfo()
      trainingWelcome.value = info.training_welcome || ''

      await loadTrainingGames()
      const gameId = route.params.gameId
      if (gameId) {
        const game = [...trainingGames.value, ...archivedGames.value].find(
          g => g.id === parseInt(gameId, 10),
        )
        if (game) await openGame(game)
      }
    })

    return {
      loading, loadError, trainingGames, sidebarGroups, selectedGame, showGameInfo,
      showTrainingWelcome, showCreateForm, isHost, creating, createForm,
      welcomeHtml, infoLinkLabel, isArchivedGame, itemCode,
      isActiveItem, selectItem, openGame, createPlayground,
      collapsed, toggleSidebar,
    }
  },
}
</script>

<style scoped>
.training-layout {
  min-height: calc(100vh - var(--nav-height, 56px) - 52px);
}
.sidebar-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.sidebar-title {
  font-weight: 700;
  color: var(--primary);
  text-decoration: none;
  font-size: 1rem;
}
.group-label {
  font-size: 11px;
  color: var(--muted);
  margin: 12px 0 6px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.sidebar-item {
  width: 100%;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.sidebar-item:hover,
.sidebar-item.active {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}
.sidebar-item:hover .item-code,
.sidebar-item.active .item-code {
  color: var(--primary);
}
.item-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--accent);
}
.item-title {
  font-size: 13px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-count {
  font-size: 11px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.sidebar-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sidebar-link {
  color: var(--muted);
  font-size: 13px;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.sidebar-link:hover {
  background: var(--hover);
  border-color: var(--border);
  color: var(--text);
}
.sidebar-link:hover .link-code {
  color: var(--primary);
}
.link-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--accent);
}

.training-main {
  overflow: auto;
}


.game-quick-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--card-grid-min-golden, 324px), 1fr));
  gap: var(--fib-21);
  margin-bottom: var(--fib-21);
}
.quick-card {
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--card-radius);
  border-left: 3px solid var(--primary);
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--gradient-card-shadow, var(--shadow-lg));
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}
.quick-card:hover {
  border-color: rgba(var(--primary-rgb), 0.5);
  box-shadow: var(--gradient-card-shadow-hover, var(--shadow-lg));
  transform: translateY(-2px);
}
.quick-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.quick-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--accent);
}
.quick-title { font-weight: 600; color: var(--text); font-size: 0.95rem; }
.quick-meta { font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
.quick-link { display: inline-block; margin-top: 10px; font-size: 12px; color: var(--primary); }

.empty-panel {
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--card-radius);
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--gradient-card-shadow, var(--shadow-lg));
  margin-bottom: 20px;
}
.empty-panel p { margin: 0 0 6px; color: var(--text); }
.empty-panel code {
  font-size: 11px;
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: var(--card-radius);
}
.empty-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}
.empty-actions a {
  padding: 8px 14px;
  font-size: 12px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  color: var(--primary);
  text-decoration: none;
}
.empty-actions a:hover { background: var(--hover); }

.training-welcome-banner {
  position: relative;
  margin-bottom: 20px;
  padding: 16px 20px;
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--card-radius);
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--gradient-card-shadow, var(--shadow-lg));
}
.training-welcome-banner .welcome-close {
  position: absolute;
  top: 8px;
  right: 12px;
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--muted);
  line-height: 1;
}
.welcome-md :deep(p) { margin: 0 0 8px; line-height: 1.7; }
.welcome-md :deep(ul) { padding-left: 20px; line-height: 1.8; margin: 8px 0; }
.welcome-md ul { padding-left: 20px; line-height: 1.8; }
.muted { color: var(--muted); font-size: 13px; }
.create-form-panel {
  max-width: 560px;
}
.create-form-panel .matrix-page-head {
  margin-bottom: 16px;
  padding-bottom: 12px;
}
.create-actions { display: flex; gap: 8px; margin-top: 8px; }
.create-lab-btn {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 320px;
  margin-top: 4px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.create-lab-btn:hover {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}
.create-lab-btn:hover .link-code {
  color: var(--primary);
}
.row-arrow {
  font-size: 12px;
  color: var(--muted);
}
</style>
