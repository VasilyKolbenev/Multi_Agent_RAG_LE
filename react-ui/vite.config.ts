import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync, existsSync, mkdirSync } from 'fs'
import { resolve } from 'path'

const copyPdfWorker = () => ({
  name: 'copy-pdf-worker',
  writeBundle() {
    const workerPath = resolve(__dirname, 'node_modules/pdfjs-dist/build/pdf.worker.min.js')
    const targetDir = resolve(__dirname, '../docs-react/assets') // Adjust to your actual build output path
    const targetPath = resolve(targetDir, 'pdf.worker.min.js')

    if (!existsSync(targetDir)) {
      mkdirSync(targetDir, { recursive: true })
    }

    if (existsSync(workerPath)) {
      copyFileSync(workerPath, targetPath)
      console.log('PDF.js worker copied to', targetPath)
    } else {
      console.warn('PDF.js worker not found at', workerPath)
    }
  }
})

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), copyPdfWorker()],
  base: '/Multi_Agent_RAG_LE/',
  build: {
    outDir: '../docs-react',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    open: true
  }
})
