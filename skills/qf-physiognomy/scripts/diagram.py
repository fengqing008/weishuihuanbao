#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diagram.py —— 生成相学文化核心知识示意图（SVG，程序化绘制，零版权）

输出：
  face_palace12.svg  面部十二宫分布示意（左侧面容 + 编号点，右侧十二宫对照）
  wuxing5.svg        五行形相示意（五种脸形轮廓并排）

用法：
  python3 scripts/diagram.py --outdir images            # 生成全部图
  python3 scripts/diagram.py --outdir images --only palace12
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

# 十二宫在面部示意图上的坐标（画布 560×620，脸中心 x=280）
PALACE_POS = {
    "命宫": (280, 208), "官禄宫": (280, 118), "迁移宫": (418, 140),
    "父母宫": (142, 140), "福德宫": (128, 232), "兄弟宫": (214, 226),
    "田宅宫": (222, 258), "妻妾宫": (196, 268), "男女宫": (224, 296),
    "疾厄宫": (280, 262), "财帛宫": (280, 300), "奴仆宫": (280, 486),
}


def svg_palace12():
    W, H = 1180, 640
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="面部十二宫分布示意图">' % (W, H)]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))

    # 面容轮廓（左侧）
    s.append('<g transform="translate(0,10)">')
    s.append('<ellipse cx="280" cy="320" rx="182" ry="232" fill="none" stroke="%s" stroke-width="1.6"/>' % LINE)
    # 发际线
    s.append('<path d="M108 240 Q280 130 452 240" fill="none" stroke="%s" stroke-width="1.2" stroke-dasharray="5 4"/>' % LINE)
    # 眉
    s.append('<path d="M186 224 Q214 214 244 224" fill="none" stroke="%s" stroke-width="2.4"/>' % OCHRE)
    s.append('<path d="M316 224 Q346 214 374 224" fill="none" stroke="%s" stroke-width="2.4"/>' % OCHRE)
    # 眼
    s.append('<path d="M192 260 Q222 246 252 260 Q222 272 192 260 Z" fill="none" stroke="%s" stroke-width="1.6"/>' % INK)
    s.append('<path d="M308 260 Q338 246 368 260 Q338 272 308 260 Z" fill="none" stroke="%s" stroke-width="1.6"/>' % INK)
    # 鼻
    s.append('<path d="M280 250 L268 306 Q280 316 292 306 Z" fill="none" stroke="%s" stroke-width="1.5"/>' % INK)
    # 口
    s.append('<path d="M232 380 Q280 366 328 380 Q280 402 232 380 Z" fill="none" stroke="%s" stroke-width="1.6"/>' % INK)
    # 下颌线
    s.append('<path d="M150 420 Q280 560 410 420" fill="none" stroke="%s" stroke-width="1.2" stroke-dasharray="5 4"/>' % LINE)
    s.append('</g>')

    # 十二宫点与编号（左侧）
    labels = list(PALACE_POS.items())
    for i, (name, (x, y)) in enumerate(labels, 1):
        yy = y + 10
        s.append('<circle cx="%d" cy="%d" r="11" fill="%s"/>' % (x, yy, GOLD))
        s.append('<text x="%d" y="%d" font-family="%s" font-size="12" fill="%s" text-anchor="middle">%d</text>'
                 % (x, yy + 4, FONT, BG, i))

    # 右侧对照表
    s.append('<text x="640" y="70" font-family="%s" font-size="21" fill="%s" font-weight="700">面部十二宫</text>' % (FONT, INK))
    s.append('<text x="640" y="98" font-family="%s" font-size="13" fill="%s">依《麻衣神相》卷三「十二宫论」，属传统之部位划分</text>' % (FONT, OCHRE))
    s.append('<line x1="640" y1="112" x2="1130" y2="112" stroke="%s" stroke-width="1"/>' % LINE)
    p12 = json.load(open(os.path.join(ASSETS, "palace12.json"), encoding="utf-8"))
    for i, p in enumerate(p12["palaces"], 1):
        y = 142 + (i - 1) * 39
        s.append('<circle cx="658" cy="%d" r="10" fill="%s"/>' % (y - 4, GOLD))
        s.append('<text x="658" y="%d" font-family="%s" font-size="11" fill="%s" text-anchor="middle">%d</text>' % (y, FONT, BG, i))
        s.append('<text x="680" y="%d" font-family="%s" font-size="14.5" fill="%s" font-weight="700">%s</text>' % (y, FONT, INK, p["name"]))
        s.append('<text x="756" y="%d" font-family="%s" font-size="13" fill="%s">%s</text>' % (y, FONT, OCHRE, p["pos"]))
    s.append('</svg>')
    return "\n".join(s)


