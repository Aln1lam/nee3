<template>
  <div class="logo-animate" :style="{ width: size + 'px', height: size + 'px' }" aria-hidden="true">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="logo-svg" fill="none">
      <rect x="3" y="4" width="18" height="16" rx="2.2" stroke="currentColor" stroke-width="1.6" />
      <path d="M7.5 9.5 L10.5 12 L7.5 14.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M12.5 14.5 H16.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
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
  color: #5ED9A8;
}
.logo-svg {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
