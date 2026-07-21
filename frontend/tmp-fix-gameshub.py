# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r'E:\neepu\frontend\src\components\GamesHub.vue')
lines = p.read_text(encoding='utf-8').splitlines()
fixes = {
    11: '          <UiButton size="small" variant="primary" @click="openCreate">创建赛事</UiButton>',
    31: '            <p>暂无赛事</p>',
    32: '            <p class="empty-hint">',
    33: '              管理员可创建赛事，或先前往',
    34: '              <router-link to="/training">训练场</router-link>',
    53: '          <span>其他赛事</span>',
    54: '          <span class="other-chevron">↓</span>',
    61: '        :aria-label="collapsed ? \'展开侧栏\' : \'收起侧栏\'"',
    64: '        <span class="chevron" :class="{ \'is-collapsed\': collapsed }">‹</span>',
    67: '      <!-- 右侧：赛事海报（点击进入详情页） -->',
    107: '          <p class="poster-enter-hint">点击进入赛事详情</p>',
    111: '          <h2 v-if="featuredGames.length">选择左侧赛事查看详情</h2>',
    112: '          <h2 v-else>暂无可参加赛事</h2>',
    113: '          <p v-if="!featuredGames.length">请等待管理员创建赛事，或运行下方命令初始化示例数据</p>',
    117: '              <router-link to="/training">开始训练</router-link>',
    118: '              <router-link to="/wiki">查看 Wiki</router-link>',
    130: '      <h3>其他赛事</h3>',
}
for lineno, content in fixes.items():
    idx = lineno - 1
    if 0 <= idx < len(lines):
        lines[idx] = content

text = '\n'.join(lines) + '\n'
text = text.replace(
    "return g?.is_hosted || (g?.title || '').includes('??')",
    "return g?.is_hosted || (g?.title || '').includes('托管')",
)
p.write_text(text, encoding='utf-8', newline='\n')
print('fixed GamesHub.vue')
