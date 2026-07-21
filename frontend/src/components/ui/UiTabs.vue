<template>
  <n-tabs
    :value="modelValue"
    :type="type"
    :size="size"
    @update:value="$emit('update:modelValue', $event)"
  >
    <n-tab-pane
      v-for="tab in tabs"
      :key="tab.key"
      :name="tab.key"
      :tab="tab.label"
      :disabled="tab.disabled"
    >
      <slot :name="tab.key" />
    </n-tab-pane>
  </n-tabs>
</template>

<script>
import { NTabs, NTabPane } from 'naive-ui'

export default {
  name: 'UiTabs',
  components: { NTabs, NTabPane },
  props: {
    modelValue: { type: [String, Number], required: true },
    tabs: { type: Array, default: () => [] },
    type: { type: String, default: 'line' },
    size: { type: String, default: 'medium' },
  },
  emits: ['update:modelValue'],
}
</script>
