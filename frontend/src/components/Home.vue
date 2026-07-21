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

    <main class="home-main sidebar-main">
      <header class="matrix-page-head home-page-head">
        <p class="matrix-page-prompt">HOM · 个人工作台</p>
        <h2 class="matrix-page-title">欢迎回来</h2>
        <p class="matrix-page-desc">轮播 · 赛事日历 · 平台公告</p>
      </header>

      <section class="hero large-hero">
        <div class="carousel">
          <div class="slides" :style="{ transform: `translateX(${ -currentIndex * 100 }%)` }">
            <div class="slide" v-for="(img, i) in heroImages" :key="i" @click="onSlideClick(img)" :class="{ clickable: img.link }">
              <img :src="img.src" :alt="img.alt" />
              <div class="slide-caption edge-tag bottom-left">{{ img.caption }}</div>
              <div class="slide-description" v-if="img.description">{{ img.description }}</div>
              <div class="edge-avatar bottom-right"><img :src="getAvatarUrl(user?.avatar)"/></div>
            </div>
          </div>
          <button class="carousel-prev" @click="prev">‹</button>
          <button class="carousel-next" @click="next">›</button>
          <div class="carousel-dots">
            <button v-for="(img,i) in heroImages" :key="i" :class="{ active: i===currentIndex }" @click="go(i)"></button>
          </div>
        </div>
      </section>

      <div class="home-bottom-grid">
        <n-card class="calendar-card">
          <template #header>
            <div class="card-title">
              <span class="link-code">CAL</span>
              <span>赛事日历</span>
            </div>
          </template>
          <div class="mini-calendar">
            <CalendarFull :events="fcEvents" :selected-region="selectedRegion" @event-click="onEventClick" @region-change="selectedRegion = $event" />
          </div>
        </n-card>

        <n-card class="announce-card">
          <template #header>
            <div class="card-title">
              <span class="link-code">BUL</span>
              <span>公告</span>
            </div>
          </template>
          <div v-if="announcements.length === 0" class="empty-announcements">
            <p>暂无公告</p>
          </div>
          <ul v-else class="announcement-list">
            <li v-for="a in announcements" :key="a.id" class="announcement-item">
              <div class="announcement-title">{{ a.title }}</div>
              <div class="announcement-content">{{ a.content.substring(0, 100) }}{{ a.content.length > 100 ? '...' : '' }}</div>
            </li>
          </ul>
        </n-card>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, inject, computed } from 'vue'
import { useRouter } from 'vue-router'
import { fetchSession, getUser } from '@/services/auth'
import { NCard } from 'naive-ui'
import CalendarFull from './CalendarFull.vue'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'
import { resolveUploadUrl } from '../utils/uploadUrl'
export default {
  name: 'Home',
  components: { NCard, CalendarFull },
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

    // 获取公告（需要登录）
    async function fetchAnnouncements() {
      try {
        const token = localStorage.getItem('neepu_token')
        if (!token) return
        
        const res = await axios.get('/api/articles/announcements', {
          headers: { Authorization: `Bearer ${token}` }
        })
        announcements.value = res.data || []
      } catch (e) {
        console.error('加载公告失败:', e)
        announcements.value = []
      }
    }

    onMounted(() => {
      fetchCarousel() // 加载轮播图
      startCarousel()
      fetchAnnouncements() // Load announcements from backend
      try {
        if (typeof navigator !== 'undefined' && !navigator.onLine) {
          // offline — skip external fetch to avoid noisy console errors
        } else {
          fetchExternalEvents()
        }
      } catch (e) {
        // defensive: if navigator is unavailable, attempt fetch
        fetchExternalEvents()
      }
      
      // Listen for user profile updates from other components (e.g., ProfileEdit)
      window.addEventListener('neepu_user_refreshed', refreshUserData)
    })
    onUnmounted(() => { 
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

    return { heroImages, currentIndex, prev, next, go, recentGames, announcements, categories, goCategory,
      user, months, currentMonth, currentYear, monthDays, prevMonth, nextMonth,
      fcEvents, onEventClick, fetchAnnouncements, getAvatarUrl, selectedRegion, externalEventsCN, externalEventsGlobal, onSlideClick,
      collapsed, toggleSidebar }
  }
}
</script>

<style scoped>
.home-page .profile-card {
  margin-bottom: var(--fib-8, 8px);
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

.large-hero .slide img { width:100%; object-fit:cover; display:block; filter:brightness(.95) }
.large-hero .slide.clickable { cursor:pointer }
.large-hero .slide.clickable:hover img { filter:brightness(1) }
.slide-caption { position:absolute; left:28px; bottom:26px; background:var(--overlay, rgba(0,0,0,0.55)); color:var(--slide-caption-color, #fff); padding:10px 14px; border-radius:8px }
.slide-description { position:absolute; left:28px; bottom:76px; background:var(--overlay, rgba(0,0,0,0.45)); color:var(--slide-caption-color, #fff); padding:6px 12px; border-radius:6px; font-size:13px; max-width:60% }

.card-title { display:flex; align-items:center; gap:10px; width:100%; font-family:var(--font-ui); font-weight:700 }
.month-header { display:flex; align-items:center; justify-content:space-between; padding-bottom:8px }
.month-header button { background:transparent; border:0; font-size:18px }
.weekdays { display:grid; grid-template-columns: repeat(7,1fr); color:var(--muted); font-size:12px; padding-bottom:8px }
.days-grid { display:grid; grid-template-columns: repeat(7,1fr); }
.day { background:var(--card-bg); display:flex; align-items:flex-start; justify-content:flex-end; border:1px solid rgba(0,0,0,0.03) }
.day.today { outline:2px solid var(--primary); }
  .day.hasEvent { box-shadow: var(--event-shadow, 0 4px 18px rgba(0,196,140,0.06)); border-color: rgba(var(--primary-rgb, 0,196,140),0.12) }
.day-num { font-size:12px; color:var(--muted) }

.empty-announcements { text-align: center; padding: var(--fib-21) 0; color: var(--muted); }
.announcement-list { list-style: none; padding: 0; margin: 0; }
.announcement-item { border-bottom: 1px solid rgba(0,0,0,0.05); }
.announcement-item:last-child { border-bottom: none; }
.announcement-title { font-weight: 600; font-size: var(--text-sm); color: var(--text); margin-bottom: 4px; }
.announcement-content { font-size: var(--text-xs); color: var(--muted); line-height: 1.5; }
.day-mark { color:var(--primary); font-size:12px; margin-left:6px }

.events-list { margin-top:6px; display:flex; flex-direction:column; gap:4px }
  .event-item { font-size:11px; padding:4px 6px; border-radius:6px; background: var(--event-coming-bg, rgba(0,191,216,0.06)); color: var(--text); border-left: 4px solid var(--primary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap }

.carousel-prev, .carousel-next { background: var(--card-bg); color: var(--slide-caption-color, #fff); width:44px; height:44px; border-radius:22px; border:0 }
.carousel-dots { position:absolute; right:14px; bottom:14px; display:flex; gap:6px }
.carousel-dots button { width:8px; height:8px; border-radius:50%; background:var(--dot-bg, rgba(255,255,255,0.5)); border:0 }
.carousel-dots button.active { background:var(--primary) }

/* responsive */
</style>
