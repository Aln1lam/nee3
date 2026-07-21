<template>
  <div class="page-container legacy-page">
    <p class="legacy-page-notice">Legacy 组件 · 请使用 /games (GamesHub)</p>

    <!-- 队伍管理面板 -->
    <div v-if="!selected" class="team-panel">
      <div class="team-title">
        <span class="bracket">[</span>
        <span>战队管理</span>
        <span class="bracket">]</span>
      </div>

      <n-grid x-gap="20" cols="1 m:2" responsive="screen">
        <!-- 创建队伍 -->
        <n-grid-item>
          <div class="team-card">
            <h4>📝 创建战队</h4>
            <n-input-group>
              <n-input v-model:value="teamName" placeholder="输入战队名称..." />
              <n-button type="error" @click="createTeam" :loading="creatingTeam">创建</n-button>
            </n-input-group>
            <div v-if="createSuccess" class="success-msg">✓ 战队创建成功！邀请码：{{ createSuccess }}</div>
          </div>
        </n-grid-item>

        <!-- 加入队伍 -->
        <n-grid-item>
          <div class="team-card">
            <h4>🔗 加入战队</h4>
            <n-input-group>
              <n-input v-model:value="inviteCode" placeholder="输入邀请码..." />
              <n-button type="default" @click="joinTeam" :loading="joiningTeam">加入</n-button>
            </n-input-group>
            <div v-if="joinSuccess" class="success-msg">✓ 加入成功！</div>
          </div>
        </n-grid-item>

        <!-- 当前队伍信息 区块头：包含所有队伍按钮 -->
        <n-grid-item :span="2">
          <div class="team-card team-info">
            <div class="team-info-header">
              <h4>👥 当前战队</h4>
              <n-button size="small" tertiary @click="toggleAllTeams" style="margin-left:12px">所有队伍</n-button>
            </div>

            <div v-if="showAllTeams" class="all-teams-list">
              <div v-if="loadingAllTeams">加载中...</div>
              <div v-else>
                <div v-for="t in allTeams" :key="t.id" class="team-row" @click="selectTeam(t.id)">
                  <span class="team-name">{{ t.name }}</span>
                  <span class="team-id">#{{ t.id }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="currentTeam" class="team-details">
              <p><strong>{{ currentTeam.name }}</strong></p>
              <p class="team-meta">ID: {{ currentTeam.id }} | 成员: {{ currentTeam.members.length }}</p>
              <div class="members-list">
                <span v-for="m in currentTeam.members" :key="m.id" class="member-badge">{{ m.nickname || 'Unknown' }}</span>
              </div>
            </div>
            <div v-else class="empty-team">
              <p>未加入任何战队。请创建或加入一个战队以激活参赛功能。</p>
            </div>
          </div>
        </n-grid-item>
      </n-grid>
    </div>

    <n-divider v-if="!selected" />

    <div class="minimal-title-bar">
      <div class="bracket-title">
        <span class="bracket">[</span>
        <span class="title-text">{{ selected ? selected.title : '赛事中心' }}</span>
        <span class="bracket">]</span>
      </div>
      <div class="actions">
        <n-button v-if="selected" secondary type="error" @click="viewScoreboard">
          <template #icon>🏆</template> 积分榜
        </n-button>
        <n-button secondary circle @click="loadGames">
          <template #icon>↻</template>
        </n-button>
      </div>
    </div>

    <div v-if="!selected" class="games-grid">
      <n-grid x-gap="24" y-gap="24" cols="1 s:2 m:3 l:3" responsive="screen">
        <n-grid-item v-for="g in games" :key="g.id">
          <n-card hoverable class="minimal-card" @click="select(g)">
            <template #header>
              <div class="card-header">
                <span class="id-tag">NO.{{ String(g.id).padStart(3, '0') }}</span>
                <n-tag :bordered="false" type="error" size="small" v-if="g.joined">已参赛</n-tag>
                <n-tag :bordered="false" size="small" v-else>未加入</n-tag>
                <n-tag :bordered="false" :type="g.is_public ? 'success' : 'warning'" size="small">
                  {{ g.is_public ? '🌐 公开' : '🔒 邀请' }}
                </n-tag>
                <n-tag :bordered="false" type="default" size="small" v-if="g.archived_at">
                  📦 已归档
                </n-tag>
              </div>
            </template>

            <div class="game-title">{{ g.title }}</div>
            <div class="game-meta">
              <span>{{ g.status === 'ongoing' ? '进行中' : g.status === 'not_started' ? '未开始' : '已结束' }}</span>
              <span class="arrow">→</span>
            </div>

            <template #action>
               <n-button 
                 block 
                 :type="g.joined ? 'default' : 'error'" 
                 secondary
                 @click.stop="joinGame(g)"
                 :disabled="(g.joined && !isGameActive(g)) || g.archived_at"
                 :loading="g._joining"
               >
                 <template v-if="g.archived_at">📦 已归档（仅查看）</template>
                 <template v-else-if="g.joined">{{ isGameActive(g) ? '进入系统' : '未开始（已报名）' }}</template>
                 <template v-else>{{ g.is_public ? '立即报名' : '凭邀请码报名' }}</template>
               </n-button>
            </template>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>

    <div v-else class="challenges-view">
      <n-button text class="back-btn" @click="selected=null">
        &lt; 返回列表
      </n-button>

      <n-grid x-gap="20" y-gap="20" cols="1 s:2 m:3 l:4" responsive="screen">
        <n-grid-item v-for="c in challenges" :key="c.id">
          <ChallengeCard
            :challenge="c"
            :game="selected"
            :joined="selected && selected.joined"
            :team-id="currentTeam?.id"
          />
        </n-grid-item>
      </n-grid>
    </div>

  </div>
