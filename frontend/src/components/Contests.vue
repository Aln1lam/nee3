<template>
  <div class="contests-hub layout-with-sidebar lab-deck" style="--sidebar-width: 248px">
    <div class="contests-stage">
      <aside class="contests-sidebar sidebar-rail">
        <div class="sidebar-head sidebar-rail-head">
          <div class="sidebar-head-row">
            <router-link to="/contests" class="sidebar-title sidebar-rail-title">赛事中心</router-link>
          </div>
          <p class="sidebar-desc sidebar-rail-sub">ARENA · CONTESTS</p>
        </div>

        <n-spin :show="loading" class="sidebar-spin">
          <nav class="sidebar-rail-nav contests-nav">
            <button
              v-for="g in sortedContestsPage"
              :key="g.id"
              type="button"
              class="sidebar-item contest-nav-item"
              :class="{ active: preview?.id === g.id }"
              @mouseenter="setPreview(g)"
              @focus="setPreview(g)"
              @click="enterGame(g)"
            >
              <span class="item-title">{{ g.title }}</span>
              <span
                class="contest-status-chip"
                :class="'is-' + contestStatusVariant(g)"
              >{{ contestStatusLabel(g) }}</span>
            </button>
            <div v-if="!sortedContestsPage.length && !loading" class="empty-side">
              <p>{{ loadError ? '加载失败，请刷新重试' : '暂无赛事' }}</p>
            </div>
          </nav>
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

      <main class="contests-main sidebar-main">
        <div v-if="loading && !preview" class="stage-loading">
          <UiLoadingTips />
        </div>

        <template v-else-if="preview">
          <section
            class="hero-contest-card"
            :class="{ 'is-live': statusVariant === 'success' }"
          >
            <div class="hero-contest-body">
              <div class="hero-copy">
                <span class="status-tag" :class="'is-' + statusKey">
                  <span class="status-led" aria-hidden="true" />
                  [{{ statusCode }}] {{ statusLabel }}
                </span>

                <h1 class="hero-title">{{ preview.title }}</h1>
                <p class="hero-desc">{{ previewDesc }}</p>

                <div class="hero-meta">
                  <div class="meta-item">
                    <div class="meta-label">起止时间</div>
                    <div class="meta-value">{{ timeRange }}</div>
                  </div>
                  <div class="meta-item">
                    <div class="meta-label">{{ countdownLabel }}</div>
                    <div class="meta-value countdown">{{ countdownText }}</div>
                  </div>
                </div>

                <div class="hero-actions">
                  <button type="button" class="cta-btn" @click="enterGame(preview)">
                    进入赛场
                    <span class="cta-arrow">→</span>
                  </button>
                </div>
              </div>

              <button
                type="button"
                class="hero-poster-container"
                aria-label="进入赛场"
                @click="enterGame(preview)"
              >
                <img
                  v-if="previewPosterUrl && !posterBroken"
                  :src="previewPosterUrl"
                  :alt="preview.title"
                  @error="posterBroken = true"
                />
                <div v-else class="cyber-poster-gradient" aria-hidden="true" />
              </button>
            </div>
          </section>

          <section v-if="galleryGames.length" class="more-contests">
            <header class="more-head">
              <h2 class="more-title">{{ otherGames.length >= 3 ? '其他赛事' : '赛事一览' }}</h2>
              <span class="more-sub">GALLERY · WALL</span>
            </header>
            <div class="other-contests-grid">
              <article
                v-for="contest in galleryCards"
                :key="contest.id"
                class="contest-card"
                role="button"
                tabindex="0"
                @click="enterGame(contest)"
                @mouseenter="setPreview(contest)"
                @keydown.enter="enterGame(contest)"
              >
                <div class="card-poster-container">
                  <img
                    v-if="contest.posterUrl"
                    :src="contest.posterUrl"
                    :alt="contest.title"
                    loading="lazy"
                    @error="onCardPosterError(contest)"
                  />
                  <div v-else class="cyber-poster-gradient" aria-hidden="true" />
                </div>
                <div class="contest-card-body">
                  <div class="contest-card-row">
                    <span
                      class="contest-status-chip"
                      :class="'is-' + contestStatusVariant(contest)"
                    >
                      <span class="chip-led" aria-hidden="true" />
                      {{ contestStatusLabel(contest) }}
                    </span>
                    <h3 class="contest-card-title">{{ contest.title }}</h3>
                  </div>
                  <p class="contest-card-time">{{ formatGameTimeRange(contest) }}</p>
                </div>
              </article>
            </div>
          </section>
        </template>

        <div v-else class="stage-empty">
          <h2>选择左侧赛事</h2>
          <p>点击任意比赛进入详情页</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NSpin, NPagination } from 'naive-ui'
