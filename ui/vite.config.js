import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 600000,          // 10 minutes — LLM can be slow
        proxyTimeout: 600000,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('[proxy error]', err.message)
          })
        },
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 10000,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          icons:  ['lucide-react'],
        },
      },
    },
  },
})
