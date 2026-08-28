#!/usr/bin/env python3
"""Verify a package-bound localization audit receipt before Shopee writes."""

import hashlib
import json
from pathlib import Path


WRITE_ACTIONS = {"create", "update", "tier_variations", "upload_image"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_receipt(receipt_path, requested_final_file=None):
    path = Path(receipt_path).expanduser().resolve()
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid audit receipt: {exc}") from exc
    if receipt.get("ok") is not True:
        raise ValueError("audit receipt is not PASS")
    audit_path = Path(receipt.get("audit_path") or "").expanduser().resolve()
    if not audit_path.is_file() or sha256(audit_path) != receipt.get("audit_sha256"):
        raise ValueError("audit manifest is missing or changed after receipt creation")
    bound = {}
    for item in receipt.get("files") or []:
        final = Path(item.get("final_file") or "").expanduser().resolve()
        expected = item.get("final_sha256")
        if not final.is_file() or not expected or sha256(final) != expected:
            raise ValueError(f"audited final file is missing or changed: {final}")
        bound[str(final)] = expected
    if not bound:
        raise ValueError("audit receipt contains no bound files")
    if requested_final_file:
        requested = str(Path(requested_final_file).expanduser().resolve())
        if requested not in bound:
            raise ValueError(f"requested upload is not in audited PASS files: {requested}")
    return receipt


def require_write_receipt(params, operation):
    if operation not in WRITE_ACTIONS:
        return None
    receipt_path = params.get("audit_receipt_path")
    if not receipt_path:
        raise ValueError(f"{operation} requires audit_receipt_path")
    requested = params.get("audit_final_file") if operation == "upload_image" else None
    if operation == "upload_image" and not requested:
        raise ValueError("upload_image requires audit_final_file bound to the receipt")
    return verify_receipt(receipt_path, requested)

