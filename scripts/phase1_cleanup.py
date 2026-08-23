#!/usr/bin/env python3
"""Phase 1 v2: Rename all LUT dirs/files to English slugs using .md metadata as key."""

import os, re, shutil, json
from pathlib import Path

BASE = Path("/Users/fdkevin/Workspace/lumix_luts/luts")

# ============================================================
# Full catalog — match by name_zh + author_zh
# ============================================================
CATALOG = [
    {
        "cat": "anniversary",
        "author_slug": "tu-xiaodai",
        "lut_slug": "txd-agfaphoto-lebox",
        "name_zh": "TXD AgfaPhoto LeBox",
        "author_zh": "兔小呆",
    },
    {
        "cat": "anniversary",
        "author_slug": "desong",
        "lut_slug": "millennium-echo",
        "name_zh": "千禧回声",
        "author_zh": "德松Desong",
    },
    {
        "cat": "anniversary",
        "author_slug": "desong",
        "lut_slug": "millennium-echo-v2",
        "name_zh": "千禧回声 v2",
        "author_zh": "德松Desong",
    },
    {
        "cat": "anniversary",
        "author_slug": "plady",
        "lut_slug": "y2000",
        "name_zh": "y2000",
        "author_zh": "plady",
    },
    {
        "cat": "portrait",
        "author_slug": "guo-bin",
        "lut_slug": "snow-portrait",
        "name_zh": "雪天人像",
        "author_zh": "郭宾",
    },
    {
        "cat": "portrait",
        "author_slug": "zhang-heng",
        "lut_slug": "healing-light",
        "name_zh": "治愈光影",
        "author_zh": "张恒",
    },
    {
        "cat": "portrait",
        "author_slug": "guo-bin",
        "lut_slug": "seaside-sunset",
        "name_zh": "海边夕阳",
        "author_zh": "郭宾",
    },
    {
        "cat": "portrait",
        "author_slug": "xue-luyao",
        "lut_slug": "warm-cool-tone",
        "name_zh": "冷暖色调",
        "author_zh": "薛璐瑶",
    },
    {
        "cat": "portrait",
        "author_slug": "xue-luyao",
        "lut_slug": "teal-orange-tone",
        "name_zh": "青橙色调",
        "author_zh": "薛璐瑶",
    },
    {
        "cat": "portrait",
        "author_slug": "xue-luyao",
        "lut_slug": "high-low-contrast",
        "name_zh": "高低对比度",
        "author_zh": "薛璐瑶",
    },
    {
        "cat": "portrait",
        "author_slug": "bozi-booz",
        "lut_slug": "spring-portrait",
        "name_zh": "春意人像",
        "author_zh": "波子Booz",
    },
    {
        "cat": "portrait",
        "author_slug": "bozi-booz",
        "lut_slug": "forest-green-cool",
        "name_zh": "森绿清冷",
        "author_zh": "波子Booz",
    },
    {
        "cat": "portrait",
        "author_slug": "jon-simo",
        "lut_slug": "gritty-cinema",
        "name_zh": "暮色",
        "author_zh": "Jon Simo",
    },
    {
        "cat": "portrait",
        "author_slug": "guo-bin",
        "lut_slug": "seaside-portrait",
        "name_zh": "海边人像",
        "author_zh": "郭宾",
    },
    {
        "cat": "portrait",
        "author_slug": "guo-bin",
        "lut_slug": "aesthetic-portrait",
        "name_zh": "唯美人像",
        "author_zh": "郭宾",
    },
    {
        "cat": "portrait",
        "author_slug": "hailuoke",
        "lut_slug": "tibet-warm-light",
        "name_zh": "藏区暖光",
        "author_zh": "海螺壳",
    },
    {
        "cat": "portrait",
        "author_slug": "ejay",
        "lut_slug": "japanese-cyan-tone",
        "name_zh": "日系青调",
        "author_zh": "EJAY",
    },
    {
        "cat": "portrait",
        "author_slug": "ejay",
        "lut_slug": "skin-tone-opt",
        "name_zh": "肤色优化",
        "author_zh": "EJAY",
    },
    {
        "cat": "portrait",
        "author_slug": "tu-xiaodai",
        "lut_slug": "txd-grainy-film",
        "name_zh": "TXD Grainy Film",
        "author_zh": "兔小呆",
    },
    {
        "cat": "portrait",
        "author_slug": "tu-xiaodai",
        "lut_slug": "light-jp-blue",
        "name_zh": "轻日系-蓝",
        "author_zh": "兔小呆",
    },
    {
        "cat": "portrait",
        "author_slug": "tu-xiaodai",
        "lut_slug": "warm-skin-tone",
        "name_zh": "暖白肤色",
        "author_zh": "兔小呆",
    },
    {
        "cat": "portrait",
        "author_slug": "tu-xiaodai",
        "lut_slug": "txd-rag-film-cned2",
        "name_zh": "TXD RaG Film CNED2",
        "author_zh": "兔小呆",
    },
    {
        "cat": "portrait",
        "author_slug": "desong",
        "lut_slug": "vintage-summer",
        "name_zh": "复古夏日",
        "author_zh": "德松Desong",
    },
    {
        "cat": "portrait",
        "author_slug": "desong",
        "lut_slug": "mosslight",
        "name_zh": "薄暮苔痕",
        "author_zh": "德松Desong",
    },
    {
        "cat": "portrait",
        "author_slug": "tu-xiaodai",
        "lut_slug": "txd-eterna",
        "name_zh": "TXD Eterna",
        "author_zh": "兔小呆",
    },
    {
        "cat": "outdoor",
        "author_slug": "ali-halip",
        "lut_slug": "summer",
        "name_zh": "夏日",
        "author_zh": "阿里Halip",
    },
    {
        "cat": "outdoor",
        "author_slug": "ba-wenhuan",
        "lut_slug": "dark-tone-story",
        "name_zh": "暗调故事",
        "author_zh": "巴文欢",
    },
    {
        "cat": "outdoor",
        "author_slug": "ba-wenhuan",
        "lut_slug": "pink-youth",
        "name_zh": "粉黛青春",
        "author_zh": "巴文欢",
    },
    {
        "cat": "outdoor",
        "author_slug": "ba-wenhuan",
        "lut_slug": "verdant-breath",
        "name_zh": "葱绿气息",
        "author_zh": "巴文欢",
    },
    {
        "cat": "outdoor",
        "author_slug": "plady",
        "lut_slug": "summer-breeze",
        "name_zh": "夏日暖风",
        "author_zh": "Plady",
    },
    {
        "cat": "outdoor",
        "author_slug": "plady",
        "lut_slug": "rich-tone",
        "name_zh": "浓厚格调",
        "author_zh": "Plady",
    },
    {
        "cat": "outdoor",
        "author_slug": "plady",
        "lut_slug": "grey-cinema",
        "name_zh": "灰度电影",
        "author_zh": "Plady",
    },
    {
        "cat": "outdoor",
        "author_slug": "bozi-booz",
        "lut_slug": "vintage-blue-tone",
        "name_zh": "复古蓝调",
        "author_zh": "波子Booz",
    },
    {
        "cat": "outdoor",
        "author_slug": "jon-simo",
        "lut_slug": "day-for-night",
        "name_zh": "幻化",
        "author_zh": "Jon Simo",
    },
    {
        "cat": "outdoor",
        "author_slug": "guo-bin",
        "lut_slug": "fresh-cuisine",
        "name_zh": "清新美食",
        "author_zh": "郭宾",
    },
    {
        "cat": "outdoor",
        "author_slug": "guo-bin",
        "lut_slug": "camping-vibe",
        "name_zh": "露营氛围",
        "author_zh": "郭宾",
    },
    {
        "cat": "outdoor",
        "author_slug": "guo-bin",
        "lut_slug": "rice-field-village",
        "name_zh": "稻田乡村",
        "author_zh": "郭宾",
    },
    {
        "cat": "outdoor",
        "author_slug": "guo-bin",
        "lut_slug": "warm-village",
        "name_zh": "温暖乡村",
        "author_zh": "郭宾",
    },
    {
        "cat": "outdoor",
        "author_slug": "guo-bin",
        "lut_slug": "dusk-atmosphere",
        "name_zh": "黄昏氛围",
        "author_zh": "郭宾",
    },
    {
        "cat": "outdoor",
        "author_slug": "guo-bin",
        "lut_slug": "golden-rice-field",
        "name_zh": "金色稻田",
        "author_zh": "郭宾",
    },
    {
        "cat": "outdoor",
        "author_slug": "guo-bin",
        "lut_slug": "verdant-scenery",
        "name_zh": "青绿风景",
        "author_zh": "郭宾",
    },
    {
        "cat": "outdoor",
        "author_slug": "hailuoke",
        "lut_slug": "positive-film",
        "name_zh": "正片",
        "author_zh": "海螺壳",
    },
    {
        "cat": "outdoor",
        "author_slug": "ejay",
        "lut_slug": "cinema-tone",
        "name_zh": "影院色调",
        "author_zh": "EJAY",
    },
    {
        "cat": "outdoor",
        "author_slug": "ejay",
        "lut_slug": "warm-film-tone",
        "name_zh": "暖调胶片",
        "author_zh": "EJAY",
    },
    {
        "cat": "outdoor",
        "author_slug": "xiao-zhai",
        "lut_slug": "candy-color",
        "name_zh": "糖果色",
        "author_zh": "小翟同学",
    },
    {
        "cat": "outdoor",
        "author_slug": "tu-xiaodai",
        "lut_slug": "blue-ripple",
        "name_zh": "蓝漾",
        "author_zh": "兔小呆",
    },
    {
        "cat": "outdoor",
        "author_slug": "qingtian",
        "lut_slug": "sunny-mint",
        "name_zh": "晴天薄荷",
        "author_zh": "晴天",
    },
    {
        "cat": "outdoor",
        "author_slug": "zhou",
        "lut_slug": "patina-of-rain",
        "name_zh": "苔痕雨季",
        "author_zh": "舟zhou",
    },
    {
        "cat": "indoor",
        "author_slug": "hailuoke",
        "lut_slug": "bw-old-film",
        "name_zh": "黑白旧胶片",
        "author_zh": "海螺壳",
    },
    {
        "cat": "indoor",
        "author_slug": "guo-bin",
        "lut_slug": "film-vintage",
        "name_zh": "胶片复古",
        "author_zh": "郭宾",
    },
    {
        "cat": "indoor",
        "author_slug": "guo-bin",
        "lut_slug": "food-film",
        "name_zh": "美食胶片",
        "author_zh": "郭宾",
    },
    {
        "cat": "indoor",
        "author_slug": "plady",
        "lut_slug": "white-negative",
        "name_zh": "白色负片",
        "author_zh": "Plady",
    },
    {
        "cat": "indoor",
        "author_slug": "jon-simo",
        "lut_slug": "vintage-vibes",
        "name_zh": "怀旧",
        "author_zh": "Jon Simo",
    },
    {
        "cat": "indoor",
        "author_slug": "hailuoke",
        "lut_slug": "vintage-old-film",
        "name_zh": "复古旧胶片",
        "author_zh": "海螺壳",
    },
    {
        "cat": "indoor",
        "author_slug": "hailuoke",
        "lut_slug": "magenta-old-film",
        "name_zh": "洋红旧胶片",
        "author_zh": "海螺壳",
    },
    {
        "cat": "indoor",
        "author_slug": "ejay",
        "lut_slug": "film-impression",
        "name_zh": "胶片印象",
        "author_zh": "EJAY",
    },
    {
        "cat": "indoor",
        "author_slug": "qingtian",
        "lut_slug": "light-green",
        "name_zh": "轻柔绿意",
        "author_zh": "晴天",
    },
]

