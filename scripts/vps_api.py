#!/usr/bin/env python3
"""Shopee VPS helper 调用器（shopee-global-product-listing 专用，主执行通道）。

对用户配置的 Seller In-House System helper 发起调用；
helper 服务端持有 Partner Key 与 token 并负责签名，客户端不接触任何密钥。

用法:
  python3 vps_api.py '<JSON 参数>' [--inline] [--out-dir <目录>]

JSON 参数（按 action）:
  action=category        全球类目树: {}（可选 language）
  action=attributes      类目属性: {"category_id": ...}
  action=brand_list      品牌列表: {"category_id":..., "offset":0, "page_size":20}
  action=item_list       全球商品列表: {"offset":0, "page_size":20}
  action=item_info       商品回读: {"global_item_id_list": "id1,id2"}
  action=create          创建全球商品: {"item": {...}}（自动加 confirm_create=true）
  action=update          修复更新: {"global_item_id":..., "item": {...}}
  action=tier_variations 初始化变体: {"global_item_id":..., "tier_variation":[...], "global_model":[...]}
  action=model_list      变体回读: {"global_item_id": ...}
  action=upload_image    图片上传: {"image_path":"/VPS路径/x.jpg", "shop_id":店铺ID,
                         "scene":"main|detail|sku", "audit_receipt_path":"本地回执",
                         "audit_final_file":"对应的本地英文终图"}
                         image_path 是 VPS 上的路径——先 scp 上去（见 SKILL.md 媒体上传流程）
  action=raw             任意已注册路由: {"method":"GET|POST", "endpoint":"/api/shopee/xxx",
                          "queryString":"a=1", "body":{...}}

通用可选字段: _query (附加查询串), image_path (multipart 上传)

配置:
  SHOPEE_HELPER_BASE 环境变量，或 ~/.shopee/credentials.json 的 "helper_base" 字段，
  未配置时不允许执行，避免误用其他用户的 helper

行为:
  - 完整响应落盘 <cwd>/shopee_api_logs/<date>/<session>/data/，--out-dir 额外归档
  - ≤8KB 打印全量; >8KB 打印摘要; --inline 强制全量
  - 拒绝任何含 publish 的路由（本技能只建 Global Product 草稿，不发布站点）
  - 所有媒体/创建/更新/变体写入在联网前强制验证本地审计回执和文件哈希
退出码: 0 成功(helper ok=true); 1 失败; 2 参数错误
"""

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
DEFAULT_HELPER = ""

ACTIONS = {
    "category":        ("GET",  "/api/shopee/global-category"),
    "attributes":      ("GET",  "/api/shopee/global-attributes"),
    "brand_list":      ("GET",  "/api/shopee/global-brand-list"),
    "item_list":       ("GET",  "/api/shopee/global-products"),
    "item_info":       ("GET",  "/api/shopee/global-item-info"),
    "create":          ("POST", "/api/shopee/global-items"),
    "update":          ("POST", "/api/shopee/global-item-update"),
    "tier_variations": ("POST", "/api/shopee/global-tier-variations"),
    "model_list":      ("GET",  "/api/shopee/global-model-list"),
    "upload_image":    ("POST", "/api/shopee/media/upload-image"),
    "status":          ("GET",  "/api/shopee/status"),
}


def fail(payload, code):
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(code)


def helper_base():
    base = (os.environ.get("SHOPEE_HELPER_BASE") or "").strip()
    if not base:
        try:
            with open(os.path.expanduser(os.environ.get("SHOPEE_CREDENTIALS_FILE")
                                         or "~/.shopee/credentials.json")) as f:
                base = str(json.load(f).get("helper_base", "")).strip()
        except (OSError, ValueError):
            pass
    if not (base or DEFAULT_HELPER):
        fail({"ok": False, "error": "HELPER_NOT_CONFIGURED",
              "detail": "请配置 SHOPEE_HELPER_BASE 或 credentials.json 的 helper_base"}, 2)
    return (base or DEFAULT_HELPER).rstrip("/")


