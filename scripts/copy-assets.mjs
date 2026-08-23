// Copy LUT files and previews to public/ for Astro build
import { cp, mkdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = import.meta.dirname + '/..';
const LUTS_DIR = join(ROOT, 'luts');
const CANONICAL_DIR = join(ROOT, 'data', 'canonical');
const PUBLIC = join(ROOT, 'public');

const categories = ['anniversary', 'portrait', 'outdoor', 'indoor'];

async function main() {
  // Copy LUT category directories
  for (const cat of categories) {
    const src = join(LUTS_DIR, cat);
    const dst = join(PUBLIC, 'luts', cat);
    if (existsSync(src)) {
      await cp(src, dst, { recursive: true, force: true });
      console.log(`  Copied: luts/${cat}/`);
    }
  }

  // Copy previews
  const previewsSrc = join(LUTS_DIR, 'previews');
  const previewsDst = join(PUBLIC, 'previews');
  if (existsSync(previewsSrc)) {
    await cp(previewsSrc, previewsDst, { recursive: true, force: true });
    const count = (await import('node:fs/promises')).readdir(previewsDst);
    console.log(`  Copied: previews/ (${(await count).length} files)`);
  }

  // Copy canonical, provenance-backed assets used by the Astro site.
  const canonicalLutsSrc = join(CANONICAL_DIR, 'luts');
  const canonicalLutsDst = join(PUBLIC, 'canonical', 'luts');
  if (existsSync(canonicalLutsSrc)) {
    await rm(canonicalLutsDst, { recursive: true, force: true });
    await cp(canonicalLutsSrc, canonicalLutsDst, { recursive: true, force: true });
    console.log('  Copied: data/canonical/luts/');
  }

  const canonicalPreviewsSrc = join(CANONICAL_DIR, 'previews');
  const canonicalPreviewsDst = join(PUBLIC, 'canonical', 'previews');
  if (existsSync(canonicalPreviewsSrc)) {
    await rm(canonicalPreviewsDst, { recursive: true, force: true });
    await cp(canonicalPreviewsSrc, canonicalPreviewsDst, { recursive: true, force: true });
    const count = (await import('node:fs/promises')).readdir(canonicalPreviewsDst);
    console.log('  Copied: data/canonical/previews/ (' + (await count).length + ' files)');
  }
}

main().catch(console.error);
