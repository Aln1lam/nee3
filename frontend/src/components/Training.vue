<template>
  <div
    class="training-layout lab-deck layout-with-sidebar"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <aside class="training-sidebar sidebar-rail">
      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/training" class="sidebar-title sidebar-rail-title">训练中心</router-link>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">TRAINING · HUB</p>
      </div>

      <div class="sidebar-rail-nav training-nav">
        <div v-for="group in sidebarGroups" :key="group.group" class="sidebar-group">
          <div class="group-label">{{ group.group }}</div>
          <button
            v-for="item in group.items"
            :key="item.id || item.slug"
            type="button"
            class="sidebar-item"
            @click="enterGame(item)"
          >
            <span class="link-code chip-cut item-chip">{{ sidebarChip(group.group) }}</span>
            <span class="item-title">{{ item.title }}</span>
          </button>
        </div>
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

    <main class="training-main sidebar-main">
      <div class="welcome-panel">
          <header class="matrix-page-head">
            <h2 class="matrix-page-title text-section">开始今日份的训练！</h2>
            <p class="matrix-page-desc text-muted">
              点击卡片或左侧条目将整页进入做题大厅；提交不计入正式赛积分与血榜。
            </p>
          </header>

          <LoadingTips v-if="loading" />

          <template v-else-if="trainingGames.length || archivedGames.length">
            <section v-if="trainingGames.length" class="hub-section">
              <h3 class="hub-section-title">
                <span class="link-code chip-cut">TRN</span>
                训练板块
              </h3>
              <div class="training-grid">
                <article
                  v-for="g in trainingGames"
                  :key="'trn-' + g.id"
                  class="quick-card training-card"
                  @click="enterGame(g)"
                >
                  <div class="quick-head">
                    <span class="quick-code link-code chip-cut">{{ itemCode(g, '训练板块') }}</span>
                  </div>
                  <div class="quick-title">{{ g.title }}</div>
                  <p class="quick-desc">{{ (g.description || '永久开放训练靶场 · 容器环境与正式赛相同').slice(0, 72) }}</p>
                  <span class="quick-link">进入练习 →</span>
                </article>
              </div>
            </section>

            <section v-if="archivedGames.length" class="hub-section">
              <h3 class="hub-section-title">
                <span class="link-code chip-cut">ARC</span>
                赛事归档板块
              </h3>
              <div class="training-grid">
                <article
                  v-for="g in archivedGames"
                  :key="'arc-' + g.id"
                  class="quick-card training-card training-card--archive"
                  @click="enterGame(g)"
                >
                  <div class="quick-head">
                    <span class="quick-code link-code chip-cut">ARC</span>
                  </div>
                  <div class="quick-title">{{ g.title }}</div>
                  <p class="quick-desc">{{ (g.description || '已归档赛事 · 供复盘练习').slice(0, 72) }}</p>
                  <span class="quick-link">进入复盘 →</span>
                </article>
              </div>
            </section>
          </template>

          <div v-else class="empty-panel">
            <p>{{ loadError ? '加载失败，请刷新重试' : '暂无练习场' }}</p>
            <p v-if="!loadError" class="muted">练习场由管理员在后台维护，请稍后再来</p>
            <div class="empty-actions">
              <router-link to="/contests">查看赛事</router-link>
              <router-link to="/wiki">查看 Wiki</router-link>
            </div>
          </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, inject, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import LoadingTips from './LoadingTips.vue'
import { fetchPlatformInfo, clearPlatformCache } from '../services/platform'
import { isAdmin as checkIsAdmin, hasSession } from '../services/auth'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'

