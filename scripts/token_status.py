#!/usr/bin/env python3
"""查看 token store 授权状态（只显示元数据，绝不输出 token 明文）。

用法:
  python3 token_status.py
"""

import json
import os
import sys
import time

STORE = os.path.expanduser(os.environ.get("SHOPEE_TOKEN_STORE") or "~/.shopee/tokens.json")


def main():
    try:
        with open(STORE, "r", encoding="utf-8") as f:
            store = json.load(f)
    except (OSError, ValueError):
        print(json.dumps({"ok": True, "entries": [], "note": "token store 为空，先跑 gen_auth_url.py 授权"},
                         ensure_ascii=False))
        return 0
    now = time.time()
    rows = []
    for key, e in (store.get("entries") or {}).items():
        exp = e.get("expire_at", 0)
        rows.append({
            "identity_id": key,
            "type": e.get("type"),
            "host": e.get("host"),
            "access_token_state": ("valid" if exp and exp - now > 120 else
                                   "expiring/expired" if exp else "unknown"),
            "expires_in_minutes": max(0, round((exp - now) / 60)) if exp else None,
            "has_refresh_token": bool(e.get("refresh_token")),
            "refresh_token_expired": bool(e.get("refresh_expire_at") and now > e["refresh_expire_at"]),
        })
    print(json.dumps({"ok": True, "store": STORE, "entries": rows,
                      "hint": "全球商品需 merchant 条目；media 上传需 shop 条目"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
