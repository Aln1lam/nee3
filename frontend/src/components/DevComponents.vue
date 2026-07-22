<template>
  <MatrixShell
    prompt=""
    title="组件实验室"
    subtitle="DEV · UI KIT"
    page-prompt="组件演示 · DEV"
    page-title="UI 组件演示"
    page-desc="Task 03 UI 组件库 + Task 04 功能组件"
    :items="[{ code: 'UI', label: '组件演示', active: true }]"
  >
  <div class="dev-components">

    <section class="dev-section">
      <h2>Button / Tag / Link</h2>
      <div class="dev-row">
        <UiButton variant="primary">主色</UiButton>
        <UiButton variant="secondary">次要</UiButton>
        <UiButton variant="danger">危险</UiButton>
        <UiButton variant="ghost">Ghost</UiButton>
        <UiButton loading>Loading</UiButton>
      </div>
      <div class="dev-row">
        <UiTag>默认</UiTag>
        <UiTag type="success">成功</UiTag>
        <UiTag type="warning">警告</UiTag>
        <UiTag type="error">错误</UiTag>
        <UiTag type="info">信息</UiTag>
        <UiLink to="/">内部链接</UiLink>
        <UiLink to="https://www.neepu.edu.cn/" external>东北电力大学</UiLink>
      </div>
    </section>

    <section class="dev-section">
      <h2>Card / Input / Select</h2>
      <UiCard title="示例卡片">
        <UiInput v-model="demoInput" label="用户名" placeholder="如 8 字符" />
        <UiInput v-model="demoInput" label="带错误" error="格式不正确" style="margin-top:12px" />
        <UiSelect v-model="demoSelect" :options="selectOpts" label="分类" style="margin-top:12px" />
      </UiCard>
    </section>

    <section class="dev-section">
      <h2>Avatar / Divider / Timer</h2>
      <div class="dev-row">
        <UiAvatar name="Alice" />
        <UiAvatar name="Bob" size="large" />
        <UiDivider vertical style="height:40px" />
        <UiTimer :seconds="demoSeconds" label="测试倒计时" @finish="onTimerFinish" />
        <UiButton size="small" @click="demoSeconds = 10">重置 10s</UiButton>
      </div>
      <UiDivider />
      <UiTimeProgress permanent />
    </section>

    <section class="dev-section">
      <h2>Tabs / Splitter</h2>
      <UiTabs v-model="activeTab" :tabs="tabs" />
      <UiSplitter v-model:ratio="splitRatio" direction="vertical" style="height:240px;margin-top:12px">
        <template #first>
          <div class="split-pane">上半区{{ Math.round(splitRatio * 100) }}%</div>
        </template>
        <template #second>
          <div class="split-pane">下半区{{ Math.round((1 - splitRatio) * 100) }}%</div>
        </template>
      </UiSplitter>
    </section>

    <section class="dev-section">
      <h2>Popover / Picture</h2>
      <div class="dev-row">
        <UiPopover placement="bottom">
          <template #trigger>
            <UiButton variant="secondary">点击 Popover</UiButton>
          </template>
          <p style="margin:0;font-size: var(--text-sm)">移动端友好的弹出层封</p>
        </UiPopover>
        <UiAvatar name="Pic" />
        <UiPicture placeholder="?" alt="示例占位" />
      </div>
    </section>

    <section class="dev-section">
      <h2>Chart / LoadingTips</h2>
      <UiChart :option="chartOption" height="220px" />
      <UiLoadingTips />
    </section>

    <section class="dev-section">
      <h2>ThemeBox / NotificationBox</h2>
      <div class="dev-row">
                <UiNotificationBox />
        <UiButton @click="toast.info('这是一条 info 通知')">触发 Toast</UiButton>
        <UiButton @click="toast.confirm('确认执行操作？', { onAccept: () => toast.success('已确认') })">
          确认 Toast
        </UiButton>
      </div>
    </section>

    <section class="dev-section">
      <h2>Terminal（xterm.js + mock）</h2>
      <Terminal
        v-model="demoFlag"
        :mock-mode="true"
        title="NEEPU CTF 终端"
        @submit="onFlagSubmit"
      />
    </section>

    <section class="dev-section">
      <h2>Captcha</h2>
      <UiCard>
        <Captcha v-model="captchaAnswer" v-model:captcha-id="captchaId" />
        <p class="dev-meta">captcha_id: {{ captchaId || '—' }}</p>
      </UiCard>
    </section>

    <section class="dev-section">
      <h2>HammerPanel / InstanceBox</h2>
      <div class="dev-row">
        <InstanceBox />
      </div>
      <UiCard title="锤子（训练场 disabled）" style="margin-top:12px">
        <HammerPanel :challenge-id="1" disabled />
      </UiCard>
    </section>

    <section class="dev-section">
      <h2>ScoreboardChart</h2>
      <ScoreboardChart :series="scoreSeries" :organizations="['无组织', '网安学部']" height="240px" />
    </section>

    <section class="dev-section">
      <h2>Article（Markdown + TOC）</h2>
      <Article :content="sampleMd" show-toc />
    </section>

    <section class="dev-section">
      <h2>SidebarLayout</h2>
      <SidebarLayout title="示例外壳" :items="sidebarItems" :collapsible="true" max-width="960px">
        <UiCard>主内容区域，可在账号设置、做题页等场景复用。</UiCard>
      </SidebarLayout>
    </section>
  </div>
  </MatrixShell>
