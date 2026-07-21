<template>
  <div class="events-root">
    <div class="calendar-toolbar">
      <h2 class="events-title"><span class="link-code">CAL</span> 赛事日历</h2>
      <div class="toolbar-actions">
        <n-space>
          <n-button :size="'small'" :type="mode==='domestic'? 'primary' : 'default'" round @click="mode='domestic'">国内</n-button>
          <n-button :size="'small'" :type="mode==='foreign'? 'primary' : 'default'" round @click="mode='foreign'">国外</n-button>
        </n-space>
      </div>
    </div>

    <div class="events-layout">
      <div class="events-main">
        <div class="calendar-header">
          <button @click="prevMonth">‹</button>
          <div>{{ year }}年 {{ month + 1 }}月</div>
          <button @click="nextMonth">›</button>
        </div>
        <div class="calendar-grid">
          <div class="cal-cell head" v-for="d in weekDays" :key="d">{{ d }}</div>
          <div class="cal-cell" v-for="cell in cells" :key="cell.key">
            <div class="cell-date">{{ cell.day }}</div>
            <div class="cell-events">
              <div v-for="e in cell.events.slice(0,3)" :key="e.id" class="evt" @click="openEvent(e)">
                {{ e.title || e['比赛名称'] }}
              </div>
              <div v-if="cell.events.length>3" class="more">+{{ cell.events.length-3 }} 场</div>
            </div>
          </div>
        </div>
      </div>

      <div class="events-side">
        <n-card>
          <template #header>
            <div class="side-header">
              <div class="side-title"><span class="link-code">LST</span> 赛程列表</div>
              <div>
                <n-select v-model:value="statusFilter" :options="statusOptions" size="small" clearable @update:value="fetchEvents" />
              </div>
            </div>
          </template>
          <div class="side-list">
            <div v-for="ev in filteredList" :key="ev.id" class="list-item" @click="openEvent(ev)">
              <div class="list-title">{{ ev.title || ev['比赛名称'] }}</div>
              <div class="list-time">{{ ev.time_range || ev['比赛时间'] }}</div>
            </div>
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { NCard, NSelect, NButton, NSpace } from 'naive-ui'

function parseRange(s) {
  if (!s) return null
  // try to parse formats like "2024-01-01 00:00:00 - 2024-01-02 08:00:00 UTC+8"
  const parts = s.split(' - ')
  try {
    const a = new Date(parts[0].replace(/UTC.*$/,'').trim())
    const b = parts[1] ? new Date(parts[1].replace(/UTC.*$/,'').trim()) : a
    return { start: a, end: b }
  } catch (e) { return null }
}

export default {
  components: { NCard, NSelect, NButton, NSpace },
  setup() {
    const mode = ref('foreign')
    const year = ref((new Date()).getFullYear())
    const month = ref((new Date()).getMonth())
    const weekDays = ['日','一','二','三','四','五','六']
    const events = ref([])
    const statusFilter = ref(null)
    const statusOptions = [{ label:'全部', value:null },{ label:'即将开始', value:'oncoming' },{ label:'进行中', value:'nowrunning' },{ label:'已结束', value:'past' }]

    function buildCells() {
      const first = new Date(year.value, month.value, 1)
      const last = new Date(year.value, month.value + 1, 0)
      const startDay = first.getDay()
      const total = last.getDate()
      const cells = []
      // fill blanks
      for (let i=0;i<startDay;i++) cells.push({ key: `b-${i}`, day: '', events: [] })
      for (let d=1; d<=total; d++) {
        const dateKey = new Date(year.value, month.value, d).toISOString().slice(0,10)
        const dayEvents = events.value.filter(ev => {
          const r = ev._range
          if (!r) return false
          // match by date (local)
          const s = r.start
          const e = r.end
          const ds = new Date(s.getFullYear(), s.getMonth(), s.getDate()).toISOString().slice(0,10)
          const de = new Date(e.getFullYear(), e.getMonth(), e.getDate()).toISOString().slice(0,10)
          return dateKey >= ds && dateKey <= de
        })
        cells.push({ key: dateKey, day: d, events: dayEvents })
      }
      return cells
    }

    const cells = computed(() => buildCells())

    const filteredList = computed(() => {
      if (!statusFilter.value) return events.value
      return events.value.filter(ev => (ev['比赛状态'] || ev.status) === statusFilter.value)
    })

    async function fetchForeign() {
      try {
        const r = await fetch('https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/Global.json')
        const data = await r.json()
        // map and parse
        events.value = data.map((it, idx) => {
          const parsed = parseRange(it['比赛时间'] || it.time || '')
          return Object.assign({ id: it['比赛ID'] || it.id || idx, title: it['比赛名称'] || it.name, time_range: it['比赛时间'] }, it, { _range: parsed, status: it['比赛状态'] })
        })
      } catch (e) { console.error('fetch foreign failed', e); events.value = [] }
    }

    async function fetchDomestic() {
      // placeholder - could hit /api/events in future
      events.value = []
    }

    async function fetchEvents() {
      if (mode.value === 'foreign') await fetchForeign()
      else await fetchDomestic()
    }

    function prevMonth() { if (month.value === 0) { month.value = 11; year.value-- } else month.value-- }
    function nextMonth() { if (month.value === 11) { month.value = 0; year.value++ } else month.value++ }

    function openEvent(ev) { window.open(ev['比赛链接'] || ev.link || ev.url || '#') }

    onMounted(()=>{ fetchEvents() })

    return { mode, year, month, weekDays, cells, events, statusFilter, statusOptions, filteredList, prevMonth, nextMonth, openEvent, fetchEvents }
  }
}
</script>

<style scoped>
.calendar-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}
.events-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-family: var(--font-ui);
  font-weight: 700;
  color: var(--text);
}
.toolbar-actions { display: flex; align-items: center; }
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: var(--calendar-gap, 6px);
}
.cell-date {
  font-size: var(--text-sm);
  color: var(--muted);
  font-weight: 600;
  font-family: var(--font-ui);
}
.cell-events { margin-top: 6px; }
.evt {
  background: rgba(var(--primary-rgb), 0.14);
  color: var(--text);
  padding: 4px 8px;
  margin-bottom: 4px;
  border-radius: var(--radius-pill, 10px);
  border-left: 3px solid var(--primary);
  cursor: pointer;
  font-size: var(--text-xs);
  font-weight: 600;
  font-family: var(--font-ui);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.more {
  font-size: var(--text-xs);
  color: var(--primary);
  font-weight: 600;
}
.events-side { flex: 1; }
.side-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.side-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}
.side-list { max-height: 520px; overflow: auto; }
.list-item {
  padding: var(--fib-13, 13px);
  border-radius: var(--card-radius);
  cursor: pointer;
  transition: background 0.2s;
}
.list-item:hover { background: rgba(var(--primary-rgb), 0.06); }
.list-title { font-weight: 600; font-family: var(--font-ui); }
.list-time {
  font-size: var(--text-xs);
  color: var(--muted);
  margin-top: 4px;
}
</style>
