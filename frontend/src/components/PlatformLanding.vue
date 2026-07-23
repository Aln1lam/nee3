<template>
  <div
    class="cover-landing"
    :class="{ 'is-ready': ready }"
    @pointermove="onPointer"
  >
    <div class="cover-landing__grid" aria-hidden="true" />
    <div
      class="cover-landing__glow cover-landing__glow--a"
      :style="glowStyle"
      aria-hidden="true"
    />
    <div class="cover-landing__glow cover-landing__glow--b" aria-hidden="true" />
    <div class="cover-landing__scan" aria-hidden="true" />

    <div class="cover-landing__frame" aria-hidden="true">
      <span class="cover-landing__corner cover-landing__corner--tl" />
      <span class="cover-landing__corner cover-landing__corner--tr" />
      <span class="cover-landing__corner cover-landing__corner--bl" />
      <span class="cover-landing__corner cover-landing__corner--br" />
      <span class="cover-landing__edge cover-landing__edge--top" />
      <span class="cover-landing__edge cover-landing__edge--bottom" />
    </div>

    <div class="cover-landing__stage">
      <div class="cover-landing__status cover-landing__reveal" style="--d: 0ms">
        <span class="cover-landing__chip">
          <span class="cover-landing__pulse" aria-hidden="true" />
          SYS · ONLINE
        </span>
        <span class="cover-landing__chip cover-landing__chip--muted">v{{ versionLabel }}</span>
      </div>

      <header class="cover-landing__hero cover-landing__reveal" style="--d: 60ms">
        <p class="cover-landing__eyebrow">
          <span class="cover-landing__code">CTF</span>
          RANGE · PRACTICE · CONTESTS
        </p>
        <h1
          class="cover-landing__title"
          :class="{ 'is-flicker': titleFlickering, 'is-blackout': titleBlackout }"
        >
          <span class="cover-landing__bracket">[</span>
          <span class="cover-landing__name">{{ displayTitle }}</span>
          <span class="cover-landing__bracket">]</span>
          <span class="cover-landing__cursor" aria-hidden="true">_</span>
        </h1>

        <!-- Hello-CTF style scramble tagline -->
        <div class="cover-landing__tagline" aria-live="polite">
          <span ref="taglineEl" class="cover-landing__tagline-text" />
        </div>

        <p class="cover-landing__desc">
          致力于打造开放、实战、可持续进化的 CTF 靶场与竞赛平台
        </p>
      </header>

      <div class="cover-landing__actions cover-landing__reveal" style="--d: 120ms">
        <button type="button" class="cover-landing__btn cover-landing__btn--primary" @click="enterTerminal">
          <span class="cover-landing__btn-code">ENT</span>
          <span>进入终端</span>
          <span class="cover-landing__btn-arrow">↗</span>
        </button>
        <button type="button" class="cover-landing__btn cover-landing__btn--ghost" @click="goTraining">
          <span class="cover-landing__btn-code">TRN</span>
          <span>演练靶场</span>
        </button>
      </div>

      <ul class="cover-landing__modules cover-landing__reveal" style="--d: 180ms" aria-label="平台模块">
        <li v-for="(mod, i) in modules" :key="mod.code" :style="{ '--i': i }">
          <button type="button" class="cover-landing__mod" @click="mod.go()">
            <span class="cover-landing__mod-top">
              <span class="cover-landing__mod-code">{{ mod.code }}</span>
              <span class="cover-landing__mod-go" aria-hidden="true">↗</span>
            </span>
            <span class="cover-landing__mod-label">{{ mod.label }}</span>
            <span class="cover-landing__mod-hint">{{ mod.hint }}</span>
          </button>
        </li>
      </ul>
    </div>

    <footer class="cover-landing__footer">
      <span>(C) {{ footerYears }} </span>
      <a :href="footerUrl" target="_blank" rel="noopener">{{ footerOrg }}</a>
      <template v-if="footerIcp">
        <span> · </span>
        <a :href="footerIcpUrl" target="_blank" rel="noopener">{{ footerIcp }}</a>
      </template>
    </footer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'
import { fetchPlatformVersion } from '@/services/platform'
import { getUser } from '@/services/auth'

defineOptions({ name: 'PlatformLanding' })

