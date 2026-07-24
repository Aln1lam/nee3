<template>
  <GameLayout
    mode="overview"
    :show-sidebar="true"
    :collapsible="true"
    storage-key="neepu_game_overview_sidebar"
    class="game-overview-shell"
  >
    <template #sidebar>
      <aside class="contest-nav-rail">
        <div class="sidebar-head sidebar-rail-head">
          <div class="sidebar-head-row">
            <h2 class="sidebar-title sidebar-rail-title">赛事列表</h2>
          </div>
          <p class="sidebar-desc sidebar-rail-sub">CONTESTS · SELECT</p>
        </div>

        <div v-if="contestListLoading" class="contest-nav-loading">加载中…</div>
        <nav v-else class="sidebar-rail-nav contest-nav-list">
          <button
            v-for="g in contestList"
            :key="g.id"
            type="button"
            class="sidebar-item contest-nav-item"
            :class="{ active: String(g.id) === String(gameId) }"
            @click="selectContest(g)"
          >
            <span class="item-title">{{ g.title }}</span>
            <span
              class="contest-status-chip"
              :class="'is-' + contestStatusVariant(g)"
            >{{ contestStatusLabel(g) }}</span>
          </button>
          <div v-if="!contestList.length" class="contest-nav-empty">暂无赛事</div>
        </nav>
      </aside>
    </template>

    <template #sidebar-footer>
      <router-link to="/contests" class="sidebar-link game-layout-back">
        <span class="link-code">CTF</span>
        <span>返回赛事</span>
      </router-link>
    </template>

    <div class="game-overview-container">
      <div v-if="loading && !game" class="page-loading">
        <UiLoadingTips />
      </div>

      <template v-else-if="game">
        <div v-if="canEdit && !editing" class="detail-topbar detail-topbar--edit-only">
          <UiButton size="small" variant="ghost" @click="startEdit">编辑赛事</UiButton>
        </div>

        <!-- 工业极客 Hero：左赛事简报 + 右沉浸 16:9 海报 -->
        <section
          class="overview-hero game-overview-card"
          :class="{ 'has-poster': !!(posterUrl && !posterBroken) }"
        >
          <div class="hero-info">
            <header class="hero-head">
              <p class="hero-kicker">CTF · ARENA BRIEF</p>
              <div class="hero-title-row">
                <h1 class="hero-title">{{ game.title }}</h1>
                <span class="status-badge" :class="'is-' + statusTagType">
                  <span class="status-pulse" aria-hidden="true" />
                  <span class="status-text">{{ statusLabel }}</span>
                </span>
              </div>
              <p v-if="timeRange" class="hero-meta">
                <span class="hero-meta-label">WINDOW</span>
                <span class="hero-meta-value">{{ timeRange }}</span>
              </p>
            </header>

            <div class="hero-body">
              <div class="hero-section-bar">
                <h2 class="hero-section-label">赛事简介</h2>
                <span class="hero-section-rule" aria-hidden="true" />
              </div>
              <template v-if="editing">
                <textarea v-model="editContent" class="edit-area" rows="12" />
                <div class="edit-actions">
                  <UiButton variant="primary" :loading="saving" @click="saveEdit">保存</UiButton>
                  <UiButton variant="ghost" @click="cancelEdit">取消</UiButton>
                </div>
              </template>
              <Article v-else :content="articleContent" :show-toc="false" class="hero-article" />
            </div>
          </div>

          <aside class="hero-aside poster-wrapper">
            <button
              type="button"
              class="poster-container"
              :class="coverTheme"
              :disabled="joining"
              aria-label="进入题目赛场"
              @click="goToChallenges"
            >
              <img
                v-if="posterUrl && !posterBroken"
                :src="posterUrl"
                alt=""
                class="poster-image-bg"
                aria-hidden="true"
                @error="posterBroken = true"
              />
              <img
                v-if="posterUrl && !posterBroken"
                :src="posterUrl"
                :alt="game.title"
                class="poster-image"
                @error="posterBroken = true"
              />
              <div v-else class="hero-poster-fallback">
                <span class="hero-poster-emoji">{{ gameEmoji }}</span>
              </div>
              <!-- 沉浸 Hover：右下角精致提示，无中央胶囊 -->
              <span class="poster-enter-hint" aria-hidden="true">
                <span class="poster-enter-label">ENTER ARENA ↗</span>
              </span>
            </button>
          </aside>
        </section>
      </template>

      <div v-else-if="!loading" class="page-empty">
        <p>赛事不存在或已下架</p>
        <UiButton @click="$router.push('/contests')">返回赛事列表</UiButton>
      </div>

      <n-modal
        v-model:show="showInviteModal"
        :mask-closable="false"
        transform-origin="center"
        class="invite-join-modal-root"
      >
        <div class="invite-join-card" role="dialog" aria-modal="true" aria-labelledby="invite-join-title-ov">
          <header class="invite-join-head">
            <span class="link-code chip-cut">KEY</span>
            <h3 id="invite-join-title-ov">校内赛邀请码</h3>
          </header>
          <p class="invite-join-desc">本场为校内赛，需邀请码才能报名。请向主办方索取后填写（与队伍密钥不同）。</p>
          <label class="invite-join-label" for="invite-code-input-ov">邀请码</label>
          <n-input
            id="invite-code-input-ov"
            v-model:value="inviteCodeInput"
            class="invite-join-input"
            placeholder="粘贴或输入邀请码"
            maxlength="64"
            @keydown.enter.prevent="confirmInviteJoin"
          />
          <div class="invite-join-actions">
            <button type="button" class="invite-join-btn invite-join-btn--ghost" :disabled="joining" @click="showInviteModal = false">取消</button>
            <button type="button" class="invite-join-btn invite-join-btn--primary" :disabled="joining" @click="confirmInviteJoin">
              {{ joining ? '校验中…' : '确认报名' }}
            </button>
          </div>
        </div>
      </n-modal>

      <div v-if="banned" class="banned-overlay">
        <div class="banned-box">
          <h2>队伍已被封禁</h2>
          <p>你的队伍在本赛事中已被管理员封禁，无法继续参赛。</p>
          <UiButton @click="$router.push('/contests')">返回赛事列表</UiButton>
        </div>
      </div>
    </div>
  </GameLayout>
