<template>
  <div class="terminal-container">
    <div class="crt-overlay"></div> <vue-command
      :commands="commands"
      :yargs-options="{ alias: { h: 'help' } }"
      prompt="guest@neepu-sec:~$"
      title="NEEPU SEC TERMINAL v1.0"
      show-intro
      intro="Welcome to NEEPU CTF Platform. Type 'help' to start."
      class="my-terminal"
    />
  </div>
</template>

<script>
import { inject, ref } from 'vue'
import VueCommand, { createStdout } from 'vue-command'
import 'vue-command/dist/vue-command.css' // 引入默认样式

export default {
  components: { VueCommand },
  setup() {
    const axios = inject('axios')
    
    // 定义命令处理逻辑
    const commands = {
      // 1. help 命令
      help: () => createStdout(`
        Available commands:
        -------------------
        login [email] [pass]   Login to the system
        ls                     List all challenges
        cat [id]               View challenge details
        flag [id] [string]     Submit a flag
        whoami                 Show current user info
        clear                  Clear terminal
      `),

      // 2. login 命令
      login: async (args) => {
        const [email, password] = args._.slice(1)
        if (!email || !password) return createStdout('Usage: login <email> <password>')
        
        try {
          const { data } = await axios.post('/api/auth/login', { email, password })
          localStorage.setItem('neepu_token', data.access_token)
          axios.defaults.headers.common['Authorization'] = 'Bearer ' + data.access_token
          return createStdout(`Access Granted. Welcome back, ${data.user.nickname}.`)
        } catch (e) {
          return createStdout(`Access Denied: ${e.response?.data?.msg || 'Unknown error'}`)
        }
      },

      // 3. ls 命令 (列出题目)
      ls: async () => {
        try {
          const { data } = await axios.get('/api/games/1/challenges')
          if (!data.items) return createStdout('No challenges found.')
          
          let output = 'ID   TITLE           SCORE\n'
          output += '--------------------------\n'
          data.items.forEach(c => {
            output += `${String(c.id).padEnd(4)} ${c.title.padEnd(15)} ${c.score}\n`
          })
          return createStdout(output)
        } catch (e) {
          return createStdout('Error fetching challenges. Are you logged in?')
        }
      },
      
      // 4. flag 命令 (提交 Flag)
      flag: async (args) => {
        const [id, flagStr] = args._.slice(1)
        if (!id || !flagStr) return createStdout('Usage: flag <challenge_id> <flag_string>')
        
        try {
          const { data } = await axios.post(`/api/games/challenges/${id}/submit`, { flag: flagStr })
          if (data.correct) return createStdout(`[SUCCESS] Flag accepted! Points added.`)
          else return createStdout(`[FAIL] Incorrect flag.`)
        } catch (e) {
          return createStdout(`System Error: ${e.message}`)
        }
      }
    }

    return { commands }
  }
}
</script>

<style scoped>
/* 核心样式：黑客绿 + 扫描线 */
.terminal-container {
  min-height: var(--term-min-height, 100vh);
  background-color: var(--term-bg, #0d0d0d);
  font-family: var(--term-font-family, 'Fira Code, monospace'); /* 记得确保你在 main.js 里引入了这个字体 */
}

/* 覆盖 vue-command 的默认样式 */
:deep(.vue-command) {
  background: transparent !important;
}
:deep(.vue-command input), :deep(.vue-command span) {
  color: var(--term-fg, #00ff41) !important; /* 经典的黑客绿 */
  text-shadow: 0 0 var(--term-glow-blur, 5px) var(--term-fg, #00ff41);
}

/* CRT 扫描线特效 (增加复古感) */
.crt-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(
    var(--term-scanline-top, rgba(18, 16, 16, 0)) 50%, 
    var(--term-scanline-bottom, rgba(0, 0, 0, 0.25)) 50%
  ), linear-gradient(
    90deg, 
    var(--term-chroma-left, rgba(255, 0, 0, 0.06)), 
    var(--term-chroma-mid, rgba(0, 255, 0, 0.02)), 
    var(--term-chroma-right, rgba(0, 0, 255, 0.06))
  );
  background-size: var(--term-scanline-size, 100% 2px), var(--term-chroma-size, 3px 100%);
  pointer-events: none; /* 让点击穿透过去 */
  z-index: var(--term-overlay-z, 999);
}
</style>