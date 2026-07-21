<template>
  <MatrixShell
    prompt=""
    title="用户目录"
    subtitle="USERS · INDEX"
    page-prompt="用户目录 · USERS"
    page-title="平台用户"
    page-desc="搜索昵称或用户名 · 点击查看公开主页"
    :items="navItems"
  >
    <template #sidebar-footer>
      <router-link to="/home" class="sidebar-link">
        <span class="link-code">HOM</span>
        <span>返回首页</span>
      </router-link>
    </template>

    <div class="search-bar">
      <n-input
        v-model:value="query"
        placeholder="搜索昵称或用户名"
        clearable
        @keyup.enter="search"
      >
        <template #suffix>
          <n-button text @click="search">搜索</n-button>
        </template>
      </n-input>
    </div>

    <n-spin :show="loading">
      <div v-if="users.length" class="user-grid">
        <article
          v-for="u in users"
          :key="u.id"
          class="user-card matrix-panel"
          @click="$router.push('/users/' + u.id)"
        >
          <span class="link-code">USR</span>
          <n-avatar size="medium" :src="u.avatar" v-if="u.avatar">{{ '' }}</n-avatar>
          <n-avatar size="medium" v-else color="var(--primary)">{{ (u.nickname || 'U').slice(0, 1) }}</n-avatar>
          <div class="user-meta">
            <div class="user-name">{{ u.nickname }}</div>
            <div class="user-sub">{{ u.username }} · 0x{{ u.id.toString(16).padStart(6, '0') }}</div>
          </div>
        </article>
      </div>
      <div v-else-if="!loading" class="empty-state">
        <p class="matrix-page-prompt">暂无用户</p>
        <p class="muted">暂无用户</p>
      </div>
    </n-spin>
  </MatrixShell>
</template>

<script>
import { ref, inject, onMounted } from 'vue'
import { NInput, NButton, NSpin, NAvatar } from 'naive-ui'
import { MatrixShell } from '@/components/shared'

export default {
  name: 'UserList',
  components: { NInput, NButton, NSpin, NAvatar, MatrixShell },
  setup() {
    const axios = inject('axios')
    const query = ref('')
    const users = ref([])
    const loading = ref(false)
    const navItems = [{ code: 'ALL', label: '全部用户', active: true }]

    async function search() {
      loading.value = true
      try {
        const { data } = await axios.get('/api/auth/users', { params: { q: query.value } })
        users.value = data?.users || data || []
      } catch {
        users.value = []
      } finally {
        loading.value = false
      }
    }

    onMounted(search)

    return { query, users, loading, search, navItems }
  },
}
</script>

<style scoped>
.search-bar {
  max-width: 420px;
}

.user-card {
  display: grid;
  grid-template-columns: 36px auto 1fr;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.user-card:hover {
  border-color: rgba(var(--primary-rgb), 0.45);
}

.user-name {
  font-weight: 600;
}

.user-sub {
  font-size: var(--text-xs);
  color: var(--muted);
  font-family: monospace;
}

.empty-state {
  padding: 40px 0;
  color: var(--muted);
}

.muted {
  margin-top: 8px;
}
</style>
