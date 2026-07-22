<template>
  <div
    class="matrix-shell layout-with-sidebar lab-deck"
    :class="{
      'sidebar-collapsed': collapsible && collapsed,
      'matrix-shell--no-sidebar': !showSidebar,
    }"
    :style="{ '--sidebar-width': sidebarWidth }"
  >
    <aside v-if="showSidebar" class="matrix-sidebar sidebar-rail">
      <slot name="sidebar">
        <div class="sidebar-head sidebar-rail-head">
          <div class="sidebar-head-row">
            <h2 v-if="title" class="sidebar-title sidebar-rail-title">{{ title }}</h2>
          </div>
          <p v-if="subtitle" class="sidebar-desc sidebar-rail-sub">{{ subtitle }}</p>
          <p v-else-if="prompt" class="sidebar-desc sidebar-rail-sub">{{ prompt }}</p>
        </div>
        <nav v-if="items.length" class="sidebar-rail-nav">
          <component
            :is="navTag(item)"
            v-for="item in items"
            :key="item.path || item.code + item.label"
            :to="item.path"
            :type="item.path ? undefined : 'button'"
            class="sidebar-item"
            :class="{ active: isActive(item) }"
            @click="onNavClick(item, $event)"
          >
            <span v-if="item.code" class="item-code">{{ item.code }}</span>
            <span class="item-title">{{ item.label }}</span>
            <span v-if="item.meta != null && item.meta !== ''" class="item-count">{{ item.meta }}</span>
          </component>
        </nav>
      </slot>
      <div v-if="$slots['sidebar-footer']" class="sidebar-links sidebar-rail-footer">
        <slot name="sidebar-footer" />
      </div>
    </aside>

    <button
      v-if="showSidebar && collapsible"
      type="button"
      class="sidebar-collapse-trigger"
      :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
      @click="toggleSidebar"
    >
      <span class="chevron" :class="{ 'is-collapsed': collapsed }">‹</span>
    </button>

    <main class="matrix-main sidebar-main">
      <header v-if="pagePrompt || pageTitle" class="matrix-page-head">
        <p v-if="pagePrompt" class="matrix-page-prompt">{{ pagePrompt }}</p>
        <h2 v-if="pageTitle" class="matrix-page-title">{{ pageTitle }}</h2>
        <p v-if="pageDesc" class="matrix-page-desc">{{ pageDesc }}</p>
      </header>
      <div class="matrix-page" :class="contentClass">
        <slot />
      </div>
    </main>
  </div>
</template>

<script>
import { useRoute, useRouter } from 'vue-router'
import { useCollapsibleSidebar } from '../../composables/useCollapsibleSidebar'

export default {
  name: 'MatrixShell',
  props: {
    prompt: { type: String, default: '' },
    title: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    items: { type: Array, default: () => [] },
    pagePrompt: { type: String, default: '' },
    pageTitle: { type: String, default: '' },
    pageDesc: { type: String, default: '' },
    showSidebar: { type: Boolean, default: true },
    bleed: { type: Boolean, default: true },
    contentClass: { type: String, default: '' },
    collapsible: { type: Boolean, default: true },
    storageKey: { type: String, default: 'neepu_matrix_sidebar_collapsed' },
    sidebarWidth: { type: String, default: '248px' },
  },
  setup(props) {
    const route = useRoute()
    const router = useRouter()
    const { collapsed, toggleSidebar } = useCollapsibleSidebar(props.storageKey)

    function navTag(item) {
      return item.path ? 'router-link' : 'button'
    }

    function isActive(item) {
      if (item.active != null) return item.active
      if (!item.path) return false
      return route.path === item.path || route.path.startsWith(`${item.path}/`)
    }

    function onNavClick(item, event) {
      if (item.path) return
      event?.preventDefault()
      if (typeof item.onClick === 'function') item.onClick()
      else if (item.to) router.push(item.to)
    }

    return { navTag, isActive, onNavClick, collapsed, toggleSidebar }
  },
}
</script>