</template>

<script>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NModal, NInput, useMessage } from 'naive-ui'
import GameLayout from './GameLayout.vue'
import { Article } from '@/components/shared'
import { UiButton, UiLoadingTips } from '@/components/ui'
import { useToast } from '../composables/toast'
import { isAdmin as checkIsAdmin, hasSession } from '../services/auth'
import { unwrapTeamResponse } from '../utils/team'
import { resolveUploadUrl } from '../utils/uploadUrl'
import { filterPublicGames } from '../utils/gameFilters'
import { gameNeedsInvite, CAMPUS_ORG } from '../utils/competitionJoin'
import '../assets/invite-join-modal.css'
import {
  getGameEmoji,
  getGameCoverTheme,
  getGameStatusLabel,
  getGameStatusVariant,
  formatGameTimeRange,
  getGamePosterPath,
  getGameSubtitle,
} from '../utils/gameDisplay'

export default {
  name: 'GameOverview',
  components: { GameLayout, Article, UiButton, UiLoadingTips, NModal, NInput },
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
    const showInviteModal = ref(false)
    const inviteCodeInput = ref('')
    const pendingAfterJoin = ref(null) // 'challenges' | 'stay'

    const needsInvite = computed(() => gameNeedsInvite(game.value))

    const gameId = computed(() => props.id || route.params.id)

    const contestList = ref([])
    const contestListLoading = ref(false)

    function unwrapContestList(payload) {
      const raw = payload?.data ?? payload
      if (Array.isArray(raw)) return raw
      if (Array.isArray(raw?.items)) return raw.items
      if (Array.isArray(raw?.competitions)) return raw.competitions
      if (Array.isArray(raw?.games)) return raw.games
      return []
    }

    async function loadContestList() {
      contestListLoading.value = true
      try {
        const { data } = await axios.get('/api/competitions/', { params: { exclude_training: true } })
        contestList.value = filterPublicGames(unwrapContestList(data))
      } catch (e) {
        console.error(e)
        contestList.value = []
      } finally {
        contestListLoading.value = false
      }
    }

    function contestStatusLabel(g) {
      return getGameStatusLabel(g)
    }

    function contestStatusVariant(g) {
      return getGameStatusVariant(g) || 'default'
    }

    function selectContest(g) {
      if (!g?.id) return
      if (String(g.id) === String(gameId.value)) return
      router.push(`/games/${g.id}`)
    }

    const isAdmin = ref(checkIsAdmin())
    const canEdit = computed(() => isAdmin.value && route.query.edit === 'true')
    const isArchived = computed(() => game.value?.status === 'archived')

    const articleContent = computed(() =>
      game.value?.rules || game.value?.description || '_暂无详细说明，请进入题目页开始挑战。_',
    )

    const gameSubtitle = computed(() => getGameSubtitle(game.value))
    const coverTheme = computed(() => getGameCoverTheme(game.value))
    const gameEmoji = computed(() => getGameEmoji(game.value))
    const statusLabel = computed(() => getGameStatusLabel(game.value))
    const statusTagType = computed(() => getGameStatusVariant(game.value))
    const timeRange = computed(() => formatGameTimeRange(game.value))

    const posterBroken = ref(false)
    const posterUrl = computed(() => {
      const path = getGamePosterPath(game.value)
      return path ? resolveUploadUrl(path, game.value?.id) : ''
    })
    watch(() => game.value?.id, () => { posterBroken.value = false })

    const phaseHint = computed(() => {
      if (!game.value) return ''
      const now = Date.now()
      const start = game.value.start_time ? new Date(game.value.start_time).getTime() : 0
      const end = game.value.end_time ? new Date(game.value.end_time).getTime() : Infinity
      if (game.value.status === 'archived') return '本场赛事已归档，可转入训练模式复习'
      if (!loggedIn.value) return needsInvite.value ? '登录后凭邀请码报名校内赛' : '登录后即可报名参赛'
      if (!hasTeam.value && !isAdmin.value) return '需先加入或创建战队才能参赛'
      if (now < start && joined.value) return '已预约，开赛后可直接进入'
      if (now < start) return '赛事尚未开始，可先预约报名'
      if (now >= end) return '赛事已结束，可通过顶部 Tab 查看积分榜'
      return ''
    })

    const teamHint = computed(() => {
      if (!loggedIn.value || isArchived.value || !game.value || hasTeam.value) return ''
      const now = Date.now()
      const end = game.value.end_time ? new Date(game.value.end_time).getTime() : Infinity
      if (now >= end) return ''
      return '尚未加入战队，请先创建或加入战队后再参赛'
    })

    const primaryCta = computed(() => {
      if (!game.value) return null

      if (isArchived.value) {
        return {
          label: '进入练习 →',
          action: () => router.push(`/training/${gameId.value}`),
        }
      }

      const now = Date.now()
      const start = game.value.start_time ? new Date(game.value.start_time).getTime() : 0
      const end = game.value.end_time ? new Date(game.value.end_time).getTime() : Infinity

      if (!loggedIn.value) {
        return { label: '登录参赛 →', action: goLogin }
      }

      if (!isAdmin.value && !hasTeam.value) {
        return { label: '加入战队 →', action: goTeams }
      }

      if (!isAdmin.value && now < start) {
        return joined.value
          ? { label: '已预约 · 等待开赛', action: () => toast.info('开赛后可从本页进入题目列表') }
          : { label: '预约报名 →', action: enterGame }
      }

      // 进行中 / 已结束：唯一核心入口 → 题目 Tab（Header 已有积分榜/队伍）
      return {
        label: '进入题目列表 →',
        action: enterGame,
      }
    })

    function goLogin() {
      router.push({ name: 'Auth', query: { redirect: route.fullPath } })
    }

    function goTeams() {
      router.push(`/games/${gameId.value}/teams`)
    }

    /** 海报点击：报名校验后进入题目 Tab */
    function goToChallenges() {
      if (isArchived.value) {
        router.push(`/training/${gameId.value}`)
        return
      }
      enterGame()
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
        message.success('规则已保存')
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
        const { data } = await axios.get('/api/teams/me', {
          params: { game_id: gameId.value },
          _skipAuthClear: true,
        })
        hasTeam.value = !!unwrapTeamResponse(data)
      } catch {
        hasTeam.value = false
      }
    }

    async function checkBanned() {
      if (!(await hasSession()) || !gameId.value) return
      // 校内赛未报名时勿空 body 探测，会误报「需要邀请码」
      if (needsInvite.value && !joined.value) return
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
          toast.info('本场赛事已归档，题目已转入训练靶场')
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
        const { data } = await axios.get(`/api/competitions/${gameId.value}/joined`)
        joined.value = !!data?.joined
      } catch {
        joined.value = false
      }
    }

    async function ensureCampusOrg() {
      if (!needsInvite.value) return
      try {
        const { data } = await axios.get('/api/teams/me', {
          params: { game_id: gameId.value },
          _skipAuthClear: true,
        })
        const team = unwrapTeamResponse(data)
        if (!team?.id) return
        if ((team.school || '').trim() === CAMPUS_ORG) return
        await axios.patch(`/api/teams/${team.id}`, { school: CAMPUS_ORG })
      } catch { /* ignore */ }
    }

    async function postJoin(inviteCode) {
      const body = {}
      if (inviteCode) body.invite_code = inviteCode
      await axios.post(`/api/competitions/${gameId.value}/join`, body)
      joined.value = true
      await ensureCampusOrg()
    }

    function openInviteModal(after) {
      pendingAfterJoin.value = after || 'challenges'
      inviteCodeInput.value = ''
      showInviteModal.value = true
    }

    async function confirmInviteJoin() {
      const code = inviteCodeInput.value.trim()
      if (!code) {
        message.warning('请输入邀请码')
        return
      }
      joining.value = true
      try {
        await postJoin(code)
        showInviteModal.value = false
        message.success('报名成功')
        const after = pendingAfterJoin.value
        pendingAfterJoin.value = null
        const now = Date.now()
        const start = game.value?.start_time ? new Date(game.value.start_time).getTime() : 0
        if (after === 'challenges' && now >= start) {
          router.push(`/games/${gameId.value}/challenges`)
        }
      } catch (e) {
        if (e.response?.status === 403 && /封禁|ban/i.test(e.response?.data?.msg || '')) {
          banned.value = true
          showInviteModal.value = false
        } else {
          message.error(e.response?.data?.msg || '邀请码无效')
        }
      } finally {
        joining.value = false
      }
    }

    async function enterGame() {
      if (joining.value) return
      if (!(await hasSession())) {
        goLogin()
        return
      }

      if (!isAdmin.value && !hasTeam.value) {
        message.warning('请先加入或创建战队')
        goTeams()
        return
      }

      const now = Date.now()
      const start = game.value?.start_time ? new Date(game.value.start_time).getTime() : 0
      const end = game.value?.end_time ? new Date(game.value.end_time).getTime() : Infinity

      if (!isAdmin.value && now >= end) {
        router.push(`/games/${gameId.value}/challenges`)
        return
      }

      if (!joined.value && needsInvite.value) {
        openInviteModal(now < start ? 'stay' : 'challenges')
        return
      }

      joining.value = true
      try {
        if (!isAdmin.value && now < start) {
          if (!joined.value) {
            await postJoin()
            message.success('预约成功，开赛后可直接进入')
          } else {
            message.info('你已预约本场赛事')
          }
          return
        }

        if (!joined.value) {
          await postJoin()
          message.success('报名成功')
        }
        router.push(`/games/${gameId.value}/challenges`)
      } catch (e) {
        if (e.response?.status === 403) banned.value = true
        else {
          const msg = e.response?.data?.msg || '操作失败'
          if (/邀请码/.test(msg)) {
            openInviteModal(now < start ? 'stay' : 'challenges')
          } else if (/队伍|战队|team/i.test(msg)) {
            message.warning('请先加入或创建战队')
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
      loadContestList()
      window.addEventListener('neepu_user_refreshed', refreshAdmin)
      window.addEventListener('neepu_user_refreshed', refreshSessionState)
    })

    onUnmounted(() => {
      window.removeEventListener('neepu_user_refreshed', refreshAdmin)
      window.removeEventListener('neepu_user_refreshed', refreshSessionState)
    })

    return {
      game, gameId, loading, joining, banned,
      editing, editContent, saving, canEdit,
      showInviteModal, inviteCodeInput, confirmInviteJoin,
      articleContent, coverTheme, gameEmoji, posterUrl, posterBroken,
      statusLabel, statusTagType, timeRange,
      contestList, contestListLoading,
      contestStatusLabel, contestStatusVariant, selectContest,
      startEdit, cancelEdit, saveEdit, goToChallenges,
    }
  },
}
</script>

