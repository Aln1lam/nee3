<template>
  <div class="page-container">
    
    <div class="header-section">
      <div class="bracket-title">
        <span class="bracket">[</span>
        <span class="title-text">提交审计</span>
        <span class="bracket">]</span>
      </div>
      <div class="search-box">
        <n-input-group>
          <n-input v-model:value="cid" placeholder="Challenge ID..." :style="{ width: 'var(--submission-input-width, 200px)' }" />
          <n-button type="default" @click="load">检索</n-button>
        </n-input-group>
      </div>
    </div>

    <div class="table-wrapper">
      <n-data-table
        :columns="columns"
        :data="data"
        :bordered="false"
        :single-line="false"
      />
    </div>

  </div>
</template>

<script>
import { ref, inject, h } from 'vue'
import { NDataTable, NTag, NInput, NInputGroup, NButton } from 'naive-ui'

export default {
  components: { NDataTable, NInput, NInputGroup, NButton },
  setup() {
    const axios = inject('axios')
    const cid = ref('')
    const data = ref([])

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
            { default: () => row.correct ? 'CORRECT' : 'WRONG' }
          )
        }
      }
    ]

    async function load() {
      if (!cid.value) return
      try {
        const res = await axios.get(`/api/games/challenges/${cid.value}/submissions`)
        data.value = res.data.items || []
      } catch (e) {
        data.value = []
        alert('查询失败')
      }
    }

    return { cid, data, columns, load }
  }
}
</script>

<style scoped>
.page-container { padding: var(--submissions-page-padding, 40px); font-family: 'Fira Code', monospace; }
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--submissions-header-margin-bottom, 30px); }
.bracket-title { font-size: 1.5rem; font-weight: 700; color: var(--submissions-title-color, #333); }
.bracket { color: #ccc; }

.table-wrapper {
  background: var(--submissions-table-bg, #fff); border: var(--submissions-table-border, 1px solid #eee); padding: var(--submissions-table-padding, 20px);
}
</style>