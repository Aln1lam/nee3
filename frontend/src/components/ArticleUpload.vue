<template>
  <div class="wiki-editor-page page-wrap">
    <n-button @click="$router.back()">取消</n-button>
    <h2>发布文章到知识库</h2>

    <div style="margin-top:16px">
      <n-form>
        <n-form-item label="文章标题" required>
          <n-input v-model:value="form.title" placeholder="请输入文章标题" />
        </n-form-item>

        <n-form-item label="选择标签">
          <n-select v-model:value="form.tags" :options="tagOptions" multiple clearable />
        </n-form-item>

        <n-form-item label="内容 (Markdown编辑)">
            <div class="editor-wrap">
              <div class="editor-topbar" style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <n-button size="small" @click="triggerImport">导入 MD</n-button>
                <input ref="importInput" type="file" accept=".md,text/markdown" style="display:none" @change="onImportFile" />
                <n-button size="small" @click="exportMarkdown">导出 MD</n-button>
                <n-button size="small" @click="exportHtml">导出 HTML</n-button>
                <div style="flex:1"></div>
                <div class="editor-status" style="color:#666;font-size:12px;">字数: {{ stats.words }} &nbsp; 行: {{ stats.lines }} &nbsp; 光标: {{ stats.cursor }}</div>
              </div>
              <div id="vditor-edit" class="vditor-host"></div>
            </div>
        </n-form-item>

        <n-form-item>
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <n-button size="small" @click="saveDraft" :loading="saving">保存草稿</n-button>
              <n-button @click="resetForm" style="margin-left:8px;">重置</n-button>
              <span style="margin-left:12px;color:#666;font-size:12px;">字数: {{ stats.words }} &nbsp; 行: {{ stats.lines }} &nbsp; 光标: {{ stats.cursor }}</span>
            </div>
            <div>
              <n-button class="publish-btn" type="primary" @click="publishArticle" :loading="saving">发布</n-button>
            </div>
          </div>
        </n-form-item>
      </n-form>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NForm, NFormItem, NInput, NSelect, NDivider, useMessage } from 'naive-ui'
import Vditor from 'vditor'
import 'vditor/dist/index.css'
// Load Vditor SVG icon sprite so <use xlink:href="#vditor-icon-..."> works
import 'vditor/dist/js/icons/material.js'
import { TAGS } from '../services/tags'