<style scoped>
.game-overview-container {
  position: relative;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 24px 32px 32px;
  box-sizing: border-box;
  width: 100%;
  margin: 0;
}


.detail-topbar {
  position: absolute;
  top: 28px;
  right: 32px;
  z-index: 2;
}
.detail-topbar--edit-only { min-height: 0; }

/* 统一毛玻璃大卡片 — 强制四周等距留白 */
.overview-hero.game-overview-card,
.game-overview-card {
  /* 高度由右侧 16:9 海报决定，禁止撑满视口制造假留白 */
  flex: 0 1 auto;
  min-height: 0;
  height: auto;
  max-height: 100%;
  display: grid;
  grid-template-columns: 30% 70%; /* 大幅提升右侧海报区占比 */
  gap: 32px;
  padding: 32px !important; /* 物理锁定：上/下/左/右统一 32px */
  box-sizing: border-box !important;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  align-items: stretch;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(145deg, rgba(18, 24, 36, 0.72) 0%, rgba(12, 16, 24, 0.55) 100%);
  backdrop-filter: blur(22px) saturate(1.2);
  -webkit-backdrop-filter: blur(22px) saturate(1.2);
  box-shadow:
    0 24px 64px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

/* 有海报：右栏出血贴齐卡片，去掉「框套图」 */
.overview-hero.game-overview-card.has-poster {
  grid-template-columns: minmax(280px, 0.95fr) minmax(0, 1.35fr);
  gap: 0;
  padding: 32px 0 32px 32px !important;
}

.overview-hero.game-overview-card.has-poster .hero-info {
  padding-right: 28px;
  z-index: 2;
}

.overview-hero.game-overview-card.has-poster .poster-wrapper {
  /* 上下吃掉 32px padding，右侧再盖住 1px 边框，顶/底/右真正贴齐 */
  margin: -33px -1px -33px 0;
  align-self: start;
  overflow: hidden;
  display: block;
  height: auto;
  min-height: 0;
}

.overview-hero.game-overview-card.has-poster .poster-container {
  width: 100%;
  height: auto;
  min-height: 0;
  /* 继续用 16:9 撑开整张卡片高度；负 margin 负责出血 */
  aspect-ratio: 16 / 9;
  padding: 0 !important; /* 盖掉全局 button 的 8px 16px，避免「框套图」 */
  margin: 0;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  overflow: hidden;
  display: block;
  flex: none;
}

.overview-hero.game-overview-card.has-poster .poster-container:hover {
  transform: none;
  border-color: transparent;
  box-shadow: none;
}

.overview-hero.game-overview-card.has-poster .poster-image-bg,
.overview-hero.game-overview-card.has-poster .poster-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.overview-hero.game-overview-card.has-poster .poster-container:hover .poster-image {
  transform: scale(1.03);
}

/* 左缘羽化：海报溶进左侧文案底 */
.overview-hero.game-overview-card.has-poster .poster-container::after {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: min(48%, 260px);
  z-index: 2;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    rgba(14, 18, 28, 0.96) 0%,
    rgba(14, 18, 28, 0.62) 38%,
    rgba(14, 18, 28, 0.18) 68%,
    rgba(14, 18, 28, 0) 100%
  );
}

