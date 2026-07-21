<template>
  <SidebarLayout
    title="账号设置"
    subtitle="ACCOUNT · SETTINGS"
    linux-path="~/account"
    linux-cmd="settings --list"
    :items="menuItems"
    :collapsible="false"
  >
    <router-view />
  </SidebarLayout>
</template>

<script>
import { SidebarLayout } from '@/components/shared'

export default {
  name: 'AccountSettings',
  components: { SidebarLayout },
  setup() {
    const menuItems = [
      { label: '基本信息', path: '/account/settings/info', code: 'USR' },
      { label: '修改密码', path: '/account/settings/password', code: 'PWD' },
      { label: '第三方绑定', path: '/account/settings/oauth', code: 'OAU' },
      { label: '注销账号', path: '/account/settings/mov-esp-ebp-pop-ebp', code: 'DEL' },
    ]
    return { menuItems }
  },
}
</script>
