#!/usr/bin/env python3
import argparse
import json
import sys


def count_words(text):
    return len(str(text or "").split())


def main():
    parser = argparse.ArgumentParser(description="Validate a Shopee global product listing draft JSON.")
    parser.add_argument("draft_json", help="Path to JSON file containing an add_global_item body or wrapper with api_json_preview.")
    args = parser.parse_args()

    with open(args.draft_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    body = data.get("api_json_preview", data)
    errors = []
    warnings = []

    title = body.get("global_item_name") or body.get("item_name") or body.get("title") or ""
    if not title:
        errors.append("missing title/global_item_name")
    elif len(title) >= 180:
        errors.append(f"title too long: {len(title)} characters")
    if any("\u4e00" <= ch <= "\u9fff" for ch in title):
        errors.append("title contains Chinese characters")

    description = body.get("description") or ""
    if not description:
        errors.append("missing description")
    elif count_words(description) >= 500:
        errors.append(f"description too long: {count_words(description)} words")

    brand = body.get("brand") or {}
    brand_name = brand.get("original_brand_name") or brand.get("brand_name") or body.get("brand_name")
    if not brand_name:
        warnings.append("brand is missing; default should usually be No Brand")

    image = body.get("image") or {}
    image_ids = image.get("image_id_list") or body.get("image_id_list") or []
    if len(image_ids) == 0:
        errors.append("missing main image_id_list")
    elif len(image_ids) > 9:
        warnings.append(f"main image count exceeds 9: {len(image_ids)}")

    description_info = body.get("description_info") or {}
    fields = ((description_info.get("extended_description") or {}).get("field_list") or [])
    detail_ids = [
        (field.get("image_info") or {}).get("image_id")
        for field in fields
        if field.get("field_type") == "image"
    ]
    if detail_ids:
        if body.get("description_type") != "extended":
            errors.append("detail images require description_type=extended")
        if len(detail_ids) > 12:
            errors.append(f"detail image count exceeds 12: {len(detail_ids)}")
        if any(not image_id for image_id in detail_ids):
            errors.append("detail image field is missing image_id")

    weight = body.get("weight")
    if weight is None:
        warnings.append("weight missing; default is 0.2 kg")

    condition = body.get("condition")
    if condition and str(condition).upper() != "NEW":
        errors.append(f"condition should be NEW, got {condition}")

    models = body.get("model_list") or body.get("models") or []
    for idx, model in enumerate(models, start=1):
        name = model.get("model_name") or model.get("name") or ""
        if len(name) > 30:
            errors.append(f"SKU/model {idx} name too long: {len(name)} characters")

    result = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
