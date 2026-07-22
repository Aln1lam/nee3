<template>
  <div class="metric-card">
    <div class="icon-wrap" aria-hidden="true">
      <n-icon :size="20" :component="icon" />
    </div>
    <div class="content">
      <div class="title">{{ title }}</div>
      <div class="value">{{ value }}</div>
      <div v-if="subtext" class="subtext">{{ subtext }}</div>
    </div>
  </div>
</template>

<script>
import { NIcon } from 'naive-ui'

export default {
  name: 'MetricCard',
  components: { NIcon },
  props: {
    title: String,
    value: [String, Number],
    icon: { type: [Object, Function], required: true },
    subtext: String,
  },
}
</script>

<style scoped>
.metric-card {
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 10px;
  box-shadow: var(--card-shadow);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-left: 3px solid rgba(94, 217, 168, 0.55);
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 18px;
  transition: border-color 0.15s, background 0.15s;
}

.metric-card:hover {
  border-color: rgba(94, 217, 168, 0.22);
  background: rgba(20, 26, 33, 0.72);
}

.icon-wrap {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #5ED9A8;
  background: rgba(94, 217, 168, 0.1);
  border: 1px solid rgba(94, 217, 168, 0.22);
}

.content {
  flex: 1;
  min-width: 0;
}

.title {
  font-size: 13px;
  color: var(--muted, #9ca3af);
  margin-bottom: 5px;
  font-weight: 500;
}

.value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text, #e8eaed);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.subtext {
  font-size: 12px;
  color: var(--muted, #9ca3af);
  margin-top: 6px;
}
</style>
