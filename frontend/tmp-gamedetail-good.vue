<template>
  <div class="game-detail-page">
    <div v-if="loading && !game" class="page-loading">
      <UiLoadingTips />
    </div>

    <template v-else-if="game">
      <div class="detail-topbar">
        <button type="button" class="back-link" @click="$router.push('/games')">← 返回赛事列表</button>
        <UiButton
          v-if="canEdit && !editing"
          size="small"
          variant="ghost"
          @click="startEdit"
        >编辑说明</UiButton>
      </div>

      <div class="detail-layout">
        <!-- 左侧：赛事介绍 -->
        <section class="intro-column">
          <h2 class="intro-heading">赛事介绍</h2>

          <template v-if="editing">
            <textarea v-model="editContent" class="edit-area" rows="16" />
            <div class="edit-actions">
              <UiButton variant="primary" :loading="saving" @click="saveEdit">保存</UiButton>
              <UiButton variant="ghost" @click="cancelEdit">取消</UiButton>
            </div>
          </template>
          <Article v-else :content="articleContent" />
        </section>

        <!-- 右侧：海报 + 状态 + 参与按钮 -->
        <aside class="action-column">
          <div class="action-card">
            <div class="action-poster" :class="coverTheme">
              <img v-if="posterUrl" :src="posterUrl" :alt="game.title" class="action-poster-img" />
              <div v-else class="action-poster-fallback">
                <span class="action-poster-emoji">{{ gameEmoji }}</span>
              </div>
            </div>

            <div class="action-body">
              <h1 class="action-title">{{ game.title }}</h1>
              <p class="action-sub">{{ gameSubtitle }}</p>

              <div class="action-status" :class="`status-${statusTagType}`">
                {{ statusLabel }}
              </div>

              <div class="action-tags">
                <UiTag variant="default" size="small">{{ game.challenge_count || 0 }} 道题目</UiTag>
                <UiTag variant="default" size="small">{{ game.participation_count || 0 }} 支队伍</UiTag>
                <UiTag v-if="game.game_type === 'official'" variant="info" size="small">正式赛</UiTag>
              </div>

              <div class="action-time">{{ timeRange }}</div>

              <GameTimer
                v-if="game"
                :start-time="game.start_time"
                :end-time="game.end_time"
                :status="game.status"
              />

              <p v-if="phaseHint" class="action-hint">{{ phaseHint }}</p>

              <UiButton
                v-if="primaryCta"
                variant="primary"
                size="large"
                block
                :loading="joining"
                @click="primaryCta.action"
              >{{ primaryCta.label }}</UiButton>

              <div class="action-secondary">
                <UiButton
                  v-if="!isArchived"
                  variant="secondary"
                  block
                  @click="$router.push(`/games/${gameId}/scoreboard`)"
                >查看积分板</UiButton>
                <UiButton
                  v-if="loggedIn && !isArchived"
                  variant="ghost"
                  block
                  @click="$router.push(`/games/${gameId}/teams`)"
                >队伍管理</UiButton>
                <UiButton
                  v-if="isArchived"
                  variant="primary"
                  block
                  @click="$router.push(`/training/${gameId}`)"
                >前往训练场</UiButton>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </template>

    <div v-else-if="!loading" class="page-empty">
      <p>赛事不存在或无权访问</p>
      <UiButton @click="$router.push('/games')">返回赛事列表</UiButton>
    </div>

    <div v-if="banned" class="banned-overlay">
      <div class="banned-box">
        <h2>队伍已被封禁</h2>
        <p>你的队伍在本赛事中已被管理员封禁，无法继续参赛。</p>
        <UiButton @click="$router.push('/games')">返回赛事列表</UiButton>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import GameTimer from './GameTimer.vue'