export default {
  components: { NButton, NForm, NFormItem, NInput, NSelect, NDivider },
  setup() {
    const axios = inject('axios')
    const router = useRouter()
    const message = useMessage()

    const vditor = ref(null)

    // 在线编辑表单
    const form = ref({
      title: '',
      tags: [],
      content: ''
    })

    const importInput = ref(null)
    const saving = ref(false)

    const stats = ref({ words: 0, lines: 0, cursor: '1:1' })

    const tagOptions = TAGS.map(t => ({ label: t, value: t }))

    // 初始化Vditor编辑器
    let statsTimer = null
    let toolbarObserver = null
    function removeUndefinedButtonsOnce() {
      try {
        const sel = '#vditor-edit .vditor-toolbar button[data-type="undefined"], #vditor-edit .vditor-toolbar button[aria-label="undefined"]'
        const nodes = document.querySelectorAll(sel)
        nodes.forEach(n => n.remove())
      } catch (e) {}
    }

    function observeToolbarAndClean() {
      try {
        const toolbar = document.querySelector('#vditor-edit .vditor-toolbar')
        if (!toolbar) return
        // initial cleanup
        removeUndefinedButtonsOnce()
        // observe future changes (some versions may append buttons later)
        toolbarObserver = new MutationObserver(mrs => {
          for (const m of mrs) {
            if (m.type === 'childList' && m.addedNodes && m.addedNodes.length) {
              removeUndefinedButtonsOnce()
            }
            if (m.type === 'attributes') {
              removeUndefinedButtonsOnce()
            }
          }
        })
        toolbarObserver.observe(toolbar, { childList: true, subtree: true, attributes: true })
      } catch (e) {}
    }

    // 移除并监听预览头（Desktop/Tablet/Mobile 等）
    let previewObserver = null
    function removePreviewHeaderOnce() {
      try {
        const sel = '#vditor-edit .vditor-preview .vditor-preview__header, #vditor-edit .vditor-preview .vditor-preview__toolbar, #vditor-edit .vditor-preview .vditor-device, #vditor-edit .vditor-preview .vditor-preview__action'
        const nodes = document.querySelectorAll(sel)
        nodes.forEach(n => n.remove())
      } catch (e) {}
    }

    function observePreviewAndClean() {
      try {
        const preview = document.querySelector('#vditor-edit .vditor-preview')
        if (!preview) return
        removePreviewHeaderOnce()
        previewObserver = new MutationObserver(mrs => {
          for (const m of mrs) {
            if (m.type === 'childList' && m.addedNodes && m.addedNodes.length) {
              removePreviewHeaderOnce()
            }
            if (m.type === 'attributes') {
              removePreviewHeaderOnce()
            }
          }
        })
        previewObserver.observe(preview, { childList: true, subtree: true, attributes: true })
      } catch (e) {}
    }

    onMounted(() => {
      // 使用分屏模式，但通过 CSS 调整左右比例，工具栏保持在顶部
      vditor.value = new Vditor('vditor-edit', {
        height: 600,
        minHeight: 480,
        mode: 'sv',
        cache: { enable: false },
        preview: {
          delay: 300,
          markdown: {
            toc: true,
            autoSpace: true
          }
        },
        toolbar: [
          'headings', 'bold', 'italic', 'strike', 'link', '|',
          'list', 'ordered-list', 'check', '|',
          'quote', 'line', 'code', 'inline-code', '|',
          'image', 'table', '|',
          'undo', 'redo', '|',
          'edit-mode', 'preview', 'outline', 'help'
        ],
        outline: { enable: true },
        after: () => {
          try {
            vditor.value && vditor.value.render && vditor.value.render()
          } catch (e) {}

          // 清理可能的 undefined 按钮（主动移除），并观察后续变化
          setTimeout(() => {
            removeUndefinedButtonsOnce()
            observeToolbarAndClean()
            // also clean preview header area
            removePreviewHeaderOnce()
            observePreviewAndClean()
          }, 100)

          // 启动统计定时器（轮询 editor 内容）
          statsTimer = setInterval(() => {
            try {
              const text = vditor.value.getValue() || ''
              const words = text.trim() ? text.replace(/\s+/g, ' ').split(' ').length : 0
              const lines = text.split(/\r?\n/).length
              let cursor = '1:1'
              try {
                const editor = vditor.value.editor
                if (editor && editor.cm) {
                  const pos = editor.cm.getCursor()
                  cursor = (pos.line + 1) + ':' + (pos.ch + 1)
                }
              } catch (e) {}
              stats.value.words = words
              stats.value.lines = lines
              stats.value.cursor = cursor
            } catch (e) {}
          }, 2000)
        }
      })
    })

    onUnmounted(() => {
      if (statsTimer) clearInterval(statsTimer)
      try {
        if (toolbarObserver) toolbarObserver.disconnect()
      } catch (e) {}
      try {
        if (previewObserver) previewObserver.disconnect()
      } catch (e) {}
    })

    // 保存文章（在线编辑），status 可选 'draft' 或 'published'
    async function saveArticle(status = 'published') {
      if (!form.value.title.trim()) {
        message.error('请输入文章标题')
        return null
      }

      if (!vditor.value) {
        message.error('编辑器未初始化')
        return null
      }

      const content = vditor.value.getValue() || ''
      if (!content.trim() && status === 'published') {
        message.error('请输入文章内容')
        return null
      }

      saving.value = true
      try {
        const payload = {
          title: form.value.title,
          content: content,
          tags: form.value.tags.join(','),
          status: status
        }

        const response = await axios.post('/api/articles/', payload, {
          withCredentials: true,
        })

        message.success(status === 'draft' ? '草稿保存成功' : '文章保存成功')
        if (response?.data?.id) {
          setTimeout(() => {
            router.push(`/knowledge/${response.data.id}`)
          }, 500)
        }
        return response
      } catch (err) {
        console.error('保存失败:', err)
        if (err.response?.status === 401) {
          message.error('未授权，请先登录')
        } else {
          message.error(err.response?.data?.msg || '保存失败')
        }
        return null
      } finally {
        saving.value = false
      }
    }

    // 重置编辑表单
    function resetForm() {
      form.value = { title: '', tags: [], content: '' }
      if (vditor.value) {
        vditor.value.setValue('')
      }
    }

    // 导入/导出 & 保存草稿/发布
    function triggerImport() {
      importInput.value?.click()
    }

    async function onImportFile(e) {
      const f = e.target.files?.[0]
      if (!f) return
      try {
        const txt = await f.text()
        if (vditor.value) vditor.value.setValue(txt)
      } catch (err) {
        console.error('导入失败', err)
      } finally {
        if (importInput.value) importInput.value.value = ''
      }
    }

    function exportMarkdown() {
      try {
        const md = vditor.value.getValue() || ''
        const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = (form.value.title || 'article') + '.md'
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      } catch (e) {
        console.error('导出 MD 失败', e)
      }
    }

    function exportHtml() {
      try {
        const html = vditor.value.getHTML ? vditor.value.getHTML() : ''
        const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = (form.value.title || 'article') + '.html'
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      } catch (e) {
        console.error('导出 HTML 失败', e)
      }
    }

    async function saveDraft() {
      await saveArticle('draft')
    }

    async function publishArticle() {
      await saveArticle('published')
    }

    return {
      form,
      importInput,
      saving,
      stats,
      tagOptions,
      saveArticle,
      resetForm,
      triggerImport,
      onImportFile,
      exportMarkdown,
      exportHtml,
      saveDraft,
      publishArticle
    }
  }
}
</script>

