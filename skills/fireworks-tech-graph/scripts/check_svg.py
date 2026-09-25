#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_svg.py — SVG 交付前静态自检器

用途
    对 fireworks-tech-graph 产出的 SVG 做写入前五项自检与交付前复核：
      规则 1 标签平衡    规则 2 属性引号    规则 3 特殊字符转义
      规则 4 marker 引用    规则 5 闭合标签
    另附 viewBox 存在性、仅 defs 无图形（空白 PNG 前兆）、中文字体缺失等检查。

用法
    python3 scripts/check_svg.py out/arch.svg
    python3 scripts/check_svg.py out/arch.svg --json
    python3 scripts/check_svg.py out/arch.svg --cjk

退出码
    0 全部通过；1 存在失败项
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET

PAIRED = ["rect", "text", "g", "line", "path", "circle", "ellipse", "polygon", "polyline",
          "tspan", "defs", "marker", "pattern", "clipPath", "filter"]
GRAPHIC = ["rect", "text", "line", "path", "circle", "ellipse", "polygon", "polyline"]
CJK = re.compile(r"[\u4e00-\u9fff]")


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_tag_balance(svg):
    fails = []
    for tag in PAIRED:
        opens = len(re.findall(r"<%s[\s>]" % tag, svg))
        self_closing = len(re.findall(r"<%s\b[^>]*/>" % tag, svg, re.S))
        closes = len(re.findall(r"</%s\s*>" % tag, svg))
        if opens and opens - self_closing != closes:
            fails.append("标签不平衡 <%s>：开 %d / 自闭 %d / 闭 %d" % (tag, opens, self_closing, closes))
    return fails


def check_quotes(svg):
    bare = re.findall(r"\s([A-Za-z\-]+)=([^\"'\s>][^\s>]*)", svg)
    return ["属性值未加引号：%s=%s" % (k, v) for k, v in bare]


def check_entities(svg):
    fails = []
    for m in re.finditer(r"<text[^>]*>(.*?)</text>", svg, re.S):
        inner = m.group(1)
        if re.search(r"<(?![/]?(tspan|title|desc)\b)", inner):
            fails.append("文本节点内含未转义的尖括号：%s" % inner[:40])
        for raw in [" & ", " > ", " < "]:
            if raw in inner and "&amp;" not in raw:
                fails.append("文本节点内含未转义符号「%s」：%s" % (raw.strip(), inner[:40]))
                break
    return fails


def check_markers(svg):
    used = set(re.findall(r'url\(#([\w\-]+)\)', svg))
    defined = set(re.findall(r'<marker\b[^>]*id="([\w\-]+)"', svg))
    missing = sorted(u for u in used if u not in defined and not re.match(r"^(grid|bg)", u))
    return ["引用了未定义的 marker 或图案：#%s" % m for m in missing]


def check_structure(svg):
    fails = []
    if not svg.rstrip().endswith("</svg>"):
        fails.append("缺少 </svg> 闭合标签")
    if "viewBox" not in svg:
        fails.append("缺少 viewBox，缩放会失真")
    graphic_hits = sum(len(re.findall(r"<%s[\s>]" % t, svg)) for t in GRAPHIC)
    if graphic_hits == 0:
        fails.append("仅含 defs 无图形元素，PNG 大概率为空白图")
    return fails


def check_cjk_font(svg):
    if CJK.search(svg) and "font-family" not in svg:
        return ["含中文字符但未声明 font-family，导出 PNG 时中文大概率缺失字形"]
    return []


def check_xml(svg_path):
    try:
        ET.parse(svg_path)
        return []
    except ET.ParseError as exc:
        return ["XML 解析失败：%s" % exc]


def main():
    ap = argparse.ArgumentParser(description="SVG 交付前静态自检器")
    ap.add_argument("svg", help="待检查的 SVG 文件路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--cjk", action="store_true", help="追加中文字体检查")
    args = ap.parse_args()

    try:
        svg = read(args.svg)
    except OSError as exc:
        print("[失败] 无法读取文件：%s" % exc, file=sys.stderr)
        return 1

    groups = [
        ("规则1 标签平衡", check_tag_balance(svg)),
        ("规则2 属性引号", check_quotes(svg)),
        ("规则3 特殊字符", check_entities(svg)),
        ("规则4 marker引用", check_markers(svg)),
        ("规则5 结构与闭合", check_structure(svg)),
        ("XML 解析", check_xml(args.svg)),
    ]
    if args.cjk:
        groups.append(("中文字体", check_cjk_font(svg)))

    total = sum(len(items) for _, items in groups)
    if args.json:
        print(json.dumps({"file": args.svg, "passed": total == 0,
                          "issues": {name: items for name, items in groups}},
                         ensure_ascii=False, indent=2))
    else:
        for name, items in groups:
            print("[%s] %s" % ("通过" if not items else "失败", name))
            for item in items:
                print("    - %s" % item)
        print("合计问题 %d 项 —— %s" % (total, "交付前复核通过" if total == 0 else "需按 Quick Fix 协议修复后重检"))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
