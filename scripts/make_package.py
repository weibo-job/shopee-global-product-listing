#!/usr/bin/env python3
"""创建标准化商品包目录结构（幂等）。

用法:
  python3 make_package.py --root <输出根目录> [--goods-id <商品号>] [--name <自定义目录名>]

目录名优先级: --name > --goods-id > 上架YYYYMMDD。
已存在的文件/目录一律不覆盖。输出创建后的包路径 JSON。
"""

import argparse
import datetime
import json
import os
import sys

GROUPS = ["01_主图", "02_详情图", "03_SKU图"]
EVIDENCE = ["page_inventory.json", "manifest_主图.json", "manifest_详情图.json", "manifest_SKU图.json"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root")
    ap.add_argument("--goods-id")
    ap.add_argument("--name")
    args = ap.parse_args()

    root = args.root or os.environ.get("SHOPEE_LISTING_OUTPUT_DIR") or os.path.join(os.getcwd(), "shopee-listing")
    folder = args.name or args.goods_id or f"上架{datetime.date.today():%Y%m%d}"
    pkg = os.path.join(root, folder)

    dirs = [pkg,
            *[os.path.join(pkg, "原图", g) for g in GROUPS],
            os.path.join(pkg, "原图", "视频"),
            os.path.join(pkg, "原图", "_evidence"),
            os.path.join(pkg, "原图", "_analysis"),
            *[os.path.join(pkg, "英文版", g) for g in GROUPS],
            os.path.join(pkg, "英文版", "api_work")]
    created = []
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            created.append(os.path.relpath(d, pkg))

    pkg_json = os.path.join(pkg, "package.json")
    if not os.path.exists(pkg_json):
        with open(pkg_json, "w", encoding="utf-8") as f:
            json.dump({
                "skill": "shopee-global-product-listing",
                "packager": "shopee-listing-packager",
                "goods_id": args.goods_id,
                "created_at": datetime.datetime.now().astimezone().isoformat(),
                "publish_boundary": "global_product_only",
                "status": "archiving",
            }, f, ensure_ascii=False, indent=2)
        created.append("package.json")
    # 预置证据占位（不覆盖已有）
    for name in EVIDENCE:
        p = os.path.join(pkg, "原图", "_evidence", name)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"note": "待 shopee-listing-packager 填写"}, f, ensure_ascii=False)
            created.append(f"原图/_evidence/{name}")

    print(json.dumps({"ok": True, "package": pkg, "created": created},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
