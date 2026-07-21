<template>
  <header class="title-bar">
    <div v-if="highlightBanner && !bannerDismissed" class="highlight-banner">
      <span>{{ highlightBanner }}</span>
      <button type="button" class="banner-close" aria-label="关闭" @click="bannerDismissed = true">×</button>
    </div>

    <div class="title-bar-inner" :data-print-time="printTime">
      <div class="title-bar-left">
        <div class="brand" @click="goHome">
          <span v-if="isGameMode && gameEmoji" class="brand-game-logo">{{ gameEmoji }}</span>
          <LogoAnimate v-else :size="32" />
          <span class="brand-name">{{ displayName }}</span>
        </div>
      </div>

      <nav class="title-bar-nav">
        <template v-if="isGameMode">
          <a
            v-for="link in gameNav"
            :key="link.path"
            :class="{ active: isActive(link.path) }"
            @click.prevent="navigate(link.path)"
          >{{ link.label }}</a>
        </template>
        <template v-else>
          <a
            v-for="link in globalNav"
            :key="link.path"
            class="btn btn-md btn-ghost"
            :class="{ 'btn-active': isActive(link.path), active: isActive(link.path) }"
            @click.prevent="navigate(link.path)"
          >
            <span class="nav-label">{{ link.label }}</span>
          </a>
          <a
            v-if="user?.is_admin"
            class="btn btn-md btn-ghost"
            :class="{ 'btn-active': isActive('/admin'), active: isActive('/admin') }"
            @click.prevent="navigate('/admin/dashboard')"
          >
            <span class="nav-label">管理</span>
          </a>
        </template>
      </nav>

      <div class="title-bar-right">
        <UiTimer v-if="isGameMode && gameMeta" :start-time="gameMeta.start_time" :end-time="gameMeta.end_time" />
        <UiTimeProgress
          v-if="isGameMode && gameMeta && !isTrainingMode"
          :start-time="gameMeta.start_time"
          :end-time="gameMeta.end_time"
        />
        <UiTimeProgress v-else-if="isTrainingMode" permanent />
        <InstanceBox v-if="user" />
        <UiNotificationBox />
        <UiThemeBox />
        <template v-if="user">
          <n-dropdown :options="userMenuOptions" trigger="click" @select="onUserMenuSelect">
            <button type="button" class="avatar-btn" aria-label="用户菜单">
              <span class="header-avatar">
                <img v-if="avatarUrl && !avatarBroken" :src="avatarUrl" alt="" @error="avatarBroken = true" />
                <span v-else class="avatar-initial">{{ avatarInitial }}</span>
              </span>
              <span class="user-nick">{{ user.nickname || user.username || '用户' }}</span>
            </button>
          </n-dropdown>
        </template>
        <n-button v-else size="small" type="primary" @click="navigate('/auth')">登录</n-button>
      </div>
    </div>
  </header>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NDropdown, useMessage } from 'naive-ui'
import LogoAnimate from './LogoAnimate.vue'
import { InstanceBox } from '@/components/shared'
import { UiTimer, UiTimeProgress, UiThemeBox, UiNotificationBox } from '@/components/ui'
import { usePlatformStore } from '@/stores/platform'
import { resolveUploadUrl } from '../utils/uploadUrl'
import { fetchSession } from '../services/auth'
import { getGameEmoji } from '../utils/gameDisplay'

const NAV_CODE_FALLBACK = {
  '/home': 'HOM',
  '/wiki': 'DOC',
  '/training': 'TRN',
  '/games': 'CTF',
  '/bulletin': 'BUL',
}

const DEFAULT_NAV = [
  { label: '知识', path: '/wiki' },
  { label: '训练', path: '/training' },
  { label: '赛事', path: '/games' },
  { label: '公告', path: '/bulletin' },
]

function enrichNav(items) {
  return (items || []).map((link) => ({
    ...link,
    code: link.code || NAV_CODE_FALLBACK[link.path] || link.label?.slice(0, 3)?.toUpperCase(),
  }))
}

