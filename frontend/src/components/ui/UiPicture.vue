<template>
  <img
    v-if="src"
    :src="src"
    :alt="alt"
    :class="['ui-picture', { 'ui-picture--loading': loading }]"
    @load="loading = false"
    @error="onError"
  />
  <div v-else class="ui-picture ui-picture--placeholder">{{ placeholder }}</div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'

export default {
  name: 'UiPicture',
  props: {
    hash: { type: String, default: '' },
    url: { type: String, default: '' },
    alt: { type: String, default: '' },
    placeholder: { type: String, default: '?' },
  },
  setup(props) {
    const src = ref('')
    const loading = ref(true)

    function resolve() {
      // 后端无 /api/media；主路径用 url（可为 /api/resources/:id/content 或 /api/uploads/serve/...）
      if (props.url) {
        src.value = props.url
        loading.value = true
        return
      }
      // hash 仅为西电式占位兼容：无对应 API 时显示 placeholder，避免 404 刷屏
      if (props.hash) {
        src.value = ''
        loading.value = false
        return
      }
      src.value = ''
      loading.value = false
    }

    function onError() {
      loading.value = false
      src.value = ''
    }

    watch(() => [props.hash, props.url], resolve, { immediate: true })
    onMounted(resolve)

    return { src, loading, onError }
  },
}
</script>

<style scoped>
.ui-picture {
  display: block;
  max-width: 100%;
  object-fit: cover;
  border-radius: var(--card-radius, 10px);
  background: var(--hover);
}
.ui-picture--placeholder {
  display: grid;
  place-items: center;
  min-height: 48px;
  color: var(--muted);
  font-size: 20px;
}
.ui-picture--loading { opacity: 0.6; }
</style>