</template>

<script>
import { ref, inject, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NGrid, NGridItem, NCard, NButton, NTag, NDivider, NInput, NInputGroup } from 'naive-ui'
import ChallengeCard from './ChallengeCard.vue'
import ChallengeModal from './Challenge.vue'

export default {
  components: { NGrid, NGridItem, NCard, NButton, NTag, NDivider, NInput, NInputGroup, ChallengeCard, ChallengeModal },
  emits: ['open-scoreboard'],
  setup(props, { emit }) {
    const axios = inject('axios')
    const router = useRouter()
    const route = useRoute()

    const games = ref([])
    const selected = ref(null)
    const challenges = ref([])

    // 队伍管理相关状态
    const teamName = ref('')
    const inviteCode = ref('')
    const currentTeam = ref(null)
    const creatingTeam = ref(false)
    const joiningTeam = ref(false)
    const createSuccess = ref(null)
    const joinSuccess = ref(false)

    const allTeams = ref([])
    const showAllTeams = ref(false)
    const loadingAllTeams = ref(false)

    // 加载当前队伍信息
    async function loadTeam() {
      try {
        const { data } = await axios.get('/api/teams/me')
        if (data && (data.id || data.name)) {
          currentTeam.value = data
        } else {
          currentTeam.value = null
        }
      } catch (e) {
        console.error('Failed to load team:', e)
        currentTeam.value = null
      }
    }

    // 加载所有队伍
    async function loadAllTeams() {
      loadingAllTeams.value = true
      try {
        const { data } = await axios.get('/api/teams/')
        allTeams.value = data.teams || []
      } catch (e) {
        console.error('Failed to load all teams:', e)
        allTeams.value = []
      } finally {
        loadingAllTeams.value = false
      }
    }

    function toggleAllTeams() {
      showAllTeams.value = !showAllTeams.value
      if (showAllTeams.value) loadAllTeams()
    }

    async function selectTeam(teamId) {
      try {
        const { data } = await axios.get(`/api/teams/${teamId}`)
        if (data && (data.id || data.name)) {
          currentTeam.value = data
          showAllTeams.value = false
        }
      } catch (e) {
        alert('获取战队详情失败')
      }
    }

    // 创建队伍
    async function createTeam() {
      if (!teamName.value) {
        alert('请输入队伍名称')
        return
      }
      creatingTeam.value = true
      try {
        const { data } = await axios.post('/api/teams/', { name: teamName.value })
        createSuccess.value = data.invite_code
        teamName.value = ''
        await loadTeam()
        setTimeout(() => { createSuccess.value = null }, 3000)
      } catch (e) {
        alert('创建失败: ' + (e.response?.data?.msg || e.message))
      } finally {
        creatingTeam.value = false
      }
    }

    // 加入队伍
    async function joinTeam() {
      if (!inviteCode.value) {
        alert('请输入邀请码')
        return
      }
      joiningTeam.value = true
      try {
        await axios.post('/api/teams/join', { invite_code: inviteCode.value })
        joinSuccess.value = true
        inviteCode.value = ''
        await loadTeam()
        setTimeout(() => { joinSuccess.value = false }, 3000)
      } catch (e) {
        alert('加入失败: ' + (e.response?.data?.msg || e.message))
      } finally {
        joiningTeam.value = false
      }
    }

    async function loadGames() {
      try {
        try {
          const t = localStorage.getItem('neepu_token')
          if (t && !axios.defaults.headers.common['Authorization']) {
            axios.defaults.headers.common['Authorization'] = 'Bearer ' + t
          }
        } catch (e) {}
        const { data } = await axios.get('/api/competitions/?per_page=100')
        const payload = data?.data || data
        games.value = payload?.items || payload || []
        console.log('Loaded games:', games.value)
        await Promise.all(games.value.map(async (g) => {
          try {
            const t = localStorage.getItem('neepu_token')
            if (!t) { g.joined = false; return }
            const r = await axios.get(`/api/competitions/${g.id}/joined`)
            g.joined = !!(r.data?.joined ?? r.data?.data?.joined)
          } catch(e) { console.error('Games: joined check failed for', g.id, e); g.joined = false }
        }))
        console.log('Games after joined check:', games.value)
      } catch(e) { console.error(e) }
    }

    function isGameActive(g) {
      if (!g || !g.start_time || !g.end_time) return false
      const now = new Date()
      return new Date(g.start_time) <= now && now <= new Date(g.end_time)
    }

    function select(g) {
      if (!g) return
      if (g.joined && !isGameActive(g)) {
        alert('比赛尚未开始，已报名但暂时无法进入')
        return
      }
      router.push(`/games/${g.id}`)
      if (g.joined) { selected.value = g; loadChallenges(g.id) }
      else { joinGame(g) }
    }

    async function loadChallenges(gid) {
      try {
        const { data } = await axios.get(`/api/challenges/games/${gid}/challenges`)
        const payload = data?.data || data
        challenges.value = Array.isArray(payload) ? payload : (payload?.items || [])
      } catch (e) { console.error('loadChallenges failed', e); challenges.value = [] }
    }

    async function joinGame(g) {
      const token = localStorage.getItem('neepu_token')
      if (!token) return alert('请先登录 / ACCESS DENIED')
      if (!axios.defaults.headers.common['Authorization']) axios.defaults.headers.common['Authorization'] = 'Bearer ' + token

      g._joining = true
      try {
        await loadTeam()
        
        // 🔴 检查是否是公开比赛
        if (!g.is_public) {
          // 非公开比赛，需要输入邀请码
          const inviteCode = prompt(`该比赛需要邀请码才能参加。\n请输入邀请码：`)
          if (!inviteCode || !inviteCode.trim()) {
            return alert('未输入邀请码，无法参赛')
          }
          
          // 带邀请码参赛
          await axios.post(`/api/competitions/${g.id}/join`, { invite_code: inviteCode.trim() })
        } else {
          // 公开比赛，直接参赛
          await axios.post(`/api/competitions/${g.id}/join`)
        }
        
        g.joined = true
        router.push(`/games/${g.id}`)
        selected.value = g
        await loadChallenges(g.id)
      } catch (e) {
        const errMsg = e.response?.data?.msg || e.message
        if (e.response?.status === 403) alert('加入失败：' + errMsg + '\n\n请先创建或加入战队，然后再加入竞赛。')
        else if (e.response?.status === 400) alert('邀请码错误：' + errMsg)
        else alert('加入失败: ' + errMsg)
      } finally { g._joining = false }
    }

    function viewScoreboard() { if (selected.value) emit('open-scoreboard', selected.value.id) }

    function onUserRefreshed() { loadGames().catch(()=>{}); loadTeam().catch(()=>{}) }

    onMounted(() => { window.addEventListener('neepu_user_refreshed', onUserRefreshed) })
    onUnmounted(() => window.removeEventListener('neepu_user_refreshed', onUserRefreshed))

    async function waitAndLoad() {
      const hasToken = () => !!localStorage.getItem('neepu_token')
      if (hasToken()) await loadGames()
      else {
        await new Promise((resolve) => {
          let settled = false
          function done() { if (!settled) { settled = true; cleanup(); resolve() } }
          function onAuthReady() { done() }
          function onUserRefreshed() { done() }
          function cleanup() { window.removeEventListener('neepu_auth_ready', onAuthReady); window.removeEventListener('neepu_user_refreshed', onUserRefreshed) }
          const t = setTimeout(() => { cleanup(); resolve() }, 2000)
          window.addEventListener('neepu_auth_ready', onAuthReady)
          window.addEventListener('neepu_user_refreshed', onUserRefreshed)
        })
        await loadGames()
      }
      const id = route.params.id
      if (id) {
        const found = games.value.find(x => String(x.id) === String(id))
        if (found) select(found)
      }
    }

    waitAndLoad()
    loadTeam()

    watch(() => route.params.id, (id) => {
      if (!id) { selected.value = null; return }
      const found = games.value.find(x => String(x.id) === String(id))
      if (found) select(found)
    })

    return { games, selected, challenges, loadGames, select, viewScoreboard, joinGame,
             teamName, inviteCode, currentTeam, creatingTeam, joiningTeam, createSuccess, joinSuccess,
             createTeam, joinTeam, allTeams, showAllTeams, toggleAllTeams, loadingAllTeams, selectTeam }
  }
}
</script>

