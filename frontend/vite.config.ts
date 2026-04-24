import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 15173, // 5-digit port as required by CLAUDE.md
    strictPort: true,
    host: true,
  },
})