.hero-info {
  /* height:0 + min-height:100%：不参与撑高 grid 行，行高由海报 16:9 决定 */
  min-width: 0;
  min-height: 100%;
  height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  padding: 0;
  box-sizing: border-box;
}

.hero-head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  flex-shrink: 0;
}

.hero-kicker {
  margin: 0;
  font-family: var(--font-mono, "JetBrains Mono", "Fira Code", monospace);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  color: rgba(94, 217, 168, 0.72);
}

.hero-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  width: 100%;
}

.hero-title {
  margin: 0;
  font-family: var(--font-ui, "M PLUS Rounded 1c", "Noto Sans SC", sans-serif);
  font-size: clamp(1.55rem, 2.5vw, 2.15rem);
  font-weight: 760;
  color: #f3f4f6;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.hero-meta {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px 10px;
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: #94a3b8;
}
.hero-meta-label {
  font-family: var(--font-mono, "JetBrains Mono", "Fira Code", monospace);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: rgba(148, 163, 184, 0.85);
}
.hero-meta-value {
  font-family: var(--font-mono, "JetBrains Mono", "Fira Code", monospace);
  color: #cbd5e1;
}

/* 呼吸感状态 Badge（工业 HUD，非生硬胶囊堆） */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 11px 5px 9px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(15, 23, 42, 0.55);
  color: #cbd5e1;
}
.status-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  box-shadow: 0 0 0 0 rgba(148, 163, 184, 0.45);
  animation: status-breathe 2.4s ease-in-out infinite;
  flex-shrink: 0;
}
.status-badge.is-success {
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.38);
  background: rgba(34, 197, 94, 0.1);
}
.status-badge.is-success .status-pulse {
  background: #4ade80;
  box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.55);
  animation-name: status-breathe-green;
}
.status-badge.is-warning {
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(245, 158, 11, 0.1);
}
.status-badge.is-warning .status-pulse {
  background: #fbbf24;
  box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.5);
  animation-name: status-breathe-amber;
}
.status-badge.is-info {
  color: #5ed9a8;
  border-color: rgba(94, 217, 168, 0.38);
  background: rgba(94, 217, 168, 0.1);
}
.status-badge.is-info .status-pulse {
  background: #5ed9a8;
  animation-name: status-breathe-green;
}
@keyframes status-breathe {
  0%, 100% { opacity: 0.65; transform: scale(1); box-shadow: 0 0 0 0 rgba(148, 163, 184, 0.35); }
  50% { opacity: 1; transform: scale(1.08); box-shadow: 0 0 0 5px rgba(148, 163, 184, 0); }
}
@keyframes status-breathe-green {
  0%, 100% { opacity: 0.7; transform: scale(1); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.45); }
  50% { opacity: 1; transform: scale(1.1); box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }
}
@keyframes status-breathe-amber {
  0%, 100% { opacity: 0.7; transform: scale(1); box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.4); }
  50% { opacity: 1; transform: scale(1.1); box-shadow: 0 0 0 6px rgba(251, 191, 36, 0); }
}