const PHRASES = [
  '/ Loading CTF range...',
  '/ System ready.',
  '/ Waiting for first blood...',
  '/ pwn · web · crypto · reverse',
  '/ nc range.neepu 1337',
  '/ flag{welcome_hacker}',
  '/ Read · Solve · Submit',
  '/ May the flag be with you.',
  '/ Access granted.',
  '/ 3',
  '/ 2',
  '/ 1',
  '/ BOOM!',
]

const SCRAMBLE_CHARS = '!<>-_\\/[]{}—=+*^?#_'

class TextScramble {
  constructor(el) {
    this.el = el
    this.queue = []
    this.frame = 0
    this.frameRequest = 0
    this.resolve = null
    this._lastHtml = ''
    this.update = this.update.bind(this)
  }

  setText(newText) {
    const oldText = this.el.innerText || ''
    const length = Math.max(oldText.length, newText.length)
    const promise = new Promise((resolve) => {
      this.resolve = resolve
    })
    this.queue = []
    for (let i = 0; i < length; i += 1) {
      const from = oldText[i] || ''
      const to = newText[i] || ''
      const start = Math.floor(Math.random() * 40)
      const end = start + Math.floor(Math.random() * 40)
      this.queue.push({ from, to, start, end, char: '' })
    }
    cancelAnimationFrame(this.frameRequest)
    this.frame = 0
    this._lastHtml = ''
    this.update()
    return promise
  }

  update() {
    if (typeof document !== 'undefined' && document.hidden) {
      this.frameRequest = requestAnimationFrame(this.update)
      return
    }
    const parts = []
    let complete = 0
    const { queue, frame } = this
    for (let i = 0; i < queue.length; i += 1) {
      const item = queue[i]
      const { from, to, start, end } = item
      if (frame >= end) {
        complete += 1
        parts.push(escapeHtml(to))
      } else if (frame >= start) {
        if (!item.char || Math.random() < 0.28) {
          item.char = SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)]
        }
        parts.push(`<span class="scramble-char">${escapeHtml(item.char)}</span>`)
      } else {
        parts.push(escapeHtml(from))
      }
    }
    const output = parts.join('')
    if (output !== this._lastHtml) {
      this.el.innerHTML = output
      this._lastHtml = output
    }
    if (complete === queue.length) {
      this.resolve?.()
    } else {
      this.frameRequest = requestAnimationFrame(this.update)
      this.frame += 1
    }
  }

  destroy() {
    cancelAnimationFrame(this.frameRequest)
  }
}

function escapeHtml(ch) {
  if (ch === '&') return '&amp;'
  if (ch === '<') return '&lt;'
  if (ch === '>') return '&gt;'
  if (ch === '"') return '&quot;'
  return ch
}

const router = useRouter()
const { platform, loadPlatform } = usePlatformStore()
const versionLabel = ref('—')
const ready = ref(false)
const taglineEl = ref(null)
const phraseIndex = ref(0)
const pointer = reactive({ x: 0, y: 0 })

let scramble = null
let taglineTimer = 0
let taglineStopped = false

const TITLE_STABLE = 'NEEPU CTF'
const TITLE_SEEDS = ['NEEPU CTF', 'neepu', 'CTF', 'neepuctf', 'NEEPU', 'ctf']

/** leetspeak / glyph substitutes for power-glitch frames */
const GLITCH_MAP = {
  a: ['a', 'A', '4', '@'],
  e: ['e', 'E', '3'],
  i: ['i', 'I', '1', '!'],
  o: ['o', 'O', '0'],
  u: ['u', 'U'],
  n: ['n', 'N'],
  p: ['p', 'P'],
  c: ['c', 'C'],
  t: ['t', 'T', '7'],
  f: ['f', 'F'],
  ' ': [' ', '_', '-', ''],
}

const displayTitle = ref(TITLE_STABLE)
const titleFlickering = ref(false)
const titleBlackout = ref(false)

let flickerTimer = 0
let flickerSeqTimer = 0

function clearFlickerTimers() {
  window.clearTimeout(flickerTimer)
  window.clearTimeout(flickerSeqTimer)
}

