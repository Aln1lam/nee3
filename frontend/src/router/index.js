// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'

const PlatformLanding = () => import('../components/PlatformLanding.vue')
const Home = () => import('../components/Home.vue')
const Auth = () => import('../components/Auth.vue')
const GamesHub = () => import('../components/GamesHub.vue')
const GameDetail = () => import('../components/GameDetail.vue')
const GameTeams = () => import('../components/GameTeams.vue')
const Teams = () => import('../components/Teams.vue')
const Submissions = () => import('../components/Submissions.vue')
const Scoreboard = () => import('../components/Scoreboard.vue')
const AdminPanel = () => import('../components/AdminPanel.vue')
const AdminSetup = () => import('../components/AdminSetup.vue')
const KnowledgeList = () => import('../components/KnowledgeList.vue')
const Events = () => import('../components/Events.vue')
const ArticleView = () => import('../components/ArticleView.vue')
const Archive = () => import('../components/Archive.vue')
const Bulletin = () => import('../components/Bulletin.vue')
const ProfileEdit = () => import('../components/ProfileEdit.vue')
const MyProfile = () => import('../components/MyProfile.vue')
const VerifyEmail = () => import('../components/VerifyEmail.vue')
const ForgotPassword = () => import('../components/ForgotPassword.vue')
const ResetPassword = () => import('../components/ResetPassword.vue')
const ChallengeWorkspace = () => import('../components/ChallengeWorkspace.vue')
const ChallengeDetailPage = () => import('../components/ChallengeDetailPage.vue')
const Training = () => import('../components/Training.vue')
const ErrorPage = () => import('../components/ErrorPage.vue')
const UserPublicProfile = () => import('../components/UserPublicProfile.vue')
const BulletinDetail = () => import('../components/BulletinDetail.vue')
const UserList = () => import('../components/UserList.vue')
const AccountSettings = () => import('../components/AccountSettings.vue')
const AccountPassword = () => import('../components/AccountPassword.vue')
const AccountOAuth = () => import('../components/AccountOAuth.vue')
const AccountDelete = () => import('../components/AccountDelete.vue')
const BulletinCreate = () => import('../components/BulletinCreate.vue')
const DevComponents = () => import('../components/DevComponents.vue')

import { ADMIN_MENU, ADMIN_LEGACY_SECTIONS } from '../config/adminMenu'

const AdminContent = () => import('../components/admin/AdminContent.vue')

/** 旧比赛管理子路由 → 平台靶场管理 Tab */
const GAME_ADMIN_CTF_TAB = {
  statistics: 'scoreboard',
  teams: 'teams',
  captures: 'traffic',
  monitor: 'cheat',
  events: 'cheat',
  traffic: 'traffic',
  hammers: 'challenges',
  challenges: 'challenges',
  edit: 'games',
  rules: 'games',
  policies: 'games',
  organize: 'games',
  git: 'games',
  lifecycle: 'games',
  timeline: 'games',
  delete: 'games',
}

/** 比赛管理子路由（Task 19 占位） */
const GAME_ADMIN_SECTIONS = [
  'statistics', 'edit', 'rules', 'policies', 'organize', 'hammers',
  'teams', 'monitor', 'events', 'git', 'traffic', 'lifecycle',
  'captures', 'timeline', 'delete',
]

const GAME_ADMIN_LABELS = {
  statistics: '统计',
  edit: '编辑',
  rules: '规则',
  policies: '访问策略',
  organize: '组织架构',
  hammers: 'Hammer 管理',
  teams: '队伍管理',
  monitor: '实时监控',
  events: '事件日志',
  git: 'Git 集成',
  traffic: '流量分析',
  lifecycle: '生命周期',
  captures: '流量捕获 PCAP',
  timeline: '时间线编辑',
  delete: '删除比赛',
}

