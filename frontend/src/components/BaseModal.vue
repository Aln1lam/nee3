<template>
  <transition name="modal-fade">
    <div v-if="modelValue" class="bm-overlay" @click.self="onMaskClick">
    <div class="bm-wrapper" :style="{ width: width || 'var(--modal-width)' }">
        <header v-if="$slots.header" class="bm-header">
          <slot name="header"></slot>
          <button v-if="showClose" class="bm-close" @click="close">×</button>
        </header>
        <section class="bm-body">
          <slot />
        </section>
        <footer v-if="$slots.footer" class="bm-footer">
          <slot name="footer"></slot>
        </footer>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'BaseModal',
  props: {
    modelValue: { type: Boolean, required: true },
    width: { type: String, default: '720px' },
    maskClosable: { type: Boolean, default: true },
    showClose: { type: Boolean, default: true }
  },
  emits: ['update:modelValue','close'],
  methods: {
    close() {
      this.$emit('update:modelValue', false)
      this.$emit('close')
    },
    onMaskClick() {
      if (this.maskClosable) this.close()
    }
  }
}
</script>

<style scoped>
.bm-overlay {
  position: fixed; inset: 0; display:flex; align-items:center; justify-content:center;
  background: var(--overlay, rgba(10,12,16,0.4)); z-index: 1200;
}
.bm-wrapper {
  background: var(--card-bg); color: var(--text); border-radius: var(--modal-border-radius, 10px); box-shadow: var(--modal-box-shadow, 0 10px 30px rgba(10,20,40,0.2));
  max-height: var(--modal-max-height, 90vh); overflow:auto; padding: var(--modal-padding, 18px);
  transform-origin: center center;
}
.bm-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px }
.bm-close { border:0; background:transparent; font-size:20px; cursor:pointer }
.bm-body { padding:8px 0 }
.bm-footer { margin-top:12px; text-align:right }

/* transition */
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity .22s ease, transform .22s ease }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; transform: translateY(-8px) scale(0.99) }
.modal-fade-enter-to, .modal-fade-leave-from { opacity: 1; transform: translateY(0) scale(1) }
</style>
