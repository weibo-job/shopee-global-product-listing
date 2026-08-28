---
name: shopee-global-product-listing
description: Use when a user supplies an authorized Pinduoduo link or product assets and asks to prepare, create, retry, or verify a Shopee cross-border Global Product without publishing it to site shops.
---

# Shopee Global Product Listing

## Core rule

Prepare accurate Shopee Global Product drafts. Do not invent product facts, required attributes, SKU options, prices, stock, certifications, compatibility, or dimensions that are not present in supplied assets, source links, or Shopee API responses.

## Default execution and image mode

- Default API channel is the user's configured VPS helper. Local direct signing is fallback-only when the helper is unavailable; never switch silently or use an unconfigured/third-party helper.
- Default image mode is `subject_locked_localization`. Prefer exact-pixel crops and Pillow text replacement. Reference-image generation is allowed only when no complete, ratio-compliant, readable original-pixel crop exists.
- Background, decoration, non-product layout, and translated text regions may change. Product silhouette, proportions, structure, color, accessories, wearing form, and SKU variant may not.
- Any morphology drift, substituted component, altered color/SKU, unsupported claim, Chinese descriptive/UI/specification text, or unverified subject comparison is `FAIL` and blocks all upload/API writes.
- Use `strict_pixel` only when the user explicitly requires every non-text pixel to remain identical.

## Mandatory detail-image decision chain

This is a non-negotiable algorithm. It **must be included** whenever answering a user who asks for this Skill's principles, workflow, or detail-image handling; do not replace it with the shorter statement “detail images must be complete cards.”

1. Fully load the source page, wait for lazy loading to settle across two identical ordered scans, and preserve the rendered `source_order`. Keep gallery, detail, SKU, and recommendation inventories separate. Exclude only documented unrelated/recommendation/duplicate material. Before building a long canvas, count the cleaned detail images and calculate each `width/height`. If the cleaned set has `<=12` relevant standalone detail cards and every ratio is `>=0.5`, use the direct branch: localize those cards without long-canvas reconstruction, then run the normal visual, semantic, claim, subject, and package audits. Otherwise continue to step 2.
2. Normalize the remaining original details to one width and concatenate them in exact source order into an **analysis-only long canvas**. Do not mistake download-file boundaries for screen boundaries.
3. Find logical complete screens from content/module boundaries. A complete screen is a self-contained product-information card: its title/copy, product or feature subject, and scene are complete and understandable without another card. First use obvious visual split signals—an abrupt background colour, brightness, material, texture, or layout change—to locate a candidate boundary (for example, a light flowing panel changing clearly into a brown feature panel). This is a hard first signal, but it is never sufficient by itself: every colour-difference boundary must pass a second hard check for complete title/copy, complete product or feature subject, and complete semantic meaning. If any of those three checks fails, do not cut at that colour boundary. If the background contrast is weak, fall back to the same title, subject, and semantic checks to locate the boundary. A crop may cross a naturally continuous original boundary, but must have complete copy, subject/person/UI, and scene, with no neighboring strip, cut edge, or dependency on another image. A continuous waterfall/flowing background may continue across screens; cut only at semantic content boundaries and never through a required subject.
4. Select at most 12 of those complete crops. If there are more than 12, select by information coverage, readability, product relevance, layout quality, semantic content-to-subject match, and low duplication—never mechanically the first 12. Keep the selected screens in their original relative order. If there are 12 or fewer, retain all relevant complete screens.
5. Use `subject_locked_localization` by default. Only when **no** original-pixel crop can simultaneously be complete, readable, and have width/height >= 0.5 may reference-image generation be used for that screen. Pass every dependent original as `referenced_image_paths`; do not use white borders, blank canvas extension, arbitrary manual stitching, stretching, essential-content cropping, or a text prompt that redraws the product. If no compliant reference-image capability exists, mark that card FAIL and stop instead of fabricating.
6. Translate only after final screen selection. Complete crops receive text-only English localization: all non-text original pixels stay unchanged. Every functional or specification claim must match the visual subject shown in that card (for example, a battery-life claim must show the battery/charging/related product context; a Bluetooth claim must show the connection/chip/related context). A card with a text-to-subject mismatch fails even when its ratio passes. An imagegen result is only an intermediate layout layer: restore the exact original product subject pixels/cutout before acceptance. Every English word, number, UI label, and specification must be source-supported.
7. Audit every main/detail/SKU file individually, including a registered original-to-final subject-overlap comparison. Any morphology drift, untranslated descriptive Chinese, wrong SKU/specification, incomplete card, or unverified audit blocks upload. Upload only after every audit is PASS; then upload detail images one at a time in the reviewed **Pinduoduo source-relative order**. Wait for and record the returned image ID before uploading the next image, and verify that the final Global Product readback preserves that same order.

