# -*- coding: utf-8 -*-
"""Wrap ChallengeWorkspace in MatrixShell + Training game-mode class."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'

# ── ChallengeWorkspace: template wrap ──
cw = ROOT / 'ChallengeWorkspace.vue'
text = cw.read_text(encoding='utf-8')

OLD_TEMPLATE_START = '''<template>
  <div class="challenge-workspace workspace-dock" :class="[`mode-${mode}`, { 'admin-tools-on': adminActive }]">
    <!-- 左：题目树 -->
    <aside class="tree-panel">'''

NEW_TEMPLATE_START = '''<template>
  <MatrixShell
    class="challenge-workspace-matrix"
    :show-sidebar="true"
    :bleed="false"
    content-class="challenge-workspace-page"
    :page-prompt="shellPagePrompt"
    :page-title="shellPageTitle"
    :page-desc="shellPageDesc"
  >
    <template #sidebar>
      <LinuxPrompt :path="shellPath" :cmd="shellCmd" extra-class="sidebar-rail-prompt" />
      <aside class="tree-panel tree-panel--matrix">'''

if OLD_TEMPLATE_START not in text:
    raise SystemExit('ChallengeWorkspace template start not found')

text = text.replace(OLD_TEMPLATE_START, NEW_TEMPLATE_START, 1)

OLD_TREE_END = '''      <div v-if="$slots['tree-footer']" class="tree-footer">
        <slot name="tree-footer" />
      </div>
    </aside>

    <!-- 右：工作区 -->
    <section class="workspace-stage">'''

NEW_TREE_END = '''      <div v-if="$slots['tree-footer']" class="tree-footer">
        <slot name="tree-footer" />
      </div>
    </aside>
    </template>

    <template #sidebar-footer>
      <router-link v-if="mode === 'training'" to="/training" class="sidebar-link">
        <span class="link-code">BAK</span>
        <span>练习场列表</span>
      </router-link>
      <router-link v-else :to="`/games/${gameId}`" class="sidebar-link">
        <span class="link-code">GME</span>
        <span>赛事详情</span>
      </router-link>
      <router-link to="/games" class="sidebar-link">
        <span class="link-code">CTF</span>
        <span>赛事列表</span>
      </router-link>
      <router-link v-if="mode !== 'training'" :to="`/games/${gameId}/scoreboard`" class="sidebar-link">
        <span class="link-code">SB</span>
        <span>排行榜</span>
      </router-link>
    </template>

    <div
      class="challenge-workspace workspace-dock"
      :class="[`mode-${mode}`, { 'admin-tools-on': adminActive }]"
    >
    <section class="workspace-stage">'''

if OLD_TREE_END not in text:
    raise SystemExit('ChallengeWorkspace tree end not found')

text = text.replace(OLD_TREE_END, NEW_TREE_END, 1)

OLD_TEMPLATE_END = '''    </section>
  </div>
</template>'''

NEW_TEMPLATE_END = '''    </section>
    </div>
  </MatrixShell>
</template>'''

if OLD_TEMPLATE_END not in text:
    raise SystemExit('ChallengeWorkspace template end not found')

text = text.replace(OLD_TEMPLATE_END, NEW_TEMPLATE_END, 1)

# ── imports & components ──
OLD_IMPORT = "import { Article, Terminal, HammerPanel } from '@/components/shared'"
NEW_IMPORT = "import { Article, Terminal, HammerPanel, MatrixShell, LinuxPrompt } from '@/components/shared'"
text = text.replace(OLD_IMPORT, NEW_IMPORT, 1)

OLD_COMPONENTS = "  components: { NTag, NInput, NButton, NTabs, NTabPane, UiLoadingTips, UiPopover, UiButton, Terminal, HammerPanel, Article },"
NEW_COMPONENTS = "  components: { NTag, NInput, NButton, NTabs, NTabPane, UiLoadingTips, UiPopover, UiButton, Terminal, HammerPanel, Article, MatrixShell, LinuxPrompt },"
text = text.replace(OLD_COMPONENTS, NEW_COMPONENTS, 1)

# ── computed shell props in return ──
OLD_RETURN = '''    return {
      challenges, challengesLoading, selectedChallenge, searchQuery,'''

NEW_COMPUTED = '''
    const shellPath = computed(() =>
      props.mode === 'training' ? `~/training/${props.gameId}` : `~/games/${props.gameId}/challenges`,
    )
    const shellCmd = computed(() =>
      props.mode === 'training' ? 'ls challenges/' : 'grep -R flag .',
    )
    const shellPagePrompt = computed(() =>
      props.mode === 'training'
        ? `cd /training/${props.gameId}`
        : `curl /games/${props.gameId}/challenges`,
    )
    const shellPageTitle = computed(() =>
      props.gameTitle || (props.mode === 'training' ? '练习场' : '赛事题目'),
    )
    const shellPageDesc = computed(() => {
      if (props.mode === 'training') return '永久开放 · 无时间限制 · 不计入正式积分'
      return props.gameStatus || '选择左侧题目开始挑战'
    })

    return {
      shellPath, shellCmd, shellPagePrompt, shellPageTitle, shellPageDesc,
      challenges, challengesLoading, selectedChallenge, searchQuery,'''

if OLD_RETURN not in text:
    raise SystemExit('ChallengeWorkspace return block not found')

text = text.replace(OLD_RETURN, NEW_COMPUTED, 1)

# ── scoped CSS: workspace-dock single column ──
OLD_DOCK_CSS = '''.workspace-dock {
  display: grid;
  grid-template-columns: var(--dock-sidebar-width, calc(var(--layout-space, 0.25rem) * 64)) minmax(0, 1fr);
  min-height: var(--workspace-height, calc(100vh - var(--nav-height, 56px)));
  height: 100%;
  border: var(--dock-border-width, 0) solid var(--gradient-card-border, var(--border));
  border-radius: var(--dock-radius, 0);
  overflow: hidden;
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--dock-shadow, none);
}'''

NEW_DOCK_CSS = '''.workspace-dock {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  border: var(--dock-border-width, 0) solid var(--gradient-card-border, var(--border));
  border-radius: var(--dock-radius, 0);
  overflow: hidden;
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--dock-shadow, none);
}'''

text = text.replace(OLD_DOCK_CSS, NEW_DOCK_CSS, 1)

OLD_TREE_PANEL = '''.tree-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid var(--border);
  background: var(--sidebar-bg, rgba(var(--primary-rgb), 0.04));
}'''

NEW_TREE_PANEL = '''.tree-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: transparent;
}

.tree-panel--matrix {
  border-top: 1px solid var(--border);
}'''

text = text.replace(OLD_TREE_PANEL, NEW_TREE_PANEL, 1)

OLD_MEDIA = '''@media (max-width: 900px) {
  .workspace-dock {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  .tree-body { max-height: 220px; }'''

NEW_MEDIA = '''@media (max-width: 900px) {
  .tree-body { max-height: 220px; }'''

text = text.replace(OLD_MEDIA, NEW_MEDIA, 1)

cw.write_text(text, encoding='utf-8', newline='\n')
print('ok ChallengeWorkspace.vue')

# ── Training.vue: game mode class ──
tr = ROOT / 'Training.vue'
tt = tr.read_text(encoding='utf-8')
OLD_MAIN = '<main class="training-main sidebar-main">'
NEW_MAIN = '<main class="training-main sidebar-main" :class="{ \'training-main--game\': !!selectedGame }">'
if OLD_MAIN not in tt:
    print('SKIP Training.vue main class')
else:
    tr.write_text(tt.replace(OLD_MAIN, NEW_MAIN, 1), encoding='utf-8', newline='\n')
    print('ok Training.vue')

print('patch_challenge_matrix.py done')
