import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
// Если деплой на Vercel, используем стандартный outDir "dist" и base "/"
// Для GitHub Pages сохраняем base и outDir как раньше
const isVercel = !!process.env.VERCEL

export default defineConfig({
  plugins: [react()],
  base: isVercel ? '/' : '/Multi_Agent_RAG_LE/',
  build: {
    outDir: isVercel ? 'dist' : '../docs-react',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    open: true
  }
})
