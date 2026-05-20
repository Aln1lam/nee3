<template>
  <div class="kb-container">
    <!-- 左侧标签区域将移至中间列（在主内容之后），此处保留空占位以便后续插入 -->

    <aside class="kb-aside kb-aside-left kb-aside-middle">
      <div class="kb-search">
        <n-input v-model:value="q" placeholder="搜索标题或内容" @keyup.enter="fetch" size="small" class="kb-input" />
        <div class="kb-search-actions">
          <n-button size="small" type="primary" @click="fetch">搜索</n-button>
          <n-button size="small" secondary @click="$router.push('/knowledge/new')">上传文件</n-button>
        </div>
      </div>

      <div class="kb-section-title">标签</div>
      <div class="kb-tags">
        <n-button v-for="c in categories" :key="c" class="kb-tag" tertiary @click="selectTag(c)" :class="{ 'selected-tag': selectedTag === c }">{{ c }}</n-button>
      </div>
      <div class="kb-clear"><n-button size="small" tertiary @click="clearCategory">清除标签</n-button></div>
    </aside>

    <main class="kb-main">
      <h2>知识库</h2>
      <div class="kb-meta">
        <span v-if="selectedTag">当前标签：<strong>{{ selectedTag }}</strong> （{{ articles.length }} 条）</span>
        <span v-else>未选择标签，显示全部（{{ articles.length }} 条）</span>
      </div>
      <div class="kb-list-panel">
        <n-list>
        <template v-if="articles.length">
          <n-list-item v-for="a in articles" :key="a.id" class="kb-list-item">
            <div class="kb-list-row">
              <div class="kb-left">
                <div class="kb-main-info">
                  <div class="kb-title"><strong>{{ a.title }}</strong></div>
                  <div class="kb-summary">{{ a.summary }}</div>
                </div>
              </div>

              <div class="kb-middle">
                <div class="kb-item-tags inline">
                  <n-tag v-for="t in renderTags(a)" :key="a.id+'-tag-'+t" size="small">{{ t }}</n-tag>
                </div>
              </div>

              <div class="kb-right">
                <div class="kb-time">{{ a.created_at }}</div>
                <div>
                  <a href="#" class="kb-read-btn" @click.prevent="goArticle(a.id)">点击阅读</a>
                </div>
              </div>
            </div>
          </n-list-item>
        </template>
        <template v-else>
          <div class="kb-empty">暂无相关文章。</div>
        </template>
        </n-list>
      </div>
    </main>

    

    <aside class="kb-aside kb-aside-right">
      <div class="kb-section-title">推荐文章</div>
      <div class="kb-recommend">
        <n-card v-for="a in articles.slice(0,5)" :key="'side-'+a.id" size="small" :bordered="false" class="kb-card">
          <div class="kb-card-row">
            <n-avatar size="40">{{ (a.title||'W').slice(0,1).toUpperCase() }}</n-avatar>
            <div class="kb-card-body">
              <div class="kb-card-title">{{ a.title }}</div>
              <div class="kb-card-meta">作者: {{ a.author_name || '未知作者' }} • {{ a.created_at }}</div>
              <div class="kb-card-tags"><n-tag v-for="t in (a.tags||'').split(',')" :key="a.id+'-t-'+t" size="small">{{ t }}</n-tag></div>
            </div>
          </div>
        </n-card>
      </div>
    </aside>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, inject, watch } from 'vue'