export default {
  name: 'Training',
  components: { NForm, NFormItem, NInput, NButton, LoadingTips },
  setup() {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_training_sidebar_collapsed')

    const loading = ref(false)
    const trainingGames = ref([])
    const archivedGames = ref([])
    const loadError = ref(false)
    const showCreateForm = ref(false)
    const isHost = ref(false)
    const creating = ref(false)
    const createForm = ref({ title: '', description: '' })
    const trainingWelcome = ref('')
    const sidebarGroups = ref([
      { group: '训练板块', items: [] },
      { group: '赛事归档板块', items: [] },
    ])

    const trainingWelcomeHtml = computed(() => {
      if (!trainingWelcome.value) return ''
      try { return parseMarkdownSafe(trainingWelcome.value) } catch { return '' }
    })

    function normalizeGroupName(name) {
      const n = String(name || '')
      if (n.includes('归档') || n === '赛事' || n === 'ARC') return '赛事归档板块'
      if (n.includes('训练') || n === 'TRN') return '训练板块'
      return n || '训练板块'
    }

    function itemCode(item, group) {
      const title = (item?.title || '').toLowerCase()
      const g = normalizeGroupName(group)
      if (g === '赛事归档板块') return 'ARC'
      if (title.includes('工控') || title.includes('ics')) return 'ICS'
      if (title.includes('web')) return 'WEB'
      if (title.includes('密码') || title.includes('crypto')) return 'CRY'
      if (title.includes('杂项') || title.includes('misc')) return 'MSC'
      if (title.includes('二进制') || title.includes('pwn')) return 'PWN'
      if (title.includes('逆向') || title.includes('reverse')) return 'REV'
      return 'TRN'
    }

    /** 侧栏微型 Chip：训练 TRN / 归档 ARC（与右侧板块标签对齐） */
    function sidebarChip(group) {
      return normalizeGroupName(group) === '赛事归档板块' ? 'ARC' : 'TRN'
    }

    async function loadTrainingGames() {
      loading.value = true
      loadError.value = false
      try {
        const sidebarRes = await axios.get('/api/platform/training/sidebar')
        const body = sidebarRes.data || {}
        let training = Array.isArray(body.training) ? body.training : []
        let archived = Array.isArray(body.archived) ? body.archived : []

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
        const hasDbItems = sidebar.some(g => (g.items || []).some(it => it.id))

        if (hasDbItems) {
          sidebarGroups.value = sidebar.map(g => ({
            group: normalizeGroupName(g.group),
            items: (g.items || []).map(it => ({ id: it.id, title: it.title })),
          }))
        } else {
          sidebarGroups.value = [
            {
              group: '训练板块',
              items: training.map(g => ({ id: g.id, title: g.title })),
            },
            {
              group: '赛事归档板块',
              items: archived.map(g => ({ id: g.id, title: g.title })),
            },
          ]
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
        router.push({ name: 'Auth', query: { redirect: `/training/challenge/${gameId}` } })
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

    /** 整页跳转到独立做题大厅，禁止右侧内嵌 */
    async function enterGame(gameOrItem) {
      const id = gameOrItem?.id
      if (!id) return
      const ok = await ensureTrainingJoin(id)
      if (!ok) return
      router.push({ path: `/training/challenge/${id}` })
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
        if (game?.id) await enterGame(game)
      } catch (e) {
        message.error(e.response?.data?.msg || '创建失败')
      } finally {
        creating.value = false
      }
    }

    async function loadTrainingWelcome() {
      try {
        clearPlatformCache()
        const info = await fetchPlatformInfo({ force: true })
        trainingWelcome.value = info.training_welcome || info.training_welcome_banner || ''
      } catch {
        trainingWelcome.value = ''
      }
    }

    function onPlatformUpdated(e) {
      const info = e?.detail
      if (info && (info.training_welcome || info.training_welcome_banner)) {
        trainingWelcome.value = info.training_welcome || info.training_welcome_banner || ''
      } else {
        loadTrainingWelcome()
      }
    }

    onMounted(async () => {
      isHost.value = checkIsAdmin()
      await loadTrainingWelcome()
      window.addEventListener('neepu_platform_updated', onPlatformUpdated)
      await loadTrainingGames()
    })

    onUnmounted(() => {
      window.removeEventListener('neepu_platform_updated', onPlatformUpdated)
    })

    return {
      loading, loadError, trainingGames, archivedGames, sidebarGroups,
      showCreateForm, isHost, creating, createForm,
      trainingWelcomeHtml, itemCode, sidebarChip, enterGame, createPlayground,
      collapsed, toggleSidebar,
    }
  },
}
</script>

<style scoped>
.training-layout {
  width: 100%;
  height: calc(100vh - var(--nav-height, 72px));
  max-height: calc(100vh - var(--nav-height, 72px));
  overflow: hidden;
}
.sidebar-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.sidebar-title {
  font-weight: 600;
  color: #ffffff;
  text-decoration: none;
  font-size: 16px;
}
.group-label {
  font-size: 12px;
  font-weight: 500;
  color: #9ca3af;
  margin: 0 0 12px;
  text-transform: none;
  letter-spacing: 0.04em;
}
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.sidebar-item:hover {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}
.sidebar-item:hover .item-chip {
  background: rgba(94, 217, 168, 0.18);
  border-color: rgba(94, 217, 168, 0.45);
}
.item-chip {
  flex-shrink: 0;
  height: 18px !important;
  min-height: 18px !important;
  max-height: 18px !important;
  padding: 0 5px !important;
  font-size: 9px !important;
  letter-spacing: 0.06em;
  border: 1px solid rgba(94, 217, 168, 0.28) !important;
  background: rgba(94, 217, 168, 0.1) !important;
  color: #5ED9A8 !important;
  border-radius: 3px !important;
}
.item-title {
  flex: 1 1 auto;
  font-size: 13px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}
.link-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #5ED9A8;
  background: rgba(94, 217, 168, 0.1);
  border: 1px solid rgba(94, 217, 168, 0.25);
}

.training-main {
  overflow: auto;
  min-height: 0;
  width: 100%;
  scrollbar-width: none;
}
.training-main::-webkit-scrollbar { display: none; width: 0; height: 0; }

.welcome-panel {
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  padding-bottom: 24px;
}

.hub-section { margin-bottom: 28px; }
.hub-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  font-family: var(--font-ui);
}

