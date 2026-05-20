<template>
  <div class="page-container">
    
    <div class="bracket-title center-mb">
      <span class="bracket">[</span>
      <span class="title-text">战队终端</span>
      <span class="bracket">]</span>
    </div>

    <n-grid x-gap="40" cols="1 m:2" responsive="screen">
      
      <n-grid-item>
        <div v-if="!team">
          <div class="panel">
            <h3 class="panel-title">/// CREATE_TEAM</h3>
            <n-input-group>
              <n-input v-model:value="name" placeholder="输入新战队名称..." />
              <n-button type="error" ghost @click="create">执行创建</n-button>
            </n-input-group>
            
            <div v-if="created" class="console-msg success">
              > [SUCCESS] 战队建立成功<br>
              > ID: {{ created.team_id }}<br>
              > INVITE_CODE: <span class="code">{{ created.invite_code }}</span>
              <n-button size="tiny" secondary @click="copyInvite" style="margin-left:10px">COPY</n-button>
            </div>
          </div>

          <div class="panel" style="margin-top: 40px">
            <h3 class="panel-title">/// JOIN_TEAM</h3>
            <n-input-group>
              <n-input v-model:value="invite" placeholder="输入邀请码 (如: inv-red)..." />
              <n-button type="default" @click="join">确认加入</n-button>
            </n-input-group>
          </div>
        </div>
        <div v-else>
          <div class="status-card">
            <div class="status-header">
              <span class="label">CURRENT STATUS</span>
              <span class="dot online"></span>
            </div>
            
            <div class="team-info">
              <h1>{{ team.name }}</h1>
              <div class="meta-row">
                <span class="key">ID:</span> <span class="val">{{ team.id }}</span>
              </div>
              <div class="meta-row">
                <span class="key">CODE:</span> <span class="val blur">{{ team.invite_code }}</span>
              </div>
            </div>

            <n-divider />
            
            <div class="members-list">
              <div class="list-title">MEMBERS [{{ team.members.length }}]</div>
              <div class="member-row" v-for="m in team.members" :key="m.id">
                <span class="role-icon">👤</span>
                <span class="member-name">{{ m.nickname || 'Unknown' }}</span>
                <span class="member-id">#{{ m.id }}</span>
              </div>
            </div>
          </div>
        </div>
      </n-grid-item>

      <n-grid-item>
        <div class="empty-state" v-if="!team">
          <div class="glitch-text">NO TEAM DATA</div>
          <p>请创建或加入一个战队以激活面板</p>
        </div>
      </n-grid-item>
    
    </n-grid>
  </div>
</template>

<script>
import { ref, inject } from 'vue'
import { useRoute } from 'vue-router'
import { NGrid, NGridItem, NInput, NInputGroup, NButton, NDivider } from 'naive-ui'

export default {
  components: { NGrid, NGridItem, NInput, NInputGroup, NButton, NDivider },
  setup() {
    const axios = inject('axios')
    const route = useRoute()
    const name = ref('')
    const invite = ref('')
    const team = ref(null)
    const created = ref(null)

    async function load() {
      try {
        const teamId = route.query.team_id
        if (teamId) {
          const { data } = await axios.get(`/api/teams/${teamId}`)
          if (data && (data.id || data.name)) team.value = data
          else team.value = null
        } else {
          const { data } = await axios.get('/api/teams/me')
          if (data && (data.id || data.name)) team.value = data
          else team.value = null
        }
      } catch (e) { console.error(e); team.value = null }
    }

    async function create() {
      try {
        const { data } = await axios.post('/api/teams/', { name: name.value })
        created.value = data
        await load()
      } catch (e) {
        console.error('create team failed', e)
        try {
          if (e.response) {
            const st = e.response.status
            let body = e.response.data
            if (typeof body !== 'string') {
              try { body = JSON.stringify(body) } catch (_) { body = String(body) }
            }
            alert(`创建失败: HTTP ${st}\n${body}`)
          } else {
            alert('创建失败: ' + (e.message || String(e)))
          }
        } catch (_) {
          alert('创建失败')
        }
      }
    }

    async function join() {
      try {
        await axios.post('/api/teams/join', { invite_code: invite.value })
        await load()
      } catch (e) {
        console.error('join team failed', e)
        try {
          if (e.response) {
            const st = e.response.status
            let body = e.response.data
            if (typeof body !== 'string') {
              try { body = JSON.stringify(body) } catch (_) { body = String(body) }
            }
            alert(`加入失败: HTTP ${st}\n${body}`)
          } else {
            alert('加入失败: ' + (e.message || String(e)))
          }
        } catch (_) {
          alert('加入失败')
        }
      }
    }

    function copyInvite() {
        if(created.value) navigator.clipboard.writeText(created.value.invite_code)
    }

    load()
    return { name, invite, team, created, create, join, copyInvite }
  }
}
</script>

