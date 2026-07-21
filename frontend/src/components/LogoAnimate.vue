<template>
  <div class="logo-animate" :style="{ width: size + 'px', height: size + 'px' }">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="logo-svg">
      <rect x="2" y="2" width="20" height="20" rx="4" fill="none" stroke="currentColor" stroke-width="1.5" class="logo-frame" />
      <path d="M13 4 L9 13 H12 L11 20 L17 10 H14 L15 4 Z" fill="currentColor" class="logo-bolt" />
    </svg>
  </div>
</template>

<script>
export default {
  name: 'LogoAnimate',
  props: {
    size: { type: Number, default: 24 },
  },
}
</script>

<style scoped>
.logo-animate {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}
.logo-svg { width: 100%; height: 100%; }
.logo-frame {
  stroke-dasharray: 80;
  stroke-dashoffset: 80;
  animation: draw-logo 2.5s ease-in-out infinite alternate;
}
.logo-bolt {
  animation: pulse-bolt 2s ease-in-out infinite;
  transform-origin: center;
}
@keyframes draw-logo {
  to { stroke-dashoffset: 0; }
}
@keyframes pulse-bolt {
  0%, 100% { opacity: 0.85; filter: drop-shadow(0 0 2px rgba(0, 180, 255, 0.3)); }
  50% { opacity: 1; filter: drop-shadow(0 0 6px rgba(0, 180, 255, 0.6)); }
}
</style>
