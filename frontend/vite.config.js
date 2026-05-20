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
        target: 'http://127.0.0.1:5000', // 你的 Flask 后端地址
        changeOrigin: true,
        // 如果后端不需要 /api 前缀，可以用 rewrite 去掉，但你的 Flask 路由都有 /api，所以不用加 rewrite
      }
    }
  }
})