# -*- coding: utf-8 -*-
"""Restore full GamesHub.vue with Ret2Shell template + logic."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'GamesHub.vue'
p.write_text(r'''<template>
  <div class="games-hub r2s-games">
    <div class="r2s-games__stage">
      <aside class="r2s-games__list-pane">
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
              <span class="r2s-games__list-title">{{ g.title }}</span>
              <span class="dot" :class="getGameStatusDotClass(g)" aria-hidden="true" />
            </button>
            <div v-if="!featuredGames.length && !loading" class="empty-side">
              <p>暂无正式赛事</p>
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
      </aside>

      <main class="r2s-games__cover">
        <div v-if="detailLoading && !selectedDetail" class="poster-loading">
          <UiLoadingTips />
        </div>
        <button
          v-else-if="selectedDetail"
          type="button"
          class="r2s-games__cover-card"
          @click="openGameDetail(selectedDetail)"
        >
          <div class="r2s-games__cover-visual" :class="coverTheme">
            <img
              v-if="posterUrl && !posterBroken"
              :src="posterUrl"
              :alt="selectedDetail.title"
              @error="posterBroken = true"
            />
            <div v-else class="r2s-games__cover-fallback">{{ getGameEmoji(selectedDetail) }}</div>
          </div>
          <span class="r2s-games__status-pill">
            <span class="dot" :class="`dot-${statusVariant === 'success' ? 'live' : statusVariant === 'warning' ? 'soon' : 'ended'}`" />
            {{ statusLabel }}
          </span>
          <div class="r2s-games__info">
            <svg class="r2s-games__info-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M4 3.5A1.5 1.5 0 015.5 2h5.086a1.5 1.5 0 011.06.44l3.914 3.914a1.5 1.5 0 01.44 1.06V16.5A1.5 1.5 0 0114.5 18h-9A1.5 1.5 0 014 16.5v-13z" />
            </svg>
            <div>
              <p class="r2s-games__info-title">{{ selectedDetail.title }}</p>
              <p class="r2s-games__info-sub">{{ gameSubtitle }}</p>
              <p class="r2s-games__info-time">{{ timeRange }}</p>
            </div>
          </div>
        </button>
        <div v-else class="poster-empty">
          <h2>选择左侧赛事查看详情</h2>
        </div>
      </main>
    </div>

    <section v-if="otherGamesAll.length" class="r2s-games__others">
      <h3>其他赛事</h3>
      <div class="r2s-games__others-grid">
        <div
          v-for="g in otherGamesPage"
          :key="g.id"
          class="r2s-games__other-card"
          @click="selectGame(g)"
        >
          <div class="title">{{ g.title }}</div>
          <UiTag :variant="getGameStatusVariant(g)" size="small">{{ getGameStatusLabel(g) }}</UiTag>
        </div>
      </div>
      <n-pagination
        v-if="otherTotalPages > 1"
        v-model:page="otherPage"
        :page-count="otherTotalPages"
        size="small"
        class="other-pagination"
      />
    </section>
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
      loading, detailLoading, selected, selectedDetail, posterBroken,
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
.poster-loading,
.poster-empty {
  width: 100%;
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
}
.poster-empty h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}
</style>
''', encoding='utf-8', newline='\n')
print('GamesHub restored')
