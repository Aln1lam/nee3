<template>
  <div class="account-page">
    <header class="matrix-page-head">
      <p class="matrix-page-prompt">第三方账号</p>
      <h2 class="matrix-page-title">第三方认证</h2>
      <p class="matrix-page-desc">绑定 GitHub 等 OAuth 登录方式</p>
    </header>

    <div class="account-panel">
      <div v-if="providers.length" class="oauth-settings">
        <p class="hint">已配置的 OAuth 提供商</p>
        <ul class="provider-list">
          <li v-for="p in providers" :key="p.id">
            <div class="provider-meta">
              <span class="link-code">OAU</span>
              <span>{{ p.label || p.id }}</span>
            </div>
            <n-button size="small" @click="connect(p)">绑定</n-button>
          </li>
        </ul>
      </div>
      <n-empty v-else description="暂未配置 OAuth 提供商">
        <template #extra>
          <p class="hint">平台管理员可在平台配置中登记 oauth_providers（需含 auth_url 才能跳转）</p>
        </template>
      </n-empty>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { NEmpty, NButton } from 'naive-ui'
import axios from 'axios'
import { fetchPlatformInfo } from '@/services/platform'

export default {
  name: 'AccountOAuth',
  components: { NEmpty, NButton },
  setup() {
    const providers = ref([])

    function connect(p) {
      const url = p.auth_url || p.url || `/api/auth/oauth/${p.id}`
      window.location.href = url
    }

    onMounted(async () => {
      try {
        const { data } = await axios.get('/api/auth/oauth/providers')
        const list = data?.data?.providers
        if (Array.isArray(list) && list.length) {
          providers.value = list
          return
        }
      } catch { /* fallback */ }
      const info = await fetchPlatformInfo()
      providers.value = info.oauth_providers || []
    })

    return { providers, connect }
  },
}
</script>

<style scoped>
.account-panel {
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
  padding: 16px;
}
.hint { font-size: var(--text-sm); color: var(--muted); margin: 0; }
.provider-list { list-style: none; padding: 0; margin: 12px 0 0; }
.provider-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.provider-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}
.provider-meta .link-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-accent, #D97706);
}
</style>