<style scoped>
:deep(.vditor) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

:deep(.vditor-menu--last) {
  padding: 8px;
}

/* 自定义布局：工具栏顶部、左侧编辑区 ~62%、右侧预览 ~38% */
:deep(#vditor-edit .vditor) {
  background: var(--card-bg);
  border-radius: var(--card-radius);
}

:deep(#vditor-edit) {
  width: 100%;
  box-sizing: border-box;
  margin: 0;
}

:deep(#vditor-edit .vditor-toolbar) {
  border-bottom: 1px solid var(--border);
  background: var(--hover);
}

:deep(.editor-wrap) {
  /* 外层编辑器容器：撑满表单宽度，内部再按 70/30 分栏 */
  width: 100%;
  max-width: none;
  margin: 0 0 12px 0; /* 顶部留点间距 */
  box-sizing: border-box;
  padding: 8px; /* 让编辑区看起来是一个独立的大框 */
  border: 1px solid var(--border);
  background: var(--gradient-card-bg, var(--card-bg));
}

:deep(.editor-topbar) {
  width: 100%; /* 顶部工具条撑满编辑器容器 */
  margin-bottom: 12px; /* 增加底部间距，避免与 vditor 工具栏紧贴 */
}

:deep(#vditor-edit .vditor-sv) {
  display: flex;
  gap: 0;
  width: 100%;
  align-items: stretch;
}

:deep(#vditor-edit .vditor-sv .vditor-reset) {
  /* 左侧编辑区（占父容器 70%） */
  width: 70% !important;
  border-right: 1px solid #f0f0f0;
  min-height: 680px; /* 更高，匹配大框视觉 */
}

:deep(#vditor-edit .vditor-sv .vditor-preview) {
  /* 右侧预览区（占父容器 30%） */
  width: 30% !important;
  padding: 24px;
  overflow: auto;
  background: var(--card-bg);
  min-height: 680px;
}

:deep(#vditor-edit .vditor-toolbar) {
  width: 100% !important;
  margin-top: 8px !important; /* 给 vditor 工具栏一些顶部空间 */
}