<style scoped>
.page-container { padding: var(--fib-21); font-family: var(--font-ui); }

/* 队伍管理面板 */
.team-panel { margin-bottom: 40px; }
.team-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 20px;
}
.team-title .bracket { color: #ccc; margin: 0 10px; }

.team-card {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: var(--fib-21);
  background: #fafafa;
  transition: all 0.3s ease;
}
.team-card:hover { border-color: #ff5252; background: var(--gradient-card-bg, var(--card-bg)); }
.team-card h4 { margin-top: 0; margin-bottom: 15px; color: #333; }

.success-msg { margin-top: 10px; padding: 8px 12px; background: #f0f9ff; border-left: 3px solid #52c41a; color: #52c41a; font-size: 0.9rem; border-radius: 2px; }

.team-info { margin-top: 0; }
.team-info-header { display:flex; align-items:center; }
.team-details p { margin: 8px 0; }
.team-details p:first-child { font-size: 1.2rem; color: #ff5252; font-weight: bold; }
.team-meta { color: #999; font-size: 0.9rem; }
.members-list { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px; }
.member-badge { background: #ff5252; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; }
.all-teams-list { max-height: 260px; overflow:auto; padding-top:10px; }
.team-row { display:flex; justify-content:space-between; padding:8px 12px; border-bottom:1px solid #f0f0f0; cursor:pointer }
.team-row:hover { background:#f6f6f6 }
.team-name { font-weight:600 }
.team-id { color:#999 }
.empty-team { color:#777; padding:12px 0 }

/* 极简标题栏 */
.minimal-title-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
.bracket-title { font-size: 1.5rem; font-weight: 700; color: #333; }
.bracket { color: #ccc; margin: 0 10px; }

/* 卡片风格 */
.minimal-card { border: 1px solid #e0e0e0; border-radius: 2px; transition: all 0.3s ease; background: var(--gradient-card-bg, var(--card-bg)); }
.minimal-card:hover { border-color: #ff5252; box-shadow: 0 4px 12px rgba(255, 82, 82, 0.1); transform: translateY(-2px); }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.id-tag { color: #999; font-size: 0.8rem; letter-spacing: 1px; }

.game-title { font-size: 1.2rem; font-weight: bold; margin: 15px 0; color: #333; }
.game-meta { display: flex; justify-content: space-between; color: #666; font-size: 0.9rem; margin-bottom: 10px; }
.arrow { color: #ff5252; font-weight: bold; }

.back-btn { margin-bottom: 20px; color: #666; }
.back-btn:hover { color: #ff5252; }

/* 题目卡片 */
.challenge-card { text-align: center; position: relative; overflow: hidden; }
.score-badge { position: absolute; top: 0; right: 0; background: #f5f5f5; color: #666; padding: 4px 8px; font-size: 0.8rem; border-bottom-left-radius: 4px; }
.chal-content h4 { margin: 20px 0 5px; font-size: 1.1rem; }
.category { color: #ff5252; font-size: 0.8rem; opacity: 0.8; }
</style>