function scheduleNextFlicker() {
  const wait = 2800 + Math.random() * 4200
  flickerTimer = window.setTimeout(() => {
    runPowerFlicker()
  }, wait)
}

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function mutateCase(text) {
  const mode = Math.random()
  if (mode < 0.25) return text.toLowerCase()
  if (mode < 0.45) return text.toUpperCase()
  // mixed / random case
  return [...text].map((ch) => {
    if (!/[a-z]/i.test(ch)) return ch
    return Math.random() > 0.5 ? ch.toUpperCase() : ch.toLowerCase()
  }).join('')
}

function mutateGlyphs(text, intensity = 0.35) {
  return [...text].map((ch) => {
    const key = ch.toLowerCase()
    const options = GLITCH_MAP[key]
    if (!options || Math.random() > intensity) {
      return Math.random() > 0.55 ? ch.toUpperCase() : ch.toLowerCase()
    }
    return pick(options)
  }).join('')
}

/** Build one diverse glitch frame from seeds */
function makeGlitchTitle() {
  const seed = pick(TITLE_SEEDS)
  const roll = Math.random()
  if (roll < 0.22) return mutateCase(seed)
  if (roll < 0.55) return mutateGlyphs(seed, 0.25 + Math.random() * 0.35)
  if (roll < 0.78) return mutateGlyphs(mutateCase(seed), 0.4 + Math.random() * 0.35)
  // heavier corruption: drop / duplicate a char
  let s = mutateGlyphs(seed, 0.55)
  if (Math.random() > 0.5 && s.length > 3) {
    const i = Math.floor(Math.random() * s.length)
    s = s.slice(0, i) + s.slice(i + 1)
  } else if (s.length < 14) {
    const i = Math.floor(Math.random() * s.length)
    s = s.slice(0, i) + s[i] + s.slice(i)
  }
  return s || seed
}

function runPowerFlicker() {
  clearFlickerTimers()
  titleFlickering.value = true

  const frames = 2 + (Math.random() > 0.4 ? 1 : 0)
  const burst = []
  burst.push({ text: '', blackout: true, ms: 40 + Math.random() * 50 })
  for (let f = 0; f < frames; f += 1) {
    burst.push({ text: makeGlitchTitle(), blackout: false, ms: 560 + Math.random() * 120 })
    if (f < frames - 1) {
      burst.push({ text: '', blackout: true, ms: 25 + Math.random() * 40 })
    }
  }
  burst.push({ text: '', blackout: true, ms: 35 + Math.random() * 45 })
  burst.push({ text: TITLE_STABLE, blackout: false, ms: 0 })

  let i = 0
  const step = () => {
    if (i >= burst.length) {
      titleFlickering.value = false
      titleBlackout.value = false
      displayTitle.value = TITLE_STABLE
      scheduleNextFlicker()
      return
    }
    const frame = burst[i]
    i += 1
    displayTitle.value = frame.text
    titleBlackout.value = !!frame.blackout
    if (frame.ms <= 0) {
      titleFlickering.value = false
      titleBlackout.value = false
      displayTitle.value = TITLE_STABLE
      scheduleNextFlicker()
      return
    }
    flickerSeqTimer = window.setTimeout(step, frame.ms)
  }
  step()
}
const footerOrg = computed(() => platform.value.footer?.org_name || '东北电力大学')
const footerUrl = computed(() => platform.value.footer?.org_url || 'https://www.neepu.edu.cn/')
const footerYears = computed(() =>
  platform.value.footer?.copyright_years || `2022-${new Date().getFullYear()}`
)
const footerIcp = computed(() => platform.value.footer?.icp || '')
const footerIcpUrl = computed(() => platform.value.footer?.icp_url || 'https://beian.miit.gov.cn/')
const glowStyle = computed(() => ({
  '--px': `${pointer.x * 14}px`,
  '--py': `${pointer.y * 10}px`,
}))

const modules = [
  { code: 'TRN', label: '训练靶场', hint: 'Practice', go: () => router.push('/training') },
  { code: 'CTF', label: '赛事中心', hint: 'Contests', go: () => router.push('/contests') },
  { code: 'WKI', label: '知识库', hint: 'Wiki', go: () => router.push('/wiki') },
  { code: 'BUL', label: '平台公告', hint: 'Bulletin', go: () => router.push('/bulletin') },
]

