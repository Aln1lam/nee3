# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r'E:\neepu\frontend\src\components\GameDetail.vue')
lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
fixes = {
    84: '                >查看积分榜</UiButton>',
    90: '                >队伍管理</UiButton>',
    96: '                >前往训练场</UiButton>',
    111: '        <h2>队伍已被封禁</h2>',
    112: '        <p>你的队伍在本赛事中已被管理员封禁，无法继续参赛。</p>',
    113: '        <UiButton @click="$router.push(\'/games\')">返回赛事列表</UiButton>',
}
for lineno, content in fixes.items():
    lines[lineno - 1] = content
p.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print('fixed GameDetail.vue')
