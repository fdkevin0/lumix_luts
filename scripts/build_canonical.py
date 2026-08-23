#!/usr/bin/env python3
"""Build a non-destructive, provenance-rich canonical LUT tree.

The script consumes a dated official snapshot under ``data/snapshots`` and the
existing ``luts/luts.json`` database.  It never removes or rewrites the legacy
``luts/`` tree.  Ambiguous cards or files fail the run before canonical output
is written, so a human can review the evidence first.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import html
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
CATEGORY_PAGES = {
    "anniversary": "113",
    "portrait": "32",
    "outdoor": "33",
    "indoor": "34",
}
CATEGORY_OFFSETS = {
    "anniversary": 0,
    "portrait": 4,
    "outdoor": 25,
    "indoor": 48,
}


def sha256(path: Path, data: bytes | None = None) -> str:
    digest = hashlib.sha256()
    if data is None:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        digest.update(data)
    return digest.hexdigest()


def clean_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", "", value))
    value = re.sub(r"\s+", " ", value).strip()
    return value


def title_without_by(value: str) -> str:
    value = clean_text(value)
    return re.sub(r"^by\s*", "", value, flags=re.IGNORECASE).strip()


def parse_page(path: Path, category: str, lcid: str) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r'<li\s+data-small="([^"]+)"(.*?)</li>', source, flags=re.DOTALL
    )
    records: list[dict] = []
    for index, (preview_url, block) in enumerate(blocks, start=1):
        href = re.search(r'<a\s+href="([^"]+)"', block)
        onclick = re.search(r"AddDownload\((\d+),\s*'([^']*)'\)", block)
        title = re.search(r"<h2>(.*?)</h2>", block, flags=re.DOTALL)
        description = re.search(
            r'<p\s+class="dot">(.*?)</p>', block, flags=re.DOTALL
        )
        if not (href and onclick and title and description):
            raise RuntimeError(
                f"无法解析 {path} 第 {index} 个官方卡片，已停止；请人工检查页面快照"
            )
        records.append(
            {
                "category": category,
                "lcid": lcid,
                "ordinal": index,
                "official_title_raw": clean_text(title.group(1)),
                "official_title": title_without_by(title.group(1)),
                "official_description": clean_text(description.group(1)),
                "preview_url": (
                    "http://www.panasonicshuma.cn" + preview_url
                    if preview_url.startswith("/")
                    else preview_url
                ),
                "download_url": html.unescape(href.group(1)),
                "remote_item_id": int(onclick.group(1)),
                "download_path": onclick.group(2),
            }
        )
    return records


def local_match(record: dict, entries: list[dict]) -> dict:
    title = record["official_title"]
    candidates = []
    for entry in entries:
        if entry["category"] != record["category"]:
            continue
        name = entry["name_zh"]
        author = entry["author"]["name_zh"]
        if title.endswith(name) and author in title:
            candidates.append(entry)
    if len(candidates) != 1:
        raise RuntimeError(
            "官方卡片无法唯一匹配本地条目，已停止："
            + json.dumps(record, ensure_ascii=False)
            + f" candidates={len(candidates)}"
        )
    return candidates[0]


def variant_for(entry: dict, path: Path) -> str:
    stem = path.stem.lower()
    if stem.endswith("_cold") or stem.endswith("-cold"):
        return "cold"
    if stem.endswith("_warm") or stem.endswith("-warm"):
        return "warm"
    if entry["id"] == "millennium-echo" and path.name == "millennium-echo.cube":
        return "cold"
    return "default"


def archive_path(
    snapshot: Path, category: str, ordinal: int, lcid: str, download_url: str
) -> Path:
    suffix = Path(unquote(download_url.split("?", 1)[0])).suffix.lower() or ".bin"
    global_ordinal = CATEGORY_OFFSETS[category] + ordinal
    path = snapshot / "raw-archives" / f"{global_ordinal:02d}-{lcid}{suffix}"
    if not path.exists():
        raise RuntimeError(f"缺少官方原始压缩包快照：{path}")
    return path


def archive_member_by_hash(archive: Path, target_hash: str) -> tuple[str, bytes]:
    if not zipfile.is_zipfile(archive):
        raise RuntimeError(f"需要从非 ZIP 压缩包恢复文件，暂无法自动处理：{archive}")
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            if info.is_dir() or info.filename.startswith("__MACOSX/"):
                continue
            data = zipped.read(info)
            if sha256(archive, data) == target_hash:
                return info.filename, data
    raise RuntimeError(f"官方压缩包中找不到目标 SHA-256：{archive} {target_hash}")


def make_file_record(
    canonical_path: Path,
    original_name: str,
    variant: str,
    source_path: str,
    source_archive_url: str,
    source_archive_snapshot: str,
) -> dict:
    return {
        "variant": variant,
        "format": canonical_path.suffix.lower().lstrip("."),
        "normalized_filename": canonical_path.name,
        "canonical_path": canonical_path.relative_to(ROOT).as_posix(),
        "original_filename": original_name,
        "source_path": source_path,
        "size": canonical_path.stat().st_size,
        "sha256": sha256(canonical_path),
        "source_archive_url": source_archive_url,
        "source_archive_snapshot": source_archive_snapshot,
    }


def build(snapshot_id: str) -> dict:
    snapshot = ROOT / "data" / "snapshots" / snapshot_id
    pages = snapshot / "source-pages"
    if not pages.is_dir():
        raise RuntimeError(f"官方页面快照目录不存在：{pages}")

    database = json.loads((ROOT / "luts" / "luts.json").read_text(encoding="utf-8"))
    entries = database["luts"]
    cards: list[dict] = []
    for category, lcid in CATEGORY_PAGES.items():
        cards.extend(parse_page(pages / f"lcid-{lcid}.html", category, lcid))
    if len(cards) != 57:
        raise RuntimeError(f"官方快照卡片数为 {len(cards)}，预期 57；已停止")

    grouped: dict[str, dict] = {}
    for card in cards:
        entry = local_match(card, entries)
        canonical_id = entry["id"]
        bucket = grouped.setdefault(
            canonical_id,
            {
                "canonical_id": canonical_id,
                "name_zh": entry["name_zh"],
                "author": entry["author"],
                "category": entry["category"],
                "category_zh": entry["category_zh"],
                "tags": entry.get("tags", []),
                "official_descriptions": [],
                "source_items": [],
                "files": [],
                "previews": [],
            },
        )
        if card["official_description"] not in bucket["official_descriptions"]:
            bucket["official_descriptions"].append(card["official_description"])
        source_archive = archive_path(
            snapshot,
            card["category"],
            card["ordinal"],
            card["lcid"],
            card["download_url"],
        )
        bucket["source_items"].append(
            {
                "remote_item_id": card["remote_item_id"],
                "source_page": f"http://www.panasonicshuma.cn/RealtimeLUTLibrary/list.aspx?lcid={card['lcid']}",
                "download_url": card["download_url"],
                "download_path": card["download_path"],
                "preview_url": card["preview_url"],
                "official_title_raw": card["official_title_raw"],
                "official_description": card["official_description"],
                "archive_snapshot": source_archive.relative_to(ROOT).as_posix(),
                "archive_sha256": sha256(source_archive),
            }
        )
        bucket["previews"].append(
            {
                "source_item_id": card["remote_item_id"],
                "preview_url": card["preview_url"],
                "status": "not-retrieved-in-snapshot",
            }
        )

    # The official site publishes two cards with the same title, but they are
    # intentionally exposed as two independent canonical LUTs: Cold and Warm.
    base_millennium = grouped.pop("millennium-echo", None)
    if base_millennium is None or len(base_millennium["source_items"]) != 2:
        raise RuntimeError("千禧回声未找到两个官方来源卡片，已停止")
    for variant, source_index in (("cold", 0), ("warm", 1)):
        split = deepcopy(base_millennium)
        split["legacy_entry_id"] = "millennium-echo"
        split["canonical_id"] = f"millennium-echo-{variant}"
        split["name_zh"] = f"千禧回声 {variant.title()}"
        split["source_items"] = [base_millennium["source_items"][source_index]]
        split["official_descriptions"] = [
            base_millennium["source_items"][source_index]["official_description"]
        ]
        split["files"] = [
            file
            for file in base_millennium["files"]
            if file.get("variant") == variant
        ]
        split["previews"] = [
            {
                **preview,
                "source_item_id": base_millennium["source_items"][source_index][
                    "remote_item_id"
                ],
            }
            for preview in base_millennium["previews"]
            if preview.get("source_item_id")
            == base_millennium["source_items"][source_index]["remote_item_id"]
            or preview.get("variant") == variant
        ]
        grouped[split["canonical_id"]] = split

    canonical_root = ROOT / "data" / "canonical"
    lut_root = canonical_root / "luts"
    manifest_root = canonical_root / "manifests"
    preview_root = canonical_root / "previews"
    for directory in (lut_root, manifest_root, preview_root):
        directory.mkdir(parents=True, exist_ok=True)

    canonical_files = 0
    preview_overrides_path = snapshot / "preview-overrides.json"
    preview_overrides = (
        json.loads(preview_overrides_path.read_text(encoding="utf-8"))
        if preview_overrides_path.exists()
        else {}
    )
    # Copy all known local files under normalized names.
    for bucket in grouped.values():
        legacy_entry_id = bucket.get("legacy_entry_id", bucket["canonical_id"])
        entry = next(e for e in entries if e["id"] == legacy_entry_id)
        source_dir = ROOT / "luts" / entry["category"] / entry["id"]
        if not source_dir.is_dir():
            raise RuntimeError(f"canonical 条目的本地目录不存在：{source_dir}")
        target_dir = lut_root / entry["category"] / entry["author"]["slug"] / bucket["canonical_id"]
        target_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(source_dir.iterdir()):
            if source.suffix.lower() not in {".cube", ".vlt"}:
                continue
            variant = variant_for(entry, source)
            if legacy_entry_id == "millennium-echo" and variant != bucket["canonical_id"].rsplit("-", 1)[-1]:
                continue
            file_variant_suffix = "default" if legacy_entry_id == "millennium-echo" else variant
            target = target_dir / (
                f"{entry['category']}--{entry['author']['slug']}--{bucket['canonical_id']}--{file_variant_suffix}{source.suffix.lower()}"
            )
            shutil.copy2(source, target)
            bucket["files"].append(
                make_file_record(
                    target,
                    source.name,
                    variant,
                    source.relative_to(ROOT).as_posix(),
                    bucket["source_items"][0]["download_url"],
                    bucket["source_items"][0]["archive_snapshot"],
                )
            )
            canonical_files += 1

        # Preserve the current local preview as a canonical display asset.
        preview_ref = entry.get("preview_image")
        if preview_ref and not (
            legacy_entry_id == "millennium-echo"
            and bucket["canonical_id"].endswith("-warm")
        ):
            preview_source = ROOT / "luts" / preview_ref
            if preview_source.exists():
                preview_stem = bucket["canonical_id"]
                preview_target = preview_root / f"{preview_stem}{preview_source.suffix.lower()}"
                shutil.copy2(preview_source, preview_target)
                bucket["previews"].append(
                    {
                        "source_item_id": bucket["source_items"][0]["remote_item_id"],
                        "variant": bucket["canonical_id"].rsplit("-", 1)[-1]
                        if legacy_entry_id == "millennium-echo"
                        else "default",
                        "canonical_path": preview_target.relative_to(ROOT).as_posix(),
                        "status": "local-existing-preview",
                    }
                )

        for override in preview_overrides.get(legacy_entry_id, []):
            if legacy_entry_id == "millennium-echo" and override["variant"] != bucket["canonical_id"].rsplit("-", 1)[-1]:
                continue
            source = ROOT / override["snapshot_path"]
            if not source.exists():
                raise RuntimeError(f"预览图 override 不存在：{source}")
            if sha256(source) != override["sha256"]:
                raise RuntimeError(f"预览图 override SHA-256 不匹配：{source}")
            target = preview_root / f"{bucket['canonical_id']}{source.suffix.lower()}"
            shutil.copy2(source, target)
            bucket["previews"].append(
                {
                    "source_item_id": bucket["source_items"][0]["remote_item_id"],
                    "variant": override["variant"],
                    "source_url": override["source_url"],
                    "canonical_path": target.relative_to(ROOT).as_posix(),
                    "sha256": override["sha256"],
                    "status": override["status"],
                }
            )

    # Restore the confirmed missing warm variant from the official snapshot.
    millennium = grouped["millennium-echo-warm"]
    target_hash = "6880f3ec2f7e5b68e6a682ea506240799803e29db44a43cd3763936bf7f29740"
    if not any(f["sha256"] == target_hash for f in millennium["files"]):
        source_archive = archive_path(
            snapshot,
            "anniversary",
            2,
            "113",
            millennium["source_items"][0]["download_url"],
        )
        original_name, data = archive_member_by_hash(source_archive, target_hash)
        target_dir = lut_root / "anniversary" / "desong" / "millennium-echo-warm"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "anniversary--desong--millennium-echo-warm--default.cube"
        target.write_bytes(data)
        record = make_file_record(
            target,
            original_name,
            "warm",
            f"{source_archive.relative_to(ROOT).as_posix()}::{original_name}",
            millennium["source_items"][0]["download_url"],
            source_archive.relative_to(ROOT).as_posix(),
        )
        if record["sha256"] != target_hash:
            raise RuntimeError("恢复的 warm 文件 SHA-256 不匹配，已停止")
        millennium["files"].append(record)
        canonical_files += 1

    for bucket in grouped.values():
        bucket["source_items_count"] = len(bucket["source_items"])
        bucket["merged_duplicate_source_items"] = max(0, len(bucket["source_items"]) - 1)
        bucket["display_description"] = bucket["official_descriptions"][0]
        bucket["schema_version"] = "1.0"
        manifest_path = manifest_root / f"{bucket['canonical_id']}.json"
        manifest_path.write_text(
            json.dumps(bucket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # Build the database consumed by the static site.  The legacy luts.json is
    # intentionally left untouched so old links remain recoverable.
    web_entries: list[dict] = []
    for bucket in grouped.values():
        legacy_entry_id = bucket.get("legacy_entry_id", bucket["canonical_id"])
        original = next(e for e in entries if e["id"] == legacy_entry_id)
        item = json.loads(json.dumps(original, ensure_ascii=False))
        item["id"] = bucket["canonical_id"]
        item["name_zh"] = bucket["name_zh"]
        item["official_name"] = bucket["name_zh"]
        item["display_name"] = bucket["name_zh"]
        item["official_descriptions"] = bucket["official_descriptions"]
        item["display_description"] = bucket["display_description"]
        item["source_items"] = bucket["source_items"]
        item["canonical_id"] = bucket["canonical_id"]
        # Creator-machine absolute paths may be embedded by LUT exporters. They
        # remain recoverable from raw archives but are never published.
        internal = item.get("internal", {})
        color_profile = internal.get("color_profile")
        if isinstance(color_profile, str) and (
            color_profile.startswith(("/Users/", "/Volumes/"))
            or re.match(r"^[A-Za-z]:\\", color_profile)
        ):
            internal["color_profile"] = None
        item["files"] = []
        for file_record in bucket["files"]:
            old = next(
                (
                    f
                    for f in original.get("files", [])
                    if f.get("name") == file_record["original_filename"]
                ),
                {},
            )
            file_entry = {
                "name": file_record["normalized_filename"],
                "type": file_record["format"],
                "size": file_record["size"],
                "sha256": file_record["sha256"],
                "variant": file_record["variant"],
                "public_path": file_record["canonical_path"].replace(
                    "data/", "", 1
                ),
                "original_filename": file_record["original_filename"],
                "lut_3d_size": old.get("lut_3d_size"),
                "domain_min": old.get("domain_min"),
                "domain_max": old.get("domain_max"),
                "generator": old.get("generator"),
                "copyright": old.get("copyright"),
                "title": old.get("title"),
            }
            item["files"].append(file_entry)
        preview_records = [p for p in bucket["previews"] if p.get("canonical_path")]
        preview = preview_records[0] if preview_records else None
        item["preview_images"] = [
            {
                "variant": p.get("variant", "default"),
                "path": p["canonical_path"].replace("data/", "", 1),
                "source_url": p.get("source_url"),
                "status": p.get("status"),
            }
            for p in preview_records
        ]
        item["preview_image"] = (
            preview["canonical_path"].replace("data/", "", 1)
            if preview
            else ""
        )
        item["total_size"] = sum(f["size"] for f in item["files"])
        web_entries.append(item)

    merged_count = sum(
        max(0, len(item["source_items"]) - 1) for item in grouped.values()
    )
    duplicate_groups: dict[str, list[str]] = {}
    for bucket in grouped.values():
        for file in bucket["files"]:
            duplicate_groups.setdefault(file["sha256"], []).append(
                file["canonical_path"]
            )
    duplicate_groups = {
        digest: paths for digest, paths in duplicate_groups.items() if len(paths) > 1
    }
    categories = []
    for category in database["categories"]:
        count = sum(1 for item in web_entries if item["category"] == category["id"])
        categories.append({**category, "lut_count": count})
    authors = []
    for author in database["authors"]:
        count = sum(
            1 for item in web_entries if item["author"]["slug"] == author["slug"]
        )
        authors.append({**author, "lut_count": count})
    web_database = {
        "meta": {
            "updated": snapshot_id,
            "total_luts": len(web_entries),
            "total_files": canonical_files,
            "official_card_count": len(cards),
        "merged_duplicate_card_count": merged_count,
        "duplicate_content_groups": duplicate_groups,
            "source": "http://www.panasonicshuma.cn/RealtimeLUTLibrary/list.aspx",
        },
        "categories": categories,
        "authors": authors,
        "tags": database["tags"],
        "generators": database["generators"],
        "lut_3d_sizes": database["lut_3d_sizes"],
        "formats": database["formats"],
        "luts": sorted(web_entries, key=lambda x: x["id"]),
    }
    (canonical_root / "luts.json").write_text(
        json.dumps(web_database, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    snapshot_manifest = {
        "schema_version": "1.0",
        "snapshot_id": snapshot_id,
        "pages": [
            {
                "lcid": lcid,
                "category": category,
                "source_url": f"http://www.panasonicshuma.cn/RealtimeLUTLibrary/list.aspx?lcid={lcid}",
                "path": (pages / f"lcid-{lcid}.html").relative_to(ROOT).as_posix(),
                "sha256": sha256(pages / f"lcid-{lcid}.html"),
            }
            for category, lcid in CATEGORY_PAGES.items()
        ],
        "archives": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "size": path.stat().st_size,
            }
            for path in sorted((snapshot / "raw-archives").iterdir())
            if path.is_file()
        ],
        "preview_overrides": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "size": path.stat().st_size,
            }
            for path in [snapshot / "preview-overrides.json"]
            + sorted((snapshot / "source-previews").glob("*"))
            if path.is_file()
        ],
    }
    (snapshot / "manifest.json").write_text(
        json.dumps(snapshot_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    review_dir = ROOT / "data" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "pending.json").write_text(
        json.dumps({"schema_version": "1.0", "items": []}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    # Camera aliases are deliberately separate from canonical names.  They are
    # short, ASCII-only, deterministic from content, and therefore stable even
    # when the display name is corrected later.
    camera_dir = ROOT / "data" / "camera"
    camera_dir.mkdir(parents=True, exist_ok=True)
    category_prefix = {"anniversary": "A", "portrait": "P", "outdoor": "O", "indoor": "I"}
    variant_code = {"cold": "C", "warm": "W", "default": "D"}
    aliases: list[dict] = []
    used_aliases: set[str] = set()
    for bucket in sorted(grouped.values(), key=lambda item: item["canonical_id"]):
        for file in sorted(bucket["files"], key=lambda item: item["normalized_filename"]):
            alias = (
                category_prefix[bucket["category"]]
                + file["sha256"][:5].upper()
                + variant_code.get(file["variant"], "X")
                + "."
                + file["format"].upper()
            )
            if alias in used_aliases:
                raise RuntimeError(f"相机别名冲突：{alias}，已停止")
            used_aliases.add(alias)
            aliases.append(
                {
                    "alias": alias,
                    "canonical_id": bucket["canonical_id"],
                    "variant": file["variant"],
                    "format": file["format"],
                    "canonical_path": file["canonical_path"],
                    "sha256": file["sha256"],
                }
            )
    (camera_dir / "aliases.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "targets": ["S9", "S5M2", "S5M2X", "G9M2", "GH7"],
                "aliases": aliases,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    global_manifest = {
        "schema_version": "1.0",
        "snapshot_id": snapshot_id,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_pages": [
            f"http://www.panasonicshuma.cn/RealtimeLUTLibrary/list.aspx?lcid={lcid}"
            for lcid in CATEGORY_PAGES.values()
        ],
        "official_card_count": len(cards),
        "canonical_lut_count": len(grouped),
        "canonical_file_count": canonical_files,
        "merged_duplicate_card_count": sum(
            max(0, len(item["source_items"]) - 1) for item in grouped.values()
        ),
        "duplicate_content_groups": duplicate_groups,
        "review_queue": [],
        "canonical_manifests": [
            f"data/canonical/manifests/{key}.json" for key in sorted(grouped)
        ],
    }
    (canonical_root / "manifest.json").write_text(
        json.dumps(global_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return global_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="2026-08-24")
    args = parser.parse_args()
    result = build(args.snapshot)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