import { UiLoadingTips } from '@/components/ui'
import { unwrapList } from '../utils/unwrap'
import { filterPublicGames } from '../utils/gameFilters'
import { resolveUploadUrl } from '../utils/uploadUrl'
import {
  getGameStatusLabel,
  getGameStatusVariant,
  getGameStatusDotClass,
  formatGameTimeRange,
  getGamePosterPath,
  getGameSubtitle,
} from '../utils/gameDisplay'

const PAGE_SIZE = 12

export default {
  name: 'Contests',
  components: { NSpin, NPagination, UiLoadingTips },
  setup() {
    const axios = inject('axios')
    const router = useRouter()
    const route = useRoute()

    const loading = ref(false)
    const loadError = ref(false)
    const games = ref([])
    const preview = ref(null)
    const keyPage = ref(1)
    const nowTick = ref(Date.now())
    const posterBroken = ref(false)
    let tickTimer = null

    /** 状态权重：进行中 > 报名中 > 已结束/归档；同权重按开始时间倒序 */
    function contestSortKey(g) {
      const label = getGameStatusLabel(g)
      let weight = 0
      if (label === '进行中') weight = 3
      else if (label === '报名中') weight = 2
      else if (label === '已结束' || label === '已归档') weight = 1
      const start = g?.start_time || g?.created_at || 0
      const startMs = start ? new Date(start).getTime() : 0
      return { weight, startMs: Number.isFinite(startMs) ? startMs : 0 }
    }

    const sortedContests = computed(() => {
      return [...(games.value || [])].sort((a, b) => {
        const ka = contestSortKey(a)
        const kb = contestSortKey(b)
        if (ka.weight !== kb.weight) return kb.weight - ka.weight
        return kb.startMs - ka.startMs
      })
    })

    const totalPages = computed(() => Math.max(1, Math.ceil(sortedContests.value.length / PAGE_SIZE)))
    const sortedContestsPage = computed(() => {
      const start = (keyPage.value - 1) * PAGE_SIZE
      return sortedContests.value.slice(start, start + PAGE_SIZE)
    })

    /** Hero 默认绑定排序第一场；网格展示其余（hover 切换 preview 时排除当前） */
    const otherGames = computed(() => {
      const pid = preview.value?.id
      return (sortedContests.value || []).filter((g) => String(g.id) !== String(pid))
    })
    /* 满 3 场用「其他」；不足时用全量排序列表填满 3 列墙 */
    const galleryGames = computed(() => {
      const others = otherGames.value
      if (others.length >= 3) return others
      return sortedContests.value || []
    })

    const statusLabel = computed(() => getGameStatusLabel(preview.value))
    const statusVariant = computed(() => getGameStatusVariant(preview.value))
    const statusKey = computed(() => {
      const v = statusVariant.value
      if (v === 'success') return 'live'
      if (v === 'warning') return 'soon'
      return 'ended'
    })
    const statusCode = computed(() => {
      if (statusKey.value === 'live') return 'LIVE'
      if (statusKey.value === 'soon') return 'SOON'
      return 'END'
    })
    const timeRange = computed(() => formatGameTimeRange(preview.value))
    const previewDesc = computed(() => getGameSubtitle(preview.value))

    const previewPosterUrl = computed(() => {
      const path = getGamePosterPath(preview.value)
      return path ? resolveUploadUrl(path, preview.value?.id) : ''
    })

    watch(() => preview.value?.id, () => { posterBroken.value = false })

    const countdownLabel = computed(() => {
      const g = preview.value
      if (!g) return '倒计时'
      const now = nowTick.value
      const start = g.start_time ? new Date(g.start_time).getTime() : 0
      const end = g.end_time ? new Date(g.end_time).getTime() : 0
      if (now < start) return '距开始'
      if (end && now < end) return '距结束'
      return '状态'
    })

    const countdownText = computed(() => {
      const g = preview.value
      if (!g) return '--'
      const now = nowTick.value
      const start = g.start_time ? new Date(g.start_time).getTime() : 0
      const end = g.end_time ? new Date(g.end_time).getTime() : 0
      let target = 0
      if (now < start) target = start
      else if (end && now < end) target = end
      else return '已结束'
      const diff = Math.max(0, target - now)
      const d = Math.floor(diff / 86400000)
      const h = Math.floor((diff % 86400000) / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      const pad = (n) => String(n).padStart(2, '0')
      if (d > 0) return `${d}天 ${pad(h)}:${pad(m)}:${pad(s)}`
      return `${pad(h)}:${pad(m)}:${pad(s)}`
    })

    const ctaLabel = computed(() => {
      const label = statusLabel.value
      if (label === '进行中') return '进入赛场'
      if (label === '报名中') return '立即参赛'
      return '查看赛事'
    })

    function contestStatusLabel(g) {
      return getGameStatusLabel(g)
    }
    function contestStatusVariant(g) {
      return getGameStatusVariant(g) || 'default'
    }
    const brokenCardPosters = ref(new Set())

    function posterUrlOf(g) {
      if (!g?.id) return ''
      if (brokenCardPosters.value.has(g.id)) return ''
      const path = getGamePosterPath(g)
      return path ? resolveUploadUrl(path, g?.id) : ''
    }

    function onCardPosterError(contest) {
      if (!contest?.id) return
      const next = new Set(brokenCardPosters.value)
      next.add(contest.id)
      brokenCardPosters.value = next
    }

    const galleryCards = computed(() =>
      (galleryGames.value || []).map((g) => ({
        ...g,
        posterUrl: posterUrlOf(g),
      })),
    )

    function setPreview(g) {
      preview.value = g
    }

    function enterGame(g) {
      if (!g?.id) return
      router.push(`/games/${g.id}`)
    }

    async function loadGames() {
      loading.value = true
      loadError.value = false
      try {
        const { data } = await axios.get('/api/competitions/', { params: { exclude_training: true } })
        games.value = filterPublicGames(unwrapList(data))
        const params = route.query
        if (params['key-page']) keyPage.value = parseInt(params['key-page'], 10) || 1
        const sel = params.selected ? parseInt(params.selected, 10) : null
        const pool = sortedContests.value
        const hit = sel ? pool.find((x) => x.id === sel) : null
        /* Hero 默认绑定智能排序第一名 */
        preview.value = hit || pool[0] || null
      } catch (e) {
        console.error(e)
        loadError.value = true
      } finally {
        loading.value = false
      }
    }

    watch(keyPage, (p) => {
      if (String(route.query['key-page'] || '') === String(p)) return
      router.replace({ query: { ...route.query, 'key-page': p } })
    })

    watch(preview, (g) => {
      if (!g?.id) return
      if (String(route.query.selected || '') === String(g.id)) return
      router.replace({ query: { ...route.query, selected: g.id } })
    })

    onMounted(async () => {
      tickTimer = setInterval(() => { nowTick.value = Date.now() }, 1000)
      await loadGames()
    })

    onUnmounted(() => {
      if (tickTimer) clearInterval(tickTimer)
    })

    return {
      loading, loadError, preview, posterBroken,
      sortedContests, sortedContestsPage, otherGames, galleryGames,
      keyPage, totalPages,
      statusLabel, statusVariant, statusKey, statusCode,
      timeRange, previewDesc, previewPosterUrl,
      countdownLabel, countdownText, ctaLabel,
      contestStatusLabel, contestStatusVariant, posterUrlOf, galleryCards, onCardPosterError,
      formatGameTimeRange, getGameStatusDotClass,
      setPreview, enterGame,
    }
  },
}
</script>

<style scoped>
.contests-hub {
  height: calc(100vh - var(--nav-height, 72px));
  max-height: calc(100vh - var(--nav-height, 72px));
  overflow: hidden; /* 禁止整页滚动，Header/侧栏绝对稳定 */
  width: 100%;
  font-family: var(--font-ui, "M PLUS Rounded 1c", "Noto Sans SC", "PingFang SC", sans-serif);
  -webkit-font-smoothing: antialiased;
  box-sizing: border-box;
}
.contests-stage {
  display: grid;
  grid-template-columns: 248px minmax(0, 1fr);
  height: 100%;
  max-height: 100%;
  min-height: 0;
  width: 100%;
  overflow: hidden;
}
.contests-sidebar {
  height: 100%;
  max-height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 侧栏独立，不带动整页 */
}
.sidebar-spin {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.contests-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px 12px;
}
.contests-nav .contest-nav-item.sidebar-item,
.contests-nav .contest-nav-item {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  justify-content: center !important;
  grid-template-columns: unset !important;
  gap: 6px !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 10px 14px !important;
  border: 1px solid transparent !important;
  border-radius: 8px !important;
  background: transparent !important;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: none !important;
  min-height: 0 !important;
  text-align: left;
  box-sizing: border-box;
}
.contests-nav .contest-nav-item .item-title {
  width: 100%;
  min-width: 0;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.4 !important;
  color: #e5e7eb;
  white-space: normal !important;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  word-break: break-word;
}
.contests-nav .contest-nav-item:hover {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
}
.contests-nav .contest-nav-item.active {
  background: rgba(16, 185, 129, 0.08) !important;
  border: 1px solid rgba(16, 185, 129, 0.25) !important;
  box-shadow: inset 0 0 12px rgba(16, 185, 129, 0.05) !important;
  color: #fff !important;
}
.contests-nav .contest-nav-item.active .item-title {
  color: #fff !important;
  font-weight: 600 !important;
}
.contest-status-chip {
  align-self: flex-start;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(148, 163, 184, 0.12);
  color: #94a3b8;
  line-height: 1.35;
}
.contests-nav .contest-nav-item.active .contest-status-chip {
  border-color: rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.14);
  color: #6ee7b7;
}
.contest-status-chip.is-success {
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.35);
  background: rgba(34, 197, 94, 0.12);
}
.contest-status-chip.is-warning {
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.12);
}
.contest-status-chip.is-info {
  color: #5ed9a8;
  border-color: rgba(94, 217, 168, 0.35);
  background: rgba(94, 217, 168, 0.12);
}
.empty-side {
  padding: 24px 14px;
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
}
.side-pagination {
  margin: 8px 0 4px;
  justify-content: center;
}

