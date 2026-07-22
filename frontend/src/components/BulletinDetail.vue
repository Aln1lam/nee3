<template>
  <n-spin :show="loading">
    <article v-if="bulletin" class="bulletin-detail">
      <header class="detail-head">
        <h1 class="detail-title">{{ bulletin.title }}</h1>
        <div class="detail-meta">
          <time class="detail-date">{{ formatDate(bulletin.created_at || bulletin.published_at) }}</time>
          <span class="detail-tag">公告</span>
        </div>
      </header>
      <div class="detail-body markdown-body" v-html="rendered"></div>
    </article>
    <div v-else-if="!loading" class="detail-empty">
      <p class="detail-empty-title">公告不存在或已下线</p>
      <n-button @click="$router.push('/bulletin')">返回全部公告</n-button>
    </div>
  </n-spin>
</template>

<script>
import { ref, computed, inject, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NSpin, NButton } from 'naive-ui'

export default {
  name: 'BulletinDetail',
  components: { NSpin, NButton },
  props: { id: { type: [String, Number], default: null } },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const loading = ref(false)
    const bulletin = ref(null)
    const bulletinId = computed(() => props.id || route.params.id)

    const rendered = computed(() => {
      const raw = bulletin.value?.content || ''
      try { return parseMarkdownSafe(raw) } catch { return '' }
    })

    function formatDate(d) {
      if (!d) return ''
      try {
        return new Date(d).toLocaleDateString('zh-CN', {
          year: 'numeric', month: '2-digit', day: '2-digit',
        })
      } catch { return d }
    }

    async function load() {
      loading.value = true
      try {
        const { data } = await axios.get(`/api/platform/bulletins/${bulletinId.value}`)
        bulletin.value = data?.data || data
      } catch {
        bulletin.value = null
      } finally {
        loading.value = false
      }
    }

    onMounted(load)
    watch(bulletinId, load)

    return { loading, bulletin, rendered, formatDate }
  },
}
</script>

<style scoped>
.bulletin-detail {
  width: 100%;
  max-width: none;
  padding: 24px 28px 40px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.detail-head {
  margin: 0 0 24px;
  padding: 0 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.detail-title {
  margin: 0 0 12px;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.02em;
  color: var(--text, #e8eaed);
}
.detail-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.detail-date {
  font-size: 13px;
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
}
.detail-tag {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 600;
  color: #5ED9A8;
  background: rgba(94, 217, 168, 0.1);
  border: 1px solid rgba(94, 217, 168, 0.28);
  border-radius: 4px;
}
.detail-body {
  width: 100%;
  padding: 4px 0 0;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  font-size: 15px;
  line-height: 1.8;
  color: var(--text, #e8eaed);
}
.detail-body :deep(*) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}
.detail-body :deep(p) { margin: 0 0 1em; line-height: 1.8; }
.detail-body :deep(ul),
.detail-body :deep(ol) {
  margin: 0 0 1.1em;
  padding-left: 1.6em;
  line-height: 1.8;
}
.detail-body :deep(li) {
  margin: 0.35em 0;
  padding-left: 0.2em;
  line-height: 1.8;
}
.detail-body :deep(li::marker) { color: #5ED9A8; }
.detail-body :deep(a) {
  color: #5ED9A8 !important;
  text-decoration: underline !important;
  text-decoration-color: rgba(94, 217, 168, 0.55) !important;
  text-underline-offset: 3px;
}
.detail-body :deep(a:hover) {
  color: #7ee7bc !important;
  text-decoration-color: #5ED9A8 !important;
}
.detail-body :deep(h1),
.detail-body :deep(h2),
.detail-body :deep(h3),
.detail-body :deep(h4) {
  margin: 1.4em 0 0.55em;
  font-weight: 650;
  line-height: 1.35;
}
.detail-body :deep(pre) {
  background: rgba(20, 26, 33, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 0 0 1.1em;
}
.detail-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
  font-size: 0.92em;
}
.detail-body :deep(blockquote) {
  margin: 0 0 1.1em;
  padding: 8px 14px;
  border-left: 3px solid rgba(94, 217, 168, 0.45);
  background: rgba(94, 217, 168, 0.05);
  color: #9ca3af;
}
.detail-empty { padding: 48px 24px; color: #9ca3af; }
.detail-empty-title {
  margin: 0 0 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text, #e8eaed);
}
</style>
