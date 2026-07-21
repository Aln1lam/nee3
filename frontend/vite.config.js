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
      'vditor'
    ]
  },
  server: {
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