export default {
  name: 'TitleBar',
  components: {
    NButton, NDropdown, LogoAnimate, InstanceBox,
    UiTimer, UiTimeProgress, UiThemeBox, UiNotificationBox,
  },
  props: { user: { type: Object, default: null } },
  emits: ['logout'],
  setup(props, { emit }) {
    const route = useRoute()
    const router = useRouter()
    const axios = inject('axios')
    const message = useMessage()
    const { platform, loadPlatform } = usePlatformStore()

    const platformName = ref('')
    const globalNav = ref([])
    const highlightBanner = ref(null)
    const bannerDismissed = ref(false)
    const gameMeta = ref(null)
    const trainingTitle = ref(null)
    const avatarBroken = ref(false)

    const gameId = computed(() => {
      const raw = route.params.id || route.params.gameId
      return raw ? parseInt(raw, 10) : null
    })

    const isGameMode = computed(() => {
      const id = gameId.value
      if (!id) return false
      const path = route.path
      if (/\/games\/\d+\/admin/.test(path)) return false
      if (path.includes('/challenges')) return true
      if (path.includes('/scoreboard')) return true
      return new RegExp(`^/games/${id}(/|$)`).test(path)
    })

    const isTrainingMode = computed(() => route.path.startsWith('/training'))
    const gameEmoji = computed(() => getGameEmoji({ title: gameMeta.value?.title || '' }))

    const displayName = computed(() => {
      if (isGameMode.value && gameMeta.value?.title) return gameMeta.value.title
      if (isTrainingMode.value && trainingTitle.value) return trainingTitle.value
      return platformName.value
    })

    const gameNav = computed(() => {
      const id = gameId.value
      if (!id) return []
      return [
        { label: '概览', path: `/games/${id}` },
        { label: '题目', path: `/games/${id}/challenges` },
        { label: '积分榜', path: `/games/${id}/scoreboard` },
        { label: '队伍', path: `/games/${id}/teams` },
        { label: '返回', path: '/games' },
      ]
    })

    const userHexId = computed(() => `0x${(props.user?.id || 0).toString(16).padStart(6, '0')}`)

    const tempUserCode = computed(() => {
      const id = props.user?.id
      if (!id) return ''
      return `NEEPU-${String(id).padStart(6, '0')}-${userHexId.value.slice(2).toUpperCase()}`
    })

    const userMenuOptions = computed(() => [
      { label: `${props.user?.nickname || '用户'} · ${userHexId.value}`, key: 'info', disabled: true },
      { type: 'divider' },
      { label: '复制临时身份码', key: 'tempcode' },
      { label: '账号设置', key: 'settings' },
      ...(props.user?.is_admin ? [{ label: '管理后台', key: 'admin' }] : []),
      { type: 'divider' },
      { label: '退出登录', key: 'logout' },
    ])

    const avatarUrl = computed(() => resolveUploadUrl(props.user?.avatar) || null)
    const avatarInitial = computed(() => (props.user?.nickname || props.user?.username || 'U').slice(0, 1).toUpperCase())

    const printTime = computed(() => {
      try { return new Date().toLocaleString('zh-CN', { hour12: false }) } catch { return '' }
    })

    watch(() => props.user?.avatar, () => { avatarBroken.value = false })

    function isActive(path) {
      const current = route.path
      if (path === '/') return current === '/'
      if (path === '/games') return current === '/games'
      const id = gameId.value
      if (id && path === `/games/${id}`) return current === path || current === `${path}/`
      if (path === '/admin') return current.startsWith('/admin')
      return current === path || current.startsWith(`${path}/`)
    }

    function navigate(path) { router.push(path) }
    function goHome() { router.push(props.user ? '/home' : '/') }

    function copyTempCode() {
      const code = tempUserCode.value
      if (!code) return
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(code)
          .then(() => message.success(`已复制临时身份码：${code}`))
          .catch(() => message.info(`临时身份码：${code}`))
      } else {
        message.info(`临时身份码：${code}`)
      }
    }

    function onUserMenuSelect(key) {
      if (key === 'logout') emit('logout')
      else if (key === 'settings') router.push('/account/settings/info')
      else if (key === 'admin') router.push('/admin/dashboard')
      else if (key === 'tempcode') copyTempCode()
    }

    async function loadGameMeta(id) {
      if (!id) { gameMeta.value = null; trainingTitle.value = null; return }
      try {
        const { data } = await axios.get(`/api/competitions/${id}`)
        const meta = data?.data || data
        gameMeta.value = meta
        if (isTrainingMode.value) trainingTitle.value = meta?.title || null
      } catch {
        gameMeta.value = null
        if (isTrainingMode.value) trainingTitle.value = null
      }
    }

    function applyPlatform(info) {
      if (!info) return
      platformName.value = info.name || platformName.value || 'NEEPU CTF 平台'
      globalNav.value = enrichNav(
        (info.nav?.length ? info.nav : DEFAULT_NAV).filter((l) => l.path !== '/home' && l.path !== '/')
      )
      highlightBanner.value = info.highlight_banner || null
    }

    function onPlatformUpdated(e) { applyPlatform(e?.detail || platform.value) }

    watch(platform, (info) => applyPlatform(info), { immediate: true, deep: true })
    watch(gameId, (id) => loadGameMeta(id), { immediate: true })

    onMounted(async () => {
      await loadPlatform()
      applyPlatform(platform.value)
      window.addEventListener('neepu_platform_updated', onPlatformUpdated)
      await fetchSession().catch(() => null)
    })

    onUnmounted(() => window.removeEventListener('neepu_platform_updated', onPlatformUpdated))

    return {
      highlightBanner, bannerDismissed, displayName, gameEmoji, globalNav, gameNav,
      isGameMode, isTrainingMode, gameMeta, userMenuOptions, avatarUrl, avatarBroken,
      avatarInitial, printTime, isActive, navigate, goHome, onUserMenuSelect,
    }
  },
}
</script>

