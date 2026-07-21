/**
 * CTF 管理端 API — 唯一入口
 *
 * 路由约定（长期维护请只扩展本文件）：
 * - 比赛写操作 / 分组 / 归档 / 流量：/api/competitions/admin/*
 * - 比赛只读列表：/api/competitions/（管理端展示）
 * - 题目 CRUD：/api/admin/challenges/games/*
 * - 动态附件包：/api/admin/dynamic-packages/*
 * - 作弊 / 首解：/api/admin/*
 * - 队伍：/api/teams/admin
 * - 排行榜（选手端）：/api/ctf/games/{id}/scoreboard*
 *
 * 已下线（410）：
 * - /api/games/*
 * - /api/admin/games CRUD / stats / export-scoreboard
 * - /api/ctf 除 scoreboard*、notices、health、cleanup 外的重叠路径
 *
 * 统计 / 导出主路径：/api/competitions/admin/{id}/stats 与 export-scoreboard
 */
import { authFetch } from '@/utils/http'
import axios from 'axios'

/** 需上传进度等 axios 特性的管理请求 */
const adminAxios = axios.create({ withCredentials: true })

function jsonBody(body) {
  return {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

function competitionsListUrl(opts = {}) {
  const params = new URLSearchParams()
  if (opts.game_type) params.set('game_type', opts.game_type)
  if (opts.include_ephemeral) params.set('include_ephemeral', '1')
  if (opts.exclude_training) params.set('exclude_training', '1')
  const qs = params.toString()
  return qs ? `/api/competitions/?${qs}` : '/api/competitions/'
}

export const ctfAdmin = {
  // —— 队伍 ——
  listTeams: () => authFetch('/api/teams/admin'),
  deleteTeam: (teamId) => authFetch(`/api/teams/admin/${teamId}`, { method: 'DELETE' }),
  deleteAllTeams: () => authFetch('/api/teams/admin', { method: 'DELETE' }),

  // —— 比赛（读）——
  /** @param {number} [_perPage] 保留参数兼容旧调用；competitions 一次返回全量 */
  /** @param {{ game_type?: string, include_ephemeral?: boolean, exclude_training?: boolean }} [opts] */
  listGames: (_perPage = 100, opts = {}) => authFetch(competitionsListUrl(opts)),
  listCompetitionsFallback: (_perPage = 100, opts = {}) => authFetch(competitionsListUrl(opts)),
  getGame: (gameId) => authFetch(`/api/competitions/${gameId}`),
  listChallenges: (gameId) => authFetch(`/api/challenges/games/${gameId}/challenges`),
  listAdminChallenges: (gameId) => authFetch(`/api/admin/challenges/games/${gameId}/challenges-list`),
  getScoreboard: (gameId) => authFetch(`/api/ctf/games/${gameId}/scoreboard`),

  // —— 比赛（写）——
  createGame: (payload) => authFetch('/api/competitions/admin/create', { method: 'POST', ...jsonBody(payload) }),
  updateGame: (gameId, payload) => authFetch(`/api/competitions/admin/${gameId}/update`, { method: 'PUT', ...jsonBody(payload) }),
  deleteGame: (gameId) => authFetch(`/api/competitions/admin/${gameId}/delete`, { method: 'DELETE' }),
  archiveGame: (gameId, payload = {}) => authFetch(`/api/competitions/admin/${gameId}/archive`, { method: 'POST', ...jsonBody(payload) }),

  // —— 分组 ——
  listDivisions: (gameId) => authFetch(`/api/competitions/${gameId}/divisions`),
  createDivision: (gameId, payload) => authFetch(`/api/competitions/admin/${gameId}/divisions/create`, { method: 'POST', ...jsonBody(payload) }),
  updateDivision: (gameId, divisionId, payload) => authFetch(`/api/competitions/admin/${gameId}/divisions/${divisionId}`, { method: 'PUT', ...jsonBody(payload) }),
  deleteDivision: (gameId, divisionId) => authFetch(`/api/competitions/admin/${gameId}/divisions/${divisionId}`, { method: 'DELETE' }),
  listDivisionMembers: (gameId, divisionId) => authFetch(`/api/competitions/admin/${gameId}/divisions/${divisionId}/members`),

  // —— 题目 ——
  getChallenge: (gameId, challengeId) => authFetch(`/api/admin/challenges/games/${gameId}/challenges/${challengeId}`),
  createChallenge: (gameId, payload) => authFetch(`/api/admin/challenges/games/${gameId}/challenges`, { method: 'POST', ...jsonBody(payload) }),
  createChallengeWithFile: (gameId, formData) => authFetch(`/api/admin/challenges/games/${gameId}/challenges`, { method: 'POST', body: formData }),
  updateChallenge: (gameId, challengeId, payload) => authFetch(`/api/admin/challenges/games/${gameId}/challenges/${challengeId}`, { method: 'PUT', ...jsonBody(payload) }),
  deleteChallenge: (gameId, challengeId) => authFetch(`/api/admin/challenges/games/${gameId}/challenges/${challengeId}`, { method: 'DELETE' }),
  uploadChallengeAttachment: (gameId, challengeId, formData) => authFetch(`/api/admin/challenges/games/${gameId}/challenges/${challengeId}/attachments`, { method: 'POST', body: formData }),
  listChallengeCategories: () => authFetch('/api/admin/challenges/categories'),
  adminChallengeListPath: (gameId) => `/api/admin/challenges/games/${gameId}/challenges-list`,

  // —— 动态附件包 ——
  listDynamicPackages: (challengeId) => authFetch(`/api/admin/dynamic-packages/challenges/${challengeId}/packages`),
  getDynamicPackageDistribution: (gameId) => authFetch(`/api/admin/dynamic-packages/statistics/package-distribution/${gameId}`),
  uploadDynamicPackages: (challengeId, formData, onUploadProgress) =>
    adminAxios.post(`/api/admin/dynamic-packages/challenges/${challengeId}/upload`, formData, { onUploadProgress }),
  updateDynamicPackage: (packageId, payload) =>
    authFetch(`/api/admin/dynamic-packages/packages/${packageId}`, { method: 'PUT', ...jsonBody(payload) }),
  deleteDynamicPackage: (packageId) =>
    authFetch(`/api/admin/dynamic-packages/packages/${packageId}`, { method: 'DELETE' }),

  // —— 赛季 ——
  listSeasons: () => authFetch('/api/admin/seasons'),
  createSeason: (payload) => authFetch('/api/admin/seasons', { method: 'POST', ...jsonBody(payload) }),
  updateSeason: (seasonId, payload) => authFetch(`/api/admin/seasons/${seasonId}`, { method: 'PUT', ...jsonBody(payload) }),
  deleteSeason: (seasonId) => authFetch(`/api/admin/seasons/${seasonId}`, { method: 'DELETE' }),

  // —— 作弊 / 首解 ——
  listCheatRecords: (params = 'page=1&per_page=50') => authFetch(`/api/admin/cheat-detection?${params}`),
  reviewCheatRecord: (recordId, payload = {}) => authFetch(`/api/admin/cheat-records/${recordId}/review`, { method: 'POST', ...jsonBody(payload) }),
  confirmCheatRecord: (recordId, payload = {}) => authFetch(`/api/admin/cheat-records/${recordId}/confirm`, { method: 'POST', ...jsonBody(payload) }),
  dismissCheatRecord: (recordId, payload = {}) => authFetch(`/api/admin/cheat-records/${recordId}/dismiss`, { method: 'POST', ...jsonBody(payload) }),
  listFirstSolves: (gameId, perPage = 100) => authFetch(`/api/admin/first-solves?game_id=${gameId}&per_page=${perPage}`),

  // —— 统计 / 导出 ——
  getGameStats: (gameId) => authFetch(`/api/competitions/admin/${gameId}/stats`),
  exportScoreboard: (gameId) => authFetch(`/api/competitions/admin/${gameId}/export-scoreboard`),
  listHammerMessages: (params = 'page=1&per_page=50') => authFetch(`/api/admin/hammer-messages?${params}`),

  // —— 流量捕获 ——
  listTrafficCaptures: (gameId, sync = true) => authFetch(`/api/competitions/admin/${gameId}/traffic-captures?sync=${sync ? 1 : 0}`),
  downloadTrafficCapture: (captureId) => authFetch(`/api/competitions/admin/traffic-captures/${captureId}/download`),
  deleteTrafficCapture: (captureId) => authFetch(`/api/competitions/admin/traffic-captures/${captureId}`, { method: 'DELETE' }),

  // —— 上传 / 资源 ——
  uploadImage: (formData) => authFetch('/api/uploads/upload-image/', { method: 'POST', body: formData }),
  resourceContentUrl: (resourceId) => `/api/resources/${resourceId}/content`,
}

export default ctfAdmin
