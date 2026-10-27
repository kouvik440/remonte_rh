import { resolve } from 'node:path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const sourceRoot = resolve(import.meta.dirname, 'src');

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, import.meta.dirname, '');
  const proxy = {
    '/api': {
      target: environment.REMONTE_RH_API_TARGET || 'http://127.0.0.1:8001',
      changeOrigin: true,
    },
  };
  return {
    envDir: import.meta.dirname,
    appType: 'spa',
    server: { proxy },
    preview: { proxy },
    plugins: [react(), tailwindcss()],
    resolve: { alias: { '@': sourceRoot } },
    root: sourceRoot,
    build: {
      outDir: resolve(import.meta.dirname, 'dist'),
      emptyOutDir: true,
    },
  };
});
