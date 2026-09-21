<template>
  <div
    class="wiki-layout layout-with-sidebar lab-deck wiki-detail-page"
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
        <!-- 扁平化文章列表：无分类折叠 -->
        <div class="sidebar-article-list custom-scrollbar">
          <div
            v-for="item in allArticles"
            :key="item.id"
            class="article-item"
            :class="{ active: isActiveArticle(item.id) }"
            @click="switchArticle(item.id)"
          >
            <span class="truncate">{{ item.title }}</span>
          </div>
          <div v-if="!allArticles.length" class="sidebar-list-empty">暂无文章</div>
        </div>
      </div>

      <!-- WKI 知识库返回 -->
      <div class="sidebar-rail-footer sidebar-footer">
        <router-link to="/wiki" class="sidebar-link return-btn">
          <span class="link-code">WKI</span>
          <span>知识库</span>
        </router-link>
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

    <main class="wiki-main sidebar-main wiki-detail-main">
      <div v-if="loading" class="detail-loading">
        <n-spin />
      </div>

      <div v-else class="article-body-wrap">
        <div class="article-panel">
          <!-- 标题仅在右侧主内容卡片头部，卡片外无悬空标题 -->
          <header v-if="article" class="article-card-header">
            <h1 class="article-title">{{ article.title }}</h1>
            <div class="article-meta">
              <span v-if="article.created_at">发布时间: {{ formatDate(article.created_at) }}</span>
              <span v-if="article.author_name">作者: {{ article.author_name }}</span>
            </div>
          </header>

          <template v-if="loadingContent">
            <div class="detail-loading">
              <n-spin />
            </div>
          </template>

          <template v-else-if="article?.content">
            <div class="article-content article-content--full">
              <Article :key="'md-' + currentArticleId" :content="article.content" :show-toc="true" />
            </div>
          </template>

          <template v-else-if="fileUrl">
            <div class="article-file-wrap">
              <template v-if="fileIsPdf">
                <div class="viewer-stage">
                  <div class="pdf-viewer-container">
                    <div class="pdf-toolbar">
                      <a :href="fileUrl" target="_blank" rel="noopener noreferrer" class="pdf-action-btn">
                        <span>🔗</span> 新窗口打开
                      </a>
                      <a :href="fileUrl" download class="pdf-action-btn">
                        <span>📥</span> 下载PDF
                      </a>
                    </div>
                    <div class="pdf-iframe-wrapper">
                      <iframe
                        :src="fileUrl"
                        class="pdf-iframe"
                        frameborder="0"
                        title="PDF查看器"
                      ></iframe>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="article-content article-content--full">
                  <Article :key="'file-' + currentArticleId" :content="fileContent" :show-toc="true" />
                </div>
              </template>
            </div>
          </template>

          <template v-else>
            <div class="detail-error">
              ⚠️ 文章内容加载失败，请重试
            </div>
          </template>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NSpin } from 'naive-ui'
import { Article } from '@/components/shared'

export default {
  props: ['id'],
  components: { NSpin, Article },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const collapsed = ref(false)
    const toggleSidebar = () => { collapsed.value = !collapsed.value }

    const allArticles = ref([])
    const article = ref(null)
    const loading = ref(true)
    const loadingContent = ref(false)
    const fileUrl = ref('')
    const fileContent = ref('')
    const fileIsPdf = ref(false)

    const currentArticleId = computed(() => {
      const raw = props.id ?? route.params.id
      return raw != null ? String(raw) : ''
    })

    function isActiveArticle(id) {
      return String(id) === currentArticleId.value
    }

    function switchArticle(id) {
      if (String(id) === currentArticleId.value) return
      router.push(`/wiki/${id}`).catch(() => null)
    }

    async function fetchAllArticles() {
      try {
        const r = await axios.get('/api/articles/', { params: { per_page: 200 } })
        allArticles.value = r.data.data?.items || r.data.items || []
      } catch (err) {
        console.error('获取文章列表失败:', err)
        allArticles.value = []
      }
    }

    async function loadFileContent() {
      if (!fileUrl.value) return
      loadingContent.value = true
      try {
        const response = await axios.get(fileUrl.value)
        fileContent.value = typeof response.data === 'string'
          ? response.data
          : (response.data?.content || '')
      } catch (err) {
        console.error('文件加载失败:', err)
        fileContent.value = ''
      } finally {
        loadingContent.value = false
      }
    }

    async function loadArticle(id, { initial = false } = {}) {
      if (!id) return
      if (initial) loading.value = true
      else loadingContent.value = true

      fileUrl.value = ''
      fileContent.value = ''
      fileIsPdf.value = false

      try {
        const key = String(id)
        const isNumericId = /^\d+$/.test(key)
        const res = isNumericId
          ? await axios.get(`/api/articles/${key}`)
          : await axios.get(`/api/articles/wiki/${encodeURIComponent(key)}`)
        const payload = res.data?.data != null && res.data?.code != null ? res.data.data : res.data
        article.value = payload

        if (!article.value.content && article.value.resource_id) {
          try {
            const fileRes = await axios.get(`/api/resources/${article.value.resource_id}`)
            const filename = fileRes.data.filename || ''
            fileUrl.value = `/api/resources/${article.value.resource_id}/content`
            if (/\.pdf$/i.test(filename)) {
              fileIsPdf.value = true
            } else {
              await loadFileContent()
            }
          } catch (err) {
            console.error('获取文件资源失败:', err)
          }
        }
      } catch (err) {
        console.error('获取文章失败:', err)
        if (initial) article.value = null
      } finally {
        loading.value = false
        loadingContent.value = false
      }
    }

    function formatDate(isoString) {
      if (!isoString) return ''
      return new Date(isoString).toLocaleDateString('zh-CN')
    }

    onMounted(async () => {
      await Promise.all([
        fetchAllArticles(),
        loadArticle(props.id || route.params.id, { initial: true }),
      ])
    })

    watch(
      () => props.id ?? route.params.id,
      (id, prev) => {
        if (id == null || String(id) === String(prev)) return
        loadArticle(id)
      },
    )

    return {
      allArticles,
      article,
      loading,
      loadingContent,
      fileUrl,
      fileContent,
      fileIsPdf,
      formatDate,
      collapsed,
      toggleSidebar,
      currentArticleId,
      isActiveArticle,
      switchArticle,
    }
  }
}
</script>

