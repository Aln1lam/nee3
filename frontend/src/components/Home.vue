<template>
  <div
    class="home-page home-wrap layout-with-sidebar lab-deck"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <aside class="home-sidebar sidebar-rail">
      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <h2 class="sidebar-title sidebar-rail-title">个人工作台</h2>
          <span class="link-code chip-cut">HOM</span>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">HOME · DESK</p>
      </div>

      <div class="profile-flat">
        <div class="profile-top">
          <div class="avatar-small"><img :src="getAvatarUrl(user?.avatar)" alt="avatar"/></div>
          <div class="profile-meta">
            <div class="profile-name">{{ user?.nickname || '访客' }}</div>
            <span class="level-badge chip-cut">{{ dashStats.level }}</span>
          </div>
        </div>
        <div class="profile-actions">
          <button type="button" class="profile-action-btn" @click="$router.push('/myprofile')">个人主页</button>
          <button type="button" class="profile-action-btn" @click="$router.push('/games')">我的比赛</button>
        </div>
      </div>

      <div class="sidebar-rail-nav">
        <div class="sidebar-group">
          <div class="group-label">快捷</div>
          <router-link to="/training" class="sidebar-item">
            <span class="item-code chip-cut">TRN</span>
            <span class="item-title">训练靶场</span>
          </router-link>
          <router-link to="/games" class="sidebar-item">
            <span class="item-code chip-cut">CTF</span>
            <span class="item-title">赛事中心</span>
          </router-link>
          <router-link to="/wiki" class="sidebar-item">
            <span class="item-code chip-cut">DOC</span>
            <span class="item-title">知识库</span>
          </router-link>
          <router-link to="/bulletin" class="sidebar-item">
            <span class="item-code chip-cut">BUL</span>
            <span class="item-title">平台公告</span>
          </router-link>
        </div>
      </div>

      <div class="sidebar-rail-footer sidebar-footer">
        <div class="sidebar-footer-copy">
          © 2022-2026
          <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">东北电力大学</a>
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

    <main class="home-main sidebar-main">
      <section class="home-hero-hud hero-banner" :class="{ 'is-live': currentHero.live }" @click="onHeroCta">
        <div class="hero-hud-copy">
          <div class="hero-hud-eyebrow">
            <span class="link-code chip-cut">EVT</span>
            <span class="hero-hud-tag">FEATURED</span>
            <span class="hero-status-chip chip-cut" :class="currentHero.statusClass">
              [{{ currentHero.status }}] {{ currentHero.statusLabel }}
            </span>
          </div>
          <h3 class="hero-hud-title">{{ currentHero.title }}</h3>
          <p class="hero-hud-countdown">{{ currentHero.countdown }}</p>
          <button type="button" class="hero-cta chip-cut" @click.stop="onHeroCta">
            {{ currentHero.cta }}
            <kbd>↵</kbd>
          </button>
        </div>
        <div class="hero-hud-deco" aria-hidden="true"></div>
      </section>

      <div class="home-bottom-grid golden-dual-column main-grid-container">
        <div class="home-col home-col-main">
          <section class="agenda-panel home-surface">
            <div class="panel-head">
              <span class="link-code chip-cut">CAL</span>
              <span class="panel-head-title">近期赛事</span>
              <div class="agenda-region">
                <button
                  type="button"
                  class="region-chip chip-cut"
                  :class="{ active: selectedRegion === 'cn' }"
                  @click="selectedRegion = 'cn'"
                >国内</button>
                <button
                  type="button"
                  class="region-chip chip-cut"
                  :class="{ active: selectedRegion === 'global' }"
                  @click="selectedRegion = 'global'"
                >国际</button>
              </div>
            </div>
            <ul class="agenda-list">
              <li v-if="upcomingAgenda.length === 0" class="agenda-empty">
                <span class="agenda-empty-ico" aria-hidden="true">
                  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="8" y="10" width="32" height="30" rx="3" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M8 18h32" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M16 6v8M32 6v8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    <rect x="14" y="24" width="6" height="5" rx="1" stroke="currentColor" stroke-width="1.2" opacity="0.7"/>
                    <rect x="21" y="24" width="6" height="5" rx="1" stroke="currentColor" stroke-width="1.2" opacity="0.45"/>
                    <rect x="28" y="24" width="6" height="5" rx="1" stroke="currentColor" stroke-width="1.2" opacity="0.3"/>
                    <rect x="14" y="32" width="6" height="5" rx="1" stroke="currentColor" stroke-width="1.2" opacity="0.45"/>
                    <rect x="21" y="32" width="6" height="5" rx="1" stroke="currentColor" stroke-width="1.2" opacity="0.3"/>
                  </svg>
                </span>
                <span class="agenda-empty-text">近期暂无赛事</span>
              </li>
              <li
                v-for="ev in upcomingAgenda"
                :key="ev.id"
                class="agenda-item"
                role="button"
                tabindex="0"
                @click="onAgendaClick(ev)"
                @keydown.enter.prevent="onAgendaClick(ev)"
              >
                <span class="agenda-date-badge">{{ ev.day }} {{ ev.mon }}</span>
                <span class="agenda-track" aria-hidden="true">
                  <span class="agenda-node"></span>
                </span>
                <span class="agenda-body">
                  <span class="agenda-title">{{ ev.title }}</span>
                  <span class="agenda-meta">{{ ev.meta }}</span>
                </span>
              </li>
            </ul>
          </section>
        </div>

        <aside class="home-col home-col-side">
          <section class="side-console home-surface">
            <div class="side-console-tabs">
              <button
                type="button"
                class="side-tab chip-cut"
                :class="{ active: sideTab === 'bul' }"
                @click="sideTab = 'bul'"
              >
                <span class="link-code chip-cut">BUL</span>
                <span>平台公告</span>
              </button>
              <button
                type="button"
                class="side-tab chip-cut"
                :class="{ active: sideTab === 'sys' }"
                @click="openSysTab"
              >
                <span class="link-code chip-cut">SYS</span>
                <span>终端控制台</span>
              </button>
            </div>

            <div v-show="sideTab === 'bul'" class="side-console-pane bul-pane">
              <div v-if="announcements.length === 0" class="empty-hud empty-hud--compact">
                <p>暂无公告</p>
              </div>
              <ul v-else class="bulletin-list">
                <li v-for="a in announcements.slice(0, 6)" :key="a.id" class="bulletin-item">
                  <div class="bulletin-title">{{ a.title }}</div>
                  <div class="bulletin-content">{{ announcementPlain(a.content) }}</div>
                </li>
              </ul>
            </div>

            <div v-show="sideTab === 'sys'" class="side-console-pane sys-pane">
              <div class="term-window">
                <div class="term-titlebar">
                  <div class="term-dots" aria-hidden="true">
                    <span class="term-dot term-dot--close"></span>
                    <span class="term-dot term-dot--min"></span>
                    <span class="term-dot term-dot--max"></span>
                  </div>
                  <span class="term-title">player@neepu-ctf:~$</span>
                </div>
                <div ref="termBodyRef" class="term-body" @click="focusTermInput">
                  <pre class="term-pre">{{ termOutput }}</pre>
                  <form class="term-input-row" @submit.prevent="runTermCommand">
                    <span class="term-prompt">player@neepu:~$</span>
                    <input
                      ref="termInputRef"
                      v-model="termInput"
                      class="term-input"
                      type="text"
                      autocomplete="off"
                      spellcheck="false"
                      aria-label="终端命令输入"
                      @keydown.enter.prevent="runTermCommand"
                      @keydown.esc.prevent="termInput = ''"
                    />
                    <span class="term-caret" aria-hidden="true"></span>
                  </form>
                </div>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, inject, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { fetchSession, getUser } from '@/services/auth'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'
