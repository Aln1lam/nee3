<template>
  <div class="error-page">
    <div class="error-shell">
      <article class="error-panel" :class="{ 'is-5xx': is5xx }">
        <div class="glow-orb" :class="{ 'is-5xx': is5xx }" aria-hidden="true"></div>

        <div class="error-eyebrow">
          <span class="link-code chip-cut">{{ chip }}</span>
          <span class="error-tag">{{ tag }}</span>
          <span class="error-status" :class="is5xx ? 'is-5xx' : 'is-4xx'">
            {{ is5xx ? '5xx · SERVER' : '4xx · CLIENT' }}
          </span>
        </div>

        <div class="error-code" :class="{ 'is-5xx': is5xx }">{{ displayCode }}</div>
        <h1 class="error-title">{{ title }}</h1>
        <p class="error-desc">{{ description }}</p>
        <p class="error-meta">NEEPU CTF · /error/{{ displayCode }}</p>

        <div class="error-actions">
          <button type="button" class="btn btn-primary" @click="goHome">
            回工作台
            <kbd>↵</kbd>
          </button>
          <button type="button" class="btn btn-ghost" @click="goBack">
            返回上一页
          </button>
        </div>

        <div class="error-foot">
          <span>© 2022-2026 东北电力大学</span>
          <a href="https://www.neepu.edu.cn/" target="_blank" rel="noopener">neepu.edu.cn</a>
        </div>
      </article>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const PAGES = {
  '400': { chip: 'BAD', tag: 'BAD REQUEST', title: '请求无效', desc: '提交的参数有点问题，检查一下再试。', family: '4xx' },
  '401': { chip: 'AUTH', tag: 'UNAUTHORIZED', title: '需要登录', desc: '先登录，再访问这个页面。', family: '4xx' },
  '403': { chip: 'DENY', tag: 'FORBIDDEN', title: '权限不足', desc: '你没有访问这里的权限，如需开通请联系管理员。', family: '4xx' },
  '404': { chip: 'MISS', tag: 'NOT FOUND', title: '页面不存在', desc: '链接可能写错了，或页面已经被移走。', family: '4xx' },
  '408': { chip: 'WAIT', tag: 'TIMEOUT', title: '请求超时', desc: '等太久了，刷新一下或稍后再试。', family: '4xx' },
  '412': { chip: 'PRE', tag: 'PRECONDITION', title: '前置条件失败', desc: '请求未满足服务器前置条件，请检查后再试。', family: '4xx' },
  '418': { chip: 'TEA', tag: "I'M A TEAPOT", title: '我是茶壶', desc: '不能冲咖啡哦 —— RFC 2324 彩蛋。', family: '4xx' },
  '429': { chip: 'RATE', tag: 'TOO MANY', title: '请求太频繁', desc: '稍微歇一会儿，再继续操作。', family: '4xx' },
  '500': { chip: 'FAIL', tag: 'SERVER ERROR', title: '服务器开小差了', desc: '我们这边出了点问题，稍后再试一次。', family: '5xx' },
  '502': { chip: 'GATE', tag: 'BAD GATEWAY', title: '网关异常', desc: '上游服务暂时连不上，请稍候再试。', family: '5xx' },
  '503': { chip: 'DOWN', tag: 'UNAVAILABLE', title: '服务暂不可用', desc: '平台维护或过载中，请稍后再来。', family: '5xx' },
  '504': { chip: 'SLOW', tag: 'GATEWAY TIMEOUT', title: '网关超时', desc: '上游响应太慢，过一会儿再试。', family: '5xx' },
  unknown: { chip: 'ERR', tag: 'UNKNOWN', title: '出错了', desc: '发生了未知错误，请返回后重试。', family: '4xx' },
}

export default {
  name: 'ErrorPage',
  props: {
    code: { type: [String, Number], default: '' },
  },
  setup(props) {
    const route = useRoute()
    const router = useRouter()

    const displayCode = computed(() => {
      const raw = props.code || route.params.code || 'unknown'
      return String(raw)
    })

    const info = computed(() => PAGES[displayCode.value] || PAGES.unknown)
    const title = computed(() => info.value.title)
    const description = computed(() => info.value.desc)
    const chip = computed(() => info.value.chip)
    const tag = computed(() => info.value.tag)
    const is5xx = computed(() => info.value.family === '5xx' || /^5\d{2}$/.test(displayCode.value))

    function goHome() {
      router.push('/home')
    }

    function goBack() {
      if (window.history.length > 1) router.back()
      else router.push('/')
    }

    return { displayCode, title, description, chip, tag, is5xx, goHome, goBack }
  },
}
</script>

