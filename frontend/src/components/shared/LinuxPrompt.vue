<template>
  <p class="linux-prompt" :class="extraClass">
    <span class="lp-user">{{ user }}</span><span class="lp-host">@{{ host }}</span><span class="lp-path">:{{ path }}$</span><template v-if="cmd"> <span class="lp-cmd">{{ cmd }}</span></template><span v-if="cursor" class="lp-cursor" aria-hidden="true" />
  </p>
</template>

<script>
export default {
  name: 'LinuxPrompt',
  props: {
    user: { type: String, default: 'ctf' },
    host: { type: String, default: 'neepu' },
    path: { type: String, default: '~' },
    cmd: { type: String, default: '' },
    cursor: { type: Boolean, default: false },
    extraClass: { type: String, default: '' },
  },
}
</script>
