<template>
  <MatrixShell
    prompt=""
    title="提交审计"
    subtitle="SUB · AUDIT"
    page-prompt="提交记录 · AUDIT"
    page-title="提交记录"
    page-desc="按题目 ID 检索 Flag 提交历史"
    :items="navItems"
  >
    <div class="matrix-panel matrix-data-panel">
      <div class="matrix-page-head">
        <span class="link-code">SRH</span>
        <n-input-group>
          <n-input v-model:value="cid" placeholder="Challenge ID..." style="max-width: 280px" />
          <n-button type="primary" :loading="loading" @click="load">检索</n-button>
        </n-input-group>
      </div>
      <n-alert v-if="error" type="error" style="margin-bottom: 12px" :bordered="false">{{ error }}</n-alert>
      <n-empty v-else-if="!loading && searched && !data.length" description="暂无提交记录" />
      <div v-else class="table-wrapper">
        <n-data-table :columns="columns" :data="data" :bordered="false" :single-line="false" :loading="loading" />
      </div>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, inject, h, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NDataTable, NTag, NInput, NInputGroup, NButton, NAlert, NEmpty, useMessage } from 'naive-ui'
import { MatrixShell } from '@/components/shared'
import { getMySubmissions } from '@/services/challenges'
import { apiErrorMessage } from '@/utils/apiError'

export default {
  name: 'Submissions',
  components: { NDataTable, NInput, NInputGroup, NButton, NAlert, NEmpty, MatrixShell },
  setup() {
    const axios = inject('axios')
    const route = useRoute()
    const message = useMessage()
    const cid = ref(String(route.query.challenge || route.query.cid || ''))
    const data = ref([])
    const loading = ref(false)
    const searched = ref(false)
    const error = ref('')
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
      if (!cid.value) {
        message.warning('请输入题目 ID')
        return
      }
      loading.value = true
      error.value = ''
      searched.value = true
      try {
        const raw = await getMySubmissions(cid.value)
        const payload = raw?.data || raw
        data.value = payload?.items || []
      } catch (e) {
        data.value = []
        error.value = apiErrorMessage(e, '加载提交记录失败')
        message.error(error.value)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      if (cid.value) load()
    })

    return { cid, data, columns, load, navItems, loading, searched, error, axios }
  },
}
</script>