import axiosGlobal from 'axios'
import { TAGS } from '../services/tags'
import { useRoute, useRouter } from 'vue-router'
import { NInput, NButton, NList, NListItem, NCard, NAvatar, NTag } from 'naive-ui'
export default {
  components: { NInput, NButton, NList, NListItem, NCard, NAvatar, NTag },
  setup() {
  const axios = inject('axios') || axiosGlobal
  const route = useRoute()
  const router = useRouter()
    const articles = ref([])
    const recentArticles = ref([])
  const q = ref('')
  const selectedTag = ref('')
  const categories = TAGS

    function selectTag(c) {
      console.debug('selectTag clicked', c)
      // clear free-text search when selecting a tag so we show tag results
      q.value = ''
      selectedTag.value = c
      try { router.push({ path: '/knowledge', query: { tag: c } }) } catch (e) { console.error(e) }
      fetch()
    }

  function clearCategory() { q.value = ''; selectedTag.value = ''; fetch() }

    async function fetch() {
      try {
        const params = { q: q.value, per_page: 50 }
        if (selectedTag.value) params.tag = selectedTag.value
        console.debug('fetching articles with params', params)
  const r = await axios.get('/api/articles/', { params })
        articles.value = r.data.data?.items || r.data.items || []
        // 如果文章包含 resource_id，尝试并行获取资源元数据以获取可访问的 file URL
        const needs = articles.value.filter(a => a.resource_id)
        if (needs.length) {
          try {
            await Promise.all(needs.map(async (a) => {
              try {
                const rr = await axios.get('/api/resources/' + a.resource_id)
                if (rr && rr.data && rr.data.url) {
                  a.file_url = rr.data.url
                }
              } catch (e) {
                // ignore per-resource errors
              }
            }))
          } catch (e) {
            console.error('fetch resource metas failed', e)
          }
        }
        console.debug('articles fetched', articles.value.length)
      } catch (e) {
        console.error('fetch articles failed', e)
      }
    }

      // Fetch recent articles for the right-side sidebar (always latest, ignore current tag filter)
      async function fetchRecent() {
        try {
          const r = await axios.get('/api/articles/', { params: { per_page: 50 } })
          const items = r.data.items || []
          // sort by created_at desc
          items.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          recentArticles.value = items.slice(0, 5)
        } catch (e) {
          console.error('fetch recent articles failed', e)
          recentArticles.value = []
        }
      }

    function onArticleSaved(e) {
      // optional: could use e.detail.id to scroll or highlight
      fetch()
    }

    function goArticle(id) {
      try { router.push('/knowledge/' + id) } catch (e) { console.error(e) }
    }

    function renderTags(a) {
      const out = []
      // article.tags may be comma-separated
      try {
        if (a.tags) {
          const parts = (a.tags || '').split(',').map(s => s && s.trim()).filter(Boolean)
          out.push(...parts)
        }
      } catch (e) {}
      return out
    }

    // 尝试从文章 body 中提取 PDF 链接，如果没有则返回空
    function extractPdfFromArticle(a) {
      if (!a) return null
      const body = a.body || ''
      // markdown 链接或裸 URL
      const mdPdfRe = /\[[^\]]*\]\(\s*(https?:\/\/[^)]+\/(?:static\/)?uploads\/[^)\s]+\.pdf(?:\?[^)]*)?|\/(?:static\/)?uploads\/[^)\s]+\.pdf(?:\?[^)]*)?)\s*\)/i
      let m = body.match(mdPdfRe)
      if (!m) {
        const plainRe = /(https?:\/\/[^\s]+\/(?:static\/)?uploads\/[\w%\-\.]+\.pdf(?:\?\S*)?)|((?:\/static\/|\/uploads\/)[\w%\-\.]+\.pdf(?:\?\S*)?)/i
        m = body.match(plainRe)
      }
      if (m) {
        let candidate = m[1] || m[2] || m[0]
        if (candidate.startsWith('/')) {
          try {
            const base = (axios && axios.defaults && axios.defaults.baseURL) ? axios.defaults.baseURL : window.location.origin
            candidate = base.replace(/\/$/, '') + candidate
          } catch (e) {}
        }
        return candidate
      }
      // 若文章对象有直接提供的 file_url 字段则使用它（并规范为后端绝对 URL）
      if (a.file_url) {
        let candidate = a.file_url
        if (candidate.startsWith('/')) {
          try {
            const base = (axios && axios.defaults && axios.defaults.baseURL) ? axios.defaults.baseURL : window.location.origin
            candidate = base.replace(/\/$/, '') + candidate
          } catch (e) {}
        }
        return candidate
      }
      return null
    }

    function filenameFromUrl(url) {
      try {
        const u = new URL(url, window.location.origin)
        const p = u.pathname
        return p.substring(p.lastIndexOf('/') + 1)
      } catch (e) {
        return url.split('/').pop()
      }
    }

    function buildPdfLink(a) {
      const pdf = extractPdfFromArticle(a)
      if (!pdf) return ''
      try {
        const u = new URL(pdf, window.location.origin)
        if (selectedTag.value) u.searchParams.set('tag', selectedTag.value)
        u.searchParams.set('file', filenameFromUrl(pdf))
        return u.toString()
      } catch (e) {
        // fallback: append params safely
        let sep = pdf.includes('?') ? '&' : '?'
        const params = []
        if (selectedTag.value) params.push('tag=' + encodeURIComponent(selectedTag.value))
        params.push('file=' + encodeURIComponent(filenameFromUrl(pdf)))
        return pdf + sep + params.join('&')
      }
    }

    onMounted(()=>{
      // apply category from query if present
      if (route.query && route.query.tag) {
        selectedTag.value = route.query.tag
      }
      if (route.query && route.query.q) {
        q.value = route.query.q
      }
      fetch()
       fetchRecent()
      window.addEventListener('neepu_article_saved', onArticleSaved)
    })
    onUnmounted(()=>{ window.removeEventListener('neepu_article_saved', onArticleSaved) })

    // respond to route changes (e.g., user clicked category on Home)
    watch(() => route.query, (nv) => {
      if (nv && nv.tag !== undefined) {
        selectedTag.value = nv.tag || ''
        fetch()
         fetchRecent()
      }
      if (nv && nv.q !== undefined) {
        q.value = nv.q || ''
        fetch()
      }
    })
    return { articles, q, fetch, categories, selectTag, clearCategory, selectedTag, goArticle, buildPdfLink, renderTags }
  }
}
</script>