CAT_SLUGS = {"anniversary", "portrait", "outdoor", "indoor"}


def read_md_title(md_path):
    """Extract the title from an .md file (# Title line)."""
    try:
        content = md_path.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
    except:
        pass
    return None


def match_entry(md_title, dir_name):
    """Match a directory to a catalog entry using md title and dir name."""
    for entry in CATALOG:
        name_zh = entry["name_zh"]
        author_zh = entry["author_zh"]
        if md_title:
            # Check if md title contains the name_zh AND author_zh
            if name_zh in md_title and author_zh in md_title:
                return entry
            # For English titles, check slug patterns
            if (
                name_zh.lower() in md_title.lower()
                and author_zh.lower() in md_title.lower()
            ):
                return entry
        # Fallback: check dir name
        if name_zh in dir_name and author_zh in dir_name:
            return entry
    return None


def main():
    print("=" * 60)
    print("Phase 1 v2: Full rename to English slugs")
    print("=" * 60)

    # Step 1: Remove junk
    print("\n[1/3] Removing junk files...")
    for d in BASE.rglob("__MACOSX"):
        shutil.rmtree(d, ignore_errors=True)
    for f in BASE.rglob("._*"):
        f.unlink(missing_ok=True)
    print("  Done")

    # Step 2: Scan all LUT dirs and build rename plan
    print("\n[2/3] Building rename plan...")
    renames = []  # (old_path, new_path)

    for cat_slug in CAT_SLUGS:
        cat_dir = BASE / cat_slug
        if not cat_dir.exists():
            print(f"  WARNING: {cat_slug} not found, skipping")
            continue

        for lut_dir in sorted(cat_dir.iterdir()):
            if not lut_dir.is_dir():
                continue
            if lut_dir.name.startswith("."):
                continue

            # Find the .md file in this directory
            md_files = list(lut_dir.glob("*.md"))
            md_title = None
            if md_files:
                md_title = read_md_title(md_files[0])

            # Match to catalog
            entry = match_entry(md_title, lut_dir.name)
            if not entry:
                print(f"  WARNING: Could not match '{lut_dir.name}' (md: {md_title})")
                continue

            # Special handling for duplicate 千禧回声: check if this is v2
            if entry["name_zh"] == "千禧回声":
                # Check if this is the second occurrence (v2)
                existing = [r for r in renames if r[1].name == "millennium-echo"]
                if existing:
                    entry = [
                        e for e in CATALOG if e["lut_slug"] == "millennium-echo-v2"
                    ][0]

            new_lut_dir = cat_dir / entry["lut_slug"]
            renames.append((lut_dir, new_lut_dir))

    # Check for conflicts
    targets = [r[1] for r in renames]
    if len(targets) != len(set(targets)):
        from collections import Counter

        dupes = [p for p, c in Counter(targets).items() if c > 1]
        print(f"  ERROR: Duplicate targets: {[d.name for d in dupes]}")
        return

    print(f"  Plan: {len(renames)} directories to rename")

    # Step 3: Execute renames
    print("\n[3/3] Executing renames...")
    moved = 0
    for old_dir, new_dir in renames:
        if old_dir == new_dir:
            continue

        if new_dir.exists():
            # Merge
            for f in old_dir.iterdir():
                dest = new_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
            if not any(old_dir.iterdir()):
                old_dir.rmdir()
        else:
            shutil.move(str(old_dir), str(new_dir))
        moved += 1

    print(f"  Renamed {moved} directories")

    # Step 4: Rename files inside to English slugs
    print("\n[4/4] Renaming LUT files to English slugs...")
    file_renamed = 0
    for entry in CATALOG:
        cat_dir = BASE / entry["cat"]
        lut_dir = cat_dir / entry["lut_slug"]
        if not lut_dir.exists():
            continue

        for f in list(lut_dir.iterdir()):
            if f.is_dir():
                continue
            if f.name.startswith("._") or f.name == ".DS_Store":
                f.unlink(missing_ok=True)
                continue

            ext = f.suffix.lower()
            if ext == ".md":
                new_name = f"{entry['lut_slug']}.md"
            elif ext in (".cube", ".vlt"):
                stem = f.stem.lower()
                if stem in ("cold", "warm"):
                    new_name = f"{entry['lut_slug']}_{stem}{ext}"
                else:
                    new_name = f"{entry['lut_slug']}{ext}"
            elif ext == ".yaml":
                new_name = f"{entry['lut_slug']}.yaml"
            else:
                continue  # skip unknown

            if f.name != new_name:
                dest = f.parent / new_name
                if dest.exists():
                    dest.unlink()
                f.rename(dest)
                file_renamed += 1

    print(f"  Renamed {file_renamed} files")

    # Print final structure
    print("\n" + "=" * 60)
    print("Final structure:")
    for cat_slug in sorted(CAT_SLUGS):
        cat_dir = BASE / cat_slug
        if not cat_dir.exists():
            continue
        entries = [d.name for d in sorted(cat_dir.iterdir()) if d.is_dir()]
        file_count = sum(1 for f in cat_dir.rglob("*") if f.is_file())
        print(f"\n{cat_slug}/ ({len(entries)} LUTs, {file_count} files)")
        for e in entries[:3]:
            files = [f.name for f in sorted((cat_dir / e).iterdir()) if f.is_file()]
            print(f"  {e}/ → {', '.join(files)}")
        if len(entries) > 3:
            print(f"  ... and {len(entries) - 3} more")

    # Remove empty dirs
    for d in sorted(BASE.rglob("*"), reverse=True):
        if d.is_dir() and d != BASE and d.parent != BASE and not any(d.iterdir()):
            d.rmdir()


if __name__ == "__main__":
    main()
