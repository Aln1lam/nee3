<template>
  <GameLayout
    mode="scroll"
    :show-sidebar="true"
    :collapsible="true"
    storage-key="neepu_game_teams_sidebar"
    class="game-teams-shell"
  >
    <template #sidebar>
      <aside class="teams-nav-rail">
        <div class="sidebar-head sidebar-rail-head">
          <div class="sidebar-head-row">
            <h2 class="sidebar-title sidebar-rail-title">{{ gameTitle }}</h2>
          </div>
          <p class="sidebar-desc sidebar-rail-sub">TEAM · SQUAD</p>
        </div>
      </aside>
    </template>

    <template #sidebar-footer>
      <button
        v-if="displayMode === 'create' || displayMode === 'join'"
        type="button"
        class="sidebar-link game-layout-back"
        @click="openChoose"
      >
        <span class="link-code">BAK</span>
        <span>返回</span>
      </button>
      <router-link
        v-else
        to="/contests"
        class="sidebar-link game-layout-back"
      >
        <span class="link-code">CTF</span>
        <span>返回赛事</span>
      </router-link>
      <div class="sidebar-footer-copy" style="margin-top: 10px;">
        © 2022-2026
        <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">东北电力大学</a>
      </div>
    </template>

    <div class="game-teams-page">
    <main class="teams-main" :class="{ 'is-form-mode': displayMode === 'create' || displayMode === 'join' }">
      <header class="matrix-page-head" :class="{ 'is-compact': displayMode === 'create' || displayMode === 'join' }">
        <p class="matrix-page-prompt">战队 · {{ pageTitle }}</p>
        <template v-if="displayMode !== 'create' && displayMode !== 'join'">
          <h2 class="matrix-page-title">{{ pageTitle }}</h2>
          <p class="matrix-page-desc">{{ pageDesc }}</p>
        </template>
      </header>



      <div v-if="!team && displayMode === 'choose'" class="choose-panel">
        <div class="choose-deck matrix-panel">
          <div class="choose-deck-head">
            <span class="link-code chip-cut">SQD</span>
            <span>选择加入方式</span>
          </div>
          <div class="choose-grid">
            <button type="button" class="choose-card" @click="mode = 'create'">
              <span class="link-code chip-cut">NEW</span>
              <div class="choose-body">
                <h3>创建队伍</h3>
                <p>建立战队并获取邀请密钥</p>
              </div>
              <span class="row-arrow" aria-hidden="true">→</span>
            </button>
            <button type="button" class="choose-card" @click="mode = 'join'">
              <span class="link-code chip-cut">KEY</span>
              <div class="choose-body">
                <h3>加入队伍</h3>
                <p>使用队长提供的邀请密钥</p>
              </div>
              <span class="row-arrow" aria-hidden="true">→</span>
            </button>
          </div>
          <p class="choose-deck-foot">正式参赛以战队为单位；创建后可邀请队友，加入后可编辑所属组织。</p>
        </div>
      </div>

      <div v-else-if="displayMode === 'create' && !team" class="form-panel matrix-panel">
        <div class="form-panel-head">
          <span class="link-code chip-cut">NEW</span>
          <span>创建队伍</span>
        </div>
        <div class="form-split">
          <div class="form-stage">
            <n-form class="form-grid" label-placement="top">
              <n-form-item class="form-grid__full" label="队名">
                <n-input v-model:value="createName" placeholder="输入队伍名称" maxlength="32" show-count />
              </n-form-item>
            </n-form>
            <div class="form-actions">
              <n-button type="primary" class="save-btn" :loading="saving" @click="createTeam">创建</n-button>
            </div>
            <div v-if="createdInvite" class="invite-key-field create-invite-row">
              <span class="link-code chip-cut">KEY</span>
              <code class="invite-key-value">{{ createdInvite }}</code>
              <button type="button" class="copy-btn" @click="copyInvite">复制</button>
            </div>
          </div>
          <aside class="form-aside">
            <span class="link-code chip-cut">TIP</span>
            <ol class="form-steps">
              <li><span class="mono">01</span>填写队名并创建</li>
              <li><span class="mono">02</span>自动生成队伍密钥</li>
              <li><span class="mono">03</span>把密钥发给队友加入</li>
            </ol>
            <p class="form-aside-note">队名勿含敏感词或「官方 / admin」等保留字。</p>
          </aside>
        </div>
      </div>

      <div v-else-if="displayMode === 'join'" class="form-panel matrix-panel">
        <div class="form-panel-head">
          <span class="link-code chip-cut">KEY</span>
          <span>加入队伍</span>
        </div>
        <div class="form-split">
          <div class="form-stage">
            <n-form class="form-grid" label-placement="top">
              <n-form-item class="form-grid__full" label="邀请密钥">
                <n-input class="mono-input" v-model:value="joinCode" placeholder="粘贴或输入邀请密钥" />
              </n-form-item>
            </n-form>
            <div class="form-actions">
              <n-button type="primary" class="save-btn" :loading="saving" @click="joinTeam">加入</n-button>
            </div>
          </div>
          <aside class="form-aside">
            <span class="link-code chip-cut">TIP</span>
            <ol class="form-steps">
              <li><span class="mono">01</span>向队长索取队伍密钥</li>
              <li><span class="mono">02</span>粘贴密钥并确认加入</li>
              <li><span class="mono">03</span>进入队伍页查看成员</li>
            </ol>
            <p class="form-aside-note">密钥区分大小写，完整粘贴即可。</p>
          </aside>
        </div>
      </div>

      <div v-else-if="displayMode === 'manage' && team" class="manage-panel">
        <div v-if="!inGame" class="teams-banner" role="status">
          <span class="link-code">REG</span>
          <p class="teams-banner-copy">
            队伍已创建，但尚未报名本赛事。
            <template v-if="isCampusGame">校内赛需邀请码。</template>
          </p>
          <button type="button" class="teams-banner-cta" :disabled="saving" @click="registerForGame">
            {{ saving ? '处理中…' : (isCampusGame ? '输入邀请码报名' : '立即报名') }}
          </button>
        </div>

        <div class="matrix-panel manage-deck">
          <header class="team-id-head">
            <span class="link-code chip-cut">TEA</span>
            <div class="team-id-copy">
              <h3 class="identity-name">{{ team.name }}</h3>
            </div>
          </header>
          <div class="member-block member-block--in-deck">
            <div class="member-block-head">
              <span class="link-code">MEM</span>
              <span>成员</span>
              <span class="member-count mono">{{ memberCount }}</span>
            </div>
            <div class="member-list member-list--scroll">
              <div
                v-for="m in team.members"
                :key="m.id"
                class="member-row"
                :title="'#' + ((m.id || 0).toString(16).padStart(6, '0'))"
              >
                <n-avatar :size="22" color="var(--primary)">{{ (m.nickname || 'U').slice(0, 1) }}</n-avatar>
                <span class="member-name">{{ m.nickname || m.username }}</span>
              </div>
            </div>
          </div>

          <n-form class="form-grid" label-placement="top">
            <n-form-item label="队伍密钥">
              <div class="invite-key-field">
                <code class="invite-key-value">{{ team.invite_code }}</code>
                <button type="button" class="copy-btn" @click="copyInvite">复制</button>
              </div>
            </n-form-item>
            <n-form-item :label="isCampusGame ? '所属组织（校内）' : '所属组织（大学）'">
              <n-input
                v-model:value="editSchool"
                :disabled="gameEnded || isCampusGame"
                maxlength="128"
                :show-count="!isCampusGame"
                :placeholder="isCampusGame ? CAMPUS_ORG : '请填写本校全称，如：××大学'"
              />
            </n-form-item>
          </n-form>
          <div class="form-actions">
            <n-button type="primary" class="save-btn" :loading="saving" @click="saveTeam">保存</n-button>
            <n-popconfirm @positive-click="leaveTeam">
              <template #trigger>
                <n-button type="error" quaternary class="leave-btn">离开队伍</n-button>
              </template>
              确定要离开当前队伍吗？
            </n-popconfirm>
          </div>
        </div>

        <section class="solve-section matrix-panel">
          <div class="section-head">
            <span class="link-code">SOL</span>
            <h3>解题状况</h3>
          </div>
          <div v-if="!solves.length" class="muted">暂无解题记录</div>
          <ul v-else class="solve-list">
            <li v-for="s in solves" :key="s.id">
              <span class="link-code">FLG</span>
              <span>
                成员 <strong>{{ s.nickname }}</strong> 解出了题目
                <a href="#" class="solve-link" @click.prevent="goChallenge(s.challenge_id)">{{ s.challenge_title }}</a>。
                <span v-if="s.blood_label" class="blood-tag" :data-level="s.blood_level">{{ s.blood_label }}</span>
                {{ s.points }} pts · {{ formatTime(s.submitted_at) }}
              </span>
            </li>
          </ul>
        </section>
      </div>

      <div v-else class="empty-main matrix-panel">
        <div class="choose-deck-head">
          <span class="link-code chip-cut">SQD</span>
          <span>尚未加入战队</span>
        </div>
        <p class="empty-copy">报名参赛时可自动创建单人队，也可先在此创建或加入。</p>
        <button type="button" class="choose-card empty-cta" @click="openChoose">
          <span class="link-code chip-cut">JOIN</span>
          <div class="choose-body">
            <h3>创建 / 加入队伍</h3>
            <p>进入战队工作台</p>
          </div>
          <span class="row-arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </main>
  <n-modal
        v-model:show="showGameInviteModal"
        :mask-closable="false"
        transform-origin="center"
        class="invite-join-modal-root"
      >
        <div class="invite-join-card" role="dialog" aria-modal="true" aria-labelledby="invite-join-title-tm">
          <header class="invite-join-head">
            <span class="link-code chip-cut">KEY</span>
            <h3 id="invite-join-title-tm">校内赛邀请码</h3>
          </header>
          <p class="invite-join-desc">本场为校内赛，报名需赛事邀请码（与上方队伍密钥不同）。</p>
          <label class="invite-join-label" for="invite-code-input-tm">邀请码</label>
          <n-input
            id="invite-code-input-tm"
            v-model:value="gameInviteInput"
            class="invite-join-input"
            placeholder="粘贴或输入邀请码"
            maxlength="64"
            @keydown.enter.prevent="confirmGameInviteJoin"
          />
          <div class="invite-join-actions">
            <button type="button" class="invite-join-btn invite-join-btn--ghost" :disabled="saving" @click="showGameInviteModal = false">取消</button>
            <button type="button" class="invite-join-btn invite-join-btn--primary" :disabled="saving" @click="confirmGameInviteJoin">
              {{ saving ? '校验中…' : '确认报名' }}
            </button>
          </div>
        </div>
      </n-modal>

  </div>
  </GameLayout>
