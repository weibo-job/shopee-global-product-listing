#!/usr/bin/env python3
"""用授权回调的 code 换取 access_token / refresh_token 并写入本地 token store。

用法:
  python3 exchange_code.py --scope merchant --code <code> --merchant-id <id>
  python3 exchange_code.py --scope shop    --code <code> --shop-id <id>

调用 POST /api/v2/public/get_access_token（public 签名），成功后把
access_token/refresh_token/expire_at 写入 ${SHOPEE_TOKEN_STORE:-~/.shopee/tokens.json}。
绝不打印任何 token 明文。
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from urllib.request import Request, urlopen

DEFAULT_HOST = os.environ.get("SHOPEE_HOST") or "https://partner.shopeemobile.com"
STORE = os.path.expanduser(os.environ.get("SHOPEE_TOKEN_STORE") or "~/.shopee/tokens.json")


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
    ap.add_argument("--code", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--merchant-id")
    group.add_argument("--shop-id")
    ap.add_argument("--host")
    args = ap.parse_args()

    pid, key, cred_host = _load_cred()
    host_env = cred_host
    if not pid or not key:
        print(json.dumps({"ok": False, "error": "PARTNER_CREDENTIALS_MISSING"}, ensure_ascii=False))
        return 1
    host = (args.host or host_env or DEFAULT_HOST or "https://partner.shopeemobile.com").rstrip("/")
    path = "/api/v2/public/get_access_token"
    ts = int(time.time())
    sign = hmac.new(key.encode(), f"{pid}{path}{ts}".encode(), hashlib.sha256).hexdigest()
    ident_field = "merchant_id" if args.merchant_id else "shop_id"
    ident_value = int(args.merchant_id or args.shop_id)
    body = {"code": args.code, "partner_id": int(pid), ident_field: ident_value}
    url = f"{host}{path}?partner_id={pid}&timestamp={ts}&sign={sign}"
    req = Request(url, data=json.dumps(body).encode(),
                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": "TOKEN_EXCHANGE_FAILED", "detail": str(exc)},
                         ensure_ascii=False))
        return 1
    if not data.get("access_token"):
        print(json.dumps({"ok": False, "error": "SHOPEE_ERROR", "shopee": data}, ensure_ascii=False))
        return 1

    now = time.time()
    store = {}
    try:
        with open(STORE, "r", encoding="utf-8") as f:
            store = json.load(f)
    except (OSError, ValueError):
        pass
    entries = store.setdefault("entries", {})
    entry = {
        "type": args.scope,
        "host": host,
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expire_at": now + int(data.get("expire_in", 14400)),
        "updated_at": now,
    }
    if data.get("refresh_in"):
        entry["refresh_expire_at"] = now + int(data["refresh_in"])
    # 回调里可能带出另一身份（商户主账号同时授权店铺），一并记录映射便于追溯
    extra_id = data.get("merchant_id" if args.scope == "shop" else "shop_id")
    entries[str(ident_value)] = entry
    store.setdefault("meta", {})[str(ident_value)] = {"scope": args.scope}
    if extra_id and str(extra_id) not in entries:
        store.setdefault("related_ids", {})[str(extra_id)] = str(ident_value)
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STORE)

    remain_h = round(int(data.get("expire_in", 14400)) / 3600, 1)
    print(json.dumps({"ok": True, "identity": ident_field, "id": str(ident_value),
                      "type": args.scope, "token_saved_to": STORE,
                      "access_token_valid_hours": remain_h,
                      "note": "全球商品用 merchant 授权；media 上传需另做 shop 授权"},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