<style scoped>
.selected-tag {
  background: rgba(0, 120, 212, 0.06);
  border: 1px solid rgba(0,120,212,0.12);
}

/* Use rem/em so fonts and borders scale together with browser zoom */
.kb-container{padding:1rem;display:flex;gap:1.25rem;box-sizing:border-box;max-width:90rem;margin:0 auto;width:100%;--kb-radius:0.5rem}
.kb-aside{box-sizing:border-box}
/* Use flexible sizes so zooming/resizing doesn't make content collapse to a tiny center */
.kb-aside-left{flex:0 0 14rem;min-width:10rem;max-width:22%}
.kb-aside-right{flex:0 0 20rem;min-width:11rem;max-width:28%}
.kb-main{flex:1;min-width:0}
.kb-container *, .kb-container *:before, .kb-container *:after { box-sizing: inherit }

/* Responsive: stack asides below main on narrow screens */
@media (max-width:48rem){
  .kb-container{flex-direction:column;padding:0.75rem}
  .kb-aside-left,.kb-aside-right{flex:0 0 auto;width:100%;max-width:none}
}
.kb-search{margin-bottom:0.75rem}
.kb-input{width:100%}
.kb-search-actions{margin-top:0.5rem;display:flex;gap:0.5rem}
.kb-section-title{font-weight:700;margin-bottom:0.5rem}
.kb-tags{display:flex;flex-direction:column;gap:0.5rem}
.kb-tag{text-align:left;padding:0.45rem;border-radius:calc(var(--kb-radius) / 1.6)}
.selected-tag{background:rgba(0,120,212,0.06);border:0.0625rem solid rgba(0,120,212,0.12)}
.kb-clear{margin-top:0.5rem}
.kb-main{flex:1}
.kb-meta{margin-bottom:0.5rem;color:#444}
.kb-list-item{cursor:pointer}
.kb-list-row{display:flex;justify-content:space-between;align-items:center;padding:0.6rem 0;border-bottom:1px solid rgba(0,0,0,0.06);gap:1rem}
.kb-left{display:flex;align-items:flex-start;gap:0.8rem;min-width:0;flex:1}
.kb-middle{display:flex;align-items:center;justify-content:center;flex:0 0 16rem}
.kb-item-tags.inline{display:flex;gap:0.5rem;align-items:center;justify-content:center}
.kb-main-info{min-width:0}
.kb-main-info .kb-title{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kb-main-info .kb-summary{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#666}
.kb-right{display:flex;flex-direction:column;align-items:flex-end;gap:8px}
.kb-summary{font-size:0.75rem;color:#666}
.kb-time{font-size:0.75rem;color:#999}
.kb-empty{padding:1rem;color:#777}
.kb-recommend{display:flex;flex-direction:column;gap:0.625rem}
.kb-card-row{display:flex;gap:0.625rem;align-items:flex-start}
.kb-card-body{flex:1}
.kb-card-title{font-weight:600}
.kb-card-meta{font-size:0.75rem;color:#666;margin-top:0.25rem}
.kb-card-tags{margin-top:0.375rem;display:flex;gap:0.375rem;flex-wrap:wrap}

/* 阅读按钮样式 */
.kb-read-btn{
  display:inline-block;
  padding:0.35rem 0.6rem;
  background:#1976d2;
  color:#fff;
  border-radius:0.375rem;
  text-decoration:none;
  font-weight:600;
  font-size:0.875rem;
}
.kb-read-btn:hover{opacity:0.95}

.kb-item-tags{display:flex;gap:0.35rem;margin-bottom:0.35rem;flex-wrap:wrap}
.kb-item-tags n-tag{background:rgba(0,0,0,0.04)}

/* Rounded corners for main elements */
.kb-aside, .kb-main, .kb-card, .kb-list-item, .kb-tag, .kb-read-btn, .kb-input {
  border-radius:var(--kb-radius);
}
.kb-list-item{
  padding:0.5rem 0.6rem;
  background:transparent;
  margin:0.25rem 0;
}

/* 白色面板样式：主要内容区域白底、圆角、阴影 */
.kb-list-panel{
  background: #ffffff;
  padding: 0.9rem;
  border-radius: var(--kb-radius);
  box-shadow: 0 6px 18px rgba(14,30,37,0.06);
  max-width: 1000px;
  margin: 0 auto;
}
.kb-aside { padding:0.6rem; }
.kb-aside .kb-section-title{ margin-top:0 }

/* Ensure children follow box-sizing so borders/padding don't break layout when zooming */
.kb-container *, .kb-container *:before, .kb-container *:after { box-sizing: inherit }
</style>