function onPointer(e) {
  const el = e.currentTarget
  const rect = el.getBoundingClientRect()
  pointer.x = ((e.clientX - rect.left) / rect.width - 0.5) * 2
  pointer.y = ((e.clientY - rect.top) / rect.height - 0.5) * 2
}

function enterTerminal() {
  const user = getUser()
  router.push(user ? '/home' : '/auth')
}

function goTraining() {
  router.push('/training')
}

function startTaglineLoop() {
  if (!taglineEl.value || taglineStopped) return
  scramble = new TextScramble(taglineEl.value)
  const next = () => {
    if (taglineStopped || !scramble) return
    const idx = phraseIndex.value
    const text = PHRASES[idx]
    scramble.setText(text).then(() => {
      if (taglineStopped) return
      const hold = idx === PHRASES.length - 1 ? 3600 : 1800
      taglineTimer = window.setTimeout(() => {
        phraseIndex.value = (idx + 1) % PHRASES.length
        next()
      }, hold)
    })
  }
  next()
}

onMounted(async () => {
  requestAnimationFrame(() => {
    ready.value = true
  })
  await nextTick()
  startTaglineLoop()
  scheduleNextFlicker()

  const info = await loadPlatform()
  const ver = await fetchPlatformVersion()
  versionLabel.value = ver?.version || ver?.data?.version || '1.0'
  if (info?.zen_game) {
    router.replace(`/games/${info.zen_game}`)
  }
})

onUnmounted(() => {
  taglineStopped = true
  window.clearTimeout(taglineTimer)
  clearFlickerTimers()
  scramble?.destroy()
  scramble = null
})
</script>

<style scoped>
.cover-landing {
  --cover-mint: #5ed9a8;
  --cover-mint-deep: #10b981;
  --cover-ink: #0b0e14;
  --cover-text: #e5e7eb;
  --cover-muted: #9ca3af;
  --cover-glass: rgba(18, 22, 32, 0.7);

  position: relative;
  width: 100%;
  min-height: calc(100vh - var(--nav-height, 72px));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px 20px 56px;
  box-sizing: border-box;
  overflow: hidden;
  background: var(--cover-ink);
  color: var(--cover-text);
  font-family: var(--font-ui);
  isolation: isolate;
}

.cover-landing__grid {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(94, 217, 168, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(94, 217, 168, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 72% 62% at 50% 44%, #000 18%, transparent 78%);
  -webkit-mask-image: radial-gradient(ellipse 72% 62% at 50% 44%, #000 18%, transparent 78%);
  animation: cover-grid-breathe 9s ease-in-out infinite;
}

.cover-landing__glow {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  filter: blur(88px);
}

.cover-landing__glow--a {
  width: min(560px, 70vw);
  height: min(560px, 70vw);
  left: 50%;
  top: 42%;
  transform: translate(calc(-50% + var(--px, 0px)), calc(-50% + var(--py, 0px)));
  background: radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.05) 45%, transparent 70%);
  opacity: 0.65;
  transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.cover-landing__glow--b {
  width: min(320px, 46vw);
  height: min(320px, 46vw);
  right: 6%;
  bottom: 10%;
  background: radial-gradient(circle, rgba(94, 217, 168, 0.1) 0%, transparent 65%);
  opacity: 0.4;
  animation: cover-drift-b 16s ease-in-out infinite;
}

.cover-landing__scan {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(180deg, transparent 0%, rgba(94, 217, 168, 0.018) 50%, transparent 100%);
  background-size: 100% 180%;
  animation: cover-scan 11s linear infinite;
  opacity: 0.65;
}

@keyframes cover-grid-breathe {
  0%, 100% { opacity: 0.85; }
  50% { opacity: 1; }
}

@keyframes cover-drift-b {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-14px, -18px); }
}

@keyframes cover-scan {
  0% { background-position: 0 0; }
  100% { background-position: 0 100%; }
}

.cover-landing__frame {
  position: absolute;
  inset: 18px 22px 40px;
  z-index: 1;
  pointer-events: none;
  max-width: 980px;
  margin: 0 auto;
  left: 0;
  right: 0;
}

