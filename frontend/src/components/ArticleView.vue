<template>
  <div class="page-wrap">
    <n-button @click="$router.back()" class="back-btn">返回</n-button>

    <div v-if="loading" style="text-align: center; padding: 40px;">
      <n-spin />
    </div>

    <div v-else>
      <!-- 文章标题和元数据 -->
      <div v-if="article" class="article-header">
        <h1 class="article-title">{{ article.title }}</h1>
        <div class="article-meta">
          <span v-if="article.created_at">发布时间: {{ formatDate(article.created_at) }}</span>
          <span v-if="article.author_name">作者: {{ article.author_name }}</span>
        </div>
      </div>

      <!-- 主体内容：优先显示在线编辑 content；其后按顺序展示 loading、上传文件（或 markdown 文件），最后显示错误提示 -->
      <div class="article-body">
        <div class="article-panel">
        <template v-if="loadingContent">
          <div style="text-align: center; padding: 40px;">
            <n-spin />
          </div>
        </template>

        <template v-else-if="article?.content">
          <div class="article-content article-content--full">
            <div v-html="renderedContent"></div>
          </div>
        </template>

        <template v-else-if="fileUrl">
          <div class="article-file-wrap">
            <template v-if="fileIsPdf">
              <div class="viewer-stage">
                <div class="pdf-viewer-container">
                  <div class="pdf-toolbar">
                    <a :href="fileUrl" target="_blank" rel="noopener noreferrer" class="pdf-action-btn">
                      <span>🔗</span> 新窗口打开
                    </a>
                    <a :href="fileUrl" download class="pdf-action-btn">
                      <span>📥</span> 下载PDF
                    </a>
                  </div>
                  <div class="pdf-iframe-wrapper">
                    <iframe 
                      :src="fileUrl" 
                      class="pdf-iframe"
                      frameborder="0"
                      title="PDF查看器"
                    ></iframe>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="article-content article-content--full">
                <div v-html="renderedContent"></div>
              </div>
            </template>
          </div>
        </template>

        <template v-else>
          <div style="color: #d32f2f; padding: 16px; border: 1px solid #d32f2f; border-radius: 4px;">
            ⚠️ 文章内容加载失败，请重试
          </div>
        </template>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, inject, computed } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NSpin } from 'naive-ui'
import { marked } from 'marked'