/* 修复：确保 Vditor 工具栏图标显示（防止全局样式覆盖 svg/icon 显示） */
:deep(#vditor-edit .vditor-toolbar .vditor-menu button),
:deep(#vditor-edit .vditor-toolbar .vditor-menu button svg) {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin-right: 8px !important; /* 按钮之间留空隙 */
  padding: 6px !important; /* 让按钮更易点按，不显拥挤 */
}

/* 隐藏错误的未定义按钮（某些环境下 Vditor 可能注入 data-type="undefined" 的占位） */
:deep(#vditor-edit .vditor-toolbar .vditor-menu button[data-type="undefined"]),
:deep(#vditor-edit .vditor-toolbar .vditor-menu button[aria-label="undefined"]) {
  display: none !important;
}

:deep(#vditor-edit .vditor-toolbar .vditor-menu button svg) {
  width: 18px !important;
  height: 18px !important;
  fill: currentColor !important;
  color: #333 !important;
  opacity: 1 !important;
}

/* 更强力保证：覆盖可能把 svg 内 path/g 设置为透明或无填充的全局规则 */
:deep(#vditor-edit .vditor-toolbar .vditor-menu button svg *),
:deep(#vditor-edit .vditor-toolbar .vditor-menu button svg path),
:deep(#vditor-edit .vditor-toolbar .vditor-menu button svg g),
:deep(#vditor-edit .vditor-toolbar .vditor-menu button svg circle),
:deep(#vditor-edit .vditor-toolbar .vditor-menu button svg rect) {
  fill: currentColor !important;
  stroke: currentColor !important;
  color: currentColor !important;
  opacity: 1 !important;
}

/* 修复：显示快捷键样式（<kbd>）用于提示里的按键效果 */
:deep(#vditor-edit kbd) {
  display: inline-block !important;
  padding: 2px 6px !important;
  margin: 0 2px !important;
  font-size: 12px !important;
  line-height: 1 !important;
  border-radius: 4px !important;
  background: #f3f4f6 !important;
  border: 1px solid rgba(0,0,0,0.08) !important;
  box-shadow: inset 0 -1px 0 rgba(0,0,0,0.02) !important;
}

:deep(#vditor-edit .vditor-reset .vditor-ir),
:deep(#vditor-edit .vditor-preview) {
  min-height: 480px;
}

/* 隐藏 Vditor 的设备预览头部（Desktop/Tablet 等）——更广的选择器以兼容不同 Vditor 版本 */
:deep(#vditor-edit .vditor-preview .vditor-preview__header),
:deep(#vditor-edit .vditor-preview .vditor-preview__toolbar),
:deep(#vditor-edit .vditor-preview .vditor-preview-toolbar),
:deep(#vditor-edit .vditor-preview .vditor-device),
:deep(#vditor-edit .vditor-preview .vditor-toolbar),
:deep(#vditor-edit .vditor-preview .vditor-handle) {
  display: none !important;
}

/* 工具栏顶部撑满编辑区域 */
.editor-topbar {
  width: 100%;
  box-sizing: border-box;
  padding: 6px 8px 10px 8px;
}

/* 发布按钮样式 */
:deep(.publish-btn) {
  padding: 8px 18px !important;
  font-weight: 600;
}

/* 让左右栏在较窄屏幕上仍能友好显示 */
@media (max-width: 900px) {
  :deep(#vditor-edit .vditor-sv .vditor-reset),
  :deep(#vditor-edit .vditor-sv .vditor-preview) {
    width: 100% !important;
    display: block;
  }
  :deep(#vditor-edit .vditor-sv) {
    flex-direction: column;
  }
}

/* 强制隐藏预览头（Desktop/Tablet/Mobile/刷新/知）——站内不需要这些控件 */
:deep(#vditor-edit .vditor-preview .vditor-preview__header),
:deep(#vditor-edit .vditor-preview .vditor-preview__toolbar),
:deep(#vditor-edit .vditor-preview .vditor-device) {
  display: none !important;
}

/* Hide the preview action container (device buttons, refresh, 知/zhihu, etc.) */
:deep(#vditor-edit .vditor-preview .vditor-preview__action) {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}
</style>
