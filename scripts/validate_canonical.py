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
ANNOTATIONS = ROOT / "data" / "annotations"
ALLOWED_PHOTO_STYLES = {
    "STD", "VIVD", "NAT", "FLAT", "LAND", "PORT", "LCLASN", "MONO",
    "LMONO", "LMONOD", "LMONOS", "LEICAMONO", "CNEA2", "CNED2", "CNEV2",
    "709L", "VLOG", "STDHLG", "MONOHLG", "2100HLG", "2100HLGF",
}


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


def lumix_photo_style(path: Path) -> str | None:
    if path.suffix.lower() != ".cube":
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("#LUMIXPHOTOSTYLE "):
            return stripped.split(None, 1)[1].split()[0].upper()
    return None


def main() -> int:
    manifest_path = CANONICAL / "manifest.json"
    database_path = CANONICAL / "luts.json"
    if not manifest_path.exists() or not database_path.exists():
        print("missing canonical manifest or database", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database = json.loads(database_path.read_text(encoding="utf-8"))
    profiles_path = ANNOTATIONS / "preview-profiles.json"
    errors: list[str] = []
    warnings: list[str] = []

    if not profiles_path.exists():
        errors.append("missing preview profile annotation manifest")
        profiles = {}
    else:
        profiles = json.loads(profiles_path.read_text(encoding="utf-8")).get("entries", {})

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
        source_previews = snapshot_manifest.get("source_previews", [])
        if len(source_previews) != 57:
            errors.append(
                f"snapshot must contain 57 source previews, found {len(source_previews)}"
            )
        rar_extracts = snapshot_manifest.get("rar_extracts", [])
        if len(rar_extracts) != 2:
            errors.append(
                f"snapshot must contain 2 RAR extracts, found {len(rar_extracts)}"
            )
        for evidence in source_previews + rar_extracts:
            path = ROOT / evidence["path"]
            if not path.exists():
                errors.append(f"missing derived snapshot evidence: {path}")
            elif file_hash(path) != evidence["sha256"]:
                errors.append(f"derived snapshot evidence hash mismatch: {path}")

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
        profile = item.get("base_photo_style")
        expected_profile = profiles.get(lut_id)
        if not isinstance(profile, dict):
            errors.append(f"missing base photo style object: {lut_id}")
        elif not expected_profile:
            errors.append(f"missing preview profile annotation: {lut_id}")
        elif any(profile.get(key) != expected_profile.get(key) for key in ("raw_label", "profile_tag", "profile_name_zh")):
            errors.append(f"database/profile annotation mismatch: {lut_id}")
        elif profile.get("profile_tag") not in ALLOWED_PHOTO_STYLES:
            errors.append(f"invalid preview profile tag: {lut_id}={profile.get('profile_tag')}")
        elif profile.get("camera_effective_profile_tag") not in ALLOWED_PHOTO_STYLES:
            errors.append(
                f"invalid effective camera profile tag: {lut_id}={profile.get('camera_effective_profile_tag')}"
            )
        preview_paths = {p.get("path") for p in item.get("preview_images", [])}
        if item.get("preview_image") and item["preview_image"] not in preview_paths:
            errors.append(f"primary preview missing from preview_images: {lut_id}")
        for preview_path in preview_paths:
            path = ROOT / "data" / preview_path
            if not path.exists():
                errors.append(f"missing canonical preview: {path}")
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
                actual_profile = lumix_photo_style(path)
                recorded_profile = file.get("lumix_photo_style")
                if actual_profile != recorded_profile:
                    errors.append(f"LUMIXPHOTOSTYLE metadata mismatch: {path}")
                if actual_profile and actual_profile not in ALLOWED_PHOTO_STYLES:
                    errors.append(f"invalid LUMIXPHOTOSTYLE tag: {path}={actual_profile}")
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
