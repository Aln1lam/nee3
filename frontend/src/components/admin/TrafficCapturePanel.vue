<template>
  <div class="pcap-panel">
    <header class="pcap-head">
      <div>
        <h3 class="pcap-title">流量捕获 PCAP</h3>
        <p class="pcap-desc">列出 / 下载 / 删除容器流量包（需赛事开启 enable_traffic_capture）</p>
      </div>
    </header>

    <div class="pcap-row">
      <label class="pcap-label">选择赛事</label>
      <n-select
        v-model:value="gameId"
        :options="gameOptions"
        :loading="gamesLoading"
        filterable
        placeholder="选择赛事"
        style="min-width: 280px; flex: 1"
        @update:value="loadCaptures"
      />
      <n-button :loading="loading" :disabled="!gameId" @click="loadCaptures">刷新</n-button>
    </div>

    <n-alert v-if="meta" type="info" :bordered="false" class="pcap-alert">
      共 {{ meta.total || 0 }} 条
      <span v-if="meta.enable === false"> · 本赛事未开启流量捕获</span>
      <span v-if="meta.storage_dir"> · {{ meta.storage_dir }}</span>
    </n-alert>

    <n-empty v-if="!loading && gameId && !rows.length" description="暂无 PCAP 记录" class="pcap-empty" />
    <n-data-table
      v-else-if="gameId"
      :columns="columns"
      :data="rows"
      :loading="loading"
      size="small"
      :bordered="false"
    />
  </div>
</template>

<script>
import { ref, computed, h, onMounted, watch } from 'vue'
import { NSelect, NButton, NAlert, NEmpty, NDataTable, useMessage } from 'naive-ui'
import { ctfAdmin } from '@/services/admin'
import { parseJsonResponse } from '@/utils/http'
import { apiErrorMessage } from '@/utils/apiError'

export default {
  name: 'TrafficCapturePanel',
  components: { NSelect, NButton, NAlert, NEmpty, NDataTable },
  props: {
    gameIdProp: { type: [Number, String], default: null },
  },
  setup(props) {
    const message = useMessage()
    const games = ref([])
    const gamesLoading = ref(false)
    const gameId = ref(props.gameIdProp ? Number(props.gameIdProp) : null)
    const rows = ref([])
    const loading = ref(false)
    const meta = ref(null)

    const gameOptions = computed(() =>
      games.value.map(g => ({ label: `${g.title} (#${g.id})`, value: g.id })),
    )

    function formatTime(t) {
      if (!t) return '-'
      try { return new Date(t).toLocaleString('zh-CN', { hour12: false }) } catch { return t }
    }
    function formatSize(n) {
      const b = Number(n) || 0
      if (b < 1024) return `${b} B`
      if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`
      return `${(b / 1048576).toFixed(1)} MB`
    }

    const columns = computed(() => [
      { title: 'ID', key: 'id', width: 60 },
      { title: '队伍', key: 'team_name' },
      { title: '题目', key: 'challenge_title' },
      { title: '选手', key: 'user_nickname', width: 100 },
      { title: '大小', key: 'file_size', width: 90, render: r => formatSize(r.file_size) },
      { title: '文件', key: 'file_exists', width: 70, render: r => (r.file_exists ? '有' : '缺') },
      { title: '时间', key: 'created_at', width: 160, render: r => formatTime(r.created_at) },
      {
        title: '操作',
        key: 'actions',
        width: 160,
        render: (r) => h('div', { style: 'display:flex;gap:6px' }, [
          h(NButton, {
            size: 'tiny',
            disabled: !r.file_exists,
            onClick: () => downloadCapture(r),
          }, { default: () => '下载' }),
          h(NButton, {
            size: 'tiny',
            type: 'error',
            secondary: true,
            onClick: () => deleteCapture(r),
          }, { default: () => '删除' }),
        ]),
      },
    ])

    async function loadGames() {
      gamesLoading.value = true
      try {
        const res = await ctfAdmin.listGames(100)
        const { data, ok } = await parseJsonResponse(res)
        let list = []
        if (ok) {
          if (Array.isArray(data?.data)) list = data.data
          else if (Array.isArray(data?.data?.items)) list = data.data.items
          else if (Array.isArray(data?.items)) list = data.items
        }
        games.value = list.filter(g => !g.is_ephemeral)
        if (!gameId.value && games.value.length) {
          const withCapture = games.value.find(g => g.id === 1) || games.value.find(g => (g.challenge_count || 0) > 0) || games.value[0]
          gameId.value = withCapture?.id || null
        }
        if (gameId.value) await loadCaptures()
      } catch (e) {
        message.error(apiErrorMessage(e, '加载赛事失败'))
      } finally {
        gamesLoading.value = false
      }
    }

    async function loadCaptures() {
      if (!gameId.value) return
      loading.value = true
      try {
        const res = await ctfAdmin.listTrafficCaptures(gameId.value, true)
        const { data: body, ok } = await parseJsonResponse(res)
        if (!ok) {
          rows.value = []
          meta.value = null
          message.error(body?.msg || '加载流量包失败')
          return
        }
        const payload = body?.data || {}
        rows.value = payload.items || []
        meta.value = {
          total: payload.total,
          storage_dir: payload.storage_dir,
          enable: payload.game?.enable_traffic_capture,
        }
      } catch (e) {
        rows.value = []
        meta.value = null
        message.error(apiErrorMessage(e, '加载流量包失败'))
      } finally {
        loading.value = false
      }
    }

    async function downloadCapture(row) {
      if (!row?.id) return
      try {
        const res = await ctfAdmin.downloadTrafficCapture(row.id)
        if (!res.ok) {
          const { data } = await parseJsonResponse(res)
          message.error(data?.msg || '下载失败')
          return
        }
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = (row.file_path || `capture_${row.id}.pcap`).split('/').pop()
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
        message.success('已开始下载')
      } catch (e) {
        message.error(apiErrorMessage(e, '下载失败'))
      }
    }

    async function deleteCapture(row) {
      if (!row?.id) return
      if (!window.confirm(`确认删除 PCAP #${row.id}？`)) return
      try {
        const res = await ctfAdmin.deleteTrafficCapture(row.id)
        const { data: body, ok } = await parseJsonResponse(res)
        if (!ok) {
          message.error(body?.msg || '删除失败')
          return
        }
        message.success(body?.msg || '已删除')
        await loadCaptures()
      } catch (e) {
        message.error(apiErrorMessage(e, '删除失败'))
      }
    }

    watch(() => props.gameIdProp, (v) => {
      if (v) {
        gameId.value = Number(v)
        loadCaptures()
      }
    })

    onMounted(loadGames)

    return {
      gameId,
      gameOptions,
      gamesLoading,
      rows,
      loading,
      meta,
      columns,
      loadCaptures,
    }
  },
}
</script>

<style scoped>
.pcap-panel { padding: 4px 0 16px; }
.pcap-head { margin-bottom: 12px; }
.pcap-title { margin: 0; font-size: 1.1rem; font-weight: 700; }
.pcap-desc { margin: 4px 0 0; font-size: 13px; color: var(--text-muted, var(--muted)); }
.pcap-row { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 14px; }
.pcap-label { font-size: 13px; color: var(--text-muted, var(--muted)); }
.pcap-alert { margin-bottom: 12px; }
.pcap-empty { padding: 28px 0; }
</style>
