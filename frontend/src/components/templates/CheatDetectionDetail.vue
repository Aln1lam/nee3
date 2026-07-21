<!--
动态题目和作弊检测前端界面增强模板
-->

<!-- ==================== 作弊检测详情页面 ==================== -->
<template>
  <div class="cheat-detection-detail">
    <n-card>
      <template #header>
        <div class="header">
          <h2>作弊检测 - 审核详情</h2>
          <n-tag :type="statusTagType" size="large">
            {{ statusText }}
          </n-tag>
        </div>
      </template>

      <n-spin :show="loading">
        <!-- 基本信息 -->
        <div class="section">
          <h3>基本信息</h3>
          <n-grid :cols="24" :x-gap="12" :y-gap="12">
            <n-grid-item :span="6">
              <div class="info-item">
                <label>题目:</label>
                <span>{{ cheatRecord.challenge?.title }}</span>
              </div>
            </n-grid-item>
            <n-grid-item :span="6">
              <div class="info-item">
                <label>类型:</label>
                <span>{{ cheatTypeText }}</span>
              </div>
            </n-grid-item>
            <n-grid-item :span="6">
              <div class="info-item">
                <label>检测时间:</label>
                <span>{{ formatTime(cheatRecord.detection_time) }}</span>
              </div>
            </n-grid-item>
            <n-grid-item :span="6">
              <div class="info-item">
                <label>相似度:</label>
                <n-progress type="circle" :percentage="Math.round(cheatRecord.similarity * 100)" />
              </div>
            </n-grid-item>
          </n-grid>
        </div>

        <!-- 问题描述 -->
        <div class="section">
          <h3>问题描述</h3>
          <n-alert type="error" closable>
            {{ getProblemDescription() }}
          </n-alert>
        </div>

        <!-- 对比信息 -->
        <div class="section">
          <h3>对比信息</h3>
          <n-grid :cols="24" :x-gap="12" :y-gap="12">
            <!-- 源队伍 (被怀疑者) -->
            <n-grid-item :span="12">
              <n-card title="队伍1 (被怀疑者)" :bordered="true">
                <n-descriptions :column="1" size="small">
                  <n-descriptions-item label="队伍">
                    {{ cheatRecord.source_team?.name || `用户 ${cheatRecord.source_user_id}` }}
                  </n-descriptions-item>
                  <n-descriptions-item label="用户">
                    {{ cheatRecord.source_user?.nickname }}
                  </n-descriptions-item>
                  <n-descriptions-item label="应该的Flag">
                    <n-code :code="cheatRecord.source_expected_flag" language="text" />
                  </n-descriptions-item>
                  <n-descriptions-item label="实际提交">
                    <n-code :code="cheatRecord.source_answer" language="text" />
                  </n-descriptions-item>
                  <n-descriptions-item v-if="cheatRecord.source_answer === cheatRecord.target_expected_flag" label="结论">
                    <n-alert type="error" size="small">
                      ⚠️ 提交内容完全匹配对方的正确flag！
                    </n-alert>
                  </n-descriptions-item>
                </n-descriptions>

                <!-- 动态容器日志 -->
                <div v-if="cheatRecord.is_dynamic_container && cheatRecord.source_container_logs" class="container-logs">
                  <h4>容器日志</h4>
                  <n-collapse accordion>
                    <n-collapse-item title="查看容器访问日志" name="source-logs">
                      <n-code
                        :code="cheatRecord.source_container_logs"
                        language="log"
                        :show-line-numbers="true"
                      />
                    </n-collapse-item>
                  </n-collapse>
                </div>
              </n-card>
            </n-grid-item>

            <!-- 目标队伍 (参考者) -->
            <n-grid-item :span="12">
              <n-card title="队伍2 (参考者/被抄的)" :bordered="true">
                <n-descriptions :column="1" size="small">
                  <n-descriptions-item label="队伍">
                    {{ cheatRecord.target_team?.name || `用户 ${cheatRecord.target_user_id}` }}
                  </n-descriptions-item>
                  <n-descriptions-item label="用户">
                    {{ cheatRecord.target_user?.nickname }}
                  </n-descriptions-item>
                  <n-descriptions-item label="应该的Flag">
                    <n-code :code="cheatRecord.target_expected_flag" language="text" />
                  </n-descriptions-item>
                  <n-descriptions-item label="实际提交">
                    <n-code :code="cheatRecord.target_answer" language="text" />
                  </n-descriptions-item>
                </n-descriptions>

                <!-- 动态容器日志 -->
                <div v-if="cheatRecord.is_dynamic_container && cheatRecord.target_container_logs" class="container-logs">
                  <h4>容器日志</h4>
                  <n-collapse accordion>
                    <n-collapse-item title="查看容器访问日志" name="target-logs">
                      <n-code
                        :code="cheatRecord.target_container_logs"
                        language="log"
                        :show-line-numbers="true"
                      />
                    </n-collapse-item>
                  </n-collapse>
                </div>
              </n-card>
            </n-grid-item>
          </n-grid>
        </div>

        <!-- 审核意见 -->
        <div class="section">
          <h3>审核意见</h3>
          <n-form :model="reviewForm">
            <n-form-item label="审核结论">
              <n-radio-group v-model:value="reviewForm.conclusion">
                <n-space>
                  <n-radio value="confirmed">确认作弊</n-radio>
                  <n-radio value="dismissed">驳回</n-radio>
                  <n-radio value="pending">待进一步调查</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>

            <n-form-item label="备注">
              <n-input
                v-model:value="reviewForm.notes"
                type="textarea"
                placeholder="输入审核备注"
                :rows="4"
              />
            </n-form-item>
          </n-form>
        </div>

        <!-- 动作按钮 -->
        <div class="actions">
          <n-button type="error" @click="submitReview('confirmed')" :loading="reviewing">
            确认作弊
          </n-button>
          <n-button type="warning" @click="submitReview('dismissed')" :loading="reviewing">
            驳回指控
          </n-button>
          <n-button type="default" @click="$router.back()">
            返回
          </n-button>
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  NCard, NButton, NSpin, NTag, NGrid, NGridItem, NAlert,
  NDescriptions, NDescriptionsItem, NCode, NCollapse, NCollapseItem,
  NForm, NFormItem, NRadioGroup, NRadio, NInput, NProgress, NSpace
} from 'naive-ui'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const message = useMessage()