<style scoped>
.page-container { padding: var(--teams-page-padding, 40px); font-family: 'Fira Code', monospace; }
.center-mb { text-align: center; margin-bottom: var(--teams-title-margin-bottom, 60px); font-size: var(--teams-title-font-size, 1.5rem); font-weight: 700; }
.bracket { color: var(--teams-bracket-color, #ccc); }

.panel-title { color: var(--teams-panel-title-color, #999); font-size: var(--teams-panel-title-font-size, 0.9rem); margin-bottom: 15px; border-left: var(--teams-panel-title-border-left, 3px solid #ff5252); padding-left: var(--teams-panel-title-padding-left, 10px); }

.console-msg {
  background: var(--teams-console-bg, #f4f4f4); padding: var(--teams-console-padding, 15px); margin-top: 15px; border-radius: 4px; font-size: var(--teams-console-font-size, 0.85rem); color: var(--teams-console-color, #555);
  border-left: var(--teams-console-border-left, 2px solid #52c41a);
}
.code { font-weight: bold; color: var(--teams-code-color, #333); }

/* 状态卡片 */
.status-card {
  background: var(--teams-status-bg, white); border: var(--teams-status-border, 1px solid #e0e0e0); padding: var(--teams-status-padding, 30px);
  box-shadow: var(--teams-status-shadow, 0 10px 30px rgba(0,0,0,0.03));
}
.status-header { display: flex; justify-content: space-between; font-size: var(--teams-status-header-font-size, 0.7rem); color: var(--teams-status-header-color, #bbb); letter-spacing: 1px; margin-bottom: 20px;}
.dot.online { width: 8px; height: 8px; background: var(--teams-dot-online, #52c41a); border-radius: 50%; box-shadow: 0 0 5px var(--teams-dot-online, #52c41a);}

.team-info h1 { margin: 0 0 20px; font-size: var(--teams-h1-size, 2rem); }
.meta-row { display: flex; margin-bottom: 5px; font-size: var(--teams-meta-font-size, 0.9rem); }
.meta-row .key { width: var(--teams-meta-key-width, 60px); color: var(--teams-meta-key-color, #999); }
.meta-row .val.blur { filter: blur(4px); transition: 0.3s; cursor: pointer; }
.meta-row .val.blur:hover { filter: none; }

.list-title { font-size: var(--teams-list-title-size, 0.8rem); color: var(--teams-list-title-color, #ccc); margin-bottom: 15px; }
.member-row { display: flex; align-items: center; padding: var(--teams-member-row-padding, 8px 0); border-bottom: var(--teams-member-row-border, 1px dashed #eee); }
.role-icon { margin-right: 10px; opacity: 0.5; }
.member-name { flex: 1; font-weight: 600; color: var(--teams-member-name-color, #555); }
.member-id { color: var(--teams-member-id-color, #ccc); font-size: 0.8rem; }

.empty-state {
  text-align: center; padding: var(--teams-empty-padding, 60px); border: var(--teams-empty-border, 2px dashed #eee); color: var(--teams-list-title-color, #ccc);
}
</style>