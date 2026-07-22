<template>
  <div
    class="wiki-layout layout-with-sidebar lab-deck"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <aside class="wiki-sidebar sidebar-rail">
      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/wiki" class="sidebar-title sidebar-rail-title">知识库</router-link>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">DOC · WIKI</p>
      </div>

      <div class="sidebar-rail-nav">
        <div class="sidebar-group">
          <div class="group-label">分类</div>
          <button
            v-for="c in categories"
            :key="c"
            type="button"
            class="sidebar-item"
            :class="{ active: selectedTag === c }"
            @click="selectTag(c)"
          >
            <span class="item-code">{{ tagCode(c) }}</span>
            <span class="item-title">{{ c }}</span>
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

    <main class="wiki-main sidebar-main">
      <header class="wiki-head">
        <div class="wiki-head-text">
          <p class="wiki-kicker">知识库 · WIKI</p>
          <h2 class="wiki-title">Wiki 文档</h2>
          <p class="wiki-desc">
            <span v-if="selectedTag">当前标签：{{ selectedTag }}（{{ articles.length }} 篇）</span>
            <span v-else>WriteUp · 教程 · 知识沉淀</span>
          </p>
        </div>

        <!-- Top Control Rail：紧凑搜索 + 投稿 -->
        <div class="wiki-control-rail">
          <div class="wiki-search">
            <svg class="wiki-search-icon" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
              <circle cx="6.5" cy="6.5" r="4.5" fill="none" stroke="currentColor" stroke-width="1.4"/>
              <path d="M10 10l3.5 3.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            </svg>
            <input
              v-model="q"
              class="wiki-search-input"
              type="search"
              placeholder="搜索标题或内容"
              @keyup.enter="fetch"
            />
          </div>
          <button type="button" class="wiki-submit-btn" @click="$router.push('/knowledge/new')">
            + 投稿 WriteUp
          </button>
        </div>
      </header>

      <div class="wiki-stage">
        <section class="wiki-feed-col">
          <div class="wiki-list-panel">
            <template v-if="articles.length">
              <article
                v-for="a in articles"
                :key="a.id"
                class="wiki-item"
                @click="goArticle(a.id)"
              >
                <div class="wiki-item-head">
                  <span class="link-code chip-cut wiki-doc-chip">DOC</span>
                  <div class="wiki-item-body">
                    <h3 class="wiki-item-title">{{ a.title }}</h3>
                    <p v-if="a.summary" class="wiki-item-summary">{{ a.summary }}</p>
                    <div class="wiki-item-foot">
                      <div class="wiki-item-tags">
                        <n-tag
                          v-for="t in renderTags(a)"
                          :key="a.id + '-tag-' + t"
                          size="small"
                          round
                        >{{ t }}</n-tag>
                      </div>
                      <time class="wiki-item-time">{{ formatWikiTime(a.created_at) }}</time>
                    </div>
                  </div>
                  <span class="wiki-item-arrow">→</span>
                </div>
              </article>
            </template>
            <div v-else class="wiki-empty">暂无相关文章</div>
          </div>
        </section>

        <aside class="wiki-aside-col">
          <!-- 知识库概览 & 热门阅读（替代重复热门标签） -->
          <section class="wiki-aside-card wiki-aside-card--soft">
            <div class="wiki-aside-head">
              <span class="link-code chip-cut">OVR</span>
              <span>知识库概览</span>
            </div>
            <div class="wiki-stats">
              <div class="wiki-stat">
                <span class="wiki-stat-label">已沉淀文章</span>
                <span class="wiki-stat-value">{{ articleCountLabel }}</span>
              </div>
              <div class="wiki-stat-divider" aria-hidden="true" />
              <div class="wiki-stat">
                <span class="wiki-stat-label">总阅读量</span>
                <span class="wiki-stat-value">{{ readsLabel }}</span>
              </div>
            </div>
            <div class="wiki-aside-subhead">
              <span class="link-code chip-cut">HOT</span>
              <span>热门阅读</span>
            </div>
            <ul class="wiki-hot-list">
              <li v-for="h in hotArticles" :key="'hot-' + h.id">
                <button type="button" class="wiki-hot-link" @click="goArticle(h.id)">
                  <span class="wiki-hot-title">{{ h.title }}</span>
                  <span class="wiki-hot-arrow">→</span>
                </button>
              </li>
              <li v-if="!hotArticles.length" class="wiki-hot-empty">暂无热门条目</li>
            </ul>
          </section>

          <!-- WriteUp 投稿指引：细线框 + 文字链 -->
          <section class="wiki-aside-card wiki-aside-card--guide">
            <div class="wiki-aside-head wiki-aside-head--muted">
              <span class="link-code chip-cut">WRT</span>
              <span>WriteUp 投稿指引</span>
            </div>
            <p class="wiki-guide-text">
              使用 Markdown 撰写：题目背景 → 思路拆解 → Payload / 关键命令 → 复盘总结。
              附件请控制在合理体积，并打上准确分类标签，便于侧栏检索。
            </p>
            <ul class="wiki-guide-mini">
              <li>标题简洁，摘要 1–2 句</li>
              <li>代码块标明语言</li>
              <li>敏感 Flag 打码后再公开</li>
            </ul>
            <button type="button" class="wiki-guide-link" @click="$router.push('/knowledge/new')">
              了解 WriteUp 撰写规范 →
            </button>
          </section>
        </aside>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, inject, watch } from 'vue'
