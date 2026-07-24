<template>
  <div class="bulletin-container">
    <header class="bulletin-page-head">
      <p class="bulletin-prompt">公告栏 · BULLETIN</p>
      <h2 class="bulletin-page-title">公告列表</h2>
      <p class="bulletin-page-desc">平台公告 · 赛事通知 · 更新动态</p>
    </header>

    <n-spin :show="loading">
      <div v-if="pagedBulletins.length" class="bulletin-list">
        <article
          v-for="item in pagedBulletins"
          :key="item.id"
          class="bulletin-item"
          @click="openDetail(item)"
        >
          <div class="item-head">
            <span class="item-tag chip-cut">BUL</span>
            <div class="item-main">
              <div class="item-title-row">
                <h2 class="bulletin-title">{{ item.title }}</h2>
                <span class="item-link">阅读全文 →</span>
              </div>
              <p v-if="item.summary" class="bulletin-summary">{{ item.summary }}</p>
              <time class="bulletin-date">{{ formatDate(item.created_at || item.published_at) }}</time>
            </div>
          </div>
        </article>
      </div>
      <div v-else-if="!loading" class="empty-state">
        <p>暂无公告</p>
        <span class="muted">管理员可在后台发布平台公告</span>
      </div>
    </n-spin>

    <n-pagination
      v-if="bulletins.length > pageSize"
      v-model:page="page"
      :page-size="pageSize"
      :item-count="bulletins.length"
      class="bulletin-pagination"
    />
  </div>
</template>

<script>
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { NSpin, NPagination } from 'naive-ui'

export default {
  name: 'Bulletin',
  components: { NSpin, NPagination },
  setup() {
    const router = useRouter()
    const bulletins = inject('bulletinList')
    const loading = inject('bulletinListLoading')
    const page = ref(1)
    const pageSize = 10

    const pagedBulletins = computed(() => {
      const list = bulletins.value || []
      const start = (page.value - 1) * pageSize
      return list.slice(start, start + pageSize)
    })

    function formatDate(d) {
      if (!d) return ''
      try {
        return new Date(d).toLocaleDateString('zh-CN', {
          year: 'numeric', month: '2-digit', day: '2-digit',
        })
      } catch { return d }
    }

    function openDetail(item) {
      if (item?.id) router.push(`/bulletin/${item.id}`)
    }

    return {
      loading, bulletins, pagedBulletins, page, pageSize,
      formatDate, openDetail,
    }
  },
}
</script>

<style scoped>
.bulletin-container {
  max-width: none;
  margin: 0;
  width: 100%;
  padding: 24px 28px 36px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.bulletin-page-head { margin: 0 0 20px; padding: 0; }
.bulletin-prompt {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--muted);
}
.bulletin-page-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}
.bulletin-page-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--muted);
}
.bulletin-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}
.bulletin-item {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(20, 26, 33, 0.6);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  padding: 16px 24px;
  width: 100%;
  box-sizing: border-box;
}
.bulletin-item:hover {
  border-color: rgba(var(--primary-rgb), 0.42);
  background: rgba(20, 26, 33, 0.82);
  box-shadow: var(--gradient-card-shadow-hover);
}
.item-head {
  display: flex;
  gap: 14px;
  align-items: center;
  width: 100%;
}
.item-tag {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 22px;
  padding: 0 7px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #5ED9A8 !important;
  background: rgba(94, 217, 168, 0.12) !important;
  border: 1px solid rgba(94, 217, 168, 0.28) !important;
  border-radius: 4px;
}
.item-main { flex: 1; min-width: 0; }
.item-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}
.bulletin-title {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 15px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.4;
  word-break: break-word;
}
.bulletin-summary {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.45;
}
.bulletin-date {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.item-link {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--primary);
  white-space: nowrap;
}
.empty-state {
  padding: 40px 24px;
  color: var(--muted);
  border: 1px dashed rgba(94, 217, 168, 0.22);
  border-radius: 10px;
  background: rgba(94, 217, 168, 0.03);
}
.muted { font-size: 13px; display: block; margin-top: 8px; }
.bulletin-pagination { margin-top: 24px; justify-content: flex-start; }
</style>
