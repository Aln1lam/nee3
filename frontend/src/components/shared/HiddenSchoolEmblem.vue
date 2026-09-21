<template>
  <button
    type="button"
    class="hidden-emblem"
    aria-label="东北电力大学"
    title="东北电力大学"
    @click="onClick"
  >
    <img src="/assets/neepu-emblem.jpg" alt="" />
  </button>
</template>

<script>
export default {
  name: 'HiddenSchoolEmblem',
  setup() {
    function onClick() {
      window.open('https://www.neepu.edu.cn/', '_blank', 'noopener')
    }
    return { onClick }
  },
}
</script>

<style scoped>
.hidden-emblem {
  position: fixed;
  right: 14px;
  bottom: 14px;
  z-index: 1200;
  width: 44px;
  height: 44px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(8, 12, 16, 0.55);
  box-shadow: 0 0 0 1px rgba(94, 217, 168, 0.2);
  cursor: pointer;
  opacity: 0.35;
  transition: opacity 0.25s ease, transform 0.25s ease;
  animation: emblem-spin 24s linear infinite;
}
.hidden-emblem:hover {
  opacity: 0.95;
  transform: scale(1.08);
  animation-play-state: paused;
}
.hidden-emblem img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  pointer-events: none;
}
@keyframes emblem-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.hidden-emblem:hover {
  animation: none;
  transform: scale(1.08);
}
</style>