**Detail-image rule:** A failed direct image URL is a retrieval failure, not proof that the source image is absent. Determine the complete original detail inventory from the fully rendered page first and exclude documented ads, recommendations, unrelated products, and invalid duplicates. Exclude a detail card that merely repeats the main image unless it contains materially different, relevant product information. If the cleaned inventory is `<=12` relevant standalone cards and every card has `width/height >=0.5`, localize those cards directly and skip long-canvas reconstruction. Otherwise normalize the ordered originals to one width and concatenate them into an exact-pixel long canvas for **analysis only**. Identify candidate boundaries using clear background colour, brightness, material, texture, or layout changes first, but treat this as only the first hard gate. Every such candidate must then pass a second hard gate: title/copy complete, product/feature subject complete, and semantic meaning complete. If any one fails, reject that boundary and do not cut there. When visual contrast is weak, use those same three checks directly. Crop the best independent screens from that canvas first; a crop may cross a natural original boundary or a continuous decorative background, but cannot contain cut copy/subject/UI, a neighboring strip, or dependence on another card. Every functional/specification claim must be visually represented by the corresponding product/function subject on the same card. If more than 12 screens qualify, select the best 12 by information coverage, readability, product relevance, layout quality, semantic content-to-subject match, and duplication—not simply the first 12—and retain their original relative order. If 12 or fewer qualify, keep all relevant screens. Use `imagegen` only when no exact-pixel crop can be both complete and ratio-compliant; pass every dependent original as a reference. Recover failed assets through the page/browser or an alternate rendition before any such decision.

**Detail-image width and visual scale:** All English detail images in one package must use the same canvas pixel width. The `width/height >= 0.5` requirement is not permission to pad an image into compliance. Do not use white borders, blank canvas extension, arbitrary background expansion, subject shrinking, or subject stretching to repair an invalid ratio. Reject obvious visual-distance jumps, abnormally tiny subjects, or changed subject proportions. If a card cannot satisfy completeness, ratio, readability, and reasonable visual scale, recover another complete crop or use subject-locked generation; otherwise mark it FAIL.

**Source-detail gate:** Never pad the detail set with recommendations, unrelated images, invented cards, or arbitrary slices. A cleaned set that already has `<=12` relevant standalone cards with every ratio `>=0.5` may use the direct branch even when it does not need long-canvas reconstruction. A set that fails that early predicate must go through long-canvas recovery and logical complete-screen analysis before selection.

**Rendered-page completeness gate:** Never decide the source image or SKU count from the initial DOM, the first viewport, or an existing archive alone. For a lazy-loaded page, scroll through the complete product detail region, wait for image loading after each scroll, and rescan until two consecutive scans produce the same ordered asset list and the page has reached the end of that region. Keep the product gallery, product detail section, SKU panel, and recommendations in separate inventories. Record raw counts, excluded counts/reasons, and the reviewed ordered counts before packaging.

**Automatic insufficient-count rescan gate:** If the first full rendered-page pass produces an insufficient or anomalous count for any required product asset group—such as fewer than 6 valid detail screens, fewer gallery images than the page counter, a SKU count mismatch, or materially fewer assets than other visible source evidence—do not conclude that the source is insufficient and do not ask the user to intervene yet. Automatically run a fresh second full pass from the top of the product page to the end of the product detail region, actively scrolling every viewport, waiting for lazy loading after each scroll, recovering `data-src` or alternate renditions, and reopening SKU selectors when SKU assets are involved. A second scan means another complete scroll pass, not rereading the initial DOM or rescanning only the current viewport. If the ordered count changes, continue full passes until two consecutive complete passes are identical. Only after this automatic recovery still yields a stable insufficient count may the workflow stop and report source insufficiency; record every pass count and the recovered order delta.

**Order-preservation gate:** The page order is authoritative. Create a numbered source manifest before downloading and assign filenames from `source_order` (`001`, `002`, `003`...), never from download completion order, filesystem lexical order, or a browser's incidental DOM index. A slow or failed download must not cause later images to shift position. Keep the source URL, order, local filename, dimensions, hash, and download status together; repair or stop on any missing/misaligned entry before localization.

