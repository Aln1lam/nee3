# -*- coding: utf-8 -*-
"""Remove todo from Home.vue and apply golden-ratio profile sidebar."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'Home.vue'
text = p.read_text(encoding='utf-8')

# ── template: remove todo card, enhance profile sidebar ──
OLD_SIDEBAR = '''    <aside class="home-sidebar">
      <n-card class="sidebar-card todo-card" size="small">
        <template #header>
          <div class="sidebar-heading">个人代办</div>
        </template>
        <ul class="todo-list">
          <li v-for="(t,i) in todos" :key="t.id || i" :class="{done: t.done}">
            <label @click.prevent="toggleTodo(i)">
              <input type="checkbox" v-model="t.done" @click.stop /> 
              <span>{{ t.text }}</span>
            </label>
            <button class="todo-delete" @click="removeTodo(i)" title="删除">×</button>
          </li>
        </ul>
        <div class="todo-add">
          <input v-model="newTodo" placeholder="添加代办..." @keyup.enter="addTodo" />
          <button @click="addTodo">添加</button>
        </div>
      </n-card>

      <n-card class="sidebar-card profile-card" size="small">
        <template #header>
          <div class="sidebar-heading">个人信息</div>
        </template>
        <div class="profile">
          <div class="avatar-small"><img :src="getAvatarUrl(user?.avatar)" alt="avatar"/></div>
          <div class="profile-meta">
            <div class="profile-name">{{ user?.nickname || '访客' }}</div>
            <div class="profile-signature">{{ user?.signature || '' }}</div>
          </div>
        </div>
        <div class="profile-actions">
          <button @click="$router.push('/myprofile')">个人主页</button>
          <button @click="$router.push('/games')">我的比赛</button>
        </div>
      </n-card>
    </aside>'''

NEW_SIDEBAR = '''    <aside class="home-sidebar">
      <div class="home-sidebar-head">
        <h2 class="home-sidebar-title">个人工作台</h2>
        <p class="home-sidebar-sub">HOME · DESK</p>
      </div>

      <n-card class="sidebar-card profile-card matrix-panel" size="small" :bordered="false">
        <div class="profile">
          <div class="avatar-small"><img :src="getAvatarUrl(user?.avatar)" alt="avatar"/></div>
          <div class="profile-meta">
            <div class="profile-name">{{ user?.nickname || '访客' }}</div>
            <div class="profile-signature">{{ user?.signature || '暂无签名' }}</div>
          </div>
        </div>
        <div class="profile-actions">
          <button type="button" class="profile-btn" @click="$router.push('/myprofile')">个人主页</button>
          <button type="button" class="profile-btn" @click="$router.push('/games')">我的比赛</button>
        </div>
      </n-card>

      <nav class="home-quick-nav">
        <router-link to="/training" class="sidebar-link">
          <span class="link-code">TRN</span>
          <span>训练靶场</span>
        </router-link>
        <router-link to="/games" class="sidebar-link">
          <span class="link-code">CTF</span>
          <span>赛事中心</span>
        </router-link>
        <router-link to="/wiki" class="sidebar-link">
          <span class="link-code">DOC</span>
          <span>知识库</span>
        </router-link>
        <router-link to="/bulletin" class="sidebar-link">
          <span class="link-code">BUL</span>
          <span>平台公告</span>
        </router-link>
      </nav>
    </aside>'''

if OLD_SIDEBAR not in text:
    raise SystemExit('Home.vue sidebar block not found')
text = text.replace(OLD_SIDEBAR, NEW_SIDEBAR, 1)

# Add page head in main
OLD_MAIN_START = '''    <section class="home-main">
      <!-- Large carousel on top -->
      <section class="hero large-hero">'''

NEW_MAIN_START = '''    <section class="home-main">
      <header class="matrix-page-head home-page-head">
        <p class="matrix-page-prompt">cd ~/home</p>
        <h2 class="matrix-page-title">欢迎回来</h2>
        <p class="matrix-page-desc">轮播 · 赛事日历 · 平台公告</p>
      </header>

      <section class="hero large-hero">'''

text = text.replace(OLD_MAIN_START, NEW_MAIN_START, 1)

# Remove loadTodos from onMounted
text = text.replace('      loadTodos() // Load todos from backend\n', '')

# Remove todo script block
TODO_BLOCK_START = '    // --- sidebar: todos and user ---\n'
TODO_BLOCK_END = '    const user = ref(null)\n'
idx_start = text.find(TODO_BLOCK_START)
idx_end = text.find(TODO_BLOCK_END)
if idx_start == -1 or idx_end == -1:
    raise SystemExit('todo script block not found')
text = text[:idx_start] + '    const user = ref(null)\n' + text[idx_end + len(TODO_BLOCK_END):]

# Fix return statement
text = text.replace(
    '''    return { heroImages, currentIndex, prev, next, go, recentGames, announcements, categories, goCategory,
      todos, newTodo, addTodo, removeTodo, toggleTodo, user, months, currentMonth, currentYear, monthDays, prevMonth, nextMonth,
      fcEvents, onEventClick, fetchAnnouncements, getAvatarUrl, selectedRegion, externalEventsCN, externalEventsGlobal, onSlideClick }''',
    '''    return { heroImages, currentIndex, prev, next, go, recentGames, announcements, categories, goCategory,
      user, months, currentMonth, currentYear, monthDays, prevMonth, nextMonth,
      fcEvents, onEventClick, fetchAnnouncements, getAvatarUrl, selectedRegion, externalEventsCN, externalEventsGlobal, onSlideClick }''',
)

# Replace scoped styles - remove todo, update profile/sidebar
OLD_STYLE_START = '''<style scoped>
.sidebar-card { border-radius:10px; overflow:visible }
.sidebar-heading { font-weight:700 }
.todo-list { list-style:none; padding:8px 4px; margin:0; max-height:180px; overflow:auto }
.todo-list li { padding:6px 8px; display:flex; align-items:center; justify-content:space-between; gap:8px; border-radius:6px; transition:background-color .2s ease }
.todo-list li:hover { background:rgba(0,0,0,0.02) }
.todo-list li label { flex:1; display:flex; align-items:center; gap:8px; cursor:pointer }
.todo-list li.done span { text-decoration: line-through; opacity:0.6 }
.todo-delete { width:24px; height:24px; border-radius:50%; background:transparent; border:none; color:#999; font-size:20px; line-height:1; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all .2s ease; flex-shrink:0 }
.todo-delete:hover { background:#ff6b6b; color:#fff; transform:scale(1.1) }
.todo-add { display:flex; gap:8px; padding:8px }
.todo-add input { flex:1; padding:6px 8px; border-radius:6px; border:1px solid var(--border) }
.todo-add button { padding:6px 10px; border-radius:6px }
.profile { display:flex; gap:12px; align-items:center; padding:12px 0 }
.avatar-small { width:56px; height:56px; border-radius:8px; overflow:hidden; border:1px solid rgba(0,0,0,0.06) }
.avatar-small img { width:100%; height:100%; object-fit:cover }
.profile-meta { font-size:13px }
.profile-name { font-weight:700 }
.profile-signature { color:#888; font-size:12px; margin-top:2px }
.profile-actions { display:flex; gap:8px; padding-top:8px }
.profile-actions button { padding:6px 10px; border-radius:6px }
'''

NEW_STYLE_START = '''<style scoped>
.home-sidebar-head {
  margin-bottom: var(--fib-13, 13px);
}
.home-sidebar-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--primary);
}
.home-sidebar-sub {
  margin: var(--fib-8, 8px) 0 0;
  font-size: var(--text-xs);
  letter-spacing: 0.1em;
  color: var(--muted);
  text-transform: uppercase;
}
.home-quick-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: var(--fib-13, 13px);
}
.home-page-head {
  margin-bottom: var(--fib-21, 21px);
}
.sidebar-card { border-radius: var(--card-radius); overflow: visible; }
.profile { display: flex; gap: var(--fib-13, 13px); align-items: center; padding: var(--fib-8, 8px) 0; }
.avatar-small {
  width: var(--fib-55, 55px);
  height: var(--fib-55, 55px);
  border-radius: var(--card-radius);
  overflow: hidden;
  border: 1px solid var(--border);
  flex-shrink: 0;
}
.avatar-small img { width: 100%; height: 100%; object-fit: cover; }
.profile-meta { font-size: var(--text-sm); min-width: 0; }
.profile-name { font-weight: 700; color: var(--text); }
.profile-signature { color: var(--muted); font-size: var(--text-xs); margin-top: var(--fib-8, 8px); }
.profile-actions { display: flex; flex-wrap: wrap; gap: var(--fib-8, 8px); padding-top: var(--fib-13, 13px); }
.profile-btn {
  padding: var(--fib-8, 8px) var(--fib-13, 13px);
  border-radius: var(--card-radius);
  border: 1px solid var(--border);
  background: transparent;
  color: var(--primary);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: background 0.15s, border-color 0.15s;
}
.profile-btn:hover {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
}
'''

if OLD_STYLE_START not in text:
    raise SystemExit('Home.vue style block not found')
text = text.replace(OLD_STYLE_START, NEW_STYLE_START, 1)

# Fix announcement colors to use theme vars
text = text.replace(
    '.announcement-title { font-weight: 600; font-size: 13px; color: #333; margin-bottom: 4px; }',
    '.announcement-title { font-weight: 600; font-size: var(--text-sm); color: var(--text); margin-bottom: 4px; }',
)
text = text.replace(
    '.announcement-content { font-size: 12px; color: #666; line-height: 1.5; }',
    '.announcement-content { font-size: var(--text-xs); color: var(--muted); line-height: 1.5; }',
)

p.write_text(text, encoding='utf-8', newline='\n')
print('ok Home.vue: todos removed, golden sidebar')
