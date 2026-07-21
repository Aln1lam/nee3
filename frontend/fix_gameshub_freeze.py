# -*- coding: utf-8 -*-
"""Fix GamesHub freeze: missing getGameSidebarCode + isAdmin binding."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'GamesHub.vue'
text = p.read_text(encoding='utf-8')

# 1) template: isAdmin -> canCreateGame
old_admin = '        <div v-if="isAdmin" class="sidebar-actions">'
new_admin = '        <div v-if="canCreateGame" class="sidebar-actions">'
if old_admin not in text:
    raise SystemExit('isAdmin block not found')
text = text.replace(old_admin, new_admin, 1)

# 2) add helper + export it
helper = '''
    function getGameSidebarCode(g) {
      const title = (g?.title || '').trim()
      if (!title) return 'CTF'
      const compact = title.replace(/\\s+/g, '')
      if (/^[A-Za-z0-9]{2,3}/.test(compact)) {
        return compact.slice(0, 3).toUpperCase()
      }
      return compact.slice(0, 2).toUpperCase() || 'CTF'
    }

'''

anchor = '    function isHosted(g) {'
if 'function getGameSidebarCode' not in text:
    if anchor not in text:
        raise SystemExit('isHosted anchor not found')
    text = text.replace(anchor, helper + anchor, 1)

old_return = '''      getGameEmoji, getGameStatusLabel, getGameStatusVariant, getGameStatusDotClass,
      selectGame, openGameDetail, scrollToOthers, openCreate,'''
new_return = '''      getGameEmoji, getGameSidebarCode, getGameStatusLabel, getGameStatusVariant, getGameStatusDotClass,
      selectGame, openGameDetail, scrollToOthers, openCreate,'''
if old_return not in text:
    raise SystemExit('return block not found')
text = text.replace(old_return, new_return, 1)

# 3) prevent keyPage <-> router replace churn
old_watch = '''    watch(keyPage, (p) => {
      router.replace({ query: { ...route.query, 'key-page': p } })
    })'''
new_watch = '''    watch(keyPage, (p) => {
      if (String(route.query['key-page'] || '') === String(p)) return
      router.replace({ query: { ...route.query, 'key-page': p } })
    })'''
if old_watch not in text:
    raise SystemExit('keyPage watch not found')
text = text.replace(old_watch, new_watch, 1)

p.write_text(text, encoding='utf-8', newline='\n')
print('GamesHub freeze fix ok')
