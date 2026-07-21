<template>
  <n-popover
    :trigger="trigger"
    :placement="placement"
    :width="width"
    :show-arrow="showArrow"
  >
    <template #trigger>
      <slot name="trigger" />
    </template>
    <slot />
  </n-popover>
</template>

<script>
import { NPopover } from 'naive-ui'

export default {
  name: 'UiPopover',
  components: { NPopover },
  props: {
    trigger: { type: String, default: 'click' },
    placement: { type: String, default: 'bottom' },
    width: { type: [Number, String], default: undefined },
    showArrow: { type: Boolean, default: true },
  },
}
</script>
