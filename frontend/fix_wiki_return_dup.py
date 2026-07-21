# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(__file__).resolve().parent / 'src' / 'components' / 'KnowledgeList.vue'
text = p.read_text(encoding='utf-8')
old = 'selectedTag, goArticle, renderTags, formatWikiTime, renderTags, collapsed, toggleSidebar,'
new = 'selectedTag, goArticle, renderTags, formatWikiTime, collapsed, toggleSidebar,'
if old not in text:
    raise SystemExit('dup return not found: ' + text[text.find('selectedTag'):text.find('selectedTag')+120])
p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
print('fixed')
