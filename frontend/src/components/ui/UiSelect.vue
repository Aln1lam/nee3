<template>
  <div class="ui-select">
    <label v-if="label" class="ui-select__label">{{ label }}</label>
    <n-select
      :value="modelValue"
      :options="options"
      :placeholder="placeholder"
      :disabled="disabled"
      :clearable="clearable"
      @update:value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<script>
import { NSelect } from 'naive-ui'

export default {
  name: 'UiSelect',
  components: { NSelect },
  props: {
    modelValue: { type: [String, Number, null], default: null },
    options: { type: Array, default: () => [] },
    label: { type: String, default: '' },
    placeholder: { type: String, default: '请选择' },
    disabled: { type: Boolean, default: false },
    clearable: { type: Boolean, default: true },
  },
  emits: ['update:modelValue'],
}
</script>

<style scoped>
.ui-select { display: flex; flex-direction: column; gap: 6px; }
.ui-select__label { font-size: var(--text-sm); font-weight: 500; }
</style>
