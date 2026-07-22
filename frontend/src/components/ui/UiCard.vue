<template>
  <div :class="['ui-card', { 'ui-card--hover': hover }]">
    <header v-if="$slots.header || title" class="ui-card__header">
      <slot name="header">{{ title }}</slot>
    </header>
    <div class="ui-card__body">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="ui-card__footer">
      <slot name="footer" />
    </footer>
  </div>
</template>

<script>
export default {
  name: 'UiCard',
  props: {
    title: { type: String, default: '' },
    hover: { type: Boolean, default: false },
  },
}
</script>

<style scoped>
.ui-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--card-radius, 10px);
  backdrop-filter: none;
  box-shadow: var(--card-shadow, var(--shadow));
  overflow: hidden;
}
.ui-card--hover {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.ui-card--hover:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
.ui-card__header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: var(--text);
}
.ui-card__body { padding: 18px; }
.ui-card__footer {
  padding: 12px 18px;
  border-top: 1px solid var(--border);
}
</style>
