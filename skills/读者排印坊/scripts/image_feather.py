#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片去框化：让插图边缘融入纸面（消除矩形硬边）

原理：矩形图直接放到版面上会形成"贴图感"，与纸面割裂。本脚本把图片四边
向版面纸色做渐隐（内部区域保持完全清晰，只在外缘过渡），实现"图与背景融合，
过渡自然，减少画面的割裂感"。不改变画面内容，不裁切主体。

做法：
    内 flat 比例完全保留原像素（不削弱主体）；外缘 t 由 0 升到 1，
    按 t 与纸色做线性混合，越靠边越接近纸色。

用法：
    python3 image_feather.py --src illustrations/opt --out illustrations/fade
    python3 image_feather.py --src light.png --out light_fade.png --paper "#FBF8F0" --band 64
    python3 image_feather.py --src in --out out --flat 0.5 --band 8%   # 按短边百分比给带

参数：
    --paper   版面纸色（须与 theme.css 的 --paper 一致），默认 #FBF8F0
    --band    渐隐带宽（像素或 N% 短边），默认 64
    --flat    内部完全清晰的占比（0–0.9），默认 0.42
    --quality JPEG 质量，默认 87
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def hex2rgb(h: str):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def feather_image(path: Path, out: Path, paper, band=64, flat=0.42, power=1.15, quality=87):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    b = int(band) if band >= 1 else max(4, int(min(h, w) * band))
    b = max(4, min(b, h // 3, w // 3))
    wy = np.minimum(np.arange(h), np.arange(h)[::-1]).astype(np.float32)
    wx = np.minimum(np.arange(w), np.arange(w)[::-1]).astype(np.float32)
    d = np.minimum(wy[:, None], wx[None, :])
    t = np.clip((1.0 - d / b - flat) / (1.0 - flat), 0.0, 1.0) ** power
    a = a * (1 - t[..., None]) + paper * t[..., None]
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".png":
        Image.fromarray(a.astype(np.uint8)).save(out, optimize=True)
    else:
        Image.fromarray(a.astype(np.uint8)).save(out, "JPEG", quality=quality, optimize=True)
    return im.size


def main():
    ap = argparse.ArgumentParser(description="图片去框化：边缘融入纸面")
    ap.add_argument("--src", required=True, help="图片文件或目录")
    ap.add_argument("--out", required=True, help="输出文件或目录")
    ap.add_argument("--paper", default="#FBF8F0", help="版面纸色（须与 theme.css 一致）")
    ap.add_argument("--band", default="64", help="渐隐带宽，像素或 N%%（如 8%%）")
    ap.add_argument("--flat", type=float, default=0.42, help="内部完全清晰占比")
    ap.add_argument("--quality", type=int, default=87)
    a = ap.parse_args()

    band = float(a.band[:-1]) / 100 if a.band.endswith("%") else float(a.band)
    paper = hex2rgb(a.paper)
    src, out = Path(a.src), Path(a.out)

    if src.is_file():
        size = feather_image(src, out, paper, band, a.flat, quality=a.quality)
        print(f"OK {src.name} -> {out.name}  {size[0]}x{size[1]}  纸色 {a.paper}")
        return 0

    files = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)
    if not files:
        print("目录内无图片", file=sys.stderr); return 1
    out.mkdir(parents=True, exist_ok=True)
    for p in files:
        feather_image(p, out / p.name, paper, band, a.flat, quality=a.quality)
    print(f"OK 去框化 {len(files)} 张 -> {out}/  纸色 {a.paper}  带宽 {a.band}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
