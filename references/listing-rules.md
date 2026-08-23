# Shopee Global Product Listing Rules

Use these user-specific listing rules unless the current Shopee category/API response is stricter.

## Images

- Use at most 9 square main images; this is a ceiling, not a requirement to invent images.
- If the original main-image set has fewer than 9 suitable square images, fill only the remaining slots with detail images whose supported information is not already represented by the selected main images and that can stand alone. Build each promoted image as a square from that single source image by safe resizing/re-layout or image generation; do not cut the product body, change its proportions, combine multiple detail images, or add unsupported content.
- Main image dimensions must be greater than 700 px.
- If no square image exists, vertical images are acceptable only when the aspect ratio is not taller than 1:2.
- Main images should clearly show product appearance, selling points, accessories, and key use information.
- If a product video is supplied, include it.

## In-image language

- For every Shopee Global Product workflow, create and use a sibling `_英文版` package after preserving the original package.
- Translate descriptive Chinese text into concise English without changing the product, subject, layout, crop, dimensions, colours, lighting, logos, icons, or supported claims. Every English claim must be traceable to Chinese text in the corresponding original image; never add functions, parameters, accessories, or selling points.
- Images without descriptive text may be copied unchanged. If an image cannot be translated safely in place, preserve it and flag it for review; never fabricate, distort, or replace the product.
- Deduplicate identical source images across main, detail, and SKU groups before editing. Translate once and reuse the reviewed English output in every required group.
- Inspect every localized image before upload. No Chinese descriptive text may remain in an accepted localized image.

## Title

- English only.
- Natural for Malaysia-market buyers.
- Include core and long-tail keywords without keyword stuffing.
- Fewer than 180 characters.

## Category

- Default category is Headphones.
- If the product is not headphones, stop and select an appropriate category from Shopee API evidence before drafting.

## Description

- English only.
- Fewer than 500 English words.
- Cover main features, specifications, functions, package/accessories, and use cases.
- Use only facts visible in images, source page, provided documents, or API evidence.

## Detail images

- At most 12 detail images; this is a ceiling, not a target.
- Width must be at least 700 px.
- Width/height must be strictly greater than 0.5 (exactly 1:2 fails).
- Every selected detail image must be independently complete and understandable. Never stitch separate source panels, split one long panel into dependent upper/lower images, or make adjacent images complete each other.
- First check dimensions and whether the product or information is cut through the middle. If all selected detail images are complete, translate them in place. If any selected detail image cuts through the product/body or makes the information incomplete, enter detail-card regeneration mode: use the original detail images only and generate a coherent English set of standalone cards, targeting 12 but never exceeding 12. If the source cannot support 12 independent cards, produce fewer rather than inventing information. If a square output is needed, use safe padding/re-layout or generation rather than cutting the product body. Keep the product proportions unchanged, do not stretch or distort it, and keep all essential product information inside each card.
- First detail images should clearly show product body, selling points, and key information.
- Exclude:
  - brand introduction images,
  - awards/honor images,
  - product review images,
  - offline store display images.

## SKU images

- Translate descriptive Chinese directly into English while preserving the subject, composition, structure, and dimensions.
- Upload exactly one corresponding SKU image for each SKU; preserve the SKU-to-image mapping and never change the number of SKU images.

## Attributes

- Default brand: No Brand.
- Required attributes must be filled from actual evidence.
- Do not invent missing required attributes.

## SKU and sales data

- SKU setup follows the provided Pinduoduo product link or SKU evidence.
- SKU image must match SKU name.
- SKU name must not exceed 30 characters.
- If source SKU name is too long, shorten without changing meaning.
- Stock follows source SKU stock when the source provides it; if SKU stock is not shown or cannot be verified, use `100` and record it as the default `stock_source=default_100` for human review.
- Selling price defaults to 2x the corresponding Pinduoduo SKU price.
- Item code and product code are blank by default.

## Logistics and condition

- Default weight: 0.2 kg.
- Default days to ship: 1.
- Package length/width/height are blank by default unless confirmed.
- Condition: New.

## Pre-create checklist

- Main images satisfy count/size/aspect requirements.
- Product video included if supplied.
- Title is English and under 180 characters.
- Category selected from appropriate Shopee category evidence.
- Description is English, fact-backed, and under 500 words.
- Detail images are compliant and filtered.
- Brand is No Brand unless valid brand evidence exists.
- Required attributes are evidence-backed.
- SKU names/images/stock match source evidence.
- SKU prices follow source price x 2 unless user overrides.
- Weight, days to ship, and condition follow defaults unless user overrides.
