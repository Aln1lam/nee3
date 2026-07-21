<template>
  <div class="ui-loading-tips">
    <n-spin v-if="showSpin" :size="spinSize" />
    <p class="ui-loading-tips__text">{{ currentTip }}</p>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { NSpin } from 'naive-ui'
import { fetchPlatformInfo } from '@/services/platform'

const DEFAULT_TIPS = [
  '正在巡检 SCADA 节点...',
  '正在同步电网拓扑...',
  '正在解析 Modbus 报文...',
  '正在校验继电保护定值...',
]

export default {
  name: 'UiLoadingTips',
  components: { NSpin },
  props: {
    showSpin: { type: Boolean, default: true },
    spinSize: { type: String, default: 'medium' },
    tips: { type: Array, default: null },
  },
  setup(props) {
    const pool = ref([...(props.tips || DEFAULT_TIPS)])
    const currentTip = ref(pool.value[0])

    onMounted(async () => {
      if (!props.tips) {
        const info = await fetchPlatformInfo()
        if (info.loading_tips?.length) pool.value = [...info.loading_tips]
      }
      currentTip.value = pool.value[Math.floor(Math.random() * pool.value.length)]
    })

    return { currentTip }
  },
}
</script>

<style scoped>
.ui-loading-tips {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  color: var(--muted);
}
.ui-loading-tips__text {
  margin: 0;
  font-size: 14px;
  font-family: var(--font-hacker);
}
</style>
