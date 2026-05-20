<template>
  <div class="challenge-admin">
    <n-card>
      <template #header>
        <div class="header-title">
          <span>CTF 题目管理</span>
          <n-select
            v-model:value="selectedGameId"
            :options="gameOptions"
            style="width: 200px; margin: 0 10px;"
            placeholder="选择竞赛"
            clearable
          />
          <n-button type="primary" @click="showCreateModal = true">
            + 创建题目
          </n-button>
        </div>
      </template>

      <n-spin :show="loading">
        <n-data-table
          :columns="columns"
          :data="challenges"
          :pagination="{ pageSize: 20 }"
          :bordered="false"
        />
      </n-spin>
    </n-card>

    <!-- 创建/编辑题目 Modal -->
    <n-modal
      v-model:show="showCreateModal"
      :title="editingChallenge ? '编辑题目' : '创建题目'"
      preset="dialog"
      size="large"
    >
      <n-form
        :model="formData"
        :rules="formRules"
        ref="formRef"
      >
        <n-form-item label="竞赛" path="game_id">
          <n-select
            v-model:value="formData.game_id"
            :options="gameOptions"
            placeholder="选择竞赛"
          />
        </n-form-item>

        <n-form-item label="题目标题" path="title">
          <n-input
            v-model:value="formData.title"
            placeholder="题目标题"
          />
        </n-form-item>

        <n-form-item label="分类" path="category">
          <n-select
            v-model:value="formData.category"
            :options="categoryOptions"
            filterable
            tag
            placeholder="选择或新建分类"
          />
        </n-form-item>

        <n-form-item label="分值" path="points">
          <n-input-number
            v-model:value="formData.points"
            placeholder="100"
            :min="1"
          />
        </n-form-item>

        <n-form-item label="描述">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="题目描述（支持 HTML）"
            :rows="4"
          />
        </n-form-item>

        <n-form-item label="提示">
          <n-input
            v-model:value="formData.hint"
            type="textarea"
            placeholder="提示信息"
            :rows="2"
          />
        </n-form-item>

        <n-form-item label="Flag" path="flag">
          <n-input
            v-model:value="formData.flag"
            type="password"
            placeholder="flag 内容"
            show-password-on="click"
          />
        </n-form-item>

        <n-form-item label="题目类型" path="challenge_type">
          <n-select
            v-model:value="formData.challenge_type"
            :options="[
              { label: '静态文件题', value: 0 },
              { label: '共享容器题', value: 1 },
              { label: '动态文件题', value: 2 },
              { label: '动态容器题', value: 3 }
            ]"
            placeholder="选择题目类型"
          />
        </n-form-item>

        <!-- Docker 容器题目相关配置 -->
        <template v-if="formData.challenge_type === 1 || formData.challenge_type === 3">
          <n-form-item label="Docker 镜像" path="docker_image">
            <n-input
              v-model:value="formData.docker_image"
              placeholder="e.g., nginx:latest 或 myregistry.azurecr.io/myimage:v1"
            />
          </n-form-item>

          <n-form-item label="容器端口">
            <n-input-number
              v-model:value="formData.docker_port"
              placeholder="80"
              :min="1"
              :max="65535"
            />
          </n-form-item>

          <n-form-item label="网络模式">
            <n-select
              v-model:value="formData.network_mode"
              :options="[
                { label: '开放网络 (Open)', value: 'Open' },
                { label: '隔离网络 (Isolated)', value: 'Isolated' },
                { label: '自定义网络 (Custom)', value: 'Custom' }
              ]"
              placeholder="选择网络模式"
            />
          </n-form-item>

          <n-divider style="margin: 10px 0;">
            <span style="font-size: 12px; color: #999;">资源限制</span>
          </n-divider>

          <n-space vertical>
            <n-form-item label="CPU 核心数">
              <n-input-number
                v-model:value="formData.cpu_count"
                placeholder="1"
                :min="0.5"
                :max="16"
                :step="0.5"
              />
            </n-form-item>

            <n-form-item label="内存限制 (MB)">
              <n-input-number
                v-model:value="formData.memory_limit"
                placeholder="256"
                :min="32"
                :max="4096"
                :step="32"
              />
            </n-form-item>

            <n-form-item label="存储限制 (MB)">
              <n-input-number
                v-model:value="formData.storage_limit"
                placeholder="1024"
                :min="256"
                :max="10240"
                :step="256"
              />
            </n-form-item>
          </n-space>
        </template>

        <n-form-item label="基础分值">
          <n-input-number
            v-model:value="formData.original_points"
            placeholder="100"
            :min="1"
          />
        </n-form-item>

        <n-form-item label="最小分值比例 (0.0-1.0)">
          <n-input-number
            v-model:value="formData.min_score_rate"
            placeholder="0.25"
            :min="0"
            :max="1"
            :step="0.05"
          />
          <span style="margin-left: 10px; color: #999;">解题人数越多，分值越低</span>
        </n-form-item>

        <n-form-item label="是否启用" path="is_enabled">
          <n-switch v-model:value="formData.is_enabled" />
        </n-form-item>
      </n-form>

      <template #action>
        <n-button @click="showCreateModal = false" :disabled="submitting">取消</n-button>
        <n-button type="primary" @click="submitForm" :loading="submitting">
          {{ submitting ? '提交中...' : (editingChallenge ? '更新' : '创建') }}
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, watch, h } from 'vue'
import {
  NCard, NButton, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NSwitch, NSpin, NSpace, NDivider, useMessage
} from 'naive-ui'

