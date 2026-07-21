<template>
  <n-popover trigger="click" placement="bottom-end">
    <template #trigger>
      <button class="theme-btn" :title="label" aria-label="切换主题">
        {{ isDark ? '🌙' : '☀️' }}
      </button>
    </template>
    <div class="theme-panel">
      <button class="theme-option" @click="setTheme('light')">浅色</button>
      <button class="theme-option" @click="setTheme('dark')">深色</button>
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
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 14px;
}
.theme-panel { display: flex; flex-direction: column; gap: 6px; min-width: 120px; }
.theme-option {
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
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
}
</style>
