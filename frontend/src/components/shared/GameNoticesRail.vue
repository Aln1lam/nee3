<template>
  <aside class="game-notices-rail" aria-label="赛事通知">
    <header class="notices-head">
      <span class="link-code">NTF</span>
      <span class="notices-title">赛事通知</span>
      <button type="button" class="notices-refresh" :disabled="loading" @click="load">刷新</button>
    </header>
    <div v-if="loading && !items.length" class="notices-empty">加载中…</div>
    <div v-else-if="!items.length" class="notices-empty">暂无通知</div>
    <ul v-else class="notices-list custom-scrollbar">
      <li v-for="n in items" :key="n.id" class="notice-item">
        <time v-if="n.created_at" class="notice-time">{{ formatTime(n.created_at) }}</time>
        <p class="notice-title">{{ n.title || '通知' }}</p>
        <p v-if="n.content" class="notice-body">{{ n.content }}</p>
      </li>
    </ul>
  </aside>
</template>

<script>
import { ref, watch, onMounted, inject } from 'vue'

export default {
  name: 'GameNoticesRail',
  props: {
    gameId: { type: [Number, String], required: true },
  },
  setup(props) {
    const axios = inject('axios')
    const items = ref([])
    const loading = ref(false)

    function formatTime(iso) {
      if (!iso) return ''
      try {
        const d = new Date(iso)
        return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      } catch {
        return iso
      }
    }

    async function load() {
      if (!props.gameId) return
      loading.value = true
      try {
        const { data } = await axios.get(`/api/competitions/${props.gameId}/notices`)
        const rows = data?.data ?? data?.items ?? data ?? []
        items.value = Array.isArray(rows) ? rows : []
      } catch {
        items.value = []
      } finally {
        loading.value = false
      }
    }

    watch(() => props.gameId, () => load(), { immediate: false })
    onMounted(load)

    return { items, loading, load, formatTime }
  },
}
</script>

<style scoped>
.game-notices-rail {
  width: 260px;
  min-width: 260px;
  max-height: 100%;
  border-left: 1px solid var(--border, rgba(94, 217, 168, 0.15));
  background: rgba(8, 12, 16, 0.72);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.notices-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border, rgba(94, 217, 168, 0.12));
  flex-shrink: 0;
}
.notices-title {
  font-size: 13px;
  font-weight: 600;
  flex: 1;
}
.notices-refresh {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(94, 217, 168, 0.25);
  background: transparent;
  color: var(--text-secondary, #9aa3ad);
  cursor: pointer;
}
.notices-refresh:hover:not(:disabled) {
  color: var(--accent, #5ed9a8);
}
.notices-list {
  list-style: none;
  margin: 0;
  padding: 8px 10px 12px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}
.notice-item {
  padding: 10px 8px;
  border-bottom: 1px dashed rgba(94, 217, 168, 0.12);
}
.notice-time {
  display: block;
  font-size: 10px;
  color: var(--text-muted, #6b7280);
  margin-bottom: 4px;
}
.notice-title {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
}
.notice-body {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  color: var(--text-secondary, #b0b8c0);
  white-space: pre-wrap;
}
.notices-empty {
  padding: 24px 12px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted, #6b7280);
}
</style>
