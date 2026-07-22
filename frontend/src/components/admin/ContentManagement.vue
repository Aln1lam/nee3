<template>
  <div class="content-management">
    
    <div class="action-bar">
      <input 
        v-model="searchText" 
        placeholder="搜索文章（标题、作者）..." 
        class="search-input"
        @keyup.enter="loadArticles"
      />
      <select v-model="filterStatus" class="filter-select" @change="loadArticles">
        <option value="">全部状态</option>
        <option value="published">已发布</option>
        <option value="draft">草稿</option>
        <option value="archived">已归档</option>
      </select>
      <button class="btn-primary" @click="loadArticles">搜索</button>
      <button class="btn-secondary" @click="loadArticles">刷新</button>
    </div>

    <table class="articles-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>标题</th>
          <th>作者ID</th>
          <th>状态</th>
          <th>分类</th>
          <th>创建时间</th>
          <th>发布时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="article in articles" :key="article.id">
          <td>{{ article.id }}</td>
          <td class="title">{{ article.title }}</td>
          <td>{{ article.author_name || '未知作者' }}</td>
          <td>
            <span :class="['badge', getStatusClass(article.status)]">
              {{ getStatusLabel(article.status) }}
            </span>
          </td>
          <td>{{ article.category || '-' }}</td>
          <td>{{ formatDate(article.created_at) }}</td>
          <td>{{ formatDate(article.published_at) }}</td>
          <td class="actions">
            <button class="btn-small view" @click="openArticle(article.id)">查看</button>
            <button 
              v-if="article.status !== 'published'"
              class="btn-small publish" 
              @click="publishArticle(article.id)"
            >
              发布
            </button>
            <button class="btn-small delete" @click="deleteArticle(article.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 分页 -->
    <div class="pagination">
      <button @click="currentPage--" :disabled="currentPage <= 1">上一页</button>
      <span>第 {{ currentPage }} 页</span>
      <button @click="currentPage++">下一页</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import platformAdmin from '@/services/admin/platform'

export default {
  name: 'ContentManagement',
  setup() {
    const articles = ref([])
    const searchText = ref('')
    const filterStatus = ref('')
    const currentPage = ref(1)

    async function loadArticles() {
      try {
        const res = await platformAdmin.listArticles({
          page: currentPage.value,
          search: searchText.value,
          status: filterStatus.value,
        })
        articles.value = res.data.items || res.data
      } catch (e) {
        console.error('加载文章失败:', e)
        alert('加载文章失败')
      }
    }

    function getStatusLabel(status) {
      const labels = {
        'published': '已发布',
        'draft': '草稿',
        'archived': '已归档'
      }
      return labels[status] || status
    }

    function getStatusClass(status) {
      return {
        'published': 'success',
        'draft': 'warning',
        'archived': 'default'
      }[status] || 'default'
    }

    function openArticle(articleId) {
      // 在前端路由中打开文章详情页面
      window.open(`/knowledge/${articleId}`, '_blank')
    }

    async function publishArticle(articleId) {
      if (!confirm('确定发布此文章吗？')) return
      
      try {
        await platformAdmin.updateArticle(articleId, { status: 'published' })
        alert('发布成功')
        loadArticles()
      } catch (e) {
        console.error('发布失败:', e)
        alert('发布失败')
      }
    }

    async function deleteArticle(articleId) {
      if (!confirm('确定删除此文章吗？删除后不可恢复。')) return
      
      try {
        await platformAdmin.deleteArticle(articleId)
        alert('删除成功')
        loadArticles()
      } catch (e) {
        console.error('删除失败:', e)
        // 如果后端返回了响应，尽量把状态码和返回体显示出来，方便定位 HTML 重定向或错误页
        try {
          if (e && e.response) {
            const st = e.response.status
            let body = e.response.data
            if (typeof body !== 'string') {
              try { body = JSON.stringify(body) } catch (ee) { body = String(body) }
            }
            const short = body ? (body.length > 1000 ? body.slice(0, 1000) + '\n...[truncated]' : body) : ''
            alert(`删除失败: HTTP ${st}\n${short}`)
          } else {
            alert('删除失败: ' + (e.message || String(e)))
          }
        } catch (ee) {
          alert('删除失败')
        }
      }
    }

    function formatDate(dateStr) {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    onMounted(() => {
      loadArticles()
    })

    return {
      articles,
      searchText,
      filterStatus,
      currentPage,
      loadArticles,
      getStatusLabel,
      getStatusClass,
      openArticle,
      publishArticle,
      deleteArticle,
      formatDate
    }
  }
}
</script>

<style scoped>
.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input, .filter-select {
  height: 36px;
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  background: rgba(20, 26, 33, 0.72);
  color: #f3f4f6;
  box-sizing: border-box;
}

.search-input {
  flex: 1 1 220px;
  min-width: 200px;
  max-width: 420px;
}

.filter-select {
  flex: 0 0 auto;
  min-width: 140px;
  width: auto;
}

.btn-primary, .btn-secondary {
  flex: 0 0 auto !important;
  width: auto !important;
  padding: 8px 18px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  transition: background 0.15s, border-color 0.15s;
}

.btn-primary {
  background: rgba(16, 185, 129, 0.18);
  border-color: rgba(16, 185, 129, 0.4);
  color: #10b981;
}
.btn-primary:hover {
  background: rgba(16, 185, 129, 0.28);
}
.btn-secondary {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
  color: #e5e7eb;
}
.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
}

.articles-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(20, 26, 33, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 20px;
}

.articles-table thead {
  background: rgba(16, 185, 129, 0.06);
  border-bottom: 1px solid rgba(16, 185, 129, 0.18);
}

.articles-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #9ca3af;
  font-size: 13px;
}

.articles-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 13px;
  font-weight: 500;
  color: #e5e7eb;
}

.articles-table tbody tr:hover {
  background: rgba(16, 185, 129, 0.04);
}

.title {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #e5e7eb;
  font-weight: 500;
}

.badge {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid transparent;
}
.badge.success {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}
.badge.warning {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.3);
}
.badge.default {
  background: rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
  border-color: rgba(148, 163, 184, 0.28);
}

.actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.btn-small.view,
.btn-small.publish {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.28);
}
.btn-small.view:hover,
.btn-small.publish:hover {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}
.btn-small.delete {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.28);
}
.btn-small.delete:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  color: #e5e7eb;
  font-weight: 500;
}
.pagination button {
  padding: 8px 12px;
  border: 1px solid rgba(16, 185, 129, 0.35);
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
  cursor: pointer;
  font-weight: 600;
}
.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