.cover-landing__corner {
  position: absolute;
  width: 16px;
  height: 16px;
  border-color: rgba(94, 217, 168, 0.45);
  border-style: solid;
  border-width: 0;
}

.cover-landing.is-ready .cover-landing__corner {
  animation: cover-corner-flash 3s ease-in-out infinite;
}

.cover-landing__corner--tl { top: 0; left: 0; border-top-width: 1px; border-left-width: 1px; }
.cover-landing__corner--tr { top: 0; right: 0; border-top-width: 1px; border-right-width: 1px; animation-delay: 0.4s; }
.cover-landing__corner--bl { bottom: 0; left: 0; border-bottom-width: 1px; border-left-width: 1px; animation-delay: 0.8s; }
.cover-landing__corner--br { bottom: 0; right: 0; border-bottom-width: 1px; border-right-width: 1px; animation-delay: 1.2s; }

@keyframes cover-corner-flash {
  0%, 100% { border-color: rgba(94, 217, 168, 0.3); }
  50% { border-color: rgba(94, 217, 168, 0.65); }
}

.cover-landing__edge {
  position: absolute;
  left: 36px;
  right: 36px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(94, 217, 168, 0.22) 20%, rgba(94, 217, 168, 0.22) 80%, transparent);
}

.cover-landing__edge--top { top: 0; }
.cover-landing__edge--bottom { bottom: 0; }

.cover-landing__stage {
  position: relative;
  z-index: 2;
  width: min(100%, 820px);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 22px;
}

.cover-landing__reveal {
  opacity: 0;
  transform: translateY(14px);
  transition: opacity 0.65s cubic-bezier(0.22, 1, 0.36, 1), transform 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: var(--d, 0ms);
}

.cover-landing.is-ready .cover-landing__reveal {
  opacity: 1;
  transform: translateY(0);
}

.cover-landing__status {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.cover-landing__chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 26px;
  padding: 0 11px;
  border-radius: 999px;
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 11px;
  letter-spacing: 0.06em;
  color: var(--cover-mint);
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  backdrop-filter: blur(10px);
}

.cover-landing__chip--muted {
  color: var(--cover-muted);
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

.cover-landing__pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cover-mint-deep);
  animation: cover-pulse 2.2s ease-out infinite;
}

@keyframes cover-pulse {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.45); }
  70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.cover-landing__hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.cover-landing__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--cover-muted);
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
}

.cover-landing__code {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #0a0f14;
  background: var(--cover-mint);
}

.cover-landing__title {
  margin: 0;
  display: flex;
  align-items: baseline;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
  min-height: 1.2em;
  font-size: clamp(28px, 4.6vw, 42px);
  line-height: 1.15;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: var(--cover-text);
  transition: opacity 0.05s linear, filter 0.05s linear;
}

.cover-landing__title.is-flicker .cover-landing__name {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  letter-spacing: 0.04em;
  color: var(--cover-mint);
}

.cover-landing__title.is-blackout {
  opacity: 0.08;
  filter: brightness(0.35);
}

.cover-landing__title.is-flicker:not(.is-blackout) {
  animation: cover-power-jitter 0.12s steps(2, end) infinite;
}

@keyframes cover-power-jitter {
  0% { transform: translate(0, 0); opacity: 1; }
  25% { transform: translate(-1px, 0.5px); opacity: 0.75; }
  50% { transform: translate(1px, -0.5px); opacity: 1; }
  75% { transform: translate(0.5px, 1px); opacity: 0.55; }
  100% { transform: translate(0, 0); opacity: 0.9; }
}

.cover-landing__name {
  display: inline-block;
  min-width: 9ch;
  text-align: center;
}

.cover-landing__bracket {
  color: rgba(94, 217, 168, 0.65);
  font-weight: 500;
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
}

.cover-landing__cursor {
  display: inline-block;
  margin-left: 2px;
  color: var(--cover-mint);
  font-weight: 700;
  animation: cover-blink 1s step-end infinite;
}

@keyframes cover-blink {
  50% { opacity: 0; }
}

.cover-landing__tagline {
  margin: 2px 0 0;
  min-height: 1.75rem;
  padding: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: clamp(14px, 2vw, 17px);
  line-height: 1.5;
  color: var(--cover-mint);
  cursor: default;
  pointer-events: none;
  letter-spacing: 0.01em;
  transition: color 0.2s ease;
}

