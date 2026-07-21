<template>
  <div class="carousel-management">
    <div class="page-header">
      <n-button type="primary" @click="showAddModal = true">
        <template #icon><n-icon><Add /></n-icon></template>
        添加轮播图
      </n-button>
    </div>

    <!-- 轮播图列表 -->
    <div class="slides-grid">
      <n-card v-for="slide in slides" :key="slide.id" class="slide-card" :class="{ inactive: !slide.is_active }">
        <div class="slide-preview">
          <img :src="getFullUrl(slide.image_url)" :alt="slide.title || '轮播图'" @error="handleImageError" />
          <div class="slide-overlay">
            <n-space>
              <n-button size="small" @click="editSlide(slide)">编辑</n-button>
              <n-button size="small" type="error" @click="confirmDelete(slide)">删除</n-button>
            </n-space>
          </div>
        </div>
        <div class="slide-info">
          <div class="slide-title">{{ slide.title || '(无标题)' }}</div>
          <div class="slide-desc">{{ slide.description || '(无描述)' }}</div>
          <div class="slide-meta">
            <n-tag :type="slide.is_active ? 'success' : 'default'" size="small">
              {{ slide.is_active ? '已启用' : '已禁用' }}
            </n-tag>
            <span class="sort-order">排序: {{ slide.sort_order }}</span>
          </div>
          <div class="slide-link" v-if="slide.link_url">
            <n-icon><LinkOutline /></n-icon>
            <a :href="slide.link_url" target="_blank">{{ slide.link_url }}</a>
          </div>
        </div>
      </n-card>

      <n-card v-if="slides.length === 0" class="empty-card">
        <n-empty description="暂无轮播图，点击上方按钮添加" />
      </n-card>
    </div>

    <!-- 添加/编辑弹窗 -->
    <n-modal v-model:show="showAddModal" preset="dialog" :title="editingSlide ? '编辑轮播图' : '添加轮播图'" style="width: 600px;">
      <n-form :model="formData" label-placement="left" label-width="80px">
        <n-form-item label="上传图片" required>
          <n-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :max="1"
            accept="image/*"
            @finish="handleUploadFinish"
            :show-file-list="false"
          >
            <n-button type="primary">选择图片上传</n-button>
          </n-upload>
          <span v-if="formData.image_url" class="upload-success">✓ 已上传</span>
        </n-form-item>
        <n-form-item label="图片预览" v-if="formData.image_url">
          <div class="preview-box">
            <img :src="getFullUrl(formData.image_url)" alt="预览" @error="handlePreviewError" />
          </div>
        </n-form-item>
        <n-form-item label="标题">
          <n-input v-model:value="formData.title" placeholder="轮播图标题（可选）" />
        </n-form-item>
        <n-form-item label="排序">
          <n-input-number v-model:value="formData.sort_order" :min="0" placeholder="数字越小越靠前" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="saveSlide" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { NButton, NCard, NModal, NForm, NFormItem, NInput, NInputNumber, NSwitch, NTag, NSpace, NIcon, NUpload, NEmpty, useMessage } from 'naive-ui'
import { Add, LinkOutline } from '@vicons/ionicons5'
import axios from 'axios'

const message = useMessage()
const slides = ref([])
const showAddModal = ref(false)
const editingSlide = ref(null)
const saving = ref(false)

const formData = ref({
  title: '',
  description: '',
  image_url: '',
  link_url: '',
  sort_order: 0,
  is_active: true
})

const token = computed(() => localStorage.getItem('neepu_token'))
const uploadUrl = '/api/uploads/upload-image/'
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${token.value}` }))

const getFullUrl = (url) => {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const base = axios && axios.defaults && axios.defaults.baseURL ? axios.defaults.baseURL.replace(/\/$/, '') : ''
  return (base ? base : '') + url
}

const fetchSlides = async () => {
  try {
    const res = await axios.get('/api/admin/platform/carousel', {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    slides.value = res.data
  } catch (e) {
    message.error('加载轮播图失败')
  }
}

const resetForm = () => {
  formData.value = {
    title: '',
    image_url: '',
    sort_order: slides.value.length,
    is_active: true
  }
  editingSlide.value = null
}

const editSlide = (slide) => {
  editingSlide.value = slide
  formData.value = { ...slide }
  showAddModal.value = true
}

const saveSlide = async () => {
  if (!formData.value.image_url) {
    message.warning('请先上传图片')
    return
  }
  
  saving.value = true
  try {
    if (editingSlide.value) {
      await axios.patch(`/api/admin/platform/carousel/${editingSlide.value.id}`, formData.value, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      message.success('更新成功')
    } else {
      await axios.post('/api/admin/platform/carousel', formData.value, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      message.success('添加成功')
    }
    showAddModal.value = false
    resetForm()
    fetchSlides()
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

const confirmDelete = async (slide) => {
  if (!confirm(`确定删除轮播图"${slide.title || '(无标题)'}"吗？`)) return
  
  try {
    await axios.delete(`/api/admin/platform/carousel/${slide.id}`, {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    message.success('删除成功')
    fetchSlides()
  } catch (e) {
    message.error('删除失败')
  }
}

const handleUploadFinish = ({ file, event }) => {
  try {
    const res = JSON.parse(event.target.response)
    if (res.url) {
      formData.value.image_url = res.url
      message.success('图片上传成功')
    }
  } catch (e) {
    message.error('上传失败')
  }
}

const handleImageError = (e) => {
  e.target.src = '/assets/avatar-placeholder.png'
}

const handlePreviewError = (e) => {
  e.target.style.display = 'none'
}

onMounted(() => {
  resetForm()
  fetchSlides()
})
</script>

<style scoped>
.carousel-management {
  padding: var(--fib-21);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  color: #333;
}

.slides-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.slide-card {
  overflow: hidden;
  transition: all 0.3s;
}

.slide-card.inactive {
  opacity: 0.6;
}

.slide-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.slide-preview {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: #f5f5f5;
}

.slide-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.slide-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.slide-preview:hover .slide-overlay {
  opacity: 1;
}

.slide-info {
  padding: 12px;
}

.slide-title {
  font-weight: 600;
  font-size: 16px;
  color: #333;
  margin-bottom: 4px;
}

.slide-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slide-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.sort-order {
  font-size: 12px;
  color: #999;
}

.slide-link {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 4px;
  overflow: hidden;
}

.slide-link a {
  color: #18a058;
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-card {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.upload-success {
  color: #18a058;
  margin-left: 12px;
  font-size: 14px;
}

.preview-box {
  width: 100%;
  max-height: 200px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.preview-box img {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
}
</style>
