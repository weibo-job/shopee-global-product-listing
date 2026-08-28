#!/usr/bin/env python3
"""Shopee Open Platform v2 直连调用器（shopee-global-product-listing 专用）。

直接对 Shopee OpenAPI 签名调用（partner 凭证 + 店铺/商户 OAuth token），
不经过任何第三方代理。签名规则：
  - 普通接口: HMAC-SHA256(partner_key, partner_id+path+timestamp+access_token+shop_id|merchant_id)
  - public/token 接口(/api/v2/public/*): HMAC-SHA256(partner_key, partner_id+path+timestamp)

用法:
  python3 shopee_api.py '<JSON 参数>' [--inline] [--out-dir <目录>]

JSON 参数:
  path         必填；如 api/v2/global_product/get_category（可带或不带前导斜杠）
  method       GET（默认）或 POST
  shop_id      店铺级身份（api/v2/media/* 上传用）
  merchant_id  商户级身份（api/v2/global_product/* 用）；二选一，
               都不传时按 path 自动从 token store 选择唯一匹配项
  queryString  GET 查询串，如 "offset=0&page_size=20&language=en"
  body         POST 的 JSON 对象（如 add_global_item 的完整商品结构）
  image_path   仅 media/upload_image：本地图片路径，脚本改走 multipart/form-data 上传
  audit_receipt_path  媒体/创建/更新/变体写入必填；英文版审计回执的本地路径
  audit_final_file    media/upload_image 必填；本次上传对应的已审计英文终图

凭证（环境变量）:
  SHOPEE_PARTNER_ID   应用 ID（必填）
  SHOPEE_PARTNER_KEY  应用密钥（必填；绝不打印）
  SHOPEE_HOST         默认 https://partner.shopeemobile.com；
                      中国大陆开发者门户用 https://openplatform.shopee.cn

Token store（${SHOPEE_TOKEN_STORE:-~/.shopee/tokens.json}）:
  {"entries": {"<shop_id|merchant_id>": {"type":"shop|merchant","host":...,
    "access_token":...,"refresh_token":...,"expire_at":...,"refresh_expire_at":...}}}
  access_token 剩余 <120s 时自动用 refresh_token 刷新并回写。
  用 gen_auth_url.py / exchange_code.py / token_status.py 管理授权。

行为:
  - 完整响应始终落盘: <cwd>/shopee_api_logs/<YYYY-MM-DD>/<session>/data/<slug>-<ts>.json
    （--out-dir 指定时额外复制一份到该目录，用于商品包 api_work 归档）
  - ≤8KB 打印全量 JSON; >8KB 打印摘要; --inline 强制全量
  - 绝不打印 Partner Key 或任何 token; 硬禁止 create_publish_task 等站点发布调用
  - 所有媒体/创建/更新/变体写入在联网前强制验证审计回执和文件哈希
退出码: 0 成功(Shopee 无 error); 2 参数错误; 1 请求失败/error 非空
"""

import hashlib
import hmac
import json
import os
import secrets
import shutil
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from asset_audit_gate import require_write_receipt

SLUG = "shopee-global-product-listing"
SMALL_THRESHOLD = 8000
BLOCKED_PATHS = {
    "api/v2/global_product/create_publish_task",
    "api/v2/global_product/set_sync_field",
}
PUBLIC_PREFIX = "/api/v2/public/"
CRED_FILE = "~/.shopee/credentials.json"
DEFAULT_HOST_FALLBACK = "https://partner.shopeemobile.com"
TOKEN_MARGIN_SECONDS = 120


def load_credentials():
    """环境变量优先；否则读 ${SHOPEE_CREDENTIALS_FILE:-~/.shopee/credentials.json}。"""
    pid = (os.environ.get("SHOPEE_PARTNER_ID") or "").strip()
    key = (os.environ.get("SHOPEE_PARTNER_KEY") or "").strip()
    host = (os.environ.get("SHOPEE_HOST") or "").strip()
    if pid and key and host:
        return pid, key, host
    try:
        with open(os.path.expanduser(os.environ.get("SHOPEE_CREDENTIALS_FILE") or CRED_FILE),
                  "r", encoding="utf-8") as f:
            cred = json.load(f)
        pid = pid or str(cred.get("partner_id", "")).strip()
        key = key or str(cred.get("partner_key", "")).strip()
        host = host or str(cred.get("host", "")).strip()
    except (OSError, ValueError):
        pass
    return pid, key, host