import { resolveUploadUrl } from '../utils/uploadUrl'
import { parseMarkdownSafe } from '../utils/markdown'
export default {
  name: 'Home',
  setup() {
  const router = useRouter()
  const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_home_sidebar_collapsed')
  const axios = inject('axios')
  const categories = ['快速开始','前言','环境设置','MISC | 杂项','Web | 网络攻防','Crypto | 密码学','Reverse | 逆向工程','Pwn | 二进制安全','AWD | 攻防模式','AI | 人工智能安全','blockchain | 区块链安全','附录']

  // --- external events (CN and Global) ---
  const externalEventsCN = ref([])
  const externalEventsGlobal = ref([])
  const selectedRegion = ref('global')  // 'cn' or 'global'
  const eventsMap = ref({}) // key: 'YYYY-MM-DD' -> [{title,...}]

  // 默认轮播图（后端无数据时使用）
  const defaultSlides = [
    { src: '/assets/index.svg', alt: 'banner', caption: 'Welcome to NEEPU CTF' },
    { src: '/assets/logo.svg', alt: 'banner2', caption: '社区与赛事' }
  ]
  const heroImages = ref([...defaultSlides])
  const currentIndex = ref(0)
  let carouselTimer = null
  const resolveUrl = (url) => {
    if (!url) return ''
    if (/^https?:\/\//i.test(url)) return url
    const base = axios && axios.defaults && axios.defaults.baseURL ? axios.defaults.baseURL.replace(/\/$/, '') : ''
    return (base ? base : '') + url
  }

  // 从后端加载轮播图
  async function fetchCarousel() {
    try {
      const res = await axios.get('/api/articles/carousel')
      if (res.data && res.data.length > 0) {
        heroImages.value = res.data.map(s => ({
          src: resolveUrl(s.image_url),
          alt: s.title || 'banner',
          caption: s.title || '',
          description: s.description || '',
          link: s.link_url
        }))
      }
    } catch (e) {
      console.log('使用默认轮播图')
    }
  }

  function startCarousel() {
    stopCarousel()
    carouselTimer = setInterval(() => { currentIndex.value = (currentIndex.value + 1) % heroImages.value.length }, 4000)
  }
  function stopCarousel() { if (carouselTimer) { clearInterval(carouselTimer); carouselTimer = null } }
  function prev() { currentIndex.value = (currentIndex.value - 1 + heroImages.value.length) % heroImages.value.length }
  function next() { currentIndex.value = (currentIndex.value + 1) % heroImages.value.length }
  function go(i) { currentIndex.value = i }

  // 点击轮播图跳转
  function onSlideClick(img) {
    if (img.link) {
      if (img.link.startsWith('http')) {
        window.open(img.link, '_blank')
      } else {
        router.push(img.link)
      }
    }
  }

  function goCategory(c) {
    // navigate to Knowledge and set category as query param
    router.push({ name: 'Knowledge', query: { cat: c } })
  }

    const recentGames = ref([
      { id: 1, title: 'NEEPU CTF - 校内赛', start: '2025-12-01', end: '2025-12-02' },
      { id: 2, title: 'NEEPU Open 2025', start: '2025-11-10', end: '2025-11-11' }
    ])
    const announcements = ref([])
    const statusOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
    // 获取公告（需要登录）
    async function fetchAnnouncements() {
      try {
        const token = localStorage.getItem('neepu_token')
        const headers = token ? { Authorization: `Bearer ${token}` } : undefined
        const res = await axios.get('/api/articles/announcements', { headers, withCredentials: true })
        const rows = res.data?.data || res.data?.items || res.data || []
        announcements.value = Array.isArray(rows) ? rows : []
      } catch (e) {
        console.error('加载公告失败:', e)
        announcements.value = []
      }
    }

    onMounted(() => {
      fetchFeaturedGame()
      fetchAnnouncements()
      try {
        if (typeof navigator !== 'undefined' && !navigator.onLine) {
          // offline — skip external fetch
        } else {
          fetchExternalEvents()
        }
      } catch (e) {
        fetchExternalEvents()
      }
      countdownTimer = setInterval(tickHeroCountdown, 1000)
      window.addEventListener('neepu_user_refreshed', refreshUserData)
    })
    onUnmounted(() => {
      if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
      stopCarousel()
      window.removeEventListener('neepu_user_refreshed', refreshUserData)
    })
    
    async function refreshUserData() {
      try {
        const u = await fetchSession({ force: true })
        user.value = u || getUser()
      } catch (e) {
        user.value = getUser()
      }
    }

    const user = ref(getUser())
    refreshUserData()

    const dashStats = computed(() => {
      const u = user.value || {}
      return {
        solved: u.solved_count ?? u.solves ?? u.challenge_solved ?? 0,
        score: u.score ?? u.points ?? 0,
        streak: u.streak ?? u.login_streak ?? 0,
        level: u.level || u.rank_title || 'ROOKIE'
      }
    })

    const featuredGame = ref(null)
    const heroCountdown = ref('')
    let countdownTimer = null

    function formatCountdown(ms) {
      if (ms <= 0) return '00:00:00'
      const total = Math.floor(ms / 1000)
      const d = Math.floor(total / 86400)
      const h = Math.floor((total % 86400) / 3600)
      const m = Math.floor((total % 3600) / 60)
      const s = total % 60
      const hh = String(h).padStart(2, '0')
      const mm = String(m).padStart(2, '0')
      const ss = String(s).padStart(2, '0')
      if (d > 0) return `${d}天 ${hh}:${mm}:${ss}`
      return `${hh}:${mm}:${ss}`
    }

    function tickHeroCountdown() {
      const g = featuredGame.value
      if (!g) {
        heroCountdown.value = '靶场 7×24 开放 · 随时开练'
        return
      }
      const now = Date.now()
      const start = g.start_time ? new Date(g.start_time).getTime() : NaN
      const end = g.end_time ? new Date(g.end_time).getTime() : NaN
      if (g.status === 'ongoing' && !isNaN(end)) {
        heroCountdown.value = `距结束 ${formatCountdown(end - now)}`
      } else if (g.status === 'not_started' && !isNaN(start)) {
        heroCountdown.value = `距开始 ${formatCountdown(start - now)}`
      } else if (g.status === 'archived') {
        heroCountdown.value = '赛事已结束 · 可转入训练复习'
      } else {
        heroCountdown.value = g.summary || g.description || '点击查看赛事详情'
      }
    }

    const platformGames = ref([])

    async function fetchFeaturedGame() {
      try {
        const res = await axios.get('/api/competitions/', { params: { exclude_training: true } })
        const rows = res.data?.data || res.data?.items || res.data || []
        const list = Array.isArray(rows) ? rows : []
        platformGames.value = list
        const ongoing = list.filter(g => g.status === 'ongoing')
        const upcoming = list
          .filter(g => g.status === 'not_started')
          .sort((a, b) => new Date(a.start_time || 0) - new Date(b.start_time || 0))
        featuredGame.value = ongoing[0] || upcoming[0] || list.find(g => g.status !== 'archived') || list[0] || null
      } catch (e) {
        platformGames.value = []
        featuredGame.value = null
      }
      tickHeroCountdown()
    }

    const currentHero = computed(() => {
      const g = featuredGame.value
      if (!g) {
        return {
          title: 'NEEPU 练习场',
          status: 'TRAIN',
          statusLabel: '随时开练',
          statusClass: 'is-train',
          countdown: heroCountdown.value,
          link: '/training',
          cta: '进入训练',
          poster: '/assets/logo.svg',
          live: false
        }
      }
      const live = g.status === 'ongoing'
      const soon = g.status === 'not_started'
      return {
        title: g.title || '赛事',
        status: live ? 'LIVE' : soon ? 'SOON' : 'EVT',
        statusLabel: live ? '正在进行' : soon ? '即将开始' : (g.status === 'archived' ? '已归档' : '赛事'),
        statusClass: live ? 'is-live' : soon ? 'is-soon' : 'is-evt',
        countdown: heroCountdown.value,
        link: `/games/${g.id}`,
        cta: live ? '立即参赛' : soon ? '查看详情' : '查看赛事',
        poster: g.poster_url ? resolveUrl(g.poster_url) : '/assets/logo.svg',
        live
      }
    })

    function onHeroCta() {
      const link = currentHero.value.link || '/training'
      if (String(link).startsWith('http')) window.open(link, '_blank')
      else router.push(link)
    }



    function getAvatarUrl(avatarPath) {
      if (!avatarPath) return '/assets/avatar-placeholder.png'
      return resolveUploadUrl(avatarPath) || '/assets/avatar-placeholder.png'
    }

    async function fetchExternalEvents(){
      try{
        // 通过后端代理获取数据，避免CORS问题
        const res = await axios.get('/api/external/events?region=both', { withCredentials: false })
        const data = res.data && res.data.data ? res.data.data : {}
        externalEventsCN.value = Array.isArray(data.cn) ? data.cn : []
        externalEventsGlobal.value = Array.isArray(data.global) ? data.global : []
        console.log('fetchExternalEvents: CN', externalEventsCN.value.length, 'Global', externalEventsGlobal.value.length)
        buildEventsMap()
        monthDays.value = buildMonthDays()
      }catch(e){
        console.warn('fetchExternalEvents failed', e)
      }
    }

    function rangeToStartEnd(rangeStr){
      try{
        if(!rangeStr) return {}
        const parts = rangeStr.split(' - ')
        const startRaw = (parts[0]||'').trim()
        let endRaw = (parts[1]||parts[0]||'').trim()
        endRaw = endRaw.replace(/UTC\+?\d+$/,'').trim()
        
        // 转换中文日期格式 "2026年1月30日 12:00" -> "2026-01-30 12:00"
        const cnToStd = (str) => str.replace(/(\d{4})年0?(\d{1,2})月0?(\d{1,2})日/g, (m, y, mo, d) => 
          `${y}-${String(mo).padStart(2,'0')}-${String(d).padStart(2,'0')}`)
        const startProc = cnToStd(startRaw)
        const endProc = cnToStd(endRaw)
        
        // 提取日期部分
        const extractDate = (s) => { const m = s.match(/(\d{4}-\d{2}-\d{2})/); return m ? m[1] : null }
        const startDate = extractDate(startProc)
        const endDate = extractDate(endProc)
        
        // 检测是否有时间信息
        const hasTime = /\d{2}:\d{2}/.test(startProc)
        
        if(startDate && endDate && !hasTime){
          // 纯日期，作为全天事件，结束日期+1天（FullCalendar要求）
          const ed = new Date(endDate + 'T00:00:00')
          ed.setDate(ed.getDate() + 1)
          const endExcl = `${ed.getFullYear()}-${String(ed.getMonth()+1).padStart(2,'0')}-${String(ed.getDate()).padStart(2,'0')}`
          return { start: startDate, end: endExcl, allDay: true }
        }
        
        // 带时间的事件
        const start = new Date(startProc + ' GMT+0800')
        const end = new Date(endProc + ' GMT+0800')
        if(isNaN(start)) return {}
        return { start: start.toISOString(), end: isNaN(end) ? start.toISOString() : end.toISOString(), allDay: false }
      }catch(e){ return {} }
    }

    // 当前选择区域的赛事
    const activeExternalEvents = computed(() => 
      selectedRegion.value === 'cn' ? externalEventsCN.value : externalEventsGlobal.value
    )
    
    const fcEvents = computed(() => {
      const now = new Date()
      const fromExternal = (activeExternalEvents.value || []).map((ev, idx) => {
        // 支持国内格式(name, comp_time_start/end)和国外格式(比赛名称, 比赛时间)
        const title = ev['比赛名称'] || ev['name'] || ev['title'] || '比赛'
        let range = ev['比赛时间'] || ev['time'] || ''
        if (!range && ev['comp_time_start'] && ev['comp_time_end']) {
          range = `${ev['comp_time_start']} - ${ev['comp_time_end']}`
        }
        const se = rangeToStartEnd(range)
        const url = ev['比赛链接'] || ev['link'] || ev['url'] || null
        const endDate = se && se.end ? new Date(se.end) : null
        const isPast = endDate ? (endDate.getTime() < now.getTime()) : false
        const bgColor = selectedRegion.value === 'cn' ? '#ff6b6b' : '#4c6ef5'
        return { 
          id: ev.id || `ext-${idx}`, 
          title, 
          start: se.start, 
          end: se.end, 
          allDay: se.allDay || false, 
          url, 
          classNames: isPast ? ['fc-past'] : ['fc-coming'],
          backgroundColor: isPast ? '#ccc' : bgColor,
          borderColor: 'transparent'
        }
      }).filter(e => e.start)
      const fromRecent = (recentGames.value || []).map(g => {
        const end = g.end || g.start
        const isPast = end ? (new Date(end).getTime() < now.getTime()) : false
        return { id: g.id || `rg-${g.title}`, title: g.title, start: g.start, end: g.end || g.start, allDay: true, classNames: isPast ? ['fc-past'] : ['fc-coming'] }
      })
      return [...fromExternal, ...fromRecent]
    })

    function onEventClick(ev){
      try{
        if(ev && ev.url) window.open(ev.url, '_blank')
        else router.push({ name: 'event-detail', params: { id: ev.id } })
      }catch(e){ console.warn('onEventClick error', e) }
    }

    function parseRangeToDates(rangeStr){
      // expected format: "YYYY-MM-DD HH:mm:ss - YYYY-MM-DD HH:mm:ss UTC+8"
      try{
        const parts = rangeStr.split(' - ')
        if(parts.length<2) return []
        const startRaw = parts[0].trim()
        let endRaw = parts[1].trim()
        // ensure GMT+0800 suffix for reliable parsing
        const start = new Date(startRaw + ' GMT+0800')
        // remove trailing timezone label if present on endRaw like 'UTC+8'
        endRaw = endRaw.replace(/UTC\+?\d+$/,'').trim()
        const end = new Date(endRaw + ' GMT+0800')
        if(isNaN(start) || isNaN(end)) return []
        const dates = []
        const cur = new Date(start.getFullYear(), start.getMonth(), start.getDate())
        const last = new Date(end.getFullYear(), end.getMonth(), end.getDate())
        while(cur <= last){
          const y = cur.getFullYear(); const m = cur.getMonth()+1; const d = cur.getDate()
          const key = `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`
          dates.push(key)
          cur.setDate(cur.getDate()+1)
        }
        return dates
      }catch(e){ return [] }
    }

    function buildEventsMap(){
      const map = {}
      const allEvents = [...externalEventsCN.value, ...externalEventsGlobal.value]
      for(const ev of allEvents){
        const title = ev['比赛名称'] || ev['name'] || ev['title'] || '比赛'
        let range = ev['比赛时间'] || ev['time'] || ''
        if (!range && ev['comp_time_start'] && ev['comp_time_end']) {
          range = `${ev['comp_time_start']} - ${ev['comp_time_end']}`
        }
        const dates = parseRangeToDates(range)
        for(const d of dates){
          map[d] = map[d] || []
          map[d].push({ title, raw: ev })
        }
      }
      eventsMap.value = map
    }

    // --- calendar ---
    const months = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月']
    const today = new Date()
    const currentMonth = ref(today.getMonth())
    const currentYear = ref(today.getFullYear())

    function daysInMonth(y,m){ return new Date(y,m+1,0).getDate() }
    function firstWeekday(y,m){ const d=new Date(y,m,1).getDay(); return d===0?7:d } // Monday=1..Sunday=7

    function buildMonthDays(){
      const total = daysInMonth(currentYear.value, currentMonth.value)
      const first = firstWeekday(currentYear.value, currentMonth.value)
      const arr = []
      // prepend blanks for alignment (we keep grid simple and just leave empty days)
      for(let i=1;i<first;i++) arr.push({ date: '', isToday:false, hasEvent:false })
      // events map from recentGames start dates
      const eventSet = new Set(recentGames.value.map(g => g.start))
      for(let d=1; d<=total; d++){
        const iso = new Date(currentYear.value, currentMonth.value, d).toISOString().slice(0,10)
          arr.push({ date: d, isToday: currentYear.value===today.getFullYear() && currentMonth.value===today.getMonth() && d===today.getDate(), hasEvent: eventSet.has(iso) || Boolean(eventsMap.value[iso] && eventsMap.value[iso].length), events: eventsMap.value[iso] ? [...eventsMap.value[iso]] : [] })
      }
      return arr
    }

    const monthDays = ref(buildMonthDays())
    function prevMonth(){ if (currentMonth.value===0){ currentMonth.value=11; currentYear.value-- } else currentMonth.value-- ; monthDays.value = buildMonthDays() }
    function nextMonth(){ if (currentMonth.value===11){ currentMonth.value=0; currentYear.value++ } else currentMonth.value++ ; monthDays.value = buildMonthDays() }

    const MONTH_SHORT = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

    const upcomingAgenda = computed(() => {
      const startBound = new Date()
      startBound.setHours(0, 0, 0, 0)
      const endBound = new Date(startBound)
      endBound.setDate(endBound.getDate() + 14)
      const items = []
      for (const e of (fcEvents.value || [])) {
        if (!e || !e.start) continue
        const s = new Date(e.start)
        if (isNaN(s.getTime())) continue
        const en = e.end ? new Date(e.end) : s
        // 与 [today, today+14] 有交集即可
        if (en.getTime() < startBound.getTime() || s.getTime() > endBound.getTime()) continue
        const show = s.getTime() < startBound.getTime() ? startBound : s
        const hh = String(show.getHours()).padStart(2, '0')
        const mm = String(show.getMinutes()).padStart(2, '0')
        const hasClock = !(e.allDay) && (show.getHours() || show.getMinutes())
        items.push({
          id: e.id,
          title: e.title,
          url: e.url || null,
          day: String(show.getDate()).padStart(2, '0'),
          mon: MONTH_SHORT[show.getMonth()],
          meta: hasClock ? `${hh}:${mm} · ${selectedRegion.value === 'cn' ? '国内' : '国际'}` : (selectedRegion.value === 'cn' ? '国内赛' : '国际赛'),
          start: show
        })
      }
      items.sort((a, b) => a.start - b.start)
      return items.slice(0, 6)
    })


    const sideTab = ref('bul')
    const termInput = ref('')
    const termInputRef = ref(null)
    const termBodyRef = ref(null)
    const termHistory = ref([])
    const TERM_PROMPT = 'player@neepu:~$'
    const NEOFETCH_BANNER = [
      '  _  _ _____ _____ _____  _   _ ',
      ' | \\| | ____| ____|  _ \\| | | |',
      ' | .` |  _| |  _| | |_) | | | |',
      ' |_|\\_|_|___|____|_|____/ \\___/',
      ' ------------------------------',
      ' OS: NEEPU-CTF Linux x86_64 (simulated)',
      ' Kernel: 6.1.0-ctf-core',
      ' Shell: /bin/zsh (Active · sandbox)',
      ' System Status: [ALL SYSTEMS OPERATIONAL]',
      ' CPU: [██████░░░░] 62%   RAM: 4.2G/16G',
      ' Uptime: 12d 4h 20m',
      '',
    ]
    const FAKE_FS = {
      '~': ['challenges/', 'games/', 'training/', 'bulletin/', 'readme.txt'],
      '~/challenges': ['web/', 'pwn/', 'reverse/', 'crypto/'],
      '~/games': ['ongoing/', 'archive/'],
      '~/training': ['lab-01', 'lab-02', 'lab-03'],
      '~/bulletin': ['welcome.md', 'maintenance.md'],
    }
    const FORTUNES = [
      'The quieter you become, the more you are able to hear. — Kali',
      'Segmentation fault (core dumped) — but only in your dreams.',
      'flag{try_harder} is never on the filesystem. Keep hacking.',
      'sudo make me a sandwich — permission denied (simulated).',
    ]
    const termLines = ref([...NEOFETCH_BANNER])
    const termOutput = computed(() => termLines.value.join(String.fromCharCode(10)))
    const termCwd = ref('~')

    function resetTerminal() {
      termLines.value = [...NEOFETCH_BANNER]
      termCwd.value = '~'
    }

    function scrollTermToBottom() {
      nextTick(() => {
        const el = termBodyRef.value
        if (el) el.scrollTop = el.scrollHeight
      })
    }

    function focusTermInput() {
      nextTick(() => {
        try { termInputRef.value && termInputRef.value.focus() } catch (e) { /* ignore */ }
      })
    }

    function openSysTab() {
      sideTab.value = 'sys'
      focusTermInput()
      scrollTermToBottom()
    }

    function termPrint(...lines) {
      for (const line of lines) termLines.value.push(String(line))
    }

    /** 拒绝壳层元字符；仅允许白名单命令本地回显 / 站内跳转 */
    function sanitizeTermRaw(raw) {
      const s = String(raw || '').trim()
      if (!s) return { ok: false, reason: 'empty' }
      if (s.length > 120) return { ok: false, reason: 'too long (max 120)' }
      // 禁止管道、重定向、命令替换、路径穿越意图等
      if (/[;|&`$<>\\\n\r]/.test(s)) return { ok: false, reason: 'metacharacters blocked' }
      if (/\.\.|\/etc|\/proc|\/sys|\/var|\/root|\/home\//i.test(s)) {
        return { ok: false, reason: 'path not allowed in sandbox' }
      }
      const parts = s.split(/\s+/).filter(Boolean)
      const cmd = (parts[0] || '').toLowerCase()
      const args = parts.slice(1).map((a) => a.slice(0, 64))
      return { ok: true, cmd, args, display: s }
    }

    function fmtNow() {
      try {
        return new Date().toLocaleString('zh-CN', { hour12: false })
      } catch (e) {
        return new Date().toISOString()
      }
    }

    function cowsayBox(msg) {
      const text = String(msg || 'moo').slice(0, 40)
      const bar = '-'.repeat(text.length + 2)
      return [
        ` ${bar}`,
        `< ${text} >`,
        ` ${bar}`,
        '        \\   ^__^',
        '         \\  (oo)\\_______',
        '            (__)\\       )\\/\\',
        '                ||----w |',
        '                ||     ||',
      ]
    }

    function runTermCommand() {
      const parsed = sanitizeTermRaw(termInput.value)
      termInput.value = ''
      if (!parsed.ok) {
        if (parsed.reason === 'empty') return
        termPrint(`${TERM_PROMPT} (blocked)`)
        termPrint(`sandbox: ${parsed.reason}`)
        scrollTermToBottom()
        return
      }

      const { cmd, args, display } = parsed
      termHistory.value.push(display)
      if (termHistory.value.length > 50) termHistory.value.shift()
      termPrint(`${TERM_PROMPT} ${display}`)

      // —— 白名单调度（无 eval / 无后端 exec）——
      if (cmd === 'clear') {
        termLines.value = []
      } else if (cmd === 'help') {
        termPrint('NEEPU SYS Console · simulated sandbox (no real shell / no RCE)')
        termPrint('Local: help status clear neofetch whoami id hostname uname uptime')
        termPrint('       pwd ls date echo history fortune cowsay')
        termPrint('CTF:   games ctf train pwn score rank bulletin news flag')
        termPrint('Fake:  ssh docker')
      } else if (cmd === 'status') {
        termPrint('Node: Normal | API: 99.9% | Docker: Ready')
        termPrint('System Status: [ALL SYSTEMS OPERATIONAL]')
        termPrint('(simulated telemetry · read-only)')
      } else if (cmd === 'neofetch') {
        termPrint(...NEOFETCH_BANNER)
      } else if (cmd === 'whoami' || cmd === 'id') {
        const name = user.value?.nickname || user.value?.username || 'player'
        if (cmd === 'whoami') termPrint(name)
        else termPrint(`uid=1000(${name}) gid=1000(ctf) groups=1000(ctf),999(docker-sim)`)
      } else if (cmd === 'hostname') {
        termPrint('neepu-ctf-node-01')
      } else if (cmd === 'uname') {
        termPrint('Linux neepu-ctf-node-01 6.1.0-ctf-core #1 SMP x86_64 GNU/Linux')
      } else if (cmd === 'uptime') {
        termPrint(` ${fmtNow()} up 12 days,  4:20,  1 user,  load average: 0.42, 0.38, 0.31`)
      } else if (cmd === 'date') {
        termPrint(fmtNow())
      } else if (cmd === 'pwd') {
        termPrint(termCwd.value === '~' ? '/home/player' : `/home/player/${termCwd.value.replace(/^~\//, '')}`)
      } else if (cmd === 'ls') {
        const target = args[0] ? (args[0].startsWith('~/') || args[0] === '~' ? args[0] : `${termCwd.value === '~' ? '~' : termCwd.value}/${args[0]}`.replace(/\/+/g, '/')) : termCwd.value
        const key = target.replace(/\/$/, '') || '~'
        const entries = FAKE_FS[key] || FAKE_FS['~']
        if (!FAKE_FS[key] && args[0]) termPrint(`ls: cannot access '${args[0]}': No such file (sandbox)`)
        else termPrint(entries.join('  '))
      } else if (cmd === 'echo') {
        // 仅原样拼接参数文本，不做变量展开
        termPrint(args.join(' ').slice(0, 100) || '')
      } else if (cmd === 'history') {
        if (!termHistory.value.length) termPrint('  (empty)')
        else termHistory.value.slice(-20).forEach((h, i) => termPrint(`  ${i + 1}  ${h}`))
      } else if (cmd === 'fortune') {
        termPrint(FORTUNES[Math.floor(Math.random() * FORTUNES.length)])
      } else if (cmd === 'cowsay') {
        termPrint(...cowsayBox(args.join(' ') || 'NEEPU CTF'))
      } else if (cmd === 'games' || cmd === 'ctf') {
        const list = (platformGames.value || []).filter((g) => g && g.status !== 'archived').slice(0, 6)
        if (!list.length) {
          termPrint('No competitions loaded. Opening /games …')
        } else {
          termPrint('ID   STATUS       TITLE')
          list.forEach((g) => {
            const st = String(g.status || '?').padEnd(12)
            termPrint(`${String(g.id).padEnd(4)} ${st} ${g.title || 'untitled'}`)
          })
          termPrint('hint: use `games go` to open /games (whitelist route)')
        }
        if (args[0] === 'go' || args[0] === 'open') router.push('/games')
      } else if (cmd === 'train' || cmd === 'pwn') {
        termPrint('Opening training sandbox → /training')
        router.push('/training')
      } else if (cmd === 'score' || cmd === 'rank') {
        const s = dashStats.value || {}
        termPrint(`Player: ${user.value?.nickname || user.value?.username || 'player'}`)
        termPrint(`Level : ${s.level || 'ROOKIE'}`)
        termPrint(`Note  : CTF scores are per-game. Global 0 means nothing here.`)
        termPrint(`Tip   : open a live game for real scoreboard.`)
        if (featuredGame.value?.id) termPrint(`Live  : ${featuredGame.value.title} (#${featuredGame.value.id})`)
      } else if (cmd === 'bulletin' || cmd === 'news') {
        const rows = (announcements.value || []).slice(0, 2)
        if (!rows.length) termPrint('(no bulletins)')
        else rows.forEach((a, i) => {
          termPrint(`[${i + 1}] ${a.title || 'untitled'}`)
          termPrint(`    ${announcementPlain(a.content) || '…'}`)
        })
      } else if (cmd === 'flag') {
        termPrint('bash: flag: Permission denied')
        termPrint('hint: real flags live inside challenges, not this toy shell.')
      } else if (cmd === 'ssh') {
        termPrint('Pseudo-tty: connecting to arena.neepu.local …')
        termPrint('Permission denied (publickey,simulated).')
      } else if (cmd === 'docker') {
        if (args[0] === 'ps' || !args.length) {
          termPrint('CONTAINER ID   IMAGE            STATUS          NAMES')
          termPrint('a1b2c3d4e5f6   neepu/chal:web   Up 2 hours      web-01')
          termPrint('f6e5d4c3b2a1   neepu/chal:pwn   Up 2 hours      pwn-01')
          termPrint('(read-only fake table · no docker socket)')
        } else {
          termPrint(`docker: '${args[0]}' is not allowed in sandbox`)
        }
      } else {
        termPrint(`zsh: command not found: ${cmd}`)
        termPrint("Type 'help' for whitelist commands.")
      }
      scrollTermToBottom()
    }

    function announcementPlain(md) {
      if (!md) return ''
      try {
        const html = parseMarkdownSafe(String(md))
        const text = String(html)
          .replace(/<br\s*\/?>/gi, ' ')
          .replace(/<\/p>/gi, ' ')
          .replace(/<[^>]+>/g, '')
          .replace(/&nbsp;/g, ' ')
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/\s+/g, ' ')
          .trim()
        return text.length > 48 ? text.slice(0, 48) + '…' : text
      } catch (e) {
        const raw = String(md).replace(/[*_`#>\[\]()!-]/g, ' ').replace(/\s+/g, ' ').trim()
        return raw.length > 48 ? raw.slice(0, 48) + '…' : raw
      }
    }

    function onAgendaClick(ev) {
      try {
        if (ev && ev.url) window.open(ev.url, '_blank')
        else if (ev && ev.id) router.push({ name: 'event-detail', params: { id: ev.id } })
        else router.push('/games')
      } catch (e) {
        router.push('/games')
      }
    }

    return { heroImages, currentIndex, prev, next, go, recentGames, announcements, categories, goCategory,
      user, months, currentMonth, currentYear, monthDays, prevMonth, nextMonth,
      fcEvents, onEventClick, upcomingAgenda, onAgendaClick, announcementPlain,
      fetchAnnouncements, getAvatarUrl, selectedRegion, externalEventsCN, externalEventsGlobal, onSlideClick,
      collapsed, toggleSidebar, statusOnline, dashStats, currentHero, onHeroCta, sideTab, openSysTab, termLines, termOutput, termInput, termInputRef, termBodyRef, runTermCommand, focusTermInput }
  }
}
</script>

<style scoped>
/* HUD 质感 / 切角 / hover — 布局见 golden-ratio.css */

/* Tag 类（link-code / item-code / level-badge）走全局清透 Chip，禁止 clip-path */
.home-page .link-code,
.home-page .item-code,
.home-page .level-badge {
  clip-path: none !important;
  border-radius: 3px !important;
  text-shadow: none !important;
  box-shadow: none !important;
}

/* 仅非 Tag 的 HUD 控件保留微切角 */
.home-page .hero-cta,
.home-page .region-chip,
.home-page .hero-status-chip,
.home-page .side-tab {
  border-radius: 0 !important;
  clip-path: polygon(
    4px 0,
    100% 0,
    100% calc(100% - 4px),
    calc(100% - 4px) 100%,
    0 100%,
    0 4px
  );
}

.home-page .home-surface {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
  transition: border-color 0.2s, box-shadow 0.2s;
}
html .home-page .home-surface {
  background: #131722;
  border-color: rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}
.home-page .home-surface:hover {
  border-color: rgba(var(--primary-rgb), 0.42);
  box-shadow:
    var(--gradient-card-shadow),
    0 0 0 1px rgba(var(--primary-rgb), 0.2);
}

/* 主面板顶栏亮条 + 块面阴影（避开全局 [class*=card]） */
.home-page .agenda-panel,
.home-page .side-console {
  position: relative;
  overflow: hidden;
  box-shadow: var(--gradient-card-shadow) !important;
}
.home-page .agenda-panel::before,
.home-page .side-console::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 2px;
  z-index: 3;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    rgb(var(--primary-rgb)) 0%,
    rgba(94, 217, 168, 0.85) 42%,
    rgba(244, 114, 182, 0.75) 100%
  );
  opacity: 0.9;
}

.status-light {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--muted);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.12);
  flex-shrink: 0;
}
.status-light.online { background: var(--primary); }

.profile-flat {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 6px 12px;
  background: transparent;
  border: 0;
  box-shadow: none;
}
.profile-top {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.avatar-small {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}
.avatar-small img { width: 100%; height: 100%; object-fit: cover; display: block; }
.profile-meta {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}
.profile-name {
  font-weight: 600;
  color: var(--text);
  font-size: 13px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  font-family: var(--font-ui);
}
.level-badge {
  flex-shrink: 0;
  /* 视觉由全局 Chip 标准接管 */
}
.profile-actions {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 6px;
  width: 100%;
}
.profile-action-btn {
  flex: 1 1 0;
  min-width: 0;
  margin: 0;
  padding: 6px 0 !important;
  min-height: 0 !important;
  height: auto !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center;
  white-space: nowrap;
  font-size: 12px !important;
  font-weight: 500;
  font-family: var(--font-ui);
  color: var(--text) !important;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 6px !important;
  cursor: pointer;
  box-shadow: none !important;
  transform: none !important;
}
.profile-action-btn:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.18) !important;
  color: #fff !important;
  transform: none !important;
}

/* ── 紧凑页头 ── */
.home-page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.home-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.home-head-titles { min-width: 0; }
.home-page .matrix-page-prompt {
  margin: 0;
  font-size: 11px;
  line-height: 1.2;
}
.home-page .matrix-page-title {
  margin: 0;
  font-size: 16px !important;
  font-weight: 600 !important;
  line-height: 1.35;
  color: var(--text-main, var(--text)) !important;
  letter-spacing: -0.01em;
  font-family: var(--font-ui) !important;
}

/* ── Hero：清爽暗色微渐变 + 左侧薄荷绿微晕 ── */
.home-hero-hud.hero-banner,
.home-hero-hud {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1.618fr) minmax(120px, 1fr);
  align-items: center;
  height: 148px;
  max-height: 160px;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: var(--card-radius);
  background: linear-gradient(135deg, rgba(35, 40, 56, 0.7) 0%, rgba(20, 24, 35, 0.9) 100%) !important;
  border: 1px solid rgba(94, 217, 168, 0.2) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
  color: #e8ecf4;
}
/* 左侧薄荷绿微光晕：烘托标题焦点 */
.home-hero-hud.hero-banner::before,
.home-hero-hud::before {
  content: '';
  position: absolute;
  top: -50px;
  left: -50px;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(94, 217, 168, 0.12) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}
.home-hero-hud:hover {
  border-color: rgba(94, 217, 168, 0.38) !important;
  box-shadow: 0 10px 36px rgba(0, 0, 0, 0.36) !important;
}
.hero-hud-copy {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.hero-hud-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
}
.hero-hud-tag {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: rgba(232, 236, 244, 0.55);
  font-family: var(--font-mono);
}
.hero-hud-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-ui);
  color: #f4f7fb !important;
}
.hero-hud-countdown {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: rgba(232, 236, 244, 0.78) !important;
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  max-width: 46ch;
}
.hero-status-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
  letter-spacing: 0.06em;
  color: #5ED9A8;
  background: rgba(94, 217, 168, 0.12);
  border: 1px solid rgba(94, 217, 168, 0.35);
}
.hero-status-chip.is-soon {
  color: #f0c674;
  background: rgba(240, 198, 116, 0.12);
  border-color: rgba(240, 198, 116, 0.35);
}
.hero-status-chip.is-train,
.hero-status-chip.is-evt {
  color: rgba(232, 236, 244, 0.75);
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
}
.home-hero-hud.is-live {
  border-color: rgba(94, 217, 168, 0.32) !important;
}
.hero-cta {
  align-self: flex-start;
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 11px;
  border: 1px solid rgba(94, 217, 168, 0.5);
  background: rgba(94, 217, 168, 0.16);
  color: #5ed9a8;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-ui);
  cursor: pointer;
}
.hero-cta kbd { font-size: 10px; font-family: var(--font-mono); opacity: 0.85; }
.hero-cta:hover { background: rgba(94, 217, 168, 0.26); }
.hero-hud-deco {
  position: relative;
  z-index: 1;
  height: 100%;
  min-height: 0;
  pointer-events: none;
  /* 右侧纯净暗色通透区，无 LIVE 水印 / 伪图案 */
  background: transparent;
}
.hero-deco-logo,
.hero-deco-mark,
.hero-hud-mesh,
.hero-hud-stripe,
.hero-hud-dots {
  display: none !important;
}

/* ── 面板头 / CAL + BUL ── */
.panel-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.panel-head-title {
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-ui);
  color: var(--text);
}
.panel-head-meta {
  margin-left: auto;
  font-size: 9px;
  letter-spacing: 0.14em;
  color: var(--muted);
  font-family: var(--font-mono);
}
.side-console {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  height: 100%;
  min-height: 0;
}
.side-console-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}
.side-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 9px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  font-size: 11px;
  font-family: var(--font-ui);
  cursor: pointer;
}
.side-tab.active {
  color: var(--text);
  background: rgba(94, 217, 168, 0.1);
  border-color: rgba(94, 217, 168, 0.28);
}
.side-console-pane {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.bul-pane {
  padding: 10px 12px;
  overflow-y: auto;
  overflow-x: hidden;
}
.sys-pane {
  padding: 0;
  background: #090B10;
}

/* ── 近期赛事 Timeline：撑满左栏，优雅行距 ── */
.agenda-panel {
  min-height: 0;
  height: 100%;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 14px 16px;
}
.agenda-region {
  margin-left: auto;
  display: inline-flex;
  gap: 4px;
}
.region-chip {
  padding: 2px 7px !important;
  min-height: 0 !important;
  height: auto !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: transparent !important;
  color: var(--muted) !important;
  font-size: 10px !important;
  font-family: var(--font-ui);
  cursor: pointer;
  border-radius: 0 !important;
  box-shadow: none !important;
  transform: none !important;
}
.region-chip.active {
  color: var(--primary) !important;
  background: rgba(var(--primary-rgb), 0.12) !important;
  border-color: rgba(var(--primary-rgb), 0.32) !important;
  font-weight: 700;
}
.agenda-list {
  list-style: none;
  margin: 0;
  padding: 4px 0 0;
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  gap: 4px;
  justify-content: space-evenly;
  overflow: hidden; /* 无局部滚动条 */
}
.agenda-empty {
  list-style: none;
  flex: 1 1 auto;
  min-height: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px 12px;
  text-align: center;
}
.agenda-empty-ico {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: rgba(94, 217, 168, 0.35);
  opacity: 0.85;
}
.agenda-empty-ico svg {
  width: 40px;
  height: 40px;
  display: block;
}
.agenda-empty-text {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  font-family: var(--font-ui);
  letter-spacing: 0.04em;
}
.agenda-item {
  position: static !important;
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 10px;
  width: 100%;
  margin: 0;
  padding: 10px 6px;
  border: 0 !important;
  border-radius: 6px;
  background: transparent !important;
  text-align: left;
  cursor: pointer;
  color: inherit;
  box-sizing: border-box;
  min-height: 0 !important;
  height: auto !important;
  transform: none !important;
  box-shadow: none !important;
  outline: none !important;
}
.agenda-item:last-child { margin-bottom: 0; }
.agenda-item:focus,
.agenda-item:focus-visible,
.agenda-item:active,
.agenda-item:focus-within {
  background: transparent !important;
  outline: none !important;
  box-shadow: none !important;
}
.agenda-item:hover {
  background: rgba(255, 255, 255, 0.04) !important;
}
.agenda-date-badge {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 58px;
  padding: 4px 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--text);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  white-space: nowrap;
}
/* 时间轴贯穿线 + 发光节点 */
.agenda-track {
  position: relative;
  flex: 0 0 14px;
  align-self: stretch;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.agenda-track::before {
  content: "";
  position: absolute;
  left: 50%;
  top: -10px;
  bottom: -10px;
  width: 0;
  border-left: 2px dashed rgba(45, 181, 138, 0.2);
  transform: translateX(-50%);
}
.agenda-item:first-child .agenda-track::before { top: 50%; }
.agenda-item:last-child .agenda-track::before { bottom: 50%; }
.agenda-node {
  position: relative;
  z-index: 1;
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  background: rgb(var(--primary-rgb));
  transform: rotate(45deg);
  box-shadow: 0 0 0 2px rgba(94, 217, 168, 0.18), 0 0 8px rgba(45, 181, 138, 0.55);
}
.agenda-item:hover .agenda-node {
  box-shadow: 0 0 0 2px rgba(94, 217, 168, 0.28), 0 0 10px rgba(45, 181, 138, 0.7);
}
.agenda-body {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 2px;
  position: static !important;
}
.agenda-title {
  display: block;
  width: 100%;
  font-size: 12px;
  font-weight: 650;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.25;
  position: static !important;
}
.agenda-meta {
  display: block;
  font-size: 10px;
  color: var(--muted);
  font-family: var(--font-mono);
  line-height: 1.2;
  position: static !important;
}

/* ── 右侧统一 Card Stack ── */
.side-stack {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  padding: 0 !important;
}
.side-stack-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 8px;
  background: rgba(var(--primary-rgb), 0.04);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
html .side-stack-head {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}
.side-stack-label {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--primary);
  background: rgba(var(--primary-rgb), 0.1);
  border: 1px solid rgba(var(--primary-rgb), 0.22);
  font-family: var(--font-mono);
}
.side-tab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  font-size: 11px;
  font-family: var(--font-ui);
  cursor: pointer;
}
.side-tab.active {
  color: var(--text);
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.3);
}
.side-stack-body {
  position: relative;
  flex: 1;
  min-height: 0;
  padding: 8px 10px;
  overflow: auto;
}
.empty-hud {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 72px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  isolation: isolate;
}
.empty-hud--compact {
  min-height: 56px;
  padding: 8px 0;
}
.empty-hud--compact::before {
  display: none;
}
.empty-hud::before {
  content: '';
  position: absolute;
  inset: 4px;
  z-index: -1;
  border-radius: 6px;
  opacity: 0.7;
  background-image:
    radial-gradient(rgba(var(--primary-rgb), 0.28) 0.65px, transparent 0.75px),
    linear-gradient(rgba(0, 0, 0, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.025) 1px, transparent 1px);
  background-size: 10px 10px, 100% 12px, 12px 100%;
}
.empty-hint { font-size: 11px; margin-top: 3px; opacity: 0.85; }

.bulletin-list,
.rank-list { list-style: none; padding: 0; margin: 0; }
/* BUL：高质感单列纵向 Feed */
.home-page .side-console .bulletin-list {
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
  height: auto !important;
  overflow: auto;
  padding: 12px 14px 14px !important;
  margin: 0 !important;
  list-style: none !important;
  align-content: start;
}
.home-page .side-console .bulletin-item {
  position: relative;
  width: 100% !important;
  height: auto !important;
  min-height: 0 !important;
  flex: none !important;
  margin: 0 !important;
  padding: 12px 16px !important;
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
  border-radius: 6px !important;
  box-shadow: none !important;
  transform: none !important;
  display: block !important;
}
.home-page .side-console .bulletin-item::after {
  display: none !important;
  content: none !important;
}
.home-page .side-console .bulletin-item:hover {
  border-color: rgba(94, 217, 168, 0.22) !important;
  background: rgba(255, 255, 255, 0.035) !important;
  box-shadow: none !important;
  transform: none !important;
}
.home-page .side-console .bulletin-title {
  font-size: 13px;
  font-weight: 600;
  color: #E2E8F0;
  margin: 0 0 6px !important;
  line-height: 1.35;
  font-family: var(--font-ui);
}
.home-page .side-console .bulletin-content {
  font-size: 12px;
  color: #94A3B8;
  line-height: 1.6;
  margin: 0 !important;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── System Status 极客微部件 ── */
.term-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: #090B10;
}
.term-titlebar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  background: #11151d;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.term-dots {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.term-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.term-dot--close { background: #ff5f57; }
.term-dot--min { background: #febc2e; }
.term-dot--max { background: #28c840; }
.term-title {
  font-family: var(--font-mono, "JetBrains Mono", monospace);
  font-size: 11px;
  color: rgba(148, 163, 184, 0.85);
  letter-spacing: 0.02em;
}
.term-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 12px 10px;
  cursor: text;
}
.term-pre {
  margin: 0 0 10px;
  padding: 0;
  white-space: pre;
  word-break: break-all;
  font-family: var(--font-mono, "JetBrains Mono", monospace);
  font-size: 11px;
  line-height: 1.45;
  color: #5ED9A8;
  background: transparent;
  border: 0;
}
.term-input-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
}
.term-prompt {
  flex-shrink: 0;
  font-family: var(--font-mono, "JetBrains Mono", monospace);
  font-size: 11px;
  color: #5ED9A8;
  font-weight: 700;
}
.term-input {
  flex: 1 1 auto;
  min-width: 0;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  background: transparent !important;
  color: #E2E8F0 !important;
  font-family: var(--font-mono, "JetBrains Mono", monospace) !important;
  font-size: 11px !important;
  padding: 0 !important;
  height: 18px !important;
  caret-color: #5ED9A8;
}
.term-caret {
  width: 7px;
  height: 13px;
  background: #5ED9A8;
  flex-shrink: 0;
  animation: term-blink 1.05s step-end infinite;
}
.term-input-row:focus-within .term-caret {
  opacity: 0;
}
@keyframes term-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  font-size: 12px;
}
.rank-item:last-child { border-bottom: none; }
.rank-pos {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  padding: 1px 4px;
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--primary);
  background: rgba(var(--primary-rgb), 0.12);
  border: 1px solid rgba(var(--primary-rgb), 0.28);
}
.rank-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }
.rank-score { font-family: var(--font-mono); font-size: 11px; color: var(--muted); }

/* 左宽右窄：CAL 主力 1.3fr / BUL+SYS 辅助 1fr */
.home-page .main-grid-container.home-bottom-grid,
.home-page .home-bottom-grid.main-grid-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  width: 100%;
  min-width: 0;
}
@media (min-width: 900px) {
  .home-page .main-grid-container.home-bottom-grid,
  .home-page .home-bottom-grid.main-grid-container {
    grid-template-columns: 1.3fr 1fr !important;
    gap: 16px !important;
  }
}
@media (min-width: 900px) {
  .home-page .home-col-main,
  .home-page .home-col-side {
    min-width: 0;
    max-width: none;
  }
}

@media (max-width: 899px) {
  .home-hero-hud {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 148px;
    max-height: none;
  }
  .hero-hud-deco { display: none; }
}
</style>

