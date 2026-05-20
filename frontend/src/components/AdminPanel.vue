<template>
  <div class="admin-panel">
    <!-- 侧边栏导航 -->
    <aside class="sidebar">
      <div class="logo-section">
        <h1>🛠️ NEEPU 管理后台</h1>
        <p class="version">v1.0</p>
      </div>

      <nav class="nav-menu">
        <button 
          v-for="item in menuItems"
          :key="item.id"
          :class="['nav-item', { active: activeMenu === item.id }]"
          @click="activeMenu = item.id"
        >
          <span class="icon">{{ item.icon }}</span>
          <span class="label">{{ item.label }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">👤</div>
          <div class="user-detail">
            <div class="user-name">{{ currentUser?.nickname }}</div>
            <div class="user-role">🔧 管理员</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <div class="top-bar-left">
          <h2 class="page-title">{{ getCurrentMenuLabel() }}</h2>
          <p class="page-breadcrumb">管理后台 > {{ getCurrentMenuLabel() }}</p>
        </div>
        <div class="top-bar-right">
          <span class="time-display">
            <i class="icon-time">🕐</i>
            {{ currentTime }}
          </span>
          <button class="btn-logout" @click="logout" style="margin-left: 20px; padding: 8px 16px; background: #ff6b6b; color: white; border: none; border-radius: 4px; cursor: pointer;">
            返回主页
          </button>
        </div>
      </header>

      <!-- 内容区 -->
      <div class="content-area">
        <!-- 仪表盘 -->
        <section v-show="activeMenu === 'dashboard'" class="menu-section">
          <PlatformDashboard />
        </section>

        <!-- 用户管理 -->
        <section v-show="activeMenu === 'users'" class="menu-section">
          <UserManagement />
        </section>

        <!-- 内容管理 -->
        <section v-show="activeMenu === 'content'" class="menu-section">
          <ContentManagement />
        </section>

        <!-- 公告管理 -->
        <section v-show="activeMenu === 'announcement'" class="menu-section">
          <AnnouncementManagement />
        </section>

        <!-- 轮播图管理 -->
        <section v-show="activeMenu === 'carousel'" class="menu-section">
          <CarouselManagement />
        </section>

        <!-- 代办分发 -->
        <section v-show="activeMenu === 'todos'" class="menu-section">
          <TodoDistribution />
        </section>

        <!-- 靶场管理 -->
        <section v-show="activeMenu === 'ctf'" class="menu-section">
          <CtfManagement />
        </section>

        <!-- 系统设置 -->
        <section v-show="activeMenu === 'settings'" class="menu-section">
          <SystemSettings />
        </section>

        <!-- 日志审计 -->
        <section v-show="activeMenu === 'logs'" class="menu-section">
          <LogAudit />
        </section>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, inject, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import PlatformDashboard from './admin/PlatformDashboard.vue'
import UserManagement from './admin/UserManagement.vue'
import ContentManagement from './admin/ContentManagement.vue'
import SystemSettings from './admin/SystemSettings.vue'
import LogAudit from './admin/LogAudit.vue'
import CtfManagement from './admin/CtfManagement.vue'
import AnnouncementManagement from './admin/AnnouncementManagement.vue'
import TodoDistribution from './admin/TodoDistribution.vue'
import CarouselManagement from './admin/CarouselManagement.vue'

export default {
  name: 'AdminPanel',
  components: {
    PlatformDashboard,
    UserManagement,
    ContentManagement,
    SystemSettings,
    LogAudit,
    CtfManagement,
    AnnouncementManagement,
    TodoDistribution,
    CarouselManagement
  },
  setup() {
    const router = useRouter()
    const axios = inject('axios')
    
    const activeMenu = ref('dashboard')
    const currentUser = ref(null)
    const currentTime = ref(new Date().toLocaleTimeString('zh-CN'))
    
    let timeInterval = null

    const menuItems = [
      { id: 'dashboard', label: '仪表盘', icon: '📊' },
      { id: 'users', label: '用户管理', icon: '👥' },
      { id: 'content', label: '内容管理', icon: '📰' },
      { id: 'announcement', label: '公告管理', icon: '📢' },
      { id: 'carousel', label: '轮播图管理', icon: '🖼️' },
      { id: 'todos', label: '代办分发', icon: '✉️' },
      { id: 'ctf', label: '靶场管理', icon: '🎯' },
      { id: 'settings', label: '系统设置', icon: '⚙️' },
      { id: 'logs', label: '日志审计', icon: '📋' }
    ]

    function getCurrentMenuLabel() {
      const item = menuItems.find(m => m.id === activeMenu.value)
      return item ? item.label : '仪表盘'
    }

    function loadCurrentUser() {
      const userStr = localStorage.getItem('neepu_user')
      if (userStr) {
        try {
          currentUser.value = JSON.parse(userStr)
        } catch (e) {}
      }
    }

    function logout() {
      router.push('/home')
    }

    function updateTime() {
      currentTime.value = new Date().toLocaleTimeString('zh-CN')
    }

    onMounted(() => {
      loadCurrentUser()
      timeInterval = setInterval(updateTime, 1000)
    })

    onUnmounted(() => {
      if (timeInterval) clearInterval(timeInterval)
    })

    return {
      activeMenu,
      currentUser,
      currentTime,
      menuItems,
      getCurrentMenuLabel,
      logout
    }
  }
}
</script>

<style scoped>
.admin-panel {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: #f5f7fa;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: linear-gradient(135deg, rgba(13,41,19,0.95), rgba(0,30,15,0.9));
  color: white;
  display: flex;
  flex-direction: column;
  border-right: 2px solid rgba(0,196,140,0.2);
  overflow-y: auto;
}

.logo-section {
  padding: 25px 20px;
  border-bottom: 2px solid rgba(0,196,140,0.3);
}

.logo-section h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.version {
  margin: 5px 0 0 0;
  font-size: 12px;
  opacity: 0.7;
}

.nav-menu {
  flex: 1;
  padding: 15px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  padding: 10px 15px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(0,196,140,0.2);
  color: rgba(255,255,255,0.9);
  border-radius: 8px;
  cursor: pointer;
  transition: all .2s ease;
  font-size: 14px;
  font-weight: 500;
  min-height: 44px;
  width: 100%;
  box-sizing: border-box;
}

.nav-item:hover {
  background: rgba(0,196,140,0.15);
  border-color: rgba(0,196,140,0.5);
  color: #fff;
}

.nav-item.active {
  background: rgba(0,196,140,0.3);
  border-color: rgba(0,196,140,0.8);
  color: #fff;
  box-shadow: 0 0 15px rgba(0,196,140,0.2);
}

.nav-item .icon {
  font-size: 16px;
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid rgba(0,196,140,0.2);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  margin-bottom: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: rgba(0,196,140,0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.user-detail {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
  opacity: 0.8;
}

.btn-logout {
  width: 100%;
  padding: 8px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: opacity .2s ease;
}

.btn-logout:hover {
  opacity: 0.9;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  background: white;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  padding: 12px 25px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.top-bar-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #222;
  margin: 0;
  padding: 0;
}

.page-breadcrumb {
  font-size: 12px;
  color: #999;
  margin: 0;
  padding: 0;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.time-display {
  font-size: 13px;
  color: #666;
  font-family: 'LXGW WenKai Mono', monospace;
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-time {
  font-size: 14px;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 25px;
}

.menu-section {
  animation: fadeIn .3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 1024px) {
  .sidebar {
    width: 220px;
  }
  
  .logo-section h1 {
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .admin-panel {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    padding: 10px;
  }
  
  .logo-section {
    flex: 1;
    padding: 10px;
    border-bottom: none;
    border-right: 1px solid rgba(0,196,140,0.2);
  }
  
  .nav-menu {
    flex-direction: row;
    flex: 1;
    padding: 0;
    gap: 5px;
  }
  
  .nav-item {
    padding: 8px 10px;
    font-size: 12px;
  }
  
  .nav-item .label {
    display: none;
  }
  
  .sidebar-footer {
    display: none;
  }
}
</style>
