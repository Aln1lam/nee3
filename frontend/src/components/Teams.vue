<template>
  <MatrixShell
    prompt=""
    title="战队终端"
    subtitle="TEAM · GLOBAL"
    page-prompt="战队大厅 · TEAM"
    page-title="全局战队"
    page-desc="创建或加入跨赛事通用战队"
    :items="navItems"
  >
    <div class="teams-page-grid">
      <div v-if="!team">
        <div class="matrix-panel" style="margin-bottom: var(--fib-21)">
          <div class="matrix-section-head">
            <span class="link-code">NEW</span>
            <h3>创建战队</h3>
          </div>
          <n-input-group>
            <n-input v-model:value="name" placeholder="输入新战队名称..." />
            <n-button type="primary" @click="create">创建</n-button>
          </n-input-group>
          <div v-if="created" class="console-msg">
            战队建立成功 · ID: {{ created.team_id }} · 邀请码: {{ created.invite_code }}
            <n-button size="tiny" quaternary @click="copyInvite">复制</n-button>
          </div>
        </div>
        <div class="matrix-panel">
          <div class="matrix-section-head">
            <span class="link-code">KEY</span>
            <h3>加入战队</h3>
          </div>
          <n-input-group>
            <n-input v-model:value="invite" placeholder="输入邀请码..." />
            <n-button @click="join">加入</n-button>
          </n-input-group>
        </div>
      </div>

      <div v-else class="matrix-panel">
        <div class="matrix-section-head">
          <span class="link-code">TEA</span>
          <h3>{{ team.name }}</h3>
        </div>
        <p class="muted">ID: {{ team.id }} · CODE: {{ team.invite_code }}</p>
        <n-divider />
        <div v-for="m in team.members" :key="m.id" class="member-row">
          <span class="link-code">USR</span>
          <span>{{ m.nickname || 'Unknown' }}</span>
          <span class="muted">#{{ m.id }}</span>
        </div>
      </div>

      <div v-if="!team" class="matrix-panel empty-panel">
        <p class="matrix-page-prompt">暂无战队，创建或加入一支队伍开始</p>
        <p class="muted">请创建或加入战队以激活面板</p>
      </div>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, inject } from 'vue'
import { useRoute } from 'vue-router'
import { NInput, NInputGroup, NButton, NDivider } from 'naive-ui'
import { MatrixShell } from '@/components/shared'

export default {
  name: 'Teams',
  components: { NInput, NInputGroup, NButton, NDivider, MatrixShell },
  setup() {
    const axios = inject('axios')
    const route = useRoute()
    const name = ref('')
    const invite = ref('')
    const team = ref(null)
    const created = ref(null)
    const navItems = [{ code: 'TEA', label: '我的战队', active: true }]

    async function load() {
      try {
        const teamId = route.query.team_id
        if (teamId) {
          const { data } = await axios.get(`/api/teams/${teamId}`)
          team.value = data?.id || data?.name ? data : null
        } else {
          const { data } = await axios.get('/api/teams/me')
          team.value = data?.id || data?.name ? data : null
        }
      } catch {
        team.value = null
      }
    }

    async function create() {
      try {
        const { data } = await axios.post('/api/teams/', { name: name.value })
        created.value = data
        await load()
      } catch (e) {
        alert(e.response?.data?.msg || '创建失败')
      }
    }

    async function join() {
      try {
        await axios.post('/api/teams/join', { invite_code: invite.value })
        await load()
      } catch (e) {
        alert(e.response?.data?.msg || '加入失败')
      }
    }

    function copyInvite() {
      if (created.value) navigator.clipboard.writeText(created.value.invite_code)
    }

    load()
    return { name, invite, team, created, create, join, copyInvite, navItems }
  },
}
</script>

<style scoped>
.console-msg {
  margin-top: var(--fib-13);
  padding: var(--fib-13);
  background: var(--hover);
  border-radius: var(--card-radius);
  font-size: var(--text-sm);
}

.member-row {
  display: flex;
  align-items: center;
  gap: var(--fib-13);
  padding: var(--fib-13) 0;
  border-bottom: 1px solid var(--border);
}

.empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: var(--fib-233);
  text-align: center;
}
</style>
