# -*- coding: utf-8 -*-
"""GamesHub: filter ephemeral tests, poster onerror, tighter sidebar."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'GamesHub.vue'
text = p.read_text(encoding='utf-8')

replacements = [
(
'''              <img
                v-if="posterUrl"
                :src="posterUrl"
                :alt="selectedDetail.title"
                class="poster-img"
              />''',
'''              <img
                v-if="posterUrl && !posterBroken"
                :src="posterUrl"
                :alt="selectedDetail.title"
                class="poster-img"
                @error="posterBroken = true"
              />'''
),
(
'          <p class="sidebar-desc sidebar-rail-sub">CTF · GAMES</p>',
'          <p class="sidebar-desc sidebar-rail-sub">正式赛事 · 不含测试数据</p>',
),
(
'''              <div v-if="!featuredGames.length && !loading" class="empty-side">
                <p>暂无赛事</p>
                <p class="empty-hint">
                  管理员可创建赛事，或先前往
                  <router-link to="/training">训练场</router-link>
                </p>
              </div>''',
'''              <div v-if="!featuredGames.length && !loading" class="empty-side">
                <p>暂无正式赛事</p>
                <p class="empty-hint">
                  测试/流量探针赛已隐藏。管理员可创建赛事，或前往
                  <router-link to="/training">训练场</router-link>
                </p>
              </div>'''
),
(
'''import { resolveUploadUrl } from '../utils/uploadUrl'
import {
  getGameEmoji,''',
'''import { resolveUploadUrl } from '../utils/uploadUrl'
import { filterPublicGames } from '../utils/gameFilters'
import {
  getGameEmoji,'''
),
('const PAGE_SIZE = 12', 'const PAGE_SIZE = 8'),
(
'''    const loading = ref(false)
    const detailLoading = ref(false)
    const games = ref([])
    const selected = ref(null)
    const selectedDetail = ref(null)
    const canCreateGame = ref(false)''',
'''    const loading = ref(false)
    const detailLoading = ref(false)
    const games = ref([])
    const selected = ref(null)
    const selectedDetail = ref(null)
    const posterBroken = ref(false)
    const canCreateGame = ref(false)'''
),
(
'''    const posterUrl = computed(() => {
      const path = getGamePosterPath(selectedDetail.value)
      return path ? resolveUploadUrl(path) : ''
    })''',
'''    const posterUrl = computed(() => {
      const path = getGamePosterPath(selectedDetail.value)
      return path ? resolveUploadUrl(path, selectedDetail.value?.id) : ''
    })'''
),
(
'''    function selectGame(g) {
      selected.value = g
      const idx = featuredPool.value.findIndex(x => x.id === g.id)
      if (idx >= 0) keyPage.value = Math.floor(idx / PAGE_SIZE) + 1
      router.replace({ query: { selected: g.id, 'key-page': keyPage.value } })
      loadGameDetail(g.id)
    }''',
'''    function selectGame(g) {
      selected.value = g
      posterBroken.value = false
      const idx = featuredPool.value.findIndex(x => x.id === g.id)
      if (idx >= 0) keyPage.value = Math.floor(idx / PAGE_SIZE) + 1
      router.replace({ query: { selected: g.id, 'key-page': keyPage.value } })
      loadGameDetail(g.id)
    }'''
),
(
'''        const { data } = await axios.get('/api/competitions/', { params: { exclude_training: true } })
        games.value = unwrapList(data)''',
'''        const { data } = await axios.get('/api/competitions/', { params: { exclude_training: true } })
        games.value = filterPublicGames(unwrapList(data))'''
),
(
'''      loading, detailLoading, selected, selectedDetail,
      featuredGames, otherGamesAll, otherGamesPage, otherTotalPages, featuredPool,
      canCreateGame, keyPage, otherPage, otherSectionRef, totalPages,
      collapsed, toggleSidebar,
      coverTheme, statusLabel, statusVariant, gameSubtitle, timeRange, posterUrl,''',
'''      loading, detailLoading, selected, selectedDetail, posterBroken,
      featuredGames, otherGamesAll, otherGamesPage, otherTotalPages, featuredPool,
      canCreateGame, keyPage, otherPage, otherSectionRef, totalPages,
      collapsed, toggleSidebar,
      coverTheme, statusLabel, statusVariant, gameSubtitle, timeRange, posterUrl,'''
),
(
'''        selectedDetail.value = data?.data || data || selected.value
      } catch {
        selectedDetail.value = selected.value
      } finally {''',
'''        selectedDetail.value = data?.data || data || selected.value
        posterBroken.value = false
      } catch {
        selectedDetail.value = selected.value
        posterBroken.value = false
      } finally {'''
),
]

for i, (old, new) in enumerate(replacements):
    if old not in text:
        raise SystemExit(f'block {i} not found')
    text = text.replace(old, new, 1)

p.write_text(text, encoding='utf-8', newline='\n')
print('GamesHub sidebar patch ok')
