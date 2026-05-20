// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
// Use lazy-loaded route components to reduce initial bundle size
const Home = () => import('../components/Home.vue')
const Auth = () => import('../components/Auth.vue')
const Games = () => import('../components/Games.vue')
const Teams = () => import('../components/Teams.vue')
const Submissions = () => import('../components/Submissions.vue')
const Scoreboard = () => import('../components/Scoreboard.vue')
const AdminPanel = () => import('../components/AdminPanel.vue')
const AdminSetup = () => import('../components/AdminSetup.vue')
const KnowledgeList = () => import('../components/KnowledgeList.vue')
const Events = () => import('../components/Events.vue')
const ArticleView = () => import('../components/ArticleView.vue')
const Archive = () => import('../components/Archive.vue')
const ProfileEdit = () => import('../components/ProfileEdit.vue')
const MyProfile = () => import('../components/MyProfile.vue')
const VerifyEmail = () => import('../components/VerifyEmail.vue')
const ForgotPassword = () => import('../components/ForgotPassword.vue')
const ResetPassword = () => import('../components/ResetPassword.vue')
const CTFCompetitions = () => import('../components/CTFCompetitions.vue')
const ChallengeDetailPage = () => import('../components/ChallengeDetailPage.vue')

const routes = [
  // 根路径重定向到平台首页
  { path: '/', redirect: '/home' },
  { path: '/home', name: 'PlatformHome', component: Home },
  { path: '/archive', name: 'Archive', component: Archive },
  { path: '/myprofile', name: 'MyProfile', component: MyProfile, meta: { requiresAuth: true } },
  { path: '/profile', name: 'Profile', component: ProfileEdit, meta: { requiresAuth: true } },
  { path: '/knowledge', name: 'Knowledge', component: KnowledgeList },
  { path: '/knowledge/new', name: 'ArticleNew', component: () => import('../components/ArticleUpload.vue') },
  { path: '/knowledge/:id', name: 'Article', component: ArticleView, props: true },
  { path: '/knowledge/:id/edit', name: 'ArticleEdit', component: () => import('../components/ArticleEdit.vue'), props: true },
  { path: '/auth', name: 'Auth', component: Auth },
  { path: '/verify-email', name: 'VerifyEmail', component: VerifyEmail },
  { path: '/forgot-password', name: 'ForgotPassword', component: ForgotPassword },
  { path: '/reset-password', name: 'ResetPassword', component: ResetPassword },
  { path: '/events', name: 'Events', component: Events },
  { path: '/ctf', name: 'CTFCompetitions', component: CTFCompetitions, meta: { requiresAuth: false } },
  { path: '/competition/:id', name: 'CompetitionDetail', component: CTFCompetitions, props: true, meta: { requiresAuth: true } },
  { path: '/challenge/:id', name: 'ChallengeDetail', component: ChallengeDetailPage, props: true, meta: { requiresAuth: true } },
  { path: '/games', name: 'Games', component: Games, meta: { requiresAuth: true } },
  // 动态路由：比如访问 /games/1 显示详情
  { path: '/games/:id', name: 'GameDetail', component: Games, props: true, meta: { requiresAuth: true } },
  { path: '/teams', name: 'Teams', component: Teams, meta: { requiresAuth: true } },
  { path: '/submissions', name: 'Submissions', component: Submissions, meta: { requiresAuth: true } },
  { path: '/admin', name: 'Admin', component: AdminPanel, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/dashboard', redirect: '/admin' },
  { path: '/admin/setup', name: 'AdminSetup', component: AdminSetup, meta: { requiresAuth: true } },
  // 如果需要单独的积分榜页面
  { path: '/scoreboard/:gameId', name: 'Scoreboard', component: Scoreboard, props: true, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：没登录且访问非 Auth 页面时，强制跳回 Auth
// 路由守卫：只在访问标记为 requiresAuth 的页面时强制跳转到登录
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('neepu_token')

  // 公共可访问路由名单（不需要登录）：首页与认证相关页面
  const publicNames = new Set(['PlatformHome', 'Auth', 'VerifyEmail', 'ForgotPassword', 'ResetPassword'])

  // 如果目标是公共页面，直接放行
  if (publicNames.has(to.name)) {
    return next()
  }

  // 其他所有页面都需要登录（除上面公共页）
  if (!token) {
    return next({ name: 'Auth' })
  }

  return next()
})

export default router