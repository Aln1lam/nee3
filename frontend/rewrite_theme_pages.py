# -*- coding: utf-8 -*-
"""Rewrite off-theme pages to Matrix / auth-aux / golden-ratio layout."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'


def write(name, content):
    p = ROOT / name
    p.write_text(content.strip() + '\n', encoding='utf-8', newline='\n')
    print(f'wrote {name}')


write('Scoreboard.vue', r'''
<template>
  <MatrixShell
    prompt="neepu@ctf:~$"
    title="积分排行"
    subtitle="SCORE · BOARD"
    :page-prompt="`curl /games/${gameId}/scoreboard`"
    page-title="赛事排行榜"
    page-desc="实时积分 · 解题数 · 最后提交"
    :items="navItems"
  >
    <template #sidebar-footer>
      <router-link :to="`/games/${gameId}`" class="sidebar-link">
        <span class="link-code">GME</span>
        <span>返回赛事</span>
      </router-link>
      <router-link to="/games" class="sidebar-link">
        <span class="link-code">CTF</span>
        <span>赛事列表</span>
      </router-link>
    </template>

    <div class="scoreboard-layout">
      <div class="matrix-panel scoreboard-panel matrix-data-panel">
        <div class="scoreboard-toolbar">
          <div>
            <span class="link-code">SB</span>
            <strong>Game #{{ gameId }}</strong>
          </div>
          <div class="toolbar-actions">
            <n-button size="small" @click="refresh">刷新</n-button>
            <n-button size="small" quaternary @click="goBack">返回</n-button>
          </div>
        </div>
        <n-spin :show="loading">
          <table v-if="items.length" class="scoreboard-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>队伍</th>
                <th>得分</th>
                <th>解题</th>
                <th>人数</th>
                <th>最后提交</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(it, idx) in items"
                :key="it.team_id || idx"
                class="scoreboard-row"
                :class="{ top3: idx < 3 }"
              >
                <td>{{ it.rank || idx + 1 }}</td>
                <td>{{ it.team_name }}</td>
                <td>{{ it.total_points }}</td>
                <td>{{ it.solved_challenges }}</td>
                <td>{{ it.members_count }}</td>
                <td>{{ formatTime(it.last_submission_time) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">
            <p class="matrix-page-prompt">scoreboard --empty</p>
            <p class="muted">暂无排行数据</p>
          </div>
        </n-spin>
      </div>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, watch, inject, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NSpin } from 'naive-ui'
import { MatrixShell } from '@/components/shared'

export default {
  name: 'Scoreboard',
  components: { MatrixShell, NButton, NSpin },
  props: { gameId: { type: [String, Number], required: true } },
  setup(props) {
    const axios = inject('axios')
    const router = useRouter()
    const items = ref([])
    const loading = ref(false)
    const navItems = computed(() => [{ code: 'SB', label: '排行榜', active: true }])

    function formatTime(timeStr) {
      if (!timeStr) return '-'
      try {
        return new Date(timeStr).toLocaleString('zh-CN')
      } catch {
        return timeStr
      }
    }

    async function load() {
      if (!props.gameId) return
      loading.value = true
      try {
        const { data } = await axios.get(`/api/ctf/games/${props.gameId}/scoreboard`)
        items.value = data.data?.rankings || data?.rankings || []
      } catch (e) {
        console.error('Failed to load scoreboard:', e)
        items.value = []
      } finally {
        loading.value = false
      }
    }

    function refresh() { load() }
    function goBack() { router.push(`/games/${props.gameId}`) }

    watch(() => props.gameId, load, { immediate: true })

    return { items, loading, navItems, refresh, goBack, formatTime }
  },
}
</script>

<style scoped>
.toolbar-actions {
  display: flex;
  gap: var(--fib-8);
}

.empty-state {
  padding: var(--fib-34);
  text-align: center;
  color: var(--muted);
}
</style>
''')


AUTH_FORM_STYLES = '''
<style scoped>
form {
  display: flex;
  flex-direction: column;
  gap: var(--fib-13);
}
.note {
  font-size: var(--text-xs);
  color: var(--muted);
}
.icon {
  font-size: 2rem;
}
</style>
'''


write('ForgotPassword.vue', r'''
<template>
  <div class="landing-page auth-aux-page">
    <div class="auth-aux-shell">
      <div class="matrix-panel auth-aux-card">
        <header class="auth-aux-head">
          <LinuxPrompt path="~/auth" cmd="recover --password" extra-class="page-eyebrow--linux" />
          <h1 class="auth-aux-title">忘记密码</h1>
          <p class="auth-aux-desc">输入注册邮箱，我们将发送密码重置链接</p>
        </header>

        <form v-if="!sent" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>邮箱地址</label>
            <input
              v-model="email"
              type="email"
              placeholder="your@email.com"
              required
              :disabled="loading"
            />
          </div>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? '发送中...' : '发送重置链接' }}
          </button>
          <p v-if="error" class="error-msg">{{ error }}</p>
        </form>

        <div v-else class="success-state">
          <div class="icon">📧</div>
          <h2>邮件已发送</h2>
          <p>如果该邮箱已注册，你将收到一封包含密码重置链接的邮件。</p>
          <p class="note">请检查收件箱和垃圾邮件文件夹。</p>
          <button type="button" class="btn-secondary" @click="sent = false">重新发送</button>
        </div>

        <div class="links">
          <router-link to="/auth">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject } from 'vue'
import { LinuxPrompt } from '@/components/shared'

export default {
  name: 'ForgotPassword',
  components: { LinuxPrompt },
  setup() {
    const axios = inject('axios')
    const email = ref('')
    const loading = ref(false)
    const sent = ref(false)
    const error = ref('')

    async function handleSubmit() {
      if (!email.value) return
      loading.value = true
      error.value = ''
      try {
        await axios.post('/api/auth/forgot-password', { email: email.value })
        sent.value = true
      } catch {
        error.value = '发送失败，请稍后重试'
      } finally {
        loading.value = false
      }
    }

    return { email, loading, sent, error, handleSubmit }
  },
}
</script>
''' + AUTH_FORM_STYLES)


write('ResetPassword.vue', r'''
<template>
  <div class="landing-page auth-aux-page">
    <div class="auth-aux-shell">
      <div class="matrix-panel auth-aux-card">
        <header class="auth-aux-head">
          <LinuxPrompt path="~/auth" cmd="passwd --reset" extra-class="page-eyebrow--linux" />
          <h1 class="auth-aux-title">设置新密码</h1>
          <p v-if="!success" class="auth-aux-desc">请输入你的新密码</p>
        </header>

        <div v-if="success" class="success-state">
          <div class="icon">✅</div>
          <h2>密码重置成功</h2>
          <p>你的密码已更新，现在可以使用新密码登录。</p>
          <button type="button" class="btn-primary" @click="goLogin">前往登录</button>
        </div>

        <form v-else @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>新密码</label>
            <input
              v-model="password"
              type="password"
              placeholder="至少6个字符"
              required
              minlength="6"
              :disabled="loading"
            />
          </div>
          <div class="form-group">
            <label>确认密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="再次输入新密码"
              required
              :disabled="loading"
            />
          </div>
          <button type="submit" class="btn-primary" :disabled="loading || !isValid">
            {{ loading ? '重置中...' : '重置密码' }}
          </button>
          <p v-if="error" class="error-msg">{{ error }}</p>
        </form>

        <div class="links">
          <router-link to="/auth">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { LinuxPrompt } from '@/components/shared'

export default {
  name: 'ResetPassword',
  components: { LinuxPrompt },
  setup() {
    const axios = inject('axios')
    const router = useRouter()
    const route = useRoute()
    const password = ref('')
    const confirmPassword = ref('')
    const loading = ref(false)
    const success = ref(false)
    const error = ref('')
    const isValid = computed(() => password.value.length >= 6 && password.value === confirmPassword.value)

    async function handleSubmit() {
      if (!isValid.value) {
        error.value = password.value !== confirmPassword.value
          ? '两次输入的密码不一致'
          : '密码至少需要6个字符'
        return
      }
      const token = route.query.token
      if (!token) {
        error.value = '无效的重置链接'
        return
      }
      loading.value = true
      error.value = ''
      try {
        await axios.post('/api/auth/reset-password', { token, password: password.value })
        success.value = true
      } catch (e) {
        const msg = e.response?.data?.msg || '重置失败'
        if (msg === 'token expired') error.value = '重置链接已过期，请重新申请'
        else if (msg === 'invalid token') error.value = '无效的重置链接'
        else error.value = msg
      } finally {
        loading.value = false
      }
    }

    function goLogin() { router.push('/auth') }

    return { password, confirmPassword, loading, success, error, isValid, handleSubmit, goLogin }
  },
}
</script>
''' + AUTH_FORM_STYLES)


write('VerifyEmail.vue', r'''
<template>
  <div class="landing-page auth-aux-page">
    <div class="auth-aux-shell">
      <div class="matrix-panel auth-aux-card">
        <header class="auth-aux-head">
          <LinuxPrompt path="~/auth" cmd="verify --email" extra-class="page-eyebrow--linux" />
          <h1 class="auth-aux-title">邮箱验证</h1>
        </header>

        <div v-if="loading" class="status">
          <n-spin size="medium" />
          <p>正在验证邮箱...</p>
        </div>

        <div v-else-if="success" class="success-state">
          <div class="icon">✅</div>
          <h2>邮箱验证成功</h2>
          <p>你的邮箱 <strong>{{ email }}</strong> 已验证</p>
          <button type="button" class="btn-primary" @click="goLogin">前往登录</button>
        </div>

        <div v-else class="status">
          <div class="icon">❌</div>
          <h2>验证失败</h2>
          <p>{{ errorMsg }}</p>
          <button type="button" class="btn-secondary" @click="goHome">返回首页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NSpin } from 'naive-ui'
import { LinuxPrompt } from '@/components/shared'

export default {
  name: 'VerifyEmail',
  components: { LinuxPrompt, NSpin },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const axios = inject('axios')
    const loading = ref(true)
    const success = ref(false)
    const email = ref('')
    const errorMsg = ref('')

    async function verify() {
      const token = route.query.token
      if (!token) {
        loading.value = false
        errorMsg.value = '缺少验证令牌'
        return
      }
      try {
        const res = await axios.post('/api/auth/verify-email', { token })
        success.value = true
        email.value = res.data.email || ''
      } catch (e) {
        const msg = e.response?.data?.msg || '验证失败'
        if (msg === 'token expired') {
          errorMsg.value = '验证链接已过期，请重新注册或请求新的验证邮件'
        } else if (msg === 'invalid token') {
          errorMsg.value = '无效的验证链接'
        } else {
          errorMsg.value = msg
        }
      } finally {
        loading.value = false
      }
    }

    onMounted(verify)
    function goLogin() { router.push('/auth') }
    function goHome() { router.push('/home') }

    return { loading, success, email, errorMsg, goLogin, goHome }
  },
}
</script>
''' + AUTH_FORM_STYLES)


write('Archive.vue', r'''
<template>
  <MatrixShell
    prompt="neepu@ctf:~$"
    title="资料归档"
    subtitle="ARC · ARCHIVE"
    page-prompt="ls ~/archive"
    page-title="归档库"
    page-desc="往届比赛 · 资料 · 文章沉淀"
    :items="navItems"
  >
    <template #sidebar-footer>
      <router-link to="/" class="sidebar-link">
        <span class="link-code">HOM</span>
        <span>返回首页</span>
      </router-link>
      <router-link to="/wiki" class="sidebar-link">
        <span class="link-code">DOC</span>
        <span>知识库</span>
      </router-link>
    </template>

    <div class="archive-list">
      <article v-for="a in archives" :key="a.id" class="archive-item">
        <span class="link-code">ARC</span>
        <div class="archive-body">
          <h3 class="archive-title">{{ a.title }}</h3>
          <time class="archive-date">{{ a.date }}</time>
        </div>
      </article>
    </div>
  </MatrixShell>
</template>

<script>
import { MatrixShell } from '@/components/shared'

export default {
  name: 'Archive',
  components: { MatrixShell },
  data() {
    return {
      navItems: [{ code: 'ARC', label: '全部归档', active: true }],
      archives: [
        { id: 1, title: 'NEEPU CTF 2024 归档', date: '2024-12' },
        { id: 2, title: 'NEEPU Workshop Materials', date: '2025-03' },
      ],
    }
  },
}
</script>

<style scoped>
.archive-item {
  display: flex;
  align-items: flex-start;
  gap: var(--fib-13);
}

.archive-title {
  margin: 0 0 var(--fib-8);
  font-size: var(--text-lg);
  font-weight: 600;
}

.archive-date {
  font-size: var(--text-xs);
  color: var(--muted);
}
</style>
''')


write('Submissions.vue', r'''
<template>
  <MatrixShell
    prompt="neepu@ctf:~$"
    title="提交审计"
    subtitle="SUB · AUDIT"
    page-prompt="grep flag /submissions"
    page-title="提交记录"
    page-desc="按题目 ID 检索 Flag 提交历史"
    :items="navItems"
  >
    <div class="matrix-panel matrix-data-panel">
      <div class="matrix-page-head">
        <span class="link-code">SRH</span>
        <n-input-group>
          <n-input v-model:value="cid" placeholder="Challenge ID..." style="max-width: 280px" />
          <n-button type="primary" @click="load">检索</n-button>
        </n-input-group>
      </div>
      <div class="table-wrapper">
        <n-data-table :columns="columns" :data="data" :bordered="false" :single-line="false" />
      </div>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, inject, h } from 'vue'
import { NDataTable, NTag, NInput, NInputGroup, NButton } from 'naive-ui'
import { MatrixShell } from '@/components/shared'

export default {
  name: 'Submissions',
  components: { NDataTable, NInput, NInputGroup, NButton, MatrixShell },
  setup() {
    const axios = inject('axios')
    const cid = ref('')
    const data = ref([])
    const navItems = [{ code: 'SUB', label: '提交审计', active: true }]

    const columns = [
      { title: 'Time', key: 'created_at', width: 200 },
      { title: 'Flag Payload', key: 'flag', ellipsis: true },
      {
        title: 'Status',
        key: 'correct',
        width: 100,
        render(row) {
          return h(
            NTag,
            { type: row.correct ? 'success' : 'error', bordered: false, size: 'small' },
            { default: () => (row.correct ? 'CORRECT' : 'WRONG') },
          )
        },
      },
    ]

    async function load() {
      if (!cid.value) return
      try {
        const res = await axios.get(`/api/games/challenges/${cid.value}/submissions`)
        data.value = res.data.items || []
      } catch {
        data.value = []
      }
    }

    return { cid, data, columns, load, navItems }
  },
}
</script>
''')


write('Teams.vue', r'''
<template>
  <MatrixShell
    prompt="neepu@ctf:~$"
    title="战队终端"
    subtitle="TEAM · GLOBAL"
    page-prompt="team status"
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
        <p class="matrix-page-prompt">team status ?empty</p>
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
''')


print('rewrite_theme_pages.py done')
