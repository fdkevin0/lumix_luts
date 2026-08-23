#!/usr/bin/env python3
"""Validate Lumix .cube LUT files and meta.yaml consistency."""

import os
import re
import sys

VALID_PHOTO_STYLES = {
    'STD', 'VIVD', 'NAT', 'LCLASN', 'FLAT', 'LAND', 'PORT',
    'MONO', 'LMONO', 'LMONOD', 'LMONOS', 'LEICAMONO',
    'CNED2', 'CNEV2', '709L', '2100HLG', '2100HLGF', 'VLOG',
}

PHOTO_STYLE_NAMES = {
    'STD': 'Standard', 'VIVD': 'Vivid', 'NAT': 'Natural',
    'LCLASN': 'L.ClassicNeo', 'FLAT': 'Flat', 'LAND': 'Landscape',
    'PORT': 'Portrait', 'MONO': 'Monochrome', 'LMONO': 'L.Monochrome',
    'LMONOD': 'L.Monochrome D', 'LMONOS': 'L.Monochrome S',
    'LEICAMONO': 'LEICA Monochrome', 'CNED2': 'Cinelike D2',
    'CNEV2': 'Cinelike V2', '709L': 'Like709',
    '2100HLG': 'Like2100(HLG)', '2100HLGF': 'Like2100(HLG) Full Range',
    'VLOG': 'V-Log',
}

LUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'luts')

errors = []
warnings = []


def check(condition, msg, is_warning=False):
    if not condition:
        (warnings if is_warning else errors).append(msg)


def parse_cube_header(filepath):
    result = {
        'photo_style': None,
        'lut_3d_size': None,
        'title': None,
        'has_domain_min': False,
        'has_domain_max': False,
        'data_line_count': 0,
        'creator': None,
    }
    in_data = False
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for line in f:
                stripped = line.strip()
                if in_data:
                    if stripped and not stripped.startswith('#'):
                        result['data_line_count'] += 1
                elif stripped.startswith('#LUMIXPHOTOSTYLE '):
                    tag = stripped.split()[-1]
                    result['photo_style'] = tag
                elif stripped.startswith('LUT_3D_SIZE '):
                    result['lut_3d_size'] = int(stripped.split()[-1])
                elif stripped.startswith('TITLE '):
                    result['title'] = stripped[6:].strip('"')
                elif stripped == 'DOMAIN_MIN 0.0 0.0 0.0':
                    result['has_domain_min'] = True
                elif stripped == 'DOMAIN_MAX 1.0 1.0 1.0':
                    result['has_domain_max'] = True
                elif stripped.startswith('# Created by '):
                    result['creator'] = stripped[13:]
                elif stripped and not stripped.startswith('#'):
                    in_data = True
                    result['data_line_count'] += 1
    except UnicodeDecodeError:
        check(False, f'{filepath}: not valid UTF-8')
    except Exception as e:
        check(False, f'{filepath}: read error: {e}')
    return result


def validate_cube_file(filepath):
    info = parse_cube_header(filepath)
    basename = os.path.basename(filepath)

    check(info['lut_3d_size'] is not None,
          f'{filepath}: missing LUT_3D_SIZE declaration')
    check(info['lut_3d_size'] == 33,
          f'{filepath}: LUT_3D_SIZE is {info["lut_3d_size"]}, expected 33',
          is_warning=True)

    expected_lines = (info['lut_3d_size'] or 33) ** 3
    check(info['data_line_count'] == expected_lines,
          f'{filepath}: expected {expected_lines} data points, got {info["data_line_count"]}')

    check(info['photo_style'] is not None,
          f'{filepath}: missing #LUMIXPHOTOSTYLE tag (camera will default to V-Log)',
          is_warning=True)
    if info['photo_style'] is not None:
        check(info['photo_style'] in VALID_PHOTO_STYLES,
              f'{filepath}: invalid photo style tag "{info["photo_style"]}"')

    # Check naming convention: <Name>_<variant>_base_<PHOTOSTYLE>.cube
    name_match = re.match(r'^(.+)_base_([A-Z0-9]+)\.cube$', basename)
    check(name_match is not None,
          f'{filepath}: filename does not follow <Name>_base_<PHOTOSTYLE>.cube convention',
          is_warning=True)
    if name_match and info['photo_style']:
        file_style = name_match.group(2)
        check(file_style == info['photo_style'],
              f'{filepath}: filename says base {file_style} but file header says {info["photo_style"]}',
              is_warning=True)

    # File size sanity check
    file_size = os.path.getsize(filepath)
    check(500_000 <= file_size <= 2_000_000,
          f'{filepath}: file size {file_size:,} bytes outside expected range (500KB-2MB)',
          is_warning=True)

    return info