import { Article } from '@/components/shared'
import { UiButton, UiTag, UiLoadingTips } from '@/components/ui'
import { useToast } from '../composables/toast'
import { getUser, isAdmin as checkIsAdmin, hasSession } from '../services/auth'
import { unwrapTeamResponse } from '../utils/team'
import { resolveUploadUrl } from '../utils/uploadUrl'
import {
  getGameEmoji,
  getGameCoverTheme,
  getGameStatusLabel,
  getGameStatusVariant,
  formatGameTimeRange,
  extractPosterPath,
  getGameSubtitle,
} from '../utils/gameDisplay'

export default {
  name: 'GameDetail',
  components: { GameTimer, Article, UiButton, UiTag, UiLoadingTips },
  props: { id: { type: [String, Number], default: null } },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()
    const toast = useToast()

    const game = ref(null)
    const loading = ref(false)
    const joining = ref(false)
    const joined = ref(false)
    const loggedIn = ref(false)
    const hasTeam = ref(false)
    const banned = ref(false)
    const editing = ref(false)
    const editContent = ref('')
    const saving = ref(false)

    const gameId = computed(() => props.id || route.params.id)
    const isAdmin = ref(checkIsAdmin())
    const canEdit = computed(() => isAdmin.value && route.query.edit === 'true')
    const isArchived = computed(() => game.value?.status === 'archived')

    const articleContent = computed(() =>
      game.value?.rules || game.value?.description || '_暂无详细说明，请报名后进入题目页开始挑战。_',
    )

    const gameSubtitle = computed(() => getGameSubtitle(game.value))
    const coverTheme = computed(() => getGameCoverTheme(game.value))
    const gameEmoji = computed(() => getGameEmoji(game.value))
    const statusLabel = computed(() => getGameStatusLabel(game.value))
    const statusTagType = computed(() => getGameStatusVariant(game.value))
    const timeRange = computed(() => formatGameTimeRange(game.value))

    const posterUrl = computed(() => {
      const path = extractPosterPath(game.value?.description)
      return path ? resolveUploadUrl(path) : ''
    })

    const phaseHint = computed(() => {
      if (!game.value) return ''
      const now = Date.now()
      const start = game.value.start_time ? new Date(game.value.start_time).getTime() : 0
      const end = game.value.end_time ? new Date(game.value.end_time).getTime() : Infinity
      if (game.value.status === 'archived') return '赛事已归档，可前往训练场继续练习'
      if (!loggedIn.value) return '登录后可报名参赛；组队赛需先创建或加入队伍'
      if (!hasTeam.value && !isAdmin.value) return '本赛事为组队赛，请先创建或加入队伍后再报名'
      if (now < start && joined.value) return '已报名，请等待比赛开始'
      if (now < start) return '当前为报名阶段，比赛尚未开始'
      if (now >= end) return '比赛已结束，可查看积分板'
      return ''
    })

    const primaryCta = computed(() => {
      if (!game.value || isArchived.value) return null

      const now = Date.now()
      const start = game.value.start_time ? new Date(game.value.start_time).getTime() : 0
      const end = game.value.end_time ? new Date(game.value.end_time).getTime() : Infinity

      if (!loggedIn.value) {
        return { label: '登录后参与 »', action: goLogin }
      }

      if (!isAdmin.value && !hasTeam.value) {
        return { label: '创建或加入队伍 »', action: goTeams }
      }

      if (!isAdmin.value && now >= end) {
        return { label: '查看积分板 »', action: () => router.push(`/games/${gameId.value}/scoreboard`) }
      }

      if (!isAdmin.value && now < start) {
        return joined.value
          ? { label: '已报名 · 等待开始', action: () => toast.info('比赛尚未开始，请耐心等待') }
          : { label: '报名参加 »', action: enterGame }
      }

      return {
        label: joined.value ? '进入题目 »' : '报名参加 »',
        action: enterGame,
      }
    })

    function goLogin() {
      router.push({ name: 'Auth', query: { redirect: route.fullPath } })
    }

    function goTeams() {
      router.push(`/games/${gameId.value}/teams`)
    }

    function startEdit() {
      editContent.value = articleContent.value
      editing.value = true
    }

    function cancelEdit() {
      editing.value = false
    }

    async function saveEdit() {
      saving.value = true
      try {
        await axios.put(`/api/competitions/admin/${gameId.value}/update`, {
          rules: editContent.value,
          description: editContent.value,
        })
        game.value = { ...game.value, rules: editContent.value, description: editContent.value }
        editing.value = false
        message.success('赛事说明已保存')
      } catch (e) {
        message.error(e.response?.data?.msg || '保存失败')
      } finally {
        saving.value = false
      }
    }

    async function refreshSessionState() {
      loggedIn.value = await hasSession()
      if (!loggedIn.value) {
        hasTeam.value = false
        joined.value = false
        return
      }
      isAdmin.value = checkIsAdmin()
      await Promise.all([checkJoined(), checkTeam(), checkBanned()])
    }

    async function checkTeam() {
      if (!(await hasSession())) {
        hasTeam.value = false
        return
      }
      try {
        const { data } = await axios.get('/api/teams/me', { _skipAuthClear: true })
        hasTeam.value = !!unwrapTeamResponse(data)
      } catch {
        hasTeam.value = false
      }
    }

    async function checkBanned() {
      if (!(await hasSession()) || !gameId.value) return
      try {
        await axios.post(`/api/competitions/${gameId.value}/join`, {})
      } catch (e) {
        const msg = e.response?.data?.msg || ''
        if (e.response?.status === 403 && /封禁|ban/i.test(msg)) {
          banned.value = true
        }
      }
    }

    async function loadGame() {
      if (!gameId.value) return
      loading.value = true
      try {
        const { data } = await axios.get(`/api/competitions/${gameId.value}`)
        game.value = data?.data || data
        if (game.value?.status === 'archived') {
          toast.info('该赛事已归档，可前往训练场继续练习')
        }
        await refreshSessionState()
        if (canEdit.value) startEdit()
      } catch {
        game.value = null
      } finally {
        loading.value = false
      }
    }

    async function checkJoined() {
      if (!(await hasSession())) {
        joined.value = false
        return
      }
      try {
        const { data } = await axios.get('/api/competitions/my')
        const list = data?.data || data || []
        joined.value = list.some(g => (g.game_id || g.id) === parseInt(gameId.value, 10))
      } catch {
        joined.value = false
      }
    }

    async function enterGame() {
      if (!(await hasSession())) {
        goLogin()
        return
      }

      if (!isAdmin.value && !hasTeam.value) {
        message.warning('请先创建或加入队伍')
        goTeams()
        return
      }

      const now = Date.now()
      const start = game.value?.start_time ? new Date(game.value.start_time).getTime() : 0
      const end = game.value?.end_time ? new Date(game.value.end_time).getTime() : Infinity

      joining.value = true
      try {
        if (!isAdmin.value && now >= end) {
          toast.warning('比赛已结束')
          router.push(`/games/${gameId.value}/scoreboard`)
          return
        }

        if (!isAdmin.value && now < start) {
          if (!joined.value) {
            await axios.post(`/api/competitions/${gameId.value}/join`, {})
            joined.value = true
            message.success('报名成功，请等待比赛开始')
          } else {
            message.info('已报名，请等待比赛开始')
          }
          return
        }

        if (!joined.value) {
          await axios.post(`/api/competitions/${gameId.value}/join`, {})
          joined.value = true
          message.success('报名成功')
        }
        router.push(`/games/${gameId.value}/challenges`)
      } catch (e) {
        if (e.response?.status === 403) banned.value = true
        else {
          const msg = e.response?.data?.msg || '操作失败'
          if (/加入团队|加入队伍|team/i.test(msg)) {
            message.warning('请先创建或加入队伍')
            goTeams()
          } else {
            message.error(msg)
          }
        }
      } finally {
        joining.value = false
      }
    }

    function refreshAdmin() {
      isAdmin.value = checkIsAdmin()
    }

    watch(gameId, loadGame, { immediate: true })
    watch(() => route.query.edit, (v) => {
      if (v === 'true' && canEdit.value && game.value) startEdit()
      else editing.value = false
    })

    onMounted(() => {
      window.addEventListener('neepu_user_refreshed', refreshAdmin)
      window.addEventListener('neepu_user_refreshed', refreshSessionState)
    })

    onUnmounted(() => {
      window.removeEventListener('neepu_user_refreshed', refreshAdmin)
      window.removeEventListener('neepu_user_refreshed', refreshSessionState)
    })

    return {
      game, gameId, loading, joining, joined, loggedIn, hasTeam, banned,
      editing, editContent, saving, canEdit, isArchived,
      articleContent, gameSubtitle, coverTheme, gameEmoji, posterUrl,
      statusLabel, statusTagType, timeRange, phaseHint, primaryCta,
      startEdit, cancelEdit, saveEdit, enterGame,
    }
  },
}
</script>