</template>

<script>
import { ref, computed, inject, onMounted, watch } from 'vue'
import * as teamsApi from '@/services/teams'
import { apiErrorMessage } from '@/utils/apiError'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NForm, NFormItem, NInput, NInputGroup, NModal,
  NAvatar, NPopconfirm, useMessage,
} from 'naive-ui'
import { unwrapTeamResponse, unwrapTeamInvite } from '../utils/team'
import {
  CAMPUS_ORG, gameNeedsInvite, gameIsOpenPublic, validateOrgInput,
} from '../utils/competitionJoin'
import '../assets/invite-join-modal.css'
import GameLayout from './GameLayout.vue'

export default {
  name: 'GameTeams',
  components: {
    GameLayout,
    NButton, NForm, NFormItem, NInput, NInputGroup, NModal,
    NAvatar, NPopconfirm,
  },
  props: { id: { type: [String, Number], default: null } },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()


    const gameId = computed(() => props.id || route.params.id)
    const team = ref(null)
    const solves = ref([])
    const mode = ref('choose')
    const saving = ref(false)
    const gameEnded = ref(false)
    const inGame = ref(false)

    const createName = ref('')
    const joinCode = ref('')
    const createdInvite = ref('')
    const editName = ref('')
    const editSchool = ref('无组织')
    const gameMeta = ref(null)
    const showGameInviteModal = ref(false)
    const gameInviteInput = ref('')
    const isCampusGame = computed(() => gameNeedsInvite(gameMeta.value))
    const isOpenGame = computed(() => gameIsOpenPublic(gameMeta.value))

    const hexId = computed(() => (team.value?.id || 0).toString(16).padStart(6, '0'))
    const memberCount = computed(() => (team.value?.members || []).length)

    const displayMode = computed(() => {
      if (!team.value && mode.value === 'manage') return 'choose'
      if (mode.value === 'list' || mode.value === 'profile') {
        return team.value ? 'manage' : 'choose'
      }
      return mode.value
    })

    const pageCmd = computed(() => {
      const map = {
        choose: 'team join',
        create: 'team new',
        join: 'team join',
        manage: 'team manage',
        profile: 'team show',
      }
      return map[displayMode.value] || 'team status'
    })

    const pageTitle = computed(() => {
      const map = {
        choose: '创建或加入队伍',
        create: '创建队伍',
        join: '加入队伍',
        manage: '队伍管理',
      }
      return map[displayMode.value] || '战队中心'
    })

    const pageDesc = computed(() => {
      const map = {
        choose: '正式赛事以战队为单位报名参赛。你可以创建新队伍，或使用邀请码加入队友的战队。',
        create: '填写队名，创建后自动获取邀请码',
        join: '向队长索取邀请码，输入后即可加入战队',
        manage: '编辑组织 · 查看解题记录',
      }
      return map[displayMode.value] || 'TEAM · SQUAD'
    })

    const gameTitle = computed(() => gameMeta.value?.title || '战队')

    function memberCode(m) {
      const id = m?.id || 0
      return `M${id.toString(16).slice(-2).toUpperCase().padStart(2, '0')}`
    }

    function openChoose() {
      mode.value = 'choose'
    }


    function openManage() {
      mode.value = team.value ? 'manage' : 'choose'
    }

    function formatTime(t) {
      if (!t) return '-'
      try { return new Date(t).toLocaleString('zh-CN') } catch { return t }
    }

    async function loadTeam() {
      try {
        const { data } = await axios.get('/api/teams/me', {
          params: { game_id: gameId.value },
        })
        const parsed = unwrapTeamResponse(data)
        inGame.value = !!(data?.in_game ?? parsed?.in_game)
        if (parsed) {
          team.value = parsed
          editName.value = parsed.name || ''
          editSchool.value = isCampusGame.value
            ? CAMPUS_ORG
            : (parsed.school || '')
          if (route.path.endsWith('/create')) {
            message.info('你已有所属队伍')
            router.replace(`/games/${gameId.value}/teams`)
            mode.value = 'manage'
            return
          }
          if (!route.path.endsWith('/create') && !route.path.endsWith('/join') && !route.params.teamId) {
            mode.value = 'manage'
          }
        } else {
          team.value = null
          inGame.value = false
          if (route.path.endsWith('/create')) mode.value = 'create'
          else if (route.path.endsWith('/join')) mode.value = 'join'
          else if (!route.params.teamId) mode.value = 'choose'
        }
      } catch {
        team.value = null
        inGame.value = false
      }
    }

    async function loadGameMeta() {
      if (!gameId.value) return
      try {
        const { data } = await axios.get(`/api/competitions/${gameId.value}`)
        gameMeta.value = data?.data || data
        if (isCampusGame.value) editSchool.value = CAMPUS_ORG
      } catch {
        gameMeta.value = null
      }
    }

    async function joinCompetition(inviteCode) {
      if (!gameId.value) return
      const body = {}
      if (inviteCode) body.invite_code = String(inviteCode).trim()
      try {
        await axios.post(`/api/competitions/${gameId.value}/join`, body)
      } catch (e) {
        const msg = e.response?.data?.msg || ''
        if (e.response?.status === 200 || /已经参加|已报名/.test(msg)) return
        throw e
      }
      if (isCampusGame.value && team.value?.id) {
        try {
          await teamsApi.updateTeam(team.value.id, { school: CAMPUS_ORG })
          editSchool.value = CAMPUS_ORG
        } catch { /* ignore */ }
      }
    }

    function openGameInviteModal() {
      gameInviteInput.value = ''
      showGameInviteModal.value = true
    }

    async function confirmGameInviteJoin() {
      const code = gameInviteInput.value.trim()
      if (!code) {
        message.warning('请输入赛事邀请码')
        return
      }
      saving.value = true
      try {
        await joinCompetition(code)
        inGame.value = true
        showGameInviteModal.value = false
        message.success('已报名本赛事')
        await loadTeam()
      } catch (e) {
        message.error(e.response?.data?.msg || '报名失败')
      } finally {
        saving.value = false
      }
    }


    async function loadSolves() {
      if (!team.value?.id) return
      try {
        const { data } = await axios.get(`/api/teams/${team.value.id}/solves`, {
          params: { game_id: gameId.value },
        })
        solves.value = data?.solves || data || []
      } catch {
        solves.value = []
      }
    }

    async function createTeam() {
      if (saving.value) return
      if (!createName.value.trim()) {
        message.warning('请输入队名')
        return
      }
      saving.value = true
      try {
        const data = await teamsApi.createTeam({
          name: createName.value,
          game_id: parseInt(gameId.value, 10),
        })
        createdInvite.value = unwrapTeamInvite(data)
        message.success('队伍创建成功')
        await loadTeam()
        if (isCampusGame.value) {
          message.info('请填写校内赛邀请码完成报名')
          openGameInviteModal()
        } else {
          await joinCompetition()
          inGame.value = true
          message.success('已为本赛事报名')
          await loadTeam()
        }
      } catch (e) {
        message.error(apiErrorMessage(e, '创建失败'))
      } finally {
        saving.value = false
      }
    }

    async function joinTeam() {
      if (saving.value) return
      if (!joinCode.value.trim()) return
      saving.value = true
      try {
        await teamsApi.joinTeam({
          invite_code: joinCode.value,
          game_id: parseInt(gameId.value, 10),
        })
        message.success('加入成功')
        await loadTeam()
        if (isCampusGame.value) {
          message.info('请填写校内赛邀请码完成报名')
          openGameInviteModal()
        } else {
          await joinCompetition()
          inGame.value = true
          message.success('已为本赛事报名')
          await loadTeam()
        }
      } catch (e) {
        message.error(apiErrorMessage(e, '加入失败'))
      } finally {
        saving.value = false
      }
    }

    async function registerForGame() {
      if (saving.value) return
      if (isCampusGame.value) {
        openGameInviteModal()
        return
      }
      saving.value = true
      try {
        await joinCompetition()
        inGame.value = true
        message.success('已报名本赛事')
        await loadTeam()
      } catch (e) {
        const msg = e.response?.data?.msg || '报名失败'
        if (/邀请码/.test(msg)) openGameInviteModal()
        else message.error(msg)
      } finally {
        saving.value = false
      }
    }

    async function saveTeam() {
      if (!team.value) return
      const org = validateOrgInput(editSchool.value, { campus: isCampusGame.value })
      if (!org.ok) {
        message.warning(org.msg)
        return
      }
      saving.value = true
      try {
        await teamsApi.updateTeam(team.value.id, {
          name: editName.value,
          school: org.value,
        })
        message.success('已保存')
        await loadTeam()
      } catch (e) {
        message.error(apiErrorMessage(e, '保存失败'))
      } finally {
        saving.value = false
      }
    }

    async function leaveTeam() {
      if (!team.value) return
      try {
        await teamsApi.leaveTeam(team.value.id)
        team.value = null
        mode.value = 'choose'
        message.success('已离开队伍')
      } catch (e) {
        message.error(e.response?.data?.msg || '操作失败')
      }
    }

    function goChallenge(challengeId) {
      router.push(`/games/${gameId.value}/challenges?challenge=${challengeId}`)
    }

    function copyInvite() {
      const code = createdInvite.value || team.value?.invite_code
      if (code) navigator.clipboard?.writeText(code)
      message.success('已复制邀请码')
    }

    function viewTeam(_t) {
      message.info('队伍名单请到运维后台：靶场管理 → 队伍管理')
    }

    async function loadViewedTeam(teamId) {
      if (!teamId) return
      // 其他队伍详情已迁至运维后台「靶场管理 → 队伍管理」
      router.replace(`/games/${gameId.value}/teams`)
    }

    watch(() => route.path, () => {
      if (route.path.endsWith('/create')) mode.value = 'create'
      else if (route.path.endsWith('/join')) mode.value = 'join'
      else if (route.path.endsWith('/choose')) mode.value = 'choose'
    }, { immediate: true })

    watch(() => route.params.teamId, (id) => {
      loadViewedTeam(id)
    }, { immediate: true })

    watch(team, (t) => {
      if (t) loadSolves()
    })

    onMounted(async () => {
      await loadGameMeta()
      await loadTeam()
      try {
        const { data } = await axios.get(`/api/competitions/${gameId.value}`)
        const g = data?.data || data
        if (g?.end_time && Date.now() > new Date(g.end_time).getTime()) gameEnded.value = true
      } catch { /* ignore */ }
    })

    return {
      gameId, team, solves, mode, displayMode, saving, gameEnded, inGame,
      createName, joinCode, createdInvite, editName, editSchool,
      memberCount, hexId, pageCmd, pageTitle, pageDesc, gameTitle,
      isCampusGame, isOpenGame, CAMPUS_ORG,
      showGameInviteModal, gameInviteInput, confirmGameInviteJoin,
      formatTime, createTeam, joinTeam, saveTeam, leaveTeam, copyInvite, viewTeam, goChallenge, registerForGame,
      openChoose, openManage, memberCode,
    }
  },
}
</script>

