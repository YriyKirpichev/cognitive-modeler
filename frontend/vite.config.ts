import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  return {
    plugins: [vue(), vueDevTools()],
    server: {
      port: parseInt(env.FRONTEND_PORT || '5175', 10),
      proxy: {
        '/api': {
          target: `http://${env.BACKEND_HOST}:${env.BACKEND_PORT}`,
          changeOrigin: true,
        },
      },
    },
    base: './',
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      rollupOptions: {
        output: {
          entryFileNames: 'assets/[name].js',
          chunkFileNames: 'assets/[name].js',
          assetFileNames: 'assets/[name].[ext]',
        },
      },
    },
    define: {
      __BACKEND_URL__: JSON.stringify(
        env.BACKEND_HOST && env.BACKEND_PORT
          ? `http://${env.BACKEND_HOST}:${env.BACKEND_PORT}`
          : 'http://localhost:8001',
      ),
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
