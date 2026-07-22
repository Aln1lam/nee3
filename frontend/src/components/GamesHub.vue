<template>
  <div class="games-hub r2s-games layout-with-sidebar lab-deck" style="--sidebar-width: 248px">
    <div class="r2s-games__stage">
      <aside class="r2s-games__list-pane sidebar-rail">
        <div v-if="canCreateGame" class="sidebar-actions">
          <button type="button" class="btn btn-md btn-primary" @click="openCreate">创建赛事</button>
        </div>
        <n-spin :show="loading">
          <div class="r2s-games__list">
            <button
              v-for="g in featuredGames"
              :key="g.id"
              type="button"
              class="r2s-games__list-btn"
              :class="{ 'is-active': selected?.id === g.id }"
              @click="selectGame(g)"
            >
              <span class="link-code">CTF</span>
              <span class="r2s-games__list-title">{{ g.title }}</span>
              <span class="dot" :class="getGameStatusDotClass(g)" aria-hidden="true" />
            </button>
            <div v-if="!featuredGames.length && !loading" class="empty-side">
              <p>{{ loadError ? '加载失败，请刷新重试' : '暂无正式赛事' }}</p>
            </div>
          </div>
        </n-spin>
        <n-pagination
          v-if="totalPages > 1"
          v-model:page="keyPage"
          :page-count="totalPages"
          size="small"
          class="side-pagination"
        />
      <div class="sidebar-rail-footer sidebar-footer sidebar-footer-copy-wrap">
        <div class="sidebar-footer-copy">
          © 2022-2026
          <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">东北电力大学</a>
        </div>
      </div>
      </aside>

      <main class="r2s-games__cover sidebar-main games-main">
        <div v-if="detailLoading && !selectedDetail" class="poster-loading">
          <UiLoadingTips />
        </div>
        <section
          v-else-if="selectedDetail"
          class="games-hero-banner"
          :class="{ 'is-live': statusVariant === 'success' }"
          @click="openGameDetail(selectedDetail)"
        >
          <div class="games-hero-copy">
            <div class="games-hero-eyebrow">
              <span class="link-code chip-cut">EVT</span>
              <span class="games-hero-tag">FEATURED</span>
              <span class="games-hero-status chip-cut" :class="'is-' + (statusVariant === 'success' ? 'live' : statusVariant === 'warning' ? 'soon' : 'ended')">
                [{{ statusVariant === 'success' ? 'LIVE' : statusVariant === 'warning' ? 'SOON' : 'END' }}] {{ statusLabel }}
              </span>
            </div>
            <h2 class="games-hero-title">{{ selectedDetail.title }}</h2>
            <p class="games-hero-sub">{{ gameSubtitle }}</p>
            <p class="games-hero-time">{{ timeRange }}</p>
            <button type="button" class="games-hero-cta chip-cut" @click.stop="openGameDetail(selectedDetail)">
              立即参赛 <kbd>↵</kbd>
            </button>
          </div>
          <div class="games-hero-deco" aria-hidden="true"></div>
        </section>
        <div v-else class="poster-empty">
          <h2>选择左侧赛事查看详情</h2>
        </div>

        <div class="games-bottom golden-dual-column">
          <section class="games-panel">
            <div class="games-panel-head">
              <span class="link-code chip-cut">LST</span>
              <span>赛事列表</span>
            </div>
            <ul class="games-feed">
              <li
                v-for="g in featuredGames"
                :key="'feed-' + g.id"
                class="games-feed-item"
                :class="{ active: selected?.id === g.id }"
                @click="selectGame(g)"
              >
                <span class="link-code chip-cut">CTF</span>
                <span class="games-feed-title">{{ g.title }}</span>
                <UiTag :variant="getGameStatusVariant(g)" size="small">{{ getGameStatusLabel(g) }}</UiTag>
              </li>
            </ul>
          </section>
          <section class="games-panel">
            <div class="games-panel-head">
              <span class="link-code chip-cut">RNK</span>
              <span>其他 / 托管</span>
            </div>
            <ul v-if="otherGamesAll.length" class="games-feed">
              <li
                v-for="g in otherGamesPage"
                :key="'oth-' + g.id"
                class="games-feed-item"
                @click="selectGame(g)"
              >
                <span class="games-feed-title">{{ g.title }}</span>
                <UiTag :variant="getGameStatusVariant(g)" size="small">{{ getGameStatusLabel(g) }}</UiTag>
              </li>
            </ul>
            <p v-else class="games-panel-empty">暂无托管赛事</p>
            <n-pagination
              v-if="otherTotalPages > 1"
              v-model:page="otherPage"
              :page-count="otherTotalPages"
              size="small"
              class="other-pagination"
            />
          </section>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NSpin, NPagination } from 'naive-ui'
