<template>
  <div
    class="bulletin-layout layout-with-sidebar lab-deck"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <aside class="bulletin-sidebar sidebar-rail">
      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/bulletin" class="sidebar-title sidebar-rail-title">公告中心</router-link>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">BULLETIN · FEED</p>
      </div>

      <nav class="sidebar-rail-nav">
        <div class="sidebar-group">
          <div class="group-label">概览</div>
          <div class="sidebar-item">
            <span class="item-code">ALL</span>
            <span class="item-title">全部公告</span>
            <span class="item-count">{{ bulletins.length }}</span>
          </div>
          <div class="sidebar-item">
            <span class="item-code">PG</span>
            <span class="item-title">当前页</span>
            <span class="item-count">{{ pagedBulletins.length }}</span>
          </div>
          <router-link
            v-if="isAdmin"
            to="/bulletin/create"
            class="sidebar-item"
          >
            <span class="item-code">NEW</span>
            <span class="item-title">发布公告</span>
            <span class="item-count">→</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-links sidebar-rail-footer">
        <router-link to="/home" class="sidebar-link">
          <span class="link-code">HOM</span>
          <span>返回首页</span>
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

    <main class="bulletin-main sidebar-main">
      <div class="bulletin-container">
      <header class="matrix-page-head">
        <p class="matrix-page-prompt">公告栏 · BULLETIN</p>
        <h2 class="matrix-page-title">公告列表</h2>
        <p class="matrix-page-desc">平台公告 · 赛事通知 · 更新动态</p>
      </header>

      <n-spin :show="loading">
        <div v-if="pagedBulletins.length" class="bulletin-list">
          <article
            v-for="item in pagedBulletins"
            :key="item.id"
            class="bulletin-item"
            @click="openDetail(item)"
          >
            <div class="item-head">
              <span class="item-tag">BUL</span>
              <div class="item-main">
                <h2 class="bulletin-title">{{ item.title }}</h2>
                <p v-if="item.summary" class="bulletin-summary">{{ item.summary }}</p>
                <div class="item-foot">
                  <time class="bulletin-date">{{ formatDate(item.created_at || item.published_at) }}</time>
                  <span class="item-link">阅读全文 →</span>
                </div>
              </div>
            </div>
          </article>
        </div>
        <div v-else-if="!loading" class="empty-state">
          <p>暂无公告</p>
          <span class="muted">管理员可在后台发布平台公告</span>
        </div>
      </n-spin>

      <n-pagination
        v-if="bulletins.length > pageSize"
        v-model:page="page"
        :page-size="pageSize"
        :item-count="bulletins.length"
        class="bulletin-pagination"
      />
      </div>
    </main>

    <n-modal v-model:show="showDetail" preset="card" :title="selected?.title" style="max-width: 640px">
      <div v-if="selected" class="detail-content">
        <time class="detail-date">{{ formatDate(selected.created_at || selected.published_at) }}</time>
        <div class="detail-body markdown-body" v-html="renderedContent"></div>
      </div>
    </n-modal>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NSpin, NModal, NPagination } from 'naive-ui'
import { unwrapList } from '../utils/unwrap'
import { useCollapsibleSidebar } from '@/composables/useCollapsibleSidebar'