.contests-main {
  min-width: 0;
  min-height: 0;
  height: calc(100vh - var(--nav-height, 72px));
  max-height: calc(100vh - var(--nav-height, 72px));
  width: 100% !important;
  max-width: none !important;
  overflow-x: hidden;
  overflow-y: auto; /* 仅主舞台纵向滚动 */
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 24px;
  box-sizing: border-box;
}
.stage-loading,
.stage-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  gap: 8px;
}
.stage-empty h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #f3f4f6;
}
.stage-empty p { margin: 0; font-size: 14px; }

/* Hero 全宽 55 / 45 */
.hero-contest-card {
  padding: 32px;
  box-sizing: border-box;
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  flex: 0 0 auto;
  align-self: stretch;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(18, 24, 36, 0.88) 0%, rgba(12, 16, 24, 0.72) 100%);
  backdrop-filter: blur(18px) saturate(1.15);
  -webkit-backdrop-filter: blur(18px) saturate(1.15);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 20px 56px rgba(0, 0, 0, 0.35);
}
.hero-contest-card.is-live { border-color: rgba(16, 185, 129, 0.28); }
.hero-contest-body {
  display: grid;
  grid-template-columns: 55% 45%;
  align-items: stretch;
  width: 100%;
  min-height: 0;
}
.hero-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  padding: 36px 32px;
  box-sizing: border-box;
}
/* Hero 海报：无外层黑框套娃，与下方卡片同质感 */
.hero-poster-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  margin: 28px 28px 28px 8px; /* 仅留白，无深色底座 */
  padding: 0;
  border: none;
  border-radius: 12px !important;
  overflow: hidden !important;
  background: transparent; /* 废除多余黑色底色 */
  box-sizing: border-box;
  cursor: pointer;
  color: inherit;
  font: inherit;
  display: block;
  align-self: center;
  isolation: isolate;
  transition: transform 0.25s ease, filter 0.25s ease;
}
.hero-poster-container:hover {
  filter: brightness(1.05);
  transform: scale(1.012);
}
.hero-poster-container img,
.hero-poster-container .cyber-poster-gradient {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px !important;
  border: 1px solid rgba(255, 255, 255, 0.1); /* 微光边框 */
  display: block;
  box-sizing: border-box;
}