<style scoped>
.wiki-detail-page {
  width: 100%;
  height: 100%;
  max-height: 100%;
  min-height: 0;
  box-sizing: border-box;
  overflow: hidden !important;
}

.wiki-detail-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 16px 20px 24px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
}
.wiki-detail-main::-webkit-scrollbar { width: 6px; }
.wiki-detail-main::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}
.wiki-detail-main::-webkit-scrollbar-track { background: transparent; }

.detail-loading {
  text-align: center;
  padding: 40px;
}
.detail-error {
  color: #d32f2f;
  padding: 16px;
  border: 1px solid #d32f2f;
  border-radius: 4px;
}

/* 扁平化文章列表 */
.sidebar-rail-nav {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-article-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 10px 0 12px;
  padding: 0 8px;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: calc(100vh - 200px);
  flex: 1 1 auto;
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}
.sidebar-article-list.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.sidebar-article-list.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.14);
  border-radius: 2px;
}
.sidebar-article-list.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.article-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.4;
  color: #9ca3af;
  border: 1px solid transparent;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.article-item:hover {
  color: #e5e7eb;
  background: rgba(255, 255, 255, 0.05);
}
.article-item.active {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  font-weight: 600;
  border-color: rgba(16, 185, 129, 0.3);
}
.article-item .truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}
.sidebar-list-empty {
  padding: 8px 12px;
  font-size: 12px;
  color: var(--muted);
}

.sidebar-rail-footer {
  margin-top: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.sidebar-footer-copy {
  font-size: 11px;
  color: var(--muted);
  line-height: 1.4;
}
.sidebar-footer-copy a {
  color: inherit;
  text-decoration: none;
}
.sidebar-footer-copy a:hover {
  color: #5ED9A8;
}

.article-body-wrap {
  display: block;
  flex: 1;
  min-height: 0;
}
.article-panel {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  padding: 20px 24px 28px;
  box-sizing: border-box;
}
.article-card-header {
  text-align: left;
  margin: 0 0 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.article-title {
  margin: 0 0 8px;
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1.25;
  color: var(--text);
}
.article-meta {
  color: var(--muted);
  font-size: 13px;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 16px;
}
.article-content--full {
  width: 100%;
  max-width: none;
  margin: 0;
}
.article-file-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
}
.viewer-stage {
  width: 100%;
  min-height: 72vh;
  border: 1px solid rgba(0, 0, 0, 0.06);
  padding: 0;
  margin: 0 0 12px;
  box-sizing: border-box;
  background-color: #ffffff;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.pdf-viewer-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.pdf-toolbar {
  display: flex;
  gap: var(--fib-13);
  padding: var(--fib-13) var(--fib-21);
  background: var(--hover);
  border-bottom: 1px solid var(--border);
}
.pdf-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: var(--fib-8) var(--fib-13);
  background: var(--card-bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}
.pdf-action-btn:hover {
  background: #1976d2;
  color: #fff;
  border-color: #1976d2;
}
.pdf-action-btn span { font-size: 16px; }
.pdf-iframe-wrapper {
  width: 100%;
  height: calc(100vh - 280px);
  min-height: 600px;
  background: #525659;
  display: flex;
  justify-content: center;
}
.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

@media (max-width: 900px) {
  .wiki-sidebar { display: none; }
  .sidebar-collapse-trigger { display: none; }
}
</style>
