#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""themeize.py — 给任意 HTML 一键换肤（theme-factory 通用包装器）

适用于任何输出 HTML 的技能：生成报告后调用本脚本换肤，不必改动原生成脚本。
依赖同目录的 theme_engine.py（缺失时把 theme-factory/scripts/theme_engine.py 复制过来即可）。

用法：
    python3 themeize.py --list-themes
    python3 themeize.py -i 报告.html -t ocean-depths              # 输出 报告_ocean-depths.html
    python3 themeize.py -i 报告.html -t midnight-galaxy --mode dark -o 效果.html
    python3 themeize.py -i 报告.html -t tech-innovation --keep "#123456"
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    from theme_engine import apply, slots, list_themes
except ImportError:
    raise SystemExit("缺少 theme_engine.py：请把 theme-factory/scripts/theme_engine.py 复制到本脚本同目录")


def main():
    ap = argparse.ArgumentParser(description="HTML 主题换肤器（theme-factory）")
    ap.add_argument("-i", "--input", help="待换肤的 HTML")
    ap.add_argument("-t", "--theme", help="主题 slug")
    ap.add_argument("-o", "--output", help="输出路径（默认 原名_主题.html）")
    ap.add_argument("--mode", choices=["light", "dark"], default="light")
    ap.add_argument("--keep", default="", help="额外豁免的色值，逗号分隔，如 #123456,#abcdef")
    ap.add_argument("--list-themes", action="store_true", help="列出全部主题")
    a = ap.parse_args()
    if a.list_themes or not a.input:
        for slug, cn, cols in list_themes():
            print("%-20s %-8s %s" % (slug, cn, " ".join(cols)))
        return
    if not a.theme:
        raise SystemExit("请用 -t 指定主题（--list-themes 查看可选值）")
    try:
        s = slots(a.theme, a.mode)
    except KeyError as e:
        raise SystemExit(str(e))
    src = pathlib.Path(a.input).read_text(encoding="utf-8")
    out, mapping = apply(src, a.theme, a.mode, [x.strip() for x in a.keep.split(",") if x.strip()])
    dst = a.output or (str(pathlib.Path(a.input).with_suffix("")) + "_" + a.theme + ".html")
    pathlib.Path(dst).write_text(out, encoding="utf-8")
    print("换肤完成：%s → %s" % (a.input, dst))
    print("主题：%s（%s，%s 模式）　色值映射 %d 条" % (s["cn"], a.theme, a.mode, len(mapping)))
    for k in sorted(mapping):
        print("  %s → %s" % (k, mapping[k]))


if __name__ == "__main__":
    main()
