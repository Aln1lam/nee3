# -*- coding: utf-8 -*-
"""Second pass: fix remaining mojibake without GBK roundtrip."""
from pathlib import Path

ROOT = Path(r'E:\neepu\frontend\src\components')


def patch(rel: str, pairs: list[tuple[str, str]]) -> None:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8', errors='replace')
    for old, new in pairs:
        text = text.replace(old, new)
    p.write_text(text, encoding='utf-8', newline='\n')


def patch_ui(rel: str, pairs: list[tuple[str, str]]) -> None:
    p = Path(r'E:\neepu\frontend\src\components') / rel
    text = p.read_text(encoding='utf-8', errors='replace')
    for old, new in pairs:
        text = text.replace(old, new)
    p.write_text(text, encoding='utf-8', newline='\n')


# GameTeams.vue
patch('GameTeams.vue', [
    ("{{ team.school || '无组�? }}", "{{ team.school || '无组织' }}"),
    ("{{ viewedTeam.school || '无组�? }}", "{{ viewedTeam.school || '无组织' }}"),
    ('<span class="row-arrow">?/span>', '<span class="row-arrow">→</span>'),
    ('<p>建立属于你的战队，获取邀请码邀请队</p>', '<p>建立属于你的战队，获取邀请码邀请队友</p>'),
    ('placeholder="可�? />', 'placeholder="可选" />'),
    ('<span>邀请码�?code>', '<span>邀请码：<code>'),
    ('          队伍已创建，但尚未报名本赛事�?          <n-button', '          队伍已创建，但尚未报名本赛事。\n          <n-button'),
    ('<n-form-item label="所属组�?>', '<n-form-item label="所属组织">'),
    ('placeholder="选择或输入组�?', 'placeholder="选择或输入组织"'),
    ('placeholder="排行榜显示标�? />', 'placeholder="排行榜显示标签" />'),
    ('解出了题�?                <a', '解出了题目\n                <a'),
    ('{{ s.challenge_title }}</a>�?                {{ s.points }}', '{{ s.challenge_title }}</a>。\n                {{ s.points }}'),
    ('{{ t.members_count || 0 }} �?· #{{ t.id }}', '{{ t.members_count || 0 }} 人 · #{{ t.id }}'),
    ('<p>报名参赛时将自动创建单人队；也可在此主动创建或加入战</p>', '<p>报名参赛时将自动创建单人队；也可在此主动创建或加入战队</p>'),
    ("{ label: '无组�?, value: '无组�? },", "{ label: '无组织', value: '无组织' },"),
    ("choose: '创建或加入队�?,", "choose: '创建或加入队伍',"),
    ("choose: '正式赛事以战队为单位报名参赛。你可以创建新队伍，或使用邀请码加入队友的战队�?,",
     "choose: '正式赛事以战队为单位报名参赛。你可以创建新队伍，或使用邀请码加入队友的战队。',"),
    ("manage: '编辑队名、组织与标签 · 查看得分与解题记�?,",
     "manage: '编辑队名、组织与标签 · 查看得分与解题记录',"),
    ("editSchool.value = parsed.school || '无组�?", "editSchool.value = parsed.school || '无组织'"),
    ("message.info('你已有所属队�?)", "message.info('你已有所属队伍')"),
    ('/已经参加|已报�?.test(msg)', '/已经参加|已报名/.test(msg)'),
    ("message.warning('请输入队�?)", "message.warning('请输入队名')"),
    ("message.success('已为本赛事报�?)", "message.success('已为本赛事报名')"),
    ("message.success('已保�?)", "message.success('已保存')"),
])

