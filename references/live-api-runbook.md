# Shopee Global Product Live API Runbook

Use this runbook after the listing package and API JSON pass validation. Treat every Shopee response body as authoritative; HTTP 200 alone is not success.

## Preflight

1. Check the VPS helper health and current token store without printing tokens or Partner Key.
2. Refresh the access token before metadata reads and live writes.
3. Resolve the authorized `merchant_id` dynamically from Shopee. Use the merchant authorization for Global Product APIs.
4. Resolve an authorized `shop_id` only when the media upload endpoint requires shop-scoped authorization. Do not substitute `shop_id` for `merchant_id` in Global Product calls.
5. Fetch current category, mandatory attributes, brand list, item limits, and authorized merchant/shop lists. Revalidate them for every product.
6. Use the reviewed `_英文版` package for media upload; preserve the original package for audit. Upload at most 9 main images (using square detail-derived candidates only when their information is not duplicated by the selected main images), then exactly one matching SKU image per SKU, and verify every local file maps to a non-empty Shopee image ID. Upload localized detail images one at a time in source/file order, record the returned IDs, enforce a maximum of 12, and reject any stitched or cross-image-dependent card. If the detail regeneration branch was used, verify every regenerated card against its source image before upload.
7. Validate title, description, category, attributes, brand, image count/order, weight, condition, price, stock, SKU mapping, and tier indexes. The draft must set `description_type=extended` and place detail images in the same order as `description_info.extended_description.field_list`.

## VPS media staging

The Shopee helper service and the SSH transfer account are different OS users. A file may exist yet still be unreadable by the helper when any parent directory blocks traversal.

1. In automation mode, stage each product under `/tmp/shopee_jobs_shopeejob/<goods_id>`, never under `/home/shopeejob`.
2. Create the shared parent and product image directories, then apply `chmod 755` to the shared parent, product directory, and `main`, `detail`, and `sku` directories.
3. After transfer, apply `chmod -R a+rX` to the staged image directories before calling the media API.
4. If every upload returns `EACCES`, inspect parent-directory traversal permissions first. Do not refresh tokens, recreate the product, or repeatedly upload the same files until filesystem access is fixed.
5. Require a non-empty Shopee image ID for every main and SKU image before `add_global_item`.

## Live write sequence

1. Call `POST /api/shopee/global-items` once with `confirm_create=true`.
2. Require all of the following before proceeding: wrapper `ok=true`, Shopee `error` empty, and a non-empty `response.global_item_id`.
3. Persist the response and `global_item_id` immediately in the package state/output folder.
4. For a product with variants, call `POST /api/shopee/global-tier-variations` with:
   - `confirm_create=true`;
   - the saved `global_item_id`;
   - `tier_variation` with source-backed option names and images;
   - model data in Shopee's `global_model` field, including valid `tier_index`, price, stock, and SKU.
5. Use `/api/v2/global_product/init_tier_variation` underneath this helper route. Do not use `add_global_model` for the initial tier setup.
6. Do not call any site-shop publish endpoint.

For an existing Global Product whose detail images are missing or out of order:

1. Do not call `add_global_item` again.
2. Upload the detail images sequentially and call `POST /api/shopee/global-item-update` with `global_item_id`, `description_type=extended`, and an `extended_description.field_list` whose image entries follow the upload order exactly.
3. Read the item back and require the returned image entries to match the ordered upload IDs one-for-one.

## Idempotent recovery

- Before a retry, read the saved state and `GET /api/shopee/global-model-list?global_item_id=...`.
- If `global_item_id` already exists, never call `add_global_item` again for the same package.
- If the item exists and model count is zero, retry only `init_tier_variation`.
- If the expected model count already exists, perform readback verification only.
- If a write response is ambiguous, read Shopee state before deciding whether to retry.
- Refresh an expired token before retrying a read. For a write, read current item/model state first so a token/network error cannot create duplicates.

## Acceptance contract

Creation is complete only when all checks pass:

- base response: `ok=true`, empty Shopee `error`, and persisted `global_item_id`;
- item readback: the same `global_item_id` is returned;
- variant readback: exact expected model count, tier options, SKU mapping, prices, and stock;
- each model has a Shopee model ID when the endpoint supplies IDs;
- `base_item_create_called` records whether the current run created or resumed the base item;
- `base_item_duplicate_call=false`;
- `item_info_verified=true`;
- `sku_mapping_verified=true`, `price_mapping_verified=true`, and `stock_mapping_verified=true`;
- `site_publish_called=false`;
- detail-image count is at most 12, and the readback detail-image ID sequence exactly matches the sequential upload manifest;
- API warnings are preserved in the result. A deprecation warning such as `normal_stock` requires checking the current Shopee schema before the next product, not guessing a replacement field.

## Failures this runbook prevents

| Failure | Prevention |
|---|---|
| `invalid_access_token` | Refresh token first; verify token state without exposing secrets. |
| Missing `merchant_id` | Resolve merchant authorization dynamically; keep merchant and shop scopes separate. |
| Media upload rejected with main-account context | Use an authorized shop only for the shop-scoped media upload. |
| All staged image uploads fail with `EACCES` | Use `/tmp/shopee_jobs_shopeejob/<goods_id>`; fix parent-directory traversal with `chmod 755`, then image readability with `chmod -R a+rX`. |
| `GlobalModel is required` | Send initial variant models as `global_model`; normalize internal `model_list` before Shopee. |
| Duplicate Global Product after a partial failure | Persist `global_item_id` and resume only the missing stage. |
| False success from HTTP 200 | Check wrapper `ok`, Shopee `error`, returned IDs, item readback, and exact model count. |
| Repeated SSH password prompts | Use one SSH ControlMaster session in the generated terminal runner; never request the password in chat. |
| Accidental site publishing | Exclude site publish calls and report `site_publish_called=false`. |
