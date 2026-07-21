<template>
  <div class="error-page">
    <header class="matrix-page-head error-head">
      <h1 class="matrix-page-title error-title">{{ title }}</h1>
      <p v-if="isTeapot" class="matrix-page-desc teapot-hint">☕ 我是茶壶，不能冲泡咖啡。</p>
      <p v-else class="matrix-page-desc">{{ description }}</p>
    </header>
    <div class="error-code">{{ code }}</div>
    <div class="error-actions">
      <n-button type="primary" @click="$router.push('/')">返回首页</n-button>
      <n-button @click="$router.back()">返回上一</n-button>
    </div>
    <div v-if="showTrace" class="error-trace-hint muted">错误码 {{ code }}</div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NButton } from 'naive-ui'

const PAGES = {
  '401': { title: '未授权', desc: '请先登录后再访问此页面' },
  '403': { title: '禁止访问', desc: '权限不足 · 请联系管理员获取权限' },
  '404': { title: '未找到', desc: '页面不存在或已被移除' },
  '412': { title: '前置条件失败', desc: '请求未满足服务器前置条件' },
  '418': { title: '我是茶壶', desc: '服务器拒绝冲泡咖啡（RFC 2324 · 418 I\'m a teapot）' },
  '500': { title: '服务器错误', desc: '服务器内部出错，请稍后重试' },
  '502': { title: '网关错误', desc: '上游服务不可用，请稍后重试' },
  unknown: { title: '出错了', desc: '发生未知错误' },
}

export default {
  name: 'ErrorPage',
  components: { NButton },
  setup() {
    const route = useRoute()
    const code = computed(() => route.params.code || 'unknown')
    const info = computed(() => PAGES[code.value] || PAGES.unknown)
    const title = computed(() => info.value.title)
    const description = computed(() => info.value.desc)
    const showTrace = computed(() => ['500', '502', 'unknown'].includes(code.value))
    const isTeapot = computed(() => code.value === '418')
    return { code, title, description, showTrace, isTeapot }
  },
}
</script>

<style scoped>
.error-page {
  min-height: calc(100vh - var(--nav-height, 64px) - 80px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  font-family: var(--font-ui);
}
.error-head {
  text-align: center;
  border-bottom: none;
  margin-bottom: 8px;
  padding-bottom: 0;
}
.error-code {
  font-size: clamp(4rem, 12vw, 8rem);
  font-weight: 700;
  color: var(--primary);
  line-height: 1;
  opacity: 0.85;
  font-family: var(--font-mono);
}
.error-title {
  margin: 0;
  font-size: 1.5rem;
}
.teapot-hint { font-style: italic; }
.error-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
.error-trace-hint {
  margin-top: 24px;
  font-size: var(--text-sm);
  color: var(--muted);
}
</style>
