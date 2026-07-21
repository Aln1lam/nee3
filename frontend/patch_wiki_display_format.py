# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'KnowledgeList.vue'
text = p.read_text(encoding='utf-8')

# template: format tags + time
old_tpl = '''                  <div class="wiki-item-tags">
                    <n-tag v-for="t in renderTags(a)" :key="a.id + '-tag-' + t" size="small">{{ t }}</n-tag>
                  </div>
                  <time class="wiki-item-time">{{ a.created_at }}</time>'''
new_tpl = '''                  <div class="wiki-item-tags">
                    <n-tag v-for="t in renderTags(a)" :key="a.id + '-tag-' + t" size="small" round>{{ t }}</n-tag>
                  </div>
                  <time class="wiki-item-time">{{ formatWikiTime(a.created_at) }}</time>'''
if old_tpl not in text:
    raise SystemExit('template foot not found')
text = text.replace(old_tpl, new_tpl, 1)

old_imp = "import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'"
new_imp = """import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'
import { formatWikiTags, formatWikiTime } from '../utils/wikiDisplay'"""
if old_imp not in text:
    raise SystemExit('import not found')
text = text.replace(old_imp, new_imp, 1)

old_fn = '''    function renderTags(a) {
      const out = []
      try {
        if (a.tags) {
          out.push(...(a.tags || '').split(',').map(s => s?.trim()).filter(Boolean))
        }
      } catch { /* ignore */ }
      return out
    }'''
new_fn = '''    function renderTags(a) {
      return formatWikiTags(a?.tags)
    }'''
if old_fn not in text:
    raise SystemExit('renderTags not found')
text = text.replace(old_fn, new_fn, 1)

old_ret = '''      articles, q, fetch, categories, selectTag, clearCategory, tagCode,'''
# find return section
if 'formatWikiTime' not in text.split('return')[-1]:
    # patch return
    marker = 'goArticle,'
    if marker not in text:
        # try another
        if 'renderTags,' in text:
            text = text.replace('renderTags,', 'renderTags, formatWikiTime,', 1)
        else:
            raise SystemExit('return marker not found')
    else:
        text = text.replace(marker, 'goArticle, renderTags, formatWikiTime,', 1)

# ensure renderTags still in return
if 'renderTags' not in text[text.rfind('return'):]:
    raise SystemExit('renderTags missing from return')

p.write_text(text, encoding='utf-8', newline='\n')
print('KnowledgeList display format ok')
