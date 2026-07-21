<template>
  <UiTimer
    :start-time="startTime"
    :end-time="endTime"
    :target-time="targetTime"
    :seconds="seconds"
    :label="label"
    @finish="$emit('finish', $event)"
  />
</template>

<script>
import { UiTimer } from '@/components/ui'

export default {
  name: 'GameTimer',
  components: { UiTimer },
  props: {
    startTime: { type: String, default: null },
    endTime: { type: String, default: null },
    targetTime: { type: String, default: null },
    seconds: { type: Number, default: null },
    label: { type: String, default: '' },
    status: { type: String, default: '' },
  },
  emits: ['finish'],
}
</script>
