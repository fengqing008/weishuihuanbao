#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diagram.py —— 姓氏溯源核心知识示意图（SVG，程序化绘制，零版权）

输出：
  surname_rank.svg   全国前十姓人口条形图（本姓高亮）+ 本姓排名定位

用法：
  python3 scripts/diagram.py --outdir images --surname 王
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
HILITE = "#A3402A"
LINE = "#C9B79A"
FONT = "'Noto Serif SC','Source Han Serif SC',serif"


def svg_rank(surname):
    data = json.load(open(os.path.join(ASSETS, "surname_rank.json"), encoding="utf-8"))
    ranks = data["ranks"]
    top = [r for r in ranks if r.get("pop_wan")][:10]
    me = next((r for r in ranks if r["surname"] == surname), None)
    if not top:
        top = ranks[:10]

    W, H = 1000, 620
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="姓氏人口排名示意图">' % (W, H)]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    s.append('<text x="60" y="52" font-family="%s" font-size="20" fill="%s" font-weight="700">全国前十姓人口</text>' % (FONT, INK))
    src = data["meta"].get("pop_source", "")
    s.append('<text x="60" y="76" font-family="%s" font-size="12.5" fill="%s">数据来源：%s</text>' % (FONT, OCHRE, src[:46]))

    mx = max(r["pop_wan"] for r in top)
    for i, r in enumerate(top):
        y = 118 + i * 46
        hit = (r["surname"] == surname)
        col = HILITE if hit else OCHRE
        s.append('<text x="60" y="%d" font-family="%s" font-size="15" fill="%s" font-weight="%s">%d. %s</text>'
                 % (y + 5, FONT, INK, "700" if hit else "400", r["rank"], r["surname"]))
        w = 470 * r["pop_wan"] / mx
        s.append('<rect x="150" y="%d" width="%.1f" height="20" rx="3" fill="%s" opacity="%s"/>'
                 % (y - 11, w, col, "1" if hit else "0.7"))
        s.append('<text x="%.1f" y="%d" font-family="%s" font-size="13.5" fill="%s">%s万人</text>'
                 % (158 + w, y + 5, FONT, GOLD if not hit else HILITE, "{:,.1f}".format(r["pop_wan"])))

    # 右侧：本姓定位
    if me:
        bx = 700
        s.append('<rect x="%d" y="104" width="250" height="196" rx="8" fill="none" stroke="%s" stroke-width="1.5"/>' % (bx, HILITE))
        s.append('<text x="%d" y="142" font-family="%s" font-size="15" fill="%s">本姓排名</text>' % (bx + 24, FONT, OCHRE))
        s.append('<text x="%d" y="196" font-family="%s" font-size="46" fill="%s" font-weight="700">第 %d</text>'
                 % (bx + 24, FONT, HILITE, me["rank"]))
        s.append('<text x="%d" y="228" font-family="%s" font-size="14" fill="%s">%s姓</text>' % (bx + 24, FONT, INK, surname))
        if me.get("pop_wan"):
            s.append('<text x="%d" y="256" font-family="%s" font-size="14" fill="%s">约 %s 万人</text>'
                     % (bx + 24, FONT, INK, "{:,.1f}".format(me["pop_wan"])))
        if me.get("share"):
            s.append('<text x="%d" y="280" font-family="%s" font-size="14" fill="%s">占全国 %s</text>'
                     % (bx + 24, FONT, INK, me["share"]))

    s.append('<text x="60" y="%d" font-family="%s" font-size="12" fill="%s">注：第 1—10 位人口为官方公布约数；全部数字为约数，供文化了解参考，不作判断依据</text>'
             % (H - 24, FONT, OCHRE))
    s.append('</svg>')
    return "\n".join(s)


def main():
    ap = argparse.ArgumentParser(description="姓氏溯源核心示意图生成")
    ap.add_argument("--outdir", default="images")
    ap.add_argument("--surname", default="王")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    p = os.path.join(a.outdir, "surname_rank.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(svg_rank(a.surname))
    print("[OK] %s（%d 字节）" % (p, os.path.getsize(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
