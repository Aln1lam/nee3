"""Fix UTF-8 Chinese text corrupted to ?? in key frontend Vue files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frontend" / "src"

REPLACEMENTS = {
    "components/PlatformLanding.vue": [
        ('<span class="splash-emoji">??</span>', '<span class="splash-emoji">🏁</span>'),
        ("<p class=\"hero-eyebrow\">NEEPU ? CAMPUS CTF</p>", "<p class=\"hero-eyebrow\">NEEPU · CAMPUS CTF</p>"),
        ("<p class=\"hero-desc\">????????????? ? ??????Wiki ????</p>",
         "<p class=\"hero-desc\">东北电力大学 CTF 实训平台 · 赛事刷题 · Wiki 教程</p>"),
        ("<span>????</span>", "<span>快速开始</span>"),
        ("<span class=\"quick-label\">????</span>\n              <span class=\"quick-hint\">???? ? ??? ? ??</span>",
         "<span class=\"quick-label\">进入赛事</span>\n              <span class=\"quick-hint\">积分赛 · 排行榜 · 解题</span>"),
        ("<span class=\"quick-label\">????</span>\n              <span class=\"quick-hint\">??? ? ?????</span>",
         "<span class=\"quick-label\">训练靶场</span>\n              <span class=\"quick-hint\">永久开放 · 随时刷题</span>"),
        ("<span class=\"quick-label\">???</span>\n              <span class=\"quick-hint\">???? ? ????</span>",
         "<span class=\"quick-label\">知识库</span>\n              <span class=\"quick-hint\">教程文档 · 学习路线</span>"),
        ('<span class="live-tag">???</span>', '<span class="live-tag">进行中</span>'),
        ('<span class="live-arrow">?</span>', '<span class="live-arrow">→</span>'),
        ("{{ footerOrg || '??????' }}", "{{ footerOrg || '东北电力大学' }}"),
        ('<router-link to="/wiki">???</router-link>', '<router-link to="/wiki">知识库</router-link>'),
        ("return name.endsWith('??') ? name.slice(0, -2) : name", "return name.endsWith('平台') ? name.slice(0, -2) : name"),
        ("return name.endsWith('??') ? '??' : ''", "return name.endsWith('平台') ? '平台' : ''"),
        ("{ code: 'WEB', title: 'Web ??', desc: '????????????', action: () => router.push('/training') }",
         "{ code: 'WEB', title: 'Web 安全', desc: 'SQL注入、XSS 等经典题型', action: () => router.push('/training') }"),
        ("{ code: 'PWN', title: '???', desc: '????ROP ?????', action: () => router.push('/training') }",
         "{ code: 'PWN', title: '二进制', desc: '栈溢出、ROP 与逆向分析', action: () => router.push('/training') }"),
        ("{ code: 'CTF', title: '????', desc: '??????????', action: () => router.push('/games') }",
         "{ code: 'CTF', title: '正式赛事', desc: '校内赛、积分赛与排行榜', action: () => router.push('/games') }"),
        ("{ code: 'DOC', title: 'Wiki ??', desc: '??????????', action: () => router.push('/wiki') }",
         "{ code: 'DOC', title: 'Wiki 教程', desc: 'WriteUp 与知识库文档', action: () => router.push('/wiki') }"),
    ],
    "components/shared/SidebarLayout.vue": [
        ("{{ mobileCollapsed ? '????' : '????' }}", "{{ mobileCollapsed ? '展开菜单' : '收起菜单' }}"),
        (":aria-label=\"collapsed ? '????' : '????'\"", ":aria-label=\"collapsed ? '展开侧栏' : '收起侧栏'\""),
        ('<span class="chevron" :class="{ \'is-collapsed\': collapsed }">?</span>',
         '<span class="chevron" :class="{ \'is-collapsed\': collapsed }">‹</span>'),
    ],
    "components/ErrorPage.vue": [
        ("<p v-if=\"isTeapot\" class=\"matrix-page-desc teapot-hint\">? ???????????</p>",
         "<p v-if=\"isTeapot\" class=\"matrix-page-desc teapot-hint\">☕ 我是茶壶，不能冲泡咖啡。</p>"),
        ('@click="$router.push(\'/\')">????</n-button>', '@click="$router.push(\'/\')">返回首页</n-button>'),
        ('@click="$router.back()">?????</n-button>', '@click="$router.back()">返回上一页</n-button>'),
        ('class="error-trace-hint muted">???? {{ code }}</div>', 'class="error-trace-hint muted">错误码 {{ code }}</div>'),
        ("'401': { title: '???', desc: '??????????????' }", "'401': { title: '未授权', desc: '请先登录后再访问此页面' }"),
        ("'403': { title: '????', desc: '???? ? ?????????????' }", "'403': { title: '禁止访问', desc: '权限不足 · 请联系管理员获取权限' }"),
        ("'404': { title: '???', desc: '???????????????????' }", "'404': { title: '未找到', desc: '页面不存在或已被移除' }"),
        ("'412': { title: '??????', desc: '??????????????' }", "'412': { title: '前置条件失败', desc: '请求未满足服务器前置条件' }"),
        ("'418': { title: '????', desc: '?????????RFC 2324 ??? 418 I\\'m a teapot?' }",
         "'418': { title: '我是茶壶', desc: '服务器拒绝冲泡咖啡（RFC 2324 · 418 I\\'m a teapot）' }"),
        ("'500': { title: '?????', desc: '???????????????????' }", "'500': { title: '服务器错误', desc: '服务器内部出错，请稍后重试' }"),
        ("'502': { title: '????', desc: '???????????????' }", "'502': { title: '网关错误', desc: '上游服务不可用，请稍后重试' }"),
        ("unknown: { title: '????', desc: '???????????' }", "unknown: { title: '出错了', desc: '发生未知错误' }"),
    ],
    "components/AccountSettings.vue": [
        ('title="????"', 'title="账号设置"'),
        ('subtitle="ACCOUNT � SETTINGS"', 'subtitle="ACCOUNT · SETTINGS"'),
        ("{ label: '????', path: '/account/settings/info', code: 'USR' }", "{ label: '基本信息', path: '/account/settings/info', code: 'USR' }"),
        ("{ label: '????', path: '/account/settings/password', code: 'PWD' }", "{ label: '修改密码', path: '/account/settings/password', code: 'PWD' }"),
        ("{ label: '?????', path: '/account/settings/oauth', code: 'OAU' }", "{ label: '第三方绑定', path: '/account/settings/oauth', code: 'OAU' }"),
        ("{ label: '????', path: '/account/settings/mov-esp-ebp-pop-ebp', code: 'DEL' }", "{ label: '注销账号', path: '/account/settings/mov-esp-ebp-pop-ebp', code: 'DEL' }"),
    ],
}

CAPTCHA = r'''<template>
  <div class="captcha-wrap">
    <img
      v-if="imgUrl"
      :src="imgUrl"
      alt="验证码"
      class="captcha-img"
      title="点击刷新验证码"
      @click="refresh"
    />
    <button v-else class="captcha-placeholder" type="button" @click="refresh">加载验证码</button>
    <div class="captcha-input-col">
      <n-input
        v-model:value="answer"
        placeholder="验证码（至少4字符）"
        :maxlength="8"
        :disabled="disabled"
        :status="errorHint ? 'error' : undefined"
        @update:value="onAnswerInput"
        @keydown.enter="$emit('enter')"
      />
      <p v-if="errorHint" class="captcha-error">{{ errorHint }}</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { NInput } from 'naive-ui'

export default {
  name: 'Captcha',
  components: { NInput },
  props: {
    disabled: { type: Boolean, default: false },
    minLength: { type: Number, default: 4 },
  },
  emits: ['update:modelValue', 'update:captchaId', 'enter', 'valid'],
  setup(props, { emit, expose }) {
    const imgUrl = ref('')
    const answer = ref('')
    const captchaId = ref('')
    const touched = ref(false)

    const errorHint = computed(() => {
      if (!touched.value || !answer.value) return ''
      if (answer.value.length < props.minLength) return `验证码至少 ${props.minLength} 个字符`
      return ''
    })

    const isValid = computed(() =>
      !!captchaId.value && answer.value.length >= props.minLength,
    )

    async function refresh() {
      try {
        if (imgUrl.value) URL.revokeObjectURL(imgUrl.value)
        const res = await axios.get('/api/captcha/', { responseType: 'blob' })
        captchaId.value = res.headers['x-captcha-id'] || ''
        imgUrl.value = URL.createObjectURL(res.data)
        answer.value = ''
        touched.value = false
        emitValue()
      } catch {
        imgUrl.value = ''
        captchaId.value = ''
        emitValue()
      }
    }

    function emitValue() {
      emit('update:modelValue', answer.value)
      emit('update:captchaId', captchaId.value)
      emit('valid', isValid.value)
    }

    function onAnswerInput() {
      touched.value = true
      emitValue()
    }

    onMounted(refresh)
    onUnmounted(() => {
      if (imgUrl.value) URL.revokeObjectURL(imgUrl.value)
    })

    expose({ refresh, isValid })

    return { imgUrl, answer, errorHint, refresh, onAnswerInput }
  },
}
</script>

<style scoped>
.captcha-wrap {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.captcha-input-col { flex: 1; min-width: 0; }
.captcha-img {
  height: 40px;
  width: 120px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  cursor: pointer;
  object-fit: cover;
  flex-shrink: 0;
}
.captcha-placeholder {
  height: 40px;
  width: 120px;
  border-radius: var(--radius-md);
  border: 1px dashed var(--border);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 12px;
  flex-shrink: 0;
}
.captcha-error {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--error, #f83030);
}
</style>
'''

UI_THEME = r'''<template>
  <n-popover trigger="click" placement="bottom-end">
    <template #trigger>
      <button class="theme-btn" :title="label" aria-label="切换主题">
        {{ isDark ? '🌙' : '☀️' }}
      </button>
    </template>
    <div class="theme-panel">
      <button class="theme-option" @click="setTheme('light')">浅色</button>
      <button class="theme-option" @click="setTheme('dark')">深色</button>
      <label class="follow-system">
        <input type="checkbox" :checked="followSystem" @change="onFollowChange" />
        跟随系统
      </label>
    </div>
  </n-popover>
</template>

<script>
import { onMounted } from 'vue'
import { NPopover } from 'naive-ui'
import { useTheme } from '@/composables/useTheme'

export default {
  name: 'UiThemeBox',
  components: { NPopover },
  setup() {
    const { isDark, label, followSystem, setTheme, setFollowSystem, initTheme } = useTheme()

    function onFollowChange(e) {
      setFollowSystem(e.target.checked)
    }

    onMounted(() => initTheme())

    return { isDark, label, followSystem, setTheme, onFollowChange }
  },
}
</script>

<style scoped>
.theme-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 14px;
}
.theme-panel { display: flex; flex-direction: column; gap: 6px; min-width: 120px; }
.theme-option {
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
}
.theme-option:hover { background: var(--hover); }
.follow-system {
  font-size: 12px;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  cursor: pointer;
}
</style>
'''

UI_NOTIF = r'''<template>
  <n-popover trigger="click" placement="bottom-end" :width="320" @update:show="onShow">
    <template #trigger>
      <button class="notif-btn" aria-label="通知消息" :class="{ unread: hasUnread }">
        <span class="notif-icon">{{ hasUnread ? '🔔' : '🔕' }}</span>
      </button>
    </template>
    <div class="notif-panel">
      <div class="notif-header">通知消息</div>
      <div v-if="!history.length" class="notif-empty">暂无消息</div>
      <ul v-else class="notif-list">
        <li v-for="item in history" :key="item.id" :class="['notif-item', item.level]">
          <span class="notif-level">{{ levelLabel(item.level) }}</span>
          <span class="notif-msg">{{ item.message }}</span>
          <time class="notif-time">{{ formatTime(item.time) }}</time>
        </li>
      </ul>
      <button v-if="history.length" class="clear-btn" @click="clearAll">清空</button>
    </div>
  </n-popover>
</template>

<script>
import { computed } from 'vue'
import { NPopover } from 'naive-ui'
import { useNotificationHistory } from '@/composables/toast'

export default {
  name: 'UiNotificationBox',
  components: { NPopover },
  setup() {
    const { history, clearHistory, markAllRead } = useNotificationHistory()

    const hasUnread = computed(() => history.value.some(h => !h.read))

    function levelLabel(level) {
      const map = { info: '信息', warning: '警告', error: '错误', success: '成功' }
      return map[level] || level
    }

    function formatTime(ts) {
      try {
        return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      } catch { return '' }
    }

    function onShow(show) {
      if (show) markAllRead()
    }

    function clearAll() {
      clearHistory()
    }

    return { history, hasUnread, levelLabel, formatTime, onShow, clearAll }
  },
}
</script>

<style scoped>
.notif-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: 32px;
  height: 32px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.notif-btn.unread { border-color: var(--primary); }
.notif-btn.unread::after {
  content: '';
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
}
.notif-icon { font-size: 14px; }
.notif-panel { max-height: 360px; overflow-y: auto; }
.notif-header { font-weight: 700; margin-bottom: 8px; color: var(--text); }
.notif-empty { color: var(--muted); font-size: 13px; padding: 12px 0; }
.notif-list { list-style: none; margin: 0; padding: 0; }
.notif-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
.notif-item.warning .notif-level { color: #fab005; }
.notif-item.error .notif-level { color: var(--accent-red, #f83030); }
.notif-item.info .notif-level { color: var(--primary); }
.notif-level { font-size: 11px; font-weight: 600; margin-right: 6px; }
.notif-msg { color: var(--text); }
.notif-time { display: block; font-size: 11px; color: var(--muted); margin-top: 2px; }
.clear-btn {
  margin-top: 8px;
  width: 100%;
  padding: 6px;
  border: 1px solid var(--border);
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
  color: var(--muted);
}
.clear-btn:hover { background: var(--hover); }
</style>
'''

BULLETIN_CREATE = r'''<template>
  <MatrixShell
    prompt=""
    title="发布平台公告"
    subtitle="BULLETIN · NEW"
    page-prompt="vim /bulletin/new"
    page-title="发布平台公告"
    page-desc="支持 Markdown 格式，发布后用户可见"
  >
    <template #sidebar-footer>
      <router-link to="/bulletin" class="sidebar-link">
        <span class="link-code">BAK</span>
        <span>返回公告中心</span>
      </router-link>
    </template>

    <n-form label-placement="top" class="create-form matrix-panel">
      <n-form-item label="公告标题" required>
        <n-input v-model:value="form.title" placeholder="输入公告标题" maxlength="256" show-count />
      </n-form-item>
      <n-form-item label="公告内容" required>
        <n-input
          v-model:value="form.content"
          type="textarea"
          placeholder="支持 Markdown 格式"
          :rows="12"
        />
      </n-form-item>
      <n-form-item label="立即发布（激活）">
        <n-switch v-model:value="form.is_active" />
      </n-form-item>
      <div class="form-actions">
        <n-button type="primary" :loading="saving" @click="submit">发布公告</n-button>
        <n-button @click="$router.push('/bulletin')">取消</n-button>
      </div>
    </n-form>

    <div v-if="previewHtml" class="preview-section matrix-panel">
      <div class="matrix-section-head">
        <span class="link-code">PRV</span>
        <h3>预览</h3>
      </div>
      <div class="preview-body markdown-body" v-html="previewHtml"></div>
    </div>
  </MatrixShell>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { parseMarkdownSafe } from '../utils/markdown'
import { NForm, NFormItem, NInput, NButton, NSwitch, useMessage } from 'naive-ui'
import { MatrixShell } from '@/components/shared'
import { platformAdmin } from '@/services/admin'

export default {
  name: 'BulletinCreate',
  components: { NForm, NFormItem, NInput, NButton, NSwitch, MatrixShell },
  setup() {
    const router = useRouter()
    const message = useMessage()
    const saving = ref(false)
    const form = ref({ title: '', content: '', is_active: true })

    const previewHtml = computed(() => {
      if (!form.value.content.trim()) return ''
      try { return parseMarkdownSafe(form.value.content) } catch { return '' }
    })

    async function submit() {
      if (!form.value.title.trim()) {
        message.warning('请填写公告标题')
        return
      }
      if (!form.value.content.trim()) {
        message.warning('请填写公告内容')
        return
      }
      saving.value = true
      try {
        await platformAdmin.createAnnouncement({
          title: form.value.title.trim(),
          content: form.value.content.trim(),
          is_active: form.value.is_active,
        })
        message.success('公告发布成功')
        router.push('/bulletin')
      } catch (e) {
        message.error('发布失败: ' + (e.response?.data?.msg || '未知错误'))
      } finally {
        saving.value = false
      }
    }

    return { form, saving, previewHtml, submit }
  },
}
</script>

<style scoped>
.create-form { margin-bottom: 16px; max-width: 720px; }
.form-actions { display: flex; gap: 12px; }
.preview-section { max-width: 720px; }
.preview-section h3 { margin: 0; font-size: 1rem; color: var(--muted); }
.preview-body { padding: 16px; background: var(--hover); border-radius: var(--card-radius); margin-top: 12px; }
</style>
'''


def apply_replacements(rel_path: str, pairs: list[tuple[str, str]]) -> int:
    path = ROOT / rel_path
    text = path.read_text(encoding="utf-8")
    n = 0
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new)
            n += 1
    path.write_text(text, encoding="utf-8")
    return n


def main():
    total = 0
    for rel, pairs in REPLACEMENTS.items():
        total += apply_replacements(rel, pairs)
        print(f"patched {rel}: {len(pairs)} rules")

    (ROOT / "components/shared/Captcha.vue").write_text(CAPTCHA, encoding="utf-8")
    (ROOT / "components/ui/UiThemeBox.vue").write_text(UI_THEME, encoding="utf-8")
    (ROOT / "components/ui/UiNotificationBox.vue").write_text(UI_NOTIF, encoding="utf-8")
    (ROOT / "components/BulletinCreate.vue").write_text(BULLETIN_CREATE, encoding="utf-8")
    print("rewrote Captcha, UiThemeBox, UiNotificationBox, BulletinCreate")

    # HammerPanel partial fix via rewrite of known bad strings
    hp = ROOT / "components/shared/HammerPanel.vue"
    ht = hp.read_text(encoding="utf-8", errors="replace")
    fixes = [
        ("import { getUser } from '@/services/auth'", "import { getUser } from '@/services/auth'\nimport { useToast } from '@/composables/toast'"),
        ("?? ", "⚠️ "),
    ]
    for old, new in [
        ('placeholder="�����������..."', 'placeholder="描述你的问题..."'),
        ('>����</n-button>', '>发送</n-button>'),
        ("toast.info(`���ӻظ���${(last.content || '').slice(0, 40)}`",
         "toast.info(`锤子回复：${(last.content || '').slice(0, 40)}`"),
        ("message.error(e.response?.data?.msg || '������Ϣʧ��')", "message.error(e.response?.data?.msg || '加载消息失败')"),
        ("message.success('�ѷ���')", "message.success('已发送')"),
        ("message.error(e.response?.data?.msg || '����ʧ��')", "message.error(e.response?.data?.msg || '发送失败')"),
        ("{{ msg.is_staff ? '����' : (msg.nickname || 'ѡ��') }}", "{{ msg.is_staff ? '官方' : (msg.nickname || '选手') }}"),
    ]:
        if old in ht:
            ht = ht.replace(old, new)
    # Replace template blocks with clean Chinese if still garbled
    if "��" in ht or "??" in ht:
        ht = ht.replace(
            '<div v-if="disabled" class="hammer-disabled">\n      ?? ',
            '<div v-if="disabled" class="hammer-disabled">\n      ⚠️ ',
        )
        import re
        ht = re.sub(
            r'<div v-if="disabled" class="hammer-disabled">.*?</div>',
            '<div v-if="disabled" class="hammer-disabled">\n      ⚠️ 锤子服务在训练场中不可用，请通过赛事入口联系官方。\n    </div>',
            ht,
            count=1,
            flags=re.DOTALL,
        )
        ht = re.sub(
            r'<div class="hammer-hint">.*?</div>',
            '<div class="hammer-hint">\n        与官方/选手实时沟通，可直接索要 flag 提示或你卡住的步骤即可。\n      </div>',
            ht,
            count=1,
            flags=re.DOTALL,
        )
        ht = ht.replace(
            'class="empty">������Ϣ�����������ڴ�����</div>',
            'class="empty">暂无消息，发送问题后请耐心等待</div>',
        )
    hp.write_text(ht, encoding="utf-8")
    print("patched HammerPanel.vue")

    import re
    remaining = 0
    for p in ROOT.rglob("*.vue"):
        t = p.read_text(encoding="utf-8", errors="replace")
        remaining += len(re.findall(r"[^\w\?]\?\?[^\w\?]|'\?\?|>\?\?", t))
    print(f"approx remaining ?? UI patterns: {remaining}")


if __name__ == "__main__":
    main()
