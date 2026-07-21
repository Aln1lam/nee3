<template>
  <div class="ui-input" :class="{ 'ui-input--error': !!error }">
    <label v-if="label" :for="inputId" class="ui-input__label">{{ label }}</label>
    <n-input
      :id="inputId"
      :value="modelValue"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :status="error ? 'error' : undefined"
      @update:value="$emit('update:modelValue', $event)"
    />
    <p v-if="error" class="ui-input__error">{{ error }}</p>
    <p v-else-if="hint" class="ui-input__hint">{{ hint }}</p>
  </div>
</template>

<script>
import { computed } from 'vue'
import { NInput } from 'naive-ui'

let uid = 0

export default {
  name: 'UiInput',
  components: { NInput },
  props: {
    modelValue: { type: [String, Number], default: '' },
    label: { type: String, default: '' },
    type: { type: String, default: 'text' },
    placeholder: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    error: { type: String, default: '' },
    hint: { type: String, default: '' },
    id: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props) {
    const inputId = computed(() => props.id || `ui-input-${++uid}`)
    return { inputId }
  },
}
</script>

<style scoped>
.ui-input { display: flex; flex-direction: column; gap: 6px; }
.ui-input__label { font-size: var(--text-sm); font-weight: 500; color: var(--text); }
.ui-input__error { margin: 0; font-size: var(--text-xs); color: var(--error, #f83030); }
.ui-input__hint { margin: 0; font-size: var(--text-xs); color: var(--muted); }
</style>
