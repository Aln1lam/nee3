/**
 * 路由清单 — 对齐 docs/route-architecture-topology.md §2
 * E2E 按 section 顺序扫描（2.1 → 2.5）。
 */

/** @typedef {'public'|'auth'|'admin'} AuthLevel */

/**
 * @typedef {object} TopologyRoute
 * @property {string} path
 * @property {string} name
 * @property {string} section  // 2.1 | 2.2 | ...
 * @property {AuthLevel} auth
 * @property {boolean} [dynamic]  需要运行时填充 :id / :gameId
 * @property {string} [aliasOf]
 * @property {string[]} [expectUrl]  期望最终 URL 匹配（正则字符串）
 * @property {boolean} [skipScan]  仅作别名验证，不做深度交互
 * @property {string} [note]
 */

/** §2.1 落地 / 公共 */
export const SECTION_21_LANDING = [
  { path: '/', name: 'Landing', section: '2.1', auth: 'public' },
  { path: '/home', name: 'PlatformHome', section: '2.1', auth: 'auth' },
  { path: '/archive', name: 'Archive', section: '2.1', auth: 'public' },
  { path: '/events', name: 'Events', section: '2.1', auth: 'public' },
  { path: '/magic/sakana', name: 'MagicSakana', section: '2.1', auth: 'public' },
  { path: '/error/404', name: 'HttpError', section: '2.1', auth: 'public' },
  {
    path: '/__e2e_missing_page__',
    name: 'CatchAll404',
    section: '2.1',
    auth: 'public',
    expectUrl: ['/error/404'],
    note: '通配 → /error/404',
  },
]

/** §2.2 账号 / 认证 */
export const SECTION_22_ACCOUNT = [
  { path: '/auth', name: 'Auth', section: '2.2', auth: 'public' },
  { path: '/account/login', name: 'AccountLoginAlias', section: '2.2', auth: 'public', expectUrl: ['/auth'], aliasOf: '/auth' },
  { path: '/account/register', name: 'AccountRegisterAlias', section: '2.2', auth: 'public', expectUrl: ['/auth'], aliasOf: '/auth' },
  { path: '/verify-email', name: 'VerifyEmail', section: '2.2', auth: 'public' },
  { path: '/forgot-password', name: 'ForgotPassword', section: '2.2', auth: 'public' },
  { path: '/reset-password', name: 'ResetPassword', section: '2.2', auth: 'public' },
  { path: '/account/settings/info', name: 'SettingsInfo', section: '2.2', auth: 'auth' },
  { path: '/account/settings/password', name: 'SettingsPassword', section: '2.2', auth: 'auth' },
  { path: '/account/settings/oauth', name: 'SettingsOAuth', section: '2.2', auth: 'auth' },
  { path: '/account/settings/mov-esp-ebp-pop-ebp', name: 'SettingsDelete', section: '2.2', auth: 'auth' },
  { path: '/myprofile', name: 'MyProfile', section: '2.2', auth: 'auth' },
  { path: '/profile', name: 'ProfileAlias', section: '2.2', auth: 'auth', expectUrl: ['/account/settings'], aliasOf: '/account/settings/info' },
]

/** §2.3 公告 / Wiki / 用户 */
export const SECTION_23_CONTENT = [
  { path: '/bulletin', name: 'Bulletin', section: '2.3', auth: 'public' },
  { path: '/bulletin/create', name: 'BulletinCreate', section: '2.3', auth: 'admin' },
  { path: '/wiki', name: 'Wiki', section: '2.3', auth: 'public' },
  { path: '/knowledge/new', name: 'ArticleNew', section: '2.3', auth: 'public' },
  { path: '/users', name: 'UserList', section: '2.3', auth: 'public' },
]

/** §2.4 训练 / 赛事 / 做题（静态入口；动态路由由运行时补全） */
export const SECTION_24_GAMES_STATIC = [
  { path: '/training', name: 'Training', section: '2.4', auth: 'public' },
  { path: '/games', name: 'GamesHub', section: '2.4', auth: 'public' },
  { path: '/ctf', name: 'CtfAlias', section: '2.4', auth: 'public', expectUrl: ['/games'], aliasOf: '/games' },
  { path: '/teams', name: 'Teams', section: '2.4', auth: 'auth' },
  { path: '/submissions', name: 'Submissions', section: '2.4', auth: 'auth' },
]

/** §2.5 管理后台 */
export const SECTION_25_ADMIN = [
  { path: '/admin/dashboard', name: 'AdminDashboard', section: '2.5', auth: 'admin' },
  { path: '/admin/users', name: 'AdminUsers', section: '2.5', auth: 'admin' },
  { path: '/admin/content', name: 'AdminContent', section: '2.5', auth: 'admin' },
  { path: '/admin/announcement', name: 'AdminAnnouncement', section: '2.5', auth: 'admin' },
  { path: '/admin/carousel', name: 'AdminCarousel', section: '2.5', auth: 'admin' },
  { path: '/admin/ctf', name: 'AdminCtf', section: '2.5', auth: 'admin' },
  { path: '/admin/settings', name: 'AdminSettings', section: '2.5', auth: 'admin' },
  { path: '/admin/logs', name: 'AdminLogs', section: '2.5', auth: 'admin' },
  { path: '/admin/setup', name: 'AdminSetup', section: '2.5', auth: 'auth' },
]

/**
 * 根据赛事 ID 展开 §2.4 动态路由
 * @param {string} gameId
 */
export function expandGameRoutes(gameId) {
  const id = String(gameId)
  return [
    { path: `/games/${id}`, name: 'GameDetail', section: '2.4', auth: 'public', dynamic: true },
    { path: `/games/${id}/challenges`, name: 'GameChallenges', section: '2.4', auth: 'auth', dynamic: true },
    { path: `/games/${id}/scoreboard`, name: 'GameScoreboard', section: '2.4', auth: 'public', dynamic: true },
    { path: `/games/${id}/teams`, name: 'GameTeams', section: '2.4', auth: 'auth', dynamic: true },
    { path: `/games/${id}/teams/choose`, name: 'GameTeamsChoose', section: '2.4', auth: 'auth', dynamic: true },
    { path: `/competition/${id}`, name: 'CompetitionAlias', section: '2.4', auth: 'auth', expectUrl: [`/games/${id}/challenges`], aliasOf: `/games/${id}/challenges`, dynamic: true },
    { path: `/scoreboard/${id}`, name: 'ScoreboardAlias', section: '2.4', auth: 'public', expectUrl: [`/games/${id}/scoreboard`], aliasOf: `/games/${id}/scoreboard`, dynamic: true },
  ]
}

/** 拓扑扫描顺序（不含动态路由） */
export const TOPOLOGY_STATIC_ORDER = [
  ...SECTION_21_LANDING,
  ...SECTION_22_ACCOUNT,
  ...SECTION_23_CONTENT,
  ...SECTION_24_GAMES_STATIC,
  ...SECTION_25_ADMIN,
]

export const TOPOLOGY_DOC = 'docs/route-architecture-topology.md'