.hero-section-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  flex-shrink: 0;
}
.hero-section-label {
  margin: 0;
  flex-shrink: 0;
  font-family: var(--font-mono, "JetBrains Mono", "Fira Code", monospace);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(94, 217, 168, 0.8);
}
.hero-section-rule {
  flex: 1 1 auto;
  height: 1px;
  background: linear-gradient(
    90deg,
    rgba(94, 217, 168, 0.35) 0%,
    rgba(255, 255, 255, 0.06) 70%,
    transparent 100%
  );
}

.hero-body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.hero-article {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
  color: #e5e7eb;
  font-size: 14px;
  line-height: 1.8;
}
.hero-article :deep(p),
.hero-article :deep(li),
.hero-article :deep(td),
.hero-article :deep(span) {
  color: #e5e7eb;
  font-size: 14px;
  line-height: 1.8;
}
.hero-article :deep(p) {
  margin: 0 0 0.85em;
}
.hero-article :deep(h1),
.hero-article :deep(h2),
.hero-article :deep(h3),
.hero-article :deep(h4) {
  color: #f9fafb;
  letter-spacing: -0.01em;
}
.hero-article :deep(a) {
  color: #5ed9a8;
}

.edit-area {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.25);
  color: #e5e7eb;
  font-family: var(--font-hacker);
  font-size: 14px;
  line-height: 1.6;
  resize: none;
}
.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-shrink: 0;
}


