import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  // 加载 .env 文件中的变量（前缀为空，可读取所有）
  const env = loadEnv(mode, process.cwd(), '')

  // 后端端口：优先用 start.py 注入的 VITE_BACKEND_PORT，回退到 8000
  const backendPort = process.env.VITE_BACKEND_PORT || env.VITE_BACKEND_PORT || '8000'
  const backendHttp = `http://localhost:${backendPort}`
  const backendWs   = `ws://localhost:${backendPort}`

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      port: 3000,
      proxy: {
        '/attack': {
          target: backendHttp,
          changeOrigin: true
        },
        '/api': {
          target: backendHttp,
          changeOrigin: true
        },
        '/health': {
          target: backendHttp,
          changeOrigin: true
        },
        '/tools': {
          target: backendHttp,
          changeOrigin: true
        },
        '/ws': {
          target: backendWs,
          ws: true,
          changeOrigin: true,
          configure: (proxy) => {
            // 后端未启动时 WS 代理会抛 ECONNABORTED/ECONNREFUSED，属正常现象，静默处理
            proxy.on('error', () => {});
            proxy.on('proxyReqWs', (_proxyReq, _req, socket) => {
              socket.on('error', () => {});
            });
          }
        }
      }
    }
  }
})
