<template>
  <n-tag :type="naiveType" :size="size" :round="round" class="ui-tag">
    <slot />
  </n-tag>
</template>

<script>
import { computed } from 'vue'
import { NTag } from 'naive-ui'

const TYPE_MAP = {
  default: 'default',
  success: 'success',
  warning: 'warning',
  error: 'error',
  info: 'info',
}

export default {
  name: 'UiTag',
  components: { NTag },
  props: {
    variant: { type: String, default: 'default' },
    size: { type: String, default: 'small' },
    round: { type: Boolean, default: true },
  },
  setup(props) {
    const naiveType = computed(() => TYPE_MAP[props.variant] || 'default')
    return { naiveType }
  },
}
</script>
