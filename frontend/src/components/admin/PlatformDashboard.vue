<template>
  <div class="dashboard">
    <!-- 关键指标卡片 -->
    <div class="metrics-grid">
      <MetricCard 
        title="总用户数" 
        :value="stats.users.total" 
        icon="👥"
        :subtext="`新增 ${stats.users.new_7d} 人 (7天)`"
      />
      <MetricCard 
        title="总文章数" 
        :value="stats.articles.total" 
        icon="📰"
        :subtext="`发布 ${stats.articles.published} 篇`"
      />
      <MetricCard 
        title="总团队数" 
        :value="stats.teams.total" 
        icon="👨‍👩‍👧‍👦"
      />
      <MetricCard 
        title="存储空间" 
        :value="`${stats.resources.storage_mb} MB`" 
        icon="💾"
        :subtext="`${stats.resources.total} 个文件`"
      />
      <MetricCard 
        title="活跃用户" 
        :value="stats.users.active" 
        icon="⚡"
      />
      <MetricCard 
        title="管理员数" 
        :value="stats.users.admins" 
        icon="🔧"
      />
    </div>

    <!-- 图表区 -->
    <div class="charts-section">
      <div class="chart-container">
        <h3>📈 用户增长趋势 (7天)</h3>
        <div class="chart">
          <div class="bar-chart">
            <div v-for="item in stats.trends.daily_new_users" :key="item.date" class="bar-item">
              <div class="bar" :style="{ height: (item.count * 20 + 40) + 'px' }"></div>
              <div class="label">{{ item.date }}</div>
              <div class="value">{{ item.count }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-container">
        <h3>📄 文章状态分布</h3>
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

    <!-- 待办任务完成情况 -->
    <div class="todo-stats">
      <h3>✅ 待办任务统计</h3>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: stats.todos.completion_rate + '%' }"></div>
      </div>
      <div class="progress-text">
        完成率: {{ stats.todos.completion_rate }}% ({{ stats.todos.completed }} / {{ stats.todos.total }})
      </div>
    </div>

    <!-- 活跃用户排行 -->
    <div class="active-users">
      <h3>👑 活跃用户 Top 10</h3>
      <table class="users-table">
        <thead>
          <tr>
            <th>排名</th>
            <th>用户昵称</th>
            <th>待办任务数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, idx) in topUsers" :key="user.user_id">
            <td><strong>{{ idx + 1 }}</strong></td>
            <td>{{ user.nickname }}</td>
            <td><span class="badge">{{ user.todo_count }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted } from 'vue'
import MetricCard from './MetricCard.vue'

export default {
  name: 'PlatformDashboard',
  components: { MetricCard },
  setup() {
    const axios = inject('axios')
    
    const stats = ref({
      users: { total: 0, new_7d: 0, new_30d: 0, admins: 0, active: 0 },
      articles: { total: 0, published: 0, draft: 0 },
      resources: { total: 0, storage_bytes: 0, storage_mb: 0 },
      todos: { total: 0, completed: 0, completion_rate: 0 },
      teams: { total: 0 },
      trends: { daily_new_users: [] }
    })
    
    const articlesDistribution = ref({ published: 0, draft: 0 })
    const topUsers = ref([])

    async function loadDashboard() {
      try {
        const token = localStorage.getItem('neepu_token')
        const headers = { Authorization: `Bearer ${token}` }
        
        const [dashRes, distRes, topRes] = await Promise.all([
          axios.get('/api/admin/platform/dashboard', { headers }),
          axios.get('/api/admin/platform/stats/articles-distribution', { headers }),
          axios.get('/api/admin/platform/stats/top-active-users', { headers })
        ])
        
        stats.value = dashRes.data
        articlesDistribution.value = distRes.data
        topUsers.value = topRes.data.items
      } catch (e) {
        console.error('加载仪表盘失败:', e)
      }
    }

    onMounted(() => {
      loadDashboard()
    })

    return {
      stats,
      articlesDistribution,
      topUsers
    }
  }
}
</script>

<style scoped>
.dashboard {
  animation: fadeIn .3s ease;
}

h2 {
  margin-top: 0;
  color: #333;
  border-bottom: 3px solid var(--card-accent);
  padding-bottom: 12px;
  margin-bottom: 25px;
}

h3 {
  color: #333;
  margin-bottom: 15px;
  font-size: 16px;
}

/* 指标卡片 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

/* 图表区 */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: var(--card-shadow);
  border-left: 4px solid var(--card-accent);
}

.chart {
  height: 250px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

/* 柱状图 */
.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: 10px;
  width: 100%;
  height: 100%;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bar {
  width: 100%;
  background: linear-gradient(135deg, var(--card-accent), rgba(0,196,140,0.6));
  border-radius: 4px 4px 0 0;
  min-height: 20px;
  transition: all .2s ease;
}

.bar:hover {
  opacity: 0.8;
  transform: translateY(-3px);
}

.bar-item .label {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
}

.bar-item .value {
  font-size: 13px;
  font-weight: 600;
  color: var(--card-accent);
  margin-top: 2px;
}

/* 饼图 */
.pie-chart {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 30px;
}

.pie-item {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
}

.pie-item.published {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
}

.pie-item.draft {
  background: linear-gradient(135deg, #ff9800, #ffb74d);
}

.pie-label {
  font-size: 13px;
  opacity: 0.9;
}

.pie-value {
  font-size: 28px;
  margin-top: 5px;
}

/* 待办统计 */
.todo-stats {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: var(--card-shadow);
  margin-bottom: 30px;
  border-left: 4px solid var(--card-accent);
}

.progress-bar {
  width: 100%;
  height: 30px;
  background: #f0f0f0;
  border-radius: 15px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--card-accent), rgba(0,196,140,0.6));
  transition: width .3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.progress-text {
  font-size: 13px;
  color: #666;
  text-align: right;
}

/* 活跃用户表 */
.active-users {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: var(--card-shadow);
  border-left: 4px solid var(--card-accent);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

.users-table thead {
  background: rgba(0,196,140,0.1);
  border-bottom: 2px solid rgba(0,196,140,0.2);
}

.users-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

.users-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.users-table tbody tr:hover {
  background: rgba(0,196,140,0.03);
}

.badge {
  display: inline-block;
  background: var(--card-accent);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

</style>
