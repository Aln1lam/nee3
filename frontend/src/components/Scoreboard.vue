<template>
  <div class="card">
    <h2>排行榜 (Game {{ gameId }})</h2>
    <button @click="close">返回</button>
    <button @click="refresh">刷新</button>
    <table class="scoreboard-table">
      <thead>
        <tr><th>排名</th><th>队伍名称</th><th>得分</th><th>解题数</th><th>队伍人数</th><th>最后提交</th></tr>
      </thead>
      <tbody>
        <tr v-for="(it, idx) in items" :key="it.team_id" class="scoreboard-row" :class="{ 'top3': idx < 3 }">
          <td class="rank">{{ it.rank || idx+1 }}</td>
          <td class="team-name">{{ it.team_name }}</td>
          <td class="points">{{ it.total_points }}</td>
          <td class="solves">{{ it.solved_challenges }}</td>
          <td class="members">{{ it.members_count }}</td>
          <td class="time">{{ formatTime(it.last_submission_time) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { ref, watch, inject } from 'vue'
export default {
  props: ['gameId'],
  emits: ['close'],
  setup(props, { emit }) {
    const axios = inject('axios')
    const items = ref([])

    function formatTime(timeStr) {
      if (!timeStr) return '-'
      try {
        const date = new Date(timeStr)
        return date.toLocaleString('zh-CN')
      } catch (e) {
        return timeStr
      }
    }

    async function load() {
      if (!props.gameId) return
      try {
        const { data } = await axios.get(`/api/ctf/games/${props.gameId}/scoreboard`)
        items.value = data.data?.rankings || []
      } catch (e) {
        console.error('Failed to load scoreboard:', e)
        items.value = []
      }
    }

    function refresh() { load() }
    function close() { emit('close') }

    watch(() => props.gameId, () => load(), { immediate: true })

    return { items, refresh, close, formatTime }
  }
}
</script>

<style>
.card { padding: var(--scoreboard-card-padding, 12px); background: var(--scoreboard-card-bg, #fafbfc); border-radius:8px }
.scoreboard-table { width: 100%; border-collapse: collapse; margin-top: var(--scoreboard-table-margin-top, 8px) }
.scoreboard-row { border-bottom: var(--scoreboard-row-border, 1px solid #eef); transition: background-color 0.2s }
.scoreboard-row:hover { background-color: rgba(0,0,0,0.02) }
.scoreboard-row.top3 { font-weight: bold; background-color: rgba(255,215,0,0.05) }
.rank { text-align: center; font-weight: bold; min-width: 50px }
.team-name { text-align: left; font-weight: 600 }
.points { text-align: right; color: var(--primary); font-weight: bold }
.solves { text-align: center }
.members { text-align: center }
.time { text-align: center; font-size: 12px; color: var(--muted) }
</style>
