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

      <div class="sidebar-links sidebar-rail-footer">
        <button type="button" class="sidebar-link" @click="clearCategory">
          <span class="link-code">CLR</span>
          <span>清除筛选</span>
        </button>
        <router-link to="/home" class="sidebar-link">
          <span class="link-code">HOM</span>
          <span>返回首页</span>
        </router-link>
        <router-link to="/training" class="sidebar-link">
          <span class="link-code">TRN</span>
          <span>训练靶场</span>
        </router-link>
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
      <header class="matrix-page-head">
        <p class="matrix-page-prompt">知识库 · WIKI</p>
        <h2 class="matrix-page-title">Wiki 文档</h2>
        <p class="matrix-page-desc">
          <span v-if="selectedTag">当前标签：{{ selectedTag }}（{{ articles.length }} 篇）</span>
          <span v-else>WriteUp · 教程 · 知识沉淀（{{ articles.length }} 篇）</span>
        </p>
      </header>

      <div class="wiki-toolbar matrix-panel">
        <n-input
          v-model:value="q"
          placeholder="搜索标题或内容"
          size="small"
          @keyup.enter="fetch"
        />
        <div class="wiki-search-actions">
          <n-button size="small" type="primary" @click="fetch">搜索</n-button>
          <n-button size="small" secondary @click="$router.push('/knowledge/new')">上传</n-button>
        </div>
      </div>

      <div class="wiki-list-panel matrix-panel">
        <template v-if="articles.length">
          <article
            v-for="a in articles"
            :key="a.id"
            class="wiki-item"
            @click="goArticle(a.id)"
          >
            <div class="wiki-item-head">
              <span class="link-code">DOC</span>
              <div class="wiki-item-body">
                <h3 class="wiki-item-title">{{ a.title }}</h3>
                <p v-if="a.summary" class="wiki-item-summary">{{ a.summary }}</p>
                <div class="wiki-item-foot">
                  <div class="wiki-item-tags">
                    <n-tag v-for="t in renderTags(a)" :key="a.id + '-tag-' + t" size="small" round>{{ t }}</n-tag>
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
    </main>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, inject, watch } from 'vue'
import axiosGlobal from 'axios'
import { TAGS } from '../services/tags'
import { useRoute, useRouter } from 'vue-router'
import { NInput, NButton, NTag } from 'naive-ui'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'
import { formatWikiTags, formatWikiTime } from '../utils/wikiDisplay'

export default {
  components: { NInput, NButton, NTag },
  setup() {
    const axios = inject('axios') || axiosGlobal
    const route = useRoute()
    const router = useRouter()
    const articles = ref([])
    const q = ref('')
    const selectedTag = ref('')
    const categories = TAGS
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_wiki_sidebar_collapsed')

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
    }
  },
}
</script>

<style scoped>
.wiki-layout {
  width: 100%;
  min-height: calc(100vh - var(--nav-height, 72px));
  margin: 0;
}

.wiki-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--fib-13, 13px);
  padding: var(--fib-13, 13px) var(--fib-21, 21px);
  margin-bottom: var(--fib-21, 21px);
}

.wiki-toolbar .n-input {
  flex: 1;
  min-width: 200px;
}

.wiki-search-actions {
  display: flex;
  gap: 8px;
}

.wiki-main {
  flex: 1;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
}

/* 多列卡片铺满主区，避免宽屏上「左竖条 + 大片空白」 */
.wiki-list-panel {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
  gap: var(--fib-21, 21px);
  padding: var(--fib-13, 13px);
  border: none;
  background: transparent;
  box-shadow: none;
}

.wiki-item {
  padding: var(--fib-21, 21px);
  border: 1px solid var(--border);
  border-radius: var(--card-radius, 12px);
  background: var(--r2s-card, var(--card-bg, #fff));
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
  min-height: 148px;
  box-sizing: border-box;
}

.wiki-item:hover {
  background: var(--hover);
  border-color: rgba(var(--primary-rgb, 8, 145, 237), 0.35);
  transform: translateY(-2px);
}

.wiki-item-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  height: 100%;
}

.wiki-item-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.wiki-item-title {
  margin: 0 0 8px;
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: 1.35;
}

.wiki-item-summary {
  margin: 0 0 12px;
  font-size: var(--text-sm);
  color: var(--muted);
  line-height: var(--text-sm--line-height);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.wiki-item-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
}

.wiki-item-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.wiki-item-time {
  font-size: var(--text-xs);
  color: var(--muted);
}

.wiki-item-arrow {
  color: var(--primary);
  font-size: var(--text-lg);
  flex-shrink: 0;
  margin-top: 2px;
}

.wiki-empty {
  grid-column: 1 / -1;
  padding: 48px 18px;
  text-align: center;
  color: var(--muted);
  font-size: var(--text-sm);
  border: 1px dashed var(--border);
  border-radius: var(--card-radius, 12px);
  background: var(--r2s-card, var(--card-bg, #fff));
}
</style>