const routes = [
  { path: '/', name: 'Landing', component: PlatformLanding },

  // 账号模块别名
  { path: '/account/login', redirect: to => ({ path: '/auth', query: { ...to.query, mode: 'login' } }) },
  { path: '/account/register', redirect: to => ({ path: '/auth', query: { ...to.query, mode: 'register' } }) },
  { path: '/account/forgot', redirect: '/forgot-password' },
  { path: '/account/reset', redirect: '/reset-password' },
  {
    path: '/account/settings',
    component: AccountSettings,
    meta: { requiresAuth: true },
    redirect: '/account/settings/info',
    children: [
      { path: 'info', name: 'SettingsInfo', component: ProfileEdit },
      { path: 'password', name: 'SettingsPassword', component: AccountPassword },
      { path: 'oauth', name: 'SettingsOAuth', component: AccountOAuth },
      { path: 'mov-esp-ebp-pop-ebp', name: 'SettingsDelete', component: AccountDelete },
    ],
  },
  { path: '/account/oauth', redirect: '/auth' },
  { path: '/account/verify', redirect: '/verify-email' },

  { path: '/home', name: 'PlatformHome', component: Home, meta: { requiresAuth: true } },
  { path: '/archive', name: 'Archive', component: Archive },
  { path: '/bulletin', name: 'Bulletin', component: Bulletin },
  { path: '/bulletin/create', name: 'BulletinCreate', component: BulletinCreate, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/bulletin/:id', name: 'BulletinDetail', component: BulletinDetail, props: true },
  { path: '/wiki/create', redirect: '/knowledge/new' },
  { path: '/users', name: 'UserList', component: UserList },
  { path: '/users/:id', name: 'UserProfile', component: UserPublicProfile, props: true },
  { path: '/myprofile', name: 'MyProfile', component: MyProfile, meta: { requiresAuth: true } },
  { path: '/profile', redirect: '/account/settings/info' },
  { path: '/wiki', name: 'Wiki', component: KnowledgeList },
  { path: '/knowledge', redirect: '/wiki' },
  { path: '/knowledge/new', name: 'ArticleNew', component: () => import('../components/ArticleUpload.vue') },
  { path: '/wiki/:id', name: 'WikiArticle', component: ArticleView, props: true },
  { path: '/knowledge/:id', redirect: to => `/wiki/${to.params.id}` },
  { path: '/knowledge/:id/edit', name: 'ArticleEdit', component: () => import('../components/ArticleEdit.vue'), props: true },

  { path: '/magic/sakana', name: 'MagicSakana', component: () => import('../components/MagicSakana.vue') },
  { path: '/auth', name: 'Auth', component: Auth },
  { path: '/verify-email', name: 'VerifyEmail', component: VerifyEmail },
  { path: '/forgot-password', name: 'ForgotPassword', component: ForgotPassword },
  { path: '/reset-password', name: 'ResetPassword', component: ResetPassword },
  { path: '/events', name: 'Events', component: Events },
  { path: '/training', name: 'Training', component: Training },
  {
    path: '/training/challenge/:id',
    name: 'TrainingChallenge',
    component: ChallengeWorkspace,
    props: (route) => ({
      gameId: route.params.id,
      mode: 'training',
      embedded: false,
    }),
    meta: { requiresAuth: true },
  },
  // 旧路径兼容：/training/:gameId → 独立做题大厅
  { path: '/training/:gameId', redirect: to => `/training/challenge/${to.params.gameId}` },

  // 赛事
  { path: '/games', name: 'GamesHub', component: GamesHub },
  { path: '/ctf', redirect: '/games' },
  { path: '/games/:id', name: 'GameDetail', component: GameDetail, props: true },
  {
    path: '/games/:id/challenges',
    name: 'GameChallenges',
    component: ChallengeWorkspace,
    props: (route) => ({
      gameId: route.params.id,
      mode: 'competition',
    }),
    meta: { requiresAuth: true },
  },
  { path: '/games/:id/scoreboard', name: 'GameScoreboard', component: Scoreboard, props: (route) => ({ gameId: route.params.id }) },
  { path: '/competition/:id', redirect: to => `/games/${to.params.id}/challenges` },
  { path: '/scoreboard/:gameId', redirect: to => `/games/${to.params.gameId}/scoreboard` },
  { path: '/games/:id/teams', name: 'GameTeams', component: GameTeams, props: true, meta: { requiresAuth: true } },
  { path: '/games/:id/teams/choose', name: 'GameTeamsChoose', component: GameTeams, props: true, meta: { requiresAuth: true } },
  { path: '/games/:id/teams/create', name: 'GameTeamsCreate', component: GameTeams, props: true, meta: { requiresAuth: true } },
  { path: '/games/:id/teams/join', name: 'GameTeamsJoin', component: GameTeams, props: true, meta: { requiresAuth: true } },
  { path: '/games/:id/teams/:teamId', name: 'GameTeamDetail', component: GameTeams, props: true, meta: { requiresAuth: true } },

  // 比赛管理（已迁至 /admin/ctf）
  {
    path: '/games/:id/admin',
    redirect: to => ({ path: '/admin/ctf', query: { game_id: to.params.id } }),
  },
  {
    path: '/games/:id/admin/challenges',
    redirect: to => ({ path: '/admin/ctf', query: { game_id: to.params.id, tab: 'challenges' } }),
  },
  ...GAME_ADMIN_SECTIONS.map(section => ({
    path: `/games/:id/admin/${section}`,
    redirect: to => ({
      path: '/admin/ctf',
      query: { game_id: to.params.id, tab: GAME_ADMIN_CTF_TAB[section] || 'games' },
    }),
  })),

  { path: '/challenge/:id', name: 'ChallengeDetail', component: ChallengeDetailPage, props: true, meta: { requiresAuth: true } },

  { path: '/teams', name: 'Teams', component: Teams, meta: { requiresAuth: true } },
  { path: '/submissions', name: 'Submissions', component: Submissions, meta: { requiresAuth: true } },
  {
    path: '/admin',
    component: AdminPanel,
    meta: { requiresAuth: true, requiresAdmin: true },
    redirect: '/admin/dashboard',
    children: ADMIN_MENU.map(item => ({
      path: item.key,
      name: `Admin${item.key.charAt(0).toUpperCase() + item.key.slice(1)}`,
      component: AdminContent,
      meta: {
        requiresAuth: true,
        requiresAdmin: true,
        adminView: item.key,
      },
    })),
  },
  ...ADMIN_LEGACY_SECTIONS.map(section => ({
    path: `/admin/${section}`,
    redirect: to => {
      const legacyMap = {
        statistics: '/admin/dashboard',
        media: '/admin/content',
        lifecycle: '/admin/ctf',
        traffic: '/admin/dashboard',
        todos: '/admin/dashboard',
      }
      return legacyMap[section] || '/admin/settings'
    },
  })),
  { path: '/admin/setup', name: 'AdminSetup', component: AdminSetup, meta: { requiresAuth: true } },

  // 开发调试（UI 组件演示）
  { path: '/dev/components', name: 'DevComponents', component: DevComponents, meta: { requiresAuth: true } },

  // 错误页
  { path: '/sigtrap/:code', name: 'Sigtrap', component: ErrorPage, props: true },
  { path: '/:pathMatch(.*)*', redirect: '/sigtrap/404' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

import { fetchSession } from '../services/auth'

const PUBLIC_ROUTES = new Set([
  'Landing', 'Auth', 'VerifyEmail', 'ForgotPassword', 'ResetPassword',
  'Wiki', 'WikiArticle', 'Archive', 'Bulletin', 'GamesHub', 'GameDetail',
  'Training', 'TrainingGame', 'Sigtrap',
  'BulletinDetail', 'UserList', 'UserProfile', 'GameScoreboard',
])

router.beforeEach(async (to, from, next) => {
  if (to.name === 'DevComponents' && !import.meta.env.DEV) {
    return next({ name: 'Sigtrap', params: { code: '404' } })
  }

  // 所有路由先恢复 Cookie 会话，避免公开页（如赛事详情）误判未登录
  const user = await fetchSession()

  if (PUBLIC_ROUTES.has(to.name)) {
    return next()
  }

  if (!user) {
    return next({ name: 'Auth', query: { redirect: to.fullPath } })
  }

  if (to.meta?.requiresAdmin && !user.is_admin) {
    return next({ name: 'Sigtrap', params: { code: '403' } })
  }

  return next()
})

export default router

export { ADMIN_MENU, ADMIN_LEGACY_SECTIONS, GAME_ADMIN_SECTIONS, GAME_ADMIN_LABELS }
