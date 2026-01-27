import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Updated: 2026-01-27
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