<style scoped>
.game-detail-page {
  width: 100%;
  margin: 0;
  min-height: calc(100vh - var(--nav-height, 56px) - 52px);
  padding: 24px 28px 48px;
  box-sizing: border-box;
}

.detail-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.back-link {
  border: none;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.back-link:hover { color: var(--primary); }

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
  align-items: start;
}

.intro-column {
  min-width: 0;
}

.intro-heading {
  margin: 0 0 24px;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text);
  text-align: center;
}

.edit-area {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card-bg);
  color: var(--text);
  font-family: 'Monaspace Neon', 'LXGW WenKai Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.action-column {
  position: sticky;
  top: calc(var(--nav-height, 56px) + 16px);
}

.action-card {
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: 14px;
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--gradient-card-shadow, var(--shadow-lg));
  overflow: hidden;
}

.action-poster {
  aspect-ratio: 4 / 3;
  position: relative;
  background: var(--card-bg);
}

.action-poster.theme-stars {
  background:
    radial-gradient(ellipse at 20% 30%, rgba(45, 181, 138, 0.22) 0%, transparent 55%),
    var(--card-bg);
}

.action-poster.theme-suzume {
  background:
    radial-gradient(ellipse at 50% 0%, rgba(45, 181, 138, 0.24) 0%, transparent 50%),
    var(--card-bg);
}

