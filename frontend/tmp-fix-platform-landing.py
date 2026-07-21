# -*- coding: utf-8 -*-
from pathlib import Path
import re

p = Path(r'E:\neepu\frontend\src\components\PlatformLanding.vue')
lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
fixes = {
    23: '            <span>快速开始</span>',
    29: '              <span class="quick-label">进入赛事</span>',
    36: '              <span class="quick-label">训练靶场</span>',
    43: '              <span class="quick-label">知识库</span>',
    51: '            <span class="live-arrow">→</span>',
    65: '        <p class="linux-uname">Linux neepu-ctf 6.8.0 · x86_64 GNU/Linux</p>',
    66: '        <span>© {{ footerYears }} {{ footerOrg }}</span>',
    67: '        <a :href="footerUrl" target="_blank" rel="noopener">{{ footerOrg || \'东北电力大学\' }}</a>',
    68: '        <router-link to="/wiki">查看 Wiki</router-link>',
}
for lineno, content in fixes.items():
    idx = lineno - 1
    if 0 <= idx < len(lines):
        lines[idx] = content

text = '\n'.join(lines) + '\n'
# fix any remaining broken closing tags like ????/span>
text = re.sub(r'<span([^>]*)>[^<]*/span>', lambda m: f'<span{m.group(1)}></span>', text)
p.write_text(text, encoding='utf-8', newline='\n')
print('fixed PlatformLanding.vue')