<style scoped>
.title-bar {
  position: sticky;
  top: 0;
  z-index: 60;
  background: var(--nav-bg);
  backdrop-filter: blur(6px) saturate(1.05);
  border-bottom: 1px solid var(--border);
  width: 100%;
  overflow: visible;
  box-sizing: border-box;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.12);
}
.highlight-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 6px 16px;
  background: rgba(248, 48, 48, 0.12);
  color: var(--accent-red, #f83030);
  font-size: var(--text-sm);
  border-bottom: 1px solid rgba(248, 48, 48, 0.2);
}
.banner-close {
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: var(--text-lg);
  line-height: 1;
}
.title-bar-inner {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  padding: 0 clamp(24px, 3vw, 48px);
  min-height: var(--nav-height, 72px);
  gap: 24px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
.title-bar-left { display: flex; align-items: center; gap: 12px; justify-self: start; flex-shrink: 0; }
.brand { display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: 700; color: var(--primary); }
.brand-game-logo { font-size: var(--text-2xl); line-height: 1; }
.brand-name {
  font-family: var(--font-ui);
  font-size: var(--text-xl);
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 280px;
}
.title-bar-nav { display: flex; gap: 8px; align-items: center; justify-content: center; justify-self: center; }
.title-bar-nav a {
  display: inline-grid;
  grid-template-columns: auto auto;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  text-decoration: none;
  padding: 12px 20px;
  border-radius: var(--card-radius);
  font-size: var(--text-lg);
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.nav-code {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-accent, #D97706);
  font-family: var(--font-ui);
}
.title-bar-nav a.active .nav-code { color: var(--primary); }
.title-bar-nav a:hover { color: var(--text); background: var(--gradient-nav-hover, var(--hover)); }
.title-bar-nav a.active { color: var(--primary); font-weight: 700; background: var(--gradient-nav-active, var(--hover)); }
.title-bar-right { display: flex; align-items: center; gap: 8px; justify-self: end; flex-shrink: 0; }
.header-avatar {
  width: 36px; height: 36px; border-radius: var(--radius-lg); overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  background: var(--primary); color: #fff; font-size: var(--text-xs); font-weight: 600;
}
.header-avatar img { width: 100%; height: 100%; object-fit: cover; }
.avatar-btn {
  display: flex; align-items: center; gap: 6px;
  background: var(--gradient-card-bg, transparent);
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--radius-lg); padding: 4px 10px 4px 4px; cursor: pointer; color: var(--text);
}
.user-nick { font-size: var(--text-sm); max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 1024px) {
  .title-bar-inner { padding: 0 16px; gap: 8px; }
  .title-bar-nav a { padding: 4px 8px; font-size: 0.82rem; }
  .user-nick { display: none; }
  .brand-name { max-width: 140px; }
}
@media print {
  .title-bar-nav, .title-bar-right { display: none !important; }
  .title-bar { position: static; border: none; }
  .title-bar-inner::after { content: attr(data-print-time); margin-left: auto; font-size: var(--text-xs); color: var(--muted); }
  .highlight-banner { display: none; }
}
</style>
