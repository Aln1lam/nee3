import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'
import c from 'highlight.js/lib/languages/c'
import cpp from 'highlight.js/lib/languages/cpp'
import java from 'highlight.js/lib/languages/java'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import php from 'highlight.js/lib/languages/php'
import plaintext from 'highlight.js/lib/languages/plaintext'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('c', c)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('c++', cpp)
hljs.registerLanguage('java', java)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('php', php)
hljs.registerLanguage('text', plaintext)
hljs.registerLanguage('plaintext', plaintext)

marked.setOptions({
  gfm: true,
  breaks: false,
})

function slugify(text) {
  return String(text || '')
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'section'
}

function tokensToPlain(tokens = []) {
  return tokens.map((t) => t.raw ?? t.text ?? '').join('').replace(/[#*`[\]]/g, '').trim()
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function highlightCode(code, lang) {
  const language = (lang || '').trim().toLowerCase()
  try {
    if (language && hljs.getLanguage(language)) {
      return hljs.highlight(code, { language }).value
    }
    return hljs.highlightAuto(code).value
  } catch {
    return escapeHtml(code)
  }
}

/** 从 Markdown 提取 TOC */
export function extractToc(markdown) {
  if (!markdown) return []
  const lines = markdown.split('\n')
  const toc = []
  const used = new Set()

  for (const line of lines) {
    const m = /^(#{1,3})\s+(.+)$/.exec(line.trim())
    if (!m) continue
    const level = m[1].length
    const text = m[2].replace(/[#*`[\]]/g, '').trim()
    let id = slugify(text)
    let n = 1
    while (used.has(id)) {
      id = `${slugify(text)}-${n++}`
    }
    used.add(id)
    toc.push({ id, text, level })
  }
  return toc
}

/** 通用 HTML 消毒 */
export function sanitizeHtml(html) {
  if (!html) return ''
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['target', 'rel', 'id', 'data-lang', 'class'],
    ADD_TAGS: ['div', 'span'],
  })
}

/** 简单 Markdown 渲染（无 TOC） */
export function parseMarkdownSafe(markdown) {
  if (!markdown) return ''
  try {
    return sanitizeHtml(renderMarkdown(String(markdown)))
  } catch {
    return ''
  }
}

/** Markdown → HTML（marked v17+），含标题锚点、代码高亮、外链 */
export function renderMarkdown(markdown) {
  if (!markdown) return ''

  const toc = extractToc(markdown)
  const slugQueue = toc.map((t) => t.id)

  const renderer = new marked.Renderer()
  renderer.heading = function heading({ tokens, depth }) {
    const html = this.parser.parseInline(tokens)
    const id = slugQueue.shift() || slugify(tokensToPlain(tokens))
    return `<h${depth} id="${id}">${html}</h${depth}>\n`
  }
  renderer.code = function code({ text, lang }) {
    const language = lang || 'text'
    const highlighted = highlightCode(text, language)
    return `<pre data-lang="${escapeHtml(language)}"><code class="hljs language-${escapeHtml(language)}">${highlighted}</code></pre>\n`
  }

  let html = marked.parse(markdown, { renderer })
  html = html.replace(/\$\$([^$]+)\$\$/g, '<div class="math-block">$1</div>')
  html = html.replace(/\$([^$\n]+)\$/g, '<span class="math-inline">$1</span>')
  html = html.replace(/<img\s+src="(?!https?:\/\/|\/api\/uploads\/serve\/)([^"]+)"/g, '<img src="/api/uploads/serve/$1"')
  html = html.replace(/<a\s+href="(https?:\/\/[^"]+)"/g, '<a href="$1" target="_blank" rel="noopener noreferrer"')
  return sanitizeHtml(html)
}