**Bundled packaging stage:** This repository includes the former `shopee-listing-packager` functionality in `scripts/scan_images.py`, `scripts/make_package.py`, and `scripts/long_canvas.py`. Run the bundled packaging stage before localization or Global Product API work; users do not need to install a separate child Skill.

## Artifact storage rule

- Store every persistent artifact produced during an upload task under `${SHOPEE_LISTING_OUTPUT_DIR:-<cwd>/shopee-listing}/<product-folder>`.
- Name `<product-folder>` with the product number when available. When no product number is available, use `上架YYYYMMDD` using the task date.
- Keep the package split into exactly two top-level asset folders: `原图/` for the complete original source package, source evidence, and original-related records; and `英文版/` for localized English assets, listing drafts, validation records, API requests/responses, readbacks, and creation results. Do not mix original and English outputs.
- Preserve the same split when staging or copying durable results. All returned asset paths must point to the corresponding `原图/` or `英文版/` folder.

## One-link delivery contract

- Before processing a link, run the bundled `scripts/preflight.py`. It must confirm that all bundled packaging, audit, authorization, and API scripts exist and that either the user's VPS helper or complete local direct credentials/token store are configured. Preflight performs no Shopee writes.
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
3. Preserve the complete source package under the product folder's `原图/`; never overwrite it. Create the English package under the same product folder's `英文版/`, retaining the `01_主图`, `02_详情图`, `03_SKU图`, and video structure. Generate English images from the corresponding original image only. Detect duplicate source images across main/detail/SKU groups before editing; translate one copy once, then reuse the reviewed English output wherever the same source image is required. Translate descriptive text only; every English claim must be traceable to Chinese text in the source image. Never add functions, parameters, accessories, or selling points. Inspect every localised image and reject it if the subject/content is altered, distorted, cropped, incomplete, contains unsupported claims, or retains Chinese descriptive text. Persist the rendered-page asset inventory and the reviewed ordered manifest in `原图/` before creating the English package. The English manifest must map each final file back to its source order; never rebuild order by listing the output directory.
4. Branch the image workflow by asset group:
  - main images: use at most 9 square images, each over 700 px. If the original has fewer than 9 suitable main images, fill the remaining main slots only with valid, independent detail screens whose information is not already represented by the selected main images. For example, 4 original main images may be supplemented with suitable detail screens after the minimum source-detail gate passes. For each chosen detail image, decide from its own visual content whether safe padding/re-layout or image generation is needed to make a square. Do not cut the product body, change its proportions, combine multiple detail images, or use recommendations/unrelated assets as main images. If a source image is useful but its ratio, dimensions, or layout is non-compliant, repair it and validate the generated result.
  - SKU images: first expand the page's actual SKU/款式 selector and enumerate every option label, even when the archive contains only one default SKU image. If an option image is lazy-loaded, select that option and capture its rendered image before proceeding. If descriptive Chinese is present, translate it into English; if the source exposes only one generic SKU image for multiple options, reuse that reviewed localized image explicitly for each option and record the reuse rather than silently dropping an option. Preserve the original subject, composition, structure, dimensions, and option order. Upload exactly one corresponding image for each source SKU; never change the SKU-to-image mapping. Persist an explicit ordered SKU manifest (source option label -> optimized name -> source image URL/file -> local file -> uploaded image ID) and iterate that manifest, never filesystem lexical order. Before any API write, require `source_sku_count == package_sku_count == request_model_count`; after `init_tier_variation`, require the readback model count and option labels to match the manifest exactly. Stop on any mismatch instead of creating a partial listing.
  - detail images: use the settled rendered-page inventory, not the first lazy-loaded batch. Exclude only recommendations, ads, reviews, brand-intro/offline-store material, duplicates, or clearly unrelated products, and record each exclusion. First apply the direct predicate: `detail_count <= 12`, every ratio `>=0.5`, and every source file is already a relevant standalone card. If it passes, localize those cards directly and skip long-canvas reconstruction. If it fails, normalize the rest to a common width and concatenate in exact `source_order`, without gap, reordering, or pixel editing, into a long canvas for analysis only. Mark logical screen boundaries by complete information modules—not raw asset boundaries—and crop only independent screens containing their complete title, text, subject/person/UI, and scene. A continuous waterfall/flowing background may cross a crop boundary, but the content module and product/feature subject must be complete; never show a neighboring strip, cut edge, or content that needs the prior/next card. Verify that every claim is visually represented by the corresponding product/function subject on the same card.
  - Select at most 12 of those complete long-canvas crops. If more than 12 qualify, choose the best 12 by coverage of product identity, wearing/use, key features, battery/charging, app/control, specifications, and variant/packaging information, while minimizing duplication. Do not default to the first 12. If 12 or fewer qualify, keep all relevant screens. Preserve selected source-relative order and record every crop's canvas range and contributing `source_order` values.
  - Every final detail image must have width/height >= 0.5, use the same final pixel width as the other detail images, and keep the complete product or information panel visible. First attempt an exact-pixel crop from the long canvas. Call `imagegen` only if no crop can simultaneously be complete and ratio-compliant. For that exceptional card, pass every dependent original through `referenced_image_paths`, create one standalone English screen, and never use safe padding, canvas extension, manual vertical stitching, stretching, essential-content cropping, or a text-only product redraw.
  - Visual-integrity gate: dimensions are necessary but never sufficient. Before upload, inspect every final card individually and inspect the ordered sequence as a continuous contact sheet or equivalent visual review. Reject any card with a top/bottom strip from a neighboring card, edge-cut text, a partial face/product/object, a composition that only makes sense when stacked with another card, a visible continuation boundary through a required subject, or a mismatch between the written function/specification and the product/function subject shown. A continuous decorative background alone is not a failure when the information module is complete. Record `edge_cut`, `neighbor_fragment`, `standalone_understanding`, and `content_subject_match` for every final card.
  - Product-form gate: establish a trusted product-form reference from the original source/main images before using `imagegen`. Generated cards must preserve the same product silhouette, wearing form, stem/nozzle, speaker grille, case geometry, accessories, and variant identity. Reject and regenerate any morphology drift, such as an open/semi-in-ear earbud becoming a silicone in-ear earbud, a short stem becoming a long stem, or a grille becoming a different speaker shape, even when text and ratio pass.
  - Exact-subject imagegen rule: for a product whose geometry is identity-critical, never describe the subject from visual inspection and ask `imagegen` to redraw it from a text prompt. When imagegen is required, pass the original source image containing the product body as `referenced_image_paths` (or the equivalent source-image input) in the same edit call, and instruct it to preserve that supplied subject exactly while changing only the required language/layout/completion elements. The source subject is the authoritative image input; prompt text is not a substitute. If the returned subject cannot be verified against the supplied source image, reject the card and stop rather than submitting an approximate redraw.
  - Claim gate for generated cards: compare every generated word, number, specification, accessory, and UI label against source evidence. Reject cards that add plausible but unsupported values or claims; a polished card with a wrong Bluetooth version or invented latency number is invalid.
  - Full-package audit gate: before any media upload or Global Product create/update, enumerate and inspect every file in `01_主图`, `02_详情图`, and `03_SKU图`; do not audit only the selected detail subset. Compare each final file with its source file/source order or SKU option and the trusted product-form reference. Persist one result per file with `asset_group`, `source_order_or_sku`, `source_file`, `final_file`, `dimensions`, `ratio`, `unrelated_content`, `edge_cut`, `neighbor_fragment`, `standalone_understanding`, `product_form_verified`, `claim_check`, `sku_mapping_verified`, and `audit_status`. `audit_status=FAIL` for any file blocks all subsequent upload/API writes; a dimensional pass never overrides a visual, subject, claim, or mapping failure. For SKU files, also verify the exact option-image mapping and every visible version/spec claim; a wrong version such as Bluetooth 5.0 versus a source-supported Bluetooth 6.0 is a hard failure.
  - Final overlap-comparison gate: after English localization or imagegen, perform a last source-to-final subject comparison for every product-bearing main/detail/SKU image against its corresponding original. Use an overlay/alignment comparison or equivalent registered geometry check, not visual impression alone. The product silhouette, scale/proportions, relative placement, stem/nozzle, grille/ports, case geometry, covers, accessories, and variant identity must remain coincident with the original subject; translated text/layout may change only outside the preserved subject. Record the comparison result and method per file. Any non-overlap, deformation, substituted component, or unverified comparison is `audit_status=FAIL` and blocks upload.
  - Exact-subject compositing rule: an imagegen return is an intermediate layout/text layer, never the final product asset. For each product-bearing output, restore the corresponding original subject pixels (or an exact source cutout) over the generated layer before acceptance. The final file must be composited from the original subject plus the generated non-subject layer; do not allow the generated layer to overwrite the product, case, covers, accessories, or variant artwork. Record the preserved-subject source and compositing boundary/mask, then rerun the overlap-comparison gate.
  - Long-canvas translation and delivery rule: for a complete selected crop, localize only verified text regions and keep every non-text pixel from the original. Record each text-region mask and require a pixel comparison showing zero difference outside those masks. An imagegen result is permitted only for a screen with no viable complete, ratio-compliant crop; use all relevant adjacent originals as references, then apply exact-subject compositing and overlap gates. A contact sheet is a review aid, not an acceptance result: visually inspect every final main/detail/SKU file individually and report a package as complete only after every per-file audit is PASS.
   - detail-image order is a hard rule after selection: preserve the reviewed relative order of the chosen screens, but do not interpret this as “always take the first 12.” The first chosen screen must be at the top, followed by the next chosen screen in source order; never reverse the selected list.
  - upload exactly one detail image per upload request, strictly in the reviewed Pinduoduo source-relative order. Wait for and record that image's returned ID before uploading the next image. Build `description_info.extended_description.field_list` from this ordered upload manifest so the next detail image immediately follows the previous one; reject any filesystem, download-completion, or regenerated-card order that differs from the reviewed Pinduoduo order.
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
   - preserve a one-to-one mapping from each Pinduoduo source SKU name to its optimized English SKU name and SKU image; never infer mapping from sorted filenames;
   - optimize wording for concise natural English without adding a style, feature, color, or accessory absent from the source SKU;
   - keep each SKU name under 30 characters;
   - stock from source SKU evidence when available; when the source does not expose SKU stock, default to `100` and record `stock_source=default_100` for human review;
   - price = Pinduoduo SKU price x 2 unless user overrides.
