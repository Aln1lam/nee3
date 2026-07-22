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
  font-size: 14px;
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

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.articles-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--card-shadow);
  margin-bottom: 20px;
}

.articles-table thead {
  background: rgba(0,196,140,0.1);
  border-bottom: 2px solid rgba(0,196,140,0.2);
}

.articles-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  font-size: 13px;
}

.articles-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  font-size: 13px;
}

.articles-table tbody tr:hover {
  background: rgba(0,196,140,0.03);
}

.title {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.badge.success {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge.warning {
  background: #fff3e0;
  color: #f57c00;
}

.badge.default {
  background: #f5f5f5;
  color: #666;
}

.actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all .2s ease;
}

.btn-small.view {
  background: #2196f3;
  color: white;
}

.btn-small.publish {
  background: #4caf50;
  color: white;
}

.btn-small.delete {
  background: #f44336;
  color: white;
}

.btn-small:hover {
  opacity: 0.9;
  transform: scale(1.05);
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
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #333;
}

.article-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  font-size: 12px;
  color: #666;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0,0,0,0.1);
}

.article-content {
  color: #333;
  line-height: 1.6;
  margin-bottom: 20px;
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