import { UiTag, UiLoadingTips } from '@/components/ui'
import { unwrapList } from '../utils/unwrap'
import { getUser, hasSession } from '../services/auth'
import { resolveUploadUrl } from '../utils/uploadUrl'
import { filterPublicGames } from '../utils/gameFilters'
import {
  getGameEmoji,
  getGameCoverTheme,
  getGameStatusLabel,
  getGameStatusVariant,
  getGameStatusDotClass,
  formatGameTimeRange,
  getGamePosterPath,
  getGameSubtitle,
} from '../utils/gameDisplay'

const PAGE_SIZE = 8
const OTHER_PAGE_SIZE = 8

export default {
  name: 'GamesHub',
  components: { NSpin, NPagination, UiTag, UiLoadingTips },
  setup() {
    const axios = inject('axios')
    const router = useRouter()
    const route = useRoute()

    const loading = ref(false)
    const loadError = ref(false)
    const detailLoading = ref(false)
    const games = ref([])
    const selected = ref(null)
    const selectedDetail = ref(null)
    const posterBroken = ref(false)
    const canCreateGame = ref(false)
    const keyPage = ref(1)
    const otherPage = ref(1)

    function isHosted(g) {
      return g?.is_hosted || (g?.title || '').includes('托管')
    }

    const featuredPool = computed(() => {
      const primary = games.value.filter(g => !isHosted(g))
      return primary.length ? primary : games.value
    })

    const totalPages = computed(() => Math.max(1, Math.ceil(featuredPool.value.length / PAGE_SIZE)))

    const featuredGames = computed(() => {
      const start = (keyPage.value - 1) * PAGE_SIZE
      return featuredPool.value.slice(start, start + PAGE_SIZE)
    })

    const otherGamesAll = computed(() => {
      const hosted = games.value.filter(g => isHosted(g))
      if (hosted.length) return hosted
      return []
    })

    const otherTotalPages = computed(() =>
      Math.max(1, Math.ceil(otherGamesAll.value.length / OTHER_PAGE_SIZE)),
    )

    const otherGamesPage = computed(() => {
      const start = (otherPage.value - 1) * OTHER_PAGE_SIZE
      return otherGamesAll.value.slice(start, start + OTHER_PAGE_SIZE)
    })

    const coverTheme = computed(() => getGameCoverTheme(selectedDetail.value))
    const statusLabel = computed(() => getGameStatusLabel(selectedDetail.value))
    const statusVariant = computed(() => getGameStatusVariant(selectedDetail.value))
    const gameSubtitle = computed(() => getGameSubtitle(selectedDetail.value))
    const timeRange = computed(() => formatGameTimeRange(selectedDetail.value))

    const posterUrl = computed(() => {
      const path = getGamePosterPath(selectedDetail.value)
      return path ? resolveUploadUrl(path, selectedDetail.value?.id) : ''
    })

    async function loadGameDetail(id) {
      if (!id) {
        selectedDetail.value = null
        return
      }
      detailLoading.value = true
      try {
        const { data } = await axios.get(`/api/competitions/${id}`)
        selectedDetail.value = data?.data || data || selected.value
        posterBroken.value = false
      } catch {
        selectedDetail.value = selected.value
        posterBroken.value = false
      } finally {
        detailLoading.value = false
      }
    }

    function selectGame(g) {
      selected.value = g
      posterBroken.value = false
      const idx = featuredPool.value.findIndex(x => x.id === g.id)
      if (idx >= 0) keyPage.value = Math.floor(idx / PAGE_SIZE) + 1
      router.replace({ query: { selected: g.id, 'key-page': keyPage.value } })
      loadGameDetail(g.id)
    }

    function openGameDetail(g) {
      router.push(`/games/${g.id}`)
    }

    function openCreate() {
      router.push({ path: '/admin/ctf', query: { create: 'true' } })
    }

    async function loadGames() {
      loading.value = true
      loadError.value = false
      try {
        const { data } = await axios.get('/api/competitions/', { params: { exclude_training: true } })
        games.value = filterPublicGames(unwrapList(data))
        const params = route.query
        if (params['key-page']) keyPage.value = parseInt(params['key-page'], 10) || 1
        const sel = params.selected
        if (sel) {
          const g = games.value.find(x => x.id === parseInt(sel, 10))
          if (g) {
            selected.value = g
            await loadGameDetail(g.id)
          }
        } else if (games.value.length) {
          selected.value = games.value[0]
          await loadGameDetail(games.value[0].id)
        }
      } catch (e) {
        console.error(e)
        loadError.value = true
      } finally {
        loading.value = false
      }
    }

    async function loadHostFlag() {
      if (!(await hasSession())) return
      const user = getUser() || {}
      canCreateGame.value = !!user.is_admin
    }

    watch(keyPage, (p) => {
      if (String(route.query['key-page'] || '') === String(p)) return
      router.replace({ query: { ...route.query, 'key-page': p } })
    })

    onMounted(async () => {
      if (route.query.create === 'true') {
        await loadHostFlag()
        if (canCreateGame.value) openCreate()
      } else {
        loadHostFlag()
      }
      await loadGames()
    })

    return {
      loading, loadError, detailLoading, selected, selectedDetail, posterBroken,
      featuredGames, otherGamesAll, otherGamesPage, otherTotalPages, featuredPool,
      canCreateGame, keyPage, otherPage, totalPages,
      coverTheme, statusLabel, statusVariant, gameSubtitle, timeRange, posterUrl,
      getGameEmoji, getGameStatusLabel, getGameStatusVariant, getGameStatusDotClass,
      selectGame, openGameDetail, openCreate,
    }
  },
}
</script>

