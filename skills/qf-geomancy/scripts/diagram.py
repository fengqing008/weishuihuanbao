#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diagram.py —— 堪舆文化核心知识示意图（SVG，程序化绘制，零版权）

输出：
  luopan24.svg   二十四山罗盘示意（外圈二十四山 / 中圈八卦八宫 / 四正十字）
  sixiang.svg    四神砂方位示意（玄武后、朱雀前、青龙左、白虎右）

用法：
  python3 scripts/diagram.py --outdir images
"""
import os
import sys
import json
import math
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

BG = "#F7F3E8"
INK = "#3A322A"
GOLD = "#B8894A"
OCHRE = "#8C5A3C"
LINE = "#C9B79A"
FONT = "'Noto Serif SC','Source Han Serif SC',serif"


def svg_luopan():
    W = H = 860
    cx = cy = 430
    R_out, R_in, R_ring = 350, 210, 265
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="二十四山罗盘示意图">' % (W, H)]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    s.append('<text x="%d" y="46" font-family="%s" font-size="20" fill="%s" font-weight="700" text-anchor="middle">二十四山罗盘示意</text>' % (cx, FONT, INK))
    s.append('<text x="%d" y="70" font-family="%s" font-size="13" fill="%s" text-anchor="middle">外圈二十四山（每山十五度）｜中圈后天八卦八宫｜四正为子午卯酉</text>' % (cx, FONT, OCHRE))

    shan = json.load(open(os.path.join(ASSETS, "24shan.json"), encoding="utf-8"))["shan"]
    bagua = json.load(open(os.path.join(ASSETS, "bagua.json"), encoding="utf-8"))["bagua"]

    # 方位角：以正北（上）为 0，顺时针
    def polar(r, deg):
        a = math.radians(deg - 90)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    # 外圈与同心圆
    for r in (R_out, R_ring, R_in):
        s.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="1.2"/>' % (cx, cy, r, LINE))
    s.append('<circle cx="%d" cy="%d" r="120" fill="none" stroke="%s" stroke-width="1.4"/>' % (cx, cy, LINE))

    # 二十四山刻度与名
    for it in shan:
        d = it["center"]
        x1, y1 = polar(R_ring, d)
        x2, y2 = polar(R_out, d)
        s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="0.9"/>' % (x1, y1, x2, y2, LINE))
        tx, ty = polar((R_out + R_ring) / 2 + 6, d)
        s.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="17" fill="%s" text-anchor="middle" dominant-baseline="middle">%s</text>'
                 % (tx, ty, FONT, INK, it["name"]))

    # 八卦八宫（中圈）
    for b in bagua:
        d = float(b.get("center", 0)) if isinstance(b.get("center"), (int, float, str)) and str(b.get("center", "")).replace(".", "").isdigit() else None
        if d is None:
            dm = {"北": 0, "东北": 45, "东": 90, "东南": 135, "南": 180, "西南": 225, "西": 270, "西北": 315}
            d = dm.get(b.get("direction", ""), 0)
            b["_d"] = d
        tx, ty = polar((R_in + R_ring) / 2, d)
        s.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="19" fill="%s" text-anchor="middle" dominant-baseline="middle" font-weight="700">%s</text>'
                 % (tx, ty, FONT, OCHRE, b["name"]))

    # 四正十字
    for d in (0, 90, 180, 270):
        x1, y1 = polar(20, d)
        x2, y2 = polar(R_out, d)
        s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="0.8" stroke-dasharray="6 5"/>' % (x1, y1, x2, y2, GOLD))
    for lbl, d in (("北", 0), ("东", 90), ("南", 180), ("西", 270)):
        tx, ty = polar(R_out + 26, d)
        s.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="15" fill="%s" text-anchor="middle" dominant-baseline="middle" font-weight="700">%s</text>'
                 % (tx, ty, FONT, GOLD, lbl))

    s.append('<text x="%d" y="%d" font-family="%s" font-size="17" fill="%s" text-anchor="middle" font-weight="700">二十四山</text>' % (cx, cy - 6, FONT, INK))
    s.append('<text x="%d" y="%d" font-family="%s" font-size="12" fill="%s" text-anchor="middle">坐向与方位之参照</text>' % (cx, cy + 18, FONT, OCHRE))
    s.append('</svg>')
    return "\n".join(s)


def svg_sixiang():
    W, H = 980, 620
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="四神砂方位示意图">' % (W, H)]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    s.append('<text x="490" y="50" font-family="%s" font-size="20" fill="%s" font-weight="700" text-anchor="middle">四神砂方位示意</text>' % (FONT, INK))
    s.append('<text x="490" y="74" font-family="%s" font-size="13" fill="%s" text-anchor="middle">依《葬书》四神砂之说：玄武在后、朱雀在前、青龙在左、白虎在右</text>' % (FONT, OCHRE))

    cx, cy = 490, 340
    # 中心穴场
    s.append('<rect x="%d" y="%d" width="130" height="96" rx="6" fill="none" stroke="%s" stroke-width="1.8"/>' % (cx - 65, cy - 48, OCHRE))
    s.append('<text x="%d" y="%d" font-family="%s" font-size="16" fill="%s" text-anchor="middle" font-weight="700">穴场</text>' % (cx, cy + 6, FONT, INK))

    # 四方
    def block(x, y, w, h, name, pos, curve):
        return ('<path d="%s" fill="none" stroke="%s" stroke-width="2"/>'
                '<text x="%d" y="%d" font-family="%s" font-size="18" fill="%s" text-anchor="middle" font-weight="700">%s</text>'
                '<text x="%d" y="%d" font-family="%s" font-size="12.5" fill="%s" text-anchor="middle">%s</text>'
                % (curve, OCHRE, x, y, FONT, INK, name, x, y + 22, FONT, GOLD, pos))

    s.append(block(cx, 130, 0, 0, "玄武", "后（北）", "M370 200 Q490 96 610 200"))
    s.append(block(cx, 566, 0, 0, "朱雀", "前（南）", "M370 480 Q490 584 610 480"))
    s.append(block(180, 342, 0, 0, "青龙", "左（东）", "M266 214 Q162 340 266 466"))
    s.append(block(800, 342, 0, 0, "白虎", "右（西）", "M714 214 Q818 340 714 466"))

    # 中心到四方虚线
    for (x, y) in ((cx, 200), (cx, 480), (266, cy), (714, cy)):
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="0.8" stroke-dasharray="5 4"/>' % (cx, cy, x, y, LINE))

    s.append('<text x="490" y="604" font-family="%s" font-size="12" fill="%s" text-anchor="middle">本图为传统文化示意，用于说明四神砂的方位关系，不构成对环境吉凶之判断</text>' % (FONT, OCHRE))
    s.append('</svg>')
    return "\n".join(s)


DIAGRAMS = {"luopan": ("luopan24.svg", svg_luopan),
            "sixiang": ("sixiang.svg", svg_sixiang)}


def main():
    ap = argparse.ArgumentParser(description="堪舆文化核心示意图生成")
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