.cover-landing__tagline-text :deep(.scramble-char) {
  opacity: 0.85;
}

.cover-landing__desc {
  margin: 0;
  max-width: 34em;
  font-size: 13px;
  line-height: 1.7;
  color: var(--cover-muted);
}

.cover-landing__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  width: 100%;
}

.cover-landing__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-width: 156px;
  height: 44px;
  padding: 0 18px;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-ui);
  cursor: pointer;
  transition:
    transform 0.25s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.25s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    color 0.2s ease;
}

.cover-landing__btn-code {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  opacity: 0.75;
}

.cover-landing__btn-arrow {
  font-size: 13px;
  opacity: 0.7;
  transition: transform 0.25s ease, opacity 0.2s ease;
}

.cover-landing__btn--primary {
  color: #0a0f14;
  background: linear-gradient(180deg, #34d399 0%, #10b981 100%);
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.18);
}

.cover-landing__btn--primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(16, 185, 129, 0.32);
}

.cover-landing__btn--primary:hover .cover-landing__btn-arrow {
  transform: translate(2px, -2px);
  opacity: 1;
}

.cover-landing__btn--ghost {
  color: var(--cover-text);
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
}

.cover-landing__btn--ghost:hover {
  transform: translateY(-3px);
  color: var(--cover-mint);
  border-color: rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.07);
  box-shadow: 0 8px 22px rgba(16, 185, 129, 0.16);
}

.cover-landing__btn--ghost .cover-landing__btn-code {
  color: var(--cover-mint);
  opacity: 0.9;
}

.cover-landing__modules {
  list-style: none;
  margin: 4px 0 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.cover-landing__modules > li {
  opacity: 0;
  transform: translateY(10px);
}

.cover-landing.is-ready .cover-landing__modules > li {
  animation: cover-mod-in 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(220ms + var(--i) * 60ms);
}

@keyframes cover-mod-in {
  to { opacity: 1; transform: translateY(0); }
}

.cover-landing__mod {
  width: 100%;
  min-height: 92px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 14px 14px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  background: var(--cover-glass);
  backdrop-filter: blur(12px);
  color: inherit;
  cursor: pointer;
  text-align: left;
  transition:
    transform 0.25s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.25s ease;
}

.cover-landing__mod-top {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cover-landing__mod-go {
  font-size: 12px;
  color: var(--cover-muted);
  opacity: 0;
  transform: translate(-3px, 3px);
  transition: opacity 0.2s ease, transform 0.25s ease, color 0.2s ease;
}

.cover-landing__mod:hover {
  transform: translateY(-4px);
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.07);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25), 0 0 18px rgba(16, 185, 129, 0.12);
}

.cover-landing__mod:hover .cover-landing__mod-go {
  opacity: 1;
  color: var(--cover-mint);
  transform: translate(0, 0);
}

.cover-landing__mod-code {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--cover-mint);
}

.cover-landing__mod-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--cover-text);
}

.cover-landing__mod-hint {
  margin-top: auto;
  font-size: 11px;
  color: var(--cover-muted);
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
}

.cover-landing__footer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 14px;
  z-index: 2;
  text-align: center;
  font-size: 12px;
  color: var(--cover-muted);
}

.cover-landing__footer a {
  color: inherit;
  text-decoration: none;
  transition: color 0.2s ease;
}

.cover-landing__footer a:hover {
  color: var(--cover-mint);
}

@media (max-width: 720px) {
  .cover-landing__modules {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .cover-landing__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .cover-landing__btn {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cover-landing__scan,
  .cover-landing__pulse,
  .cover-landing__cursor,
  .cover-landing__grid,
  .cover-landing__glow--b,
  .cover-landing__title.is-flicker:not(.is-blackout),
  .cover-landing.is-ready .cover-landing__corner,
  .cover-landing.is-ready .cover-landing__modules > li {
    animation: none !important;
  }

  .cover-landing__glow--a {
    transition: none;
  }

  .cover-landing__reveal,
  .cover-landing.is-ready .cover-landing__reveal,
  .cover-landing__modules > li {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
</style>
