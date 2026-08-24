// @ts-check
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://lumix.fdkevin.cloud',
  output: 'static',
  vite: {
    server: {
      fs: {
        allow: ['..'], // allow imports from parent (luts/luts.json)
      },
    },
  },
});
