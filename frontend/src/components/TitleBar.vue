<template>
  <header class="title-bar">
    <div v-if="highlightBanner && !bannerDismissed" class="highlight-banner">
      <span>{{ highlightBanner }}</span>
      <button type="button" class="banner-close" aria-label="关闭" @click="bannerDismissed = true">×</button>
    </div>

    <div class="title-bar-inner" :data-print-time="printTime">
      <div class="title-bar-left">
        <div class="brand" @click="goHome">
          <LogoAnimate :size="28" />
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
        <UiThemeBox />
        <InstanceBox v-if="user" />
        <UiNotificationBox />
        <template v-if="user">
          <n-dropdown :options="userMenuOptions" trigger="click" @select="onUserMenuSelect">
            <button type="button" class="user-trigger" aria-label="用户菜单">
              <span class="header-avatar">
                <img v-if="avatarUrl && !avatarBroken" :src="avatarUrl" alt="" @error="avatarBroken = true" />
                <span v-else class="avatar-initial">{{ avatarInitial }}</span>
              </span>
              <span class="user-nick">{{ user.nickname || user.username || '用户' }}</span>
              <span class="user-role-chip">{{ userRoleBadge }}</span>
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
import { UiTimer, UiTimeProgress, UiNotificationBox, UiThemeBox } from '@/components/ui'
import { usePlatformStore } from '@/stores/platform'
import { resolveUploadUrl } from '../utils/uploadUrl'
import { fetchSession } from '../services/auth'

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
    NButton, NDropdown, LogoAnimate, InstanceBox, UiThemeBox,
    UiTimer, UiTimeProgress, UiNotificationBox,
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

    const userRoleBadge = computed(() => {
      const u = props.user || {}
      if (u.is_admin) return 'ADM'
      if (u.is_moderator) return 'MOD'
      if (u.team_id) return 'RNK'
      return 'USR'
    })

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
      highlightBanner, bannerDismissed, displayName, globalNav, gameNav,
      isGameMode, isTrainingMode, gameMeta, userMenuOptions, avatarUrl, avatarBroken,
      avatarInitial, userRoleBadge, printTime, isActive, navigate, goHome, onUserMenuSelect,
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
  backdrop-filter: none;
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
.brand { display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: 700; color: var(--text); }
.brand .logo-animate { color: var(--primary); }
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
.title-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-self: end;
  flex-shrink: 0;
  padding-right: 24px;
  margin-right: 8px;
  min-width: 0;
  overflow: visible;
}
/* NSSCTF 风：无白药丸，图标哑光 + 用户扁平行 */
.title-bar-right :deep(.notif-btn),
.title-bar-right :deep(.theme-btn),
.title-bar-right :deep(.instance-btn) {
  width: 32px !important;
  height: 32px !important;
  min-height: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 6px !important;
  background: transparent !important;
  box-shadow: none !important;
  transform: none !important;
  font-size: 18px !important;
  line-height: 1 !important;
  overflow: visible !important;
}
.title-bar-right :deep(.instance-btn) {
  color: var(--muted) !important;
}
.title-bar-right :deep(.instance-btn:hover) {
  color: var(--muted) !important;
  background: rgba(148, 163, 184, 0.08) !important;
}
.title-bar-right :deep(.instance-btn.active) {
  color: #2496ED !important;
  background: rgba(36, 150, 237, 0.1) !important;
}
.title-bar-right :deep(.notif-btn) {
  color: var(--muted) !important;
}
.title-bar-right :deep(.notif-btn:hover) {
  color: var(--primary) !important;
  background: rgba(94, 217, 168, 0.08) !important;
}
.title-bar-right :deep(.instance-icon) {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: inherit !important;
  line-height: 0 !important;
}
.title-bar-right :deep(.docker-status-icon),
.title-bar-right :deep(.docker-whale-icon) {
  width: 20px !important;
  height: 20px !important;
  display: block !important;
  overflow: visible !important;
}
.header-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(var(--primary-rgb), 0.16);
  color: rgb(var(--primary-rgb));
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-sizing: border-box;
}
.header-avatar img {
  width: 32px;
  height: 32px;
  object-fit: cover;
  display: block;
  border-radius: 50%;
}
.user-trigger {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px;
  margin: 0;
  margin-right: 2px;
  padding: 2px 0 !important;
  overflow: visible;
  min-height: 0 !important;
  height: auto !important;
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  transform: none !important;
  cursor: pointer;
  color: var(--text-main, var(--text));
}
.user-trigger:hover .user-nick { color: rgb(var(--primary-rgb)); }
.user-nick {
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-ui);
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}
.user-role-chip {
  flex-shrink: 0;
  /* 视觉由全局 Chip 标准接管，禁止局部 clip-path */
  clip-path: none !important;
}

@media (max-width: 1024px) {
  .title-bar-inner { padding: 0 16px; gap: 8px; }
  .title-bar-nav a { padding: 4px 8px; font-size: 0.82rem; }
  .user-nick, .user-role-chip { display: none; }
  .brand-name { max-width: 140px; }
}
@media print {
  .title-bar-nav, .title-bar-right { display: none !important; }
  .title-bar { position: static; border: none; }
  .title-bar-inner::after { content: attr(data-print-time); margin-left: auto; font-size: var(--text-xs); color: var(--muted); }
  .highlight-banner { display: none; }
}
</style>
