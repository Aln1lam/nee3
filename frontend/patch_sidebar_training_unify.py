# -*- coding: utf-8 -*-
"""Unify list sidebars to /training pattern: 248px rail, sidebar-item, useCollapsibleSidebar."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'


def patch_knowledge_list():
    p = ROOT / 'KnowledgeList.vue'
    text = p.read_text(encoding='utf-8')

    old_sidebar = '''      <div class="wiki-search sidebar-rail-nav">
        <n-input
          v-model:value="q"
          placeholder="搜索标题或内容"
          size="small"
          @keyup.enter="fetch"
        />
        <div class="wiki-search-actions">
          <n-button size="small" type="primary" @click="fetch">搜索</n-button>
          <n-button size="small" secondary @click="$router.push('/knowledge/new')">上传</n-button>
        </div>

        <div class="wiki-section-title">标签</div>
        <div class="wiki-tags">
          <button
            v-for="c in categories"
            :key="c"
            type="button"
            class="sidebar-item wiki-tag"
            :class="{ active: selectedTag === c }"
            @click="selectTag(c)"
          >
            <span class="item-code">TAG</span>
            <span class="item-title">{{ c }}</span>
          </button>
        </div>
        <button type="button" class="sidebar-link wiki-clear" @click="clearCategory">
          <span class="link-code">CLR</span>
          <span>清除筛选</span>
        </button>
      </div>

      <div class="sidebar-links sidebar-rail-footer">'''

    new_sidebar = '''      <div class="sidebar-rail-nav">
        <div class="sidebar-group">
          <div class="group-label">分类</div>
          <button
            v-for="c in categories"
            :key="c"
            type="button"
            class="sidebar-item"
            :class="{ active: selectedTag === c }"
            @click="selectTag(c)"
          >
            <span class="item-code">{{ tagCode(c) }}</span>
            <span class="item-title">{{ c }}</span>
          </button>
        </div>
      </div>

      <div class="sidebar-links sidebar-rail-footer">
        <button type="button" class="sidebar-link" @click="clearCategory">
          <span class="link-code">CLR</span>
          <span>清除筛选</span>
        </button>'''

    if old_sidebar not in text:
        raise SystemExit('KnowledgeList sidebar block not found')
    text = text.replace(old_sidebar, new_sidebar, 1)

    old_main = '''      <header class="matrix-page-head">
        <LinuxPrompt path="~/wiki" cmd="ls articles/" extra-class="matrix-page-prompt" />
        <h2 class="matrix-page-title">Wiki 文档</h2>
        <p class="matrix-page-desc">
          <span v-if="selectedTag">当前标签：{{ selectedTag }}（{{ articles.length }} 篇）</span>
          <span v-else>WriteUp · 教程 · 知识沉淀（{{ articles.length }} 篇）</span>
        </p>
      </header>

      <div class="wiki-list-panel matrix-panel">'''

    new_main = '''      <header class="matrix-page-head">
        <LinuxPrompt path="~/wiki" cmd="ls articles/" extra-class="matrix-page-prompt" />
        <h2 class="matrix-page-title">Wiki 文档</h2>
        <p class="matrix-page-desc">
          <span v-if="selectedTag">当前标签：{{ selectedTag }}（{{ articles.length }} 篇）</span>
          <span v-else>WriteUp · 教程 · 知识沉淀（{{ articles.length }} 篇）</span>
        </p>
      </header>

      <div class="wiki-toolbar matrix-panel">
        <n-input
          v-model:value="q"
          placeholder="搜索标题或内容"
          size="small"
          @keyup.enter="fetch"
        />
        <div class="wiki-search-actions">
          <n-button size="small" type="primary" @click="fetch">搜索</n-button>
          <n-button size="small" secondary @click="$router.push('/knowledge/new')">上传</n-button>
        </div>
      </div>

      <div class="wiki-list-panel matrix-panel">'''

    if old_main not in text:
        raise SystemExit('KnowledgeList main block not found')
    text = text.replace(old_main, new_main, 1)

    old_script = '''import { LinuxPrompt } from '@/components/shared'

export default {
  components: { NInput, NButton, NTag, LinuxPrompt },
  setup() {
    const axios = inject('axios') || axiosGlobal
    const route = useRoute()
    const router = useRouter()
    const articles = ref([])
    const q = ref('')
    const selectedTag = ref('')
    const categories = TAGS
    const collapsed = ref(false)

    function toggleSidebar() {
      collapsed.value = !collapsed.value
    }'''

    new_script = '''import { LinuxPrompt } from '@/components/shared'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'

export default {
  components: { NInput, NButton, NTag, LinuxPrompt },
  setup() {
    const axios = inject('axios') || axiosGlobal
    const route = useRoute()
    const router = useRouter()
    const articles = ref([])
    const q = ref('')
    const selectedTag = ref('')
    const categories = TAGS
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_wiki_sidebar_collapsed')

    function tagCode(tag) {
      const t = (tag || '').toLowerCase()
      if (t.includes('环境')) return 'ENV'
      if (t.includes('misc') or t.includes('杂项')) return 'MSC'
      if (t.includes('web')) return 'WEB'
      if (t.includes('crypto') or t.includes('密码')) return 'CRY'
      if (t.includes('reverse') or t.includes('逆向')) return 'REV'
      if (t.includes('pwn') or t.includes('二进制')) return 'PWN'
      if (t.includes('awd')) return 'AWD'
      if (t.includes('ai') or t.includes('人工智能')) return 'AI'
      if (t.includes('blockchain') or t.includes('区块链')) return 'BC'
      if (t.includes('其他')) return 'OTH'
      return 'DOC'
    }'''

    # Fix Python or -> JS or in tagCode
    new_script = new_script.replace(' or ', ' || ')

    if old_script not in text:
        raise SystemExit('KnowledgeList script block not found')
    text = text.replace(old_script, new_script, 1)

    old_return = '''    return {
      articles, q, fetch, categories, selectTag, clearCategory,
      selectedTag, goArticle, renderTags, collapsed, toggleSidebar,
    }'''

    new_return = '''    return {
      articles, q, fetch, categories, selectTag, clearCategory, tagCode,
      selectedTag, goArticle, renderTags, collapsed, toggleSidebar,
    }'''

    if old_return not in text:
        raise SystemExit('KnowledgeList return block not found')
    text = text.replace(old_return, new_return, 1)

    old_style = '''.wiki-search {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wiki-search-actions {
  display: flex;
  gap: 8px;
}

.wiki-section-title {
  margin-top: 8px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--muted);
  text-transform: uppercase;
}

.wiki-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: min(40vh, 360px);
  overflow-y: auto;
}

.wiki-tag {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
}

.wiki-tag.active {
  border-color: rgba(var(--primary-rgb), 0.35);
  background: rgba(var(--primary-rgb), 0.08);
}

.wiki-clear {
  width: 100%;
  margin-top: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
}'''

    new_style = '''.wiki-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--fib-13, 13px);
  padding: var(--fib-13, 13px) var(--fib-21, 21px);
  margin-bottom: var(--fib-21, 21px);
}

.wiki-toolbar .n-input {
  flex: 1;
  min-width: 200px;
}

.wiki-search-actions {
  display: flex;
  gap: 8px;
}'''

    if old_style not in text:
        raise SystemExit('KnowledgeList style block not found')
    text = text.replace(old_style, new_style, 1)

    p.write_text(text, encoding='utf-8', newline='\n')
    print('ok KnowledgeList.vue')


def patch_admin_panel():
    p = ROOT / 'AdminPanel.vue'
    text = p.read_text(encoding='utf-8')

    old = '''import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { LinuxPrompt } from '@/components/shared'
import { ADMIN_MENU } from '@/config/adminMenu'

export default {
  name: 'AdminPanel',
  components: { LinuxPrompt },
  setup() {
    const route = useRoute()
    const collapsed = ref(false)
    const menuItems = ADMIN_MENU'''

    new = '''import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { LinuxPrompt } from '@/components/shared'
import { ADMIN_MENU } from '@/config/adminMenu'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'

export default {
  name: 'AdminPanel',
  components: { LinuxPrompt },
  setup() {
    const route = useRoute()
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_admin_sidebar_collapsed')
    const menuItems = ADMIN_MENU'''

    if old not in text:
        raise SystemExit('AdminPanel script block not found')
    text = text.replace(old, new, 1)

    old_toggle = '''    function toggleSidebar() {
      collapsed.value = !collapsed.value
    }

    return {'''

    new_toggle = '''    return {'''

    if old_toggle not in text:
        raise SystemExit('AdminPanel toggle block not found')
    text = text.replace(old_toggle, new_toggle, 1)

    p.write_text(text, encoding='utf-8', newline='\n')
    print('ok AdminPanel.vue')


def patch_home():
    p = ROOT / 'Home.vue'
    text = p.read_text(encoding='utf-8')

    old_root = '''<template>
  <div class="home-page home-wrap">
    <aside class="home-sidebar">
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
    </aside>

    <section class="home-main">'''

    new_root = '''<template>
  <div
    class="home-page home-wrap layout-with-sidebar lab-deck"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <aside class="home-sidebar sidebar-rail">
      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <h2 class="sidebar-title sidebar-rail-title">个人工作台</h2>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">HOME · DESK</p>
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

      <div class="sidebar-rail-nav">
        <div class="sidebar-group">
          <div class="group-label">快捷</div>
          <router-link to="/training" class="sidebar-item">
            <span class="item-code">TRN</span>
            <span class="item-title">训练靶场</span>
          </router-link>
          <router-link to="/games" class="sidebar-item">
            <span class="item-code">CTF</span>
            <span class="item-title">赛事中心</span>
          </router-link>
          <router-link to="/wiki" class="sidebar-item">
            <span class="item-code">DOC</span>
            <span class="item-title">知识库</span>
          </router-link>
          <router-link to="/bulletin" class="sidebar-item">
            <span class="item-code">BUL</span>
            <span class="item-title">平台公告</span>
          </router-link>
        </div>
      </div>
    </aside>

    <button
      type="button"
      class="sidebar-collapse-trigger"
      :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
      @click="toggleSidebar"
    >
      <span class="chevron" :class="{ 'is-collapsed': collapsed }">‹</span>
    </button>

    <main class="home-main sidebar-main">'''

    if old_root not in text:
        raise SystemExit('Home template block not found')
    text = text.replace(old_root, new_root, 1)

    old_close = '''    </section>
  </div>
</template>'''

    new_close = '''    </main>
  </div>
</template>'''

    if old_close not in text:
        raise SystemExit('Home close block not found')
    text = text.replace(old_close, new_close, 1)

    old_import = '''import CalendarFull from './CalendarFull.vue'
export default {
  name: 'Home',
  components: { NCard, CalendarFull },
  setup() {
  const router = useRouter()'''

    new_import = '''import CalendarFull from './CalendarFull.vue'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'
export default {
  name: 'Home',
  components: { NCard, CalendarFull },
  setup() {
  const router = useRouter()
  const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_home_sidebar_collapsed')'''

    if old_import not in text:
        raise SystemExit('Home import block not found')
    text = text.replace(old_import, new_import, 1)

    old_return = '''    return { heroImages, currentIndex, prev, next, go, recentGames, announcements, categories, goCategory,
      user, months, currentMonth, currentYear, monthDays, prevMonth, nextMonth,
      fcEvents, onEventClick, fetchAnnouncements, getAvatarUrl, selectedRegion, externalEventsCN, externalEventsGlobal, onSlideClick }'''

    new_return = '''    return { heroImages, currentIndex, prev, next, go, recentGames, announcements, categories, goCategory,
      user, months, currentMonth, currentYear, monthDays, prevMonth, nextMonth,
      fcEvents, onEventClick, fetchAnnouncements, getAvatarUrl, selectedRegion, externalEventsCN, externalEventsGlobal, onSlideClick,
      collapsed, toggleSidebar }'''

    if old_return not in text:
        raise SystemExit('Home return block not found')
    text = text.replace(old_return, new_return, 1)

    old_style = '''.home-sidebar-head {
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
.home-page-head {'''

    new_style = '''.home-page .profile-card {
  margin-bottom: var(--fib-8, 8px);
}
.home-page-head {'''

    if old_style not in text:
        raise SystemExit('Home style block not found')
    text = text.replace(old_style, new_style, 1)

    p.write_text(text, encoding='utf-8', newline='\n')
    print('ok Home.vue')


def patch_golden_ratio():
    p = Path(__file__).resolve().parent / 'src' / 'assets' / 'golden-ratio.css'
    text = p.read_text(encoding='utf-8')

    old_home = '''/* ── 个人工作台 /home ── */
.home-page.home-wrap {
  display: flex;
  gap: var(--space-gutter-lg);
  padding: var(--space-gutter-lg);
  align-items: flex-start;
  min-height: var(--workspace-height);
  box-sizing: border-box;
  width: 100%;
  max-width: none;
}

.home-page .home-sidebar {
  flex: 0 0 min(372px, 38.2%);
  width: min(372px, 38.2%);
  max-width: 372px;
  display: flex;
  flex-direction: column;
  gap: var(--space-gutter);
  padding: var(--fib-21);
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: 0 var(--radius-xl) var(--radius-xl) 0;
  background: var(--glass-sidebar-bg, var(--sidebar-bg));
  backdrop-filter: blur(6px);
  box-sizing: border-box;
}

.home-page .home-sidebar .sidebar-link {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  align-items: center;
  gap: var(--fib-8);
  padding: 10px 0;
  border: 1px solid transparent;
  border-radius: var(--card-radius);
  color: var(--muted);
  text-decoration: none;
  font-size: var(--text-sm);
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.home-page .home-sidebar .sidebar-link:hover {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}

.home-page .home-sidebar .sidebar-link:hover .link-code {
  color: var(--primary);
}

.home-page .home-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-gutter-lg);
}'''

    new_home = '''/* ── 个人工作台 /home（248px 侧栏，与 /training 一致）── */
.home-page.home-wrap {
  min-height: var(--workspace-height);
  box-sizing: border-box;
  width: 100%;
  max-width: none;
}

.home-page .home-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-gutter-lg);
}'''

    if old_home not in text:
        raise SystemExit('golden-ratio home block not found')
    text = text.replace(old_home, new_home, 1)

    old_media = '''@media (max-width: 899px) {
  .home-page.home-wrap {
    flex-direction: column;
  }

  .home-page .home-sidebar {
    width: 100%;
    max-width: none;
    flex: none;
    flex-direction: row;
    overflow-x: auto;
  }

  .home-page .home-bottom-grid {
    grid-template-columns: 1fr;
  }'''

    new_media = '''@media (max-width: 899px) {
  .home-page .home-bottom-grid {
    grid-template-columns: 1fr;
  }'''

    if old_media not in text:
        raise SystemExit('golden-ratio home media block not found')
    text = text.replace(old_media, new_media, 1)

    old_pad = '''.training-main:not(.training-main--game),
.bulletin-main,
.wiki-main,
.admin-main,
.game-admin__main {
  padding: var(--space-gutter-lg);
}

@media (min-width: 1200px) {
  .training-main:not(.training-main--game),
  .bulletin-main,
  .wiki-main,
  .admin-main {
    padding: var(--space-section) clamp(var(--fib-34), 4vw, var(--fib-55));
  }
}'''

    new_pad = '''.training-main:not(.training-main--game),
.bulletin-main,
.wiki-main,
.admin-main,
.home-main,
.game-admin__main {
  padding: var(--space-gutter-lg);
}

@media (min-width: 1200px) {
  .training-main:not(.training-main--game),
  .bulletin-main,
  .wiki-main,
  .admin-main,
  .home-main {
    padding: var(--space-section) clamp(var(--fib-34), 4vw, var(--fib-55));
  }
}'''

    if old_pad not in text:
        raise SystemExit('golden-ratio padding block not found')
    text = text.replace(old_pad, new_pad, 1)

    p.write_text(text, encoding='utf-8', newline='\n')
    print('ok golden-ratio.css')


if __name__ == '__main__':
    patch_knowledge_list()
    patch_admin_panel()
    patch_home()
    patch_golden_ratio()
