#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配图三型处理器：把矩形插图转成"融入版面的形态"

矩形图直接摆到版面上会形成"贴图感"（设计书称"割裂感"）。本脚本按内容特征把图
处理成三型，使整册有形态节奏而不单调：

    cut   退底型 —— 主体从不规则轮廓中"浮"出，无矩形边界（适合主体集中、四周留白的图）
    round 圆形型 —— 圆形取景 + 细圆环 + 圆内浅衬底，形成"舷窗"聚焦（适合物件特写）
    fade  渐隐型 —— 矩形保留，四边向纸色渐隐（适合画面铺满、无明显主体的图）

三型的共同前提是**底色归一**：AI 生成图的米白底（实测约 #E6DED3）比版面纸色
（#FBF8F0）深，差值约 44，不归一就会显出矩形。故先把接近底色的像素替换为版面纸色，
再做形态处理。处理完统一把透明区合为纸色存 JPEG（视觉等价而体积小一个数量级）。

用法：
    python3 image_style.py --src 图.jpg --out 出.png --mode cut
    python3 image_style.py --src 目录 --out 目录 --mode cut --paper "#FBF8F0"
    python3 image_style.py --src 图.jpg --out 出.jpg --mode round --ring "#96795C"

参数：
    --mode   cut / round / fade（默认 cut）
    --paper  版面纸色，须与 theme.css 的 --paper 一致（默认 #FBF8F0）
    --band   渐隐带宽像素（fade，默认 64）
    --flat   内部完全清晰占比（fade，默认 0.42）
    --depth  墨色加深系数（1.0 不加深，默认 1.5）
    --seed   轮廓抖动种子（cut，同种子可复现）
    --ring   圆环颜色（round，默认 #96795C）
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def hex2rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def est_bg(a):
    """以四边 4% 带宽的中位数估计该图底色（每张图底色略有差异）"""
    h, w = a.shape[:2]; m = max(3, int(min(h, w) * 0.04))
    e = np.concatenate([a[:m].reshape(-1, 3), a[-m:].reshape(-1, 3),
                        a[:, :m].reshape(-1, 3), a[:, -m:].reshape(-1, 3)])
    return np.median(e, axis=0)


def norm_bg(a, bg, paper, t1=22.0, t2=70.0):
    """底色归一：接近底色的像素软替换为版面纸色"""
    d = np.sqrt(((a - bg) ** 2).sum(-1))
    w = np.clip((t2 - d) / (t2 - t1), 0, 1)
    return a * (1 - w[..., None]) + paper * w[..., None]


def deepen(a, paper, k=1.5):
    """围绕纸色放大差异——线条加深，纸面不变"""
    return np.clip(paper + (a - paper) * k, 0, 255)


def rough(al, seed, amp=0.09, cell=46):
    """轮廓低频抖动：边缘呈自然手绘的不规则感"""
    h, w = al.shape
    rs = np.random.RandomState(seed)
    s = rs.rand(max(2, h // cell), max(2, w // cell)).astype(np.float32)
    n = np.asarray(Image.fromarray((s * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255.0
    return np.clip(al + (n - 0.5) * amp, 0, 1)


def _save(rgb, al, out, paper):
    """透明区合纸色后按后缀存盘（视觉等价，体积远小于 PNG）"""
    al = np.clip(al, 0, 1)[..., None]
    flat = rgb * al + paper * (1 - al)
    im = Image.fromarray(np.clip(flat, 0, 255).astype(np.uint8))
    if out.suffix.lower() == ".png":
        im.save(out, optimize=True)
    else:
        im.save(out, "JPEG", quality=88, optimize=True)


def do_cut(a, out, paper, depth, seed, margin=24, blur=5.0):
    bg = est_bg(a); d = np.sqrt(((a - bg) ** 2).sum(-1))
    al = np.clip((d - 12.0) / (54.0 - 12.0), 0, 1) ** 0.70
    al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255.0
    al = rough(np.clip(al * 1.25, 0, 1), seed)
    ys, xs = np.where(al > 0.12)
    if len(ys) == 0:
        return do_fade(a, out, paper, depth)
    y0, y1 = max(0, ys.min() - margin), min(a.shape[0], ys.max() + 1 + margin)
    x0, x1 = max(0, xs.min() - margin), min(a.shape[1], xs.max() + 1 + margin)
    sub = deepen(norm_bg(a[y0:y1, x0:x1], bg, paper), paper, depth)
    _save(sub, al[y0:y1, x0:x1], out, paper)


def do_round(a, out, paper, depth, ring, pad=20):
    bg = est_bg(a); rgb = deepen(norm_bg(a, bg, paper), paper, depth)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((yy - h / 2) / (h / 2 - pad)) ** 2 + ((xx - w / 2) / (w / 2 - pad)) ** 2)
    iw = np.clip((1.0 - r) / 0.06, 0, 1)[..., None]
    inner = np.clip(paper * 0.975, 0, 255)              # 圆内浅衬底，使圆形可辨
    rgb = rgb * (1 - iw * 0.5) + inner * (iw * 0.5)
    rs = np.clip(1.0 - np.abs(r - 1.0) / 0.0125, 0, 1)[..., None]
    rgb = rgb * (1 - rs) + ring * rs
    al = np.clip((1.0 - r) / 0.05, 0, 1) ** 0.9
    _save(rgb, np.maximum(al, rs[..., 0]), out, paper)


def do_fade(a, out, paper, depth, band=64, flat=0.42, power=1.15):
    bg = est_bg(a); rgb = deepen(norm_bg(a, bg, paper), paper, depth)
    h, w = rgb.shape[:2]; b = min(band, h // 3, w // 3)
    wy = np.minimum(np.arange(h), np.arange(h)[::-1]).astype(np.float32)
    wx = np.minimum(np.arange(w), np.arange(w)[::-1]).astype(np.float32)
    dd = np.minimum(wy[:, None], wx[None, :])
    t = np.clip((1.0 - dd / b - flat) / (1 - flat), 0, 1) ** power
    flat_rgb = rgb * (1 - t[..., None]) + paper * t[..., None]
    Image.fromarray(flat_rgb.astype(np.uint8)).save(out, "JPEG", quality=90, optimize=True)


def main():
    ap = argparse.ArgumentParser(description="配图三型处理器（退底/圆形/渐隐）")
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="cut", choices=["cut", "round", "fade"])
    ap.add_argument("--paper", default="#FBF8F0")
    ap.add_argument("--band", type=float, default=64)
    ap.add_argument("--flat", type=float, default=0.42)
    ap.add_argument("--depth", type=float, default=1.5)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--ring", default="#96795C")
    a = ap.parse_args()

    paper, ring = hex2rgb(a.paper), hex2rgb(a.ring)
    src, out = Path(a.src), Path(a.out)

    def run(p, o):
        arr = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
        if a.mode == "cut":
            do_cut(arr, o, paper, a.depth, a.seed)
        elif a.mode == "round":
            do_round(arr, o, paper, a.depth, ring)
        else:
            do_fade(arr, o, paper, a.depth, a.band, a.flat)
        return o

    if src.is_file():
        o = out if out.suffix else out.with_suffix(".png" if a.mode != "fade" else ".jpg")
        run(src, o); print(f"OK [{a.mode}] {src.name} -> {o.name}")
        return 0
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)
    if not files:
        print("目录内无图片", file=sys.stderr); return 1
    out.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(files):
        ext = ".jpg" if a.mode == "fade" else ".png"
        run(p, out / (p.stem + "_" + a.mode + ext))
    print(f"OK [{a.mode}] {len(files)} 张 -> {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
