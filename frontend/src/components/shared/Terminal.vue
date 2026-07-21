<template>
  <div class="challenge-terminal">
    <div class="term-header">
      <span class="term-dot red"></span>
      <span class="term-dot yellow"></span>
      <span class="term-dot green"></span>
      <span class="term-title">{{ title }}</span>
      <span v-if="showXterm" class="term-status">{{ mockMode ? 'Flag 提交 · 装饰终端' : 'Flag 提交' }}</span>
    </div>

    <div v-if="showXterm" ref="termRef" class="challenge-terminal__xterm" />

    <div class="term-hint">
      <template v-if="mockMode">本面板为装饰终端（非真实 Shell），仅用于粘贴提交 Flag。</template>
      容器/TCP 题目请使用题目页「在线环境」给出的公网地址（nc / 浏览器），勿在此面板内期望交互式 Shell。
      快捷键：Ctrl+Shift+V 粘贴后回车提交。
    </div>

    <div class="flag-bar">
      <n-input
        v-model:value="localFlag"
        placeholder="flag{...}"
        :disabled="disabled || loading"
        @keydown.enter="onSubmit"
      />
      <n-button
        type="primary"
        :loading="loading"
        :disabled="disabled"
        @click="onSubmit"
      >{{ disabled ? '已解锁' : '提交' }}</n-button>
    </div>

    <div v-if="lastResult" class="term-output" :class="lastResult.ok ? 'ok' : 'err'">
      {{ lastResult.msg }}
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { NInput, NButton } from 'naive-ui'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import { CanvasAddon } from '@xterm/addon-canvas'
import '@xterm/xterm/css/xterm.css'

export default {
  name: 'ChallengeTerminal',
  components: { NInput, NButton },
  props: {
    modelValue: { type: String, default: '' },
    loading: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
    result: { type: Object, default: null },
    mockMode: { type: Boolean, default: true },
    title: { type: String, default: 'NEEPU CTF 终端' },
  },
  emits: ['update:modelValue', 'submit'],
  setup(props, { emit }) {
    const termRef = ref(null)
    const localFlag = ref(props.modelValue)
    const lastResult = ref(null)

    let term = null
    let fitAddon = null
    let ro = null
    let mockTimer = null

    const showXterm = computed(() => props.mockMode !== false)

    watch(() => props.modelValue, v => { localFlag.value = v })
    watch(localFlag, v => emit('update:modelValue', v))
    watch(() => props.result, v => { if (v) lastResult.value = v }, { deep: true })

    function onSubmit() {
      if (props.disabled || props.loading) return
      emit('submit')
    }

    function writeln(text) {
      term?.writeln(text)
    }

    function initTerm() {
      if (!termRef.value || term) return
      term = new Terminal({
        cursorBlink: true,
        fontSize: 13,
        fontFamily: "var(--font-mono)",
        theme: {
          background: '#0d1117',
          foreground: '#58a6ff',
          cursor: '#58a6ff',
        },
        scrollback: 2000,
      })
      fitAddon = new FitAddon()
      term.loadAddon(fitAddon)
      term.loadAddon(new WebLinksAddon())
      term.loadAddon(new CanvasAddon())
      term.open(termRef.value)
      fitAddon.fit()
      term.writeln('\x1b[32m[*]\x1b[0m 在题目页启动环境后，使用公网 IP:端口 连接')
    }

    function startMock() {
      stopMock()
      if (!term) return
      const lines = [
        '\x1b[36m[info]\x1b[0m Web 题：浏览器打开 http://公网IP:端口',
        '\x1b[36m[info]\x1b[0m Pwn/Misc：nc 公网IP 端口',
        '\x1b[32m[info]\x1b[0m 获取 flag 后在下方输入框提交',
      ]
      let i = 0
      mockTimer = setInterval(() => {
        if (i < lines.length) {
          writeln(lines[i++])
        } else {
          stopMock()
        }
      }, 600)
    }

    function stopMock() {
      if (mockTimer) {
        clearInterval(mockTimer)
        mockTimer = null
      }
    }

    function bindResize() {
      if (!termRef.value || !fitAddon) return
      ro = new ResizeObserver(() => {
        try { fitAddon.fit() } catch { /* ignore */ }
      })
      ro.observe(termRef.value)
    }

    async function setupTerminal() {
      if (!showXterm.value) return
      await nextTick()
      initTerm()
      bindResize()
      startMock()
    }

    watch(showXterm, async (v) => {
      if (v) await setupTerminal()
      else disposeTerm()
    })

    function disposeTerm() {
      stopMock()
      ro?.disconnect()
      ro = null
      term?.dispose()
      term = null
      fitAddon = null
    }

    onMounted(setupTerminal)
    onUnmounted(disposeTerm)

    return {
      termRef, localFlag, lastResult, showXterm, onSubmit,
    }
  },
}
</script>

<style scoped>
.challenge-terminal {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--term-bg, #0d1117);
  font-family: var(--font-hacker);
}
.term-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.term-dot { width: 10px; height: 10px; border-radius: 50%; }
.term-dot.red { background: #ff5f57; }
.term-dot.yellow { background: #febc2e; }
.term-dot.green { background: #28c840; }
.term-title {
  margin-left: 8px;
  font-size: var(--text-xs);
  color: var(--muted);
  flex: 1;
}
.term-status { font-size: 11px; color: var(--muted); }
.challenge-terminal__xterm {
  height: 220px;
  padding: 4px 8px;
}
.term-hint {
  font-size: 11px;
  color: var(--muted);
  padding: 8px 12px 0;
  opacity: 0.85;
}
.flag-bar {
  display: flex;
  gap: 8px;
  padding: 10px 12px 12px;
}
.flag-bar :deep(.n-input) { flex: 1; }
.flag-bar :deep(.n-input .n-input__input-el) {
  background: rgba(0, 0, 0, 0.3) !important;
  color: var(--term-fg, #58a6ff) !important;
  font-family: inherit;
}
.term-output {
  padding: 0 12px 12px;
  font-size: var(--text-sm);
}
.term-output.ok { color: var(--success, #51cf66); }
.term-output.err { color: var(--accent-red, #f83030); }
</style>
