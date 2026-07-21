<template>
  <MatrixShell
    prompt=""
    title="资料归档"
    subtitle="ARC · ARCHIVE"
    page-prompt="资料归档 · ARCHIVE"
    page-title="归档库"
    page-desc="往届比赛 · 资料 · 文章沉淀"
    :items="navItems"
  >
    <template #sidebar-footer>
      <router-link to="/" class="sidebar-link">
        <span class="link-code">HOM</span>
        <span>返回首页</span>
      </router-link>
      <router-link to="/wiki" class="sidebar-link">
        <span class="link-code">DOC</span>
        <span>知识库</span>
      </router-link>
    </template>

    <div class="archive-list">
      <article v-for="a in archives" :key="a.id" class="archive-item">
        <span class="link-code">ARC</span>
        <div class="archive-body">
          <h3 class="archive-title">{{ a.title }}</h3>
          <time class="archive-date">{{ a.date }}</time>
        </div>
      </article>
    </div>
  </MatrixShell>
</template>

<script>
import { MatrixShell } from '@/components/shared'

export default {
  name: 'Archive',
  components: { MatrixShell },
  data() {
    return {
      navItems: [{ code: 'ARC', label: '全部归档', active: true }],
      archives: [
        { id: 1, title: 'NEEPU CTF 2024 归档', date: '2024-12' },
        { id: 2, title: 'NEEPU Workshop Materials', date: '2025-03' },
      ],
    }
  },
}
</script>

<style scoped>
.archive-item {
  display: flex;
  align-items: flex-start;
  gap: var(--fib-13);
}

.archive-title {
  margin: 0 0 var(--fib-8);
  font-size: var(--text-lg);
  font-weight: 600;
}

.archive-date {
  font-size: var(--text-xs);
  color: var(--muted);
}
</style>
