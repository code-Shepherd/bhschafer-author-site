# B. H. Schafer Author Site (Version 2)

A full Astro-based rebuild of the author site as a multipage, static platform designed for Cloudflare Pages.

## Stack

- Astro (static output)
- Astro content collections for Journal posts
- Markdown content in `src/content/journal/`
- No database/CMS/client framework

## Install

```bash
npm install
```

## Local development

```bash
npm run dev
```

## Build

```bash
npm run build
```

Build output is generated in `dist/`.

## Cloudflare Pages deployment assumptions

- Framework preset: **Astro** (or static site)
- Build command: `npm run build`
- Output directory: `dist`
- Node runtime: modern LTS (18+ recommended)

## Add a Journal post

1. Create a new Markdown file in `src/content/journal/`.
2. Include required frontmatter:

```yaml
---
title: Your Title
description: Short summary
pubDate: 2026-04-18
draft: false
updatedDate: 2026-04-19 # optional
tags: [craft, fiction] # optional
coverImage: /images/example.png # optional
---
```

3. Write post content below the frontmatter.
4. Draft posts (`draft: true`) are excluded from generated Journal pages.

## Update the “Latest from Substack” homepage card

Edit `src/data/site.ts` and update the `latestSubstack` object:

- `title`
- `url`
- `date`
- `excerpt`

The component is intentionally data-driven so this can be replaced later by build-time RSS ingestion.
