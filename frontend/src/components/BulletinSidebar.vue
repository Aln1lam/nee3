<template>
  <aside class="bulletin-sidebar sidebar-rail">
    <div class="sidebar-head sidebar-rail-head">
      <div class="sidebar-head-row">
        <router-link to="/bulletin" class="sidebar-title sidebar-rail-title">公告中心</router-link>
      </div>
      <p class="sidebar-desc sidebar-rail-sub">BULLETIN · FEED</p>
    </div>

    <nav class="sidebar-rail-nav">
      <div class="sidebar-group">
        <router-link
          v-slot="{ href, navigate, isExactActive }"
          to="/bulletin"
          custom
        >
          <a
            :href="href"
            class="sidebar-item"
            :class="{ active: isExactActive || allActive }"
            @click="navigate"
          >
            <span class="item-code">ALL</span>
            <span class="item-title">全部公告</span>
            <span class="item-count">{{ items.length }}</span>
          </a>
        </router-link>

        <router-link
          v-for="item in items"
          :key="item.id"
          :to="`/bulletin/${item.id}`"
          class="sidebar-item"
          :class="{ active: isActive(item.id) }"
        >
          <span class="item-code">BUL</span>
          <span class="item-title">{{ item.title }}</span>
        </router-link>

        <router-link
          v-if="isAdmin"
          to="/bulletin/create"
          class="sidebar-item"
        >
          <span class="item-code">NEW</span>
          <span class="item-title">发布公告</span>
          <span class="item-count">→</span>
        </router-link>
      </div>
    </nav>

    <div class="sidebar-rail-footer sidebar-footer sidebar-footer-copy-wrap">
      <div class="sidebar-footer-copy">
        © 2022-2026
        <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">东北电力大学</a>
      </div>
    </div>
  </aside>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'BulletinSidebar',
  props: {
    items: { type: Array, default: () => [] },
    isAdmin: { type: Boolean, default: false },
  },
  setup() {
    const route = useRoute()
    const allActive = computed(() => route.name === 'Bulletin' || route.path === '/bulletin')
    function isActive(id) {
      return String(route.params.id) === String(id)
    }
    return { allActive, isActive }
  },
}
</script>