.hero-aside.poster-wrapper,
.poster-wrapper {
  width: 100%;
  height: auto;
  max-width: 100%;
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  overflow: visible; /* 允许 hover scale(1.02) 轻微溢出 */
}

.poster-container {
  /* 铺满右列宽 → 16:9 定高 → 上/下/右 = 卡片 padding 32px */
  width: 100%;
  aspect-ratio: 16 / 9;
  max-width: 100%;
  max-height: 100%;
  height: auto;
  min-height: 0;
  margin: 0;
  padding: 0;
  position: relative;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  color: inherit;
  font: inherit;
  text-align: left;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.3);
  flex: 0 0 auto;
}
.poster-container:hover {
  transform: scale(1.02);
  border-color: rgba(var(--primary-rgb), 0.42);
  box-shadow: var(--gradient-card-shadow-hover);
}
.poster-container:focus-visible {
  outline: 2px solid rgba(94, 217, 168, 0.55);
  outline-offset: 2px;
}
.poster-container:disabled {
  cursor: wait;
  opacity: 0.9;
}
.poster-container.theme-stars {
  background:
    radial-gradient(ellipse at 20% 30%, rgba(45, 181, 138, 0.18) 0%, transparent 55%),
    rgba(0, 0, 0, 0.35);
}
.poster-container.theme-suzume {
  background:
    radial-gradient(ellipse at 50% 0%, rgba(45, 181, 138, 0.2) 0%, transparent 50%),
    rgba(0, 0, 0, 0.35);
}