/* 全页统一 Cyber 海报占位（Hero + 卡片） */
.cyber-poster-gradient {
  width: 100%;
  height: 100%;
  min-height: 100%;
  background:
    radial-gradient(ellipse at 25% 20%, rgba(16, 185, 129, 0.32) 0%, transparent 48%),
    radial-gradient(ellipse at 85% 80%, rgba(56, 189, 248, 0.12) 0%, transparent 42%),
    linear-gradient(155deg, #101820 0%, #162436 50%, #0c121a 100%);
}
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 28px;
  padding: 0 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  font-family: var(--font-mono, "JetBrains Mono", "Fira Code", monospace);
  color: #10b981;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  width: fit-content;
}
.status-tag .status-led {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ef4444;
  animation: live-pulse 1.4s ease infinite;
}
.status-tag.is-soon {
  color: #f0c674;
  background: rgba(240, 198, 116, 0.12);
  border-color: rgba(240, 198, 116, 0.35);
}
.status-tag.is-soon .status-led {
  background: #fbbf24;
  animation: soon-pulse 1.8s ease infinite;
}
.status-tag.is-ended {
  color: #9ca3af;
  background: rgba(107, 114, 128, 0.12);
  border-color: rgba(107, 114, 128, 0.3);
}
.status-tag.is-ended .status-led {
  background: #6b7280;
  animation: none;
}
@keyframes live-pulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
  70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