export default {
  components: {
    NCard, NButton, NDataTable, NModal, NForm, NFormItem,
    NInput, NInputNumber, NSelect, NSwitch, NSpin, NSpace, NDivider
  },
  setup() {
    const axios = inject('axios')
    const message = useMessage()

    const loading = ref(false)
    const submitting = ref(false)
    const showCreateModal = ref(false)
    const selectedGameId = ref(null)
    const games = ref([])
    const challenges = ref([])
    const categories = ref([])
    const editingChallenge = ref(null)
    const formRef = ref(null)

    const formData = ref({
      game_id: null,
      title: '',
      category: '',
      points: 100,
      original_points: 100,
      description: '',
      hint: '',
      flag: '',
      challenge_type: 0,  // 0=StaticAttachment, 1=StaticContainer, 2=DynamicAttachment, 3=DynamicContainer
      docker_image: '',
      docker_port: 80,
      network_mode: 'Open',  // Open, Isolated, Custom
      cpu_count: 1,
      memory_limit: 256,     // MB
      storage_limit: 1024,   // MB
      min_score_rate: 0.25,
      is_dynamic: false,     // 保留兼容性
      is_enabled: true
    })

    const formRules = {
      game_id: { required: true, message: '请选择竞赛', trigger: 'change' },
      title: { required: true, message: '请输入题目标题', trigger: 'blur' },
      category: { required: true, message: '请选择分类', trigger: 'change' },
      points: { required: true, message: '请输入分值', trigger: 'blur' },
      flag: { required: true, message: '请输入 Flag', trigger: 'blur' }
    }

    const gameOptions = computed(() =>
      games.value.map(g => ({ label: g.title, value: g.id }))
    )

    const categoryOptions = computed(() =>
      categories.value.map(c => ({ label: c.name, value: c.name }))
    )

    const columns = [
      {
        title: '题目',
        key: 'title',
        width: 150
      },
      {
        title: '分类',
        key: 'category_name',
        width: 100
      },
      {
        title: '分值',
        key: 'points',
        width: 80
      },
      {
        title: '提交次数',
        key: 'submission_count',
        width: 100,
        render: (row) => row.submission_count || 0
      },
      {
        title: '解决人数',
        key: 'solve_count',
        width: 100,
        render: (row) => row.solve_count || 0
      },
      {
        title: '动态',
        key: 'is_dynamic',
        width: 80,
        render: (row) => row.is_dynamic ? '是' : '否'
      },
      {
        title: '状态',
        key: 'is_enabled',
        width: 80,
        render: (row) => row.is_enabled ? '启用' : '禁用'
      },
      {
        title: '操作',
        key: 'actions',
        width: 150,
        render: (row) => h('div', { style: 'display: flex; gap: 8px;' }, [
          h(NButton, {
            text: true,
            type: 'primary',
            onClick: () => editChallenge(row),
            size: 'small'
          }, { default: () => '编辑' }),
          h(NButton, {
            text: true,
            type: 'error',
            onClick: () => deleteChallenge(row.id),
            size: 'small'
          }, { default: () => '删除' })
        ])
      }
    ]

    const fetchGames = async () => {
      try {
        const response = await axios.get('/api/competitions/')
        games.value = response.data.data || []
        if (!selectedGameId.value && games.value.length > 0) {
          selectedGameId.value = games.value[0].id
        }
      } catch (error) {
        message.error('获取竞赛列表失败')
      }
    }

    const fetchCategories = async () => {
      try {
        const response = await axios.get('/api/admin/challenges/categories')
        categories.value = response.data.data || []
      } catch (error) {
        console.warn('获取分类失败', error)
      }
    }

    const fetchChallenges = async () => {
      if (!selectedGameId.value) return

      try {
        loading.value = true
        const response = await axios.get(`/api/admin/challenges/games/${selectedGameId.value}/challenges-list`)
        challenges.value = response.data.data || []
      } catch (error) {
        message.error('获取题目列表失败')
      } finally {
        loading.value = false
      }
    }

    const editChallenge = (challenge) => {
      editingChallenge.value = challenge
      formData.value = {
        game_id: challenge.game_id,
        title: challenge.title,
        category: challenge.category || challenge.category_name,
        points: challenge.points,
        original_points: challenge.original_points || challenge.points,
        description: challenge.description,
        hint: challenge.hint,
        flag: challenge.flag,
        challenge_type: challenge.challenge_type || 0,
        docker_image: challenge.docker_image || '',
        docker_port: challenge.docker_port || 80,
        network_mode: challenge.network_mode || 'Open',
        cpu_count: challenge.cpu_count || 1,
        memory_limit: challenge.memory_limit || 256,
        storage_limit: challenge.storage_limit || 1024,
        min_score_rate: challenge.min_score_rate || 0.25,
        is_dynamic: challenge.is_dynamic,
        is_enabled: challenge.is_enabled
      }
      showCreateModal.value = true
    }

    const deleteChallenge = async (challengeId) => {
      if (!confirm('确定要删除这个题目吗？')) return

      try {
        await axios.delete(
          `/api/admin/challenges/games/${selectedGameId.value}/challenges/${challengeId}`
        )
        message.success('题目删除成功')
        await fetchChallenges()
      } catch (error) {
        message.error(error.response?.data?.msg || '删除失败')
      }
    }

    const submitForm = async () => {
      try {
        submitting.value = true
        // 基本验证
        if (!formData.value.title?.trim()) {
          message.error('请输入题目标题')
          return
        }
        if (!formData.value.flag?.trim()) {
          message.error('请输入 Flag')
          return
        }
        if (!formData.value.category) {
          message.error('请选择分类')
          return
        }
        if (!formData.value.points || formData.value.points <= 0) {
          message.error('请输入有效的分值')
          return
        }

        const gameId = formData.value.game_id || selectedGameId.value
        if (!gameId) {
          message.error('请选择竞赛')
          return
        }

        const submitData = {
          title: formData.value.title.trim(),
          description: formData.value.description || '',
          category: formData.value.category,
          points: parseInt(formData.value.points) || 100,
          original_points: parseInt(formData.value.original_points) || parseInt(formData.value.points) || 100,
          flag: formData.value.flag.trim(),
          hint: formData.value.hint || '',
          challenge_type: formData.value.challenge_type || 0,
          
          // Docker相关字段
          docker_image: formData.value.docker_image || null,
          docker_port: parseInt(formData.value.docker_port) || 80,
          network_mode: formData.value.network_mode || 'Open',
          cpu_count: parseFloat(formData.value.cpu_count) || 1,
          memory_limit: parseInt(formData.value.memory_limit) || 256,
          storage_limit: parseInt(formData.value.storage_limit) || 1024,
          min_score_rate: parseFloat(formData.value.min_score_rate) || 0.25,
          
          is_enabled: formData.value.is_enabled !== false
        }
        
        // 容器题目的验证
        if ((formData.value.challenge_type === 1 || formData.value.challenge_type === 3) && !submitData.docker_image) {
          message.error('容器题目必须指定 Docker 镜像')
          return
        }

        console.log('Submitting challenge:', submitData)

        let response
        let successMsg
        if (editingChallenge.value) {
          // 更新
          response = await axios.put(
            `/api/admin/challenges/games/${gameId}/challenges/${editingChallenge.value.id}`,
            submitData,
            { headers: { 'Content-Type': 'application/json' } }
          )
          console.log('Update response:', response)
          successMsg = '✅ 题目更新成功'
        } else {
          // 创建
          response = await axios.post(
            `/api/admin/challenges/games/${gameId}/challenges`,
            submitData,
            { headers: { 'Content-Type': 'application/json' } }
          )
          console.log('Create response:', response)
          successMsg = '✅ 题目创建成功'
        }

        message.success(successMsg, { duration: 3 })
        showCreateModal.value = false
        editingChallenge.value = null
        formData.value = {
          game_id: null,
          title: '',
          category: '',
          points: 100,
          original_points: 100,
          description: '',
          hint: '',
          flag: '',
          challenge_type: 0,
          docker_image: '',
          docker_port: 80,
          network_mode: 'Open',
          cpu_count: 1,
          memory_limit: 256,
          storage_limit: 1024,
          min_score_rate: 0.25,
          is_dynamic: false,
          is_enabled: true
        }
        await fetchChallenges()
      } catch (error) {
        console.error('Submit error:', error)
        let errorMsg = '操作失败'
        
        if (error?.response?.data?.msg) {
          errorMsg = error.response.data.msg
        } else if (error?.message) {
          errorMsg = error.message
        } else if (Array.isArray(error)) {
          errorMsg = error.map(e => e?.message || String(e)).join('; ')
        }
        
        message.error('❌ ' + errorMsg, { duration: 3 })
      } finally {
        submitting.value = false
      }
    }

    onMounted(async () => {
      await fetchGames()
      await fetchCategories()
    })

    // 监听选中的竞赛变化
    watch(selectedGameId, () => {
      if (selectedGameId.value) {
        fetchChallenges()
      }
    })

    return {
      loading,
      submitting,
      showCreateModal,
      selectedGameId,
      challenges,
      columns,
      gameOptions,
      categoryOptions,
      formData,
      formRules,
      formRef,
      editingChallenge,
      editChallenge,
      deleteChallenge,
      submitForm
    }
  }
}
</script>

<style scoped>
.challenge-admin {
  padding: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
