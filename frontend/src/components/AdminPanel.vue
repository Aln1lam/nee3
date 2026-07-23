<template>
  <div
    class="admin-layout layout-with-sidebar lab-deck"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <aside class="admin-sidebar sidebar-rail">
      <div class="sidebar-head sidebar-rail-head">
        <div class="sidebar-head-row">
          <router-link to="/admin/dashboard" class="sidebar-title sidebar-rail-title">运维管理</router-link>
        </div>
        <p class="sidebar-desc sidebar-rail-sub">ADMIN · OPS</p>
      </div>

      <nav class="sidebar-rail-nav admin-nav">
        <div class="sidebar-group">
          <div class="group-label">模块</div>
          <router-link
            v-for="item in menuItems"
            :key="item.key"
            :to="`/admin/${item.key}`"
            class="sidebar-item"
            :class="{ active: activeKey === item.key }"
          >
            <span class="item-code">{{ item.code }}</span>
            <span class="item-title">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-rail-footer sidebar-footer sidebar-footer-copy-wrap">
        <div class="sidebar-footer-copy">
          © 2022-2026
          <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">东北电力大学</a>
        </div>
      </div>

    </aside>

    <button
      type="button"
      class="sidebar-collapse-trigger"
      :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
      @click="toggleSidebar"
    >
      <span class="chevron" :class="{ 'is-collapsed': collapsed }">‹</span>
    </button>

    <main class="admin-main sidebar-main">
      <header v-if="currentMenu" class="matrix-page-head">
        <p class="matrix-page-prompt">{{ currentMenu.code }} · {{ currentMenu.label }}</p>
        <h2 class="matrix-page-title">{{ currentMenu.label }}</h2>
        <p class="matrix-page-desc">{{ currentMenu.desc }}</p>
      </header>
      <div class="admin-panel admin-content-wrap">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ADMIN_MENU } from '@/config/adminMenu'
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'

export default {
  name: 'AdminPanel',
  components: {},
  setup() {
    const route = useRoute()
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_admin_sidebar_collapsed')
    const menuItems = ADMIN_MENU

    const activeKey = computed(() => route.meta?.adminView || (route.path.startsWith('/admin/content') ? 'content' : route.path.split('/').pop()) || 'dashboard')
    const currentMenu = computed(() => menuItems.find(m => m.key === activeKey.value) || menuItems[0])

    return {
      collapsed,
      menuItems,
      activeKey,
      currentMenu,
      toggleSidebar,
    }
  },
}
</script>

<style scoped>
/* NEEPU_ADMIN_PANEL_HD */
.admin-layout,
.admin-main,
.admin-content-wrap {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial,
    "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #f3f4f6;
}
.admin-layout :deep(.matrix-page-title) {
  color: #f3f4f6 !important;
  font-weight: 700 !important;
  opacity: 1 !important;
}
.admin-layout :deep(.matrix-page-prompt),
.admin-layout :deep(.matrix-page-desc) {
  color: #9ca3af !important;
  font-weight: 500 !important;
  opacity: 1 !important;
}
.admin-layout :deep(.admin-panel),
.admin-layout :deep(.admin-panel *) {
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
}
/* /NEEPU_ADMIN_PANEL_HD */

.admin-layout {
  width: 100%;
  min-height: calc(100vh - var(--nav-height, 72px));
  margin: 0;
}

.admin-sidebar {
  width: var(--sidebar-width, 248px);
  flex-shrink: 0;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.admin-main {
  flex: 1;
  min-width: 0;
  padding: clamp(16px, 2vw, 24px);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.admin-content-wrap {
  flex: 1;
  min-width: 0;
  width: 100%;
  max-width: none;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  position: static;
  height: auto;
  display: block;
}
</style>
