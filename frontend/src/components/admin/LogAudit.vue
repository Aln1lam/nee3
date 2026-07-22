<template>
  <div class="log-audit">
    
    <div class="action-bar">
      <input 
        v-model="searchText" 
        placeholder="搜索日志（操作、对象）..." 
        class="search-input"
        @keyup.enter="loadLogs"
      />
      <select v-model="filterAction" class="filter-select" @change="loadLogs">
        <option value="">全部操作</option>
        <option value="login">登录</option>
        <option value="logout">登出</option>
        <option value="register">注册</option>
        <option value="create">创建</option>
        <option value="update">更新</option>
        <option value="delete">删除</option>
        <option value="admin">管理员操作</option>
      </select>
      <select v-model="filterTarget" class="filter-select" @change="loadLogs">
        <option value="">全部对象</option>
        <option value="session">会话</option>
        <option value="user">用户</option>
        <option value="profile">个人资料</option>
        <option value="article">文章</option>
        <option value="team">团队</option>
        <option value="game">竞赛</option>
        <option value="resource">资源</option>
      </select>
      <button class="btn-primary" @click="loadLogs">搜索</button>
      <button class="btn-secondary" @click="loadLogs">刷新</button>
      <div class="delete-controls">
        <div class="month-group">
          <label>起始月
            <template v-if="monthOptions.length">
              <select v-model="startMonth" class="month-input">
                <option v-for="m in monthOptions" :key="m" :value="m">{{ m.replace('-', '年') + '月' }}</option>
              </select>
            </template>
            <template v-else>
              <input type="month" v-model="startMonth" class="month-input" />
            </template>
          </label>
        </div>
        <div class="month-group">
          <label>结束月
            <template v-if="monthOptions.length">
              <select v-model="endMonth" class="month-input">
                <option v-for="m in monthOptions" :key="m" :value="m">{{ m.replace('-', '年') + '月' }}</option>
              </select>
            </template>
            <template v-else>
              <input type="month" v-model="endMonth" class="month-input" />
            </template>
          </label>
        </div>
        <!-- 预览功能已移除（不再需要） -->
        <button class="btn-danger" @click="confirmDeleteByMonths">按月删除</button>
      </div>
    </div>

    <div class="logs-stats">
      <div class="stat-card">
        <div class="stat-label">24小时操作数</div>
        <div class="stat-value">{{ stats.today_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">本周操作数</div>
        <div class="stat-value">{{ stats.week_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">本月操作数</div>
        <div class="stat-value">{{ stats.month_count }}</div>
      </div>
    </div>

    <table class="logs-table">
      <thead>
        <tr>
          <th>时间</th>
          <th>操作人</th>
          <th>操作类型</th>
          <th>对象类型</th>
          <th>对象名称</th>
          <th>IP地址</th>
          <th>状态</th>
          <th>详情</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td class="time">{{ formatDate(log.created_at) }}</td>
          <td class="actor">{{ log.actor_name || log.actor_id || '系统' }}</td>
          <td>
            <span :class="['action-badge', getActionClass(log.action)]">
              {{ getActionLabel(log.action) }}
            </span>
          </td>
          <td>
            <span :class="['target-badge', getTargetClass(log.target_type)]">{{ getTargetLabel(log.target_type) }}</span>
          </td>
          <td class="description">{{ formatTargetName(log) }}</td>
          <td class="ip">{{ log.ip_address || '-' }}</td>
          <td>
            <span :class="['status-badge', log.status === 'success' ? 'success' : 'failed']">
              {{ log.status === 'success' ? '✓' : '✗' }}
            </span>
          </td>
          <td>
            <button class="btn-small" @click="showDetails(log)">查看</button>
            <button
              :disabled="deletingId === log.id"
              class="btn-small btn-danger"
              @click="confirmDelete(log)">
              <span v-if="deletingId === log.id">删除中...</span>
              <span v-else>删除</span>
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 分页 -->
    <div class="pagination">
      <button @click="currentPage = Math.max(1, currentPage - 1)" :disabled="currentPage <= 1">上一页</button>
      <span>第 {{ currentPage }} / 共 {{ totalPages }} 页</span>
      <button @click="currentPage = Math.min(totalPages, currentPage + 1)" :disabled="currentPage >= totalPages">下一页</button>
    </div>

    <!-- 详情模态框 -->
    <div v-if="showDetailsModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>日志详情</h3>
        <div class="details-grid">
          <div class="detail-item">
            <span class="label">操作ID</span>
            <span class="value">{{ detailLog.id }}</span>
          </div>
          <div class="detail-item">
            <span class="label">时间</span>
            <span class="value">{{ formatDate(detailLog.created_at) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">操作人</span>
            <span class="value">{{ detailLog.actor_name || '系统' }} (ID: {{ detailLog.actor_id || '-' }})</span>
          </div>
          <div class="detail-item">
            <span class="label">操作类型</span>
            <span class="value">{{ getActionLabel(detailLog.action) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">对象类型</span>
            <span class="value"><span :class="['target-badge', getTargetClass(detailLog.target_type)]">{{ getTargetLabel(detailLog.target_type) }}</span></span>
          </div>
          <div class="detail-item">
            <span class="label">对象ID</span>
            <span class="value">{{ detailLog.target_id || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">对象名称</span>
            <span class="value">{{ detailLog.target_name || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">IP地址</span>
            <span class="value">{{ detailLog.ip_address || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">状态</span>
            <span class="value">{{ detailLog.status === 'success' ? '成功' : '失败' }}</span>
          </div>
        </div>
        <div class="detail-full">
          <span class="label">原始日志 (JSON)</span>
          <div class="value"><pre style="white-space:pre-wrap;word-break:break-word">{{ JSON.stringify(detailLog, null, 2) }}</pre></div>
        </div>
        <div class="form-actions">
          <button class="btn-primary" @click="closeModal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { platformAdmin as adminApi } from '@/services/admin'

export default {
  name: 'LogAudit',
  setup() {
    const logs = ref([])
    const searchText = ref('')
    const filterAction = ref('')
    const filterTarget = ref('')
    const currentPage = ref(1)
    const perPage = ref(10)
    const total = ref(0)
    const totalPages = computed(() => {
      return perPage.value > 0 ? Math.max(1, Math.ceil(total.value / perPage.value)) : 1
    })
    const showDetailsModal = ref(false)
    const detailLog = ref({})
    const stats = ref({
      today_count: 0,
      week_count: 0,
      month_count: 0
    })
    const startMonth = ref('')
    const endMonth = ref('')
    const monthOptions = ref([])
    let message
    try {
      message = useMessage()
    } catch (e) {
      // 如果没有 MessageProvider（防止运行时抛错），回退为控制台函数
      message = {
        info: (t) => console.info('[message.info]', t),
        success: (t) => console.log('[message.success]', t),
        warning: (t) => console.warn('[message.warning]', t),
        error: (t) => console.error('[message.error]', t)
      }
    }
    const deletingId = ref(null)

    async function loadLogs() {
      try {
        const res = await adminApi.getLogs({
          page: currentPage.value,
          per_page: perPage.value,
          search: searchText.value,
          action: filterAction.value,
          target: filterTarget.value,
        })
        logs.value = res.data.items || []
        // 更新分页元数据
        total.value = res.data.total || 0
        if (res.data.per_page) perPage.value = res.data.per_page
        if (res.data.page) currentPage.value = res.data.page
        // 同时加载统计数据
        loadStats()
      } catch (e) {
        console.error('加载日志失败:', e)
        // 更友好的错误提示，处理会话过期场景
        const errMsg = (e && e.response && (e.response.data && (e.response.data.error || e.response.data.msg))) || e.message || '加载日志失败'
        if (/(token\s*expired|expired token|token expired|unauthorized|401)/i.test(errMsg) || e?.response?.status === 401) {
          message.error('加载失败：登录已过期，请重新登录')
          try {
            localStorage.removeItem('neepu_token')
            localStorage.removeItem('token')
          } catch (_) { /* ignore */ }
          setTimeout(() => { window.location.href = '/' }, 1200)
        } else {
          message.error(`加载日志失败：${errMsg}`)
        }
      }
    }

    async function loadStats() {
      try {
        const res = await adminApi.getLogsStats()
        stats.value = res.data
      } catch (e) {
        console.error('加载统计失败:', e)
      }
    }

    function getActionLabel(action) {
      const labels = {
        'create': '创建',
        'update': '更新',
        'delete': '删除',
        'view': '查看',
        'login': '登录',
        'logout': '登出',
        'register': '注册',
        'export': '导出',
        'admin_update': '管理员更新',
        'admin_delete': '管理员删除',
        'todo_distribute': '分发代办',
        'todo': '代办操作'
      }
      return labels[action] || action
    }

    function getActionClass(action) {
      if (!action) return 'default'
      if (action.startsWith('admin')) return 'admin'
      if (action === 'todo_distribute' || action.startsWith('todo')) return 'todo'
      return {
        'create': 'create',
        'update': 'update',
        'delete': 'delete',
        'login': 'login',
        'logout': 'logout',
        'register': 'register',
        'export': 'export',
        'view': 'view'
      }[action] || 'default'
    }

    function getTargetLabel(target) {
      const labels = {
        'session': '会话',
        'user': '用户',
        'profile': '个人资料',
        'article': '文章',
        'team': '团队',
        'game': '竞赛',
        'resource': '资源',
        'announcement': '公告',
        'carousel': '轮播图',
        'todo': '代办',
        'scoreboard': '排行榜',
        'submission': '提交',
        'ctf': 'CTF',
        'system_config': '系统配置'
      }
      return labels[target] || (target || '-')
    }

    function getTargetClass(target) {
      if (!target) return ''
      const map = {
        'todo': 'target-todo',
        'announcement': 'target-announcement',
        'carousel': 'target-carousel',
        'user': 'target-user',
        'team': 'target-team',
        'game': 'target-game',
        'submission': 'target-submission'
      }
      return map[target] || ''
    }

    function formatDate(dateStr) {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    function formatTargetName(log) {
      if (!log || !log.target_name) return '-'
      const name = log.target_name
      // 如果形式为 "prefix: rest"，尝试把 prefix 翻成中文
      try {
        // 尝试通过在字符串中查找已知英文对象类型并替换为中文
        const map = {
          'session': '会话',
          'user': '用户',
          'profile': '个人资料',
          'article': '文章',
          'team': '团队',
          'game': '竞赛',
          'resource': '资源',
          'announcement': '公告',
          'carousel': '轮播图',
          'todo': '代办',
          'scoreboard': '排行榜',
          'submission': '提交',
          'ctf': 'CTF',
          'system_config': '系统配置'
        }
        let out = name
        for (const key in map) {
          // 匹配像 "carousel:" 或 "carousel："，并替换为中文标签和中文冒号
          const re = new RegExp('\\b' + key + '\\s*[:：]', 'i')
          if (re.test(out)) {
            out = out.replace(re, map[key] + '：')
            break
          }
          // 也尝试匹配 " key " 后直接跟标识（例如 "查看 carousel: x" 中的 carousel）
          const re2 = new RegExp('\\b' + key + '\\b', 'i')
          if (re2.test(out)) {
            // 只在未替换冒号形式时，将首个出现的 key 替换为中文
            out = out.replace(re2, map[key])
            break
          }
        }
        // 返回替换后的结果
        // 进一步将已知的后缀标识翻译为中文展示
        try {
          const suffixMap = {
            'carousel_list': '轮播图列表',
            'announcements_list': '公告列表',
            'announcements': '公告列表',
            'carousel': '轮播图'
          }
          for (const key in suffixMap) {
            const reSuf = new RegExp('\\b' + key + '\\b', 'i')
            if (reSuf.test(out)) {
              out = out.replace(reSuf, suffixMap[key])
              break
            }
          }
        } catch (e) {}
        return out
      } catch (e) {}
      return name
    }

    function showDetails(log) {
      detailLog.value = { ...log }
      showDetailsModal.value = true
    }

    async function confirmDelete(log) {
      const id = log && log.id
      if (!id) return message.warning('无效的日志')
      if (!window.confirm(`确定删除日志 id=${id} ? 此操作不可恢复`)) return
      try {
        deletingId.value = id
        const res = await adminApi.deleteLog(id)
        if (res && (res.status === 200 || res.status === 204) ) {
          message.success(`删除成功: ${id}`)
        } else if (res && res.data && res.data.deleted_id) {
          message.success(`删除成功: ${res.data.deleted_id}`)
        } else {
          message.info('删除请求已发送，可能部分被后台处理')
        }
        await loadLogs()
        closeModal()
      } catch (e) {
        console.error('删除失败', e)
        const msg = (e && e.response && (e.response.data && (e.response.data.error || e.response.data.msg))) || e.message || '删除失败'
        if (/(token\s*expired|expired token|token expired)/i.test(msg)) {
          message.error('删除失败：登录已过期，请重新登录')
          localStorage.removeItem('neepu_token')
          localStorage.removeItem('token')
          setTimeout(() => { window.location.href = '/' }, 1200)
        } else {
          message.error(`删除失败：${msg}`)
        }
      } finally {
        deletingId.value = null
      }
    }

    // 预览功能已移除 - 保留空位以便将来扩展

    async function confirmDeleteByMonths() {
      if (!startMonth.value || !endMonth.value) return message.warning('请选择起始月与结束月')
      if (startMonth.value > endMonth.value) return message.warning('起始月不能晚于结束月')
      if (!window.confirm(`确定删除 ${startMonth.value} 至 ${endMonth.value} 整月范围内的所有日志？此操作不可恢复`)) return
      try {
        const res = await adminApi.deleteLogsByMonths(startMonth.value, endMonth.value, false)
        const deleted = (res && res.data && res.data.deleted) || 0
        message.success(`已删除 ${deleted} 条日志`)
        loadLogs()
      } catch (e) {
        console.error(e)
        const msg = (e && e.response && (e.response.data && (e.response.data.error || e.response.data.msg))) || e.message || '删除失败'
        if (/(token\s*expired|expired token|token expired)/i.test(msg)) {
          message.error('删除失败：登录已过期，请重新登录')
          localStorage.removeItem('neepu_token')
          localStorage.removeItem('token')
          setTimeout(() => { window.location.href = '/' }, 1200)
        } else {
          message.error(`删除失败：${msg}`)
        }
      }
    }

    function closeModal() {
      showDetailsModal.value = false
      detailLog.value = {}
    }

    onMounted(() => {
      loadLogs()
      // load available months for selection
      adminApi.getLogMonths().then(res => {
        if (res && res.data && Array.isArray(res.data.months)) {
          monthOptions.value = res.data.months
          if (!startMonth.value && monthOptions.value.length) startMonth.value = monthOptions.value[0]
          if (!endMonth.value && monthOptions.value.length) endMonth.value = monthOptions.value[monthOptions.value.length - 1]
        }
      }).catch(err => {
        console.warn('加载月份列表失败', err)
      })
    })

    // 当页码变化时自动重新加载
    watch(currentPage, (newPage, oldPage) => {
      if (newPage < 1) currentPage.value = 1
      if (newPage > totalPages.value) currentPage.value = totalPages.value
      if (newPage !== oldPage) loadLogs()
    })

    return {
      logs,
      searchText,
      filterAction,
      filterTarget,
      currentPage,
      perPage,
      total,
      totalPages,
      showDetailsModal,
      detailLog,
      stats,
      monthOptions,
      startMonth,
      endMonth,
      deletingId,
      loadLogs,
      getActionLabel,
      getActionClass,
      getTargetLabel,
      getTargetClass,
      formatDate,
      formatTargetName,
      showDetails,
      confirmDeleteByMonths,
      confirmDelete,
      closeModal
    }
  }
}
</script>

<style scoped>
h2 {
  margin-top: 0;
  color: #333;
  border-bottom: 3px solid var(--card-accent);
  padding-bottom: 12px;
  margin-bottom: 20px;
}

.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-input, .filter-select {
  padding: 10px 12px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  font-size: 13px;
  background: var(--gradient-card-bg, var(--card-bg));
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.btn-primary, .btn-secondary {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all .2s ease;
}

.btn-primary {
  background: var(--card-accent);
  color: white;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-primary:hover, .btn-secondary:hover {
  opacity: 0.9;
}

.logs-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--gradient-card-bg, var(--card-bg));
  padding: 15px;
  border-radius: 8px;
  box-shadow: var(--card-shadow);
  border: 1px solid rgba(0,0,0,0.06);
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--card-accent);
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--card-shadow);
  margin-bottom: 20px;
  font-size: 12px;
}

.logs-table thead {
  background: rgba(0,196,140,0.1);
  border-bottom: 2px solid rgba(0,196,140,0.2);
}

.logs-table th {
  padding: 10px;
  text-align: left;
  font-weight: 600;
  color: #333;
  font-size: 12px;
}

.logs-table td {
  padding: 10px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

/* 强制日志表格单元格文字为深色，避免在某些主题下看不见 */
.logs-table td, .logs-table .description {
  color: #333;
}

.action-badge {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 6px;
  background: #f3f6f8;
  color: #2d3748;
  font-weight: 600;
  font-size: 12px;
  border: 1px solid rgba(0,0,0,0.06);
}

/* 保持所有子类样式一致（统一视觉） */
.action-badge.create, .action-badge.update, .action-badge.delete, .action-badge.login,
.action-badge.logout, .action-badge.register, .action-badge.export, .action-badge.admin,
.action-badge.todo {
  background: #f3f6f8;
  color: #2d3748;
  border-color: rgba(0,0,0,0.06);
}

.logs-table tbody tr:hover {
  background: rgba(0,196,140,0.03);
}

.time {
  min-width: 140px;
}

.actor {
  min-width: 100px;
}

.id {
  font-family: monospace;
  font-size: 11px;
}

.ip {
  font-family: monospace;
  font-size: 11px;
}

.action-badge, .target-badge {
  display: inline-block;
  padding: 3px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.action-badge.create {
  background: #e8f5e9;
  color: #2e7d32;
}

.action-badge.update {
  background: #e3f2fd;
  color: #1565c0;
}

.action-badge.delete {
  background: #ffebee;
  color: #c62828;
}

.action-badge.login {
  background: #f3e5f5;
  color: #7b1fa2;
}

.action-badge.register {
  background: #e8f5e9;
  color: #388e3c;
}

.action-badge.logout {
  background: #eceff1;
  color: #546e7a;
}

.action-badge.admin {
  background: #fff8e1;
  color: #f57f17;
}

.target-badge {
  background: #fff3e0;
  color: #f57c00;
}

/* 轻微区分不同对象类型的浅色背景（保持统一形状） */
.target-todo { background: #fff7e6; color: #ff8c00; border-color: rgba(255,140,0,0.12); }
.target-announcement { background: #f0fff4; color: #00a85a; border-color: rgba(0,168,90,0.08); }
.target-carousel { background: #f0f7ff; color: #1677ff; border-color: rgba(22,119,255,0.08); }
.target-user { background: #fff0f6; color: #c41d7f; border-color: rgba(196,29,127,0.06); }
.target-team { background: #fffaf0; color: #d48806; border-color: rgba(212,136,6,0.06); }
.target-game { background: #f7fff6; color: #07c160; border-color: rgba(7,193,96,0.06); }
.target-submission { background: #fff9f0; color: #fa8c16; border-color: rgba(250,140,22,0.06); }

.status-badge {
  display: inline-block;
  width: 20px;
  height: 20px;
  text-align: center;
  line-height: 20px;
  border-radius: 50%;
  font-size: 12px;
}

.status-badge.success {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.failed {
  background: #ffebee;
  color: #c62828;
}

.user-agent {
  font-size: 11px;
  color: #888;
  word-break: break-all;
}

.btn-small {
  padding: 4px 8px;
  border: none;
  border-radius: 3px;
  background: #2196f3;
  color: white;
  cursor: pointer;
  font-size: 11px;
  transition: all .2s ease;
}

.btn-small:hover {
  opacity: 0.9;
}

/* 删除相关样式 */
.delete-controls {
  margin-left: auto;
  display: flex;
  gap: 8px;
  align-items: center;
}
.month-group label {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #555;
}
.month-input {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(0,0,0,0.08);
  background: var(--gradient-card-bg, var(--card-bg));
  margin-top: 6px;
}
.btn-danger {
  background: #e55353;
  color: #fff;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-outline {
  background: transparent;
  border: 1px solid rgba(0,0,0,0.08);
  color: #333;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-outline:hover, .btn-danger:hover {
  opacity: 0.92;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 12px;
  border: 1px solid var(--card-accent);
  border-radius: 4px;
  background: var(--gradient-card-bg, var(--card-bg));
  color: var(--card-accent);
  cursor: pointer;
  transition: all .2s ease;
}

.pagination button:hover:not(:disabled) {
  background: var(--card-accent);
  color: white;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--gradient-card-bg, var(--card-bg));
  padding: 25px;
  border-radius: 10px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-item .label {
  font-weight: 600;
  color: #666;
  font-size: 12px;
  margin-bottom: 4px;
}

.detail-item .value {
  color: #333;
  font-size: 13px;
  word-break: break-all;
}

.detail-full {
  margin-bottom: 20px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.detail-full .label {
  font-weight: 600;
  color: #666;
  font-size: 12px;
  margin-bottom: 8px;
  display: block;
}

.detail-full .value {
  color: #333;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.form-actions {
  display: flex;
  gap: 10px;
}

.btn-primary {
  flex: 1;
}
</style>
