import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

const raiz = fileURLToPath(new URL('./', import.meta.url));
const salida = fileURLToPath(new URL('../app/static/dist', import.meta.url));

export default defineConfig({
  root: raiz,
  plugins: [react()],
  build: {
    outDir: salida,
    emptyOutDir: true,
    // Los bundles se sirven desde Flask, no desde el dev server de Vite.
    manifest: false,
    // Se conservan los sourcemaps: el bundle va minificado y sin ellos
    // depurar un error en producción es inviable.
    sourcemap: true,
    target: 'es2018',
    rollupOptions: {
      input: {
        'wizard-activos': fileURLToPath(new URL('./src/wizard-activos.jsx', import.meta.url)),
      },
      output: {
        // Nombres estables (sin hash) para poder referenciarlos desde Jinja.
        // La invalidación de caché la resuelve el helper `static_v()` de Flask,
        // que añade ?v=<mtime> a la URL.
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]',
      },
    },
  },
});
