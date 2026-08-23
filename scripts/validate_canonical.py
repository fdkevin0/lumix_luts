#!/usr/bin/env python3
"""Validate the canonical LUT tree and its immutable snapshot manifest."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cube_info(path: Path) -> tuple[int | None, int]:
    size = None
    points = 0
    in_data = False
    with path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = re.match(r"LUT_3D_SIZE\s+(\d+)", stripped)
            if match:
                size = int(match.group(1))
                continue
            if stripped.startswith(("DOMAIN_MIN", "DOMAIN_MAX", "TITLE")):
                continue
            if in_data or re.match(r"[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+$", stripped):
                in_data = True
                points += 1
    return size, points


def main() -> int:
    manifest_path = CANONICAL / "manifest.json"
    database_path = CANONICAL / "luts.json"
    if not manifest_path.exists() or not database_path.exists():
        print("missing canonical manifest or database", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database = json.loads(database_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    if manifest["official_card_count"] != 57:
        errors.append(f"official card count={manifest['official_card_count']} expected 57")
    if manifest["canonical_lut_count"] != len(database["luts"]):
        errors.append("manifest/database LUT count mismatch")
    if manifest["canonical_file_count"] != sum(len(item["files"]) for item in database["luts"]):
        errors.append("manifest/database file count mismatch")

    snapshot_manifest_path = ROOT / "data" / "snapshots" / manifest["snapshot_id"] / "manifest.json"
    if not snapshot_manifest_path.exists():
        errors.append(f"missing snapshot manifest: {snapshot_manifest_path}")
    else:
        snapshot_manifest = json.loads(snapshot_manifest_path.read_text(encoding="utf-8"))
        if len(snapshot_manifest.get("pages", [])) != 4:
            errors.append("snapshot must contain four official category pages")
        if len(snapshot_manifest.get("archives", [])) != 57:
            errors.append("snapshot must contain 57 official archives")
        for evidence in snapshot_manifest.get("pages", []) + snapshot_manifest.get("archives", []):
            path = ROOT / evidence["path"]
            if not path.exists():
                errors.append(f"missing snapshot evidence: {path}")
            elif file_hash(path) != evidence["sha256"]:
                errors.append(f"snapshot evidence hash mismatch: {path}")
        for evidence in snapshot_manifest.get("preview_overrides", []):
            path = ROOT / evidence["path"]
            if not path.exists():
                errors.append(f"missing preview evidence: {path}")
            elif file_hash(path) != evidence["sha256"]:
                errors.append(f"preview evidence hash mismatch: {path}")

    review_path = ROOT / "data" / "review" / "pending.json"
    if not review_path.exists():
        errors.append("missing review queue")
    else:
        review = json.loads(review_path.read_text(encoding="utf-8"))
        if review.get("items"):
            errors.append(f"review queue has {len(review['items'])} pending item(s)")

    seen_ids: set[str] = set()
    seen_hashes: dict[str, list[str]] = {}
    file_count = 0
    for item in database["luts"]:
        lut_id = item["id"]
        if lut_id in seen_ids:
            errors.append(f"duplicate canonical id: {lut_id}")
        seen_ids.add(lut_id)
        for file in item["files"]:
            file_count += 1
            path = ROOT / "data" / file["public_path"]
            if not re.fullmatch(
                r"[a-z0-9]+(?:--[a-z0-9-]+){3}\.(?:cube|vlt)", path.name
            ):
                errors.append(f"invalid canonical filename: {path.name}")
            if not path.exists():
                errors.append(f"missing canonical file: {path}")
                continue
            actual_hash = file_hash(path)
            if actual_hash != file["sha256"]:
                errors.append(f"sha256 mismatch: {path}")
            if path.stat().st_size != file["size"]:
                errors.append(f"size mismatch: {path}")
            seen_hashes.setdefault(actual_hash, []).append(str(path))
            if path.suffix.lower() == ".cube":
                try:
                    size, points = cube_info(path)
                    if size is None:
                        errors.append(f"missing LUT_3D_SIZE: {path}")
                    elif points != size**3:
                        errors.append(f"cube point count {points} != {size}^3: {path}")
                except UnicodeDecodeError:
                    errors.append(f"cube is not UTF-8: {path}")
            elif path.suffix.lower() == ".vlt":
                text = path.read_text(encoding="utf-8", errors="replace")
                if "LUT_3D_SIZE" not in text:
                    warnings.append(f"vlt has no LUT_3D_SIZE declaration: {path}")

    for digest, paths in sorted(seen_hashes.items()):
        if len(paths) > 1:
            warnings.append("duplicate content group " + digest[:16] + ": " + ", ".join(paths))

    if file_count != manifest["canonical_file_count"]:
        errors.append("canonical file count mismatch")

    aliases_path = ROOT / "data" / "camera" / "aliases.json"
    if not aliases_path.exists():
        errors.append("missing camera alias manifest")
    else:
        aliases = json.loads(aliases_path.read_text(encoding="utf-8")).get("aliases", [])
        names = [entry["alias"] for entry in aliases]
        if len(names) != file_count:
            errors.append("camera alias/file count mismatch")
        if len(names) != len(set(names)):
            errors.append("duplicate camera alias")
        for name in names:
            if not re.fullmatch(r"[A-Z0-9]{1,8}\.(?:CUBE|VLT)", name):
                errors.append(f"invalid camera alias: {name}")
    print(f"Validated {len(seen_ids)} canonical LUT(s), {file_count} file(s)")
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for warning in warnings:
            print("  !", warning)
    if errors:
        print(f"Errors ({len(errors)}):")
        for error in errors:
            print("  x", error)
        return 1
    print("Canonical validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