def svg_wuxing5():
    W, H = 1180, 400
    shapes = [
        ("金形", "面方而正", "M-58 -70 L58 -70 L58 70 L-58 70 Z"),
        ("木形", "面长而瘦", "M-46 -84 Q0 -92 46 -84 Q40 84 0 90 Q-40 84 -46 -84 Z"),
        ("水形", "面圆而润", "M-54 -66 Q0 -90 54 -66 Q70 0 54 66 Q0 90 -54 66 Q-70 0 -54 -66 Z"),
        ("火形", "上尖下阔", "M-22 -78 Q0 -88 22 -78 Q62 20 58 66 Q0 92 -58 66 Q-62 20 -22 -78 Z"),
        ("土形", "面圆而厚", "M-60 -62 Q0 -78 60 -62 Q74 30 52 72 Q0 92 -52 72 Q-74 30 -60 -62 Z"),
    ]
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="五行形相示意图">' % (W, H)]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    s.append('<text x="590" y="54" font-family="%s" font-size="21" fill="%s" font-weight="700" text-anchor="middle">五行形相</text>' % (FONT, INK))
    s.append('<text x="590" y="82" font-family="%s" font-size="13" fill="%s" text-anchor="middle">依《神相全编·五行形相》，以五行比类脸形之传统方法</text>' % (FONT, OCHRE))
    for i, (name, desc, path) in enumerate(shapes):
        cx = 150 + i * 222
        s.append('<g transform="translate(%d,240)">' % cx)
        s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2"/>' % (path, OCHRE))
        # 简化的五官线
        s.append('<path d="M-30 -22 Q-14 -27 2 -22" fill="none" stroke="%s" stroke-width="1.6"/>' % LINE)
        s.append('<path d="M-2 -22 Q14 -27 30 -22" fill="none" stroke="%s" stroke-width="1.6"/>' % LINE)
        s.append('<path d="M-22 4 Q-8 -4 6 4" fill="none" stroke="%s" stroke-width="1.3"/>' % LINE)
        s.append('<path d="M-6 4 Q8 -4 22 4" fill="none" stroke="%s" stroke-width="1.3"/>' % LINE)
        s.append('<text x="0" y="128" font-family="%s" font-size="17" fill="%s" font-weight="700" text-anchor="middle">%s</text>' % (FONT, INK, name))
        s.append('<text x="0" y="150" font-family="%s" font-size="12.5" fill="%s" text-anchor="middle">%s</text>' % (FONT, OCHRE, desc))
        s.append('</g>')
    s.append('</svg>')
    return "\n".join(s)


DIAGRAMS = {"palace12": ("face_palace12.svg", svg_palace12),
            "wuxing": ("wuxing5.svg", svg_wuxing5)}


def main():
    ap = argparse.ArgumentParser(description="相学文化核心示意图生成")
    ap.add_argument("--outdir", default="images")
    ap.add_argument("--only", choices=list(DIAGRAMS), help="只生成指定图")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    keys = [a.only] if a.only else list(DIAGRAMS)
    for k in keys:
        fn, gen = DIAGRAMS[k]
        p = os.path.join(a.outdir, fn)
        with open(p, "w", encoding="utf-8") as f:
            f.write(gen())
        print("[OK] %s（%d 字节）" % (p, os.path.getsize(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
