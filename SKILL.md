---
name: shopee-global-product-listing
description: Use when a user supplies an authorized Pinduoduo link or product assets and asks to prepare, create, retry, or verify a Shopee cross-border Global Product without publishing it to site shops.
---

# Shopee Global Product Listing

## Core rule

Prepare accurate Shopee Global Product drafts. Do not invent product facts, required attributes, SKU options, prices, stock, certifications, compatibility, or dimensions that are not present in supplied assets, source links, or Shopee API responses.

**Detail-image minimum:** A failed direct image URL is a retrieval failure, not proof that the source image is absent. Determine the original detail-image count from the rendered product page/source evidence first. If the original provides 12 or more detail images, the English package and Shopee request must contain exactly 12 detail images. Recover failed assets through the page/browser or an alternate rendition; if recovery is impossible, use the recovered source images as references for faithful `imagegen` replacements. Upload fewer than 12 only after verifying that the original product truly provides fewer than 12 detail images.

**Detail-image width:** All English detail images in one package must use the same pixel width. After translation, re-layout, or image generation, normalize every detail image to the selected package width and reject the package if widths are mixed.

**REQUIRED SUB-SKILL:** Use `shopee-listing-packager` to archive the authorized Pinduoduo page and prepare/localize the media package before Global Product API work.

## One-link delivery contract

- A Pinduoduo link is the normal input. Extract its source `goods_id`, authorized product evidence, images, SKU names, source prices, and source stock without asking the user to re-enter facts already present on the page.
- Run the complete packaging, validation, queue, Shopee API creation, and readback workflow. Do not ask the user to operate Terminal, paste shell commands, enter the VPS password, or reconfirm a validated Global Product write.
- Ask the user only when a genuinely mandatory fact cannot be established from the source page, supplied assets, defaults in `references/listing-rules.md`, or current Shopee metadata. Never invent the missing fact.
- Return the verified `global_item_id` as the lead result. Keep technical evidence in the package and summarize it only when useful or when creation is blocked.
- This contract creates a Global Product draft only. The user reviews and manually publishes it to site shops later.

## Required inputs

For each product, collect:

- Authorized product images and detail images.
- Pinduoduo link or SKU evidence when SKU, stock, and source price matter.
- Product type/category hint from the user when the product is not headphones.
- Target price rule or explicit price.
- Weight/dimensions if different from defaults.
- Product video if available.

If a required fact is absent, mark it as missing in the draft instead of guessing. Exception: when a SKU's stock cannot be established from the source page or supplied SKU evidence, use stock `100`, record that it is the default, and surface it for human review.

## Workflow

1. Read `references/listing-rules.md` before drafting. Before any live API write, also read `references/live-api-runbook.md`.
2. Inspect supplied assets and separate main, detail, SKU, and excluded images.
3. Preserve the complete source package first; never overwrite it. Then create a sibling `上架整理_<model>_英文版` package with the same `01_主图`, `02_详情图`, `03_SKU图`, and video structure. Generate English images from the corresponding original image only. Detect duplicate source images across main/detail/SKU groups before editing; translate one copy once, then reuse the reviewed English output wherever the same source image is required. Translate descriptive text only; every English claim must be traceable to Chinese text in the source image. Never add functions, parameters, accessories, or selling points. Inspect every localised image and reject it if the subject/content is altered, distorted, cropped, incomplete, contains unsupported claims, or retains Chinese descriptive text.
4. Branch the image workflow by asset group:
   - main images: use at most 9 square images, each over 700 px. If the original has fewer than 9 suitable square images, choose detail images whose information is not already represented by the selected main images. For each chosen detail image, decide from its own visual content whether safe crop, proportional resize/re-layout, or image generation is needed to make a square. Do not cut the product body, change its proportions, or combine multiple detail images. If a source image is useful but its ratio, dimensions, or layout is non-compliant, do not discard it: use safe padding/re-layout or the `imagegen` skill with the original as reference, then validate the generated result.
   - SKU images: translate directly into English while preserving the original subject, composition, structure, and dimensions. Upload exactly one corresponding image for each SKU; never change the SKU-to-image mapping.
   - detail images: first check dimensions and whether the product or an information panel is cut through the middle. If the original has more than 12 detail images, the English package must contain exactly 12 detail images, never fewer: select 12 in original order, translate them, and repair any non-compliant selection by safe re-layout or `imagegen`. If every selected detail image is complete and compliant, translate the Chinese text in place without changing the subject or structure. If any selected detail image cuts through the product/body or makes the information incomplete, enter detail-card regeneration mode: use the original detail images as the only references and use image generation to create a coherent English set of standalone detail cards. Every regenerated card must retain the source product and source-supported content; if the original has 12 or more usable detail images, do not reduce the English set below 12. A low count caused only by non-compliant ratio, low resolution, or failed direct download is not acceptable: recover the source where possible, then re-layout or regenerate a faithful replacement before excluding it.
   - detail images in either branch must be independently complete: never split one source panel into dependent upper/lower images, stitch adjacent panels, or make one image rely on the next. Do not force a square crop that cuts the product; use safe padding/re-layout or generation instead. Do not stretch or distort the product; preserve its proportions and keep all essential product information within each card.
   - the next detail image must immediately follow the previous one in the ordered `description_info.extended_description.field_list`;
   - exclude brand intro, awards, reviews, and offline store images.
