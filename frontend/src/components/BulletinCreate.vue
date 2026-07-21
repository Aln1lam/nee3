<template>
  <MatrixShell
    prompt=""
    title="发布平台公告"
    subtitle="BULLETIN · NEW"
    page-prompt="发布公告 · NEW"
    page-title="发布平台公告"
    page-desc="支持 Markdown 格式，发布后用户可见"
  >
    <template #sidebar-footer>
      <router-link to="/bulletin" class="sidebar-link">
        <span class="link-code">BAK</span>
        <span>返回公告中心</span>
      </router-link>
    </template>

    <n-form label-placement="top" class="create-form matrix-panel">
      <n-form-item label="公告标题" required>
        <n-input v-model:value="form.title" placeholder="输入公告标题" maxlength="256" show-count />
      </n-form-item>
      <n-form-item label="公告内容" required>
        <n-input
          v-model:value="form.content"
          type="textarea"
          placeholder="支持 Markdown 格式"
          :rows="12"
        />
      </n-form-item>
      <n-form-item label="立即发布（激活）">
        <n-switch v-model:value="form.is_active" />
      </n-form-item>
      <div class="form-actions">
        <n-button type="primary" :loading="saving" @click="submit">发布公告</n-button>
        <n-button @click="$router.push('/bulletin')">取消</n-button>
      </div>
    </n-form>

    <div v-if="previewHtml" class="preview-section matrix-panel">
      <div class="matrix-section-head">
        <span class="link-code">PRV</span>
        <h3>预览</h3>
      </div>
      <div class="preview-body markdown-body" v-html="previewHtml"></div>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NForm, NFormItem, NInput, NButton, NSwitch, useMessage } from 'naive-ui'
import { MatrixShell } from '@/components/shared'
import { platformAdmin } from '@/services/admin'

export default {
  name: 'BulletinCreate',
  components: { NForm, NFormItem, NInput, NButton, NSwitch, MatrixShell },
  setup() {
    const router = useRouter()
    const message = useMessage()
    const saving = ref(false)
    const form = ref({ title: '', content: '', is_active: true })

    const previewHtml = computed(() => {
      if (!form.value.content.trim()) return ''
      try { return parseMarkdownSafe(form.value.content) } catch { return '' }
    })

    async function submit() {
      if (!form.value.title.trim()) {
        message.warning('请填写公告标题')
        return
      }
      if (!form.value.content.trim()) {
        message.warning('请填写公告内容')
        return
      }
      saving.value = true
      try {
        await platformAdmin.createAnnouncement({
          title: form.value.title.trim(),
          content: form.value.content.trim(),
          is_active: form.value.is_active,
        })
        message.success('公告发布成功')
        router.push('/bulletin')
      } catch (e) {
        message.error('发布失败: ' + (e.response?.data?.msg || '未知错误'))
      } finally {
        saving.value = false
      }
    }

    return { form, saving, previewHtml, submit }
  },
}
</script>

<style scoped>
.create-form { margin-bottom: 16px; max-width: none; width: 100%; }
.form-actions { display: flex; gap: 12px; }
.preview-section { max-width: none; width: 100%; }
.preview-section h3 { margin: 0; font-size: 1rem; color: var(--muted); }
.preview-body { padding: 16px; background: var(--hover); border-radius: var(--card-radius); margin-top: 12px; }
</style>