/* 柔化模糊底：极端比例时填满 16:9 画框 */
.poster-image-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(28px) saturate(1.1) brightness(0.45);
  transform: scale(1.1);
  pointer-events: none;
  z-index: 0;
}

.poster-image {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.45s ease;
}
.poster-container:hover .poster-image {
  transform: scale(1.04);
}

.hero-poster-fallback {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-poster-emoji { font-size: 64px; }

/* 沉浸 Hover：右下角 ENTER ARENA，废除中央胶囊 */
.poster-enter-hint {
  position: absolute;
  right: 16px;
  bottom: 14px;
  z-index: 3;
  opacity: 0;
  transform: translateY(6px);
  transition: opacity 0.28s ease, transform 0.28s ease;
  pointer-events: none;
}
.poster-container:hover .poster-enter-hint,
.poster-container:focus-visible .poster-enter-hint {
  opacity: 1;
  transform: translateY(0);
}
.poster-enter-label {
  display: inline-block;
  font-family: var(--font-mono, "JetBrains Mono", "Fira Code", monospace);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: #ecfdf5;
  padding-bottom: 3px;
  border-bottom: 1px solid rgba(94, 217, 168, 0.65);
  box-shadow: 0 6px 14px -8px rgba(94, 217, 168, 0.85);
}

.page-loading,
.page-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--muted);
}