def build_request(base, params):
    action = params.get("action")
    image_path = params.get("image_path")
    if action == "raw":
        method = str(params.get("method") or "GET").upper()
        endpoint = str(params.get("endpoint") or "")
        if not endpoint.startswith("/api/shopee/"):
            fail({"ok": False, "error": "ARG_ERROR",
                  "detail": "raw endpoint 必须以 /api/shopee/ 开头"}, 2)
    elif action in ACTIONS:
        method, endpoint = ACTIONS[action]
    else:
        fail({"ok": False, "error": "ARG_ERROR",
              "detail": f"未知 action: {action}；可用: {', '.join(sorted(ACTIONS))} 或 raw"}, 2)

    if "publish" in endpoint.lower():
        fail({"ok": False, "error": "PUBLISH_BLOCKED",
              "detail": "本技能边界：只创建 Global Product 草稿，禁止发布到站点店铺",
              "publish_called": False}, 2)

    gate_action = action
    if action == "raw" and method == "POST":
        if "upload-image" in endpoint:
            gate_action = "upload_image"
        elif "tier-variation" in endpoint:
            gate_action = "tier_variations"
        elif "global-item-update" in endpoint:
            gate_action = "update"
        elif "global-items" in endpoint:
            gate_action = "create"
    try:
        require_write_receipt(params, gate_action)
    except ValueError as exc:
        fail({"ok": False, "error": "ASSET_AUDIT_REQUIRED", "detail": str(exc)}, 2)

    url = base + endpoint
    query = {}
    for k, v in params.items():
        if k.startswith("_") or k in ("body", "item", "image_path", "action",
                                      "method", "endpoint", "queryString",
                                      "audit_receipt_path", "audit_final_file"):
            continue
        if v is not None:
            query[k] = v
    extra_q = params.get("_query") or params.get("queryString")
    if extra_q:
        for pair in str(extra_q).split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                query[k] = v
    if query and method == "GET":
        url += "?" + "&".join(f"{k}={v}" for k, v in query.items())

    data = headers = None
    if method == "POST":
        if action == "upload_image":
            # helper 的上传接口收 JSON：image_path 必须是 VPS 上的路径
            # （先用 scp/ssh 把图传到 VPS staging，如 /tmp/shopee_jobs_shopeejob/<goods_id>/）
            body = {
                "image_path": params.get("image_path"),
                "shop_id": params.get("shop_id"),
                "scene": params.get("scene"),
                "ratio": params.get("ratio"),
            }
            if not body["image_path"]:
                fail({"ok": False, "error": "ARG_ERROR",
                      "detail": "upload_image 需要 image_path（VPS 上的绝对路径，先 scp 上去）"}, 2)
            if not body["shop_id"]:
                fail({"ok": False, "error": "ARG_ERROR",
                      "detail": "upload_image 需要 shop_id（media_space 必须以 shop_id 签名）"}, 2)
            data = json.dumps(body, ensure_ascii=False).encode()
            headers = {"Content-Type": "application/json"}
        else:
            body = params.get("body")
            if body is None and params.get("item") is not None:
                body = {"item": params["item"]}
            if action == "create" and isinstance(body, dict):
                body.setdefault("confirm_create", True)
            if action == "tier_variations" and isinstance(body, dict):
                body.setdefault("confirm_create", True)
            data = json.dumps(body or {}, ensure_ascii=False).encode()
            headers = {"Content-Type": "application/json"}
    return method, url, data, headers, endpoint


def out_root():
    root = os.path.join(os.getcwd(), "shopee_api_logs")
    try:
        os.makedirs(root, exist_ok=True)
        probe = os.path.join(root, ".probe")
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
    for k in ("ok", "error", "merchant_id"):
        if k in d:
            s[k] = d[k]
    resp = d.get("shopee_response") if isinstance(d.get("shopee_response"), dict) else d
    if isinstance(resp, dict):
        r = resp.get("response") if isinstance(resp.get("response"), dict) else {}
        for k in ("global_item_id", "total", "category_list"):
            if k in r:
                v = r[k]
                s[k] = f"list[{len(v)}]" if isinstance(v, list) else v
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
            saved = os.path.join(
                data_dir, f"{SLUG}-vps-{time.strftime('%H%M%S', time.localtime(started_ts))}-{secrets.token_hex(2)}.json")
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
    if inline or len(raw_text or "") <= SMALL_THRESHOLD:
        print(json.dumps(result, ensure_ascii=False))
    else:
        slim = dict(result)
        slim.pop("response", None)
        slim["response_summary"] = summarize(raw_text or "")
        print(json.dumps(slim, ensure_ascii=False))


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
              "detail": "用法: vps_api.py '<JSON>' [--inline] [--out-dir <dir>]"}, 2)
    try:
        params = json.loads(positional[0])
    except ValueError as exc:
        fail({"ok": False, "error": "JSON_PARSE", "detail": str(exc)}, 2)
    if not isinstance(params, dict):
        fail({"ok": False, "error": "ARG_ERROR", "detail": "参数须为 JSON 对象"}, 2)

    started = time.time()
    try:
        method, url, data, headers, endpoint = build_request(helper_base(), params)
    except SystemExit:
        raise
    req = Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urlopen(req, timeout=300) as resp:
            text = resp.read().decode(errors="replace")
            status = resp.status
    except HTTPError as exc:
        try:
            text = exc.read().decode(errors="replace")
        except Exception:
            text = ""
        status = exc.code
    except URLError as exc:
        emit({"ok": False, "error": "NETWORK_ERROR", "detail": str(exc.reason),
              "helper": helper_base()}, None, inline, out_dir, started)
        sys.exit(1)

    try:
        wrapper = json.loads(text)
    except ValueError:
        wrapper = None
    ok = status == 200 and isinstance(wrapper, dict) and wrapper.get("ok") is not False \
        and not wrapper.get("error")
    shopee_resp = (wrapper or {}).get("shopee_response") or {}
    shopee_err = shopee_resp.get("error") if isinstance(shopee_resp, dict) else ""
    if shopee_err:
        ok = False
    result = {
        "ok": bool(ok),
        "request": {"action": params.get("action"), "endpoint": endpoint, "method": method},
        "httpStatus": status,
        "shopee_error": shopee_err or "",
        "elapsed_ms": int((time.time() - started) * 1000),
        "response": wrapper if wrapper is not None else text,
    }
    emit(result, text, inline, out_dir, started)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
