/**
 * 按 docs/route-architecture-topology.md 的前后端 API 契约清单。
 * expect: 'ok' | 'gone' | 'auth' | 'client'
 *   ok     → 登录后应为 2xx（业务失败可 4xx，但不能是 404/410）
 *   gone   → 必须 410（已下线路径，防前端误用）
 *   auth   → 未登录可为 401；登录后不应 404/410
 *   client → 故意测客户端错误（400/401/422 等），不能是 404/410/5xx
 */

/** @typedef {'ok'|'gone'|'auth'|'client'} ExpectKind */

/**
 * @typedef {object} ApiProbe
 * @property {string} id
 * @property {string} section  // 拓扑章节 3.x / 2.x 对照
 * @property {string} method
 * @property {string|((ctx: ProbeCtx) => string)} path
 * @property {ExpectKind} expect
 * @property {object|((ctx: ProbeCtx) => object|undefined)} [body]
 * @property {boolean} [admin]
 * @property {string} [note]
 */

/**
 * @typedef {object} ProbeCtx
 * @property {string|null} gameId
 * @property {string|null} challengeId
 */

/** @type {ApiProbe[]} */
export const API_PROBES = [
  // —— 3.2 公共 ——
  { id: 'health', section: '3.2', method: 'GET', path: '/api/health/', expect: 'ok' },
  { id: 'platform_info', section: '3.2', method: 'GET', path: '/api/platform/info', expect: 'ok' },
  { id: 'captcha', section: '3.2', method: 'GET', path: '/api/captcha/', expect: 'ok' },
  { id: 'bulletins', section: '3.2', method: 'GET', path: '/api/platform/bulletins', expect: 'ok' },
  { id: 'training_sidebar', section: '3.2', method: 'GET', path: '/api/platform/training/sidebar', expect: 'ok' },
  { id: 'external_events', section: '3.2', method: 'GET', path: '/api/external/events?region=both', expect: 'ok' },

  // —— 3.1 Auth ——
  { id: 'auth_me', section: '3.1', method: 'GET', path: '/api/auth/me', expect: 'auth' },
  { id: 'auth_users', section: '3.1', method: 'GET', path: '/api/auth/users', expect: 'ok' },
  { id: 'auth_oauth_providers', section: '3.1', method: 'GET', path: '/api/auth/oauth/providers', expect: 'ok' },

  // —— 3.3 Teams ——
  { id: 'teams_me', section: '3.3', method: 'GET', path: '/api/teams/me', expect: 'auth' },
  { id: 'teams_list', section: '3.3', method: 'GET', path: '/api/teams/', expect: 'auth' },
  { id: 'teams_admin', section: '3.3', method: 'GET', path: '/api/teams/admin', expect: 'auth', admin: true },

  // —— 3.4 Competitions 主路径 ——
  { id: 'comp_list', section: '3.4', method: 'GET', path: '/api/competitions/', expect: 'ok' },
  {
    id: 'comp_detail',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/competitions/${ctx.gameId}`,
    expect: 'ok',
    note: '需 gameId',
  },
  {
    id: 'comp_joined',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/competitions/${ctx.gameId}/joined`,
    expect: 'auth',
  },
  {
    id: 'comp_divisions',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/competitions/${ctx.gameId}/divisions`,
    expect: 'ok',
  },
  {
    id: 'comp_admin_stats',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/competitions/admin/${ctx.gameId}/stats`,
    expect: 'auth',
    admin: true,
  },

  // —— 3.4 CTF 仅 scoreboard ——
  {
    id: 'ctf_scoreboard',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/ctf/games/${ctx.gameId}/scoreboard`,
    expect: 'ok',
  },
  {
    id: 'ctf_scoreboard_timeline',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/ctf/games/${ctx.gameId}/scoreboard/timeline`,
    expect: 'ok',
  },
  {
    id: 'ctf_scoreboard_user',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/ctf/games/${ctx.gameId}/scoreboard/user`,
    expect: 'auth',
  },

  // —— 3.4 已下线 ——
  { id: 'gone_games_list', section: '3.4', method: 'GET', path: '/api/games/', expect: 'gone' },
  {
    id: 'gone_games_detail',
    section: '3.4',
    method: 'GET',
    path: (ctx) => `/api/games/${ctx.gameId}`,
    expect: 'gone',
  },
  {
    id: 'gone_admin_games',
    section: '3.4',
    method: 'GET',
    path: '/api/admin/games',
    expect: 'gone',
    admin: true,
  },
  {
    id: 'gone_admin_games_put',
    section: '3.4',
    method: 'PUT',
    path: (ctx) => `/api/admin/games/${ctx.gameId}`,
    expect: 'gone',
    admin: true,
    body: { title: 'e2e-should-410' },
  },
  {
    id: 'gone_ctf_join',
    section: '3.4',
    method: 'POST',
    path: (ctx) => `/api/ctf/games/${ctx.gameId}/join`,
    expect: 'gone',
    body: {},
  },

  // —— 3.5 Challenges ——
  {
    id: 'chal_list',
    section: '3.5',
    method: 'GET',
    path: (ctx) => `/api/challenges/games/${ctx.gameId}/challenges`,
    expect: 'auth',
  },
  {
    id: 'chal_detail',
    section: '3.5',
    method: 'GET',
    path: (ctx) => `/api/challenges/${ctx.challengeId}`,
    expect: 'auth',
  },
  {
    id: 'chal_stats',
    section: '3.5',
    method: 'GET',
    path: (ctx) => `/api/challenges/${ctx.challengeId}/stats`,
    expect: 'auth',
  },
  {
    id: 'chal_container_status',
    section: '3.5',
    method: 'GET',
    path: (ctx) => `/api/challenges/${ctx.challengeId}/container-status`,
    expect: 'auth',
  },
  {
    id: 'chal_hints',
    section: '3.5',
    method: 'GET',
    path: (ctx) => `/api/challenges/${ctx.challengeId}/hints`,
    expect: 'auth',
  },
  {
    id: 'chal_submissions',
    section: '3.5',
    method: 'GET',
    path: (ctx) => `/api/challenges/${ctx.challengeId}/submissions`,
    expect: 'auth',
  },

  // —— 3.7 Admin ——
  {
    id: 'admin_chal_list',
    section: '3.7',
    method: 'GET',
    path: (ctx) => `/api/admin/challenges/games/${ctx.gameId}/challenges-list`,
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_chal_categories',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/challenges/categories',
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_platform_dashboard',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/platform/dashboard',
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_platform_users',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/platform/users?page=1&per_page=10',
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_platform_config',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/platform/config',
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_platform_carousel',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/platform/carousel',
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_platform_announcements',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/platform/announcements',
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_platform_logs',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/platform/logs?page=1&per_page=10',
    expect: 'auth',
    admin: true,
  },
  {
    id: 'admin_cheat',
    section: '3.7',
    method: 'GET',
    path: '/api/admin/cheat-detection?page=1&per_page=10',
    expect: 'auth',
    admin: true,
  },

  // —— 已知前端误用（契约守卫）——
  {
    id: 'mismatch_admin_challenges_flat_post',
    section: 'mismatch',
    method: 'POST',
    path: '/api/admin/challenges',
    expect: 'client',
    admin: true,
    body: { title: 'e2e', flag: 'x', score: 100, game_id: 1 },
    note: '遗留 Admin.vue 路径；期望 404（不是成功创建）',
  },
]

/**
 * @param {number} status
 * @param {ExpectKind} expect
 */
export function statusMatchesExpect(status, expect) {
  if (expect === 'gone') return status === 410
  if (expect === 'ok') return status >= 200 && status < 300
  if (expect === 'auth') {
    // 已登录会话下：2xx 或合理业务 4xx（403/400），禁止 404/410/5xx
    if (status === 404 || status === 410) return false
    if (status >= 500) return false
    return status >= 200 && status < 500
  }
  if (expect === 'client') {
    // 误用路径：404/405/410/422/400 均可；禁止 2xx/5xx
    if (status >= 200 && status < 300) return false
    if (status >= 500) return false
    return true
  }
  return false
}
