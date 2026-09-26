# -*- coding: utf-8 -*-
"""luopan.py — 二十四山与八卦方位查询（堪舆文化视角）

用法:
  python3 luopan.py --deg 120            # 按度数定山
  python3 luopan.py --name 巽             # 按山名查询
  python3 luopan.py --bagua 巽            # 按八卦查看所辖三山
  python3 luopan.py --list                # 列二十四山
  python3 luopan.py --json --deg 90
"""
import os
import sys
import json
import argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE, "assets")


def load(fn):
    with open(os.path.join(ASSETS, fn), encoding="utf-8") as f:
        return json.load(f)


def normalize(d):
    return d % 360


def shan_of_deg(shan, deg):
    """二十四山各占 15 度，中心度 ±7.5。"""
    deg = normalize(deg)
    for s in shan:
        lo = normalize(s["center"] - 7.5)
        hi = normalize(s["center"] + 7.5)
        if lo < hi:
            if lo <= deg < hi:
                return s
        else:  # 跨 0 度
            if deg >= lo or deg < hi:
                return s
    return None


def main():
    ap = argparse.ArgumentParser(description="二十四山与八卦方位查询（堪舆文化视角）")
    ap.add_argument("--deg", type=float, help="方位度数（0=正北，顺时针）")
    ap.add_argument("--name", default="", help="山名")
    ap.add_argument("--bagua", default="", help="八卦名")
    ap.add_argument("--list", action="store_true", help="列二十四山")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    shan = load("24shan.json")
    bagua = load("bagua.json")

    if a.list:
        for s in shan["shan"]:
            print("%-2s 中心%3d°  %s  %s宫  [%s]" %
                  (s["name"], s["center"], s["wuxing"], s["bagua"], s["type"]))
        print("\n共 %d 山（后天八卦分辖八宫，每宫三山）" % shan["count"])
        return

    if a.bagua:
        g = [b for b in bagua["bagua"] if b["name"] == a.bagua]
        if not g:
            print("无此卦：%s" % a.bagua, file=sys.stderr)
            sys.exit(1)
        b = g[0]
        print("【%s】方位 %s（%s）　五行 %s" % (b["name"], b["direction"], b["shan"], b["wuxing"]))
        print("  度数区间：%.1f° — %.1f°" % (b["start"], b["end"]))
        print("  寓意：%s" % b["note"])
        for s in shan["shan"]:
            if s["bagua"] == b["name"]:
                print("  ├ %s（%s，%d°）：%s" % (s["name"], s["wuxing"], s["center"], s["note"]))
        return

    if a.name:
        m = [s for s in shan["shan"] if s["name"] == a.name.replace("山", "")]
        if not m:
            print("无此山：%s" % a.name, file=sys.stderr)
            sys.exit(1)
        s = m[0]
        if a.json:
            print(json.dumps(s, ensure_ascii=False, indent=1))
        else:
            print("【%s】%s宫　五行 %s　%s" % (s["name"], s["bagua"], s["wuxing"], s["type"]))
            print("  中心度数：%d°（辖 %.1f°—%.1f°）" % (s["center"], normalize(s["center"] - 7.5), normalize(s["center"] + 7.5)))
            print("  说明：%s" % s["note"])
        return

    if a.deg is not None:
        s = shan_of_deg(shan["shan"], a.deg)
        g = [b for b in bagua["bagua"] if b["name"] == s["bagua"]][0]
        if a.json:
            print(json.dumps({"deg": a.deg, "shan": s, "bagua": g}, ensure_ascii=False, indent=1))
        else:
            print("方位 %g° → 【%s】山（%s宫，五行 %s）" % (a.deg, s["name"], s["bagua"], s["wuxing"]))
            print("  所属八卦：%s（%s）" % (g["name"], g["direction"]))
            print("  说明：%s" % s["note"])
        return

    ap.error("请用 --deg / --name / --bagua / --list 之一")
    print("说明：本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")


if __name__ == "__main__":
    main()
