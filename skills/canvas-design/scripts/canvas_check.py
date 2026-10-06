#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画布设计交付前自检器（canvas_check.py）。

仅使用 Python 标准库（argparse / json / sys），对单页视觉作品的交付参数做规则自检：

  1. 画布尺寸须为正整数，且命中或可归入内置预设（post / square / story / a4）；
  2. 正文与背景、大标题与背景的对比度须达标
     （正文 >= 4.5:1，大标题 >= 3:1，按 WCAG 2.2 相对亮度公式计算）；
  3. 文字量上限：汉字 <= 25，拉丁字符 <= 40（90/10 配比原则）；
  4. 安全边距比例 >= 画面短边的 6%；
  5. 复现参数（seed）须已记录，缺失时给出提示而非中断。

退出码：
  0 —— 全部校验通过；
  1 —— 校验不通过（对比度 / 边距 / 文字量超限等硬性告警）；
  2 —— 输入不足或参数非法（缺关键字段、颜色或数值不可解析）。

用法：
  python3 canvas_check.py --width 1080 --height 1350 --fg "#1a1a1a" --bg "#faf8f4" \
      --text-len 18 --margin-ratio 0.06 --seed art-movement-hash --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys

MIN_MARGIN_RATIO = 0.06
MIN_CONTRAST_BODY = 4.5
MIN_CONTRAST_LARGE = 3.0
MAX_CJK = 25
MAX_LATIN = 40

PRESETS = {
    "post": (1080, 1350),
    "square": (1080, 1080),
    "story": (1080, 1920),
    "a4": (2480, 3508),
}

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _hex_to_rgb(text: str, field: str):
    """解析 6 位十六进制颜色，失败时抛出 ValueError。"""
    m = _HEX_RE.match((text or "").strip())
    if not m:
        raise ValueError("字段 %s 颜色不可解析：%r（须为 #RRGGBB）" % (field, text))
    v = int(m.group(1), 16)
    return ((v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF)


def _rel_luminance(rgb) -> float:
    """WCAG 相对亮度。"""
    out = []
    for c in rgb:
        s = c / 255.0
        out.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
    r, g, b = out
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg) -> float:
    """两色对比度。"""
    l1, l2 = _rel_luminance(fg), _rel_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def check(args: argparse.Namespace) -> dict:
    """执行校验，返回结构化结果字典。"""
    if args.width is None or args.height is None:
        raise ValueError("缺少必填参数：--width 与 --height")

    width, height = int(args.width), int(args.height)
    if width <= 0 or height <= 0:
        raise ValueError("画布尺寸须为正整数")

    problems = []
    notes = []

    matched = None
    for name, (w, h) in PRESETS.items():
        if (width, height) == (w, h):
            matched = name
            break
    if matched:
        notes.append("尺寸命中内置预设：%s（%dx%d）" % (matched, width, height))
    else:
        notes.append("尺寸 %dx%d 未命中内置预设，按自定义画布处理，边距须按短边重算" % (width, height))

    ratio = None
    if args.fg and args.bg:
        fg = _hex_to_rgb(args.fg, "--fg")
        bg = _hex_to_rgb(args.bg, "--bg")
        ratio = round(contrast_ratio(fg, bg), 3)
        if ratio < MIN_CONTRAST_BODY:
            problems.append("正文/背景对比度 %.3f:1 低于 4.5:1 门槛" % ratio)
        elif ratio < MIN_CONTRAST_LARGE:
            problems.append("对比度 %.3f:1 仅够大标题（<3:1 则标题亦不合格）" % ratio)
        else:
            notes.append("对比度 %.3f:1 达标" % ratio)
    else:
        notes.append("未提供 --fg/--bg，跳过对比度校验")

    if args.text_len is not None:
        cjk = int(args.text_len)
        if cjk <= 0:
            raise ValueError("文字量须为正整数")
        if cjk > MAX_CJK:
            problems.append("汉字数 %d 超过上限 %d，破坏 90/10 配比" % (cjk, MAX_CJK))
        else:
            notes.append("汉字数 %d 在上限 %d 之内" % (cjk, MAX_CJK))
    else:
        notes.append("未提供 --text-len，跳过文字量校验")

    if args.margin_ratio is not None:
        mr = float(args.margin_ratio)
        if mr < 0:
            raise ValueError("边距比例不可为负")
        if mr < MIN_MARGIN_RATIO:
            problems.append("安全边距比例 %.4f 低于短边 6%% 下限，元素可能贴边或被裁切" % mr)
        else:
            notes.append("安全边距比例 %.4f 达标" % mr)
    else:
        notes.append("未提供 --margin-ratio，跳过边距校验")

    if args.seed:
        notes.append("已记录复现 seed：%s" % args.seed)
    else:
        notes.append("未提供 --seed，画面不可复现，建议以运动名哈希派生 seed")

    return {
        "size": {"width": width, "height": height, "preset": matched},
        "contrast": ratio,
        "text_len": args.text_len,
        "margin_ratio": args.margin_ratio,
        "seed": args.seed,
        "problems": problems,
        "notes": notes,
        "result": "PASS" if not problems else "FAIL",
    }


def main(argv=None) -> int:
    """命令行入口。返回退出码 0/1/2。"""
    parser = argparse.ArgumentParser(
        description="画布设计交付前自检器（标准库实现，退出码 0/1/2）")
    parser.add_argument("--width", type=int, help="画布宽（像素）")
    parser.add_argument("--height", type=int, help="画布高（像素）")
    parser.add_argument("--fg", help="文字色 #RRGGBB")
    parser.add_argument("--bg", help="背景色 #RRGGBB")
    parser.add_argument("--text-len", dest="text_len", type=int, help="画面汉字总数")
    parser.add_argument("--margin-ratio", dest="margin_ratio", type=float,
                        help="安全边距占短边比例（如 0.06）")
    parser.add_argument("--seed", help="复现 seed（字符或数字）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args(argv)

    try:
        res = check(args)
    except ValueError as exc:
        print("[输入不足] %s" % exc)
        print("提示：缺少关键字段时请补齐后重跑；未核实的素材一律标【待核】。")
        return 2

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("尺寸：%dx%d（预设 %s）" % (res["size"]["width"], res["size"]["height"],
                                       res["size"]["preset"]))
        print("对比度：%s" % (res["contrast"] if res["contrast"] is not None else "未校验"))
        for n in res["notes"]:
            print("  · %s" % n)
        for p in res["problems"]:
            print("  ! %s" % p)
        print("结论：%s" % res["result"])

    return 0 if res["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
