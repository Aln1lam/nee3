<template>
  <div class="article-root" :class="{ 'article-root--with-toc': showSideRail }">
    <nav v-if="showSideRail" class="article-toc" aria-label="目录">
      <div class="article-toc__title">目录</div>
      <ul class="article-toc__list">
        <li
          v-for="item in toc"
          :key="item.id"
          :class="`toc-l${item.level}`"
        >
          <a :href="`#${item.id}`" @click.prevent="scrollTo(item.id)">{{ item.text }}</a>
        </li>
      </ul>
    </nav>
    <div v-if="editable" class="article-edit-hint">编辑模式：请在父组件接入 Markdown 编辑</div>
    <div
      ref="bodyRef"
      class="article-body markdown-body"
      :class="{ 'article-body--print': printFriendly }"
      v-html="html"
    />
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { extractToc, renderMarkdown } from '@/utils/markdown'
import 'highlight.js/styles/github.css'

export default {
  name: 'Article',
  props: {
    content: { type: String, default: '' },
    showToc: { type: Boolean, default: false },
    printFriendly: { type: Boolean, default: true },
    /** 管理员 inline 编辑预留（Task 04）*/
    editable: { type: Boolean, default: false },
  },
  emits: ['update:content'],
  setup(props) {
    const bodyRef = ref(null)
    const toc = computed(() => extractToc(props.content))
    const html = computed(() => renderMarkdown(props.content))
    const showSideRail = computed(() => props.showToc && toc.value.length > 0)

    function scrollTo(id) {
      const safeId = typeof CSS !== 'undefined' && CSS.escape ? CSS.escape(id) : id.replace(/[^\w-]/g, '')
      const el = bodyRef.value?.querySelector(`#${safeId}`)
      if (!el) return
      const scroller = el.closest('.wiki-detail-main') || el.closest('.wiki-detail-page') || el.closest('.page-wrap')
      if (scroller) {
        const top = el.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop - 24
        scroller.scrollTo({ top, behavior: 'smooth' })
      } else {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }

    function attachCodeCopy() {
      const root = bodyRef.value
      if (!root) return
      root.querySelectorAll('pre').forEach((pre) => {
        if (pre.querySelector('.code-copy-btn')) return
        const code = pre.querySelector('code')
        const text = code?.textContent || pre.textContent || ''
        const btn = document.createElement('button')
        btn.type = 'button'
        btn.className = 'code-copy-btn'
        btn.textContent = '复制'
        btn.addEventListener('click', async () => {
          try {
            await navigator.clipboard.writeText(text)
            btn.textContent = '已复制'
            setTimeout(() => { btn.textContent = '复制' }, 1500)
          } catch {
            btn.textContent = '失败'
          }
        })
        pre.style.position = 'relative'
        pre.appendChild(btn)
      })
    }

    watch(html, async () => {
      await nextTick()
      attachCodeCopy()
    })

    onMounted(async () => {
      await nextTick()
      attachCodeCopy()
    })

    return { bodyRef, toc, html, scrollTo, showSideRail }
  },
}
</script>

<style scoped>
.article-root {
  display: block;
}
.article-edit-hint {
  margin-bottom: 8px;
  padding: 6px 10px;
  font-size: var(--text-xs);
  color: var(--warning, #fab005);
  background: rgba(250, 176, 5, 0.08);
  border-radius: var(--radius-md);
  border: 1px dashed rgba(250, 176, 5, 0.35);
}
.article-root--with-toc {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
  align-items: start;
}
.article-toc {
  position: sticky;
  top: 12px;
  align-self: start;
  max-height: calc(100vh - 120px);
  overflow: auto;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius, 10px);
  background: var(--card-bg);
  font-size: var(--text-sm);
  z-index: 2;
}
.article-toc__list {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
}
.article-toc__list::-webkit-scrollbar {
  width: 6px;
}
.article-toc__list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}
.article-toc::-webkit-scrollbar {
  width: 6px;
}
.article-toc::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}
.article-toc::-webkit-scrollbar-track {
  background: transparent;
}
.article-toc__title {
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 8px;
}
.article-toc a {
  color: var(--muted);
  text-decoration: none;
  display: block;
  padding: 4px 0;
  line-height: 1.4;
}
.article-toc a:hover { color: var(--primary); }
.toc-l2 { padding-left: 12px; }
.toc-l3 { padding-left: 24px; }
.article-body {
  line-height: 1.7;
  color: var(--text);
  word-break: break-word;
}
.article-body :deep(pre) {
  position: relative;
  background: var(--code-bg);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  overflow-x: auto;
}
.article-body :deep(.code-copy-btn) {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card-bg);
  color: var(--muted);
  cursor: pointer;
}
.article-body :deep(.code-copy-btn:hover) { color: var(--primary); }
.article-body :deep(h1), .article-body :deep(h2), .article-body :deep(h3) {
  scroll-margin-top: calc(var(--nav-height, 64px) + 12px);
}
.article-body :deep(.math-inline) {
  font-family: 'Times New Roman', serif;
  font-style: italic;
  color: var(--primary);
  padding: 0 2px;
}
.article-body :deep(.math-block) {
  text-align: center;
  font-family: 'Times New Roman', serif;
  font-style: italic;
  color: var(--primary);
  margin: 12px 0;
  padding: 8px;
  background: var(--hover);
  border-radius: var(--radius-md);
}
.article-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
}
.article-body :deep(th), .article-body :deep(td) {
  border: 1px solid var(--border);
  padding: 8px 12px;
}
.article-body :deep(th) { background: var(--hover); }
@media (max-width: 900px) {
  .article-root--with-toc { grid-template-columns: 1fr; }
  .article-toc { position: static; }
}
@media print {
  .article-toc { display: none; }
  .article-body--print :deep(.code-copy-btn) { display: none; }
}
</style>
