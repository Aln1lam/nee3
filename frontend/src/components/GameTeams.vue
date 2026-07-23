<template>
  <div class="game-teams-page">
    <main class="teams-main">
      <header class="matrix-page-head">
        <p class="matrix-page-prompt">战队 · {{ pageTitle }}</p>
        <h2 class="matrix-page-title">{{ pageTitle }}</h2>
        <p class="matrix-page-desc">{{ pageDesc }}</p>
      </header>

      <nav v-if="showModeTabs" class="mode-tabs">
        <button
          type="button"
          class="mode-tab"
          :class="{ active: displayMode === 'manage' }"
          @click="openManage"
        >
          <span class="link-code">MGT</span>
          <span>队伍管理</span>
        </button>
        <button
          type="button"
          class="mode-tab"
          :class="{ active: displayMode === 'list' }"
          @click="mode = 'list'"
        >
          <span class="link-code">LST</span>
          <span>公开列表</span>
        </button>
      </nav>

      <div v-if="team" class="team-summary matrix-panel">
        <div class="team-card-head">
          <span class="link-code">TEA</span>
          <h3>{{ team.name }}</h3>
        </div>
        <div class="team-tags">
          <n-tag size="small" round>#{{ hexId }}</n-tag>
          <n-tag size="small" type="default" round>{{ team.school || '无组织' }}</n-tag>
        </div>
        <div class="member-list">
          <div v-for="m in team.members" :key="m.id" class="member-row">
            <span class="link-code">{{ memberCode(m) }}</span>
            <n-avatar size="small" color="var(--primary)">{{ (m.nickname || 'U').slice(0, 1) }}</n-avatar>
            <span class="member-name">{{ m.nickname || m.username }}</span>
            <span class="member-hex">#{{ (m.id || 0).toString(16).padStart(6, '0') }}</span>
          </div>
        </div>
      </div>

      <div v-if="!team && displayMode === 'choose'" class="choose-panel">
        <div class="choose-grid">
          <button type="button" class="choose-card" @click="mode = 'create'">
            <span class="link-code">NEW</span>
            <div class="choose-body">
              <h3>创建队伍</h3>
              <p>建立属于你的战队，获取邀请码邀请队友</p>
            </div>
            <span class="row-arrow">→</span>
          </button>
          <button type="button" class="choose-card" @click="mode = 'join'">
            <span class="link-code">KEY</span>
            <div class="choose-body">
              <h3>加入队伍</h3>
              <p>输入邀请码加入已有战队</p>
            </div>
            <span class="row-arrow">→</span>
          </button>
        </div>
      </div>

      <div v-else-if="displayMode === 'create' && !team" class="form-panel matrix-panel">
        <n-form label-placement="top">
          <n-form-item label="队名">
            <n-input v-model:value="createName" placeholder="输入队伍名称" maxlength="32" show-count />
            <p class="field-hint">勿含敏感词或「官方 / admin」等保留字</p>
          </n-form-item>
          <n-form-item label="标签（显示在排行榜昵称下方）">
            <n-input v-model:value="createTag" placeholder="可选" />
          </n-form-item>
        </n-form>
        <div class="form-actions">
          <n-button type="primary" :loading="saving" @click="createTeam">创建</n-button>
          <n-button @click="mode = 'choose'">返回</n-button>
        </div>
        <div v-if="createdInvite" class="invite-box">
          <span class="link-code">KEY</span>
          <span>邀请码：<code>{{ createdInvite }}</code></span>
          <n-button size="tiny" @click="copyInvite">复制</n-button>
        </div>
      </div>

      <div v-else-if="displayMode === 'join'" class="form-panel matrix-panel">
        <n-input v-model:value="joinCode" placeholder="输入邀请码" />
        <div class="form-actions">
          <n-button type="primary" :loading="saving" @click="joinTeam">加入</n-button>
          <n-button @click="mode = 'choose'">返回</n-button>
        </div>
      </div>

      <div v-else-if="displayMode === 'manage' && team" class="manage-panel">
        <n-alert v-if="!inGame" type="warning" style="margin-bottom: 16px">
          队伍已创建，但尚未报名本赛事。
          <n-button size="tiny" type="primary" :loading="saving" @click="registerForGame">立即报名</n-button>
        </n-alert>

        <div class="matrix-panel manage-form">
          <n-form label-placement="top">
            <n-form-item label="队伍密钥">
              <n-input-group>
                <n-input :value="team.invite_code" readonly />
                <n-button @click="copyInvite">复制</n-button>
              </n-input-group>
            </n-form-item>
            <n-form-item label="队伍名称">
              <n-input v-model:value="editName" :disabled="gameEnded" />
            </n-form-item>
            <n-form-item label="所属组织">
              <n-select
                v-model:value="editSchool"
                :options="schoolOptions"
                filterable
                tag
                clearable
                placeholder="选择或输入组织"
              />
            </n-form-item>
            <n-form-item label="标签文字">
              <n-input v-model:value="editTag" placeholder="排行榜显示标签" />
            </n-form-item>
          </n-form>
          <div class="form-actions">
            <n-button type="primary" :loading="saving" @click="saveTeam">保存</n-button>
            <n-popconfirm @positive-click="leaveTeam">
              <template #trigger>
                <n-button type="error" quaternary>离开队伍</n-button>
              </template>
              确定要离开当前队伍吗？
            </n-popconfirm>
          </div>
        </div>

        <section class="score-section matrix-panel" v-if="team">
          <div class="section-head">
            <span class="link-code">SCR</span>
            <h3>得分曲线</h3>
          </div>
          <div ref="scoreChartRef" class="score-chart"></div>
        </section>

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
                {{ s.points }} pts · {{ formatTime(s.submitted_at) }}
              </span>
            </li>
          </ul>
        </section>

        <section class="extra-section matrix-panel">
          <div class="section-head">
            <span class="link-code">EXT</span>
            <h3>额外分数变动</h3>
          </div>
          <p class="muted">没有额外分数变动</p>
        </section>
      </div>

      <div v-else-if="displayMode === 'profile' && viewedTeam" class="team-summary matrix-panel">
        <div class="team-card-head">
          <span class="link-code">TEA</span>
          <h3>{{ viewedTeam.name }}</h3>
          <n-button size="tiny" quaternary @click="router.push(`/games/${gameId}/teams`)">返回列表</n-button>
        </div>
        <div class="team-tags">
          <n-tag size="small" round>#{{ (viewedTeam.id || 0).toString(16).padStart(6, '0') }}</n-tag>
          <n-tag size="small" type="default" round>{{ viewedTeam.school || '无组织' }}</n-tag>
        </div>
        <div class="member-list">
          <div v-for="m in (viewedTeam.members || [])" :key="m.id" class="member-row">
            <span class="link-code">{{ memberCode(m) }}</span>
            <n-avatar size="small" color="var(--primary)">{{ (m.nickname || 'U').slice(0, 1) }}</n-avatar>
            <span class="member-name">{{ m.nickname || m.username }}</span>
          </div>
        </div>
      </div>

      <div v-else-if="displayMode === 'list'" class="list-panel">
        <n-spin :show="listLoading">
          <div v-if="allTeams.length" class="public-team-list">
            <button
              v-for="t in allTeams"
              :key="t.id"
              type="button"
              class="public-team"
              @click="viewTeam(t)"
            >
              <span class="link-code">TEA</span>
              <span class="team-name">{{ t.name }}</span>
              <span class="team-meta">{{ t.members_count || 0 }} 人 · #{{ t.id }}</span>
            </button>
          </div>
          <div v-else-if="!listLoading" class="empty-list">
            <p class="muted">暂无队伍</p>
          </div>
        </n-spin>
      </div>

      <div v-else class="empty-main">
        <p>报名参赛时将自动创建单人队；也可在此主动创建或加入战队</p>
        <button type="button" class="mode-tab join-cta" @click="openChoose">
          <span class="link-code">JOIN</span>
          <span>创建 / 加入队伍</span>
          <span class="row-arrow">→</span>
        </button>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as teamsApi from '@/services/teams'
