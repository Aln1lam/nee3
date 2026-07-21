# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'

# embedded prop — hide MatrixShell page head inside Training layout
cw = ROOT / 'ChallengeWorkspace.vue'
text = cw.read_text(encoding='utf-8')

if 'embedded:' not in text:
    text = text.replace(
        "    backLink: { type: Object, default: null },\n  },",
        "    backLink: { type: Object, default: null },\n    embedded: { type: Boolean, default: false },\n  },",
        1,
    )

old = '''    const shellPagePrompt = computed(() =>
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
    })'''

new = '''    const shellPagePrompt = computed(() => {
      if (props.embedded) return ''
      return props.mode === 'training'
        ? `cd /training/${props.gameId}`
        : `curl /games/${props.gameId}/challenges`
    })
    const shellPageTitle = computed(() => {
      if (props.embedded) return ''
      return props.gameTitle || (props.mode === 'training' ? '练习场' : '赛事题目')
    })
    const shellPageDesc = computed(() => {
      if (props.embedded) return ''
      if (props.mode === 'training') return '永久开放 · 无时间限制 · 不计入正式积分'
      return props.gameStatus || '选择左侧题目开始挑战'
    })'''

if old in text:
    text = text.replace(old, new, 1)
    print('ok ChallengeWorkspace embedded head')
else:
    print('SKIP ChallengeWorkspace embedded')

cw.write_text(text, encoding='utf-8', newline='\n')

tr = ROOT / 'Training.vue'
tt = tr.read_text(encoding='utf-8')
old2 = '''        <ChallengeWorkspace
          :game-id="selectedGame.id"
          mode="training"
          :game-title="selectedGame.title"
        />'''
new2 = '''        <ChallengeWorkspace
          :game-id="selectedGame.id"
          mode="training"
          :game-title="selectedGame.title"
          embedded
        />'''
if old2 in tt:
    tr.write_text(tt.replace(old2, new2, 1), encoding='utf-8', newline='\n')
    print('ok Training embedded prop')
else:
    print('SKIP Training embedded')