# ErrorPage.vue
patch('ErrorPage.vue', [
    ('<p v-if="isTeapot" class="matrix-page-desc teapot-hint">�?我是茶壶，不能冲泡咖啡</p>',
     '<p v-if="isTeapot" class="matrix-page-desc teapot-hint">☕ 我是茶壶，不能冲泡咖啡。</p>'),
    ('@click="$router.back()">返回上一页</n-button>', '@click="$router.back()">返回上一页</n-button>'),
    ('class="error-trace-hint muted">错误�?{{ code }}</div>', 'class="error-trace-hint muted">错误码 {{ code }}</div>'),
    ("'401': { title: '未授�?, desc: '请先登录后再访问此页�? },",
     "'401': { title: '未授权', desc: '请先登录后再访问此页面' },"),
    ("'404': { title: '未找�?, desc: '页面不存在或已被移除' },",
     "'404': { title: '未找到', desc: '页面不存在或已被移除' },"),
    ("'418': { title: '我是茶壶', desc: '服务器拒绝冲泡咖啡（RFC 2324 · 418 I\\'m a teapot�? },",
     "'418': { title: '我是茶壶', desc: '服务器拒绝冲泡咖啡（RFC 2324 · 418 I\\'m a teapot）' },"),
    ("'500': { title: '服务器错�?, desc: '服务器内部出错，请稍后重�? },",
     "'500': { title: '服务器错误', desc: '服务器内部出错，请稍后重试' },"),
    ("'502': { title: '网关错误', desc: '上游服务不可用，请稍后重�? },",
     "'502': { title: '网关错误', desc: '上游服务不可用，请稍后重试' },"),
    ("unknown: { title: '出错�?, desc: '发生未知错误' },",
     "unknown: { title: '出错了', desc: '发生未知错误' },"),
])

# GameAdmin.vue
patch('GameAdmin.vue', [
    ('<n-form-item label="简�?>', '<n-form-item label="简介">'),
    ('<p class="muted">修改后同步更�?Timer �?TimeProgress 显示</p>',
     '<p class="muted">修改后同步更新 Timer 与 TimeProgress 显示</p>'),
    ('<n-form-item label="开始时�?>', '<n-form-item label="开始时间">'),
    ('placeholder="输入赛事名称以确�? />', 'placeholder="输入赛事名称以确认" />'),
    ("policies: '配置报名访问策略、邀请码与分组限制�?,",
     "policies: '配置报名访问策略、邀请码与分组限制',"),
    ("organize: '管理组织架构与学校范围�?,", "organize: '管理组织架构与学校范围',"),
    ("monitor: '实时监控提交与容器状态�?,", "monitor: '实时监控提交与容器状态',"),
    ("events: '查看赛事事件与审计日志�?,", "events: '查看赛事事件与审计日志',"),
    ("git: 'Git 仓库集成与题目同步�?,", "git: 'Git 仓库集成与题目同步',"),
    ("traffic: '流量分析�?Rune 脚本�?,", "traffic: '流量分析与 Rune 脚本',"),
    ("lifecycle: '归档、迁移与赛事生命周期管理�?,", "lifecycle: '归档、迁移与赛事生命周期管理',"),
    ("|| '该模块配置界面�?)", "|| '该模块配置界面'"),
    ("return '已归�?", "return '已归档'"),
    ("return '未开�?", "return '未开始'"),
    ("return '进行�?", "return '进行中'"),
    ("return '已结�?", "return '已结束'"),
    ("{ label: '未开�?, value: 'not_started' },", "{ label: '未开始', value: 'not_started' },"),
    ("{ label: '进行�?, value: 'ongoing' },", "{ label: '进行中', value: 'ongoing' },"),
    ("{ label: '已结�?, value: 'ended' },", "{ label: '已结束', value: 'ended' },"),
    ("{ label: '已归�?, value: 'archived' },", "{ label: '已归档', value: 'archived' },"),
    ("r.is_correct ? '�? : '�?)", "r.is_correct ? '✓' : '✗'"),
    ("message.success('已保�?)", "message.success('已保存')"),
    ("message.success('赛事已删�?)", "message.success('赛事已删除')"),
    ('<div class="stat-card"><span>题目�?/span>', '<div class="stat-card"><span>题目数</span>'),
    ('<div class="stat-card"><span>提交�?/span>', '<div class="stat-card"><span>提交数</span>'),
    ('<div class="stat-card"><span>状�?/span>', '<div class="stat-card"><span>状态</span>'),
    ('<n-form-item label="状�?>', '<n-form-item label="状态">'),
    ('>保存时间�?/UiButton>', '>保存时间线</UiButton>'),
    ('<p class="danger-text">此操作不可恢复，将删除赛事及所有相关数据�?/p>',
     '<p class="danger-text">此操作不可恢复，将删除赛事及所有相关数据。</p>'),
    ('>积分�?/router-link>', '>积分榜</router-link>'),
])

