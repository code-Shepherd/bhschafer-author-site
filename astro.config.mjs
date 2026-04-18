import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://bhschafer.com',
  output: 'static',
  markdown: {
    shikiConfig: {
      theme: 'github-dark'
    }
  }
});
