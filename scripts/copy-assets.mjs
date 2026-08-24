// Materialize the canonical LUT assets for Astro's public-directory build step.
import { cp, mkdir, readdir, rm } from 'node:fs/promises';
import { join } from 'node:path';

const ROOT = import.meta.dirname + '/..';
const CANONICAL_DIR = join(ROOT, 'data', 'canonical');
const PUBLIC = join(ROOT, 'public');

async function main() {
  await rm(PUBLIC, { recursive: true, force: true });
  await mkdir(join(PUBLIC, 'canonical'), { recursive: true });

  const canonicalLutsSrc = join(CANONICAL_DIR, 'luts');
  const canonicalLutsDst = join(PUBLIC, 'canonical', 'luts');
  const canonicalPreviewsSrc = join(CANONICAL_DIR, 'previews');
  const canonicalPreviewsDst = join(PUBLIC, 'canonical', 'previews');

  await Promise.all([
    cp(canonicalLutsSrc, canonicalLutsDst, { recursive: true }),
    cp(canonicalPreviewsSrc, canonicalPreviewsDst, { recursive: true }),
  ]);

  const previewCount = (await readdir(canonicalPreviewsDst)).length;
  console.log('  Copied: data/canonical/luts/');
  console.log(`  Copied: data/canonical/previews/ (${previewCount} files)`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