def validate_meta_yaml(dirpath):
    try:
        import yaml
    except ImportError:
        check(False, 'PyYAML not installed; skipping meta.yaml validation. Install: pip install pyyaml')
        return None, []

    meta_path = os.path.join(dirpath, 'meta.yaml')
    if not os.path.exists(meta_path):
        check(False, f'{dirpath}: missing meta.yaml', is_warning=True)
        return None, []

    with open(meta_path, 'r', encoding='utf-8') as f:
        try:
            meta = yaml.safe_load(f)
        except yaml.YAMLError as e:
            check(False, f'{meta_path}: invalid YAML: {e}')
            return None, []

    check('author' in meta, f'{meta_path}: missing "author" field')
    check('luts' in meta, f'{meta_path}: missing "luts" field')

    if 'luts' not in meta:
        return meta, []

    meta_files = set()
    for lut in meta['luts']:
        check('file' in lut, f'{meta_path}: lut entry missing "file" field')
        check('name' in lut, f'{meta_path}: lut entry missing "name" field', is_warning=True)
        check('photo_style' in lut, f'{meta_path}: lut entry missing "photo_style" field')

        if 'file' in lut:
            cube_path = os.path.join(dirpath, lut['file'])
            check(os.path.exists(cube_path),
                  f'{meta_path}: referenced file "{lut["file"]}" does not exist')
            if 'photo_style' in lut:
                check(lut['photo_style'] in VALID_PHOTO_STYLES,
                      f'{meta_path}: invalid photo_style "{lut["photo_style"]}"')
            meta_files.add(lut['file'])

    return meta, meta_files


def main():
    if not os.path.isdir(LUTS_DIR):
        print(f'Error: luts directory not found at {LUTS_DIR}')
        sys.exit(1)

    cube_files_found = set()

    for dirpath, dirnames, filenames in os.walk(LUTS_DIR):
        # Check for meta.yaml in this directory
        cube_in_dir = [f for f in filenames if f.endswith('.cube')]
        if cube_in_dir:
            meta, meta_files = validate_meta_yaml(dirpath)

            for cube_file in cube_in_dir:
                cube_path = os.path.join(dirpath, cube_file)
                rel_path = os.path.relpath(cube_path, os.path.dirname(LUTS_DIR))
                cube_files_found.add(cube_path)

                validate_cube_file(cube_path)

                if meta_files is not None:
                    check(cube_file in meta_files,
                          f'{cube_path}: cube file not listed in meta.yaml',
                          is_warning=True)

            if meta_files is not None:
                for mf in meta_files:
                    check(mf in set(cube_in_dir),
                          f'{os.path.join(dirpath, mf)}: listed in meta.yaml but file not found')

    print(f'\nValidated {len(cube_files_found)} cube file(s)')
    if warnings:
        print(f'\nWarnings ({len(warnings)}):')
        for w in warnings:
            print(f'  ⚠ {w}')
    if errors:
        print(f'\nErrors ({len(errors)}):')
        for e in errors:
            print(f'  ✗ {e}')
        sys.exit(1)
    elif not warnings:
        print('All checks passed.')
    else:
        print('\nPassed with warnings.')


if __name__ == '__main__':
    main()
