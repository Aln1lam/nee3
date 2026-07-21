# -*- coding: utf-8 -*-
"""Fix ChallengeDetailPage back navigation to valid route names."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'ChallengeDetailPage.vue'
text = p.read_text(encoding='utf-8')

old = '''    function goBack() {
      if (challenge.value?.game_id) {
        router.push({ name: 'CompetitionDetail', params: { id: challenge.value.game_id } })
      } else {
        router.push({ name: 'CTFCompetitions' })
      }
    }'''

new = '''    function goBack() {
      if (challenge.value?.game_id) {
        router.push(`/games/${challenge.value.game_id}/challenges`)
      } else {
        router.push({ name: 'GamesHub' })
      }
    }'''

if old not in text:
    raise SystemExit('goBack block not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
print('ChallengeDetailPage nav ok')
