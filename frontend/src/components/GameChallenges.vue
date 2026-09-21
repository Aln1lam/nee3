<template>
  <div class="game-challenges-root game-challenges-content">
    <ChallengeWorkspace :game-id="gameId" :mode="mode" />
  </div>
</template>

<script>
import { onBeforeMount } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import ChallengeWorkspace from './ChallengeWorkspace.vue'
import { fetchSession } from '@/services/auth'

export default {
  name: 'GameChallenges',
  components: { ChallengeWorkspace },
  props: {
    gameId: { type: [String, Number], required: true },
    mode: { type: String, default: 'competition' },
  },
  setup(props) {
    const router = useRouter()

    onBeforeMount(async () => {
      if (props.mode !== 'competition') return
      const user = await fetchSession()
      if (!user) {
        router.replace({ name: 'Auth', query: { redirect: `/games/${props.gameId}/challenges` } })
        return
      }
      if (user.is_admin) return
      try {
        const { data } = await axios.get(`/api/competitions/${props.gameId}/joined`)
        if (!data?.joined) {
          router.replace({ name: 'GameTeams', params: { id: props.gameId } })
        }
      } catch {
        router.replace({ name: 'GameDetail', params: { id: props.gameId } })
      }
    })

    return {}
  },
}
</script>

<style scoped>
.game-challenges-root {
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  box-sizing: border-box;
}
.game-challenges-root :deep(.challenge-workspace-matrix) {
  height: 100%;
  max-height: 100%;
  overflow: hidden;
}
.game-challenges-root :deep(.matrix-main) {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.game-challenges-root :deep(.challenge-workspace-page),
.game-challenges-root :deep(.workspace-dock) {
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}
.game-challenges-root :deep(.workspace-stage),
.game-challenges-root :deep(.stage-content) {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
}
</style>
