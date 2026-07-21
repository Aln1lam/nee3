<template>
  <n-avatar
    :size="size"
    :src="src"
    :round="round"
    :color="fallbackColor"
    class="ui-avatar"
  >
    {{ fallbackLetter }}
  </n-avatar>
</template>

<script>
import { computed } from 'vue'
import { NAvatar } from 'naive-ui'

export default {
  name: 'UiAvatar',
  components: { NAvatar },
  props: {
    src: { type: String, default: '' },
    name: { type: String, default: '' },
    size: { type: [Number, String], default: 'medium' },
    round: { type: Boolean, default: true },
  },
  setup(props) {
    const fallbackLetter = computed(() => {
      const n = (props.name || '').trim()
      return n ? n.charAt(0).toUpperCase() : '?'
    })
    const fallbackColor = computed(() => (props.src ? undefined : 'var(--primary)'))
    return { fallbackLetter, fallbackColor }
  },
}
</script>
