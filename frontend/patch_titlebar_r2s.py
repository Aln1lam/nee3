# -*- coding: utf-8 -*-
"""Simplify TitleBar labels to match Xidian (icon+text, no TRN codes)."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'TitleBar.vue'
text = p.read_text(encoding='utf-8')

old_nav = '''          <a
            v-for="link in globalNav"
            :key="link.path"
            :class="{ active: isActive(link.path) }"
            @click.prevent="navigate(link.path)"
          >
            <span v-if="link.code" class="nav-code">{{ link.code }}</span>
            <span class="nav-label">{{ link.label }}</span>
          </a>
          <a v-if="user?.is_admin" :class="{ active: isActive('/admin') }" @click.prevent="navigate('/admin/dashboard')">
            <span class="nav-code">ADM</span>
            <span class="nav-label">管理</span>
          </a>'''

new_nav = '''          <a
            v-for="link in globalNav"
            :key="link.path"
            class="btn btn-md btn-ghost"
            :class="{ 'btn-active': isActive(link.path), active: isActive(link.path) }"
            @click.prevent="navigate(link.path)"
          >
            <span class="nav-label">{{ link.label }}</span>
          </a>
          <a
            v-if="user?.is_admin"
            class="btn btn-md btn-ghost"
            :class="{ 'btn-active': isActive('/admin'), active: isActive('/admin') }"
            @click.prevent="navigate('/admin/dashboard')"
          >
            <span class="nav-label">管理</span>
          </a>'''

if old_nav not in text:
    raise SystemExit('nav block not found')
text = text.replace(old_nav, new_nav, 1)

# Filter default nav: drop 首页 from top like xidian (知识 训练 赛事 公告)
old_def = '''const DEFAULT_NAV = [
  { label: '首页', path: '/home' },
  { label: '知识', path: '/wiki' },
  { label: '训练', path: '/training' },
  { label: '赛事', path: '/games' },
  { label: '公告', path: '/bulletin' },
]'''
new_def = '''const DEFAULT_NAV = [
  { label: '知识', path: '/wiki' },
  { label: '训练', path: '/training' },
  { label: '赛事', path: '/games' },
  { label: '公告', path: '/bulletin' },
]'''
if old_def not in text:
    raise SystemExit('DEFAULT_NAV not found')
text = text.replace(old_def, new_def, 1)

# When applying platform nav, filter home
old_apply = "globalNav.value = enrichNav(info.nav?.length ? info.nav : DEFAULT_NAV)"
new_apply = """globalNav.value = enrichNav(
        (info.nav?.length ? info.nav : DEFAULT_NAV).filter((l) => l.path !== '/home' && l.path !== '/')
      )"""
if old_apply not in text:
    raise SystemExit('applyPlatform nav assign not found')
text = text.replace(old_apply, new_apply, 1)

p.write_text(text, encoding='utf-8', newline='\n')
print('TitleBar r2s ok')
