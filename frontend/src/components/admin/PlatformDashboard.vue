<template>
  <div class="dashboard">
    <div class="metrics-grid">
      <MetricCard
        title="总用户数"
        :value="stats.users.total"
        :icon="User"
        :subtext="`新增 ${stats.users.new_7d} 人 (7天)`"
      />
      <MetricCard
        title="总文章数"
        :value="stats.articles.total"
        :icon="FileText"
        :subtext="`发布 ${stats.articles.published} 篇`"
      />
      <MetricCard
        title="总团队数"
        :value="stats.teams.total"
        :icon="Users"
      />
      <MetricCard
        title="存储空间"
        :value="`${stats.resources.storage_mb} MB`"
        :icon="Database"
        :subtext="`${stats.resources.total} 个文件`"
      />
      <MetricCard
        title="活跃用户"
        :value="stats.users.active"
        :icon="Activity"
      />
      <MetricCard
        title="管理员数"
        :value="stats.users.admins"
        :icon="ShieldCheck"
      />
    </div>

    <div class="charts-section">
      <div class="chart-container">
        <h3 class="section-title">
          <n-icon :size="18" :component="TrendingUp" class="section-icon" />
          <span>用户增长趋势 (7天)</span>
        </h3>
        <div class="chart">
          <div class="bar-chart">
            <div v-for="item in stats.trends.daily_new_users" :key="item.date" class="bar-item">
              <div class="bar-track">
                <div class="bar" :style="{ height: barHeight(item.count) }"></div>
              </div>
              <div class="label">{{ item.date }}</div>
              <div class="value">{{ item.count }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-container">
        <h3 class="section-title">
          <n-icon :size="18" :component="FileText" class="section-icon" />
          <span>文章状态分布</span>
        </h3>
        <div class="chart">
          <div class="pie-chart">
            <div class="pie-item published">
              <div class="pie-label">已发布</div>
              <div class="pie-value">{{ articlesDistribution.published }}</div>
            </div>
            <div class="pie-item draft">
              <div class="pie-label">草稿</div>
              <div class="pie-value">{{ articlesDistribution.draft }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="active-users">
      <h3 class="section-title">
        <n-icon :size="18" :component="Crown" class="section-icon" />
        <span>活跃用户 Top 10</span>
      </h3>
      <table class="users-table">
        <thead>
          <tr>
            <th>排名</th>
            <th>用户昵称</th>
            <th>提交次数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, idx) in topUsers" :key="user.user_id">
            <td class="rank-cell"><strong>{{ idx + 1 }}</strong></td>
            <td class="nick-cell">{{ user.nickname }}</td>
            <td><span class="badge">{{ user.submission_count }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { NIcon } from 'naive-ui'
import { User, Users, Activity, ShieldCheck, FileText, Database, TrendingUp, Crown } from '@vicons/tabler'
import MetricCard from './MetricCard.vue'
import platformAdmin from '@/services/admin/platform'

export default {
  name: 'PlatformDashboard',
  components: { MetricCard, NIcon },
  setup() {
    const DEFAULT_STATS = {
      users: { total: 0, new_7d: 0, new_30d: 0, admins: 0, active: 0 },
      articles: { total: 0, published: 0, draft: 0 },
      resources: { total: 0, storage_bytes: 0, storage_mb: 0 },
      teams: { total: 0 },
      trends: { daily_new_users: [] },
    }

    const stats = ref({ ...DEFAULT_STATS })
    const articlesDistribution = ref({ published: 0, draft: 0 })
    const topUsers = ref([])

    async function loadDashboard() {
      try {
        const [dashRes, distRes, topRes] = await Promise.all([
          platformAdmin.getDashboard(),
          platformAdmin.getArticlesDistribution(),
          platformAdmin.getTopActiveUsers(),
        ])

        const d = dashRes.data || {}
        stats.value = {
          users: { ...DEFAULT_STATS.users, ...(d.users || {}) },
          articles: { ...DEFAULT_STATS.articles, ...(d.articles || {}) },
          resources: { ...DEFAULT_STATS.resources, ...(d.resources || {}) },
          teams: { ...DEFAULT_STATS.teams, ...(d.teams || {}) },
          trends: {
            daily_new_users: d.trends?.daily_new_users || DEFAULT_STATS.trends.daily_new_users,
          },
        }
        articlesDistribution.value = distRes.data || { published: 0, draft: 0 }
        topUsers.value = topRes.data?.items || []
      } catch (e) {
        console.error('加载仪表盘失败:', e)
      }
    }

    onMounted(loadDashboard)

    function barHeight(count) {
      const n = Number(count) || 0
      const max = Math.max(
        1,
        ...(stats.value.trends.daily_new_users || []).map((x) => Number(x.count) || 0),
      )
      const px = Math.round(24 + (n / max) * 140)
      return `${px}px`
    }

    return {
      stats,
      articlesDistribution,
      topUsers,
      User,
      Users,
      Activity,
      ShieldCheck,
      FileText,
      Database,
      TrendingUp,
      Crown,
      barHeight,
    }
  },
}
</script>

<style scoped>
.dashboard {
  animation: fadeIn 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text, #e8eaed);
}

.section-icon {
  color: #5ED9A8;
  opacity: 0.9;
}

.chart-container {
  background: rgba(20, 26, 33, 0.55);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px 18px;
  overflow: visible;
}

.chart {
  min-height: 220px;
  height: auto;
  overflow: visible;
  display: flex;
  align-items: stretch;
  justify-content: center;
}

.bar-chart {
  display: flex;
  align-items: stretch;
  justify-content: space-around;
  gap: 10px;
  width: 100%;
  min-height: 220px;
  height: 240px;
  overflow: visible;
  box-sizing: border-box;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  flex: 1;
  min-width: 0;
  height: 100%;
  overflow: visible;
}

.bar-track {
  flex: 1 1 auto;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  min-height: 160px;
  overflow: visible;
}

.bar {
  width: 60%;
  max-width: 28px;
  min-height: 8px;
  background: linear-gradient(180deg, #7ee7bc, #5ED9A8);
  border-radius: 6px 6px 0 0;
  box-shadow: 0 0 12px rgba(94, 217, 168, 0.25);
  transition: opacity 0.15s, transform 0.15s;
}

.bar:hover {
  opacity: 0.95;
  transform: translateY(-2px);
}

.bar-item .label {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  color: #9ca3af;
  margin-top: 8px;
  white-space: nowrap;
}

.bar-item .value {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: #5ED9A8;
  margin-top: 2px;
}

.pie-chart {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 30px;
  width: 100%;
  height: 100%;
}

.pie-item {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border: 1px solid rgba(94, 217, 168, 0.25);
}

.pie-item.published {
  background: rgba(94, 217, 168, 0.16);
  color: #5ED9A8;
}

.pie-item.draft {
  background: rgba(255, 255, 255, 0.05);
  color: #9ca3af;
  border-color: rgba(255, 255, 255, 0.1);
}

.pie-label {
  font-size: 13px;
  opacity: 1;
  color: inherit;
}

.pie-value {
  font-size: 28px;
  margin-top: 5px;
  font-variant-numeric: tabular-nums;
}

.active-users {
  background: rgba(20, 26, 33, 0.72);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 16px 18px;
  overflow: visible;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
.active-users,
.active-users * {
  opacity: 1 !important;
  filter: none !important;
  text-shadow: none !important;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.users-table thead {
  background: rgba(94, 217, 168, 0.06);
  border-bottom: 1px solid rgba(94, 217, 168, 0.18);
}

.users-table th {
  padding: 12px;
  text-align: left;
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #9ca3af !important;
  letter-spacing: 0.02em;
  text-transform: none !important;
  opacity: 1 !important;
}

.users-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 14px !important;
  font-weight: 500 !important;
  color: #f3f4f6 !important;
  opacity: 1 !important;
}

.users-table td.nick-cell {
  color: #f3f4f6 !important;
  font-weight: 500 !important;
}

.users-table td.rank-cell,
.users-table td.rank-cell strong {
  color: #10b981 !important;
  font-weight: 700 !important;
  font-variant-numeric: tabular-nums;
}

.users-table tbody tr:hover {
  background: rgba(16, 185, 129, 0.06);
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  background: rgba(16, 185, 129, 0.16);
  color: #10b981 !important;
  border: 1px solid rgba(16, 185, 129, 0.4);
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700 !important;
  font-variant-numeric: tabular-nums;
  opacity: 1 !important;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
