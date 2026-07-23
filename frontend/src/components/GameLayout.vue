<template>
  <MatrixShell
    class="game-layout"
    :class="[shellClass, { 'game-layout--no-sidebar': !showSidebar, 'game-layout--overview': mode === 'overview' }]"
    sidebar-width="248px"
    :show-sidebar="showSidebar"
    :bleed="true"
    :collapsible="collapsible && showSidebar"
    :storage-key="storageKey"
    content-class="game-layout-page"
    page-prompt=""
    page-title=""
    page-desc=""
  >
    <template v-if="showSidebar && $slots.sidebar" #sidebar>
      <slot name="sidebar" />
    </template>
    <template v-if="showSidebar" #sidebar-footer>
      <slot name="sidebar-footer">
        <router-link to="/contests" class="sidebar-link game-layout-back">
          <span class="link-code">CTF</span>
          <span>返回赛事</span>
        </router-link>
      </slot>
    </template>

    <div class="game-layout-main" :class="mainClass">
      <slot />
    </div>
  </MatrixShell>
</template>

<script>
import { computed } from 'vue'
import { MatrixShell } from '@/components/shared'

export default {
  name: 'GameLayout',
  components: { MatrixShell },
  props: {
    mode: {
      type: String,
      default: 'overview', // overview | scroll
    },
    showSidebar: { type: Boolean, default: true },
    collapsible: { type: Boolean, default: true },
    storageKey: { type: String, default: 'neepu_game_layout_sidebar' },
    shellClass: { type: [String, Object, Array], default: '' },
  },
  setup(props) {
    const mainClass = computed(() => ({
      'is-overview': props.mode === 'overview',
      'is-scroll': props.mode === 'scroll',
      'game-challenges-content': props.mode === 'scroll',
    }))
    return { mainClass }
  },
}
</script>

<style scoped>
.game-layout {
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  box-sizing: border-box;
}
.game-layout--no-sidebar :deep(.matrix-main) {
  width: 100%;
  max-width: 100%;
}
.game-layout :deep(.matrix-sidebar),
.game-layout :deep(.sidebar-rail) {
  height: 100%;
  max-height: 100%;
  overflow: hidden;
}
.game-layout :deep(.matrix-main) {
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0 !important;
}
.game-layout :deep(.matrix-page-head) {
  display: none;
}
.game-layout :deep(.matrix-page),
.game-layout :deep(.game-layout-page) {
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  box-sizing: border-box;
}
.game-layout-main {
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  box-sizing: border-box;
}
.game-layout-main.is-overview {
  overflow: hidden;
}
.game-layout-main.is-scroll,
.game-layout-main.game-challenges-content {
  overflow-x: hidden;
  overflow-y: auto;
}

.game-layout--overview :deep(.matrix-sidebar.sidebar-rail) {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.game-layout--overview :deep(.sidebar-rail-footer) {
  margin-top: auto;
  flex-shrink: 0;
  padding: 12px 14px 16px;
}
.game-layout--overview :deep(.game-layout-back) {
  width: 100%;
}

/* 概览侧栏赛事 List：Glass Glow 选中态（无左侧亮条） */
.game-layout--overview :deep(.contest-nav-item.sidebar-item),
.game-layout--overview :deep(.contest-nav-item) {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  grid-template-columns: unset !important;
  width: 100% !important;
  border-radius: 8px !important;
  border: 1px solid transparent !important;
  padding: 10px 14px !important;
  background: transparent !important;
  box-shadow: none !important;
  transition: all 0.2s ease;
}
.game-layout--overview :deep(.contest-nav-item:hover) {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
}
.game-layout--overview :deep(.contest-nav-item.active) {
  background: rgba(16, 185, 129, 0.08) !important;
  border: 1px solid rgba(16, 185, 129, 0.25) !important;
  box-shadow: inset 0 0 12px rgba(16, 185, 129, 0.05) !important;
  color: #fff !important;
}
.game-layout--overview :deep(.contest-nav-item .item-title) {
  width: 100%;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: #e5e7eb;
  white-space: normal !important;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.game-layout--overview :deep(.contest-nav-item.active .item-title) {
  color: #fff !important;
  font-weight: 600 !important;
}
.game-layout--overview :deep(.contest-status-chip) {
  border-radius: 4px !important;
  font-size: 11px !important;
}
</style>