5. Use Shopee API evidence before final JSON:
   - get category,
   - get attributes for selected category,
   - get brand list or set No Brand when valid,
   - verify existing global item details if cloning/reference is involved.
6. Draft English listing:
   - title: natural Malaysia-market English, under 180 characters;
   - description: English, under 500 words, only fact-backed;
   - condition: New;
   - brand: No Brand unless evidence requires otherwise.
7. Draft SKU/model data:
   - preserve a one-to-one mapping from each Pinduoduo source SKU name to its optimized English SKU name and SKU image;
   - optimize wording for concise natural English without adding a style, feature, color, or accessory absent from the source SKU;
   - keep each SKU name under 30 characters;
   - stock from source SKU evidence when available; when the source does not expose SKU stock, default to `100` and record `stock_source=default_100` for human review;
   - price = Pinduoduo SKU price x 2 unless user overrides.
8. Validate the localized image package and draft JSON with the image validator and `scripts/validate_listing_draft.py`.
   - Image recovery is a hard gate: before validation, compare source asset count with the reviewed package count. When source detail count is greater than 12, require exactly 12 English detail images. For every source image excluded because of ratio, size, crop, direct-download format, or localization layout, record the reason and the safe re-layout/imagegen replacement path. Do not call a package complete when useful source content was simply omitted.
9. If validation passes and no mandatory facts are missing, execute the live sequence from `references/live-api-runbook.md` using the `_英文版` package. Upload each localized detail image sequentially, capture its image ID in the same order, and include the ordered IDs in `description_info.extended_description.field_list` with `description_type=extended`. Capture `global_item_id` immediately after `add_global_item`; initialize first-time variants with `init_tier_variation` and `global_model`. The user has pre-authorized this validated Global Product write, so do not add another confirmation gate.
10. Resume idempotently after any failure: when `global_item_id` exists, never call `add_global_item` again for that package. Read the item/model state and retry only the missing stage. If the base item exists but its detail-image list is missing or out of order, re-upload the localized detail images one by one and call the global-item update endpoint with the ordered extended-description fields.
   Before any live write, inspect package-local `创建成功_*.json`, `api_work/create_summary.json`, and the existing-item readback for a prior `global_item_id`; do not rely only on a temporary VPS output folder, which can be empty after a restart.
11. Return a creation package and lead with the verified `global_item_id`:
   - listing summary,
   - original and `_英文版` asset paths, with localization review status,
   - missing facts,
   - excluded images and reasons,
   - Shopee API JSON used for creation,
   - Shopee API creation response.

## Automatic Mac-to-VPS execution

When the dedicated Mac LaunchAgent is installed, use the file-backed queue under `/private/tmp/ShopeeJobRunner` instead of asking the user to open Terminal or enter the VPS password for each product. The enqueue script stages a temporary copy there because a background LaunchAgent may not have macOS privacy access to `Documents`.

