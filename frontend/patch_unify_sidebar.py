# -*- coding: utf-8 -*-
"""Unify all sidebars to /training sidebar-rail pattern (248px, head-row, sidebar-item)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'


def patch(path, old, new, label=None):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        print(f'SKIP {path}: {label or old[:40]!r}')
        return
    p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print(f'ok {path}: {label or "patched"}')


def strip_scoped_sidebar_overrides(path, class_name):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    pattern = rf'\.{re.escape(class_name)} \{{[^}}]+\}}\n\n'
    new_text, n = re.subn(pattern, '', text, count=1)
    if n:
        p.write_text(new_text, encoding='utf-8', newline='\n')
        print(f'ok {path}: removed .{class_name} scoped override')
    else:
        print(f'SKIP {path}: no .{class_name} block')


# Wiki
patch('KnowledgeList.vue', 'style="--sidebar-width: 256px"', 'style="--sidebar-width: 248px"', 'wiki width')
patch('KnowledgeList.vue',
      '''      <div class="sidebar-head sidebar-rail-head">
        <LinuxPrompt path="~/wiki" cmd="man index" extra-class="sidebar-rail-prompt" />
        <h2 class="sidebar-rail-title">知识库</h2>
        <p class="sidebar-desc sidebar-rail-sub">DOC · WIKI</p>
      </div>''',
      '''      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/wiki" class="sidebar-title sidebar-rail-title">知识库</router-link>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">DOC · WIKI</p>
      </div>''',
      'wiki head')

# Bulletin
patch('Bulletin.vue', 'style="--sidebar-width: 256px"', 'style="--sidebar-width: 248px"')
patch('Bulletin.vue',
      'class="bulletin-layout layout-with-sidebar"\n    :class="{ \'sidebar-collapsed\': collapsed }"',
      'class="bulletin-layout layout-with-sidebar lab-deck"\n    :class="{ \'sidebar-collapsed\': collapsed }"',
      'bulletin lab-deck')
patch('Bulletin.vue',
      '''      <div class="sidebar-head sidebar-rail-head">
        <LinuxPrompt path="~/bulletin" cmd="tail -f feed" extra-class="sidebar-rail-prompt" />
        <h2 class="sidebar-rail-title">公告中心</h2>
        <p class="sidebar-desc sidebar-rail-sub">BULLETIN · FEED</p>
      </div>''',
      '''      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/bulletin" class="sidebar-title sidebar-rail-title">公告中心</router-link>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">BULLETIN · FEED</p>
      </div>''',
      'bulletin head')
patch('Bulletin.vue',
      '''        <div class="sidebar-row">
          <span class="link-code">ALL</span>
          <span class="row-label">全部公告</span>
          <span class="row-value">{{ bulletins.length }}</span>
        </div>
        <div class="sidebar-row">
          <span class="link-code">PG</span>
          <span class="row-label">当前页</span>
          <span class="row-value">{{ pagedBulletins.length }}</span>
        </div>
        <router-link
          v-if="isAdmin"
          to="/bulletin/create"
          class="sidebar-row sidebar-row--action"
        >
          <span class="link-code">NEW</span>
          <span class="row-label">发布公告</span>
          <span class="row-arrow">→</span>
        </router-link>''',
      '''        <div class="sidebar-item">
          <span class="item-code">ALL</span>
          <span class="item-title">全部公告</span>
          <span class="item-count">{{ bulletins.length }}</span>
        </div>
        <div class="sidebar-item">
          <span class="item-code">PG</span>
          <span class="item-title">当前页</span>
          <span class="item-count">{{ pagedBulletins.length }}</span>
        </div>
        <router-link
          v-if="isAdmin"
          to="/bulletin/create"
          class="sidebar-item"
        >
          <span class="item-code">NEW</span>
          <span class="item-title">发布公告</span>
          <span class="item-count">→</span>
        </router-link>''',
      'bulletin nav')
patch('Bulletin.vue',
      '<div class="sidebar-footer sidebar-rail-footer">',
      '<div class="sidebar-links sidebar-rail-footer">',
      'bulletin footer')
strip_scoped_sidebar_overrides('Bulletin.vue', 'bulletin-sidebar')

# Admin
patch('AdminPanel.vue', 'style="--sidebar-width: 256px"', 'style="--sidebar-width: 248px"')
patch('AdminPanel.vue',
      '''      <div class="sidebar-head sidebar-rail-head">
        <LinuxPrompt path="~/admin" cmd="ops --panel" extra-class="sidebar-rail-prompt" />
        <h2 class="sidebar-rail-title">运维管理</h2>
        <p class="sidebar-desc sidebar-rail-sub">ADMIN · OPS</p>
      </div>''',
      '''      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/admin/dashboard" class="sidebar-title sidebar-rail-title">运维管理</router-link>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">ADMIN · OPS</p>
      </div>''',
      'admin head')

# GamesHub
patch('GamesHub.vue', 'style="--sidebar-width: 256px"', 'style="--sidebar-width: 248px"')
patch('GamesHub.vue',
      'class="games-layout layout-with-sidebar"\n      :class="{ \'sidebar-collapsed\': collapsed }"',
      'class="games-layout layout-with-sidebar lab-deck"\n      :class="{ \'sidebar-collapsed\': collapsed }"',
      'games lab-deck')
patch('GamesHub.vue',
      '''      <aside class="games-sidebar sidebar-rail">
        <LinuxPrompt path="~/games" cmd="ls -la" extra-class="sidebar-rail-prompt" />
        <div v-if="isAdmin" class="sidebar-actions">''',
      '''      <aside class="games-sidebar sidebar-rail">
        <div class="sidebar-head sidebar-rail-head">
          <div class="sidebar-head-row">
            <router-link to="/games" class="sidebar-title sidebar-rail-title">赛事列表</router-link>
          </div>
          <p class="sidebar-desc sidebar-rail-sub">CTF · GAMES</p>
        </div>
        <div v-if="isAdmin" class="sidebar-actions">''',
      'games head')
patch('GamesHub.vue',
      '''              class="game-list-item"
              :class="{ active: selected?.id === g.id }"
              @click="selectGame(g)"
            >
              <span class="game-flag" aria-hidden="true">{{ getGameEmoji(g) }}</span>
              <span class="game-name">{{ g.title }}</span>
              <span class="status-dot" :class="getGameStatusDotClass(g)" aria-hidden="true" />''',
      '''              class="sidebar-item game-list-item"
              :class="{ active: selected?.id === g.id }"
              @click="selectGame(g)"
            >
              <span class="item-code">{{ getGameSidebarCode(g) }}</span>
              <span class="item-title">{{ g.title }}</span>
              <span class="item-count status-dot" :class="getGameStatusDotClass(g)" aria-hidden="true" />''',
      'games items')

gh = ROOT / 'GamesHub.vue'
ght = gh.read_text(encoding='utf-8')
if 'function getGameSidebarCode' not in ght:
    ght = ght.replace(
        '''    function scrollToOthers() {
      otherSectionRef.value?.scrollIntoView({ behavior: 'smooth' })
    }''',
        '''    function getGameSidebarCode(g) {
      const t = (g?.title || 'GME').replace(/\\s+/g, '')
      return t.slice(0, 3).toUpperCase() || 'GME'
    }

    function scrollToOthers() {
      otherSectionRef.value?.scrollIntoView({ behavior: 'smooth' })
    }''',
        1,
    )
    ght = ght.replace(
        '      scrollToOthers,',
        '      getGameSidebarCode,\n      scrollToOthers,',
        1,
    )
    gh.write_text(ght, encoding='utf-8', newline='\n')
    print('ok GamesHub.vue: getGameSidebarCode')

# ChallengeWorkspace
patch('ChallengeWorkspace.vue',
      '''  <MatrixShell
    class="challenge-workspace-matrix"
    :show-sidebar="true"
    :bleed="false"
    content-class="challenge-workspace-page"''',
      '''  <MatrixShell
    class="challenge-workspace-matrix"
    :show-sidebar="true"
    :bleed="false"
    :collapsible="!embedded"
    :storage-key="embedded ? 'neepu_training_ws_sidebar' : 'neepu_challenge_sidebar_collapsed'"
    content-class="challenge-workspace-page"''',
      'workspace collapsible')
patch('ChallengeWorkspace.vue',
      '''      <LinuxPrompt :path="shellPath" :cmd="shellCmd" extra-class="sidebar-rail-prompt" />
      <aside class="tree-panel tree-panel--matrix">''',
      '''      <aside class="tree-panel tree-panel--matrix">''',
      'workspace sidebar prompt')

print('patch_unify_sidebar.py done')
