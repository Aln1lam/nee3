/** 平台管理侧栏 — 与路由子路径一一对应 */
export const ADMIN_MENU = [
  {
    key: 'dashboard',
    label: '仪表盘',
    code: 'DSH',
    cmd: 'overview',
    desc: '平台关键指标、资源用量与运行概况',
  },
  {
    key: 'users',
    label: '用户管理',
    code: 'USR',
    cmd: 'roster',
    desc: '账号检索、权限调整与选手信息',
  },
  {
    key: 'content',
    label: '内容管理',
    code: 'CNT',
    cmd: 'library',
    desc: '文章、Wiki 与平台内容维护',
  },
  {
    key: 'announcement',
    label: '公告管理',
    code: 'BLT',
    cmd: 'notices',
    desc: '平台公告与赛事通知维护',
  },
  {
    key: 'ctf',
    label: '靶场管理',
    code: 'CTF',
    cmd: 'arenas',
    desc: '赛事、题目、分组与归档',
  },
  {
    key: 'settings',
    label: '系统设置',
    code: 'CFG',
    cmd: 'settings',
    desc: '站点信息、注册策略与邮件配置',
  },
  {
    key: 'logs',
    label: '日志审计',
    code: 'LOG',
    cmd: 'audit',
    desc: '操作日志检索与导出',
  },
]

/** 旧 query ?tab= 与历史路径别名 */
export const ADMIN_TAB_ALIASES = {
  dashboard: 'dashboard',
  statistics: 'dashboard',
  users: 'users',
  content: 'content',
  announcement: 'announcement',
  carousel: 'dashboard',
  ctf: 'ctf',
  settings: 'settings',
  logs: 'logs',
  todos: 'dashboard',
  captcha: 'settings',
  email: 'settings',
  edit: 'settings',
  cluster: 'settings',
  sync: 'settings',
  media: 'content',
  oauth: 'settings',
  traffic: 'dashboard',
  lifecycle: 'ctf',
}

export const ADMIN_LEGACY_SECTIONS = [
  'statistics', 'captcha', 'email', 'edit', 'cluster', 'sync', 'media', 'oauth', 'traffic', 'lifecycle', 'todos', 'carousel',
]
