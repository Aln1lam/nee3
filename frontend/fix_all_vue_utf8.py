# -*- coding: utf-8 -*-
"""Fix UTF-8 Chinese corruption in Vue components."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r'E:\neepu\frontend\src\components')


def write(rel: str, text: str) -> None:
    p = ROOT / rel if not rel.startswith('components/') else Path(r'E:\neepu\frontend\src') / rel
    p.write_text(text, encoding='utf-8', newline='\n')


def patch_lines(rel: str, fixes: dict[int, str]) -> None:
    p = ROOT / rel
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    for lineno, content in fixes.items():
        if 1 <= lineno <= len(lines):
            lines[lineno - 1] = content
    p.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def patch_replacements(rel: str, pairs: list[tuple[str, str]]) -> None:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8', errors='replace')
    for old, new in pairs:
        text = text.replace(old, new)
    p.write_text(text, encoding='utf-8', newline='\n')


def fix_broken_close_tags(text: str) -> str:
    """Fix tags like 列表?/router-link> or �?/span>"""
    text = re.sub(
        r'([\u4e00-\u9fff\w])[^\s<]{0,2}/([A-Za-z][A-Za-z0-9-]*)>',
        r'\1</\2>',
        text,
    )
    return text


def try_gbk_line(line: str) -> str:
    if '\ufffd' not in line and '�' not in line:
        return line
    try:
        fixed = line.encode('gbk', errors='ignore').decode('utf-8', errors='replace')
        if fixed.count('\ufffd') < line.count('\ufffd') or ('�' in line and '�' not in fixed):
            return fixed
    except Exception:
        pass
    return line


def fix_gamedetail() -> None:
    src = Path(r'E:\neepu\frontend\tmp-gamedetail-good.vue').read_text(encoding='utf-8')
    cur = (ROOT / 'GameDetail.vue').read_text(encoding='utf-8', errors='replace')

    # Keep current template structure but restore Chinese
    template_fixes = {
        9: '        <button type="button" class="back-link" @click="$router.push(\'/games\')">← 返回赛事列表</button>',
        15: '        >编辑说明</UiButton>',
        19: '        <!-- 左侧：赛事介绍 -->',
        21: '          <h2 class="intro-heading">赛事介绍</h2>',
        26: '              <UiButton variant="primary" :loading="saving" @click="saveEdit">保存</UiButton>',
        27: '              <UiButton variant="ghost" @click="cancelEdit">取消</UiButton>',
        33: '        <!-- 右侧：海报 + 状态 + 参与按钮 -->',
        52: '                <UiTag variant="default" size="small">{{ game.challenge_count || 0 }} 道题</UiTag>',
        53: '                <UiTag variant="default" size="small">{{ game.participation_count || 0 }} 支队伍</UiTag>',
        54: '                <UiTag v-if="game.game_type === \'official\'" variant="info" size="small">正式赛</UiTag>',
        105: '      <p>赛事不存在或无权访问</p>',
        106: '      <UiButton @click="$router.push(\'/games\')">返回赛事列表</UiButton>',
    }
    patch_lines('GameDetail.vue', template_fixes)

    # Script: extract from good file, adapt API names
    m = re.search(r'<script>(.*)</script>', src, re.DOTALL)
    if not m:
        return
    script = m.group(1)
    script = script.replace('extractPosterPath', 'getGamePosterPath')
    script = script.replace(
        'const path = getGamePosterPath(game.value?.description)',
        'const path = getGamePosterPath(game.value)',
    )
    # Restore joined API from current file
    script = script.replace(
        """        const { data } = await axios.get('/api/competitions/my')
        const list = data?.data || data || []
        joined.value = list.some(g => (g.game_id || g.id) === parseInt(gameId.value, 10))""",
        """        const { data } = await axios.get(`/api/competitions/${gameId.value}/joined`)
        joined.value = !!data?.joined""",
    )
    script = script.replace(
        "const { data } = await axios.get('/api/teams/me', { _skipAuthClear: true })",
        "const { data } = await axios.get('/api/teams/me', {\n          params: { game_id: gameId.value },\n          _skipAuthClear: true,\n        })",
    )
    # Add teamHint
    if 'teamHint' not in script:
        script = script.replace(
            '    const primaryCta = computed(() => {',
            """    const teamHint = computed(() => {
      if (!loggedIn.value || isArchived.value || !game.value || hasTeam.value) return ''
      const now = Date.now()
      const end = game.value.end_time ? new Date(game.value.end_time).getTime() : Infinity
      if (now >= end) return ''
      return '正式赛事以战队为单位参赛，进入题目前请先创建或加入队伍。'
    })

    const primaryCta = computed(() => {""",
        )
    script = script.replace(
        'statusLabel, statusTagType, timeRange, phaseHint, primaryCta,',
        'statusLabel, statusTagType, timeRange, phaseHint, teamHint, primaryCta,',
    )
    cur_lines = (ROOT / 'GameDetail.vue').read_text(encoding='utf-8').splitlines()
    out = []
    in_script = False
    for line in cur_lines:
        if line.strip() == '<script>':
            out.append(line)
            out.append(script.strip())
            in_script = True
            continue
        if in_script:
            if line.strip() == '</script>':
                out.append(line)
                in_script = False
            continue
        out.append(line)
    (ROOT / 'GameDetail.vue').write_text('\n'.join(out) + '\n', encoding='utf-8', newline='\n')


def fix_titlebar() -> None:
    patch_lines('TitleBar.vue', {
        5: '      <button class="banner-close" @click="bannerDismissed = true" aria-label="关闭">×</button>',
        38: '            <span class="nav-label">管理</span>',
        63: '            <button class="avatar-btn" aria-label="用户菜单">',
        68: '              <span class="user-nick">{{ user.nickname || user.username || \'用户\' }}</span>',
        72: '        <n-button v-else size="small" type="primary" @click="navigate(\'/auth\')">登录</n-button>',
        149: "      if (t.includes('web')) return '🌐'",
        150: "      if (t.includes('pwn')) return '💥'",
        151: "      if (t.includes('crypto')) return '🔐'",
        152: "      if (t.includes('reverse') || t.includes('逆向')) return '🔄'",
        153: "      return '🏁'",
        170: "        { label: '概览', path: `/games/${id}` },",
        171: "        { label: '题目', path: `/games/${id}/challenges` },",
        172: "        { label: '积分榜', path: `/games/${id}/scoreboard` },",
        173: "        { label: '队伍', path: `/games/${id}/teams` },",
        174: "        { label: '返回', path: '/games' },",
        185: "      { label: `${props.user?.nickname || '用户'} · ${userHexId.value}`, key: 'info', disabled: true },",
        187: "      { label: '复制临时身份码', key: 'tempcode' },",
        188: "      { label: '账号设置', key: 'settings' },",
        189: "      ...(props.user?.is_admin ? [{ label: '管理后台', key: 'admin' }] : []),",
        191: "      { label: '退出', key: 'logout' },",
        235: '            message.success(`已复制临时身份码：${code}`)',
        236: '          }).catch(() => message.info(`临时身份码：${code}`))',
        238: '          message.info(`临时身份码：${code}`)',
        265: "      platformName.value = info.name || platformName.value || 'CTF 平台'",
    })


def fix_bulletin() -> None:
    patch_lines('Bulletin.vue', {
        10: '        <h2 class="sidebar-rail-title">公告中心</h2>',
        11: '        <p class="sidebar-desc sidebar-rail-sub">BULLETIN · FEED</p>',
        17: '          <span class="row-label">全部公告</span>',
        22: '          <span class="row-label">当前页</span>',
        31: '          <span class="row-label">发布公告</span>',
        32: '          <span class="row-arrow">→</span>',
        39: '          <span>返回首页</span>',
        43: '          <span>查看赛事</span>',
        51: "      :aria-label=\"collapsed ? '展开侧栏' : '收起侧栏'\"",
        54: '      <span class="chevron" :class="{ \'is-collapsed\': collapsed }">‹</span>',
        60: '        <h2 class="matrix-page-title">公告列表</h2>',
        61: '        <p class="matrix-page-desc">平台公告 · 赛事通知 · 更新动态</p>',
        79: '                  <span class="item-link">阅读全文 →</span>',
        86: '          <p>暂无公告</p>',
        87: '          <span class="muted">管理员可在后台发布平台公告</span>',
    })


def fix_training() -> None:
    patch_lines('Training.vue', {
        15: '          <router-link to="/training" class="sidebar-title sidebar-rail-title">练习场列表</router-link>',
        16: '          <n-tag size="small" type="success" :bordered="false">永久开放</n-tag>',
        66: '      <span class="chevron" :class="{ \'is-collapsed\': collapsed }">‹</span>',
        73: '            <h2 class="matrix-page-title">创建练习场</h2>',
        77: '            <n-form-item label="练习场名称">',
        80: '            <n-form-item label="简介">',
        91: '            <h2 class="matrix-page-title">开始今日份的训练！</h2>',
        92: '            <p class="matrix-page-desc">',
        93: '              从左侧选择练习场 · 无时间限制 · 无限重试 · 不计入正式赛事积分',
        107: '                <span class="quick-meta">{{ g.challenge_count || 0 }} 题</span>',
        110: '              <span class="quick-link">进入练习 →</span>',
        115: '            <p>暂无练习场</p>',
        116: '            <p class="muted">管理员可创建练习场，或运行 <code>python backend/init_ctf.py</code> 初始化示例数据</p>',
        130: '            <span>创建练习场</span>',
        131: '            <span class="row-arrow">→</span>',
        141: "          :back-link=\"{ to: '/training', label: '← 返回练习场列表' }\"",
        146: '    <n-modal v-model:show="showGameInfo" preset="card" title="练习场说明" style="max-width: 560px">',
        207: "      if (title.includes('二进制') || title.includes('pwn')) return 'PWN'",
        221: '        // 若 sidebar 接口未返回训练数据，则回退到竞赛 API',
        262: "        console.error('加载练习场失败', e)",
        272: "        message.warning('请先登录后再进入练习场')",
        280: "        message.error(e.response?.data?.msg || '进入练习场失败')",
        311: "        message.success('练习场创建成功')",
        334: "      isArchivedGame.value ? '查看归档信息' : '查看练习场信息',",
        339: "        ? '\\n\\n> 本题为**归档赛事**题目，内容已从正式比赛迁移至练习场，仅供学习复盘。'",
        347: "        + 'TCP 类题目请使用 netcat 连接，更多环境配置请参阅题目说明与部署文档。'",
    })


def fix_platform_and_gameshub() -> None:
    import subprocess
    subprocess.run(['python', r'E:\neepu\frontend\tmp-fix-gameshub.py'], check=True)
    subprocess.run(['python', r'E:\neepu\frontend\tmp-fix-platform-landing.py'], check=True)
    patch_replacements('PlatformLanding.vue', [
        ("<p class=\"hero-desc\">?????? CTF ???? ? ???? ? Wiki ??</p>",
         "<p class=\"hero-desc\">东北电力大学 CTF 实训平台 · 赛事刷题 · Wiki 教程</p>"),
        ("return name.endsWith('??') ? name.slice(0, -2) : name",
         "return name.endsWith('平台') ? name.slice(0, -2) : name"),
        ("return name.endsWith('??') ? '??' : ''",
         "return name.endsWith('平台') ? '平台' : ''"),
        ("{ code: 'WEB', title: 'Web ??', desc: 'SQL ???XSS ?????', action: () => router.push('/training') }",
         "{ code: 'WEB', title: 'Web 安全', desc: 'SQL注入、XSS 等经典题型', action: () => router.push('/training') }"),
        ("{ code: 'PWN', title: '???', desc: '????ROP ?????', action: () => router.push('/training') }",
         "{ code: 'PWN', title: '二进制', desc: '栈溢出、ROP 与逆向分析', action: () => router.push('/training') }"),
        ("{ code: 'CTF', title: '????', desc: '????????????', action: () => router.push('/games') }",
         "{ code: 'CTF', title: '正式赛事', desc: '校内赛、积分赛与排行榜', action: () => router.push('/games') }"),
        ("{ code: 'DOC', title: 'Wiki ??', desc: 'WriteUp ???????', action: () => router.push('/wiki') }",
         "{ code: 'DOC', title: 'Wiki 教程', desc: 'WriteUp 与知识库文档', action: () => router.push('/wiki') }"),
    ])


def fix_mojibake_files() -> None:
    files = list(ROOT.rglob('*.vue')) + list((ROOT / 'ui').rglob('*.vue'))
    for p in files:
        text = p.read_text(encoding='utf-8', errors='replace')
        if '\ufffd' not in text and '�' not in text:
            continue
        lines = [try_gbk_line(ln) for ln in text.splitlines()]
        new_text = fix_broken_close_tags('\n'.join(lines) + '\n')
        p.write_text(new_text, encoding='utf-8', newline='\n')


def fix_misc() -> None:
    patch_replacements('ToastContainer.vue', [
        ('aria-label="??"', 'aria-label="关闭"'),
        ('@click.stop="dismiss(t.id)">�</button>', '@click.stop="dismiss(t.id)">×</button>'),
    ])
    # Run extracted fix for ErrorPage, AccountSettings, etc.
    import importlib.util
    spec = importlib.util.spec_from_file_location('extfix', r'E:\neepu\frontend\tmp-extracted-fix.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def main() -> None:
    fix_gamedetail()
    fix_titlebar()
    fix_bulletin()
    fix_training()
    fix_platform_and_gameshub()
    fix_mojibake_files()
    fix_misc()
    print('All fixes applied.')


if __name__ == '__main__':
    main()