8. Validate the localized image package and draft JSON with the image validator and `scripts/validate_listing_draft.py`.
   - Source sufficiency is a hard gate: after exclusions and long-canvas recovery, require at least 6 valid original detail screens. If fewer than 6 remain, stop and report insufficient source material; do not call any Shopee create/update/publish endpoint.
   - Image recovery is a hard gate: before validation, compare the settled rendered-page inventory with the reviewed package count. Recover logical complete screens from the exact-pixel long canvas before selection; call `imagegen` only for a selected logical screen that has no complete, ratio-compliant crop. When the recovered inventory is greater than 12, require exactly 12 selected/rebuilt English detail screens, preserving source-relative order. For every source image excluded because it is a duplicate, recommendation, unrelated asset, or part of an imagegen replacement, record the reason and replacement path. Do not call a package complete when useful source content was simply omitted.
   - SKU completeness is a hard gate: compare the rendered source option manifest, localized SKU files, request tier options, and readback models. A successful API response is not sufficient if any source SKU is absent or any option-image mapping differs.
   - Detail-order validation is a hard gate: verify the localized detail manifest is in reviewed order, that each final file maps to the intended source order, that each image is uploaded in its own request, and that the recorded upload IDs and Shopee readback IDs match that order exactly. Reject and repair any reversed, lexical-only, download-completion-order, or otherwise reordered list.
   - Full-package audit is a hard gate: the package is not ready until every main, detail, and SKU file has an auditable PASS. If any visual inspection, product-form, source-claim, unrelated-content, edge/fragment, or SKU-mapping check is unresolved or failed, stop and report the exact files and reasons; do not create a partial listing.