<style scoped>
.error-page {
  min-height: calc(100vh - var(--nav-height, 72px));
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px 48px;
  font-family: var(--font-ui);
  background:
    radial-gradient(ellipse 70% 50% at 12% 18%, rgba(var(--primary-rgb, 94, 217, 168), 0.07), transparent 55%),
    radial-gradient(ellipse 50% 40% at 88% 82%, rgba(var(--primary-rgb, 94, 217, 168), 0.03), transparent 50%);
}

.error-shell {
  width: min(560px, 100%);
  position: relative;
}

.error-panel {
  position: relative;
  padding: 36px 32px 32px;
  border-radius: var(--card-radius, 10px);
  background: rgba(19, 23, 34, 0.72);
  border: 1px solid rgba(var(--primary-rgb, 94, 217, 168), 0.18);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  overflow: hidden;
}

.error-panel::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 2px;
  background: linear-gradient(
    180deg,
    transparent,
    rgba(var(--primary-rgb, 94, 217, 168), 0.55) 30%,
    rgba(var(--primary-rgb, 94, 217, 168), 0.55) 70%,
    transparent
  );
  opacity: 0.7;
  pointer-events: none;
}

.error-panel.is-5xx {
  border-color: rgba(248, 113, 113, 0.22);
}

.error-panel.is-5xx::before {
  background: linear-gradient(
    180deg,
    transparent,
    rgba(248, 113, 113, 0.5) 30%,
    rgba(248, 113, 113, 0.5) 70%,
    transparent
  );
}

.glow-orb {
  position: absolute;
  width: 220px;
  height: 220px;
  right: -60px;
  top: -80px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(var(--primary-rgb, 94, 217, 168), 0.14), transparent 70%);
  pointer-events: none;
}

.glow-orb.is-5xx {
  background: radial-gradient(circle, rgba(248, 113, 113, 0.12), transparent 70%);
}

.error-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
}

.error-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.14em;
  color: rgba(229, 231, 235, 0.5);
  text-transform: uppercase;
}

.error-status {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted, #9ca3af);
}

.error-status.is-4xx {
  color: var(--primary, #5ED9A8);
}

.error-status.is-5xx {
  color: #f87171;
}

.error-code {
  font-family: var(--font-mono);
  font-size: clamp(4.5rem, 14vw, 6.5rem);
  font-weight: 700;
  line-height: 0.92;
  letter-spacing: -0.04em;
  color: var(--primary, #5ED9A8);
  opacity: 0.92;
  margin: 0 0 14px;
}

.error-code.is-5xx {
  color: #fca5a5;
  opacity: 0.88;
}

.error-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: #f4f7fb;
  letter-spacing: 0.01em;
  font-family: var(--font-ui);
}

.error-desc {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text, #e5e7eb);
  max-width: 42ch;
}

.error-meta {
  margin-top: 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted, #9ca3af);
  letter-spacing: 0.02em;
}

.error-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}

.btn {
  appearance: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 42px;
  padding: 0 18px;
  border-radius: 8px;
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.btn-primary {
  background: #10b981;
  color: #0a0f14;
  border: 1px solid transparent;
}

.btn-primary:hover {
  background: #34d399;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.28);
}

.btn-ghost {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text, #e5e7eb);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.btn-ghost:hover {
  border-color: rgba(var(--primary-rgb, 94, 217, 168), 0.4);
  background: rgba(var(--primary-rgb, 94, 217, 168), 0.08);
}

.btn kbd {
  font-family: var(--font-mono);
  font-size: 11px;
  opacity: 0.75;
  font-weight: 500;
}

.error-foot {
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: var(--muted, #9ca3af);
}

.error-foot a {
  color: var(--primary, #5ED9A8);
  text-decoration: none;
}

.error-foot a:hover {
  text-decoration: underline;
}

@media (max-width: 640px) {
  .error-panel {
    padding: 28px 20px 24px;
  }
  .error-foot {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
