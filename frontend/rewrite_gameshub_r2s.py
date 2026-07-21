# -*- coding: utf-8 -*-
"""Rewrite GamesHub template to Ret2Shell games layout."""
from pathlib import Path
import re

p = Path(__file__).resolve().parent / 'src' / 'components' / 'GamesHub.vue'
text = p.read_text(encoding='utf-8')

# Replace entire template
m = re.search(r'<template>[\s\S]*?</template>', text)
if not m:
    raise SystemExit('template not found')

new_tpl = r'''<template>
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
            <span class="dot" />
            {{ statusLabel }}
          </span>
          <div class="r2s-games__info">
            <svg class="r2s-games__info-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M4 3.5A1.5 1.5 0 015.5 2h5.086a1.5 1.5 0 011.06.44l3.914 3.914a1.5 1.5 0 01.44 1.06V16.5A1.5 1.5 0 0114.5 18h-9A1.5 1.5 0 014 16.5v-13z"/>
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
</template>'''

text = text[:m.start()] + new_tpl + text[m.end()]

# Remove obsolete layout-with-sidebar classes dependency is fine
# Soften scoped styles that fight r2s — leave but ensure root class ok

# Ensure canCreateGame used (already), getGameSidebarCode may be unused — ok

p.write_text(text, encoding='utf-8', newline='\n')
print('GamesHub template rewritten')
