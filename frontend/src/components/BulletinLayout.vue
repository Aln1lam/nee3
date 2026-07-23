<template>
  <div
    class="bulletin-layout layout-with-sidebar lab-deck"
    :class="{ 'sidebar-collapsed': collapsed }"
    style="--sidebar-width: 248px"
  >
    <BulletinSidebar :items="bulletins" />

    <button
      type="button"
      class="sidebar-collapse-trigger"
      :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
      @click="toggleSidebar"
    >
      <span class="chevron" :class="{ 'is-collapsed': collapsed }">‹</span>
    </button>

    <main class="bulletin-main sidebar-main">
      <router-view v-slot="{ Component }">
        <transition name="bulletin-pane" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script>
import { ref, provide, inject, onMounted } from 'vue'
import { unwrapList } from '../utils/unwrap'
import { useCollapsibleSidebar } from '@/composables/useCollapsibleSidebar'
import BulletinSidebar from './BulletinSidebar.vue'

export default {
  name: 'BulletinLayout',
  components: { BulletinSidebar },
  setup() {
    const axios = inject('axios')
    const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_bulletin_sidebar')
    const bulletins = ref([])
    const listLoading = ref(false)

    async function loadList() {
      listLoading.value = true
      try {
        const { data } = await axios.get('/api/platform/bulletins')
        bulletins.value = unwrapList(data)
      } catch {
        bulletins.value = []
      } finally {
        listLoading.value = false
      }
    }

    provide('bulletinList', bulletins)
    provide('bulletinListLoading', listLoading)
    provide('reloadBulletinList', loadList)

    onMounted(loadList)

    return { collapsed, toggleSidebar, bulletins }
  },
}
</script>

<style scoped>
.bulletin-layout {
  width: 100%;
  height: calc(100vh - var(--nav-height, 72px));
  max-height: calc(100vh - var(--nav-height, 72px));
  overflow: hidden;
  margin: 0;
}

.bulletin-main {
  overflow: auto;
  min-height: 0;
  width: 100%;
}

.bulletin-pane-enter-active,
.bulletin-pane-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.bulletin-pane-enter-from,
.bulletin-pane-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