export default {
  props: ['id'],
  components: { NButton, NSpin },
  setup(props) {
    const axios = inject('axios')
    const route = useRoute()

    const article = ref(null)
    const loading = ref(true)
    const loadingContent = ref(false)
    const fileUrl = ref('')
    const fileContent = ref('')
    const fileIsPdf = ref(false)

    // 获取文章详情
    onMounted(async () => {
      try {
        const id = props.id || route.params.id
        const res = await axios.get(`/api/articles/${id}`)
        article.value = res.data

        // 如果没有在线编辑的content，检查是否有上传的文件
        if (!article.value.content && article.value.resource_id) {
          // 直接使用 resource_id 构造文件访问 URL
          try {
            const fileRes = await axios.get(`/api/resources/${article.value.resource_id}`)
            const filename = fileRes.data.filename || ''
            
            // 使用 /api/resources/{id}/content 直接访问文件内容
            fileUrl.value = `/api/resources/${article.value.resource_id}/content`
            
            // 根据文件名判断是否为 PDF
            if (/\.pdf$/i.test(filename)) {
              fileIsPdf.value = true
            } else {
              await loadFileContent()
            }
          } catch (err) {
            console.error('获取文件资源失败:', err)
          }
        }
      } catch (err) {
        console.error('获取文章失败:', err)
      } finally {
        loading.value = false
      }
    })

    // 加载文件内容
    async function loadFileContent() {
      if (!fileUrl.value) return
      
      loadingContent.value = true
      try {
        const response = await axios.get(fileUrl.value)
        fileContent.value = response.data
      } catch (err) {
        console.error('文件加载失败:', err)
        fileContent.value = ''
      } finally {
        loadingContent.value = false
      }
    }

    // 计算渲染的内容
    const renderedContent = computed(() => {
      // 优先使用在线编辑的content
      let markdown = article.value?.content || fileContent.value || ''
      
      if (!markdown) return ''

      // 使用marked渲染markdown
      let html = marked.parse(markdown)

      // 处理图片路径：将相对路径转换为 /uploads/ 路径
      html = html.replace(/<img\s+src="(?!https?:\/\/|\/uploads\/)([^"]+)"/g, '<img src="/uploads/$1"')

      return html
    })

    // 格式化日期
    function formatDate(isoString) {
      if (!isoString) return ''
      return new Date(isoString).toLocaleDateString('zh-CN')
    }

    return {
      article,
      loading,
      loadingContent,
      fileUrl,
      fileIsPdf,
      renderedContent,
      formatDate
    }
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 24px 40px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}
.back-btn {
  margin-bottom: 16px;
}
.article-header {
  text-align: center;
  margin-bottom: 8px;
}
.article-title {
  margin: 8px 0 6px 0;
  font-size: 3rem;
  font-weight: 800;
}
.article-meta {
  color: #666;
  font-size: 13px;
  display: inline-flex;
  gap: 16px;
}
.article-body {
  display: block;
}
.article-content--full {
  width: 82%;
  max-width: 1000px;
  margin: 0 auto;
}
.article-file-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
}
.viewer-stage {
  width: 100%;
  min-height: 72vh;
  border: 1px solid rgba(0,0,0,0.06);
  padding: 0;
  margin: 18px 0 28px 0;
  box-sizing: border-box;
  background-color: #ffffff;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.pdf-viewer-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.pdf-toolbar {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #f5f5f5;
  border-bottom: 1px solid rgba(0,0,0,0.1);
}

.pdf-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #fff;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.pdf-action-btn:hover {
  background: #1976d2;
  color: #fff;
  border-color: #1976d2;
}

.pdf-action-btn span {
  font-size: 16px;
}

.pdf-iframe-wrapper {
  width: 100%;
  height: calc(100vh - 280px);
  min-height: 600px;
  background: #525659;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.pdf-container {
  width: 760px;
  max-width: 78%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 auto;
}

.article-content {
  font-size: 16px;
  line-height: 1.8;
  color: #333;
}

/* Article panel: white background for viewing/editing files */
.article-panel {
  background: #ffffff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(14,30,37,0.06);
  max-width: 1000px;
  margin: 0 auto;
}

:deep(.article-content h1) {
  font-size: 2em;
  margin: 0.83em 0;
  font-weight: bold;
}

:deep(.article-content h2) {
  font-size: 1.5em;
  margin: 0.75em 0;
  font-weight: bold;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

:deep(.article-content h3) {
  font-size: 1.25em;
  margin: 0.67em 0;
  font-weight: bold;
}

:deep(.article-content p) {
  margin: 1em 0;
}

:deep(.article-content code) {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

:deep(.article-content pre) {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 1em 0;
}

:deep(.article-content pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}

:deep(.article-content blockquote) {
  border-left: 4px solid #ddd;
  margin: 1em 0;
  padding-left: 1em;
  color: #666;
}

:deep(.article-content ul),
:deep(.article-content ol) {
  margin: 1em 0;
  padding-left: 2em;
}

:deep(.article-content li) {
  margin: 0.5em 0;
}

:deep(.article-content table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

:deep(.article-content th),
:deep(.article-content td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

:deep(.article-content th) {
  background-color: #f5f5f5;
  font-weight: bold;
}

:deep(.article-content img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 1em 0;
}

:deep(.article-content a) {
  color: #1976d2;
  text-decoration: none;
}

:deep(.article-content a:hover) {
  text-decoration: underline;
}

@media (max-width: 900px) {
  .article-content--full, .pdf-container {
    width: 92% !important;
    min-width: 0;
  }
  .article-title { font-size: 1.8rem; }
  .pdf-frame { height: calc(70vh); }
}
</style>