import axiosGlobal from 'axios'
import { TAGS } from '../services/tags'
import { useRoute, useRouter } from 'vue-router'
import { NTag } from 'naive-ui'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'
import { formatWikiTags, formatWikiTime } from '../utils/wikiDisplay'

function heatScore(a) {
  const id = Number(a?.id) || 0
  const len = String(a?.content || a?.summary || '').length
  return id * 41 + 180 + Math.min(len, 800)
}

function formatReads(n) {
  if (n >= 1000) {
    const k = n / 1000
    return (Math.round(k * 10) / 10).toString().replace(/\.0$/, '') + 'k'
  }
  return String(n)
}

export default {
  components: { NTag },
  setup() {
    const axios = inject('axios') || axiosGlobal
    const route = useRoute()
    const router = useRouter()
    const articles = ref([])
    const catalog = ref([])
    const catalogTotal = ref(0)
    const q = ref('')
    const selectedTag = ref('')
    const categories = TAGS
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_wiki_sidebar_collapsed')

    const articleCountLabel = computed(() => `${catalogTotal.value} 篇`)
    const readsLabel = computed(() => {
      const n = catalog.value.reduce((s, a) => s + heatScore(a), 0)
      return formatReads(n || catalogTotal.value * 200)
    })
    const hotArticles = computed(() => {
      return [...catalog.value]
        .sort((a, b) => heatScore(b) - heatScore(a))
        .slice(0, 3)
    })

    function tagCode(tag) {
      const t = (tag || '').toLowerCase()
      if (t.includes('环境')) return 'ENV'
      if (t.includes('misc') || t.includes('杂项')) return 'MSC'
      if (t.includes('web')) return 'WEB'
      if (t.includes('crypto') || t.includes('密码')) return 'CRY'
      if (t.includes('reverse') || t.includes('逆向')) return 'REV'
      if (t.includes('pwn') || t.includes('二进制')) return 'PWN'
      if (t.includes('awd')) return 'AWD'
      if (t.includes('blockchain') || t.includes('区块链')) return 'BC'
      if (t.includes('ai') || t.includes('人工智能')) return 'AI'
      if (t.includes('其他')) return 'OTH'
      return 'DOC'
    }

    function selectTag(c) {
      q.value = ''
      if (selectedTag.value === c) {
        clearCategory()
        return
      }
      selectedTag.value = c
      try { router.push({ path: '/wiki', query: { tag: c } }) } catch { /* ignore */ }
      fetch()
    }

    function clearCategory() {
      q.value = ''
      selectedTag.value = ''
      router.push('/wiki').catch(() => null)
      fetch()
    }

    async function fetchCatalog() {
      try {
        const r = await axios.get('/api/articles/', { params: { per_page: 50 } })
        const items = r.data.data?.items || r.data.items || []
        catalog.value = items
        catalogTotal.value = r.data.data?.total ?? items.length
      } catch {
        catalog.value = []
        catalogTotal.value = 0
      }
    }

    async function fetch() {
      try {
        const params = { q: q.value, per_page: 50 }
        if (selectedTag.value) params.tag = selectedTag.value
        const r = await axios.get('/api/articles/', { params })
        articles.value = r.data.data?.items || r.data.items || []
        const needs = articles.value.filter(a => a.resource_id)
        if (needs.length) {
          await Promise.all(needs.map(async (a) => {
            try {
              const rr = await axios.get('/api/resources/' + a.resource_id)
              if (rr?.data?.url) a.file_url = rr.data.url
            } catch { /* ignore */ }
          }))
        }
      } catch {
        articles.value = []
      }
    }

    function onArticleSaved() {
      fetch()
      fetchCatalog()
    }

    function goArticle(id) {
      router.push('/wiki/' + id).catch(() => null)
    }

    function renderTags(a) {
      return formatWikiTags(a?.tags)
    }

    onMounted(() => {
      if (route.query?.tag) selectedTag.value = route.query.tag
      if (route.query?.q) q.value = route.query.q
      fetch()
      fetchCatalog()
      window.addEventListener('neepu_article_saved', onArticleSaved)
    })

    onUnmounted(() => {
      window.removeEventListener('neepu_article_saved', onArticleSaved)
    })

    watch(() => route.query, (nv) => {
      if (nv?.tag !== undefined) {
        selectedTag.value = nv.tag || ''
        fetch()
      }
      if (nv?.q !== undefined) {
        q.value = nv.q || ''
        fetch()
      }
    })

    return {
      articles, q, fetch, categories, selectTag, clearCategory, tagCode,
      selectedTag, goArticle, renderTags, formatWikiTime, collapsed, toggleSidebar,
      articleCountLabel, readsLabel, hotArticles,
    }
  },
}
</script>

