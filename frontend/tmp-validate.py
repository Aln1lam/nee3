# -*- coding: utf-8 -*-
from pathlib import Path

root = Path(r'E:\neepu\frontend\src\components')
key = [
    'TitleBar.vue', 'GameAdmin.vue', 'Bulletin.vue', 'BulletinDetail.vue',
    'BulletinCreate.vue', 'Training.vue', 'GamesHub.vue', 'GameDetail.vue',
    'ChallengeWorkspace.vue', 'KnowledgeList.vue', 'PlatformLanding.vue',
    'GameTeams.vue', 'DevComponents.vue', 'ErrorPage.vue', 'UserList.vue',
    'MyProfile.vue', 'Admin.vue', 'Archive.vue', 'ArticleView.vue', 'Scoreboard.vue',
    'shared/MatrixShell.vue', 'shared/LinuxPrompt.vue',
]
for name in key:
    p = root / name
    if not p.exists():
        print(name, 'MISSING')
        continue
    text = p.read_text(encoding='utf-8', errors='replace')
    lines = text.count('\n') + 1
    ok = ('</template>' in text and '</script>' in text) if p.suffix == '.vue' else True
    rep = text.count('\ufffd')
    qm = 0
    for l in text.splitlines():
        if "'??'" in l or '"??"' in l or '>??<' in l or '????' in l:
            qm += 1
    broken = 0
    for l in text.splitlines():
        if '?/span>' in l or '?/n-' in l:
            broken += 1
    print(f'{name}: lines={lines} complete={ok} replacement={rep} qmark_lines={qm} broken_tags={broken}')