.banned-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgba(248, 48, 48, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}
.banned-box {
  background: var(--card-bg);
  border: 2px solid var(--accent-red, #f83030);
  border-radius: var(--radius-xl);
  padding: 32px;
  text-align: center;
  max-width: 400px;
}
.banned-box h2 {
  color: var(--accent-red, #f83030);
  margin: 0 0 12px;
}

@media (max-width: 960px) {
  .game-overview-container {
    padding: 16px;
    overflow-y: auto;
    justify-content: flex-start;
  }
  .overview-hero.game-overview-card,
  .game-overview-card {
    grid-template-columns: 1fr;
    gap: 24px;
    padding: 24px !important;
    min-height: 0;
    height: auto;
    max-height: none;
    overflow: visible;
    align-items: stretch;
    flex: 0 1 auto;
    margin: 0 auto;
  }
  .overview-hero.game-overview-card.has-poster {
    padding: 24px !important;
    gap: 20px;
  }
  .overview-hero.game-overview-card.has-poster .hero-info {
    padding-right: 0;
    height: auto;
    min-height: 0;
  }
  .overview-hero.game-overview-card.has-poster .poster-wrapper {
    margin: 0;
  }
  .overview-hero.game-overview-card.has-poster .poster-container {
    min-height: 0;
    aspect-ratio: 16 / 9;
    border-radius: 12px;
  }
  .overview-hero.game-overview-card.has-poster .poster-container::after {
    width: 100%;
    height: 36%;
    inset: auto 0 0 0;
    background: linear-gradient(
      0deg,
      rgba(12, 16, 24, 0.75) 0%,
      rgba(12, 16, 24, 0) 100%
    );
  }
  .hero-info {
    height: auto;
    min-height: 0;
  }
  .poster-wrapper {
    width: 100%;
    height: auto;
    justify-content: center;
  }
  .poster-container {
    width: 100%;
    max-width: 100%;
    aspect-ratio: 16 / 9;
    height: auto;
  }
  .hero-body { max-height: 40vh; }
}

/* 左侧赛事选择列表 — 现代极客纵向 List（非药丸） */
.contest-nav-rail {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
  height: 100%;
  overflow: hidden;
}
.contest-nav-loading,
.contest-nav-empty {
  padding: 20px 14px;
  color: var(--muted);
  font-size: 13px;
  text-align: center;
}
.contest-nav-list {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 6px 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.contest-nav-item.sidebar-item,
.contest-nav-item {
  /* 纵向矩形 ListItem — Glass 基态（无左侧亮条） */
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  justify-content: center !important;
  grid-template-columns: unset !important;
  column-gap: 0 !important;
  gap: 6px !important;
  width: 100% !important;
  max-width: 100%;
  box-sizing: border-box;
  text-align: left;
  margin: 0 !important;
  padding: 10px 14px !important;
  border: 1px solid transparent !important;
  border-radius: 8px !important;
  background: transparent !important;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 0 !important;
  box-shadow: none !important;
}
.contest-nav-item .item-title {
  width: 100%;
  min-width: 0;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.4 !important;
  color: #e5e7eb;
  white-space: normal !important;
  overflow: hidden;
  text-overflow: unset;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  word-break: break-word;
}
.contest-nav-item:hover {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
  color: #e5e7eb;
}
/* 选中态：Glass Glow 柔光充盈（废除左侧竖条） */
.contest-nav-item.active {
  background: rgba(16, 185, 129, 0.08) !important;
  border: 1px solid rgba(16, 185, 129, 0.25) !important;
  box-shadow: inset 0 0 12px rgba(16, 185, 129, 0.05) !important;
  color: #ffffff !important;
}
.contest-nav-item.active .item-title {
  color: #ffffff !important;
  font-weight: 600 !important;
}
.contest-status-chip {
  align-self: flex-start;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  padding: 2px 8px;
  border-radius: 4px; /* 微圆角矩形，非 999px 药丸 */
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(148, 163, 184, 0.12);
  color: #94a3b8;
  line-height: 1.35;
}
.contest-nav-item.active .contest-status-chip {
  border-color: rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.14);
  color: #6ee7b7;
}
.contest-status-chip.is-success {
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.35);
  background: rgba(34, 197, 94, 0.12);
}
.contest-status-chip.is-warning {
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.12);
}
.contest-status-chip.is-info {
  color: #5ed9a8;
  border-color: rgba(94, 217, 168, 0.35);
  background: rgba(94, 217, 168, 0.12);
}


</style>
