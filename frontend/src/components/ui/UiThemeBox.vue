<template>
  <n-popover trigger="click" placement="bottom-end">
    <template #trigger>
      <button class="theme-btn" type="button" :title="label" aria-label="切换主题">
        <svg v-if="isDark" class="theme-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path d="M21 14.5A8.5 8.5 0 0 1 9.5 3 7 7 0 1 0 21 14.5z" stroke-linejoin="round"/>
        </svg>
        <svg v-else class="theme-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke-linecap="round"/>
        </svg>
      </button>
    </template>
    <div class="theme-panel">
      <button type="button" class="theme-option" @click="setTheme('light')">浅色</button>
      <button type="button" class="theme-option" @click="setTheme('dark')">深色</button>
      <label class="follow-system">
        <input type="checkbox" :checked="followSystem" @change="onFollowChange" />
        跟随系统
      </label>
    </div>
  </n-popover>
</template>

<script>
import { onMounted } from 'vue'
import { NPopover } from 'naive-ui'
import { useTheme } from '@/composables/useTheme'

export default {
  name: 'UiThemeBox',
  components: { NPopover },
  setup() {
    const { isDark, label, followSystem, setTheme, setFollowSystem, initTheme } = useTheme()
    function onFollowChange(e) {
      setFollowSystem(e.target.checked)
    }
    onMounted(() => initTheme())
    return { isDark, label, followSystem, setTheme, onFollowChange }
  },
}
</script>

<style scoped>
.theme-btn {
  background: transparent;
  border: 0;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  min-height: 0;
  padding: 0;
  cursor: pointer;
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.theme-btn:hover {
  color: var(--primary);
  background: rgba(var(--primary-rgb), 0.1);
}
.theme-ico { width: 18px; height: 18px; display: block; }
.theme-panel { display: flex; flex-direction: column; gap: 6px; min-width: 120px; }
.theme-option {
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
  color: var(--text);
  font-family: var(--font-ui);
}
.theme-option:hover { background: var(--hover); }
.follow-system {
  font-size: var(--text-xs);
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  cursor: pointer;
  font-family: var(--font-ui);
}
</style>
