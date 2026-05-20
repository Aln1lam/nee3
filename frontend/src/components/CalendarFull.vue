<template>
  <div class="calendar-full">
    <FullCalendar ref="calendarRef" :options="calendarOptions" />
  </div>
</template>

<script>
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
// CSS imports may require adjustment depending on installed FullCalendar version
// Note: some FullCalendar package builds don't expose CSS via subpath imports
// to avoid Vite import-resolution errors we load CSS via CDN in index.html
// If you prefer local imports, adjust to the exact package/build paths available in node_modules.

export default {
  name: 'CalendarFull',
  components: { FullCalendar },
  props: {
    events: { type: Array, default: () => [] },
    selectedRegion: { type: String, default: 'global' }
  },
  emits: ['event-click', 'region-change'],
  data() {
    const self = this
    return {
      calendarOptions: {
        plugins: [ dayGridPlugin, timeGridPlugin, interactionPlugin ],
        initialView: 'dayGridMonth',
        customButtons: {
          cnButton: {
            text: '国内',
            click: function() { self.$emit('region-change', 'cn') }
          },
          globalButton: {
            text: '国外',
            click: function() { self.$emit('region-change', 'global') }
          }
        },
        headerToolbar: { left: 'prev,next', center: 'title', right: 'cnButton,globalButton dayGridMonth,timeGridWeek' },
        events: this.events,
        eventDisplay: 'block',
        height: 'auto',
        editable: false,
        selectable: false,
        eventClick: (info) => {
          try{
            // prefer opening an external URL if present on the event
            const evt = info.event
            const maybeUrl = evt.url || (evt.extendedProps && evt.extendedProps.url) || (evt._def && evt._def.extendedProps && evt._def.extendedProps.url) || (evt.toPlainObject && evt.toPlainObject().url)
            if(maybeUrl){
              try{ window.open(maybeUrl, '_blank') }catch(e){ window.location.href = maybeUrl }
              if(info.jsEvent && info.jsEvent.preventDefault) info.jsEvent.preventDefault()
              return
            }
            // otherwise emit for the parent to handle (SPA route, detail view, etc.)
            const payload = info.event && info.event.toPlainObject ? info.event.toPlainObject() : { id: info.event.id, title: info.event.title, start: info.event.start, end: info.event.end }
            this.$emit('event-click', payload)
          }catch(e){
            try{ this.$emit('event-click', { id: info.event.id, title: info.event.title, start: info.event.start, end: info.event.end, url: info.event.url }) }catch(_){}
          }
        }
      }
    }
  },
  watch: {
    events(newVal){ this.calendarOptions = { ...this.calendarOptions, events: newVal } },
    selectedRegion: {
      immediate: true,
      handler(newVal) {
        this.$nextTick(() => {
          this.updateRegionButtonStyles(newVal)
        })
      }
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.updateRegionButtonStyles(this.selectedRegion)
    })
  },
  methods: {
    updateRegionButtonStyles(region) {
      const el = this.$el
      if (!el) return
      const cnBtn = el.querySelector('.fc-cnButton-button')
      const globalBtn = el.querySelector('.fc-globalButton-button')
      if (cnBtn) {
        cnBtn.classList.toggle('fc-button-active', region === 'cn')
      }
      if (globalBtn) {
        globalBtn.classList.toggle('fc-button-active', region === 'global')
      }
    }
  }
}
</script>

<style scoped>
.calendar-full { padding: 6px }
</style>

<style>
/* Global styles for FullCalendar custom buttons */
.fc-cnButton-button.fc-button-active,
.fc-globalButton-button.fc-button-active {
  background-color: #00c48c !important;
  border-color: #00c48c !important;
}
</style>
