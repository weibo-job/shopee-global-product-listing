#!/usr/bin/env python3
"""详情图分析用长画布：拼接（build）与按 y 边界切分（split）。

用法:
  # 按文件名顺序把目录内图片统一宽度后纵向拼成"仅用于分析"的长画布
  python3 long_canvas.py build --dir <图片目录> --out <canvas.png> [--width N]

  # 按切分线（y 像素坐标，含首 0）把长画布切成候选卡
  python3 long_canvas.py split --canvas <canvas.png> --boundaries "0,1280,2560" \
      --out-dir <cards 目录> [--prefix card]

说明:
  - build 输出 segments（每张源图的 y 区间），供边界定位回溯 source_order。
  - split 只做确定性像素切割；切出的图是"候选卡"，必须再通过
    shopee-global-product-listing 的完整性三查与审计后才可用。
"""

import argparse
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

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
NUM_PREFIX = re.compile(r"^(\d+)")


def cmd_build(args):
    files = sorted(
        os.path.join(args.dir, n) for n in os.listdir(args.dir)
        if os.path.isfile(os.path.join(args.dir, n)) and os.path.splitext(n)[1].lower() in EXTS
    )
    if not files:
        print(json.dumps({"ok": False, "error": "NO_IMAGES", "detail": args.dir}, ensure_ascii=False))
        return 1

    images = []
    for p in files:
        im = Image.open(p)
        im.load()
        images.append((os.path.basename(p), im.convert("RGB")))

    widths = [im.width for _n, im in images]
    target_w = args.width or min(widths)  # 统一到最窄宽，避免上采样失真
    total_h, segments, canvas_parts = 0, [], []
    for name, im in images:
        if im.width != target_w:
            new_h = round(im.height * target_w / im.width)
            im = im.resize((target_w, new_h), Image.LANCZOS)
        m = NUM_PREFIX.match(name)
        segments.append({
            "file_name": name,
            "source_order": int(m.group(1)) if m else None,
            "y0": total_h,
            "y1": total_h + im.height,
        })
        canvas_parts.append(im)
        total_h += im.height

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    canvas = Image.new("RGB", (target_w, total_h), (255, 255, 255))
    offset = 0
    for seg, part in zip(segments, canvas_parts):
        canvas.paste(part, (0, offset))
        seg["resized"] = part.width != target_w
        offset += part.height
    canvas.save(args.out, quality=95)
    print(json.dumps({"ok": True, "canvas": os.path.abspath(args.out),
                      "width": target_w, "height": total_h,
                      "count": len(segments), "segments": segments}, ensure_ascii=False, indent=2))
    return 0


def cmd_split(args):
    if not os.path.isfile(args.canvas):
        print(json.dumps({"ok": False, "error": "CANVAS_MISSING", "detail": args.canvas}, ensure_ascii=False))
        return 1
    try:
        bounds = sorted({int(b) for b in str(args.boundaries).split(",") if str(b).strip() != ""})
    except ValueError:
        print(json.dumps({"ok": False, "error": "ARG_ERROR",
                          "detail": "boundaries 须为逗号分隔的整数 y 坐标"}, ensure_ascii=False))
        return 2
    if len(bounds) < 2 or bounds[0] != 0:
        bounds = [0] + bounds

    os.makedirs(args.out_dir, exist_ok=True)
    canvas = Image.open(args.canvas).convert("RGB")
    cards = []
    for i in range(len(bounds) - 1):
        y0, y1 = bounds[i], min(bounds[i + 1], canvas.height)
        if y1 - y0 <= 0:
            continue
        card = canvas.crop((0, y0, canvas.width, y1))
        out_path = os.path.join(args.out_dir, f"{args.prefix}{i + 1:03d}.png")
        card.save(out_path)
        cards.append({"card_file": out_path, "canvas_range": [y0, y1],
                      "width": card.width, "height": card.height,
                      "ratio": round(card.width / card.height, 4)})
    print(json.dumps({"ok": True, "out_dir": os.path.abspath(args.out_dir),
                      "cards": cards,
                      "note": "候选卡需通过父技能完整性三查后才可用"}, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--dir", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--width", type=int)
    b.set_defaults(func=cmd_build)

    s = sub.add_parser("split")
    s.add_argument("--canvas", required=True)
    s.add_argument("--boundaries", required=True)
    s.add_argument("--out-dir", required=True)
    s.add_argument("--prefix", default="card")
    s.set_defaults(func=cmd_split)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