.action-poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.action-poster-fallback {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-poster-emoji { font-size: 56px; }

.action-body {
  padding: 20px 18px 22px;
}

.action-title {
  margin: 0 0 6px;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.35;
}

.action-sub {
  margin: 0 0 14px;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.5;
}

.action-status {
  text-align: center;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 14px;
  color: var(--muted);
}

.action-status.status-success { color: var(--success, #16A34A); }
.action-status.status-warning { color: var(--warning, #D97706); }
.action-status.status-info { color: var(--info, #1A9B6E); }

.action-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-bottom: 12px;
}

.action-time {
  font-size: 12px;
  color: var(--warning, #D97706);
  text-align: center;
  line-height: 1.5;
  margin-bottom: 12px;
}

.action-hint {
  margin: 0 0 14px;
  font-size: 12px;
  color: var(--muted);
  text-align: center;
  line-height: 1.5;
}

.action-secondary {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.page-loading,
.page-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 24px;
  color: var(--muted);
}

.banned-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgba(248, 48, 48, 0.15);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banned-box {
  background: var(--card-bg);
  border: 2px solid var(--accent-red, #f83030);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  max-width: 400px;
}

.banned-box h2 {
  color: var(--accent-red, #f83030);
  margin: 0 0 12px;
}

@media (max-width: 960px) {
  .game-detail-page { padding: 16px; }
  .detail-layout {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  .action-column { position: static; }
  .intro-heading { text-align: left; font-size: 1.2rem; }
}
</style>
