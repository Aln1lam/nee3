/** 平台管理侧栏 — 与路由子路径一一对应
 * staff: 管理员 + 协管可进（作弊审核在靶场管理内）
 * admin: 仅管理员
 */
export const ADMIN_MENU = [
  {
    key: 'dashboard',
    label: '仪表盘',
    code: 'DSH',
    cmd: 'overview',
    desc: '平台关键指标、资源用量与运行概况',
    access: 'admin',
  },
  {
    key: 'users',
    label: '用户管理',
    code: 'USR',
    cmd: 'roster',
    desc: '账号检索、权限调整与选手信息',
    access: 'admin',
  },
  {
    key: 'content',
    label: '内容管理',
    code: 'CNT',
    cmd: 'library',
    desc: '文章、Wiki 与平台内容维护',
    access: 'admin',
  },
  {
    key: 'announcement',
    label: '公告管理',
    code: 'BLT',
    cmd: 'notices',
    desc: '平台公告与赛事通知维护',
    access: 'admin',
  },
  {
    key: 'ctf',
    label: '靶场管理',
    code: 'CTF',
    cmd: 'arenas',
    desc: '赛事、题目、分组、作弊审核与归档',
    access: 'staff',
  },
  {
    key: 'settings',
    label: '系统设置',
    code: 'CFG',
    cmd: 'settings',
    desc: '站点信息、注册策略与邮件配置',
    access: 'admin',
  },
  {
    key: 'logs',
    label: '日志审计',
    code: 'LOG',
    cmd: 'audit',
    desc: '操作日志检索与导出',
    access: 'admin',
  },
]

/** 按当前用户过滤侧栏 */
export function filterAdminMenu(user) {
  const isAdmin = !!(user && user.is_admin)
  const isStaff = !!(user && (user.is_admin || user.is_moderator))
  if (!isStaff) return []
  return ADMIN_MENU.filter((item) => {
    if (item.access === 'staff') return true
    return isAdmin
  })
}

export function defaultAdminPath(user) {
  if (user?.is_admin) return '/admin/dashboard'
  if (user?.is_moderator) return '/admin/ctf?tab=cheat'
  return '/home'
}

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
