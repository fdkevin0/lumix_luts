# Lumix LUTs

An archival catalog and static download site for Panasonic Lumix Real Time LUT
presets. The project preserves source evidence, builds a normalized catalog,
and adds camera-facing metadata to downloaded `.cube` files without changing
their color data.

Production site: <https://lumix.fdkevin.cloud>

## Requirements

- Node.js 22.12.0 or newer
- npm
- Python 3.12 or newer

No third-party Python packages are required.

## Getting started

```bash
npm ci
npm run check
npm run dev
```

`npm run check` regenerates the canonical catalog, verifies that generated data
is committed, validates every LUT and snapshot hash, tests browser-side metadata
rewriting, type-checks Astro, builds the site, and confirms that the build only
contains canonical assets.

## Repository layout

```text
data/
  snapshots/<date>/     Immutable source pages, archives, previews, and hashes
  annotations/          Reviewed IDs, names, tags, and photo-style annotations
  canonical/            Deterministic, normalized catalog generated from inputs
  camera/               Generated camera-safe aliases
  review/               Items that still require human review
docs/research/           Supporting technical research
scripts/                 Catalog generation, validation, and build checks
src/                     Astro pages, components, styles, and browser logic
```

There is one data pipeline:

```text
snapshots + annotations -> canonical catalog -> Astro build -> Cloudflare assets
```

Do not edit files under `data/canonical/` by hand. Update the snapshot or
annotation input and regenerate the catalog instead.

## Data workflow

The current source snapshot is `2026-08-24`. To reproduce its canonical output:

```bash
npm run audit:canonical
npm run validate:canonical
git diff --exit-code -- data/canonical data/camera data/review data/snapshots
```

Important invariants:

- Snapshot evidence is immutable. A new retrieval uses a new dated directory.
- Source pages, archives, preview images, and RAR extracts are SHA-256 pinned.
- Canonical filenames use lowercase ASCII, digits, and hyphens.
- Ambiguous source matches stop generation instead of silently guessing.
- Duplicate payloads remain separate when Panasonic publishes them as separate
  catalog entries.
- Human interpretation lives in `data/annotations/`, never in source evidence.

See [`data/README.md`](data/README.md) for the detailed data model.

## Commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Astro development server |
| `npm run audit:canonical` | Regenerate canonical data from reviewed inputs |
| `npm run validate:canonical` | Validate catalog structure, hashes, and LUT data |
| `npm run test:cube-metadata` | Test download-time Lumix metadata rewriting |
| `npm run typecheck` | Run Astro and TypeScript diagnostics |
| `npm run build` | Build the static site into `dist/` |
| `npm run check:assets` | Verify canonical build assets and reject legacy paths |
| `npm run check` | Run the complete local and CI verification suite |
| `npm run cf:dev` | Preview the static build with Wrangler |
| `npm run deploy` | Build and deploy with Wrangler |

## Lumix compatibility

Panasonic documentation guarantees `.cube` LUT grids from 2 through 33 points.
This catalog also preserves seven original 65-point files that have been tested
successfully but remain outside the documented range; the site displays a clear
compatibility warning and never downsamples them.

When a user downloads a `.cube` file, the browser can update `TITLE` and
`#LUMIXPHOTOSTYLE` and optionally set Panasonic-documented grain, color-noise,
sharpness, and noise-reduction fields. LUT RGB rows are preserved byte-for-byte
apart from the surrounding text serialization required to rewrite the header.
`.vlt` files are downloaded unchanged.

The metadata research and source references are documented in
[`docs/research/cube-sdk-and-lumix-metadata.md`](docs/research/cube-sdk-and-lumix-metadata.md).

## Deployment

Astro produces a static `dist/` directory. Wrangler publishes that directory as
Cloudflare Workers Static Assets using `wrangler.jsonc`. The `main` branch is the
production branch; GitHub Actions validates and builds changes but does not
deploy them directly.

## Rights

LUT files, preview images, names, and descriptions remain the property of their
respective authors and rights holders. This repository preserves provenance and
does not relicense those assets.
