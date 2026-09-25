#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""image-enhancer 单图增强 / 诊断入口

用法：
  python3 scripts/enhance.py --analyze raw/screen.png --json out/diag.json
  python3 scripts/enhance.py raw/screen.png out/screen_enhanced.png --preset ppt --scale 2

退出码：0 成功；1 参数错误；2 源图不可读/损坏；3 格式不支持；4 输出写入失败。
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageStat
except ImportError:  # 依赖缺失，提示降级路径
    sys.stderr.write("Pillow 未安装：pip install Pillow>=9.0；或改用 ImageMagick 兜底命令\n")
    sys.exit(5)

SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff", ".gif"}
PRESETS = {
    "ppt": dict(scale=2.0, sharpen=1.35, denoise=0, contrast=1.06, color=1.04, fmt="PNG"),
    "doc": dict(scale=1.5, sharpen=1.20, denoise=1, contrast=1.04, color=1.00, fmt="PNG"),
    "web": dict(scale=1.0, sharpen=0.95, denoise=1, contrast=1.02, color=1.02, fmt="JPEG"),
    "print": dict(scale=3.0, sharpen=1.50, denoise=1, contrast=1.08, color=1.06, fmt="PNG"),
    "social": dict(scale=1.5, sharpen=1.10, denoise=1, contrast=1.03, color=1.08, fmt="JPEG"),
}
MAX_SIDE = 4096
BLUR_THRESHOLD = 500.0   # 拉普拉斯方差低于此值判为模糊需增强（截图/文档类默认；照片类可下调）


def check_source(path: Path):
    """源图体检：返回 (ok, reason)。"""
    if not path.exists():
        return False, "not_found"
    if path.stat().st_size == 0:
        return False, "zero_byte"
    if path.suffix.lower() not in SUPPORTED:
        return False, "unsupported_format"
    try:
        with Image.open(path) as im:
            im.verify()
    except Exception as exc:  # 损坏图不中断批量
        return False, f"corrupt_image:{type(exc).__name__}"
    return True, "ok"


def analyze(path: Path, blur_threshold=None):
    """诊断：尺寸、模式、透明通道、锐度评分、是否需要增强。

    锐度用拉普拉斯方差（Laplacian variance）衡量——业界通用的模糊判定指标，
    数值越大越锐；低于阈值判为 needs_enhance。
    """
    thr = BLUR_THRESHOLD if blur_threshold is None else float(blur_threshold)
    with Image.open(path) as im:
        grey = im.convert("L")
        lap = grey.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], 1, 0))
        score = round(ImageStat.Stat(lap).var[0], 2)
        return {
            "file": str(path),
            "size": list(im.size),
            "mode": im.mode,
            "has_alpha": im.mode in ("RGBA", "LA") or "transparency" in im.info,
            "format": im.format,
            "sharpness_score": score,
            "blur_threshold": thr,
            "verdict": "needs_enhance" if score < thr else "already_ok",
        }


def enhance(src: Path, dst: Path, preset="ppt", scale=None, sharpen=None,
            denoise=None, contrast=None, color=None, quality=95):
    """增强流水线：去噪 → 重采样 → 锐化 → 对比度 → 饱和度 → 写盘。"""
    cfg = dict(PRESETS[preset])
    for key, val in (("scale", scale), ("sharpen", sharpen), ("denoise", denoise),
                     ("contrast", contrast), ("color", color)):
        if val is not None:
            cfg[key] = val
    with Image.open(src) as im:
        has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
        if cfg["denoise"]:
            im = im.filter(ImageFilter.MedianFilter(size=3))
        if cfg["scale"] != 1.0:
            w, h = im.size
            im = im.resize((round(w * cfg["scale"]), round(h * cfg["scale"])), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(
            radius=1.6, percent=round(cfg["sharpen"] * 100), threshold=3))
        im = ImageEnhance.Contrast(im).enhance(cfg["contrast"])
        im = ImageEnhance.Color(im).enhance(cfg["color"])
        im = ImageEnhance.Sharpness(im).enhance(cfg["sharpen"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        if cfg["fmt"] == "JPEG" and not has_alpha:
            im.convert("RGB").save(dst, quality=quality, subsampling=0, optimize=True)
        else:
            im.save(dst)
        out_size, mode = im.size, im.mode
    return cfg, has_alpha, out_size, mode


def main():
    ap = argparse.ArgumentParser(description="image-enhancer 单图增强入口")
    ap.add_argument("input", nargs="?", help="源图路径")
    ap.add_argument("output", nargs="?", help="输出图路径，命名 *+_enhanced.<ext> 为宜")
    ap.add_argument("--analyze", action="store_true", help="只诊断不出图")
    ap.add_argument("--blur-threshold", type=float,
                    help="模糊判定阈值（拉普拉斯方差，默认 %g）" % BLUR_THRESHOLD)
    ap.add_argument("--json", help="诊断 JSON 落盘路径")
    ap.add_argument("--preset", default="ppt", choices=list(PRESETS), help="用途预设")
    ap.add_argument("--scale", type=float, help="放大倍数（默认取预设）")
    ap.add_argument("--sharpen", type=float, help="锐化强度 0.8-2.0")
    ap.add_argument("--denoise", type=int, choices=[0, 1], help="是否去噪")
    ap.add_argument("--contrast", type=float, help="对比度系数")
    ap.add_argument("--color", type=float, help="饱和度系数")
    ap.add_argument("--max-side", type=int, default=MAX_SIDE, help="单边上限，超出先缩后放")
    args = ap.parse_args()

    if not args.input:
        ap.print_help()
        return 1
    src = Path(args.input)
    ok, reason = check_source(src)
    if not ok:
        sys.stderr.write(f"源图不可用：{src} | {reason}\n")
        return 3 if reason == "unsupported_format" else 2

    if args.analyze:
        info = analyze(src, args.blur_threshold)
        text = json.dumps(info, ensure_ascii=False, indent=2)
        if args.json:
            Path(args.json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json).write_text(text, encoding="utf-8")
        print(text)
        return 0

    if not args.output:
        sys.stderr.write("缺少 output 参数\n")
        return 1
    dst = Path(args.output)
    try:
        with Image.open(src) as probe:
            long_side = max(probe.size)
        scale = args.scale if args.scale is not None else PRESETS[args.preset]["scale"]
        if long_side * scale > args.max_side:
            scale = round(args.max_side / long_side, 4)
            sys.stderr.write(f"提示：单边超限，倍数下调为 {scale}\n")
        cfg, has_alpha, out_size, mode = enhance(
            src, dst, args.preset, scale, args.sharpen, args.denoise,
            args.contrast, args.color)
    except Exception as exc:
        sys.stderr.write(f"输出写入失败：{exc}\n")
        return 4

    print(json.dumps({
        "src": str(src), "dst": str(dst), "preset": args.preset,
        "params": cfg, "alpha_preserved": has_alpha,
        "in_size": list(Image.open(src).size), "out_size": list(out_size),
        "out_mode": mode,
        "in_bytes": src.stat().st_size, "out_bytes": dst.stat().st_size,
        "status": "done",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
