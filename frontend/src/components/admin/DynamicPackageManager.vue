<template>
  <div class="dpm">
    <header class="dpm-head">
      <div>
        <h3 class="dpm-title">动态附件包</h3>
        <p class="dpm-desc">按队伍分发不同附件包（对齐 Ret2Shell DynamicPackage）</p>
      </div>
    </header>

    <n-alert v-if="featureStub" type="warning" :bordered="false" class="dpm-alert">
      后端仍返回 stub：上传 / 修改 / 删除不可用。
    </n-alert>

    <n-alert v-else-if="loadError" type="error" :bordered="false" class="dpm-alert">
      {{ loadError }}
    </n-alert>

    <div class="dpm-row">
      <label class="dpm-label">选择题目</label>
      <n-select
        v-model:value="selectedChallengeId"
        :options="challengeOptions"
        :loading="challengesLoading"
        clearable
        filterable
        placeholder="仅展示动态附件类题目"
        style="min-width: 280px; flex: 1"
        @update:value="onChallengeChange"
      />
      <n-button :loading="packagesLoading" :disabled="!selectedChallengeId" @click="loadPackages">
        刷新
      </n-button>
    </div>

    <div v-if="selectedChallengeId" class="dpm-body">
      <div class="dpm-toolbar">
        <span class="dpm-count">已上传 {{ packages.length }} 个包</span>
        <n-button type="primary" :disabled="featureStub" @click="showUpload = true">
          上传 ZIP
        </n-button>
      </div>

      <n-empty
        v-if="!packagesLoading && !packages.length"
        :description="featureStub ? '暂无数据（功能未开放）' : '暂无附件包'"
        class="dpm-empty"
      />

      <n-data-table
        v-else
        :columns="columns"
        :data="packages"
        :loading="packagesLoading"
        size="small"
        :bordered="false"
      />
    </div>

    <n-modal v-model:show="showUpload" preset="card" title="上传动态附件包" style="width: 480px">
      <n-alert v-if="featureStub" type="warning" :bordered="false" style="margin-bottom: 12px">
        当前为 stub，提交将失败。
      </n-alert>
      <n-form label-placement="top">
        <n-form-item label="题目">
          <n-select v-model:value="uploadChallengeId" :options="challengeOptions" />
        </n-form-item>
        <n-form-item label="ZIP 文件">
          <input type="file" accept=".zip" @change="onFileSelected" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showUpload = false">取消</n-button>
          <n-button type="primary" :loading="uploading" :disabled="featureStub || !selectedFile" @click="uploadPackage">
            上传
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script>
import { ref, computed, h, onMounted } from 'vue'
import {
  NAlert, NSelect, NButton, NEmpty, NDataTable, NModal, NForm, NFormItem, NSpace, useMessage,
} from 'naive-ui'
import { ctfAdmin } from '@/services/admin'
import { parseJsonResponse } from '@/utils/http'
import { apiErrorMessage } from '@/utils/apiError'

