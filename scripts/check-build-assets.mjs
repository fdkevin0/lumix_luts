import { access, readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

const ROOT = join(import.meta.dirname, '..');
const DIST = join(ROOT, 'dist');
const database = JSON.parse(
  await readFile(join(ROOT, 'data', 'canonical', 'luts.json'), 'utf8'),
);

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

const expected = new Set();
for (const lut of database.luts) {
  for (const file of lut.files) expected.add(file.public_path);
  for (const preview of lut.preview_images ?? []) expected.add(preview.path);
}

const missing = [];
for (const relativePath of expected) {
  if (!(await exists(join(DIST, relativePath)))) missing.push(relativePath);
}

if (await exists(join(DIST, 'previews'))) {
  throw new Error('Legacy asset directory was published: dist/previews');
}

const routeFiles = await readdir(join(DIST, 'luts'), { recursive: true });
const leakedAssets = routeFiles.filter((path) => /\.(?:cube|vlt|md)$/i.test(path));
if (leakedAssets.length > 0) {
  throw new Error(`Legacy LUT assets were published outside canonical/:\n${leakedAssets.join('\n')}`);
}

if (missing.length > 0) {
  throw new Error(`Missing ${missing.length} canonical build asset(s):\n${missing.join('\n')}`);
}

console.log(`Validated ${expected.size} canonical build assets; no legacy assets published.`);
