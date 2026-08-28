# Localization Audit Lock

Read this reference when preparing the final English image package or before any Shopee media/create/update write.

## Required file

Save `英文版/localization_audit.json` with this shape:

```json
{
  "schema_version": 1,
  "package_dir": "/absolute/product/package",
  "expected_counts": {"main": 5, "detail": 12, "sku": 2},
  "source_sku_count": 2,
  "package_sku_count": 2,
  "request_model_count": 2,
  "files": [
    {
      "asset_group": "main",
      "source_order_or_sku": "001",
      "source_file": "/absolute/product/package/原图/01_主图/001.png",
      "final_file": "/absolute/product/package/英文版/01_主图/001.png",
      "source_sha256": "...",
      "final_sha256": "...",
      "descriptive_text_present": true,
      "localization_method": "pillow_text_mask",
      "text_mask_file": "/absolute/product/package/英文版/_audit_masks/main-001.png",
      "final_ocr_text": "English OCR text only",
      "unrelated_content": false,
      "edge_cut": false,
      "neighbor_fragment": false,
      "standalone_understanding": true,
      "content_subject_match": true,
      "product_form_verified": true,
      "claim_check": "PASS",
      "sku_mapping_verified": true,
      "subject_overlap_verified": true,
      "audit_status": "PASS"
    }
  ]
}
```

Use absolute paths or paths relative to `package_dir`. Every image physically present in `英文版/01_主图`, `02_详情图`, and `03_SKU图` must have exactly one audit entry, and the expected counts must match both the manifest and directories.

For a text-bearing image, provide a grayscale text mask with white pixels only where text replacement is allowed. The validator requires zero decoded-pixel changes outside that mask. A text-free image must preserve all decoded source pixels. Prefer PNG final files when a lossy re-encode would alter pixels outside the text mask.

## Generate the write receipt

```bash
python3 <installed-skill-dir>/scripts/validate_asset_audit.py \
  "<package>/英文版/localization_audit.json" \
  --receipt-out "<package>/英文版/audit_receipt.json"
```

The command runs macOS Vision OCR locally against every actual final image; this uses local compute rather than model tokens. It fails closed if OCR cannot run, if actual pixels contain recognized CJK, or if any per-file gate, count, dimension, ratio, common detail width, source/final hash, manifest OCR result, pixel-preservation, or directory-inventory check fails. It emits a receipt only on complete PASS.

## Required write parameters

Every `create`, `update`, `tier_variations`, or `upload_image` call through `vps_api.py`, and every corresponding POST through `shopee_api.py`, must include:

```json
{"audit_receipt_path": "/absolute/product/package/英文版/audit_receipt.json"}
```

Every image upload must additionally include:

```json
{"audit_final_file": "/absolute/product/package/英文版/02_详情图/001.png"}
```

The API wrapper re-hashes the audit and all final files before opening the network connection. A missing, stale, altered, or mismatched receipt is `ASSET_AUDIT_REQUIRED` and must not be bypassed.