# DevComponents.vue - rewrite key broken strings
patch('DevComponents.vue', [
    ('title="组件实验�?', 'title="组件实验室"'),
    ('page-desc="Task 03 UI 组件�?+ Task 04 功能组件"', 'page-desc="Task 03 UI 组件库 + Task 04 功能组件"'),
    ('label="用户�? placeholder="�? 字符"', 'label="用户名" placeholder="如 8 字符"'),
    ('label="带错�? error="格式不正�?', 'label="带错误" error="格式不正确"'),
    ('label="测试倒计�?', 'label="测试倒计时"'),
    ('>上半�?', '>上半区'),
    ('>下半�?', '>下半区'),
    ("toast.info('这是一�?info 通知')", "toast.info('这是一条 info 通知')"),
    ("toast.confirm('确认执行操作�?, { onAccept: () => toast.success('已确�?) })",
     "toast.confirm('确认执行操作？', { onAccept: () => toast.success('已确认') })"),
    ('title="锤子（训练场 disabled�?', 'title="锤子（训练场 disabled）"'),
    ("organizations=\"['无组�?, '网安学部']\"", "organizations=\"['无组织', '网安学部']\""),
    ('## 连接器教�?', '## 连接器教程'),
    ('可管理）�?', '可管理）。'),
    ("toast.warning('倒计时结�?)", "toast.warning('倒计时结束')"),
    ("|| '(�?'", "|| '(空)'"),
    ('<p style="margin:0;font-size: var(--text-sm)">移动端友好的弹出层封�?/p>',
     '<p style="margin:0;font-size: var(--text-sm)">移动端友好的弹出层封装</p>'),
    ('<h2>Terminal（xterm.js + mock�?/h2>', '<h2>Terminal（xterm.js + mock）</h2>'),
    ("captcha_id: {{ captchaId || '�? }}", "captcha_id: {{ captchaId || '—' }}"),
    ('<h2>Article（Markdown + TOC�?/h2>', '<h2>Article（Markdown + TOC）</h2>'),
    ('<UiCard>主内容区域，可在账号设置、做题页等场景复用�?/UiCard>',
     '<UiCard>主内容区域，可在账号设置、做题页等场景复用。</UiCard>'),
])

# Account files
patch('AccountDelete.vue', [
    ('开发者彩�?· 账号仍安全保</p>', '开发者彩蛋 · 账号仍安全保留</p>'),
    ('栈帧已清理，但账号仍安全保留�?/p>', '栈帧已清理，但账号仍安全保留。</p>'),
    ('如需注销账号请联系管理员�?/p>', '如需注销账号请联系管理员。</p>'),
])
patch('AccountOAuth.vue', [
    ('<h2 class="matrix-page-title">第三方认�?/h2>', '<h2 class="matrix-page-title">第三方认证</h2>'),
    ('绑定 GitHub �?OAuth 登录方式', '绑定 GitHub 等 OAuth 登录方式'),
    ('<p class="hint">已配置的 OAuth 提供�?/p>', '<p class="hint">已配置的 OAuth 提供商</p>'),
    ('description="暂未配置 OAuth 提供�?>', 'description="暂未配置 OAuth 提供商">'),
    ('可在后台配�?GitHub �?OAuth 登录方式', '可在后台配置 GitHub 等 OAuth 登录方式'),
])

