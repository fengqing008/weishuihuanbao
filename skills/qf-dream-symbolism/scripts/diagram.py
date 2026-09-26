#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diagram.py —— 梦象解读核心知识示意图（SVG，程序化绘制，零版权）

输出：
  sixdream.svg       《周礼》六梦结构示意（正噩梦思寤喜惧）
  symbol_cats.svg    意象类别分布图（按 dream_symbols.json 分类统计）

用法：
  python3 scripts/diagram.py --outdir images
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

BG = "#F7F3E8"
INK = "#3A322A"
GOLD = "#B8894A"
OCHRE = "#8C5A3C"
LINE = "#C9B79A"
FONT = "'Noto Serif SC','Source Han Serif SC',serif"

SIX = [
    ("正梦", "无所感动，平安自梦", 0),
    ("噩梦", "惊愕而梦", 1),
    ("思梦", "觉时所思念而梦", 2),
    ("寤梦", "觉时道之而梦", 3),
    ("喜梦", "喜悦而梦", 4),
    ("惧梦", "恐惧而梦", 5),
]


def svg_sixdream():
    W, H = 1000, 420
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="周礼六梦结构示意图">' % (W, H)]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    s.append('<text x="500" y="52" font-family="%s" font-size="20" fill="%s" font-weight="700" text-anchor="middle">《周礼》六梦</text>' % (FONT, INK))
    s.append('<text x="500" y="76" font-family="%s" font-size="13" fill="%s" text-anchor="middle">《周礼·春官·占梦》以六类分梦，为传统析梦最早的分类框架</text>' % (FONT, OCHRE))
    bw, bh, gap = 148, 178, 16
    x0 = (W - (bw * 6 + gap * 5)) / 2
    for i, (name, desc, k) in enumerate(SIX):
        x = x0 + i * (bw + gap)
        s.append('<rect x="%.0f" y="130" width="%d" height="%d" rx="8" fill="none" stroke="%s" stroke-width="1.4"/>' % (x, bw, bh, LINE))
        s.append('<text x="%.0f" y="172" font-family="%s" font-size="20" fill="%s" text-anchor="middle" font-weight="700">%s</text>' % (x + bw / 2, FONT, OCHRE, name))
        # 描述按 7 字换行
        for j in range(0, len(desc), 7):
            s.append('<text x="%.0f" y="%d" font-family="%s" font-size="13" fill="%s" text-anchor="middle">%s</text>'
                     % (x + bw / 2, 208 + (j // 7) * 22, FONT, INK, desc[j:j + 7]))
        s.append('<text x="%.0f" y="%d" font-family="%s" font-size="11" fill="%s" text-anchor="middle">%d</text>' % (x + bw / 2, 288, FONT, GOLD, k + 1))
    s.append('<text x="500" y="380" font-family="%s" font-size="12" fill="%s" text-anchor="middle">本图为文化知识示意，用于说明六梦的分类方式，不构成对梦境的解释或预测</text>' % (FONT, OCHRE))
    s.append('</svg>')
    return "\n".join(s)


def svg_symbol_cats():
    data = json.load(open(os.path.join(ASSETS, "dream_symbols.json"), encoding="utf-8"))
    syms = data["symbols"]
    cats = {}
    for it in syms:
        cats[it.get("category", "其他")] = cats.get(it.get("category", "其他"), 0) + 1
    cats = sorted(cats.items(), key=lambda x: -x[1])

    W = 1000
    H = 150 + len(cats) * 46
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="梦境意象类别分布">' % (W, H)]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    s.append('<text x="60" y="52" font-family="%s" font-size="20" fill="%s" font-weight="700">意象类别分布</text>' % (FONT, INK))
    s.append('<text x="60" y="76" font-family="%s" font-size="13" fill="%s">本技能收录意象共 %d 个，按类别统计如下</text>' % (FONT, OCHRE, len(syms)))
    mx = max(c for _, c in cats)
    for i, (name, c) in enumerate(cats):
        y = 120 + i * 46
        s.append('<text x="60" y="%d" font-family="%s" font-size="15" fill="%s">%s</text>' % (y + 5, FONT, INK, name))
        w = 420 * c / mx
        s.append('<rect x="180" y="%d" width="%.0f" height="20" rx="3" fill="%s" opacity="0.75"/>' % (y - 11, w, OCHRE))
        s.append('<text x="%.0f" y="%d" font-family="%s" font-size="14" fill="%s">%d</text>' % (186 + w, y + 5, FONT, GOLD, c))
    s.append('</svg>')
    return "\n".join(s)


DIAGRAMS = {"sixdream": ("sixdream.svg", svg_sixdream),
            "cats": ("symbol_cats.svg", svg_symbol_cats)}


def main():
    ap = argparse.ArgumentParser(description="梦象解读核心示意图生成")
    ap.add_argument("--outdir", default="images")
    ap.add_argument("--only", choices=list(DIAGRAMS))
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for k in ([a.only] if a.only else list(DIAGRAMS)):
        fn, gen = DIAGRAMS[k]
        p = os.path.join(a.outdir, fn)
        with open(p, "w", encoding="utf-8") as f:
            f.write(gen())
        print("[OK] %s（%d 字节）" % (p, os.path.getsize(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
