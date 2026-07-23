<template>
  <div class="bulletin-create">
    <header class="create-head">
      <p class="create-prompt">公告栏 · NEW</p>
      <h2 class="create-title">发布平台公告</h2>
      <p class="create-desc">支持 Markdown 格式，发布后用户可见</p>
    </header>

    <n-form label-placement="top" class="create-form matrix-panel">
      <n-form-item label="公告标题" required class="create-field">
        <n-input
          v-model:value="form.title"
          class="create-title-input"
          placeholder="输入公告标题"
          maxlength="256"
          show-count
        />
      </n-form-item>

      <n-form-item label="公告内容" required class="create-field">
        <n-input
          v-model:value="form.content"
          class="create-content-input"
          type="textarea"
          placeholder="支持 Markdown 格式"
          :autosize="{ minRows: 12, maxRows: 28 }"
        />
      </n-form-item>

      <div class="create-footer">
        <label class="create-switch">
          <n-switch v-model:value="form.is_active" size="small" />
          <span>立即发布（激活）</span>
        </label>
        <div class="create-actions">
          <n-button class="btn-cancel" @click="$router.push('/bulletin')">取消</n-button>
          <n-button class="btn-publish" type="primary" :loading="saving" @click="submit">
            发布公告
          </n-button>
        </div>
      </div>
    </n-form>

    <div v-if="previewHtml" class="preview-section matrix-panel">
      <div class="matrix-section-head">
        <span class="link-code">PRV</span>
        <h3>预览</h3>
      </div>
      <div class="preview-body markdown-body" v-html="previewHtml"></div>
    </div>
  </div>
</template>

<script>
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NForm, NFormItem, NInput, NButton, NSwitch, useMessage } from 'naive-ui'
import { platformAdmin } from '@/services/admin'

export default {
  name: 'BulletinCreate',
  components: { NForm, NFormItem, NInput, NButton, NSwitch },
  setup() {
    const router = useRouter()
    const message = useMessage()
    const reloadBulletinList = inject('reloadBulletinList', null)
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
        if (typeof reloadBulletinList === 'function') await reloadBulletinList()
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
.bulletin-create {
  width: 100%;
  max-width: none;
  padding: 20px 28px 36px;
  box-sizing: border-box;
  font-family: "M PLUS Rounded 1c", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.create-head {
  margin-bottom: 18px;
}
.create-prompt {
  margin: 0 0 6px;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: #6b7280;
  font-family: "JetBrains Mono", "Fira Code", monospace;
}
.create-title {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #f3f4f6;
  letter-spacing: 0.01em;
}
.create-desc {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}

.create-form {
  margin-bottom: 16px;
  width: 100%;
  max-width: none;
  padding: 20px 22px 18px !important;
}

.create-field {
  margin-bottom: 14px !important;
}

.create-form :deep(.n-form-item-label) {
  color: #d1d5db !important;
  font-weight: 500 !important;
  font-size: 13px !important;
}

.create-title-input :deep(.n-input) {
  --n-height: 42px !important;
  --n-font-size: 14px !important;
  --n-color: rgba(255, 255, 255, 0.03) !important;
  --n-color-focus: rgba(255, 255, 255, 0.05) !important;
  --n-text-color: #ffffff !important;
  --n-placeholder-color: rgba(156, 163, 175, 0.75) !important;
  --n-border: 1px solid rgba(255, 255, 255, 0.1) !important;
  --n-border-hover: 1px solid rgba(16, 185, 129, 0.3) !important;
  --n-border-focus: 1px solid rgba(16, 185, 129, 0.4) !important;
  --n-box-shadow-focus: 0 0 0 2px rgba(16, 185, 129, 0.12) !important;
  background: rgba(255, 255, 255, 0.03) !important;
  border-radius: 8px !important;
}

.create-title-input :deep(.n-input__input-el),
.create-title-input :deep(input) {
  height: 42px !important;
  font-size: 14px !important;
  color: #ffffff !important;
}

.create-title-input :deep(.n-input__count),
.create-title-input :deep(.n-input-word-count) {
  font-size: 12px !important;
  color: #9ca3af !important;
  opacity: 1 !important;
}

.create-content-input :deep(.n-input) {
  --n-color: rgba(255, 255, 255, 0.03) !important;
  --n-color-focus: rgba(255, 255, 255, 0.05) !important;
  --n-text-color: #e5e7eb !important;
  --n-placeholder-color: rgba(156, 163, 175, 0.75) !important;
  --n-border: 1px solid rgba(255, 255, 255, 0.1) !important;
  --n-border-hover: 1px solid rgba(16, 185, 129, 0.3) !important;
  --n-border-focus: 1px solid rgba(16, 185, 129, 0.4) !important;
  --n-box-shadow-focus: 0 0 0 2px rgba(16, 185, 129, 0.12) !important;
  background: rgba(255, 255, 255, 0.03) !important;
  border-radius: 8px !important;
}

.create-content-input :deep(textarea),
.create-content-input :deep(.n-input__textarea-el) {
  min-height: 280px !important;
  font-size: 14px !important;
  line-height: 1.65 !important;
  color: #e5e7eb !important;
  font-family: "M PLUS Rounded 1c", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif !important;
}

.create-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 6px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: wrap;
}

.create-switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #d1d5db;
  cursor: pointer;
  user-select: none;
}

.create-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.btn-publish {
  height: 38px !important;
  padding: 0 20px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  border-radius: 8px !important;
  background: #10b981 !important;
  color: #0a0f14 !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
}

.btn-publish:hover {
  filter: brightness(1.05);
  box-shadow: 0 0 14px rgba(16, 185, 129, 0.35) !important;
}

.btn-cancel {
  height: 38px !important;
  padding: 0 16px !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  border-radius: 8px !important;
  background: rgba(107, 114, 128, 0.12) !important;
  color: #d1d5db !important;
  border: 1px solid rgba(107, 114, 128, 0.28) !important;
}

.btn-cancel:hover {
  background: rgba(107, 114, 128, 0.2) !important;
  border-color: rgba(107, 114, 128, 0.4) !important;
}

.preview-section {
  width: 100%;
  max-width: none;
  padding: 16px 18px !important;
}
.preview-section h3 {
  margin: 0;
  font-size: 1rem;
  color: #9ca3af;
}
.preview-body {
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  margin-top: 10px;
  color: #e5e7eb;
}
</style>
