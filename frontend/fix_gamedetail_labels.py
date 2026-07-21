# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(__file__).resolve().parent / 'src' / 'components' / 'GameDetail.vue'
t = p.read_text(encoding='utf-8')
t = t.replace(
    '@click="$router.push(`/games/${gameId}/teams`)"\n                >编辑赛事</UiButton>',
    '@click="$router.push(`/games/${gameId}/teams`)"\n                >战队</UiButton>',
    1,
)
t = t.replace(
    '@click="$router.push(`/training/${gameId}`)"\n                >排行榜</UiButton>',
    '@click="$router.push(`/training/${gameId}`)"\n                >进入练习</UiButton>',
    1,
)
t = t.replace(
    "return { label: '登录参赛 →', action: () => router.push(`/games/${gameId.value}/scoreboard`) }",
    "return { label: '查看排行 →', action: () => router.push(`/games/${gameId.value}/scoreboard`) }",
    1,
)
p.write_text(t, encoding='utf-8', newline='\n')
print('ok')
