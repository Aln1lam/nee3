<template>
  <!--
    LEGACY / 未挂现网路由。
    现网管理：/admin/* → AdminPanel + AdminContent + CtfManagement。
    本文件仅保留兼容；API 已对齐到 competitions/ctf/admin 主路径。
  -->
  <div>
    <h2>管理面板</h2>
    <div v-if="!isAdmin" class="admin-alert">
      <div class="admin-alert-title">缺少管理员权限</div>
      <div class="admin-alert-desc">当前账户没有管理员权限。若在后台提升了权限，请点击下方刷新并重试。</div>
      <div class="admin-alert-actions">
        <n-button @click="(async ()=>{ await (typeof window !== 'undefined' && window.$$reloadUser ? window.$$reloadUser() : null); location.reload(); })" type="primary">刷新并重试</n-button>
      </div>
    </div>
    <div v-if="errorMsg" class="admin-error">{{ errorMsg }}</div>
    <div v-if="loading" class="admin-loading">加载中...</div>
    <n-tabs type="line" v-model:value="currentTab" v-if="isAdmin">
      <n-tab-pane name="submissions" tab="提交记录">
        <n-data-table :columns="subCols" :data="subs" :scroll-x="800" />
      </n-tab-pane>

      <n-tab-pane name="challenges" tab="题目管理">
        <n-space vertical>
          <div class="admin-panel admin-create-chal">
            <n-input v-model:value="newChallenge.title" placeholder="题目标题" />     
            <n-input v-model:value="newChallenge.flag" placeholder="flag{...}" />        
            <n-input v-model:value="newChallenge.score" type="number" :style="{ width: 'var(--admin-input-width-small, 120px)' }" placeholder="分值" />
            <n-select v-model:value="newChallenge.game_id" :options="gameOptions" placeholder="选择比赛" :style="{ width: 'var(--admin-select-width, 160px)' }" />
            <n-button @click="createChallenge" type="primary">创建题目</n-button>    
          </div>

          <div v-for="c in challenges" :key="c.id" class="admin-panel admin-chal-row">   
            <div class="admin-row">
              <div>
                <div><strong>{{ c.title }}</strong> <small>(ID: {{ c.id }})</small></div>
                <div class="admin-row-meta">Game: {{ c.game_id }}</div>       
              </div>
              <n-input v-model:value="c.score" :style="{ width: 'var(--admin-input-width-small, 120px)' }" type="number" />      
              <n-input v-model:value="c.flag" :style="{ width: 'var(--admin-input-width-medium, 220px)' }" />
              <n-button @click="saveChallenge(c)" size="small" secondary>保存</n-button>
            </div>
            <div>
              <n-button @click="deleteChallenge(c)" size="small" type="error" ghost>删除</n-button>
            </div>
          </div>
        </n-space>
      </n-tab-pane>

      <n-tab-pane name="games" tab="比赛管理">
        <n-space vertical>
          <div v-for="g in games" :key="g.id" class="admin-panel admin-game-row">
            <div class="admin-row">
              <div style="flex: 1">
                <div><strong>{{ g.title }}</strong> (ID: {{ g.id }})</div>
                <div class="admin-row-meta">状态: {{ g.status }} | 公开: {{ g.is_public ? '是' : '否' }}</div>
              </div>
              <n-date-picker v-model:value="g.start_time" type="datetime" placeholder="开始时间" />
              <n-date-picker v-model:value="g.end_time" type="datetime" placeholder="结束时间" />
              <n-button @click="saveGame(g)" size="small" secondary>保存</n-button>
              <n-button @click="() => toggleGameDivisions(g.id)" size="small" secondary>{{ expandedGameId === g.id ? '隐藏' : '显示' }}分组</n-button>
            </div>

            <!-- Game Divisions Section -->
            <div v-if="expandedGameId === g.id" class="game-divisions-section">
              <div class="divisions-header">
                <h4>📋 分组管理</h4>
                <n-button @click="() => openCreateDivisionModal(g.id)" size="small" type="primary">+ 创建分组</n-button>
              </div>
              
              <div v-if="loadingDivisions" class="admin-loading">加载分组中...</div>
              <div v-else-if="gameDivisions[g.id] && gameDivisions[g.id].length === 0" class="admin-empty">暂无分组</div>
              <div v-else>
                <div v-for="d in gameDivisions[g.id]" :key="d.id" class="division-item">
                  <div class="division-info-inline">
                    <div>
                      <strong>{{ d.name }}</strong> <small>(ID: {{ d.id }})</small>
                      <div class="division-meta">
                        邀请码: <span class="code">{{ d.invite_code || '未设置' }}</span>
                        <span v-if="d.school_scope" class="division-meta">学校范围: {{ d.school_scope }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="division-actions">
                    <n-button @click="() => viewDivisionMembers(g.id, d)" size="small" secondary>查看成员</n-button>
                    <n-button @click="() => copyToClipboard(d.invite_code)" size="small" secondary>复制邀请码</n-button>
                    <n-button @click="() => deleteDivision(g.id, d.id)" size="small" type="error" ghost>删除</n-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </n-space>
      </n-tab-pane>

      <n-tab-pane name="users" tab="用户管理">
        <n-space vertical>
          <div class="admin-search-row">
            <n-input v-model:value="usersQuery" placeholder="搜索邮箱或昵称" @input="onUsersSearch" :style="{ width: 'var(--admin-search-width, 320px)' }" />
            <n-button type="primary" @click="() => openEditUser(null)">新建用户</n-button>
          </div>
          <n-data-table :columns="userCols" :data="users" :loading="usersLoading" :scroll-x="800" />
        </n-space>
      </n-tab-pane>

      <n-tab-pane name="teams" tab="队伍管理">
        <n-space vertical>
          <div class="admin-search-row">
            <n-input v-model:value="teamsQuery" placeholder="搜索队伍" @input="onTeamsSearch" :style="{ width: 'var(--admin-search-width, 320px)' }" />
            <n-button type="primary" @click="() => openEditTeam(null)">新建队伍</n-button>
          </div>
          <n-data-table :columns="teamCols" :data="teams" :loading="teamsLoading" :scroll-x="800" />
        </n-space>
      </n-tab-pane>
    </n-tabs>

    <!-- User Edit Modal -->
    <n-modal v-model:show="showUserModal" preset="dialog" :closable="true">
      <template #header>编辑用户</template>
      <n-card>
        <n-form>
          <n-form-item label="邮箱">
            <n-input v-model:value="editUser.email" :disabled="true" />
          </n-form-item>
          <n-form-item label="昵称">
            <n-input v-model:value="editUser.nickname" />
          </n-form-item>
          <n-form-item label="管理员">
            <n-switch v-model:value="editUser.is_admin" />
          </n-form-item>
          <n-form-item label="队伍">
            <n-select v-model:value="editUser.team_id" :options="teamOptionsSelect" placeholder="选择队伍（可空）" />
          </n-form-item>
          <div class="form-actions">
            <n-button @click="() => { showUserModal = false }">取消</n-button>
            <n-button type="primary" @click="saveUser">保存</n-button>
          </div>
        </n-form>
      </n-card>
    </n-modal>

    <!-- Team Edit Modal -->
    <n-modal v-model:show="showTeamModal" preset="dialog" :closable="true">
      <template #header>编辑队伍</template>
      <n-card>
        <n-form>
          <n-form-item label="名称">
            <n-input v-model:value="editTeam.name" />
          </n-form-item>
          <n-form-item label="成员">
            <n-select v-model:value="editTeam.members" :options="userOptionsSelect" multiple placeholder="选择成员（可空）" />
          </n-form-item>
          <div class="form-actions">
            <n-button @click="() => { showTeamModal = false }">取消</n-button>
            <n-button type="primary" @click="saveTeam">保存</n-button>
          </div>
        </n-form>
      </n-card>
    </n-modal>

    <!-- Create/Edit Division Modal -->
    <n-modal v-model:show="showDivisionModal" preset="dialog" :closable="true">
      <template #header>{{ editingDivisionId ? '编辑' : '创建' }}分组</template>
      <n-card>
        <n-form>
          <n-form-item label="分组名称">
            <n-input v-model:value="newDivision.name" placeholder="例如: 高级组、初级组" />
          </n-form-item>
          <n-form-item label="邀请码">
            <n-input v-model:value="newDivision.invite_code" placeholder="邀请码（选填，系统自动生成）" />
          </n-form-item>
          <n-form-item label="学校范围">
            <n-input v-model:value="newDivision.school_scope" placeholder="留空表示全局" />
          </n-form-item>
          <n-form-item label="描述">
            <n-input v-model:value="newDivision.description" placeholder="分组描述（选填）" type="textarea" />
          </n-form-item>
          <div class="form-actions">
            <n-button @click="() => { showDivisionModal = false }">取消</n-button>
            <n-button type="primary" @click="saveDivision" :loading="savingDivision">保存</n-button>
          </div>
        </n-form>
      </n-card>
    </n-modal>

    <!-- Division Members Modal -->
    <n-modal v-model:show="showDivisionMembersModal" preset="dialog" :closable="true" style="width: 800px">
      <template #header>分组成员 - {{ selectedDivision?.name }}</template>
      <n-card>
        <div v-if="divisionMembersLoading" class="admin-loading">加载成员中...</div>
        <div v-else>
          <div class="division-info">
            <p><strong>邀请码:</strong> <span class="code">{{ selectedDivision?.invite_code }}</span></p>
            <p><strong>成员数:</strong> {{ divisionMembers.length }}</p>
          </div>
          <n-data-table 
            v-if="divisionMembers.length > 0"
            :columns="divisionMemberCols" 
            :data="divisionMembers" 
            :scroll-x="600"
          />
          <div v-else class="admin-empty">该分组还没有成员</div>
        </div>
      </n-card>
    </n-modal>
  </div>
</template>

<script>
import { ref, onMounted, inject, watch, h } from 'vue'
import { NButton, NDataTable, NTabs, NTabPane, NInput, NSpace, NDatePicker, NSelect, NModal, NCard, NForm, NFormItem, NSwitch } from 'naive-ui'

export default {
  components: { NButton, NDataTable, NTabs, NTabPane, NInput, NSpace, NDatePicker, NSelect, NModal, NCard, NForm, NFormItem, NSwitch },
  setup() {
    const axios = inject('axios')
    const subs = ref([])
    const challenges = ref([])
    const currentTab = ref('submissions')
    const newChallenge = ref({ title: '', flag: '', score: 100, game_id: null })
    const games = ref([])
    const gameOptions = ref([])
    const user = ref(null)
    const isAdmin = ref(false)
    const loading = ref(false)
    const errorMsg = ref('')

    const subCols = [
      { title: 'ID', key: 'id' },
      { title: '队伍', key: 'team_name' },
      { title: '提交者', key: 'nickname' },
      { title: '题目', key: 'challenge_id' },
      { title: 'Flag', key: 'flag' },
      { title: '是否正确', key: 'correct' },
      { title: '时间', key: 'created_at' },
    ]

      // users/teams state
    const users = ref([])
      const usersLoading = ref(false)
      const usersPage = ref(1)
      const usersQuery = ref('')
      const usersTotal = ref(0)
      const showUserModal = ref(false)
      const editUser = ref({})

  const teams = ref([])
  const teamsLoading = ref(false)
  const teamsQuery = ref('')
      const showTeamModal = ref(false)
      const editTeam = ref({})
  const teamOptionsSelect = ref([])
  const userOptionsSelect = ref([])

      // Division management state
      const expandedGameId = ref(null)
      const gameDivisions = ref({})  // { gameId: [divisions] }
      const loadingDivisions = ref(false)
      const showDivisionModal = ref(false)
      const editingDivisionId = ref(null)
      const editingGameId = ref(null)
      const newDivision = ref({ name: '', invite_code: '', school_scope: '', description: '' })
      const savingDivision = ref(false)
      const showDivisionMembersModal = ref(false)
      const selectedDivision = ref(null)
      const divisionMembers = ref([])
      const divisionMembersLoading = ref(false)
      const divisionMemberCols = [
        { title: '用户ID', key: 'user_id' },
        { title: '昵称', key: 'nickname' },
        { title: '邮箱', key: 'email' },
        { title: '使用的邀请码', key: 'invite_code_used' },
        { title: '验证时间', key: 'verified_at' }
      ]

      // placeholder columns; render functions will be defined after methods so they can reference handlers
      let userCols = []
      let teamCols = []

    async function load() {
      errorMsg.value = ''
      if (!isAdmin.value) return
      loading.value = true
      // LEGACY：本组件未挂入现网 router（管理走 AdminPanel + CtfManagement）。
      // 对齐真实 API，避免打不存在的 /api/admin/submissions。
      try {
        const r1 = await axios.get('/api/admin/first-solves', { params: { page: 1, per_page: 50 } })
        const items = r1.data?.data?.items || r1.data?.items || []
        subs.value = items
      } catch (e) {
        console.error(e)
        if (e.response && (e.response.status === 401 || e.response.status === 403)) errorMsg.value = '无权限访问提交/首解记录'
        subs.value = []
      }
      try {
        // 无全局 /api/admin/challenges 列表；需按赛拉取。此处仅清空，避免 404。
        challenges.value = []
      } catch (e) {
        console.error(e)
      }
      try {
        const r3 = await axios.get('/api/competitions/', { params: { include_ephemeral: 1 } })
        const items = r3.data?.data?.items || r3.data?.data || r3.data?.items || []
        games.value = (Array.isArray(items) ? items : []).map(g => ({
          ...g,
          start_time: g.start_time ? new Date(g.start_time) : null,
          end_time: g.end_time ? new Date(g.end_time) : null,
        }))
        gameOptions.value = games.value.map(g => ({ label: g.title, value: g.id }))
      } catch (e) {
        console.error(e)
        if (e.response && (e.response.status === 401 || e.response.status === 403)) errorMsg.value = '无权限访问比赛管理'
      }
      loading.value = false
    }

    // reload data when tab changes
    watch(currentTab, () => {
      if (isAdmin.value) load()
    })

    // --- Users / Teams API ---
    let usersSearchTimer = null
    function onUsersSearch() {
      if (usersSearchTimer) clearTimeout(usersSearchTimer)
      usersSearchTimer = setTimeout(() => fetchUsers(), 300)
    }

    let teamsSearchTimer = null
    function onTeamsSearch() {
      if (teamsSearchTimer) clearTimeout(teamsSearchTimer)
      teamsSearchTimer = setTimeout(() => fetchTeams(), 300)
    }

    async function fetchUsers() {
      usersLoading.value = true
      try {
        const r = await axios.get('/api/admin/users', { params: { email: usersQuery.value, nickname: usersQuery.value } })
        users.value = r.data.items || []
        // populate user options used in team member multi-select
        userOptionsSelect.value = users.value.map(u => ({ label: (u.nickname || u.email || ('user-' + u.id)), value: u.id }))
      } catch (e) {
        console.error('fetchUsers failed', e)
      }
      usersLoading.value = false
    }

    async function fetchTeams() {
      teamsLoading.value = true
      try {
        const r = await axios.get('/api/admin/teams')
        teams.value = r.data.items || []
        teamOptionsSelect.value = teams.value.map(t => ({ label: t.name, value: t.id }))
      } catch (e) {
        console.error('fetchTeams failed', e)
      }
      teamsLoading.value = false
    }

    function openEditUser(u) {
      editUser.value = JSON.parse(JSON.stringify(u || { nickname: '', is_admin: false, team_id: null }))
      showUserModal.value = true
    }

    async function saveUser() {
      try {
        const id = editUser.value.id
        const payload = { nickname: editUser.value.nickname, is_admin: !!editUser.value.is_admin, team_id: editUser.value.team_id }
        await axios.put('/api/admin/users/' + id, payload)
        showUserModal.value = false
        await fetchUsers()
      } catch (e) { console.error('saveUser failed', e) }
    }

    function openEditTeam(t) {
      // when editing existing team, include members as array of ids
      if (t && t.id) {
        const members = (t.members || []).map(m => m.id)
        editTeam.value = JSON.parse(JSON.stringify({ id: t.id, name: t.name, members }))
      } else {
        editTeam.value = JSON.parse(JSON.stringify({ name: '', members: [] }))
      }
      showTeamModal.value = true
    }

    async function saveTeam() {
      try {
        let id = editTeam.value.id
        // create team if it doesn't exist (use regular teams POST)
        if (!id) {
          const r = await axios.post('/api/teams', { name: editTeam.value.name })
          id = r.data.team_id
        } else {
          await axios.put('/api/admin/teams/' + id, { name: editTeam.value.name })
        }

        // update membership: compare existing team members with desired
        // find the original team from teams list
        const original = teams.value.find(t => t.id === id) || { members: [] }
        const originalIds = (original.members || []).map(m => m.id)
        const desiredIds = editTeam.value.members || []
        const toAdd = desiredIds.filter(x => !originalIds.includes(x))
        const toRemove = originalIds.filter(x => !desiredIds.includes(x))

        // For each added user, set team_id to id; for removed, set team_id to null
        const ops = []
        for (const uid of toAdd) {
          ops.push(axios.put('/api/admin/users/' + uid, { team_id: id }))
        }
        for (const uid of toRemove) {
          ops.push(axios.put('/api/admin/users/' + uid, { team_id: null }))
        }
        if (ops.length) await Promise.all(ops)

        showTeamModal.value = false
        // refresh both teams and users data
        await Promise.all([fetchTeams(), fetchUsers()])
      } catch (e) { console.error('saveTeam failed', e) }
    }

  // build columns now that handlers exist
    userCols = [
      { title: 'ID', key: 'id' },
      { title: '邮箱', key: 'email' },
      { title: '昵称', key: 'nickname' },
      { title: '管理员', key: 'is_admin' },
      { title: '队伍', key: 'team_name' },
      { title: '操作', key: 'actions', render(row) { return h('div', { style: 'display:flex;gap:6px' }, [ h(NButton, { size: 'small', onClick: () => openEditUser(row) }, { default: () => '编辑' }) ]) } }
    ]

    teamCols = [
      { title: 'ID', key: 'id' },
      { title: '名称', key: 'name' },
      { title: '成员数', key: 'members_count' },
      { title: '操作', key: 'actions', render(row) { return h('div', { style: 'display:flex;gap:6px' }, [ h(NButton, { size: 'small', onClick: () => openEditTeam(row) }, { default: () => '编辑' }) ]) } }
    ]

    async function createChallenge() {
      try {
        const gameId = newChallenge.value.game_id
        if (!gameId) {
          errorMsg.value = '创建题目需要选择比赛'
          return
        }
        const payload = {
          title: newChallenge.value.title,
          flag: newChallenge.value.flag,
          original_points: newChallenge.value.score,
          score: newChallenge.value.score,
        }
        // 主路径：/api/admin/challenges/games/{gameId}/challenges（扁平 POST 已不存在）
        await axios.post(`/api/admin/challenges/games/${gameId}/challenges`, payload)
        newChallenge.value = { title: '', flag: '', score: 100, game_id: null }
        await load()
      } catch (e) { console.error(e); errorMsg.value = '创建题目失败' }
    }

    async function saveChallenge(c) {
      try {
        const gameId = c.game_id
        if (!gameId) {
          errorMsg.value = '保存题目缺少 game_id'
          return
        }
        await axios.put(`/api/admin/challenges/games/${gameId}/challenges/${c.id}`, {
          original_points: c.score,
          score: c.score,
          title: c.title,
          flag: c.flag,
        })
        await load()
      } catch (e) { console.error(e); errorMsg.value = '保存题目失败' }
    }

    async function deleteChallenge(c) {
      try {
        const gameId = c.game_id
        if (!gameId) {
          errorMsg.value = '删除题目缺少 game_id'
          return
        }
        await axios.delete(`/api/admin/challenges/games/${gameId}/challenges/${c.id}`)
        await load()
      } catch (e) { console.error(e); errorMsg.value = '删除题目失败' }
    }

    async function saveGame(g) {
      try {
        // /api/admin/games 已 410；赛事写操作走 competitions 主路径
        await axios.put(`/api/competitions/admin/${g.id}/update`, {
          start_time: g.start_time ? g.start_time.toISOString() : null,
          end_time: g.end_time ? g.end_time.toISOString() : null,
        })
        await load()
      } catch (e) { console.error(e); errorMsg.value = '保存比赛失败' }
    }

    // Division management methods
    async function toggleGameDivisions(gameId) {
      if (expandedGameId.value === gameId) {
        expandedGameId.value = null
      } else {
        expandedGameId.value = gameId
        // Load divisions for this game
        await loadGameDivisions(gameId)
      }
    }

    async function loadGameDivisions(gameId) {
      if (gameDivisions.value[gameId]) return // Already loaded
      loadingDivisions.value = true
      try {
        const r = await axios.get(`/api/competitions/${gameId}/divisions`)
        gameDivisions.value[gameId] = r.data.data || []
      } catch (e) {
        console.error('获取分组失败', e)
        errorMsg.value = '获取分组失败'
      }
      loadingDivisions.value = false
    }

    function openCreateDivisionModal(gameId) {
      editingGameId.value = gameId
      editingDivisionId.value = null
      newDivision.value = { name: '', invite_code: '', school_scope: '', description: '' }
      showDivisionModal.value = true
    }

    async function saveDivision() {
      if (!editingGameId.value) {
        errorMsg.value = '请先选择比赛'
        return
      }
      if (!newDivision.value.name) {
        errorMsg.value = '分组名称不能为空'
        return
      }
      try {
        savingDivision.value = true
        const payload = {
          name: newDivision.value.name,
          invite_code: newDivision.value.invite_code || undefined,
          school_scope: newDivision.value.school_scope || null,
          description: newDivision.value.description || null
        }
        await axios.post(`/api/competitions/admin/${editingGameId.value}/divisions/create`, payload)
        showDivisionModal.value = false
        // Reload divisions for this game
        gameDivisions.value[editingGameId.value] = undefined
        await loadGameDivisions(editingGameId.value)
      } catch (e) {
        console.error('保存分组失败', e)
        errorMsg.value = e.response?.data?.msg || '保存分组失败'
      } finally {
        savingDivision.value = false
      }
    }

    async function viewDivisionMembers(gameId, division) {
      selectedDivision.value = division
      divisionMembersLoading.value = true
      divisionMembers.value = []
      try {
        const r = await axios.get(`/api/competitions/admin/${gameId}/divisions/${division.id}/members`)
        divisionMembers.value = r.data.data?.members || []
      } catch (e) {
        console.error('获取分组成员失败', e)
        errorMsg.value = '获取分组成员失败'
      } finally {
        divisionMembersLoading.value = false
      }
      showDivisionMembersModal.value = true
    }

    function copyToClipboard(text) {
      if (!text) {
        errorMsg.value = '邀请码未设置'
        return
      }
      navigator.clipboard.writeText(text).then(() => {
        console.log('已复制到剪贴板')
      }).catch(e => {
        console.error('复制失败', e)
      })
    }

    async function deleteDivision(gameId, divisionId) {
      if (!confirm('确定要删除这个分组吗？')) return
      try {
        await axios.delete(`/api/competitions/admin/${gameId}/divisions/${divisionId}`)
        // Reload divisions for this game
        gameDivisions.value[gameId] = undefined
        await loadGameDivisions(gameId)
      } catch (e) {
        console.error('删除分组失败', e)
        errorMsg.value = '删除分组失败'
      }
    }

    function refreshUserFromStorage() {
      try {
        const s = localStorage.getItem('neepu_user')
        user.value = s ? JSON.parse(s) : null
        isAdmin.value = !!(user.value && user.value.is_admin)
      } catch (e) { user.value = null; isAdmin.value = false }
    }

    async function tryRefreshFromServer() {
      try {
        const s = localStorage.getItem('neepu_user')
        if (!s) return
        const parsed = JSON.parse(s)
        if (!parsed || !parsed.id) return
        const r = await axios.get('/api/auth/me', { params: { id: parsed.id } })
        if (r && r.data) {
          localStorage.setItem('neepu_user', JSON.stringify(r.data))
          refreshUserFromStorage()
        }
      } catch (e) {
        console.error('refresh user failed', e)
      }
    }

    onMounted(async () => {
      refreshUserFromStorage()
      await tryRefreshFromServer()
      console.log('[Admin] mounted, isAdmin:', isAdmin.value)
      console.log('[Admin] currentTab:', currentTab.value)
      await load()
      console.log('[Admin] games loaded:', games.value.length)
      // prefetch users/teams for admin panel
      if (isAdmin.value) {
        fetchUsers().catch(()=>{})
        fetchTeams().catch(()=>{})
      }
    })

    // expose reactive state and handlers for template
    return { subs, subCols, challenges, newChallenge, createChallenge, saveChallenge, deleteChallenge, games, gameOptions, saveGame, currentTab, loading, errorMsg, isAdmin, user,
      // users/teams
      users, usersLoading, usersQuery, usersTotal, onUsersSearch, fetchUsers, userCols, showUserModal, editUser, openEditUser, saveUser,
      teams, teamsLoading, teamsQuery, onTeamsSearch, fetchTeams, teamCols, showTeamModal, editTeam, openEditTeam, saveTeam, teamOptionsSelect, userOptionsSelect,
      // divisions in games
      expandedGameId, gameDivisions, loadingDivisions, showDivisionModal, editingDivisionId, editingGameId, newDivision, savingDivision,
      toggleGameDivisions, loadGameDivisions, openCreateDivisionModal, saveDivision, 
      showDivisionMembersModal, selectedDivision, divisionMembers, divisionMembersLoading, divisionMemberCols, viewDivisionMembers, copyToClipboard, deleteDivision
    }
  }
}
</script>

<style scoped>
/* small admin styles */
.admin-alert { padding: var(--admin-alert-padding, 20px); border: var(--admin-alert-border, 1px solid #ffd8d8); background: var(--admin-alert-bg, #fff6f6); border-radius: var(--admin-alert-radius, 6px); margin-bottom: var(--admin-alert-margin-bottom, 12px); }
.admin-alert-title { font-weight: 600; color: var(--admin-alert-title-color, #b42318) }
.admin-alert-desc { margin-top: 8px; color: var(--admin-muted-color, #6b7280) }
.admin-alert-actions { margin-top: 10px }
.admin-error { margin-bottom: 10px; color: var(--admin-error-color, #b42318) }
.admin-loading { margin-bottom: 10px; color: var(--admin-loading-color, #0ea5a2) }
.admin-empty { margin: 20px 0; text-align: center; color: var(--admin-muted-color, #6b7280) }
.admin-panel { padding: var(--admin-panel-padding, 10px); border: var(--admin-panel-border, 1px solid #eee); border-radius: var(--admin-panel-radius, 6px); display:flex; flex-direction: column; gap: var(--admin-panel-gap, 12px); }
.admin-create-chal { border-style: dashed; border: var(--admin-panel-dashed-border, 1px dashed #ddd); flex-direction: row; }
.admin-chal-row { padding: var(--admin-panel-padding, 10px); border: var(--admin-panel-border, 1px solid #eee); border-radius: var(--admin-panel-radius, 6px); display:flex; align-items:center; justify-content:space-between; margin-bottom: 8px; flex-direction: row; }
.admin-row { display:flex; align-items:center; gap: var(--admin-row-gap, 12px); flex-wrap: wrap; }
.admin-row-meta { font-size: 12px; color: var(--muted); margin-top: 4px; }
.admin-game-row { padding: var(--admin-panel-padding, 10px); border: var(--admin-panel-border, 1px solid #eee); border-radius: var(--admin-panel-radius, 6px); margin-bottom:8px; flex-direction: column; }
.admin-search-row { display:flex; gap: var(--admin-row-gap, 12px); align-items:center; margin-bottom:8px; flex-wrap: wrap; }
.form-actions { display:flex; gap: var(--profile-actions-gap, 8px); justify-content:flex-end; margin-top: var(--profile-actions-margin-top, 12px) }
.row-actions { display:flex; gap: var(--admin-actions-gap, 8px) }
.code { font-family: monospace; background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
.division-info { background: #f9f9f9; padding: 12px; border-radius: 4px; margin-bottom: 12px; }
.division-info p { margin: 4px 0; }
.game-divisions-section { margin-top: 16px; padding: 12px; background: #f5f5f5; border-radius: 6px; border-left: 4px solid #1890ff; }
.divisions-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.divisions-header h4 { margin: 0; }
.division-item { padding: 10px; background: var(--gradient-card-bg, var(--card-bg)); border: 1px solid #eee; border-radius: 4px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
.division-info-inline { flex: 1; }
.division-meta { font-size: 12px; color: #999; display: inline-block; margin-left: 12px; }
.division-actions { display: flex; gap: 8px; }
</style>
