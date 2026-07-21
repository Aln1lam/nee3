<template>
  <div
    class="sidebar-layout layout-with-sidebar lab-deck"
    :class="{ 'sidebar-collapsed': collapsible && collapsed }"
    :style="{ '--sidebar-width': '248px', maxWidth: layoutMaxWidth }"
  >
    <button
      v-if="collapsible"
      class="sidebar-toggle"
      type="button"
      :aria-expanded="!mobileCollapsed"
      @click="mobileCollapsed = !mobileCollapsed"
    >
      {{ mobileCollapsed ? '展开菜单' : '收起菜单' }}
    </button>

    <aside
      class="sidebar-layout__side sidebar-rail"
      :class="{ 'mobile-hidden': mobileCollapsed && collapsible }"
    >
      <div class="sidebar-rail-head sidebar-head">
        <div class="sidebar-head-row">
          <h2 v-if="title" class="sidebar-title sidebar-layout__title sidebar-rail-title">{{ title }}</h2>
        </div>
        <p v-if="subtitle" class="sidebar-layout__subtitle sidebar-desc sidebar-rail-sub">{{ subtitle }}</p>
        <p v-else-if="prompt" class="sidebar-layout__prompt sidebar-desc sidebar-rail-sub">{{ prompt }}</p>
      </div>

      <div class="sidebar-rail-nav">
        <slot name="sidebar">
          <nav v-if="items.length" class="sidebar-layout__nav">
            <router-link
              v-for="item in items"
              :key="item.path"
              :to="item.path"
              class="sidebar-layout__link sidebar-item"
              :class="{ active: isActive(item.path) }"
            >
              <span v-if="item.code" class="link-code item-code">{{ item.code }}</span>
              <span class="link-label item-title">{{ item.label }}</span>
            </router-link>
          </nav>
        </slot>
      </div>

      <div v-if="$slots['sidebar-footer']" class="sidebar-links sidebar-layout__footer sidebar-rail-footer">
        <slot name="sidebar-footer" />
      </div>
    </aside>

    <button
      v-if="collapsible"
      type="button"
      class="sidebar-collapse-trigger"
      :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
      @click="toggleSidebar"
    >
      <span class="chevron" :class="{ 'is-collapsed': collapsed }">‹</span>
    </button>

    <main class="sidebar-layout__main sidebar-main">
      <slot />
    </main>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCollapsibleSidebar } from '../../composables/useCollapsibleSidebar'

export default {
  name: 'SidebarLayout',
  components: {},
  props: {
    title: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    prompt: { type: String, default: '' },
    linuxPath: { type: String, default: '' },
    linuxCmd: { type: String, default: '' },
    items: { type: Array, default: () => [] },
    collapsible: { type: Boolean, default: true },
    maxWidth: { type: String, default: 'none' },
    storageKey: { type: String, default: 'neepu_sidebar_collapsed' },
  },
  setup(props) {
    const route = useRoute()
    const mobileCollapsed = ref(false)
    const layoutMaxWidth = computed(() => props.maxWidth)
    const { collapsed, toggleSidebar } = useCollapsibleSidebar(props.storageKey)

    function isActive(path) {
      return route.path === path || route.path.startsWith(path + '/')
    }

    return {
      mobileCollapsed, collapsed, toggleSidebar, isActive, layoutMaxWidth,
    }
  },
}
</script>

<style scoped>
.sidebar-layout {
  max-width: v-bind(layoutMaxWidth);
}

.sidebar-toggle {
  display: none;
  margin: 12px 16px 0;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--card-bg);
  color: var(--text);
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: inherit;
}

.sidebar-layout__side {
  position: sticky;
  top: var(--nav-height, 56px);
  align-self: flex-start;
  max-height: calc(100vh - var(--nav-height, 56px));
  z-index: 10;
}

.sidebar-layout__nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-layout__footer {
  flex-shrink: 0;
}

.sidebar-layout__side :deep(.sidebar-layout__nav) {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-layout__side :deep(.sidebar-layout__link) {
  border-radius: var(--radius-lg);
  box-sizing: border-box;
  max-width: 100%;
}

.sidebar-layout__side :deep(.link-code) {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-accent, #D97706);
}

.sidebar-layout__side :deep(.sidebar-layout__link:hover) {
  background: var(--hover);
  border-color: var(--border);
  color: var(--text);
}

.sidebar-layout__side :deep(.sidebar-layout__link.active) {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}

.sidebar-layout__side :deep(.sidebar-layout__link.active .link-code) {
  color: var(--primary);
}

.sidebar-layout__link {
  border-radius: var(--radius-lg);
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.link-code {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-accent, #D97706);
}

.sidebar-layout__link:hover {
  background: var(--hover);
  border-color: var(--border);
  color: var(--text);
}

.sidebar-layout__link.active {
  background: rgba(var(--primary-rgb), 0.12);
  border-color: rgba(var(--primary-rgb), 0.35);
  color: var(--primary);
}

.sidebar-layout__link.active .link-code {
  color: var(--primary);
}

.sidebar-layout__main {
  padding: 24px 28px 32px;
}

@media (max-width: 768px) {
  .sidebar-toggle { display: inline-block; }

  .sidebar-layout__side.mobile-hidden {
    display: none;
  }

  .sidebar-layout__side {
    position: static;
    max-height: none;
  }

  .sidebar-layout__main {
    padding: 16px;
  }
}
</style>
