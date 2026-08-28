#!/usr/bin/env python3
"""生成 Shopee OpenAPI v2 授权链接（直连模式）。

用法:
  python3 gen_auth_url.py --scope merchant --redirect 'https://你的回调页' [--host https://partner.shopeemobile.com]
  python3 gen_auth_url.py --scope shop    --redirect '...'   [--host ...]

- 全球商品（global_product/*）必须用 merchant 授权；图片上传（media/upload_image）用 shop 授权。
- 链接 1 小时左右有效，过期重新生成本脚本即可。
- 用户在浏览器打开链接、用对应主账号/店铺账号登录授权后，
  Shopee 会重定向到 redirect 地址并附带 code 与 shop_id/merchant_id 参数；
  把 code 交给 exchange_code.py 完成 token 入库。
"""

import argparse
import hashlib
import hmac
import os
import sys
import time
from urllib.parse import quote

DEFAULT_HOST = os.environ.get("SHOPEE_HOST") or "https://partner.shopeemobile.com"


def _load_cred():
    """env 优先，其次 ~/.shopee/credentials.json。返回 (pid, key, host)。"""
    import json as _json
    pid = (os.environ.get("SHOPEE_PARTNER_ID") or "").strip()
    key = (os.environ.get("SHOPEE_PARTNER_KEY") or "").strip()
    host = (os.environ.get("SHOPEE_HOST") or "").strip()
    if pid and key and host:
        return pid, key, host
    try:
        with open(os.path.expanduser(os.environ.get("SHOPEE_CREDENTIALS_FILE")
                                     or "~/.shopee/credentials.json")) as f:
            c = _json.load(f)
        pid = pid or str(c.get("partner_id", "")).strip()
        key = key or str(c.get("partner_key", "")).strip()
        host = host or str(c.get("host", "")).strip()
    except (OSError, ValueError):
        pass
    return pid, key, host


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", required=True, choices=["merchant", "shop"])
    ap.add_argument("--redirect", required=True)
    ap.add_argument("--host")
    args = ap.parse_args()

    pid, key, cred_host = _load_cred()
    host_env = cred_host
    if not pid or not key:
        print(json_err("PARTNER_CREDENTIALS_MISSING",
                       "未配置 SHOPEE_PARTNER_ID / SHOPEE_PARTNER_KEY"))
        return 1
    host = (args.host or host_env or DEFAULT_HOST or "https://partner.shopeemobile.com").rstrip("/")
    path = f"/api/v2/{args.scope}/auth_partner"
    ts = int(time.time())
    sign = hmac.new(key.encode(), f"{pid}{path}{ts}".encode(), hashlib.sha256).hexdigest()
    url = (f"{host}{path}?partner_id={pid}&timestamp={ts}&sign={sign}"
           f"&redirect={quote(args.redirect, safe='')}")
    print(f"1. 用{'商户主账号' if args.scope == 'merchant' else '店铺账号'}在浏览器打开下面链接并完成授权：\n")
    print(url)
    print("\n2. 授权后从 redirect 回调地址取出 code（及 shop_id/merchant_id），运行：")
    print(f"   exchange_code.py --scope {args.scope} --code <code> "
          + (f"--merchant-id <merchant_id>" if args.scope == "merchant" else "--shop-id <shop_id>"))
    return 0


def json_err(code, detail):
    import json
    return json.dumps({"ok": False, "error": code, "detail": detail}, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
