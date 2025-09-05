import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/multiagent-rag-pro/',
  build: {
    outDir: '../docs-react',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    open: true
  }
})
