#!/usr/bin/env python3
"""安装后静态配置检查；不发起 Shopee 写请求，也不输出任何密钥。"""

import json
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REQUIRED = (
    "scan_images.py",
    "make_package.py",
    "long_canvas.py",
    "validate_listing_draft.py",
    "validate_asset_audit.py",
    "asset_audit_gate.py",
    "shopee_api.py",
    "vps_api.py",
    "gen_auth_url.py",
    "exchange_code.py",
    "token_status.py",
)


def configured_credentials():
    helper = os.environ.get("SHOPEE_HELPER_BASE", "").strip()
    partner_id = os.environ.get("SHOPEE_PARTNER_ID", "").strip()
    partner_key = os.environ.get("SHOPEE_PARTNER_KEY", "").strip()
    config_path = Path(os.path.expanduser(
        os.environ.get("SHOPEE_CREDENTIALS_FILE", "~/.shopee/credentials.json")
    ))
    data = {}
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False, False, "credentials.json 无法解析"
    helper = helper or str(data.get("helper_base", "")).strip()
    partner_id = partner_id or str(data.get("partner_id", "")).strip()
    partner_key = partner_key or str(data.get("partner_key", "")).strip()
    shop_or_merchant = bool(
        os.environ.get("SHOPEE_SHOP_ID", "").strip()
        or os.environ.get("SHOPEE_MERCHANT_ID", "").strip()
        or data.get("shop_id")
        or data.get("merchant_id")
    )
    token_path = Path(os.path.expanduser(
        os.environ.get("SHOPEE_TOKEN_STORE", "~/.shopee/tokens.json")
    ))
    direct_ok = bool(partner_id and partner_key and shop_or_merchant and token_path.is_file())
    return bool(helper), direct_ok, str(config_path), token_path.is_file()


def main():
    missing = [name for name in REQUIRED if not (HERE / name).is_file()]
    helper_ok, direct_ok, source, token_store_present = configured_credentials()
    result = {
        "ok": not missing and (helper_ok or direct_ok),
        "scripts": {"missing": missing, "count": len(REQUIRED) - len(missing)},
        "api": {
            "helper_configured": helper_ok,
            "direct_credentials_configured": direct_ok,
            "config_source": source,
            "token_store_present": token_store_present,
        },
        "writes_performed": False,
    }
    if not result["ok"]:
        result["next_step"] = (
            "配置 SHOPEE_HELPER_BASE，或配置 SHOPEE_PARTNER_ID/SHOPEE_PARTNER_KEY "
            "及授权 Token 后重试；不要使用他人的 helper。"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