import { apiErrorMessage } from '@/utils/apiError'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NForm, NFormItem, NInput, NInputGroup, NSelect,
  NTag, NAvatar, NSpin, NPopconfirm, NAlert, useMessage,
} from 'naive-ui'
import * as echarts from 'echarts'
import { unwrapTeamResponse, unwrapTeamInvite } from '../utils/team'

export default {
  name: 'GameTeams',
  components: {
    NButton, NForm, NFormItem, NInput, NInputGroup, NSelect,
    NTag, NAvatar, NSpin, NPopconfirm, NAlert, 
  },
  props: { id: { type: [String, Number], default: null } },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()
    const router = useRouter()
    const message = useMessage()

    const scoreChartRef = ref(null)
    let scoreChart = null

    const gameId = computed(() => props.id || route.params.id)
    const team = ref(null)
    const viewedTeam = ref(null)
    const allTeams = ref([])
    const solves = ref([])
    const mode = ref('choose')
    const saving = ref(false)
    const listLoading = ref(false)
    const gameEnded = ref(false)
    const inGame = ref(false)

    const createName = ref('')
    const createTag = ref('')
    const joinCode = ref('')
    const createdInvite = ref('')
    const editName = ref('')
    const editTag = ref('')
    const editSchool = ref(null)

    const schoolOptions = [
      { label: '东北电力大学', value: '东北电力大学' },
      { label: '无组织', value: '无组织' },
      { label: '高校', value: '高校' },
    ]

    const hexId = computed(() => (team.value?.id || 0).toString(16).padStart(6, '0'))

    const displayMode = computed(() => {
      if (mode.value === 'profile') return 'profile'
      if (!team.value && mode.value === 'manage') return 'choose'
      return mode.value
    })

    const showModeTabs = computed(() => (
      !!team.value && ['manage', 'list'].includes(displayMode.value)
    ))

    const pageCmd = computed(() => {
      const map = {
        choose: 'team join',
        create: 'team new',
        join: 'team join',
        manage: 'team manage',
        list: 'team list',
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
        list: '队伍公开列表',
        profile: '队伍详情',
      }
      return map[displayMode.value] || '战队中心'
    })

    const pageDesc = computed(() => {
      const map = {
        choose: '正式赛事以战队为单位报名参赛。你可以创建新队伍，或使用邀请码加入队友的战队。',
        create: '填写队名与标签，创建后自动获取邀请码',
        join: '向队长索取邀请码，输入后即可加入战队',
        manage: '编辑队名、组织与标签 · 查看得分与解题记录',
        list: '查看本赛事所有已公开战队',
        profile: '查看参赛队伍的公开信息',
      }
      return map[displayMode.value] || 'TEAM · SQUAD'
    })

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
          editTag.value = parsed.tag || ''
          editSchool.value = parsed.school || '无组织'
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

    async function joinCompetition() {
      if (!gameId.value) return
      try {
        await axios.post(`/api/competitions/${gameId.value}/join`, {})
      } catch (e) {
        const msg = e.response?.data?.msg || ''
        if (e.response?.status === 200 || /已经参加|已报名/.test(msg)) return
        throw e
      }
    }

    async function loadAllTeams() {
      listLoading.value = true
      try {
        const { data } = await axios.get('/api/teams/', { params: { game_id: gameId.value } })
        allTeams.value = data?.teams || data || []
      } catch {
        allTeams.value = []
      } finally {
        listLoading.value = false
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
          tag: createTag.value,
          game_id: parseInt(gameId.value, 10),
        })
        createdInvite.value = unwrapTeamInvite(data)
        message.success('队伍创建成功')
        await joinCompetition()
        inGame.value = true
        message.success('已为本赛事报名')
        await loadTeam()
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
        await joinCompetition()
        inGame.value = true
        message.success('已为本赛事报名')
        await loadTeam()
      } catch (e) {
        message.error(apiErrorMessage(e, '加入失败'))
      } finally {
        saving.value = false
      }
    }

    async function registerForGame() {
      if (saving.value) return
      saving.value = true
      try {
        await joinCompetition()
        inGame.value = true
        message.success('已报名本赛事')
        await loadTeam()
      } catch (e) {
        message.error(e.response?.data?.msg || '报名失败')
      } finally {
        saving.value = false
      }
    }

    async function saveTeam() {
      if (!team.value) return
      saving.value = true
      try {
        await teamsApi.updateTeam(team.value.id, {
          name: editName.value,
          tag: editTag.value,
          school: editSchool.value,
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

    async function loadScoreChart() {
      if (!team.value?.id) return
      try {
        const { data } = await axios.get(`/api/teams/${team.value.id}/score-timeline`, {
          params: { game_id: gameId.value },
        })
        const timeline = data?.timeline || []
        await nextTick()
        if (!scoreChartRef.value) return
        if (!scoreChart) scoreChart = echarts.init(scoreChartRef.value)
        scoreChart.setOption({
          tooltip: { trigger: 'axis' },
          grid: { left: 40, right: 16, top: 24, bottom: 32 },
          xAxis: { type: 'time' },
          yAxis: { type: 'value', name: 'pts', scale: true },
          series: [{
            type: 'line',
            step: 'end',
            smooth: false,
            showSymbol: false,
            data: timeline.filter(p => p.time).map(p => [p.time, p.points]),
            itemStyle: { color: '#2DB58A' },
            lineStyle: { width: 2 },
          }],
        })
      } catch { /* ignore */ }
    }

    function goChallenge(challengeId) {
      router.push(`/games/${gameId.value}/challenges?challenge=${challengeId}`)
    }

    function copyInvite() {
      const code = createdInvite.value || team.value?.invite_code
      if (code) navigator.clipboard?.writeText(code)
      message.success('已复制邀请码')
    }

    function viewTeam(t) {
      router.push(`/games/${gameId.value}/teams/${t.id}`)
    }

    async function loadViewedTeam(teamId) {
      if (!teamId) {
        viewedTeam.value = null
        return
      }
      const tid = parseInt(teamId, 10)
      if (team.value?.id === tid) {
        viewedTeam.value = null
        mode.value = 'manage'
        return
      }
      try {
        const { data } = await axios.get(`/api/teams/${tid}`, {
          params: { game_id: gameId.value },
        })
        viewedTeam.value = data?.team || data
        mode.value = 'profile'
      } catch {
        message.error('无法加载队伍信息')
        viewedTeam.value = null
        router.replace(`/games/${gameId.value}/teams`)
      }
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
      if (t) {
        loadSolves()
        loadScoreChart()
      }
    })

    onUnmounted(() => { scoreChart?.dispose() })

    onMounted(async () => {
      await loadTeam()
      await loadAllTeams()
      try {
        const { data } = await axios.get(`/api/competitions/${gameId.value}`)
        const g = data?.data || data
        if (g?.end_time && Date.now() > new Date(g.end_time).getTime()) gameEnded.value = true
      } catch { /* ignore */ }
    })

    return {
      gameId, team, viewedTeam, allTeams, solves, mode, displayMode, saving, listLoading, gameEnded, inGame,
      createName, createTag, joinCode, createdInvite, editName, editTag, editSchool,
      schoolOptions, scoreChartRef, hexId, showModeTabs, pageCmd, pageTitle, pageDesc,
      formatTime, createTeam, joinTeam, saveTeam, leaveTeam, copyInvite, viewTeam, goChallenge, registerForGame,
      openChoose, openManage, memberCode,
    }
  },
}
</script>

<style scoped>
.game-teams-page {
  margin: 0;
  min-height: calc(100vh - var(--nav-height, 56px));
}

.teams-main {
  flex: 1;
  min-width: 0;
  width: 100%;
  max-width: none;
  margin: 0;
  overflow: auto;
}

.mode-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 16px;
}

