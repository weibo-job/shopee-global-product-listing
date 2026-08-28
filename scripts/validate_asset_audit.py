#!/usr/bin/env python3
"""Validate every localized asset and emit a file-hash-bound audit receipt."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
GROUP_DIRS = {"main": "01_主图", "detail": "02_详情图", "sku": "03_SKU图"}
REQUIRED_BOOLS = (
    "unrelated_content", "edge_cut", "neighbor_fragment",
    "standalone_understanding", "content_subject_match",
    "product_form_verified", "sku_mapping_verified", "subject_overlap_verified",
)
VISION_OCR = Path(__file__).with_name("vision_ocr.swift")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_file(package_dir, value):
    path = Path(value or "").expanduser()
    return (path if path.is_absolute() else package_dir / path).resolve()


def decoded_equal(source, final):
    with Image.open(source) as a, Image.open(final) as b:
        return a.size == b.size and ImageChops.difference(
            a.convert("RGB"), b.convert("RGB")).getbbox() is None


def unchanged_outside_mask(source, final, mask):
    with Image.open(source) as a, Image.open(final) as b, Image.open(mask) as m:
        a, b = a.convert("RGB"), b.convert("RGB")
        if a.size != b.size or m.size != a.size:
            return False
        outside = ImageOps.invert(m.convert("L")).convert("RGB")
        return ImageChops.multiply(ImageChops.difference(a, b),
                                   outside).getbbox() is None


def image_files(directory):
    if not directory.is_dir():
        return set()
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    return {str(path.resolve()) for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in extensions}


def vision_ocr(paths):
    ordered = sorted({str(Path(path).resolve()) for path in paths})
    if not VISION_OCR.is_file():
        raise RuntimeError(f"Vision OCR helper missing: {VISION_OCR}")
    environment = os.environ.copy()
    module_cache = "/private/tmp/shopee-global-product-listing-swift-module-cache"
    environment["CLANG_MODULE_CACHE_PATH"] = module_cache
    environment["SWIFT_MODULECACHE_PATH"] = module_cache
    result = subprocess.run(
        ["swift", str(VISION_OCR), *ordered], text=True, capture_output=True,
        env=environment)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"Vision OCR failed: {detail}")
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Vision OCR returned invalid JSON: {exc}") from exc
    for path in ordered:
        record = output.get(path)
        if not isinstance(record, dict):
            raise RuntimeError(f"Vision OCR omitted result for {path}")
        if record.get("error"):
            raise RuntimeError(f"Vision OCR failed for {path}: {record['error']}")
        if not isinstance(record.get("text"), str):
            raise RuntimeError(f"Vision OCR returned invalid text for {path}")
    return {path: output[path]["text"] for path in ordered}


def validate(audit_path):
    audit_path = Path(audit_path).expanduser().resolve()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    package_dir = Path(audit.get("package_dir") or audit_path.parent.parent).expanduser().resolve()
    errors = []
    files = audit.get("files") or []
    if audit.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    counts = Counter(item.get("asset_group") for item in files)
    expected = audit.get("expected_counts") or {}
    for group in GROUP_DIRS:
        if counts[group] != int(expected.get(group, -1)):
            errors.append(f"{group} audit count does not match expected_counts")
    if counts["main"] < 1 or counts["main"] > 9:
        errors.append("main image count must be 1..9")
    if counts["detail"] < 6 or counts["detail"] > 12:
        errors.append("detail image count must be 6..12")
    sku_counts = [audit.get("source_sku_count"), audit.get("package_sku_count"),
                  audit.get("request_model_count")]
    if len(set(sku_counts)) != 1 or sku_counts[0] != counts["sku"]:
        errors.append("source/package/request SKU counts do not match audited SKU files")

    final_by_group = {group: set() for group in GROUP_DIRS}
    receipt_files = []
    detail_widths = set()
    ocr_targets = []
    for index, item in enumerate(files, 1):
        label = f"file[{index}]"
        group = item.get("asset_group")
        if group not in GROUP_DIRS:
            errors.append(f"{label}: invalid asset_group")
            continue
        source = resolve_file(package_dir, item.get("source_file"))
        final = resolve_file(package_dir, item.get("final_file"))
        final_by_group[group].add(str(final))
        if not source.is_file() or not final.is_file():
            errors.append(f"{label}: source or final file missing")
            continue
        ocr_targets.append((label, str(final)))
        source_hash, final_hash = sha256(source), sha256(final)
        if item.get("source_sha256") != source_hash:
            errors.append(f"{label}: source_sha256 mismatch")
        if item.get("final_sha256") != final_hash:
            errors.append(f"{label}: final_sha256 mismatch")
        if item.get("audit_status") != "PASS":
            errors.append(f"{label}: audit_status is not PASS")
        for field in REQUIRED_BOOLS:
            if not isinstance(item.get(field), bool):
                errors.append(f"{label}: {field} must be boolean")
        if item.get("unrelated_content") or item.get("edge_cut") or item.get("neighbor_fragment"):
            errors.append(f"{label}: visual integrity flag failed")
        for field in ("standalone_understanding", "content_subject_match",
                      "product_form_verified", "sku_mapping_verified",
                      "subject_overlap_verified"):
            if item.get(field) is not True:
                errors.append(f"{label}: {field} is not verified")
        if item.get("claim_check") != "PASS":
            errors.append(f"{label}: claim_check is not PASS")
        if CJK.search(str(item.get("final_ocr_text") or "")):
            errors.append(f"{label}: final OCR still contains CJK")

        has_text = item.get("descriptive_text_present") is True
        if has_text:
            if decoded_equal(source, final):
                errors.append(f"{label}: text-bearing final image is pixel-identical to source")
            mask_value = item.get("text_mask_file")
            if not mask_value:
                errors.append(f"{label}: text-bearing image requires text_mask_file")
            else:
                mask = resolve_file(package_dir, mask_value)
                if not mask.is_file() or not unchanged_outside_mask(source, final, mask):
                    errors.append(f"{label}: pixels changed outside the registered text mask")
        elif not decoded_equal(source, final):
            errors.append(f"{label}: text-free image must preserve decoded source pixels")

        with Image.open(final) as image:
            width, height = image.size
        if width < 700 or width / height < 0.5:
            errors.append(f"{label}: dimensions or aspect ratio fail")
        if group == "main" and width != height:
            errors.append(f"{label}: main image must be square")
        if group == "detail":
            detail_widths.add(width)
        receipt_files.append({"asset_group": group, "final_file": str(final),
                              "final_sha256": final_hash})

    try:
        detected_text = vision_ocr(path for _label, path in ocr_targets)
    except (OSError, RuntimeError) as exc:
        errors.append(str(exc))
    else:
        for label, path in ocr_targets:
            if CJK.search(detected_text[path]):
                errors.append(f"{label}: Vision OCR detected CJK in final image")

    if len(detail_widths) != 1:
        errors.append("all detail images must use one common width")
    english_dir = package_dir / "英文版"
    for group, dirname in GROUP_DIRS.items():
        actual = image_files(english_dir / dirname)
        if actual != final_by_group[group]:
            errors.append(f"{group} English directory does not exactly match audited files")
    return audit_path, audit, receipt_files, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_json")
    parser.add_argument("--receipt-out")
    args = parser.parse_args()
    try:
        audit_path, _audit, files, errors = validate(args.audit_json)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [f"invalid audit manifest: {exc}"]
        audit_path, files = Path(args.audit_json).expanduser().resolve(), []
    result = {"ok": not errors, "errors": errors, "audited_file_count": len(files)}
    if not errors and args.receipt_out:
        receipt = {"schema_version": 1, "ok": True, "audit_path": str(audit_path),
                   "audit_sha256": sha256(audit_path), "files": files}
        out = Path(args.receipt_out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        result["receipt"] = str(out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
