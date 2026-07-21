<template>
  <n-button
    :type="naiveType"
    :size="size"
    :loading="loading"
    :disabled="disabled"
    :quaternary="variant === 'ghost'"
    :class="['ui-btn', `ui-btn--${variant}`]"
    v-bind="$attrs"
    @click="$emit('click', $event)"
  >
    <slot />
  </n-button>
</template>

<script>
import { computed } from 'vue'
import { NButton } from 'naive-ui'

export default {
  name: 'UiButton',
  components: { NButton },
  inheritAttrs: false,
  props: {
    variant: { type: String, default: 'primary' }, // primary | secondary | danger | ghost
    size: { type: String, default: 'medium' },
    loading: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
  },
  emits: ['click'],
  setup(props) {
    const naiveType = computed(() => {
      if (props.variant === 'danger') return 'error'
      if (props.variant === 'secondary' || props.variant === 'ghost') return 'default'
      return 'primary'
    })
    return { naiveType }
  },
}
</script>

<style scoped>
.ui-btn--secondary {
  background: var(--hover) !important;
}
.ui-btn--danger {
  --n-color: var(--error, #f83030) !important;
}
</style>