def get_host(entry=None):
    return (entry or {}).get("host") or load_credentials()[2] or DEFAULT_HOST_FALLBACK


def fail(payload, code):
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(code)


# ---------------------------------------------------------------- credentials

def partner_creds():
    pid, key, _host = load_credentials()
    if not pid or not key:
        fail({
            "ok": False,
            "error": "PARTNER_CREDENTIALS_MISSING",
            "hint": "未找到凭证。请配置 SHOPEE_PARTNER_ID / SHOPEE_PARTNER_KEY 环境变量，"
                    "或写入 ~/.shopee/credentials.json：{\"partner_id\":..., \"partner_key\":..., \"host\":...}",
        }, 1)
    return pid, key


def sign(partner_key, parts):
    base = "".join(str(p) for p in parts)
    return hmac.new(partner_key.encode(), base.encode(), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------- token store

def store_path():
    return os.path.expanduser(os.environ.get("SHOPEE_TOKEN_STORE") or "~/.shopee/tokens.json")


def load_store():
    try:
        with open(store_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_store(data):
    path = store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def pick_entry(params, path_no_slash):
    """选 token 条目：显式 id 优先；否则按 path 类型自动匹配（须唯一）。"""
    store = load_store()
    entries = store.get("entries") or {}
    want_type = "shop" if path_no_slash.startswith("/api/v2/media/") else (
        "merchant" if path_no_slash.startswith("/api/v2/global_product/") else None)
    sid, mid = params.get("shop_id"), params.get("merchant_id")
    if sid or mid:
        key = str(sid or mid)
        ent = entries.get(key)
        if not ent:
            fail({"ok": False, "error": "NO_TOKEN_FOR_IDENTITY",
                  "detail": f"{key} 不在 token store；先跑 gen_auth_url.py + exchange_code.py 授权"}, 2)
        return key, ent, store
    cands = [(k, e) for k, e in entries.items()
             if want_type is None or e.get("type") == want_type]
    if not cands:
        fail({"ok": False, "error": "EMPTY_TOKEN_STORE",
              "detail": "无可用授权条目；先跑 gen_auth_url.py 生成授权链接完成授权"}, 2)
    if len(cands) > 1 and want_type is None:
        fail({"ok": False, "error": "AMBIGUOUS_IDENTITY",
              "detail": f"store 有多条授权 {[k for k,_ in cands]}，请显式传 shop_id 或 merchant_id"}, 2)
    if len(cands) > 1:
        fail({"ok": False, "error": "AMBIGUOUS_IDENTITY",
              "detail": f"多条 {want_type} 授权 {[k for k, _ in cands]}，请显式指定"}, 2)
    k, e = cands[0]
    return k, e, store


# ---------------------------------------------------------------- refresh/HTTP

def do_post_json(host, path, pid, key, body):
    ts = int(time.time())
    qs = f"partner_id={pid}&timestamp={ts}&sign={sign(key, [pid, path, ts])}"
    url = f"{host}{path}?{qs}"
    req = Request(url, data=json.dumps(body, ensure_ascii=False).encode(),
                  headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def ensure_fresh(entry_key, entry, store):
    """过期前自动刷新；返回 (access_token, host)。失败不抛异常——由主流程按错误处理。"""
    host = get_host(entry)
    exp = entry.get("expire_at")
    tok = entry.get("access_token")
    if tok and exp and exp - time.time() > TOKEN_MARGIN_SECONDS:
        return tok, host
    rt = entry.get("refresh_token")
    rexp = entry.get("refresh_expire_at")
    if not rt:
        return tok, host  # 无 refresh token，交给业务报 invalid_access_token
    if rexp and time.time() > rexp:
        return tok, host  # refresh token 也过期，需重新授权
    pid, key = partner_creds()
    ident_field = "shop_id" if entry.get("type") == "shop" else "merchant_id"
    try:
        resp = do_post_json(host, "/api/v2/public/refresh_access_token", pid, key,
                            {"refresh_token": rt, ident_field: int(entry_key),
                             "partner_id": int(pid)})
    except Exception:
        return tok, host
    if resp.get("access_token"):
        entry.update(access_token=resp["access_token"],
                     refresh_token=resp.get("refresh_token", rt),
                     expire_at=time.time() + int(resp.get("expire_in", 14400)),
                     refresh_expire_at=(time.time() + int(resp.get("refresh_in", 0))
                                        if resp.get("refresh_in") else entry.get("refresh_expire_at")))
        store.setdefault("entries", {})[entry_key] = entry
        try:
            save_store(store)
        except OSError:
            pass
        return entry["access_token"], host
    return tok, host


def call_api(host, path, pid, key, method, access_token, ident_field, ident_value,
             query_string=None, body=None, image_path=None):
    ts = int(time.time())
    sign_parts = [pid, path, ts]
    query = {"partner_id": pid, "timestamp": ts}
    if path.startswith(PUBLIC_PREFIX):
        query["sign"] = sign(key, sign_parts)
    else:
        query["sign"] = sign(key, sign_parts + [access_token, str(ident_value)])
        query["access_token"] = access_token
        query[ident_field] = ident_value
    if query_string:
        for pair in str(query_string).split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                query[k] = v
    ordered = "&".join(f"{k}={v}" for k, v in query.items())
    url = f"{host}{path}?{ordered}"

    data, headers = None, {}
    if method == "POST":
        if image_path:
            boundary = "----shopeeBoundary" + secrets.token_hex(8)
            with open(image_path, "rb") as f:
                img = f.read()
            mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
            parts = []
            for k, v in query.items():
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="image_data"; '
                          f'filename="{os.path.basename(image_path)}"\r\n'
                          f'Content-Type: {mime}\r\n\r\n').encode() + img + b"\r\n")
            parts.append(f"--{boundary}--\r\n".encode())
            data = b"".join(parts)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        else:
            data = json.dumps(body or {}, ensure_ascii=False).encode()
            headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    started = time.time()
    try:
        with urlopen(req, timeout=180) as resp:
            return resp.status, resp.read().decode(errors="replace"), int((time.time() - started) * 1000)
    except HTTPError as exc:
        try:
            txt = exc.read().decode(errors="replace")
        except Exception:
            txt = ""
        return exc.code, txt, int((time.time() - started) * 1000)


# ---------------------------------------------------------------- output

def out_root():
    root = os.path.join(os.getcwd(), "shopee_api_logs")
    try:
        probe = os.path.join(root, ".probe")
        os.makedirs(root, exist_ok=True)
        open(probe, "w").close()
        os.remove(probe)
        return root
    except OSError:
        return None


def summarize(text):
    try:
        d = json.loads(text)
    except ValueError:
        return {"summary": True, "bytes": len(text), "head": text[:400]}
    s = {"summary": True, "bytes": len(text), "top_level_keys": list(d)[:12]}
    for k in ("error", "msg", "request_id"):
        if k in d:
            s[k] = d[k]
    resp = d.get("response") if isinstance(d.get("response"), dict) else d
    for k in ("global_item_id", "total", "category_list"):
        if isinstance(resp, dict) and k in resp:
            s[k] = resp[k]
    return s


def emit(result, raw_text, inline, out_dir, started_ts):
    saved = None
    root = out_root()
    if root:
        date_s = time.strftime("%Y-%m-%d", time.localtime(started_ts))
        sess = (os.environ.get("SESSION_ID") or "").strip() or \
            time.strftime("%H%M%S", time.localtime(started_ts)) + "-" + secrets.token_hex(3)
        data_dir = os.path.join(root, date_s, sess, "data")
        try:
            os.makedirs(data_dir, exist_ok=True)
            saved = os.path.join(data_dir, f"{SLUG}-{time.strftime('%H%M%S', time.localtime(started_ts))}-{secrets.token_hex(2)}.json")
            with open(saved, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            result["saved_to"] = saved
        except OSError as exc:
            result["save_error"] = str(exc)
    if out_dir and saved:
        try:
            os.makedirs(out_dir, exist_ok=True)
            dst = os.path.join(out_dir, os.path.basename(saved))
            shutil.copyfile(saved, dst)
            result["archived_to"] = dst
        except OSError as exc:
            result["archive_error"] = str(exc)

    small = len(raw_text or "") <= SMALL_THRESHOLD
    if inline or small:
        print(json.dumps(result, ensure_ascii=False))
    else:
        slim = {k: v for k, v in result.items()}
        slim.pop("response", None)
        slim["response_summary"] = summarize(raw_text or "")
        print(json.dumps(slim, ensure_ascii=False))


# ---------------------------------------------------------------- main

def norm(path):
    return "/" + str(path).lstrip("/")


def main():
    args = sys.argv[1:]
    inline = "--inline" in args
    out_dir = None
    if "--out-dir" in args:
        i = args.index("--out-dir")
        if i + 1 >= len(args):
            fail({"ok": False, "error": "ARG_ERROR", "detail": "--out-dir 需要目录参数"}, 2)
        out_dir = args[i + 1]
        args = args[:i] + args[i + 2:]
    positional = [a for a in args if not a.startswith("-")]
    if len(positional) != 1:
        print(__doc__)
        fail({"ok": False, "error": "USAGE",
              "detail": "用法: shopee_api.py '<JSON>' [--inline] [--out-dir <dir>]"}, 2)
    try:
        params = json.loads(positional[0])
    except ValueError as exc:
        fail({"ok": False, "error": "JSON_PARSE", "detail": str(exc)}, 2)
    if not isinstance(params, dict) or not params.get("path"):
        fail({"ok": False, "error": "ARG_ERROR", "detail": "缺少 path"}, 2)

    # 兼容驼峰入参
    for camel, snake in (("shopId", "shop_id"), ("merchantId", "merchant_id"),
                         ("queryString", "queryString"), ("imagePath", "image_path")):
        if camel in params and snake not in params:
            params[snake] = params.pop(camel)

    path = norm(params["path"])
    method = str(params.get("method") or "GET").upper()
    if method not in ("GET", "POST"):
        fail({"ok": False, "error": "ARG_ERROR", "detail": f"method 不支持: {method}"}, 2)
    if not path.startswith("/api/v2/"):
        fail({"ok": False, "error": "ARG_ERROR",
              "detail": "path 必须以 api/v2/ 开头，例如 api/v2/global_product/get_category"}, 2)
    if path in BLOCKED_PATHS or "publish_task" in path:
        fail({"ok": False, "error": "PUBLISH_BLOCKED",
              "detail": "本技能边界：只创建 Global Product 草稿，禁止发布到站点店铺",
              "publish_called": False}, 2)

    gate_action = None
    if method == "POST":
        if path.endswith("/add_global_item"):
            gate_action = "create"
        elif path.endswith("/update_global_item"):
            gate_action = "update"
        elif path.endswith("/init_tier_variation"):
            gate_action = "tier_variations"
        elif path.endswith("/upload_image"):
            gate_action = "upload_image"
    try:
        require_write_receipt(params, gate_action)
    except ValueError as exc:
        fail({"ok": False, "error": "ASSET_AUDIT_REQUIRED", "detail": str(exc)}, 2)

    pid, key = partner_creds()

    public_call = path.startswith(PUBLIC_PREFIX)
    if public_call:
        access_token, ident_field, ident_value, host = "", "", "", get_host()
    else:
        entry_key, entry, store = pick_entry(params, path)
        access_token, host = ensure_fresh(entry_key, entry, store)
        ident_field = "shop_id" if entry.get("type") == "shop" else "merchant_id"
        ident_value = entry_key

    status, text, elapsed_ms = call_api(
        host, path, pid, key, method, access_token, ident_field, ident_value,
        query_string=params.get("queryString"), body=params.get("body"),
        image_path=params.get("image_path"))

    try:
        wrapper = json.loads(text)
    except ValueError:
        wrapper = None
    # Shopee v2 成功响应形如 {"error":"","msg":"","response":{...}}；失败 {"error":"xxx","msg":"..."}
    shopee_err = ""
    if isinstance(wrapper, dict):
        err = wrapper.get("error")
        if err not in (None, "", "none"):
            shopee_err = f"{err}: {wrapper.get('msg')}" if wrapper.get("msg") else str(err)
    ok = status == 200 and isinstance(wrapper, dict) and not shopee_err
    result = {
        "ok": ok,
        "request": {"path": path, "method": method,
                    "identity": ident_field if not public_call else "public"},
        "httpStatus": status,
        "elapsed_ms": elapsed_ms,
        "shopee_error": shopee_err,
        "response": wrapper if wrapper is not None else text,
    }
    emit(result, text, inline, out_dir, time.time())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