1. Generate one idempotent package runner inside the product directory. It must support these environment variables:
   - `SHOPEE_AUTOMATION=1` to skip helper deployment and use non-interactive SSH;
   - `SHOPEE_SERVER_USER=shopeejob` for the low-privilege remote user;
   - `SHOPEE_IDENTITY_FILE` for the dedicated SSH identity.
   - Every run must use a job/product-specific remote staging directory, including in `SHOPEE_AUTOMATION=1` mode. Never reuse a fixed `/tmp/shopee_jobs_shopeejob/<goods_id>` directory across deleted/recreated products; stale `add_global_item_result.json` there can incorrectly suppress a new create call. Persist the authoritative ID only in the package-local success summary.
2. Stage reviewed images under `/tmp/shopee_jobs_shopeejob/<goods_id>`, not under `/home/shopeejob`. Before media upload, make every parent/image directory traversable with `chmod 755` and every staged image readable with `chmod -R a+rX`. Then call only the VPS helper on `127.0.0.1:3000`. Never read or print Partner Key or tokens.
3. After local validation passes, enqueue atomically:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/shopee-global-product-listing/scripts/enqueue_shopee_job.py" \
  --goods-id '<goods_id>' \
  --product-dir '<absolute package directory>'
```

4. Read the matching result from `/private/tmp/ShopeeJobRunner/queue/completed` or `failed`. Poll state; do not use a fixed assumption about runtime.
5. A zero process exit alone is insufficient. Success requires every field below:
   - `api_result.ok=true` and a non-empty `global_item_id`;
   - `base_item_duplicate_call=false`;
   - `item_info_verified=true`;
   - exact expected model count and a non-empty Shopee model ID for each returned model;
   - `sku_mapping_verified=true`, `price_mapping_verified=true`, and `stock_mapping_verified=true`;
   - detail-image count is at most 12, every detail upload has a non-empty image ID, and the item readback detail-image IDs exactly equal the upload order;
   - all Shopee error fields empty;
   - `site_publish_called=false`.
6. Copy the final request, write response, item/model readback, and success summary from the staged job into the durable product package.
7. If the dedicated identity or LaunchAgent is absent, prepare the package but stop before enqueueing and direct the user to the one-time installer. Never fall back to repeated interactive root-password prompts.

## Local API tool expectations

When the project contains the Shopee VPS helper service, prefer these local endpoints:

- `GET /api/shopee/global-products`
- `GET /api/shopee/global-category`
- `GET /api/shopee/global-attributes?category_id=...`
- `GET /api/shopee/global-brand-list?category_id=...`
- `GET /api/shopee/global-item-info?global_item_id_list=...`
- `POST /api/shopee/global-items/preview`
- `POST /api/shopee/global-items` with `confirm_create=true` after validation passes
- `POST /api/shopee/global-item-update` with `confirm_create=true` when repairing an existing item's detail-image sequence
- `POST /api/shopee/global-tier-variations` with `confirm_create=true` for first-time variants; send the model array as `global_model` (the local helper may normalize an internal `model_list`)
- `GET /api/shopee/global-model-list?global_item_id=...` to verify variant creation
- `POST /api/shopee/media/upload-image`

Never print Partner Key, access token, refresh token, or server secrets.

## Output format

For each product, produce:

1. `listing_summary` - title, category, brand, weight, condition, SKU count.
2. `asset_check` - main/detail/SKU image counts and violations.
3. `missing_info` - unresolved facts requiring user confirmation.
4. `api_json_preview` - add_global_item body used for creation.
5. `api_result` - Shopee creation response and `global_item_id` when available.
6. `publish_boundary` - state that this creates Global Product only and does not publish to site shops.
7. `acceptance_evidence` - item readback, exact model count, empty Shopee error fields, and booleans proving no duplicate base-item call and no site publish.

Default boundary: create Global Product only. Do not publish to MY/TH/TW/PH/VN/SG/MX/AR site shops; the user reviews and publishes manually in Shopee.