@keyframes soon-pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}
.hero-title {
  margin: 0;
  font-size: clamp(1.65rem, 2.9vw, 2.4rem);
  font-weight: 760;
  line-height: 1.2;
  color: #f3f4f6;
  letter-spacing: -0.02em;
}
.hero-desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  color: #e5e7eb;
  max-width: 48ch;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
.hero-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.meta-item {
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.meta-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #9ca3af;
  margin-bottom: 6px;
  text-transform: uppercase;
}
.meta-value {
  font-size: 13px;
  font-weight: 600;
  color: #e5e7eb;
  font-family: var(--font-mono, "JetBrains Mono", "Fira Code", monospace);
  line-height: 1.4;
}
.meta-value.countdown {
  font-size: 20px;
  font-weight: 700;
  color: #10b981;
}
.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 46px;
  padding: 0 24px;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  color: #0a0f14;
  background: #10b981;
  box-shadow: 0 0 22px rgba(16, 185, 129, 0.38), 0 8px 20px rgba(16, 185, 129, 0.22);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}
.cta-btn:hover {
  filter: brightness(1.06);
  transform: translateY(-1px);
  box-shadow: 0 0 30px rgba(16, 185, 129, 0.48), 0 10px 24px rgba(16, 185, 129, 0.28);
}
.cta-arrow { font-size: 18px; line-height: 1; }