</template>

<script>
import { ref } from 'vue'
import {
  UiButton, UiCard, UiLink, UiInput, UiAvatar, UiTag, UiSelect,
  UiTabs, UiSplitter, UiTimer, UiTimeProgress, UiLoadingTips,
  UiChart, UiNotificationBox, UiDivider, UiPopover, UiPicture,
} from '@/components/ui'
import { Article, SidebarLayout, MatrixShell, Terminal, Captcha, HammerPanel, ScoreboardChart, InstanceBox } from '@/components/shared'
import { useToast } from '@/composables/toast'

export default {
  name: 'DevComponents',
  components: {
    UiButton, UiCard, UiLink, UiInput, UiAvatar, UiTag, UiSelect,
    UiTabs, UiSplitter, UiTimer, UiTimeProgress, UiLoadingTips,
    UiChart, UiNotificationBox, UiDivider, UiPopover, UiPicture,
    Article, SidebarLayout, MatrixShell, Terminal, Captcha, HammerPanel, ScoreboardChart, InstanceBox,
  },
  setup() {
    const toast = useToast()
    const demoInput = ref('')
    const demoSelect = ref(null)
    const demoSeconds = ref(30)
    const activeTab = ref('a')
    const splitRatio = ref(0.55)
    const demoFlag = ref('')
    const captchaAnswer = ref('')
    const captchaId = ref('')

    const selectOpts = [
      { label: 'Web', value: 'web' },
      { label: 'Pwn', value: 'pwn' },
      { label: 'Crypto', value: 'crypto' },
    ]

    const tabs = [
      { key: 'a', label: '终端' },
      { key: 'b', label: '提示' },
      { key: 'c', label: '锤子', disabled: true },
    ]

    const sidebarItems = [
      { label: '菜单 A', path: '/dev/components' },
      { label: '菜单 B', path: '/wiki' },
    ]

    const chartOption = {
      xAxis: { type: 'category', data: ['10:00', '11:00', '12:00', '13:00'] },
      yAxis: { type: 'value' },
      series: [{ type: 'line', smooth: true, data: [120, 200, 150, 320] }],
    }

    const scoreSeries = [
      { name: 'Team A', data: [['2026-07-10 10:00', 100], ['2026-07-10 11:00', 250], ['2026-07-10 12:00', 320]] },
      { name: 'Team B', data: [['2026-07-10 10:00', 80], ['2026-07-10 11:00', 180], ['2026-07-10 12:00', 290]] },
    ]

    const sampleMd = `## 连接器教程
NEEPU 在线环境题目启动后，直接使用公网 IP:端口 连接（顶栏「容器实例」可管理）。
### 代码示例

\`\`\`bash
nc host 1337
\`\`\`

### 公式

行内 $E=mc^2$ 与块级公式：

$$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$$

| 协议 | 端口 |
|------|------|
| tcp  | 1337 |
| http | 80   |
`

    function onTimerFinish() {
      toast.warning('倒计时结束')
    }

    function onFlagSubmit() {
      toast.info(`提交 flag: ${demoFlag.value || '(空)'}`)
    }

    return {
      toast, demoInput, demoSelect, demoSeconds, activeTab, splitRatio,
      demoFlag, captchaAnswer, captchaId, scoreSeries,
      selectOpts, tabs, sidebarItems, chartOption, sampleMd, onTimerFinish, onFlagSubmit,
    }
  },
}
</script>

<style scoped>
.dev-components {
  max-width: none;
  width: 100%;
  margin: 0;
  box-sizing: border-box;
}
.dev-hint { color: var(--muted); font-size: 14px; margin-bottom: 24px; }
.dev-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.dev-section h2 {
  font-size: 1rem;
  color: var(--primary);
  margin: 0 0 12px;
}
.dev-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.split-pane {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
  background: var(--hover);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--muted);
}
.dev-meta {
  margin: 8px 0 0;
  font-size: var(--text-xs);
  color: var(--muted);
  font-family: monospace;
}
</style>