# UserPublicProfile
patch('UserPublicProfile.vue', [
    ("user?.school || '无组�? }}", "user?.school || '无组织' }}"),
    ("user?.email_verified ? '已验�? : '基础' }}", "user?.email_verified ? '已验证' : '基础' }}"),
    ('注册�?{{ formatDate', '注册于 {{ formatDate'),
    ('探索不止…�?/div>', '探索不止…</div>'),
    ('成员参与�?<strong>', '成员参与了 <strong>'),
    ('{{ p.game_title }}</strong>�?', '{{ p.game_title }}</strong>'),
    ('<div class="stat-label">解题�?/div>', '<div class="stat-label">解题数</div>'),
    ('<div class="stat-label">所在队�?/div>', '<div class="stat-label">所在队伍</div>'),
])

# shared components
patch('shared/Article.vue', [
    ('Markdown 编辑�?/div>', 'Markdown 编辑器</div>'),
    ('管理�?inline 编辑预留（Task 04�?*/', '管理员 inline 编辑预留（Task 04）*/'),
    ("btn.textContent = '已复�?", "btn.textContent = '已复制'"),
])
patch('shared/Captcha.vue', [
    ('alt="验证�?', 'alt="验证码"'),
    ('title="点击刷新验证�?', 'title="点击刷新验证码"'),
    ('>加载验证�?/button>', '>加载验证码</button>'),
    ('placeholder="验证码（至少4字符�?', 'placeholder="验证码（至少4字符）"'),
    ('`验证码至�?${props.minLength} 个字符`', '`验证码至少 ${props.minLength} 个字符`'),
])
patch('shared/HammerPanel.vue', [
    ('联系官方�?    </div>', '联系官方。\n    </div>'),
    ('与官�?选手实时沟通，可直接索�?flag 提示或你卡住的步骤即可�?',
     '与官方/选手实时沟通，可直接索要 flag 提示或你卡住的步骤即可。'),
    ('有问题请在此提�?/div>', '有问题请在此提问</div>'),
    ('发�?        </n-button>', '发送\n        </n-button>'),
    ('`锤子回复�?{', '`锤子回复：${'),
    ("message.success('已发�?)", "message.success('已发送')"),
    ("message.error(e.response?.data?.msg || '发送失�?)", "message.error(e.response?.data?.msg || '发送失败')"),
])
patch('shared/InstanceBox.vue', [
    ('<span class="instance-icon">?/span>', '<span class="instance-icon">🖥</span>'),
    ('（IP:端口 �?http://IP:端口</p>', '（IP:端口 或 http://IP:端口）</p>'),
    ("|| '�? }}", "|| '—' }}"),
    ('>销�?/n-button>', '>销毁</n-button>'),
    ("return '运行�?", "return '运行中'"),
    ("return '启动�?", "return '启动中'"),
    ("return '已停�?", "return '已停止'"),
    ("return '�?", "return '—'"),
    ("message.success('实例已延�?)", "message.success('实例已延长')"),
    ("message.success('实例已销�?)", "message.success('实例已销毁')"),
    ("message.error(e.response?.data?.msg || '销毁失�?)", "message.error(e.response?.data?.msg || '销毁失败')"),
    ("message.success('已复�?)", "message.success('已复制')"),
])
patch('shared/Terminal.vue', [
    ("disabled ? '已解�? : '提交' }}", "disabled ? '已解锁' : '提交' }}"),
    ("在下方输入框提�?,", "在下方输入框提交',"),
])

patch_ui('ui/UiTimer.vue', [
    ('倒计时到该时�?*/', '倒计时到该时刻*/'),
    ('距开始的开始时�?*/', '距开始的开始时间*/'),
    ('直接秒数倒计�?*/', '直接秒数倒计时*/'),
    ("return '倒计�?", "return '倒计时'"),
    ("return '距开�?", "return '距开始'"),
    ("return '距结�?", "return '距结束'"),
    ("return '已结�?", "return '已结束'"),
])

# GamesHub CSS comments only
patch('GamesHub.vue', [
    ('/* ??????rail ??????????????*/', '/* 左侧 sidebar rail 折叠时的布局 */'),
    ('/* ??????????????*/', '/* 赛事海报卡片样式 */'),
    ('/* ??????? ???*/', '/* 响应式：移动端 */'),
])

print('Pass 2 complete.')
