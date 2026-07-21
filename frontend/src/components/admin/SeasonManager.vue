<template>
  <div class="season-mgr">
    <header class="sm-head">
      <div>
        <h3 class="sm-title">赛季管理</h3>
        <p class="sm-desc">维护年度赛季元数据（如 2026 / 春季）</p>
      </div>
      <n-button type="primary" @click="openCreate">新建赛季</n-button>
    </header>

    <n-data-table
      :columns="columns"
      :data="rows"
      :loading="loading"
      size="small"
      :bordered="false"
    />

    <n-modal v-model:show="showModal" preset="card" :title="editingId ? '编辑赛季' : '新建赛季'" style="width: 420px">
      <n-form label-placement="top">
        <n-form-item label="年份" required>
          <n-input-number v-model:value="form.year" :min="2000" :max="2100" style="width: 100%" />
        </n-form-item>
        <n-form-item label="赛季名" required>
          <n-input v-model:value="form.season" placeholder="如 春季 / Spring" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="form.description" type="textarea" :rows="2" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="save">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script>
import { ref, h, onMounted } from 'vue'
import {
  NButton, NDataTable, NModal, NForm, NFormItem, NInput, NInputNumber, NSpace, useMessage,
} from 'naive-ui'
import { ctfAdmin } from '@/services/admin'
import { parseJsonResponse } from '@/utils/http'
import { apiErrorMessage } from '@/utils/apiError'

export default {
  name: 'SeasonManager',
  components: { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NInputNumber, NSpace },
  setup() {
    const message = useMessage()
    const rows = ref([])
    const loading = ref(false)
    const showModal = ref(false)
    const saving = ref(false)
    const editingId = ref(null)
    const form = ref({ year: new Date().getFullYear(), season: '', description: '' })

    const columns = [
      { title: 'ID', key: 'id', width: 60 },
      { title: '年份', key: 'year', width: 80 },
      { title: '赛季', key: 'season' },
      { title: '描述', key: 'description', ellipsis: { tooltip: true } },
      {
        title: '操作',
        key: 'actions',
        width: 140,
        render: (r) => h('div', { style: 'display:flex;gap:6px' }, [
          h(NButton, { size: 'tiny', onClick: () => openEdit(r) }, { default: () => '编辑' }),
          h(NButton, {
            size: 'tiny', type: 'error', secondary: true,
            onClick: () => remove(r.id),
          }, { default: () => '删除' }),
        ]),
      },
    ]

    async function load() {
      loading.value = true
      try {
        const res = await ctfAdmin.listSeasons()
        const { data, ok } = await parseJsonResponse(res)
        rows.value = ok ? (Array.isArray(data?.data) ? data.data : Array.isArray(data) ? data : []) : []
      } catch (e) {
        message.error(apiErrorMessage(e, '加载赛季失败'))
      } finally {
        loading.value = false
      }
    }

    function openCreate() {
      editingId.value = null
      form.value = { year: new Date().getFullYear(), season: '', description: '' }
      showModal.value = true
    }

    function openEdit(r) {
      editingId.value = r.id
      form.value = { year: r.year, season: r.season || '', description: r.description || '' }
      showModal.value = true
    }

    async function save() {
      if (!form.value.year || !String(form.value.season || '').trim()) {
        message.warning('年份与赛季名必填')
        return
      }
      saving.value = true
      try {
        const payload = {
          year: form.value.year,
          season: String(form.value.season).trim(),
          description: form.value.description || null,
        }
        const res = editingId.value
          ? await ctfAdmin.updateSeason(editingId.value, payload)
          : await ctfAdmin.createSeason(payload)
        const { ok, data } = await parseJsonResponse(res)
        if (!ok) {
          message.error(data?.msg || '保存失败')
          return
        }
        message.success('已保存')
        showModal.value = false
        await load()
      } catch (e) {
        message.error(apiErrorMessage(e, '保存失败'))
      } finally {
        saving.value = false
      }
    }

    async function remove(id) {
      if (!window.confirm(`删除赛季 #${id}？`)) return
      try {
        const res = await ctfAdmin.deleteSeason(id)
        const { ok, data } = await parseJsonResponse(res)
        if (!ok) {
          message.error(data?.msg || '删除失败')
          return
        }
        message.success('已删除')
        await load()
      } catch (e) {
        message.error(apiErrorMessage(e, '删除失败'))
      }
    }

    onMounted(load)
    return {
      rows, loading, showModal, saving, editingId, form, columns,
      openCreate, openEdit, save, remove,
    }
  },
}
</script>

<style scoped>
.sm-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
.sm-title { margin: 0 0 4px; font-size: 16px; }
.sm-desc { margin: 0; color: var(--muted); font-size: 13px; }
</style>
