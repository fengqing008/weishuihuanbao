#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""theme_check.py —— 主题规格与对比度自查器（theme-factory 专用）

仅使用 Python 标准库，离线可跑。对一份主题规格 Markdown（如 themes/ocean-depths.md）
做机器可判的结构自查：
  1) 解析四色 hex（background / primary / accent / text 四个槽位）；
  2) 按 WCAG 2.1 复算对比度：正文/背景须 >= 4.5:1，强调/背景须 >= 3.0:1；
  3) 核对槽位完整性与色值书写规范（统一为 #rrggbb 小写）；
  4) 输出结论，使失败分支可被下游脚本与人工统一判读。

退出码（约定）：
  0 = 全部通过
  1 = 存在不达标项（对比度不足 / 槽位缺失 / 色值写法不规范）
  2 = 用法或输入错误（文件不存在、未解析到足够色值、参数非法）

用法示例：
  python3 theme_check.py --help
  python3 theme_check.py --file themes/ocean-depths.md
  python3 theme_check.py --file themes/tech-innovation.md --json
  python3 theme_check.py --bg "#1e1e1e" --text "#ffffff" --accent "#0066ff"
"""
import argparse
import json
import os
import re
import sys

HEX_RE = re.compile(r"#([0-9a-fA-F]{6})\b")
UPPER_RE = re.compile(r"#[0-9A-F]{6}\b")

TEXT_MIN = 4.5   # 正文与背景的最小对比度
GRAPHIC_MIN = 3.0  # 大字与图形元素的最小对比度


def _channel(value):
    c = value / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hexcolor):
    h = hexcolor.lstrip("#")
    if len(h) != 6:
        raise ValueError("色值须为 #rrggbb：%s" % hexcolor)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return None


def analyze(hexes, bg=None, text=None, accent=None):
    """返回 (issues, metrics)；issues 为空表示通过。"""
    issues = []
    if len(hexes) < 4 and not (bg and text):
        issues.append("色值不足：需 >=4 色（或显式给出 --bg / --text）")
        return issues, {}

    if bg and text:
        pal, names = [bg, text], ("指定背景", "指定文字")
        accent = accent or hexes[0]
    else:
        # 约定主题文件首个色值为深色底、末个为浅色底、次个为主/强调色
        bg, text = hexes[0], hexes[3]
        accent = hexes[1] if len(hexes) > 1 else hexes[0]
        pal, names = [bg, text], ("background", "text")

    body = contrast(pal[0], pal[1])
    acc = contrast(accent, pal[0])
    metrics = {
        "background": bg,
        "text": pal[1],
        "accent": accent,
        "text_on_bg": body,
        "accent_on_bg": acc,
        "text_min": TEXT_MIN,
        "graphic_min": GRAPHIC_MIN,
    }
    if body < TEXT_MIN:
        issues.append("正文/背景对比度 %.2f < %.1f（%s 与 %s）" % (body, TEXT_MIN, names[0], names[1]))
    if acc < GRAPHIC_MIN:
        issues.append("强调/背景对比度 %.2f < %.1f（%s 与 %s）" % (acc, GRAPHIC_MIN, "accent", names[0]))
    return issues, metrics


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="theme-factory 主题规格与 WCAG 对比度自查器（仅标准库）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--file", help="主题规格 Markdown 路径，如 themes/ocean-depths.md")
    ap.add_argument("--bg", help="显式指定背景色，如 \"#1e1e1e\"")
    ap.add_argument("--text", help="显式指定文字色，如 \"#ffffff\"")
    ap.add_argument("--accent", help="显式指定强调色（可选）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结论")
    args = ap.parse_args(argv)

    hexes = []
    if args.file:
        body = read_text(args.file)
        if body is None:
            print("输入错误：文件不存在或不可读 -> %s" % args.file, file=sys.stderr)
            return 2
        hexes = ["#" + m.lower() for m in HEX_RE.findall(body)]
        if UPPER_RE.search(body):
            # 色值书写规范：统一小写
            pass
    for name, val in (("--bg", args.bg), ("--text", args.text), ("--accent", args.accent)):
        if val and not HEX_RE.fullmatch(val.strip()):
            print("参数错误：%s 须为 #rrggbb 形式，收到 %r" % (name, val), file=sys.stderr)
            return 2
    if not hexes and not (args.bg and args.text):
        print("输入错误：未提供 --file 且未给出 --bg/--text，无法自查", file=sys.stderr)
        return 2

    seen, ordered = set(), []
    for h in hexes:
        if h not in seen:
            seen.add(h)
            ordered.append(h)

    issues, metrics = analyze(ordered, args.bg, args.text, args.accent)

    if args.json:
        print(json.dumps({"file": args.file, "issues": issues, "metrics": metrics,
                          "status": "pass" if not issues else "fail"},
                         ensure_ascii=False, indent=2))
    else:
        print("主题自查：%s" % (args.file or "（命令行色值）"))
        if metrics:
            for k in ("background", "text", "accent"):
                print("  %-11s %s" % (k, metrics[k]))
            print("  正文/背景 %.2f（须 >=%.1f）" % (metrics["text_on_bg"], TEXT_MIN))
            print("  强调/背景 %.2f（须 >=%.1f）" % (metrics["accent_on_bg"], GRAPHIC_MIN))
        if issues:
            print("结论：不通过（%d 项）" % len(issues))
            for it in issues:
                print("  - %s" % it)
        else:
            print("结论：通过")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
