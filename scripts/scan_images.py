#!/usr/bin/env python3
"""扫描图片目录：尺寸/比例/MD5/组内去重，输出顺序清单 JSON。

用法:
  python3 scan_images.py <dir> [--manifest-out <path.json>] [--recursive]

输出（stdout）: JSON 清单，按文件名排序；source_order 取文件名数字前缀（如 001.jpg -> 1），
无前缀则按排序序号。duplicate_of 指向组内首个同 MD5 文件。
"""

import argparse
import hashlib
import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:
    print(json.dumps({"ok": False, "error": "PILLOW_MISSING",
                      "hint": "pip3 install Pillow"}), file=sys.stderr)
    sys.exit(2)

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
NUM_PREFIX = re.compile(r"^(\d+)")


def md5sum(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--manifest-out")
    ap.add_argument("--recursive", action="store_true")
    args = ap.parse_args()

    root = args.directory
    if not os.path.isdir(root):
        print(json.dumps({"ok": False, "error": "DIR_MISSING", "detail": root}, ensure_ascii=False))
        sys.exit(1)

    files = []
    if args.recursive:
        for dirpath, _dirs, names in os.walk(root):
            for n in names:
                p = os.path.join(dirpath, n)
                if os.path.splitext(n)[1].lower() in EXTS:
                    files.append(p)
        files.sort()
    else:
        files = sorted(
            os.path.join(root, n) for n in os.listdir(root)
            if os.path.isfile(os.path.join(root, n)) and os.path.splitext(n)[1].lower() in EXTS
        )

    entries, seen_md5, errors = [], {}, []
    for idx, path in enumerate(files, start=1):
        name = os.path.basename(path)
        m = NUM_PREFIX.match(name)
        entry = {
            "source_order": int(m.group(1)) if m else idx,
            "local_file": path,
            "file_name": name,
        }
        try:
            with Image.open(path) as im:
                w, h = im.size
            entry.update(width=w, height=h,
                         ratio=round(w / h, 4) if h else None,
                         md5=md5sum(path), download_status="ok")
            first = seen_md5.get(entry["md5"])
            entry["duplicate_of"] = first if first and first != name else None
            seen_md5.setdefault(entry["md5"], name)
        except Exception as exc:  # noqa: BLE001
            entry["download_status"] = "error"
            entry["error"] = str(exc)
            errors.append(name)
        entries.append(entry)

    ok_count = sum(1 for e in entries if e.get("download_status") == "ok")
    dup_count = sum(1 for e in entries if e.get("duplicate_of"))
    result = {
        "ok": True,
        "directory": root,
        "total": len(entries),
        "readable": ok_count,
        "duplicates": dup_count,
        "errors": errors,
        "entries": entries,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.manifest_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.manifest_out)), exist_ok=True)
        with open(args.manifest_out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        result["manifest_saved_to"] = os.path.abspath(args.manifest_out)
    print(text)


if __name__ == "__main__":
    main()
