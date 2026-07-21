<template>
  <div class="myprofile-wrap">
    <n-card class="profile-header-card">
      <div class="profile-header">
        <div class="profile-avatar">
          <img :src="getAvatarUrl(user?.avatar)" :alt="user?.nickname || '用户'" />
        </div>
        <div class="profile-info">
          <h1 class="profile-nickname">{{ user?.nickname || '访客' }}</h1>
          <p class="profile-email">{{ user?.email || '未登录' }}</p>
          <p class="profile-signature">{{ user?.signature || '这个人很懒，没有个人签名' }}</p>
          <div class="profile-stats">
            <div class="stat-item">
              <div class="stat-label">参赛次数</div>
              <div class="stat-value">{{ participationCount }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">解题数</div>
              <div class="stat-value">{{ submissionCount }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">所在队伍</div>
              <div class="stat-value">{{ teamCount }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="profile-actions">
        <n-button type="primary" @click="goToProfileEdit">编辑个人信息</n-button>
        <n-button @click="goBack">返回首页</n-button>
      </div>
    </n-card>

    <div class="profile-content-grid">
      <n-card class="profile-section">
        <template #header>
          <div class="section-title">最近参赛</div>
        </template>
        <div v-if="recentParticipation.length === 0" class="empty-state">
          <p>暂无参赛记录</p>
        </div>
        <ul v-else class="participation-list">
          <li v-for="p in recentParticipation" :key="p.id" class="participation-item">
            <div class="participation-info">
              <div class="participation-title">{{ p.game_title }}</div>
              <div class="participation-time">{{ formatDate(p.created_at) }}</div>
            </div>
            <div v-if="p.rank" class="participation-rank">{{ p.rank }}名</div>
          </li>
        </ul>
      </n-card>

      <n-card class="profile-section">
        <template #header>
          <div class="section-title">所在队伍</div>
        </template>
        <div v-if="userTeams.length === 0" class="empty-state">
          <p>暂未加入任何队伍</p>
        </div>
        <ul v-else class="teams-list">
          <li v-for="t in userTeams" :key="t.id" class="team-item">
            <div class="team-name">{{ t.name }}</div>
            <div class="team-desc">{{ t.description || '无队伍描述' }}</div>
          </li>
        </ul>
      </n-card>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, inject } from 'vue'
import { fetchSession, getUser } from '@/services/auth'
import { useRouter } from 'vue-router'
import { NCard, NButton } from 'naive-ui'
import { resolveUploadUrl } from '../utils/uploadUrl'

export default {
  name: 'MyProfile',
  components: { NCard, NButton },
  setup() {
    const router = useRouter()
    const axios = inject('axios')
    const user = ref(null)
    const participationCount = ref(0)
    const submissionCount = ref(0)
    const teamCount = ref(0)
    const recentParticipation = ref([])
    const userTeams = ref([])

    onMounted(() => {
      loadUserData()
      // Listen for user profile updates from ProfileEdit
      window.addEventListener('neepu_user_refreshed', loadUserData)
    })
    
    onUnmounted(() => {
      window.removeEventListener('neepu_user_refreshed', loadUserData)
    })

    async function loadUserData() {
      try {
        user.value = (await fetchSession({ force: true })) || getUser()
      } catch (e) {
        user.value = null
      }
    }

    function formatDate(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
    }

    function getAvatarUrl(avatarPath) {
      if (!avatarPath) return '/assets/avatar-placeholder.png'
      return resolveUploadUrl(avatarPath) || '/assets/avatar-placeholder.png'
    }

    function goToProfileEdit() {
      router.push('/profile')
    }

    function goBack() {
      router.push('/home')
    }

    return {
      user,
      participationCount,
      submissionCount,
      teamCount,
      recentParticipation,
      userTeams,
      formatDate,
      getAvatarUrl,
      goToProfileEdit,
      goBack
    }
  }
}
</script>

<style scoped>
.profile-header-card {
  border-radius: 12px;
  margin-bottom: 24px;
}

.profile-header {
  display: flex;
  align-items: flex-start;
  padding: var(--fib-34) 0;
}

.profile-avatar {
  flex-shrink: 0;
  width: 140px;
  height: 140px;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid rgba(0, 0, 0, 0.08);
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-info {
  flex: 1;
}

.profile-nickname {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.profile-email {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #666;
}

.profile-signature {
  margin: 12px 0 20px 0;
  font-size: 14px;
  color: #888;
  font-style: italic;
  max-width: 500px;
}

.profile-stats {
  display: flex;
  margin-bottom: var(--fib-21);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary, #00c48c);
}

.profile-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.profile-actions :deep(.n-button) {
  min-width: 120px;
}

.profile-section {
  border-radius: 12px;
}

.section-title {
  font-weight: 700;
  font-size: 16px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #999;
}

.participation-list,
.teams-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.participation-item,
.team-item {
  padding: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.participation-item:last-child,
.team-item:last-child {
  border-bottom: none;
}

.participation-info {
  flex: 1;
}

.participation-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  margin-bottom: 4px;
}

.participation-time {
  font-size: 12px;
  color: #999;
}

.participation-rank {
  font-weight: 700;
  font-size: 16px;
  color: var(--primary, #00c48c);
  min-width: 60px;
  text-align: right;
}

.team-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  margin-bottom: 4px;
}

.team-desc {
  font-size: 12px;
  color: #999;
}

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: var(--fib-21);
  }

  .profile-avatar {
    width: 100px;
    height: 100px;
  }

  .profile-nickname {
    font-size: 24px;
  }

  .profile-stats {
    justify-content: center;
  }

}
</style>
