<template>
  <div class="captcha-wrap">
    <img
      v-if="imgUrl"
      :src="imgUrl"
      alt="验证码"
      class="captcha-img"
      title="点击刷新验证码"
      @click="refresh"
    />
    <button v-else class="captcha-placeholder" type="button" @click="refresh">加载验证码</button>
    <div class="captcha-input-col">
      <n-input
        v-model:value="answer"
        placeholder="验证码（至少4字符）"
        :maxlength="8"
        :disabled="disabled"
        :status="errorHint ? 'error' : undefined"
        @update:value="onAnswerInput"
        @keydown.enter="$emit('enter')"
      />
      <p v-if="errorHint" class="captcha-error">{{ errorHint }}</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { NInput } from 'naive-ui'

export default {
  name: 'Captcha',
  components: { NInput },
  props: {
    disabled: { type: Boolean, default: false },
    minLength: { type: Number, default: 4 },
  },
  emits: ['update:modelValue', 'update:captchaId', 'enter', 'valid'],
  setup(props, { emit, expose }) {
    const imgUrl = ref('')
    const answer = ref('')
    const captchaId = ref('')
    const touched = ref(false)

    const errorHint = computed(() => {
      if (!touched.value || !answer.value) return ''
      if (answer.value.length < props.minLength) return `验证码至少 ${props.minLength} 个字符`
      return ''
    })

    const isValid = computed(() =>
      !!captchaId.value && answer.value.length >= props.minLength,
    )

    async function refresh() {
      try {
        if (imgUrl.value) URL.revokeObjectURL(imgUrl.value)
        const res = await axios.get('/api/captcha/', { responseType: 'blob' })
        captchaId.value = res.headers['x-captcha-id'] || ''
        imgUrl.value = URL.createObjectURL(res.data)
        answer.value = ''
        touched.value = false
        emitValue()
      } catch {
        imgUrl.value = ''
        captchaId.value = ''
        emitValue()
      }
    }

    function emitValue() {
      emit('update:modelValue', answer.value)
      emit('update:captchaId', captchaId.value)
      emit('valid', isValid.value)
    }

    function onAnswerInput() {
      touched.value = true
      emitValue()
    }

    onMounted(refresh)
    onUnmounted(() => {
      if (imgUrl.value) URL.revokeObjectURL(imgUrl.value)
    })

    expose({ refresh, isValid })

    return { imgUrl, answer, errorHint, refresh, onAnswerInput }
  },
}
</script>

<style scoped>
.captcha-wrap {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.captcha-input-col { flex: 1; min-width: 0; }
.captcha-img {
  height: 40px;
  width: 120px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  cursor: pointer;
  object-fit: cover;
  flex-shrink: 0;
}
.captcha-placeholder {
  height: 40px;
  width: 120px;
  border-radius: var(--radius-md);
  border: 1px dashed var(--border);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 12px;
  flex-shrink: 0;
}
.captcha-error {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--error, #f83030);
}
</style>
