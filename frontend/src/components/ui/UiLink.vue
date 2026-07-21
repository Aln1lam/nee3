<template>
  <component
    :is="tag"
    :href="external ? to : undefined"
    :to="!external ? to : undefined"
    :target="external ? '_blank' : undefined"
    :rel="external ? 'noopener noreferrer' : undefined"
    class="ui-link"
    :class="{ 'ui-link--external': external }"
  >
    <slot />
    <span v-if="external" class="ui-link__ext" aria-hidden="true">↗</span>
  </component>
</template>

<script>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

export default {
  name: 'UiLink',
  props: {
    to: { type: String, required: true },
    external: { type: Boolean, default: false },
  },
  setup(props) {
    const tag = computed(() => (props.external ? 'a' : RouterLink))
    return { tag }
  },
}
</script>

<style scoped>
.ui-link {
  color: var(--primary);
  text-decoration: none;
  transition: opacity 0.15s;
}
.ui-link:hover { text-decoration: underline; opacity: 0.9; }
.ui-link__ext { font-size: 0.85em; margin-left: 2px; }
</style>