<style scoped>
.teams-nav-rail {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
}

.game-teams-shell :deep(.game-layout-main) {
  padding: 0;
}

.game-teams-page {
  margin: 0;
  height: 100%;
  max-height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
}

.teams-main {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
  padding: 22px 24px 48px;
  box-sizing: border-box;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

.teams-main > .matrix-page-head {
  margin: 0 0 18px;
  padding: 0 0 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.teams-main > .matrix-page-head.is-compact {
  margin-bottom: 12px;
  padding-bottom: 8px;
}

.teams-main > .matrix-page-head.is-compact .matrix-page-prompt {
  margin: 0;
}

.teams-main > .matrix-page-head .matrix-page-title {
  margin: 0;
  font-size: 1.2rem;
  line-height: 1.3;
  color: var(--text, #e5e7eb);
  font-weight: 600;
}

.teams-main > .matrix-page-head .matrix-page-desc {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--muted, #9ca3af);
  max-width: 40rem;
}

.mode-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 12px;
}

.mode-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--muted);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.mode-tab:hover,
.mode-tab.active {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.35);
  color: var(--primary, #5ED9A8);
}

.mode-tab.join-cta { margin-top: 10px; }

/* 卡片：半透明面 + 细边，禁止 blur 糊正文 */
.matrix-panel {
  padding: 16px 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--card-radius, 10px);
  background: rgba(22, 26, 36, 0.88);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.matrix-panel:hover {
  border-color: rgba(255, 255, 255, 0.12);
}

.manage-deck:hover {
  border-color: rgba(var(--primary-rgb), 0.28);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.team-summary { margin-bottom: 12px; }

/* 身份条：Chip + 队名主信号 + 一行 muted 元信息（禁药丸堆砌） */
.team-id-head {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: start;
  gap: 10px 12px;
  margin: 0 0 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.team-id-copy {
  min-width: 0;
}

.identity-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--text, #e5e7eb);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mono,
.member-hex {
  font-family: var(--font-mono), "JetBrains Mono", "Fira Code", ui-monospace, monospace !important;
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0;
  letter-spacing: 0.04em;
  -webkit-font-smoothing: antialiased;
}

.member-block {
  margin-bottom: 4px;
}

.member-block--in-deck {
  padding-bottom: 14px;
  margin-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.member-block-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--muted, #9ca3af);
}

.member-count {
  margin-left: auto;
  font-size: 11px;
  color: var(--muted, #9ca3af);
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 0;
}

.member-list--scroll {
  max-height: min(200px, 32vh);
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  padding-right: 2px;
}

/* 成员行：8px 矩形，禁止药丸列表 */
.member-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  font-size: 13px;
  transition: border-color 0.15s, background 0.15s;
}

.member-row:hover {
  border-color: rgba(16, 185, 129, 0.28);
  background: rgba(16, 185, 129, 0.06);
}

.member-name {
  flex: 1;
  min-width: 0;
  color: var(--text, #e5e7eb);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-hex {
  font-size: 11px;
  color: var(--muted, #9ca3af);
}



.link-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.row-arrow {
  font-size: 12px;
  color: var(--muted);
}

.list-panel,
.manage-panel {
  width: 100%;
}

.teams-banner {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 10px 12px;
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: var(--card-radius, 10px);
  border: 1px solid rgba(16, 185, 129, 0.28);
  background: rgba(16, 185, 129, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.teams-banner-copy {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text, #e5e7eb);
}

.teams-banner-cta {
  height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid rgba(16, 185, 129, 0.45);
  background: #10b981;
  color: #0a0f14;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: box-shadow 0.15s, filter 0.15s;
}

.teams-banner-cta:hover:not(:disabled) {
  box-shadow: 0 0 18px rgba(16, 185, 129, 0.28);
}

.teams-banner-cta:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .teams-banner {
    grid-template-columns: auto 1fr;
  }
  .teams-banner-cta {
    grid-column: 1 / -1;
    width: 100%;
  }
}


.choose-panel,
.list-panel,
.manage-panel {
  width: 100%;
}

.choose-deck {
  padding: 22px 22px 24px;
}

.choose-deck-head,
.form-panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 12px;
  color: var(--muted, #9ca3af);
}

/* back lives in sidebar-footer (BAK / CTF) */

.choose-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.choose-card {
  display: grid !important;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  justify-content: stretch;
  gap: 14px;
  width: 100%;
  box-sizing: border-box;
  min-height: 112px !important;
  height: auto !important;
  padding: 22px 20px !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s, transform 0.15s;
}

.choose-card:hover {
  border-color: rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.08);
  box-shadow: inset 0 0 0 1px rgba(16, 185, 129, 0.12), 0 0 20px rgba(16, 185, 129, 0.12);
  transform: translateY(-2px);
}

.choose-card:hover .row-arrow {
  color: var(--primary, #5ED9A8);
}

.choose-body h3 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text, #e5e7eb);
}

.choose-body p {
  margin: 0;
  font-size: 13px;
  color: var(--muted, #9ca3af);
  line-height: 1.55;
}

.form-panel {
  width: 100%;
  max-width: none;
  padding: 22px 22px 24px;
}

.form-split {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  align-items: start;
}

.form-stage {
  min-width: 0;
}

.form-aside {
  min-width: 0;
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.form-aside .link-code {
  display: inline-flex;
  margin-bottom: 8px;
}

.form-aside p,
.form-aside-note {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--muted, #9ca3af);
}

.form-steps {
  margin: 0 0 12px;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.form-steps li {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text, #e5e7eb);
}

.form-steps .mono {
  flex: 0 0 auto;
  min-width: 1.6em;
  color: var(--primary, #5ED9A8);
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  opacity: 0.9;
}

.form-aside-note {
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 12px !important;
}

.teams-main.is-form-mode {
  max-width: 560px;
}

.teams-main.is-form-mode .form-panel {
  padding: 22px 22px 24px;
}

.teams-main.is-form-mode .form-stage {
  display: flex;
  flex-direction: column;
  padding: 0 0 4px;
}

.teams-main.is-form-mode .form-aside {
  display: flex;
  flex-direction: column;
}

.teams-main.is-form-mode .save-btn {
  min-width: 120px;
}

.game-teams-page:has(.teams-main.is-form-mode),
.game-teams-page:has(.choose-panel) {
  background:
    radial-gradient(ellipse 72% 58% at 42% 28%, rgba(94, 217, 168, 0.08), transparent 68%),
    radial-gradient(ellipse 50% 40% at 78% 72%, rgba(94, 217, 168, 0.04), transparent 70%),
    var(--page-bg, #0b0e14);
}

.create-invite-row {
  margin-top: 14px;
}

/* choose stays stacked — avoid wide flat twin strips */

.empty-main {
  max-width: 560px;
  padding: 18px 20px;
}

.empty-copy {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--muted, #9ca3af);
}

.empty-cta {
  min-height: 72px;
}

.choose-deck-foot {
  margin: 14px 0 0;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 12px;
  line-height: 1.5;
  color: var(--muted, #9ca3af);
}

@media (max-width: 720px) {
  .choose-grid {
    grid-template-columns: 1fr;
  }
}

.manage-deck {
  margin-bottom: 14px;
  padding: 18px 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 14px;
  row-gap: 2px;
}

.form-grid :deep(.n-form-item) {
  margin-bottom: 12px;
}

.form-grid :deep(.n-form-item-label) {
  font-size: 12px !important;
  color: var(--muted, #9ca3af) !important;
}

.form-grid__full { grid-column: 1 / -1; }

/* 密钥：原生 code，强制锐利等宽，绝不走 Naive Input */
.invite-key-field {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 44px;
  padding: 0 8px 0 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  box-sizing: border-box;
}

.invite-key-field:hover {
  border-color: rgba(16, 185, 129, 0.35);
}

.invite-key-value {
  flex: 1;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: #ecfdf5;
  font-family: var(--font-mono), "JetBrains Mono", "Fira Code", ui-monospace, monospace !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0;
  letter-spacing: 0.08em;
  line-height: 1.2;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
  text-shadow: none !important;
  filter: none !important;
  user-select: all;
}

.copy-btn {
  flex-shrink: 0;
  height: 32px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid rgba(16, 185, 129, 0.4);
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.22), rgba(16, 185, 129, 0.1));
  color: #6ee7b7;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.copy-btn:hover {
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.36), rgba(16, 185, 129, 0.16));
  border-color: rgba(16, 185, 129, 0.65);
  box-shadow: 0 0 18px rgba(16, 185, 129, 0.22);
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.save-btn {
  min-height: 44px !important;
  height: 44px !important;
  padding: 0 22px !important;
  font-weight: 600 !important;
}

.leave-btn {
  color: #f87171 !important;
}

.field-hint {
  margin: 6px 0 0;
  font-size: 11px;
  color: var(--muted, #9ca3af);
}

/* 常规输入：浅底细边，focus 薄荷绿，无 blur */
.game-teams-page :deep(.n-input),
.game-teams-page :deep(.n-base-selection) {
  min-height: 44px !important;
  --n-height: 42px !important;
  --n-color: rgba(255, 255, 255, 0.04) !important;
  --n-color-focus: rgba(255, 255, 255, 0.05) !important;
  --n-border: 1px solid rgba(255, 255, 255, 0.1) !important;
  --n-border-hover: 1px solid rgba(16, 185, 129, 0.4) !important;
  --n-border-focus: 1px solid rgba(16, 185, 129, 0.5) !important;
  --n-box-shadow-focus: 0 0 0 1px rgba(16, 185, 129, 0.25) !important;
  --n-text-color: #ffffff !important;
  --n-caret-color: var(--primary, #5ED9A8) !important;
  border-radius: 8px;
}

.game-teams-page :deep(.n-input .n-input__input-el),
.game-teams-page :deep(.n-input .n-input__textarea-el) {
  font-size: 14px !important;
  color: #ffffff !important;
  -webkit-font-smoothing: antialiased;
}

.game-teams-page :deep(.mono-input .n-input__input-el) {
  font-family: var(--font-mono), "JetBrains Mono", "Fira Code", ui-monospace, monospace !important;
  font-weight: 600 !important;
  font-variant-ligatures: none;
  letter-spacing: 0.06em;
  color: #ecfdf5 !important;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.section-head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text, #e5e7eb);
}

.solve-section {
  margin-top: 10px;
}

.blood-tag {
  display: inline-block;
  margin: 0 4px;
  padding: 0 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  border: 1px solid rgba(45, 181, 138, 0.45);
  color: #2db58a;
  background: rgba(45, 181, 138, 0.12);
}

.blood-tag[data-level="0"] {
  border-color: rgba(250, 204, 21, 0.55);
  color: #facc15;
  background: rgba(250, 204, 21, 0.12);
}

.blood-tag[data-level="1"] {
  border-color: rgba(148, 163, 184, 0.55);
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.12);
}

.blood-tag[data-level="2"] {
  border-color: rgba(205, 127, 50, 0.55);
  color: #d97706;
  background: rgba(205, 127, 50, 0.12);
}

.muted {
  color: var(--muted, #9ca3af);
  font-size: 13px;
}

.solve-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.solve-list li {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 13px;
}

.solve-link {
  color: var(--primary, #5ED9A8);
  text-decoration: none;
}

.solve-link:hover { text-decoration: underline; }

.public-team-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.public-team {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(22, 26, 36, 0.75);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.public-team:hover {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.08);
}

.team-name {
  font-weight: 600;
  color: var(--text, #e5e7eb);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-meta {
  font-size: 12px;
  color: var(--muted);
  white-space: nowrap;
}

.empty-list,
.empty-main {
  text-align: left;
  padding: 28px 0;
  color: var(--muted);
  max-width: 480px;
}

@media (max-width: 720px) {
  .teams-main { max-width: none; }
  .form-grid { grid-template-columns: 1fr; }
  .choose-grid { grid-template-columns: 1fr; }
}
</style>