export default {
  name: 'Bulletin',
  components: { NSpin, NModal, NPagination },
  setup() {
    const axios = inject('axios')
    const router = useRouter()
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_bulletin_sidebar')
    const loading = ref(false)
    const bulletins = ref([])
    const showDetail = ref(false)
    const selected = ref(null)
    const page = ref(1)
    const pageSize = 10
    const isAdmin = ref(false)

    try {
      const u = JSON.parse(localStorage.getItem('neepu_user') || '{}')
      isAdmin.value = !!u.is_admin
    } catch { /* ignore */ }

    const pagedBulletins = computed(() => {
      const start = (page.value - 1) * pageSize
      return bulletins.value.slice(start, start + pageSize)
    })

    const renderedContent = computed(() => {
      const raw = selected.value?.content || ''
      try { return parseMarkdownSafe(raw) } catch { return '' }
    })

    function formatDate(d) {
      if (!d) return ''
      try {
        return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
      } catch { return d }
    }

    function openDetail(item) {
      if (item?.id) {
        router.push(`/bulletin/${item.id}`)
        return
      }
      selected.value = item
      showDetail.value = true
    }

    async function load() {
      loading.value = true
      try {
        const { data } = await axios.get('/api/platform/bulletins')
        bulletins.value = unwrapList(data)
      } catch {
        bulletins.value = []
      } finally {
        loading.value = false
      }
    }

    onMounted(load)

    return {
      loading, bulletins, pagedBulletins, page, pageSize,
      showDetail, selected, renderedContent, formatDate, openDetail, isAdmin,
      collapsed, toggleSidebar,
    }
  },
}
</script>

<style scoped>
.bulletin-layout {
  width: 100%;
  min-height: calc(100vh - var(--nav-height, 56px) - 52px);
  margin: 0;
}

.sidebar-prompt {
  margin: 0 0 6px;
}

.sidebar-head h2 {
  margin: 0;
  font-size: 1rem;
  color: var(--primary);
  font-weight: 700;
}

.sidebar-desc {
  margin: 4px 0 16px;
  font-size: 10px;
  letter-spacing: 0.1em;
  color: var(--muted);
  text-transform: uppercase;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.sidebar-row {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 2px;
  border: 1px solid transparent;
  font-size: var(--text-sm);
  color: var(--muted);
}

.sidebar-row--action {
  text-decoration: none;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.sidebar-row--action:hover {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}

.sidebar-row--action:hover .link-code {
  color: var(--primary);
}

.link-code {
  font-family: var(--font-ui);
}

.row-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-value {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}

.row-arrow {
  font-size: var(--text-xs);
  color: var(--muted);
}

.sidebar-link {
  display: grid;
  grid-template-columns: 36px 1fr;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 2px;
  border: 1px solid transparent;
  color: var(--muted);
  text-decoration: none;
  font-size: var(--text-sm);
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

.bulletin-layout {
  height: calc(100vh - var(--nav-height, 72px));
  max-height: calc(100vh - var(--nav-height, 72px));
  overflow: hidden;
}
.bulletin-main {
  overflow: auto;
  min-height: 0;
  width: 100%;
}
.bulletin-container {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  padding: 8px 8px 24px;
  box-sizing: border-box;
}
.bulletin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: none;
  width: 100%;
}

.bulletin-item {
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--card-radius);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  padding: 12px 16px;
  height: auto;
}

.bulletin-item:hover {
  border-color: rgba(var(--primary-rgb), 0.22);
  background: rgba(255, 255, 255, 0.035);
}

.item-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.item-tag {
  flex-shrink: 0;
  margin-top: 3px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #5ED9A8 !important;
  background: rgba(94, 217, 168, 0.1) !important;
  border: 1px solid rgba(94, 217, 168, 0.25) !important;
  border-radius: var(--radius-pill);
  font-family: var(--font-ui);
}

.item-main {
  flex: 1;
  min-width: 0;
}

.bulletin-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
  line-height: 1.45;
  word-break: break-word;
}

.bulletin-summary {
  margin: 6px 0 0;
  font-size: var(--text-sm);
  color: var(--muted);
  line-height: 1.5;
}

.item-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.bulletin-date {
  font-size: var(--text-xs);
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

.item-link {
  font-size: var(--text-xs);
  color: var(--primary);
}

.empty-state {
  padding: 48px 24px;
  color: var(--muted);
  border: 1px dashed var(--border);
  border-radius: 2px;
  text-align: left;
  max-width: none;
  width: 100%;
}

.muted {
  font-size: var(--text-sm);
  display: block;
  margin-top: 8px;
}

.detail-date {
  font-size: var(--text-sm);
  color: var(--muted);
  display: block;
  margin-bottom: 16px;
}

.bulletin-pagination {
  margin-top: 20px;
  justify-content: flex-start;
}


</style>