9. If validation passes and no mandatory facts are missing, execute the live sequence from `references/live-api-runbook.md` using the product folder's `英文版/` package. Upload exactly one localized detail image per request in reviewed first-to-last order, capture its image ID before the next upload, and include the ordered IDs in `description_info.extended_description.field_list` with `description_type=extended`. Capture `global_item_id` immediately after `add_global_item`; initialize first-time variants with `init_tier_variation` and `global_model`. The user has pre-authorized this validated Global Product write, so do not add another confirmation gate.
10. Resume idempotently after any failure: when `global_item_id` exists, never call `add_global_item` again for that package. Read the item/model state and retry only the missing stage. If the base item exists but its detail-image list is missing or out of order, re-upload the localized detail images one by one and call the global-item update endpoint with the ordered extended-description fields.
   Before any live write, inspect package-local `创建成功_*.json`, `api_work/create_summary.json`, and the existing-item readback for a prior `global_item_id`; do not rely only on a temporary VPS output folder, which can be empty after a restart.
11. Return a creation package and lead with the verified `global_item_id`:
   - listing summary,
   - `原图/` and `英文版/` asset paths, with localization review status,
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
   - detail-image count is at most 12, every one-image upload has a non-empty image ID, and the item readback detail-image IDs exactly equal the reviewed first-to-last upload order;
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
