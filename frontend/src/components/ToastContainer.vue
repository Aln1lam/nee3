<template>
  <div class="toast-container" aria-live="polite">
    <transition-group name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="toast-item"
        :class="`toast-${t.level}`"
        @click="!t.accept && !t.reject && dismiss(t.id)"
      >
        <span class="toast-icon">{{ icons[t.level] }}</span>
        <span class="toast-msg">{{ t.message }}</span>
        <div v-if="t.accept || t.reject" class="toast-actions" @click.stop>
          <button v-if="t.reject" class="toast-action reject" @click="onReject(t)">{{ t.rejectLabel }}</button>
          <button v-if="t.accept" class="toast-action accept" @click="onAccept(t)">{{ t.acceptLabel }}</button>
        </div>
        <button v-else class="toast-close" aria-label="关闭" @click.stop="dismiss(t.id)">×</button>
      </div>
    </transition-group>
  </div>
</template>

<script>
import { useToast } from '../composables/toast'

export default {
  name: 'ToastContainer',
  setup() {
    const { toasts, dismiss, onAccept, onReject } = useToast()
    const icons = { info: 'ℹ', success: '✓', warning: '⚠', error: '✗' }
    return { toasts, dismiss, onAccept, onReject, icons }
  },
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: calc(var(--nav-height, 64px) + 12px);
  right: 16px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 360px;
  pointer-events: none;
}
.toast-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  background: var(--card-bg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-lg);
  backdrop-filter: none;
  font-size: var(--text-sm);
  cursor: pointer;
  pointer-events: auto;
}
.toast-info { border-left: 3px solid var(--primary); }
.toast-success { border-left: 3px solid var(--success, #51cf66); }
.toast-warning { border-left: 3px solid #fab005; }
.toast-error { border-left: 3px solid var(--accent-red, #f83030); }
.toast-icon { flex-shrink: 0; font-size: var(--text-sm); }
.toast-msg { flex: 1; line-height: 1.4; }
.toast-actions { display: flex; gap: 6px; flex-shrink: 0; }
.toast-action {
  padding: 2px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: transparent;
  font-size: var(--text-xs);
  cursor: pointer;
  color: var(--text);
}
.toast-action.accept { background: var(--primary); color: #fff; border-color: var(--primary); }
.toast-action.reject:hover, .toast-action.accept:hover { opacity: 0.9; }
.toast-close {
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: var(--text-base);
  padding: 0 2px;
  line-height: 1;
}
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(20px); }
</style>
