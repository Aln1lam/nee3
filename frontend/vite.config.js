import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import jsx from '@vitejs/plugin-vue-jsx'
import path from 'path'

export default defineConfig({
  plugins: [
    vue({ script: { lang: 'ts' } }),
    jsx()
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'axios',
      'naive-ui',
      '@vicons/ionicons5',
      '@vicons/tabler',
      'marked',
      'vditor',
      'echarts/core',
      'echarts/charts',
      'echarts/components',
      'echarts/renderers',
    ]
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('echarts')) return 'vendor-echarts'
          if (id.includes('naive-ui') || id.includes('vueuc') || id.includes('vooks')) return 'vendor-naive'
          if (id.includes('vditor')) return 'vendor-vditor'
          if (id.includes('@xterm') || id.includes('xterm')) return 'vendor-xterm'
          if (id.includes('@fullcalendar')) return 'vendor-calendar'
          if (id.includes('highlight.js') || id.includes('marked') || id.includes('dompurify')) {
            return 'vendor-markdown'
          }
          if (id.includes('vue') || id.includes('vue-router') || id.includes('axios')) {
            return 'vendor-vue'
          }
        },
      },
    },
    chunkSizeWarningLimit: 900,
  },
  server: {
    host: '0.0.0.0',
    // 开启代理：前端请求 /api 时，Vite 自动转发给 Flask
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        // 开发时让 Set-Cookie 落在当前前端 origin，便于 HttpOnly 会话联调
        cookieDomainRewrite: '',
        cookiePathRewrite: '/',
      },
    }
  }
})
