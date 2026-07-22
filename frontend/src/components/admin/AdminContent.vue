<template>
  <div class="admin-content">
    <PlatformDashboard v-if="view === 'dashboard'" />
    <UserManagement v-else-if="view === 'users'" />
    <ContentManagement v-else-if="view === 'content'" />
    <AnnouncementManagement v-else-if="view === 'announcement'" />
    <CtfManagement v-else-if="view === 'ctf'" />
    <SystemSettings v-else-if="view === 'settings'" />
    <LogAudit v-else-if="view === 'logs'" />
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PlatformDashboard from './PlatformDashboard.vue'
import UserManagement from './UserManagement.vue'
import ContentManagement from './ContentManagement.vue'
import SystemSettings from './SystemSettings.vue'
import LogAudit from './LogAudit.vue'
import CtfManagement from './CtfManagement.vue'
import AnnouncementManagement from './AnnouncementManagement.vue'

export default {
  name: 'AdminContent',
  components: {
    PlatformDashboard,
    UserManagement,
    ContentManagement,
    SystemSettings,
    LogAudit,
    CtfManagement,
    AnnouncementManagement,
  },
  setup() {
    const route = useRoute()
    const view = computed(() => route.meta?.adminView || 'dashboard')
    return { view }
  },
}
</script>

<style scoped>
.admin-content {
  width: 100%;
  max-width: none;
}
</style>