/* 3 列等宽 Gallery — 与 Hero 同宽 100% 对齐 */
.more-contests {
  width: 100% !important;
  max-width: none !important;
  flex: 0 0 auto;
  align-self: stretch;
}
.more-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 14px;
}
.more-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #f3f4f6;
}
.more-sub {
  font-family: var(--font-mono, "JetBrains Mono", monospace);
  font-size: 11px;
  letter-spacing: 0.14em;
  color: rgba(94, 217, 168, 0.65);
}
.other-contests-grid {
  display: grid !important;
  grid-template-columns: repeat(3, 1fr) !important; /* 强制 3 列，消除右侧死黑 */
  gap: 20px !important;
  width: 100% !important;
  max-width: none !important;
  box-sizing: border-box;
}
.contest-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(18, 24, 36, 0.62);
  overflow: hidden !important; /* 与顶部海报圆角重合裁剪 */
  cursor: pointer;
  text-align: left;
  color: inherit;
  transition: all 0.3s ease;
}
.contest-card:hover {
  transform: translateY(-4px);
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.07);
  box-shadow:
    0 12px 28px rgba(0, 0, 0, 0.32),
    0 0 24px rgba(16, 185, 129, 0.1);
}
.contest-card:focus-visible {
  outline: 2px solid rgba(16, 185, 129, 0.55);
  outline-offset: 2px;
}
/* 卡片海报：上方圆角 + 强制裁剪 */
.card-poster-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  height: auto;
  max-height: 180px;
  border-radius: 10px 10px 0 0 !important;
  overflow: hidden !important;
  background: transparent; /* 与 Hero 一致：无多余黑底座 */
  flex-shrink: 0;
  isolation: isolate;
}
.card-poster-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border-radius: 10px 10px 0 0;
  transition: transform 0.35s ease;
}
.contest-card:hover .card-poster-container img {
  transform: scale(1.04);
}
.card-poster-container .cyber-poster-gradient {
  min-height: 120px;
  border: none;
  border-radius: 0;
}
.contest-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px 14px;
}
.contest-card-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.contest-card-body .contest-status-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}
.chip-led {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.contest-card-title {
  margin: 0;
  min-width: 0;
  flex: 1 1 auto;
  font-size: 15px;
  font-weight: 600;
  color: #e5e7eb;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.contest-card-time {
  margin: 0;
  font-size: 12px;
  font-family: var(--font-mono, monospace);
  color: #9ca3af;
  line-height: 1.4;
}

@media (max-width: 1100px) {
  .other-contests-grid {
    grid-template-columns: repeat(3, 1fr) !important; /* 中屏仍保持 3 列与 Hero 对齐 */
  }
  .card-poster-container { max-height: 150px; }
}
@media (max-width: 900px) {
  .contests-stage { grid-template-columns: 1fr; }
  .contests-sidebar { max-height: 38vh; }
  .contests-main {
    height: auto;
    max-height: none;
  }
  .hero-contest-body { grid-template-columns: 1fr; }
  .hero-poster-container {
    margin: 0 20px 20px;
  }
  .hero-copy { padding: 24px 20px 16px; }
  .hero-meta { grid-template-columns: 1fr; }
  .other-contests-grid {
    grid-template-columns: 1fr !important;
  }
  .card-poster-container { max-height: none; }
}

</style>
