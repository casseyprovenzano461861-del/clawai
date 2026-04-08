import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
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
        target: 'http://localhost:8888',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8888',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8888',
        changeOrigin: true
      },
      '/tools': {
        target: 'http://localhost:8888',
        changeOrigin: true
      }
    }
  }
})