.training-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fill, minmax(324px, 1fr)) !important;
  gap: 20px !important;
  padding: 0 0 8px;
  width: 100%;
  box-sizing: border-box;
}
.quick-card.training-card {
  aspect-ratio: auto !important;
  min-height: 148px !important;
  padding: 16px 18px !important;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: var(--card-radius);
  border-left: 3px solid var(--primary);
  background: var(--card-bg);
  box-shadow: none;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, transform 0.2s;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.training-card--archive {
  border-left-color: rgba(126, 184, 255, 0.75);
}
.training-grid .quick-card:hover {
  border-color: rgba(var(--primary-rgb), 0.45);
  background: rgba(var(--primary-rgb), 0.06);
  transform: translateY(-2px);
}
.quick-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.quick-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.quick-title {
  font-size: 16px;
  font-weight: 650;
  color: var(--text);
  margin-bottom: 8px;
  line-height: 1.35;
}
.quick-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.55;
  flex: 1;
}
.quick-link {
  font-size: 12px;
  color: #5ED9A8;
  font-weight: 600;
}

.empty-panel {
  padding: 40px 18px;
  text-align: center;
  color: var(--muted);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
.empty-panel p { margin: 0 0 6px; }
.empty-panel code {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: #5ED9A8;
}
.empty-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 14px;
}
.empty-actions a {
  color: #5ED9A8;
  text-decoration: none;
  font-size: 13px;
}
.empty-actions a:hover { text-decoration: underline; }

.create-actions { display: flex; gap: 8px; margin-top: 8px; }
.create-lab-btn {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 320px;
  margin-top: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  cursor: pointer;
}
.create-lab-btn:hover {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}
.row-arrow { font-size: 12px; color: var(--muted); }
</style>
