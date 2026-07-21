<template>
  <div class="chal-inner">
    <!-- 容器题目：使用 ContainerChallenge 组件 -->
    <ContainerChallenge 
      v-if="isContainerChallenge" 
      :challengeId="challenge.id"
      :challenge="challenge"
      :teamId="teamId"
    />
    
    <!-- 非容器题目：使用旧的 Flag 输入框 -->
    <template v-else>
      <div class="desc-box">
        <p v-if="challenge.content">{{ challenge.content }}</p>
        <p v-else class="empty-desc">// 暂无情报描述 //</p>
      </div>
      
      <div class="action-box">
        <n-input-group>
          <n-input 
            v-model:value="flag" 
            type="text" 
            placeholder="NEEPUCTF{...}" 
            :disabled="!joined || submitting"
            @keydown.enter="submit"
          >
            <template #prefix>
              <span class="chal-prefix">&gt;</span>
            </template>
          </n-input>
          <n-button 
            type="error" 
            secondary
            @click="submit" 
            :disabled="!joined"
            :loading="submitting"
          >
            {{ joined ? 'EXECUTE' : 'LOCKED' }}
          </n-button>
        </n-input-group>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, inject, computed } from 'vue'
import { NInput, NInputGroup, NButton, useMessage } from 'naive-ui'
import ContainerChallenge from './ContainerChallenge.vue'

export default {
  components: { NInput, NInputGroup, NButton, ContainerChallenge },
  props: ['challenge', 'joined'],
  setup(props) {
    const axios = inject('axios')
    const message = useMessage()
    
    const flag = ref('')
    const submitting = ref(false)
    const teamId = ref(null)
    
    // 判断是否是容器题目
    const isContainerChallenge = computed(() => {
      return props.challenge && (props.challenge.docker_image || props.challenge.is_docker)
    })
    
    // 从 localStorage 获取 teamId
    try {
      const userData = localStorage.getItem('neepu_user')
      if (userData) {
        const user = JSON.parse(userData)
        teamId.value = user.team_id || null
      }
    } catch (e) {
      console.warn('Failed to parse user data from localStorage')
    }
    
    async function submit() {
      if (submitting.value) return
      if (!props.joined) {
          message.warning('⚠️ ACCESS DENIED: 请先加入比赛')
          return
      }
      if (!flag.value.trim()) {
          message.warning('⚠️ 提交内容不能为空')
          return
      }
      
      submitting.value = true
      try {
        const { data } = await axios.post(`/api/challenges/${props.challenge.id}/submit`, {
          flag: flag.value,
          answer: flag.value,
        })
        const payload = data?.data || data
        if (payload?.is_correct || payload?.correct || data?.correct) {
            message.success('✅ CONNECTION ESTABLISHED: Flag 正确！')
            flag.value = ''
        } else {
            message.error('Flag 不正确')
        }
      } catch (e) { 
        message.error('提交失败: ' + (e.response?.data?.msg || e.message)) 
      } finally {
        submitting.value = false
      }
    }
    
    return { flag, submit, submitting, isContainerChallenge, teamId }
  }
}
</script>

<style scoped>
.chal-inner {
  font-family: var(--font-ui);
}

.desc-box { 
  background: var(--chal-desc-bg, #f9f9f9); 
  padding: var(--chal-desc-padding, 12px 16px); 
  border-radius: var(--chal-desc-radius, 4px); 
  margin-bottom: var(--chal-desc-margin-bottom, 20px); 
  font-size: var(--chal-desc-font-size, 0.85rem); 
  line-height: var(--chal-desc-line-height, 1.6); 
  color: var(--chal-desc-color, #444);
  border-left: var(--chal-desc-border-left, 3px solid #ff5252); /* 左侧红色竖线点缀 */
}

.empty-desc {
  color: var(--chal-empty-color, #ccc); font-style: italic;
}

.action-box {
  display: flex;
  align-items: center;
  gap: var(--chal-action-gap, 8px);
}
.chal-prefix { color: var(--muted, #999) }
</style>