const loading = ref(true)
const reviewing = ref(false)

const cheatRecord = ref({
  challenge: null,
  source_team: null,
  source_user: null,
  target_team: null,
  target_user: null,
  source_container_logs: null,
  target_container_logs: null
})

const reviewForm = ref({
  conclusion: 'pending',
  notes: ''
})

const statusTagType = computed(() => {
  const statusMap = {
    pending: 'warning',
    reviewed: 'info',
    confirmed: 'error',
    dismissed: 'success'
  }
  return statusMap[cheatRecord.value.status] || 'default'
})

const statusText = computed(() => {
  const textMap = {
    pending: '待审核',
    reviewed: '已审核',
    confirmed: '已确认作弊',
    dismissed: '已驳回'
  }
  return textMap[cheatRecord.value.status] || '未知'
})

const cheatTypeText = computed(() => {
  const typeMap = {
    direct_copy: '直接复制',
    similarity: '相似度过高',
    flag_mismatch: '答案不匹配',
    rapid_submission: '快速提交异常'
  }
  return typeMap[cheatRecord.value.cheat_type] || '未知'
})

function getProblemDescription() {
  const record = cheatRecord.value
  
  if (record.cheat_type === 'flag_mismatch') {
    return `队伍1 (${record.source_team?.name}) 提交的答案与队伍2 (${record.target_team?.name}) 的正确Flag完全相同 (相似度100%)。这表明队伍1可能获得了队伍2的题目文件或答案。`
  } else if (record.similarity >= 0.95) {
    return `队伍1和队伍2的答案高度相似 (相似度 ${(record.similarity * 100).toFixed(1)}%)，存在作弊嫌疑。`
  }
  
  return `两个队伍存在可疑的答案相似度 (相似度 ${(record.similarity * 100).toFixed(1)}%)。`
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

async function loadCheatRecord() {
  try {
    loading.value = true
    const recordId = route.params.id
    
    // 主路径：/api/admin/cheat-detection（无独立 details；按 id 从列表取）
    const response = await axios.get('/api/admin/cheat-detection', {
      params: { page: 1, per_page: 100 },
      withCredentials: true,
    })
    const items = response.data?.data?.items || response.data?.items || []
    const found = items.find((r) => String(r.id) === String(recordId))
    if (response.data?.status === 'success' || response.data?.code === 200) {
      if (found) {
        cheatRecord.value = found
      } else {
        message.error('未找到该作弊记录')
      }
    } else {
      message.error(response.data.message || response.data.msg || '加载失败')
    }
  } catch (error) {
    message.error('加载作弊记录失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function submitReview(conclusion) {
  try {
    reviewing.value = true
    const recordId = route.params.id
    
    // 主路径：/api/admin/cheat-records/:id/{review|confirm|dismiss}
    const action = conclusion === 'confirmed' || conclusion === 'confirm'
      ? 'confirm'
      : conclusion === 'dismissed' || conclusion === 'dismiss'
        ? 'dismiss'
        : 'review'
    const response = await axios.post(
      `/api/admin/cheat-records/${recordId}/${action}`,
      {
        admin_note: reviewForm.value.notes,
      },
      { withCredentials: true },
    )
    
    if (response.data.status === 'success') {
      message.success('审核已提交')
      await loadCheatRecord()
    } else {
      message.error(response.data.message || '提交失败')
    }
  } catch (error) {
    message.error('提交审核失败: ' + error.message)
  } finally {
    reviewing.value = false
  }
}

onMounted(() => {
  loadCheatRecord()
})
</script>

<style scoped>
.cheat-detection-detail {
  padding: var(--fib-21);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section {
  margin-top: 24px;
  margin-bottom: 24px;
}

.section h3 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item label {
  font-weight: 600;
  color: #666;
}

.container-logs {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.container-logs h4 {
  margin-bottom: 12px;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}
</style>

<!-- ==================== 动态附件管理界面 ==================== -->

<template>
  <div class="dynamic-attachment-admin">
    <n-card>
      <template #header>
        <div class="header-title">
          <span>动态附件管理</span>
          <n-button type="primary" @click="showUploadModal = true">
            + 上传附件包
          </n-button>
        </div>
      </template>

      <n-spin :show="loading">
        <!-- 已上传的包列表 -->
        <n-data-table
          :columns="columns"
          :data="packages"
          :pagination="{ pageSize: 20 }"
          :bordered="false"
        />
      </n-spin>
    </n-card>

    <!-- 上传 Modal -->
    <n-modal
      v-model:show="showUploadModal"
      title="上传动态附件包"
      preset="dialog"
      size="large"
    >
      <n-form :model="uploadForm" :rules="formRules" ref="formRef">
        <n-form-item label="题目" path="challenge_id">
          <n-select
            v-model:value="uploadForm.challenge_id"
            :options="challengeOptions"
            placeholder="选择题目"
          />
        </n-form-item>

        <n-form-item label="竞赛" path="game_id">
          <n-select
            v-model:value="uploadForm.game_id"
            :options="gameOptions"
            placeholder="选择竞赛"
          />
        </n-form-item>

        <n-form-item label="附件包(ZIP)" path="file">
          <n-upload
            v-model:file-list="fileList"
            accept=".zip"
            @change="handleFileChange"
          >
            <n-button>选择文件</n-button>
          </n-upload>
          <div class="upload-tip">
            上传包含多个压缩包的ZIP文件。系统将自动解析内部的所有压缩包，并随机分配给各队伍。
          </div>
        </n-form-item>
      </n-form>

      <template #action>
        <n-button @click="showUploadModal = false">取消</n-button>
        <n-button type="primary" @click="submitUpload" :loading="uploading">
          上传
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'

const message = useMessage()

const loading = ref(false)
const uploading = ref(false)
const showUploadModal = ref(false)

const packages = ref([])
const fileList = ref([])

const uploadForm = ref({
  challenge_id: null,
  game_id: null
})

const columns = [
  { title: '题目', key: 'challenge_title', width: 150 },
  { title: '包序号', key: 'package_index', width: 80 },
  { title: '原始文件名', key: 'package_filename', width: 200 },
  { title: '预期Flag', key: 'expected_flag', width: 200 },
  { title: '分配队伍', key: 'team_name', width: 120 },
  { title: '上传时间', key: 'created_at', width: 180 },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row) => h(NSpace, null, {
      default: () => [
        h(NButton, {
          type: 'tertiary',
          size: 'small',
          onClick: () => handleDelete(row.id)
        }, { default: () => '删除' })
      ]
    })
  }
]

const challengeOptions = computed(() => [
  // 从后端获取
])

const gameOptions = computed(() => [
  // 从后端获取
])

const formRules = {
  challenge_id: { required: true, message: '请选择题目', trigger: 'change' },
  game_id: { required: true, message: '请选择竞赛', trigger: 'change' },
  file: { required: true, message: '请选择文件', trigger: 'change' }
}

function handleFileChange() {
  // 文件变更处理
}

async function submitUpload() {
  try {
    uploading.value = true
    
    const formData = new FormData()
    formData.append('challenge_id', uploadForm.value.challenge_id)
    formData.append('game_id', uploadForm.value.game_id)
    
    if (fileList.value.length > 0) {
      formData.append('file', fileList.value[0].file)
    }
    
    // 主路径：/api/admin/dynamic-packages/challenges/:id/upload（field=file）
    const response = await axios.post(
      `/api/admin/dynamic-packages/challenges/${uploadForm.value.challenge_id}/upload`,
      formData,
      { withCredentials: true },
    )
    
    if (response.data.status === 'success' || response.data.code === 200) {
      message.success(response.data.msg || '上传成功')
      showUploadModal.value = false
      fileList.value = []
    } else {
      message.error(response.data.message || response.data.msg || '上传失败')
    }
  } catch (error) {
    message.error('上传出错: ' + error.message)
  } finally {
    uploading.value = false
  }
}

async function handleDelete(packageId) {
  // 删除逻辑
}
</script>

<style scoped>
.dynamic-attachment-admin {
  padding: var(--fib-21);
}

.header-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-tip {
  margin-top: 12px;
  padding: 12px;
  background-color: #f0f9ff;
  border-left: 3px solid #0ea5e9;
  color: #0c4a6e;
  font-size: 12px;
  border-radius: 4px;
}
</style>