<style scoped>
.wiki-layout {
  width: 100%;
  height: calc(100vh - var(--nav-height, 72px));
  max-height: calc(100vh - var(--nav-height, 72px));
  overflow: hidden !important;
  margin: 0;
}

/* NEEPU_WIKI_FONT_STACK */
.wiki-layout,
.wiki-layout :deep(*):not(.sidebar-rail-sub):not(.sidebar-desc) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}
.wiki-layout .wiki-title {
  font-weight: 700 !important;
}
.wiki-layout .wiki-item-title,
.wiki-layout .wiki-hot-title {
  font-weight: 500 !important;
}
.wiki-layout :deep(.sidebar-rail-sub),
.wiki-layout :deep(.sidebar-desc.sidebar-rail-sub) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
  font-size: 11px !important;
  letter-spacing: 1px !important;
  color: #6b7280 !important;
}
.wiki-layout :deep(.sidebar-title),
.wiki-layout :deep(.sidebar-rail-title) {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #ffffff !important;
}
.wiki-layout :deep(.group-label) {
  font-size: 12px !important;
  font-weight: 500 !important;
  color: #9ca3af !important;
  margin-bottom: 12px !important;
}
.wiki-layout :deep(.sidebar-item) {
  padding: 8px 12px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.5 !important;
}
.wiki-layout :deep(.sidebar-item .item-title) {
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.5 !important;
}
/* /NEEPU_WIKI_FONT_STACK */

/* 侧栏 */
.wiki-layout :deep(.sidebar-rail),
.wiki-sidebar.sidebar-rail {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.wiki-layout :deep(.sidebar-rail-nav),
.wiki-sidebar .sidebar-rail-nav {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.wiki-layout :deep(.sidebar-rail-nav)::-webkit-scrollbar,
.wiki-sidebar .sidebar-rail-nav::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}
.wiki-layout :deep(.sidebar-item),
.wiki-sidebar .sidebar-item {
  height: auto;
  align-items: center;
  gap: 10px;
}
.wiki-layout :deep(.sidebar-item .item-code),
.wiki-sidebar .item-code {
  flex-shrink: 0;
  min-width: 36px;
  height: 20px;
  line-height: 20px;
}
.wiki-layout :deep(.sidebar-item .item-title),
.wiki-sidebar .item-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wiki-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 20px 16px;
  scrollbar-width: none;
}
.wiki-main::-webkit-scrollbar { display: none; width: 0; height: 0; }

/* 头部：文案 + 紧凑 Control Rail */
.wiki-head {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px 20px;
}
.wiki-kicker {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: #5ED9A8;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
}
.wiki-title {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.25;
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
}
.wiki-desc {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.4;
}

.wiki-control-rail {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.wiki-search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: min(280px, 42vw);
  height: 36px;
  padding: 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  transition: border-color 0.15s, background 0.15s;
}
.wiki-search:focus-within {
  border-color: rgba(94, 217, 168, 0.4);
  background: rgba(94, 217, 168, 0.04);
}
.wiki-search-icon {
  flex-shrink: 0;
  color: var(--muted);
  opacity: 0.85;
}
.wiki-search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text);
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
}
.wiki-search-input::placeholder { color: var(--muted); opacity: 0.85; }
.wiki-search-input::-webkit-search-cancel-button { display: none; }

.wiki-submit-btn {
  flex-shrink: 0;
  height: 36px;
  padding: 0 14px;
  border: 1px solid rgba(94, 217, 168, 0.35);
  border-radius: 8px;
  background: rgba(94, 217, 168, 0.12);
  color: #5ED9A8;
  font-size: 13px;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
}
.wiki-submit-btn:hover {
  background: rgba(94, 217, 168, 0.2);
  border-color: rgba(94, 217, 168, 0.55);
  transform: translateY(-1px);
}

