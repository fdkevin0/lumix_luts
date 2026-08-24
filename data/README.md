# Data model

The data tree separates immutable source evidence, reviewed human annotations,
and deterministic generated output.

## Layers

### `snapshots/<date>/`

A snapshot is the evidence captured from the source catalog on a specific date:

- `source-pages/`: the four category pages used to identify official entries;
- `raw-archives/`: the original ZIP and RAR downloads;
- `source-previews/`: the 57 source preview images;
- `rar-extracts/`: retained, hash-pinned payloads for the two RAR compression
  methods that Python's standard library cannot decode;
- `manifest.json`: source paths, sizes, retrieval time, and SHA-256 hashes.

Snapshots are append-only. Never overwrite a historical snapshot in place.

### `annotations/`

Reviewed information that cannot be derived safely from the source files:

- `catalog.json`: stable IDs, author slugs, English names, tags, and expected
  payload hashes;
- `preview-profiles.json`: the photo-style labels read from preview images and
  cross-checked against embedded `#LUMIXPHOTOSTYLE` values.

Annotations may be corrected through normal review. They must not contain source
assets or generated output.

### `canonical/`

Generated, production-facing data:

- `luts/`: normalized LUT filenames;
- `previews/`: normalized display previews;
- `manifests/`: provenance and file metadata for each catalog entry;
- `luts.json`: the database consumed by Astro;
- `manifest.json`: global generation metadata.

Canonical output must be reproducible from snapshots and annotations. CI runs
the generator and fails if the resulting Git diff is non-empty.

### `camera/` and `review/`

`camera/aliases.json` contains generated ASCII filenames suitable for Lumix
cameras. `review/pending.json` blocks canonical publication whenever an item
cannot be matched unambiguously.

## Current snapshot

The `2026-08-24` snapshot contains:

- 57 official source cards;
- 57 canonical LUT entries;
- 63 canonical LUT files;
- 57 source previews;
- one known duplicate-content group: `blue-ripple` and `light-jp-blue`.

The two Millennium Echo source cards are intentionally published as separate
Cold and Warm canonical entries.

## Regeneration

From the repository root:

```bash
npm run audit:canonical
npm run validate:canonical
git diff --exit-code -- data/canonical data/camera data/review data/snapshots
```

Generation stops on missing evidence, hash mismatches, ambiguous cards,
conflicting photo-style annotations, or alias collisions.
