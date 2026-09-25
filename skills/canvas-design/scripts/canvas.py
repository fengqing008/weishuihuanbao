#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
canvas-design 画布构造与导出引擎（scripts/canvas.py）

链路：背景层 -> 重复图案层 -> 几何主体层 -> 极简文字层 -> 导出 PNG / PDF。
所有可见元素落在安全边距以内，文字色按 WCAG 相对亮度公式自动挑选，seed 可复现。

示例
----
python3 scripts/canvas.py --philosophy-phrase "Chromatic Silence" \
    --palette "#0f172a,#e2b34a" --title "静默的秩序" \
    --subtitle "单页视觉 · 2026" -o out.png

python3 scripts/canvas.py --preset brutalist-tide --size a4 --pdf -o poster.png

python3 scripts/canvas.py --list-presets

依赖：Python 3 + Pillow；numpy 存在时用于叠加极淡纸纹（缺失自动跳过）。
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# 常量
# --------------------------------------------------------------------------

SIZES = {
    "post": (1080, 1350),      # 竖版社交媒体配图 / 海报
    "square": (1080, 1080),    # 方图
    "story": (1080, 1920),     # 竖屏故事
    "a4": (2480, 3508),        # A4 300dpi 打印件
    "letter": (2550, 3300),    # Letter 300dpi
}

PATTERNS = ("grid", "stripes", "dots", "concentric", "triangles", "hatch", "blocks")

