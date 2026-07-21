<template>
  <div class="metric-card">
    <div class="icon">{{ icon }}</div>
    <div class="content">
      <div class="title">{{ title }}</div>
      <div class="value">{{ value }}</div>
      <div v-if="subtext" class="subtext">{{ subtext }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MetricCard',
  props: {
    title: String,
    value: [String, Number],
    icon: String,
    subtext: String
  }
}
</script>

<style scoped>
.metric-card {
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 10px;
  box-shadow: var(--card-shadow);
  border-left: 4px solid var(--card-accent);
  display: flex;
  align-items: flex-start;
  gap: 15px;
  transition: all .2s ease;
}

.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(10,20,40,0.12);
}

.icon {
  font-size: 32px;
  opacity: 0.8;
}

.content {
  flex: 1;
}

.title {
  font-size: 13px;
  color: #666;
  margin-bottom: 5px;
}

.value {
  font-size: 28px;
  font-weight: 700;
  color: var(--card-accent);
}

.subtext {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}
</style>