export default {
  name: 'DynamicPackageManager',
  components: { NAlert, NSelect, NButton, NEmpty, NDataTable, NModal, NForm, NFormItem, NSpace },
  props: {
    gameId: { type: [Number, String], default: null },
  },
  setup(props) {
    const message = useMessage()
    const challenges = ref([])
    const packages = ref([])
    const featureStub = ref(false)
    const loadError = ref('')
    const challengesLoading = ref(false)
    const packagesLoading = ref(false)
    const selectedChallengeId = ref(null)
    const uploadChallengeId = ref(null)
    const selectedFile = ref(null)
    const showUpload = ref(false)
    const uploading = ref(false)

    const challengeOptions = computed(() =>
      challenges.value.map(c => ({
        label: `${c.title} (#${c.id})`,
        value: c.id,
      })),
    )

    const columns = [
      { title: '变体', key: 'variant_id', width: 80 },
      { title: '文件名', key: 'filename' },
      { title: '哈希', key: 'file_hash', ellipsis: { tooltip: true } },
      {
        title: '状态',
        key: 'is_active',
        width: 80,
        render: r => (r.is_active ? '启用' : '禁用'),
      },
      {
        title: '操作',
        key: 'actions',
        width: 100,
        render: r => h(NButton, {
          size: 'tiny',
          type: 'error',
          secondary: true,
          disabled: featureStub.value,
          onClick: () => removePackage(r.id),
        }, { default: () => '删除' }),
      },
    ]

    function unwrapList(body) {
      if (!body) return []
      if (Array.isArray(body)) return body
      if (Array.isArray(body.data)) return body.data
      if (Array.isArray(body.data?.items)) return body.data.items
      if (Array.isArray(body.items)) return body.items
      return []
    }

    async function probeStub() {
      try {
        const res = await ctfAdmin.listDynamicPackages(1)
        const { data: body } = await parseJsonResponse(res)
        featureStub.value = body?.meta?.status === 'stub'
      } catch {
        /* ignore */
      }
    }

    async function loadChallengesForGame(gid) {
      const res = await ctfAdmin.listAdminChallenges(gid)
      const { data, ok } = await parseJsonResponse(res)
      return ok ? unwrapList(data) : []
    }

    async function loadChallenges() {
      challengesLoading.value = true
      loadError.value = ''
      try {
        await probeStub()
        let rows = []
        const preferred = props.gameId || new URLSearchParams(window.location.search).get('game_id')
        if (preferred) {
          rows = await loadChallengesForGame(preferred)
        }
        if (!rows.length) {
          const res = await ctfAdmin.listGames(100)
          const { data, ok } = await parseJsonResponse(res)
          const games = ok ? unwrapList(data) : []
          // 优先找有题目的赛事（跳过归档空场）
          for (const g of games.slice(0, 12)) {
            if (!g?.id) continue
            rows = await loadChallengesForGame(g.id)
            if (rows.length) break
          }
        }
        const dyn = rows.filter(
          c => c.challenge_type === 2 || c.type === 'dynamic_package' || c.challenge_type === 'dynamic',
        )
        challenges.value = dyn.length ? dyn : rows
        if (!challenges.value.length) {
          loadError.value = featureStub.value
            ? '暂无题目可选；动态附件包仍为 stub'
            : '未找到可管理的题目'
        }
      } catch (e) {
        loadError.value = apiErrorMessage(e, '加载题目失败')
      } finally {
        challengesLoading.value = false
      }
    }

    async function loadPackages() {
      if (!selectedChallengeId.value) return
      packagesLoading.value = true
      loadError.value = ''
      try {
        const res = await ctfAdmin.listDynamicPackages(selectedChallengeId.value)
        const { data: body, status, ok } = await parseJsonResponse(res)
        if (status === 401 || status === 403) {
          loadError.value = '无权限访问动态附件包'
          packages.value = []
          return
        }
        featureStub.value = body?.meta?.status === 'stub'
        packages.value = body?.packages || body?.data || []
        if (!Array.isArray(packages.value)) packages.value = []
        if (!ok && !featureStub.value) {
          loadError.value = body?.msg || '加载失败'
        }
      } catch (e) {
        loadError.value = apiErrorMessage(e, '加载包列表失败')
        packages.value = []
      } finally {
        packagesLoading.value = false
      }
    }

    function onChallengeChange(id) {
      uploadChallengeId.value = id
      if (id) loadPackages()
      else packages.value = []
    }

    function onFileSelected(e) {
      selectedFile.value = e.target.files?.[0] || null
    }

    async function uploadPackage() {
      if (!uploadChallengeId.value || !selectedFile.value) {
        message.warning('请选择题目和文件')
        return
      }
      uploading.value = true
      try {
        const form = new FormData()
        form.append('file', selectedFile.value)
        await ctfAdmin.uploadDynamicPackages(uploadChallengeId.value, form)
        message.success('上传成功')
        showUpload.value = false
        selectedChallengeId.value = uploadChallengeId.value
        await loadPackages()
      } catch (e) {
        message.error(apiErrorMessage(e, '上传失败'))
      } finally {
        uploading.value = false
      }
    }

    async function removePackage(id) {
      if (!window.confirm('确定删除此包？')) return
      try {
        const res = await ctfAdmin.deleteDynamicPackage(id)
        const { ok, data } = await parseJsonResponse(res)
        if (!ok) {
          message.error(data?.msg || '删除失败')
          return
        }
        message.success('已删除')
        await loadPackages()
      } catch (e) {
        message.error(apiErrorMessage(e, '删除失败'))
      }
    }

    onMounted(loadChallenges)

    return {
      featureStub,
      loadError,
      challengesLoading,
      packagesLoading,
      selectedChallengeId,
      uploadChallengeId,
      challengeOptions,
      packages,
      columns,
      showUpload,
      uploading,
      selectedFile,
      loadPackages,
      onChallengeChange,
      onFileSelected,
      uploadPackage,
    }
  },
}
</script>

<style scoped>
.dpm {
  padding: 4px 0 16px;
}
.dpm-head {
  margin-bottom: 12px;
}
.dpm-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text, var(--page-bg));
}
.dpm-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-muted, var(--muted));
}
.dpm-alert {
  margin-bottom: 14px;
}
.dpm-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.dpm-label {
  font-size: 13px;
  color: var(--text-muted, var(--muted));
}
.dpm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.dpm-count {
  font-size: 13px;
  color: var(--text-muted, var(--muted));
}
.dpm-empty {
  padding: 32px 0;
}
</style>
