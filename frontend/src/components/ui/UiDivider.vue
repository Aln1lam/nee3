<template>
  <n-divider :vertical="vertical" :title-placement="titlePlacement">
    <slot />
  </n-divider>
</template>

<script>
import { NDivider } from 'naive-ui'

export default {
  name: 'UiDivider',
  components: { NDivider },
  props: {
    vertical: { type: Boolean, default: false },
    titlePlacement: { type: String, default: 'center' },
  },
}
</script>