FONT_CANDIDATES = {
    "sans": [
        "/usr/local/share/fonts/custom/NotoSansSC-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "sans-bold": [
        "/usr/local/share/fonts/custom/NotoSansSC-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "serif": [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
}

FONT_RESOLVED = {}

PRESETS = {
    "chromatic-silence": {
        "motion": "Chromatic Silence",
        "palette": ["#0f172a", "#1d283a", "#e2b34a", "#9fb3c8"],
        "pattern": "grid",
        "pattern_scale": 0.045,
        "shapes": 2,
        "note": "深墨底承载单点高纯度暖金，其余色彩压到低饱和陪衬位。",
    },
    "brutalist-tide": {
        "motion": "Brutalist Tide",
        "palette": ["#e8e4dc", "#111111", "#d94f2b", "#3f6f8f"],
        "pattern": "stripes",
        "pattern_scale": 0.030,
        "shapes": 3,
        "note": "裸色纸底与粗重黑线并置，一条朱红斜纹打破均质。",
    },
    "grid-reverie": {
        "motion": "Grid Reverie",
        "palette": ["#f2f4f7", "#c9d2dd", "#2f4858", "#86b0bd"],
        "pattern": "dots",
        "pattern_scale": 0.028,
        "shapes": 2,
        "note": "雾白底上的点阵缓慢呼吸，深青以圆环形态落定重心。",
    },
    "organic-monolith": {
        "motion": "Organic Monolith",
        "palette": ["#1b1b1f", "#2e2a25", "#c2a878", "#7d5a3c"],
        "pattern": "hatch",
        "pattern_scale": 0.020,
        "shapes": 3,
        "note": "深褐底与高密度细线共存，米金圆环成为画面唯一光源。",
    },
}

DEFAULT_PALETTE = "#0f172a,#1d283a,#e2b34a,#f8fafc"


# --------------------------------------------------------------------------
# 色彩工具
# --------------------------------------------------------------------------

def parse_color(text: str):
    s = str(text).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError("颜色格式须为 3 位或 6 位十六进制，收到：%s" % text)
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError("颜色含非法字符：%s" % text)


def parse_palette(text: str):
    colors = [parse_color(p) for p in str(text).split(",") if p.strip()]
    if not colors:
        raise ValueError("色板为空")
    return colors


def _linear(channel: float) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb) -> float:
    r, g, b = (_linear(v) for v in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


def saturation(rgb) -> float:
    r, g, b = (v / 255.0 for v in rgb[:3])
    return colorsys.rgb_to_hsv(r, g, b)[1]


def pick_ink(background, palette):
    """挑选与背景对比度最高的文字色，并在全部候选中对比度不足时兜底黑白。"""
    candidates = list(palette) + [(255, 255, 255), (17, 19, 24), (0, 0, 0)]
    best, best_ratio = candidates[0], 0.0
    for c in candidates:
        k = contrast_ratio(background, c)
        if k > best_ratio:
            best, best_ratio = c, k
    return best, best_ratio


def pick_ink_against(background, palette, avoid):
    """挑选与背景对比度最高、且与 avoid 明显区分的辅助文字色。"""
    candidates = list(palette) + [(255, 255, 255), (0, 0, 0)]
    best, best_ratio = candidates[0], 0.0
    for c in candidates:
        if contrast_ratio(c, avoid) < 1.25:
            continue
        k = contrast_ratio(background, c)
        if k > best_ratio:
            best, best_ratio = c, k
    return best, best_ratio


def pick_accent(palette):
    """取饱和度最高的颜色作几何主体色；饱和度相同时取更亮的一支。"""
    return max(palette, key=lambda c: (saturation(c), luminance(c)))


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def pad_palette(colors, minimum: int = 4):
    """把不足四个席位的色板补齐：两席时插入一支过渡色，其余用中值混合。"""
    out = list(colors)
    if not out:
        raise ValueError("色板为空")
    if len(out) == 1:
        out.append(mix(out[0], (255, 255, 255), 0.55))
    while len(out) < minimum:
        out.append(mix(out[0], out[-1], 0.5))
    return out


# --------------------------------------------------------------------------
# 字体
# --------------------------------------------------------------------------

def load_font(family: str, size: int):
    size = max(8, int(size))
    for path in FONT_CANDIDATES[family]:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                FONT_RESOLVED[family] = path
                return font
            except Exception:
                continue
    FONT_RESOLVED[family] = "<Pillow default bitmap font>"
    return ImageFont.load_default()


def text_width(font, text: str) -> float:
    try:
        return float(font.getlength(text))
    except Exception:
        return float(font.getbbox(text)[2] - font.getbbox(text)[0])


def line_height(font, sample: str = "字Ag") -> int:
    box = font.getbbox(sample)
    return int(box[3] - box[1])


def wrap_text(text: str, font, max_width: float):
    lines = []
    for para in str(text).split("\n"):
        cur = ""
        for ch in para:
            if text_width(font, cur + ch) <= max_width or not cur:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines or [""]


# --------------------------------------------------------------------------
# 图案层
# --------------------------------------------------------------------------

def _fit_step(total: float, target: float) -> float:
    """把步长吸附到可整除总长的最近值，避免末行出现半格接缝。"""
    target = max(4.0, float(target))
    n = max(1, int(round(total / target)))
    return total / n


def draw_pattern(size, pattern: str, colors, rng, scale: float):
    """在舞台内绘制重复图案层，返回 RGBA 图层。"""
    sw, sh = size
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    stage_min = min(sw, sh)
    step_target = stage_min * max(0.008, float(scale))

    line_c = colors[0]
    alt_c = colors[1] if len(colors) > 1 else colors[0]

    if pattern == "grid":
        sx = _fit_step(sw, step_target)
        sy = _fit_step(sh, step_target)
        alpha = 34
        w = max(1, int(stage_min * 0.0011))
        x = 0.0
        while x <= sw + 0.5:
            d.line([(x, 0), (x, sh)], fill=line_c + (alpha,), width=w)
            x += sx
        y = 0.0
        while y <= sh + 0.5:
            d.line([(0, y), (sw, y)], fill=line_c + (alpha,), width=w)
            y += sy

    elif pattern == "stripes":
        pitch = _fit_step(sw + sh, step_target * 1.6)
        band = pitch * 0.34
        alpha = 40
        pos = -sh
        while pos <= sw + sh:
            d.polygon(
                [(pos, 0), (pos + band, 0), (pos + band - sh, sh), (pos - sh, sh)],
                fill=alt_c + (alpha,),
            )
            pos += pitch

    elif pattern == "dots":
        sx = _fit_step(sw, step_target)
        sy = _fit_step(sh, step_target)
        r = max(1.0, stage_min * 0.0022)
        alpha = 52
        row = 0
        y = sy / 2
        while y < sh:
            offset = (sx / 2) if row % 2 else 0.0
            x = offset + sx / 2
            while x < sw:
                d.ellipse([x - r, y - r, x + r, y + r], fill=line_c + (alpha,))
                x += sx
            y += sy
            row += 1

    elif pattern == "concentric":
        cx, cy = sw * 0.46, sh * 0.38
        r_max = math.hypot(max(cx, sw - cx), max(cy, sh - cy))
        ring_gap = _fit_step(r_max, step_target * 1.8)
        w = max(1, int(stage_min * 0.0013))
        alpha = 36
        r = ring_gap
        while r < r_max:
            d.ellipse([cx - r, cy - r, cx + r, cy + r],
                      outline=line_c + (alpha,), width=w)
            r += ring_gap

    elif pattern == "triangles":
        sx = _fit_step(sw, step_target * 1.4)
        sy = _fit_step(sh, step_target * 1.2)
        alpha = 30
        row = 0
        y = 0.0
        while y < sh:
            offset = (sx / 2) if row % 2 else 0.0
            x = -sx + offset
            while x < sw:
                d.polygon([(x, y), (x + sx, y), (x + sx / 2, y + sy)],
                          fill=(alt_c if row % 2 else line_c) + (alpha,))
                x += sx
            y += sy
            row += 1

    elif pattern == "hatch":
        pitch = _fit_step(sw + sh, step_target * 0.9)
        alpha = 44
        w = max(1, int(stage_min * 0.0012))
        pos = -sh
        while pos <= sw + sh:
            d.line([(pos, 0), (pos - sh, sh)], fill=line_c + (alpha,), width=w)
            pos += pitch
        pos = 0
        while pos <= sw + sh:
            d.line([(pos, 0), (pos + sh, sh)], fill=line_c + (alpha // 2,), width=w)
            pos += pitch

    elif pattern == "blocks":
        cols = max(3, int(round(sw / (step_target * 2.4))))
        rows = max(3, int(round(sh / (step_target * 2.4))))
        cw, chh = sw / cols, sh / rows
        for i in range(cols):
            for j in range(rows):
                if rng.random() < 0.42:
                    t = rng.choice([line_c, alt_c])
                    d.rectangle(
                        [i * cw + cw * 0.06, j * chh + chh * 0.06,
                         (i + 1) * cw - cw * 0.06, (j + 1) * chh - chh * 0.06],
                        fill=t + (28,),
                    )
    else:
        raise ValueError("未知图案族：%s" % pattern)

    return layer


# --------------------------------------------------------------------------
# 几何主体层
# --------------------------------------------------------------------------

def draw_geometry(size, colors, rng, count: int):
    """绘制一至三组大尺度几何主体，返回 RGBA 图层。

    布局约束：主形状与同心外环互不相交（环半径 = 主半径 + 间隙），
    整组几何收在舞台高度的 [0.05, 0.66] 区间内，与文字带（0.72 起）保持空白。
    """
    sw, sh = size
    base = min(sw, sh)
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    accent, partner = colors[0], colors[1]

    top_limit = sh * 0.05
    bottom_limit = sh * 0.66
    avail = max(1.0, bottom_limit - top_limit)
    ring_outer = min(base * 0.28, avail * 0.46)
    ring_w = max(2, int(base * 0.005))
    gap_min = base * 0.05

    r = ring_outer * rng.uniform(0.60, 0.72)
    if ring_outer - r < gap_min:
        r = max(base * 0.05, ring_outer - gap_min)

    cy = top_limit + ring_outer + (avail - 2 * ring_outer) * rng.uniform(0.2, 0.8)
    cy = min(max(cy, top_limit + ring_outer), bottom_limit - ring_outer)

    lo, hi = ring_outer + sw * 0.02, sw - ring_outer - sw * 0.02
    if hi <= lo:
        cx = sw / 2.0
    else:
        cx = min(max(sw * rng.uniform(0.32, 0.60), lo), hi)

    kind = rng.choice(["circle", "square", "triangle"])
    if kind == "circle":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent + (255,))
    elif kind == "square":
        d.rectangle([cx - r, cy - r, cx + r, cy + r], fill=accent + (255,))
    else:
        d.polygon([(cx, cy - r), (cx + r * 0.92, cy + r * 0.72),
                   (cx - r * 0.92, cy + r * 0.72)], fill=accent + (255,))

    if count >= 2:
        d.ellipse([cx - ring_outer, cy - ring_outer, cx + ring_outer, cy + ring_outer],
                  outline=partner + (235,), width=ring_w)

    if count >= 3:
        pr = base * rng.uniform(0.016, 0.028)
        placed = None
        for px, py in ((sw * 0.15, sh * 0.12), (sw * 0.85, sh * 0.10),
                       (sw * 0.86, sh * 0.60)):
            if math.hypot(px - cx, py - cy) > ring_outer + pr + base * 0.06:
                placed = (px, py)
                break
        if placed is not None:
            px, py = placed
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=partner + (255,))

    return layer


# --------------------------------------------------------------------------
# 纹理
# --------------------------------------------------------------------------

def add_paper_grain(image, strength: int, seed: int):
    """叠加极淡纸纹。numpy 缺失时原样返回。"""
    if strength <= 0:
        return image
    try:
        import numpy as np
    except Exception:
        return image
    arr = np.asarray(image.convert("RGB"), dtype=np.int16)
    rng = np.random.default_rng(seed)
    noise = rng.integers(-strength, strength + 1, size=arr.shape[:2], dtype=np.int16)
    arr = np.clip(arr + noise[..., None], 0, 255).astype("uint8")
    return Image.fromarray(arr).convert("RGBA")


# --------------------------------------------------------------------------
# 主构造
# --------------------------------------------------------------------------

def build_image(opts) -> Image.Image:
    width, height = opts["width"], opts["height"]
    palette = pad_palette(opts["palette"])
    base = min(width, height)
    margin = int(round(base * opts["margin_ratio"]))
    sw, sh = width - 2 * margin, height - 2 * margin

    rng = random.Random(opts["seed"])

    background = palette[0]
    canvas = Image.new("RGBA", (width, height), background + (255,))

    pattern_layer = draw_pattern((sw, sh), opts["pattern"], palette[1:], rng,
                                 opts["pattern_scale"])
    canvas.alpha_composite(pattern_layer, (margin, margin))

    geometry_layer = draw_geometry((sw, sh), [pick_accent(palette),
                                              palette[-1]], rng, opts["shapes"])
    canvas.alpha_composite(geometry_layer, (margin, margin))

    canvas = add_paper_grain(canvas, opts["grain"], opts["seed"] + 7)

    # ---------------- 文字层 ----------------
    ink, ink_ratio = pick_ink(background, palette)
    ink_soft, _ = pick_ink_against(background, palette, ink)

    title_size = base * 0.070
    body_size = base * 0.0195
    eyebrow_size = base * 0.0155
    mark_size = base * 0.0135

    font_title = load_font("sans-bold", title_size)
    font_body = load_font("sans", body_size)
    font_eyebrow = load_font("sans", eyebrow_size)
    font_mark = load_font("sans", mark_size)

    gap = base * 0.018
    y_hair = margin + sh * 0.72
    x0 = margin
    stage_right = margin + sw
    stage_bottom = margin + sh

    title_lines = wrap_text(opts["title"], font_title, sw)
    lh_title = line_height(font_title) * 1.18
    lh_body = line_height(font_body) * 1.5

    # 自动收敛字号，保证文字块不越过舞台底边
    guard = 0
    while guard < 40:
        block_h = (gap * 1.4 + lh_body) + (lh_title * len(title_lines)) \
            + (lh_body * 1.2) + (lh_body * 1.6)
        if y_hair + block_h <= stage_bottom - gap * 0.2:
            break
        title_size *= 0.94
        font_title = load_font("sans-bold", title_size)
        title_lines = wrap_text(opts["title"], font_title, sw)
        lh_title = line_height(font_title) * 1.18
        guard += 1

    draw = ImageDraw.Draw(canvas)

    # 眉标（运动名，大写 + 加宽字距）
    eyebrow = opts["phrase"].upper()
    y = y_hair - gap * 1.4 - line_height(font_eyebrow)
    draw.text((x0, y), eyebrow, font=font_eyebrow, fill=ink_soft + (255,))

    # 细分隔线
    hair_w = max(1, int(base * 0.0014))
    draw.line([(x0, y_hair), (stage_right, y_hair)], fill=ink + (140,), width=hair_w)

    # 标题
    ty = y_hair + gap * 1.4
    for ln in title_lines:
        draw.text((x0, ty), ln, font=font_title, fill=ink + (255,))
        ty += lh_title

    # 副题
    if opts["subtitle"]:
        ty += lh_body * 0.2
        for ln in wrap_text(opts["subtitle"], font_body, sw):
            draw.text((x0, ty), ln, font=font_body, fill=ink_soft + (255,))
            ty += lh_body

    # 右下角标记
    mark = opts["mark"]
    if mark:
        mw = text_width(font_mark, mark)
        mh = line_height(font_mark)
        draw.text((stage_right - mw, stage_bottom - mh - gap * 0.2),
                  mark, font=font_mark, fill=ink_soft + (255,))

    opts["_ink"] = ink
    opts["_ink_ratio"] = ink_ratio
    opts["_fonts"] = dict(FONT_RESOLVED)
    return canvas


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="canvas.py",
        description="canvas-design 画布构造引擎：由设计哲学生成单页视觉作品（PNG／PDF）。",
        epilog="示例：python3 scripts/canvas.py --philosophy-phrase \"Chromatic Silence\" "
               "--palette \"#0f172a,#e2b34a\" --title \"静默的秩序\" -o out.png",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--philosophy-phrase", default=None,
                   help="设计哲学／艺术运动的名称，1—2 词，渲染为画面眉标")
    p.add_argument("--title", default=None, help="画面主标题，缺省时取哲学名")
    p.add_argument("--subtitle", default="", help="一行副题，可留空")
    p.add_argument("--mark", default=None,
                   help="右下角微标记，缺省时自动生成为 seed 短码")
    p.add_argument("--palette", default=None,
                   help="逗号分隔色板，首色为底、次色为图案、饱和最高色为几何主体。"
                        "例：#0f172a,#1d283a,#e2b34a,#f8fafc")
    p.add_argument("--pattern", default=None, choices=list(PATTERNS),
                   help="重复图案族，缺省取预设值或 grid")
    p.add_argument("--pattern-scale", dest="pattern_scale", type=float, default=None,
                   help="图案步长相对短边的比例，0.01—0.08")
    p.add_argument("--shapes", type=int, default=None, choices=[1, 2, 3],
                   help="几何主体组数，1—3")
    p.add_argument("--size", default="post", choices=list(SIZES),
                   help="输出画幅：post 1080x1350 / square / story / a4 300dpi / letter")
    p.add_argument("--width", type=int, default=None, help="自定义画布宽度，覆盖 --size")
    p.add_argument("--height", type=int, default=None, help="自定义画布高度，覆盖 --size")
    p.add_argument("--preset", default=None, choices=list(PRESETS),
                   help="内置设计哲学预设，显式参数优先于预设")
    p.add_argument("--seed", type=int, default=None, help="随机种子，缺省由哲学名哈希派生")
    p.add_argument("--margin-ratio", dest="margin_ratio", type=float, default=0.06,
                   help="安全边距相对短边的比例，默认 0.06")
    p.add_argument("--grain", type=int, default=3, help="纸纹强度 0—8，0 为关闭")
    p.add_argument("--pdf", nargs="?", const="", default=None,
                   help="同时导出 PDF；给空值输出到 PNG 同目录同名 PDF")
    p.add_argument("--spec", default=None, help="把本次参数与实测对比度写入 JSON 文件")
    p.add_argument("-o", "--out", default="canvas_out.png", help="PNG 输出路径")
    p.add_argument("--quiet", action="store_true", help="只输出结果路径")
    p.add_argument("--list-presets", action="store_true", help="打印全部内置预设后退出")
    return p