.wiki-stage {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  width: 100%;
  min-width: 0;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  align-items: stretch;
}
@media (min-width: 900px) {
  .wiki-stage {
    grid-template-columns: 1.3fr 1fr !important;
  }
}

.wiki-feed-col {
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.wiki-list-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  padding: 0 4px 8px 0;
  border: none;
  background: transparent;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.wiki-list-panel::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.wiki-item {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
  box-sizing: border-box;
  flex-shrink: 0;
}
.wiki-item:hover {
  background: rgba(255, 255, 255, 0.035);
  border-color: rgba(94, 217, 168, 0.3);
  transform: translateY(-2px);
}
.wiki-item-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.wiki-item-body { flex: 1; min-width: 0; }
.wiki-item-title {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.4;
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
}
.wiki-item-summary {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.wiki-item-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.wiki-item-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.wiki-item-time { font-size: 11px; color: var(--muted); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important; }
.wiki-item-arrow {
  color: #5ED9A8;
  flex-shrink: 0;
  margin-top: 2px;
  opacity: 0.55;
  transition: opacity 0.15s, transform 0.15s;
}
.wiki-item:hover .wiki-item-arrow {
  opacity: 1;
  transform: translateX(2px);
}
.wiki-empty {
  padding: 40px 18px;
  text-align: center;
  color: var(--muted);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.wiki-aside-col {
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.wiki-aside-col::-webkit-scrollbar { display: none; width: 0; height: 0; }

.wiki-aside-card {
  padding: 16px;
  border-radius: 10px;
  flex-shrink: 0;
}
.wiki-aside-card--soft {
  border: 1px solid rgba(94, 217, 168, 0.14);
  background: rgba(255, 255, 255, 0.02);
}
.wiki-aside-card--guide {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
}
.wiki-aside-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.wiki-aside-head--muted { color: var(--muted); font-weight: 550; }
.wiki-aside-subhead {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 14px 0 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}

.wiki-stats {
  display: flex;
  align-items: stretch;
  gap: 0;
  margin-bottom: 14px;
  padding: 10px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.wiki-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.wiki-stat-label {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.02em;
}
.wiki-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #5ED9A8;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
  letter-spacing: -0.02em;
}
.wiki-stat-divider {
  width: 1px;
  margin: 2px 14px;
  background: rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.wiki-hot-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.wiki-hot-link {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 4px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  text-align: left;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
  transition: background 0.15s;
}
.wiki-hot-link:hover { background: rgba(94, 217, 168, 0.06); }
.wiki-hot-title {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wiki-hot-arrow {
  flex-shrink: 0;
  color: #5ED9A8;
  opacity: 0.5;
  transition: opacity 0.15s, transform 0.15s;
}
.wiki-hot-link:hover .wiki-hot-arrow {
  opacity: 1;
  transform: translateX(2px);
}
.wiki-hot-empty {
  font-size: 12px;
  color: var(--muted);
  padding: 8px 4px;
}

.wiki-guide-text {
  margin: 0 0 10px;
  font-size: 12px;
  line-height: 1.65;
  color: var(--muted);
}
.wiki-guide-mini {
  margin: 0 0 14px;
  padding-left: 16px;
  font-size: 11px;
  line-height: 1.7;
  color: var(--muted);
  opacity: 0.9;
}
.wiki-guide-link {
  display: inline-flex;
  align-items: center;
  padding: 0;
  border: none;
  background: transparent;
  color: #5ED9A8;
  font-size: 12px;
  font-weight: 500;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
  cursor: pointer;
  opacity: 0.9;
  transition: opacity 0.15s, transform 0.15s;
}
.wiki-guide-link:hover {
  opacity: 1;
  transform: translateX(2px);
}

/* Chip / Tag — 薄荷绿晶片，禁粉 */
.wiki-layout :deep(.link-code),
.wiki-layout :deep(.item-code),
.wiki-layout .link-code,
.wiki-layout .item-code,
.wiki-layout .chip-cut,
.wiki-doc-chip {
  background: rgba(94, 217, 168, 0.1) !important;
  color: #5ED9A8 !important;
  border: 1px solid rgba(94, 217, 168, 0.25) !important;
}
.wiki-layout :deep(.n-tag) {
  background: rgba(94, 217, 168, 0.08) !important;
  color: #5ED9A8 !important;
  border: 1px solid rgba(94, 217, 168, 0.22) !important;
}
</style>
