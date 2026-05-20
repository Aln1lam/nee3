<template>
  <div style="padding:16px;max-width:900px;">
    <n-button @click="$router.back()">取消</n-button>
    <h2>{{ isNew ? '撰写文章' : '编辑文章' }}</h2>

    <n-form>
      <n-form-item label="标题">
        <n-input v-model:value="title" />
      </n-form-item>
      <n-form-item label="摘要">
        <n-input v-model:value="summary" />
      </n-form-item>
      <n-form-item label="选择标签">
        <n-select v-model:value="tags" :options="tagOptions" multiple clearable />
      </n-form-item>

      <n-form-item label="正文 (Markdown)">
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
          <input ref="fileInput" type="file" @change="onFileChange" />
          <n-button size="small" @click="triggerFile">上传并插入图片</n-button>
          <n-button size="small" @click="togglePreview">切换预览</n-button>
        </div>
        <textarea v-model="body" style="width:100%;height:320px;font-family:monospace;" />
      </n-form-item>

      <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px;">
        <n-button @click="$router.back()">取消</n-button>
        <n-button type="info" @click="save('draft')">保存草稿</n-button>
        <n-button type="primary" @click="save('published')">发布</n-button>
      </div>
    </n-form>

    <div v-if="preview" style="margin-top:24px;border-top:1px solid #eee;padding-top:12px">
      <h3>预览</h3>
      <div v-html="renderedHtml"></div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NForm, NFormItem, NInput, NSelect } from 'naive-ui'
import { TAGS } from '../services/tags'

export default {
  components: { NButton, NForm, NFormItem, NInput, NSelect },
  props: { id: { type: [String, Number], default: null } },
  setup(props) {
    const axios = inject('axios')
    const isNew = ref(!props.id)
    const title = ref('')
    const summary = ref('')
    const tags = ref([])
    const body = ref('')
    const preview = ref(false)
    const fileInput = ref(null)
    const renderedHtml = ref('')

    async function load() {
      if (!props.id) return
      try {
        const r = await axios.get('/api/articles/' + props.id)
          title.value = r.data.title
          summary.value = r.data.summary
          // backend stores tags as comma-separated string; convert to array for the select
          tags.value = (r.data.tags || '').split(',').map(s => s && s.trim()).filter(Boolean)
        body.value = r.data.body || ''
      } catch (e) { console.error('load article failed', e) }
    }

    function triggerFile() { fileInput.value && fileInput.value.click() }

    async function onFileChange(e) {
      const f = e.target.files && e.target.files[0]
      if (!f) return
      const fd = new FormData()
      fd.append('file', f)
      try {
        const r = await axios.post('/api/uploads/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        const url = r.data.url
        // insert markdown image at current cursor position (append for simplicity)
        body.value = body.value + '\n\n![' + (f.name || '') + '](' + url + ')\n'
      } catch (e) { console.error('upload failed', e) }
    }

    const tagOptions = TAGS.map(t => ({ label: t, value: t }))

    async function save(status) {
      // send tags as array of names; backend will join into a string
      const payload = { title: title.value, body: body.value, summary: summary.value, tags: tags.value, status }
      try {
        if (isNew.value) {
          const r = await axios.post('/api/articles/', payload)
          const id = r.data.id
          // navigate to detail and notify other components
          router.push('/knowledge/' + id)
          // dispatch article saved event for other components
          try {
            window.dispatchEvent(new CustomEvent('neepu_article_saved', { detail: { id } }))
          } catch (e) { /* ignore */ }
        } else {
          await axios.put('/api/articles/' + props.id, payload)
          router.push('/knowledge/' + props.id)
          try {
            window.dispatchEvent(new CustomEvent('neepu_article_saved', { detail: { id: props.id } }))
          } catch (e) { /* ignore */ }
        }
      } catch (e) { console.error('save failed', e) }
    }

    function togglePreview() {
      preview.value = !preview.value
      if (preview.value) renderMarkdown()
    }

    async function renderMarkdown() {
      // try to use marked if available, otherwise escape basic markdown (very small fallback)
      try {
        const marked = (await import('marked')).default
        renderedHtml.value = marked.parse(body.value || '')
      } catch (e) {
        // fallback: simple newline->br and escape
        renderedHtml.value = (body.value || '').replace(/&/g, '&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>')
      }
    }

    const router = useRouter()

    onMounted(load)
    return { isNew, title, summary, tags, tagOptions, body, preview, triggerFile, onFileChange, fileInput, save, renderedHtml, togglePreview }
  }
}
</script>

<style scoped>
textarea { font-family: monospace; padding:8px }
</style>