def print_presets():
    print("内置设计哲学预设（--preset 取值）：")
    for key, val in PRESETS.items():
        print("  %-20s motion=%s  pattern=%-10s shapes=%d"
              % (key, val["motion"], val["pattern"], val["shapes"]))
        print("      palette: %s" % ",".join(val["palette"]))
        print("      note   : %s" % val["note"])


def resolve_options(args):
    preset = PRESETS.get(args.preset) if args.preset else None

    phrase = args.philosophy_phrase or (preset["motion"] if preset else "Untitled Motion")
    title = args.title or phrase
    palette_str = args.palette or (",".join(preset["palette"]) if preset else DEFAULT_PALETTE)
    pattern = args.pattern or (preset["pattern"] if preset else "grid")
    pattern_scale = (args.pattern_scale if args.pattern_scale is not None
                     else (preset["pattern_scale"] if preset else 0.035))
    shapes = (args.shapes if args.shapes is not None
              else (preset["shapes"] if preset else 2))

    if args.width and args.height:
        width, height = args.width, args.height
    else:
        width, height = SIZES[args.size]

    if args.seed is not None:
        seed = args.seed
    else:
        digest = hashlib.sha256(phrase.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)

    mark = args.mark
    if mark is None:
        mark = "SEED %s · %s" % (format(seed % 100000, "05d"), pattern.upper())

    return {
        "phrase": phrase,
        "title": title,
        "subtitle": args.subtitle,
        "mark": mark,
        "palette": parse_palette(palette_str),
        "palette_raw": palette_str,
        "pattern": pattern,
        "pattern_scale": max(0.008, min(0.10, pattern_scale)),
        "shapes": shapes,
        "width": width,
        "height": height,
        "seed": seed,
        "margin_ratio": max(0.02, min(0.16, args.margin_ratio)),
        "grain": max(0, min(8, args.grain)),
        "preset": args.preset,
    }


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_presets:
        print_presets()
        return 0

    try:
        opts = resolve_options(args)
    except ValueError as exc:
        parser.error(str(exc))

    image = build_image(opts)

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    rgb = image.convert("RGB")
    rgb.save(out_path, optimize=True)

    pdf_path = None
    if args.pdf is not None:
        pdf_path = args.pdf.strip() or os.path.splitext(out_path)[0] + ".pdf"
        pdf_path = os.path.abspath(pdf_path)
        os.makedirs(os.path.dirname(pdf_path) or ".", exist_ok=True)
        rgb.save(pdf_path, "PDF", resolution=300.0)

    spec_path = None
    if args.spec:
        spec_path = os.path.abspath(args.spec)
        os.makedirs(os.path.dirname(spec_path) or ".", exist_ok=True)
        spec = {
            "motion": opts["phrase"],
            "title": opts["title"],
            "subtitle": opts["subtitle"],
            "canvas": [opts["width"], opts["height"]],
            "margin_px": int(round(min(opts["width"], opts["height"]) * opts["margin_ratio"])),
            "palette": opts["palette_raw"],
            "pattern": opts["pattern"],
            "pattern_scale": opts["pattern_scale"],
            "shapes": opts["shapes"],
            "seed": opts["seed"],
            "grain": opts["grain"],
            "ink": "#%02x%02x%02x" % opts["_ink"],
            "ink_contrast_ratio": round(opts["_ink_ratio"], 2),
            "fonts": opts["_fonts"],
            "png": out_path,
            "pdf": pdf_path,
        }
        with open(spec_path, "w", encoding="utf-8") as fh:
            json.dump(spec, fh, ensure_ascii=False, indent=2)

    if args.quiet:
        print(out_path)
    else:
        print("画布设计完成")
        print("  哲学／运动 : %s" % opts["phrase"])
        print("  画布       : %dx%d" % (opts["width"], opts["height"]))
        print("  安全边距   : %d px" % int(round(min(opts["width"], opts["height"]) * opts["margin_ratio"])))
        print("  图案族     : %s (scale %.3f)" % (opts["pattern"], opts["pattern_scale"]))
        print("  几何主体   : %d 组" % opts["shapes"])
        print("  seed       : %d" % opts["seed"])
        print("  文字对比度 : %.2f:1 %s"
              % (opts["_ink_ratio"],
                 "通过" if opts["_ink_ratio"] >= 4.5 else "未达 4.5:1，须调整色板"))
        print("  字体回退   : %s" % json.dumps(opts["_fonts"], ensure_ascii=False))
        print("  PNG        : %s" % out_path)
        if pdf_path:
            print("  PDF        : %s" % pdf_path)
        if spec_path:
            print("  规格记录   : %s" % spec_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
