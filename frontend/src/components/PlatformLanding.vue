<template>
  <div class="r2s-landing">
    <h1 class="r2s-landing__title">
      <span>[ {{ platformName }} ]</span><span class="r2s-landing__cursor">_</span>
    </h1>
    <a class="r2s-landing__slogan" href="/magic/sakana" @click.prevent="goSlogan">
      {{ slogan }}
    </a>
    <footer class="r2s-landing__footer">
      <span>(C) {{ footerYears }} </span>
      <a :href="footerUrl" target="_blank" rel="noopener">{{ footerOrg }}</a>
      <template v-if="footerIcp">
        <span> | </span>
        <a :href="footerIcpUrl" target="_blank" rel="noopener">{{ footerIcp }}</a>
      </template>
    </footer>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'
import { fetchPlatformVersion } from '@/services/platform'

export default {
  name: 'PlatformLanding',
  setup() {
    const router = useRouter()
    const { platform, loadPlatform } = usePlatformStore()

    const platformName = computed(() => platform.value.name || 'NEEPU CTF')
    const slogan = computed(() =>
      platform.value.slogan || platform.value.subtitle || '为世界上所有美好而战'
    )
    const footerOrg = computed(() => platform.value.footer?.org_name || '东北电力大学')
    const footerUrl = computed(() => platform.value.footer?.org_url || 'https://www.neepu.edu.cn/')
    const footerYears = computed(() =>
      platform.value.footer?.copyright_years || `2022-${new Date().getFullYear()}`
    )
    const footerIcp = computed(() => platform.value.footer?.icp || '')
    const footerIcpUrl = computed(() => platform.value.footer?.icp_url || 'https://beian.miit.gov.cn/')

    function goSlogan() {
      router.push('/magic/sakana').catch(() => {
        window.open('https://ctf.xidian.edu.cn/magic/sakana', '_blank')
      })
    }

    onMounted(async () => {
      const info = await loadPlatform()
      await fetchPlatformVersion()
      if (info?.zen_game) {
        router.replace(`/games/${info.zen_game}`)
      }
    })

    return {
      platformName, slogan, footerOrg, footerUrl, footerYears, footerIcp, footerIcpUrl, goSlogan,
    }
  },
}
</script>
