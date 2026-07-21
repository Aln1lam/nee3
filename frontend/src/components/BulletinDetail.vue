<template>
  <MatrixShell
    prompt=""
    title="公告详情"
    subtitle="BULLETIN · DETAIL"
    :page-prompt="pagePrompt"
    :page-title="bulletin?.title || '公告详情'"
    page-desc="平台公告 · 全文阅读"
  >
    <template #sidebar-footer>
      <router-link to="/bulletin" class="sidebar-link">
        <span class="link-code">BAK</span>
        <span>返回列表</span>
      </router-link>
      <router-link to="/bulletin" class="sidebar-link">
        <span class="link-code">LST</span>
        <span>公告列表</span>
      </router-link>
    </template>

    <n-spin :show="loading">
      <article v-if="bulletin" class="bulletin-article matrix-panel">
        <time class="date">{{ formatDate(bulletin.created_at || bulletin.published_at) }}</time>
        <div class="content markdown-body" v-html="rendered"></div>
      </article>
      <div v-else-if="!loading" class="empty matrix-panel">
        <p class="matrix-page-prompt">公告不存在或已下线</p>
        <p>公告不存在</p>
        <n-button @click="$router.push('/bulletin')">返回列表</n-button>
      </div>
    </n-spin>
  </MatrixShell>
</template>

<script>
import { ref, computed, inject, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NSpin, NButton } from 'naive-ui'
import { MatrixShell } from '@/components/shared'

export default {
  name: 'BulletinDetail',
  components: { NSpin, NButton, MatrixShell },
  props: { id: { type: [String, Number], default: null } },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const loading = ref(false)
    const bulletin = ref(null)

    const bulletinId = computed(() => props.id || route.params.id)
    const pagePrompt = computed(() => `cat /bulletin/${bulletinId.value}`)

    const rendered = computed(() => {
      const raw = bulletin.value?.content || ''
      try { return parseMarkdownSafe(raw) } catch { return '' }
    })

    function formatDate(d) {
      if (!d) return ''
      try { return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) } catch { return d }
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

    return { loading, bulletin, rendered, formatDate, pagePrompt }
  },
}
</script>

<style scoped>
.bulletin-article { max-width: none; width: 100%; }
.date { color: var(--muted); font-size: 14px; display: block; margin-bottom: 16px; }
.content { line-height: 1.8; }
.content :deep(pre) { background: var(--code-bg); padding: 12px; border-radius: var(--card-radius); overflow-x: auto; }
.empty { text-align: center; padding: 40px; color: var(--muted); max-width: none; width: 100%; }
</style>