<style scoped>
.games-hub.r2s-games {
  height: calc(100vh - var(--nav-height, 72px));
  max-height: calc(100vh - var(--nav-height, 72px));
  overflow: hidden;
  width: 100%;
  display: block;
  padding: 0;
  box-sizing: border-box;
}
.r2s-games__stage {
  display: grid;
  grid-template-columns: 248px minmax(0, 1fr);
  gap: 0;
  height: 100%;
  min-height: 0;
  align-items: stretch;
}
.r2s-games__list-pane {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.empty-side {
  padding: 24px 14px;
  color: var(--muted);
  font-size: 14px;
  text-align: center;
}
.side-pagination,
.other-pagination {
  margin-top: 12px;
  justify-content: center;
}
.games-main {
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: auto;
  padding: 16px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-sizing: border-box;
}
.poster-loading,
.poster-empty {
  width: 100%;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
}
.poster-empty h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}
.r2s-games__list-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100% !important;
}
.r2s-games__list-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}

/* Home 同款 Hero Banner — 废除白灰浮动盒 */
.games-hero-banner {
  position: relative;
  overflow: hidden;
  width: 100%;
  min-height: 148px;
  max-height: 180px;
  padding: 16px 20px;
  border-radius: var(--card-radius);
  border: 1px solid rgba(var(--primary-rgb), 0.22);
  background: linear-gradient(135deg, rgba(35, 40, 56, 0.75) 0%, rgba(20, 24, 35, 0.92) 100%);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  display: grid;
  grid-template-columns: 1.618fr 1fr;
  align-items: center;
  box-sizing: border-box;
  flex-shrink: 0;
}
.games-hero-banner::before {
  content: '';
  position: absolute;
  top: -50px;
  left: -50px;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(var(--primary-rgb), 0.12) 0%, transparent 70%);
  pointer-events: none;
}
.games-hero-banner.is-live {
  border-color: rgba(var(--primary-rgb), 0.35);
}
.games-hero-copy { position: relative; z-index: 1; min-width: 0; }
.games-hero-eyebrow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.games-hero-tag {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: rgba(226, 232, 240, 0.55);
  font-family: var(--font-mono);
}
.games-hero-status {
  display: inline-flex;
  padding: 2px 7px;
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--primary);
  background: rgba(var(--primary-rgb), 0.12);
  border: 1px solid rgba(var(--primary-rgb), 0.35);
}
.games-hero-status.is-soon {
  color: #f0c674;
  background: rgba(240, 198, 116, 0.12);
  border-color: rgba(240, 198, 116, 0.35);
}
.games-hero-status.is-ended {
  color: var(--muted);
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}
.games-hero-title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-ui);
}
.games-hero-sub,
.games-hero-time {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.45;
}
.games-hero-time { font-family: var(--font-mono); }
.games-hero-cta {
  margin-top: 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid rgba(var(--primary-rgb), 0.5);
  background: rgba(var(--primary-rgb), 0.16);
  color: var(--primary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-ui);
}
.games-hero-cta:hover { background: rgba(var(--primary-rgb), 0.26); }
.games-hero-cta kbd { font-size: 10px; font-family: var(--font-mono); opacity: 0.85; }
.games-hero-deco { pointer-events: none; }

.games-bottom {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  flex: 1 1 auto;
  min-height: 0;
}
@media (min-width: 900px) {
  .games-bottom {
    grid-template-columns: 1.3fr 1fr !important;
  }
}
.games-panel {
  min-width: 0;
  min-height: 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--card-radius);
  background: rgba(255, 255, 255, 0.02);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.games-panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  flex-shrink: 0;
}
.games-feed {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: auto;
  min-height: 0;
}
.games-feed-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  color: var(--text);
}
.games-feed-item:hover,
.games-feed-item.active {
  background: rgba(var(--primary-rgb), 0.08);
  border-color: rgba(var(--primary-rgb), 0.22);
}
.games-feed-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}
.games-panel-empty {
  margin: 12px 0;
  color: var(--muted);
  font-size: 13px;
}
@media (max-width: 899px) {
  .r2s-games__stage { grid-template-columns: 1fr; }
  .games-hero-banner { grid-template-columns: 1fr; max-height: none; }
}
</style>
