<template>
  <div class="page-wrap">
    <n-card>
      <template #header>
        <div class="card-title">归档 / Archive</div>
      </template>
      <div class="desc">存放往届比赛、资料和文章归档。</div>
      <div class="archive-list">
        <div v-for="a in archives" :key="a.id" class="archive-item">
          <div class="title">{{ a.title }}</div>
          <div class="meta">{{ a.date }}</div>
        </div>
      </div>
    </n-card>
  </div>
</template>

<script>
import { NCard } from 'naive-ui'
export default {
  name: 'Archive',
  components: { NCard },
  data() {
    return {
      archives: [
        { id: 1, title: 'NEEPU CTF 2024 归档', date: '2024-12' },
        { id: 2, title: 'NEEPU Workshop Materials', date: '2025-03' }
      ]
    }
  }
}
</script>

<style scoped>
.page-wrap { padding:16px }
.archive-item { padding:10px 0; border-bottom:1px solid #f0f0f0 }
.title { font-weight:700 }
.meta { color:#888 }
</style>