.mode-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
  color: var(--muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.mode-tab:hover,
.mode-tab.active {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}

.mode-tab.join-cta {
  margin-top: 12px;
}

.team-summary {
  margin-bottom: 16px;
}

.matrix-panel {
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
}

.team-card {
  margin-bottom: 12px;
}

.team-card-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.team-card-head h3 {
  margin: 0;
  font-size: 0.95rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.member-row {
  display: grid;
  grid-template-columns: 28px auto 1fr auto;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
}

.member-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-hex {
  font-family: monospace;
  font-size: 11px;
  color: var(--muted);
}

.empty-card {
  text-align: left;
  color: var(--muted);
  margin-bottom: 12px;
}

.empty-prompt {
  margin: 0 0 8px;
  font-size: 11px;
  color: var(--color-accent, #D97706);
}

.empty-title {
  margin: 0 0 6px;
  font-weight: 600;
  color: var(--text);
}

.empty-hint {
  margin: 0 0 12px;
  font-size: var(--text-xs);
  line-height: 1.5;
}

.link-code {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-accent, #D97706);
}

.row-arrow {
  font-size: var(--text-xs);
  color: var(--muted);
}

.choose-panel,
.list-panel,
.manage-panel {
  max-width: none;
  width: 100%;
}

.choose-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(var(--card-grid-min, 320px), 1fr));
  gap: 12px;
}

.choose-card {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  align-items: start;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.choose-card:hover {
  border-color: rgba(var(--primary-rgb), 0.45);
  background: rgba(var(--primary-rgb), 0.06);
}

.choose-card:hover .link-code {
  color: var(--primary);
}

.choose-body h3 {
  margin: 0 0 6px;
  font-size: 0.95rem;
  color: var(--text);
}

.choose-body p {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--muted);
  line-height: 1.5;
}

.form-panel {
  max-width: 560px;
}

.form-panel .matrix-page-head,
.manage-panel > .matrix-page-head {
  margin-bottom: 16px;
  padding-bottom: 12px;
}

.manage-form {
  margin-bottom: 12px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.invite-box {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
  padding: 12px;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  font-size: 14px;
}

.invite-box code {
  color: var(--primary);
}

.section-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}

.section-head h3 {
  margin: 0;
  font-size: 0.95rem;
}

.score-section,
.solve-section,
.extra-section {
  margin-top: 12px;
}

.score-chart {
  height: 240px;
  width: 100%;
}

.muted {
  color: var(--muted);
  font-size: 14px;
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
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
  align-items: start;
}

.solve-link {
  color: var(--primary);
  text-decoration: none;
}

.solve-link:hover {
  text-decoration: underline;
}

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
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--card-bg);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.public-team:hover {
  border-color: rgba(var(--primary-rgb), 0.45);
  background: rgba(var(--primary-rgb), 0.06);
}

.public-team:hover .link-code {
  color: var(--primary);
}

.team-name {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-meta {
  font-size: var(--text-xs);
  color: var(--muted);
  white-space: nowrap;
}

.empty-list,
.empty-main {
  text-align: left;
  padding: 48px 0;
  color: var(--muted);
  max-width: 480px;
}

.empty-main .join-cta {
  max-width: 280px;
  margin-top: 12px;
}

@media (max-width: 900px) {
  .teams-main {
    padding: 16px;
  }
  .choose-grid {
    grid-template-columns: 1fr;
  }
}
.field-hint { margin: 6px 0 0; font-size: 12px; color: var(--text-muted, var(--muted)); }
</style>
