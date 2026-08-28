#!/usr/bin/env python3
"""Atomically enqueue a prepared Shopee Global Product package."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import os
import secrets
import shutil
import sys


DEFAULT_QUEUE = pathlib.Path("/private/tmp/ShopeeJobRunner/queue")
DEFAULT_STAGING = pathlib.Path("/private/tmp/ShopeeJobRunner/jobs")
ALLOWED_ROOT = pathlib.Path(os.environ.get("SHOPEE_ALLOWED_ROOT") or os.getcwd()).expanduser().resolve()


def enqueue(
    goods_id: str,
    product_dir: pathlib.Path,
    runner: pathlib.Path,
    queue: pathlib.Path = DEFAULT_QUEUE,
    staging: pathlib.Path = DEFAULT_STAGING,
) -> pathlib.Path:
    product_dir = product_dir.expanduser().resolve()
    runner = runner.expanduser().resolve()
    queue = queue.expanduser().resolve()
    staging = staging.expanduser().resolve()
    try:
        runner.relative_to(product_dir)
    except ValueError:
        raise ValueError("runner must be inside product-dir")
    if not product_dir.is_dir() or not runner.is_file():
        raise ValueError("product directory or runner is missing")

    inbox = queue / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    job_id = f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{goods_id}-{secrets.token_hex(3)}"
    staged_dir = staging / job_id
    shutil.copytree(product_dir, staged_dir)
    staged_runner = staged_dir / runner.relative_to(product_dir)
    payload = {
        "schema_version": 1,
        "job_id": job_id,
        "goods_id": str(goods_id),
        "source_product_dir": str(product_dir),
        "product_dir": str(staged_dir),
        "runner": str(staged_runner),
        "created_at": dt.datetime.now().astimezone().isoformat(),
        "publish_boundary": "global_product_only",
    }
    temporary = inbox / f".{job_id}.tmp"
    ready = inbox / f"{job_id}.ready.json"
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(ready)
    return ready


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goods-id", required=True)
    parser.add_argument("--product-dir", required=True, type=pathlib.Path)
    parser.add_argument("--runner", type=pathlib.Path)
    parser.add_argument("--queue", type=pathlib.Path, default=DEFAULT_QUEUE)
    parser.add_argument("--staging", type=pathlib.Path, default=DEFAULT_STAGING)
    args = parser.parse_args()

    product_dir = args.product_dir.expanduser().resolve()
    try:
        product_dir.relative_to(ALLOWED_ROOT)
    except ValueError:
        raise SystemExit(f"product-dir must be under {ALLOWED_ROOT}")
    runner = (args.runner or product_dir / "run_stage1_prepare.sh").expanduser().resolve()
    try:
        ready = enqueue(str(args.goods_id), product_dir, runner, args.queue, args.staging)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(ready)
    return 0


if __name__ == "__main__":
    sys.exit(main())
