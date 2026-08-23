#!/usr/bin/env python3
"""Build the static LUT download website from meta.yaml files."""

import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print('Error: PyYAML required. Install: pip install pyyaml', file=sys.stderr)
    sys.exit(1)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUTS_DIR = os.path.join(REPO_ROOT, 'luts')
SITE_DIR = os.path.join(REPO_ROOT, 'site')
DATA_DIR = os.path.join(SITE_DIR, '_data')

VALID_PHOTO_STYLES = {
    'STD', 'VIVD', 'NAT', 'LCLASN', 'FLAT', 'LAND', 'PORT',
    'MONO', 'LMONO', 'LMONOD', 'LMONOS', 'LEICAMONO',
    'CNED2', 'CNEV2', '709L', '2100HLG', '2100HLGF', 'VLOG',
}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def parse_cube_photo_style(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('#LUMIXPHOTOSTYLE '):
                    return stripped.split()[-1]
                if stripped and not stripped.startswith('#') and not stripped.startswith('LUT_3D_SIZE') and not stripped.startswith('TITLE') and not stripped.startswith('DOMAIN'):
                    break
    except Exception:
        pass
    return None


def collect_luts():
    entries = []
    seen_ids = set()

    for dirpath, dirnames, filenames in os.walk(LUTS_DIR):
        if 'meta.yaml' not in filenames:
            continue

        meta_path = os.path.join(dirpath, 'meta.yaml')
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = yaml.safe_load(f)

        if not meta or 'luts' not in meta:
            continue

        author = meta.get('author', {})
        author_name = author.get('name', 'Unknown') if isinstance(author, dict) else str(author)
        author_link = author.get('link', '') if isinstance(author, dict) else ''
        collection = meta.get('collection', '')
        collection_en = meta.get('collection_en', collection)

        for lut in meta['luts']:
            cube_file = lut.get('file', '')
            cube_path = os.path.join(dirpath, cube_file)

            if not os.path.exists(cube_path):
                print(f'Warning: {cube_path} not found, skipping', file=sys.stderr)
                continue

            rel_path = os.path.relpath(cube_path, REPO_ROOT)
            file_photo_style = parse_cube_photo_style(cube_path)
            meta_photo_style = lut.get('photo_style', '')

            if file_photo_style and meta_photo_style and file_photo_style != meta_photo_style:
                print(f'Warning: {cube_file} header says {file_photo_style} but meta.yaml says {meta_photo_style}',
                      file=sys.stderr)

            lut_id = slugify(os.path.splitext(cube_file)[0])
            if lut_id in seen_ids:
                lut_id = slugify(f"{author_name}-{cube_file}")
            seen_ids.add(lut_id)

            preview = lut.get('preview', '')
            if preview:
                preview = os.path.relpath(os.path.join(dirpath, preview), REPO_ROOT)

            entry = {
                'id': lut_id,
                'name': lut.get('name', cube_file),
                'name_zh': lut.get('name_zh', lut.get('name', '')),
                'author': author_name,
                'author_link': author_link,
                'collection': collection,
                'collection_en': collection_en,
                'file': rel_path,
                'photo_style': meta_photo_style or file_photo_style or 'VLOG',
                'tags': lut.get('tags', []),
                'description_zh': lut.get('description_zh', ''),
                'description_en': lut.get('description_en', ''),
                'preview': preview,
            }
            entries.append(entry)

    return entries


def build_site(entries, repo_slug=''):
    os.makedirs(DATA_DIR, exist_ok=True)

    luts_json = json.dumps(entries, ensure_ascii=False, indent=2)
    json_path = os.path.join(DATA_DIR, 'luts.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(luts_json)
    print(f'Generated {json_path} ({len(entries)} LUTs)')

    # Generate index.html with inlined JSON for zero-fetch loading
    html_path = os.path.join(SITE_DIR, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(generate_html(entries, luts_json, repo_slug))
    print(f'Generated {html_path}')

    # Copy static assets (style.css, script.js already exist in site/)
    return True


def generate_html(entries, luts_json, repo_slug=''):
    collections = sorted(set(e['collection'] for e in entries if e['collection']))
    photo_styles = sorted(set(e['photo_style'] for e in entries))
    all_tags = sorted(set(t for e in entries for t in e['tags']))

    collection_options = '\n'.join(
        f'<option value="{c}">{e["collection_en"]} / {c}</option>'
        for c in collections
        for e in entries if e['collection'] == c
    ) if collections else ''

    # Deduplicate collection options
    seen = set()
    unique_collection_options = []
    for line in collection_options.split('\n'):
        if line not in seen:
            seen.add(line)
            unique_collection_options.append(line)
    collection_options = '\n'.join(unique_collection_options)

    style_chips = '\n'.join(
        f'<button class="chip" data-style="{s}">{s}</button>'
        for s in photo_styles
    )

    tag_chips = '\n'.join(
        f'<button class="chip" data-tag="{t}">{t}</button>'
        for t in all_tags
    )

    return f'''<!DOCTYPE html>
<html lang="zh-Hans">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lumix LUTs / Lumix 色彩预设</title>
  <meta name="description" content="Panasonic Lumix 相机 .cube LUT 色彩预设下载">
  <meta property="og:title" content="Lumix LUTs">
  <meta property="og:description" content="Panasonic Lumix .cube LUT 色彩预设下载站">
  <meta property="og:type" content="website">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header>
    <div class="header-inner">
      <h1>Lumix LUTs <span class="subtitle">色彩预设</span></h1>
      <p class="header-desc">Panasonic Lumix 相机 Real Time LUT .cube 文件下载</p>
    </div>
  </header>

  <main>
    <section class="filters">
      <div class="filter-row">
        <select id="collection-filter">
          <option value="">全部合集 / All Collections</option>
          {collection_options}
        </select>
        <input type="text" id="search" placeholder="搜索 LUT / Search...">
      </div>
      <div class="filter-row">
        <span class="filter-label">Photo Style:</span>
        <div class="chip-group" id="style-chips">{style_chips}</div>
      </div>
      <div class="filter-row">
        <span class="filter-label">Tags:</span>
        <div class="chip-group" id="tag-chips">{tag_chips}</div>
      </div>
    </section>

    <p class="result-count" id="result-count"></p>

    <div class="grid" id="lut-grid"></div>

    <div class="modal" id="modal">
      <div class="modal-content" id="modal-content"></div>
    </div>
  </main>

  <footer>
    <p>相机最多注册 39 个 LUT 文件 / Camera supports up to 39 LUT files</p>
    <p><a href="https://github.com/{repo_slug}" target="_blank" rel="noopener" id="repo-link">GitHub</a></p>
  </footer>

  <script id="luts-data" type="application/json">{luts_json}</script>
  <script>var REPO_SLUG = "{repo_slug}";</script>
  <script src="script.js"></script>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description='Build the static LUT download website')
    parser.add_argument('--repo', default='', help='GitHub repo slug (e.g. user/lumix_luts) for download links')
    args = parser.parse_args()

    if not os.path.isdir(LUTS_DIR):
        print(f'Error: luts directory not found at {LUTS_DIR}', file=sys.stderr)
        sys.exit(1)

    entries = collect_luts()
    if not entries:
        print('Error: no LUT entries found', file=sys.stderr)
        sys.exit(1)

    build_site(entries, repo_slug=args.repo)
    print(f'\nSite built successfully with {len(entries)} LUT(s).')


if __name__ == '__main__':
    main()
