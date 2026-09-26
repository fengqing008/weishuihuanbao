#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""palettes.py —— 十套配色定义、对比度校验与 CSS 变量生成

用法：
  python3 palettes.py list                    十套配色一览（含关键对比度）
  python3 palettes.py css [--theme ocean]     输出 CSS 变量块（省略 --theme 输出全部十套）
  python3 palettes.py check [--json]          WCAG 2.1 对比度校验，不达标退出码 1
  python3 palettes.py json                    导出完整 JSON（供 build_report.py 调用）

来源：theme-factory 十套主题原色；本脚本按长文阅读与打印场景补齐容器色、弱化色、
边框色与页头渐变，并按对比度下限对部分强调色做了加深。
"""
import argparse
import json
import sys

# ---------- 色彩工具 ----------


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(t):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in t)


def mix(a, b, w):
    ca, cb = hx(a), hx(b)
    return to_hex(tuple(ca[i] * (1 - w) + cb[i] * w for i in range(3)))


def lum(c):
    r, g, b = [v / 255 for v in hx(c)]

    def f(u):
        return u / 12.92 if u <= 0.03928 else ((u + 0.055) / 1.055) ** 2.4

    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def cr(a, b):
    la, lb = lum(a), lum(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


# ---------- 十套配色 ----------
RAW = [
    dict(id="ocean", zh="深海蓝调", name="Ocean Depths", mode="dark",
         bg="#14202e", surface="#1e2c3f", surface2="#223350", text="#eef7f2", muted="#a9c2c6",
         accent="#56c1c1", accent2="#a8dadc", border="#2e4457",
         use="领导汇报、数据仪表盘、咨询报告",
         origins=[["Deep Navy", "#1a2332"], ["Teal", "#2d8b8b"],
                  ["Seafoam", "#a8dadc"], ["Cream", "#f1faee"]]),
    dict(id="sunset", zh="日落大道", name="Sunset Boulevard", mode="light",
         bg="#fdf7f1", surface="#fdfdfd", surface2="#faefe6", text="#264653", muted="#63757c",
         accent="#b04623", accent2="#9c7420", border="#f0dccd",
         use="市场品牌、活动策划、传播型长图",
         origins=[["Burnt Orange", "#e76f51"], ["Coral", "#f4a261"],
                  ["Warm Sand", "#e9c46a"], ["Deep Teal", "#264653"]]),
    dict(id="forest", zh="森林冠层", name="Forest Canopy", mode="light",
         bg="#faf9f6", surface="#fdfdfd", surface2="#f1f2ec", text="#26391f", muted="#6b7360",
         accent="#40693f", accent2="#8d9470", border="#dfe2d6",
         use="环保与 ESG 报告、行业研究长文",
         origins=[["Forest Green", "#2d4a2b"], ["Sage", "#7d8471"],
                  ["Olive", "#a4ac86"], ["Ivory", "#faf9f6"]]),
    dict(id="minimal", zh="现代极简", name="Modern Minimalist", mode="light",
         bg="#f6f7f8", surface="#fdfdfd", surface2="#eef0f2", text="#232e36", muted="#64717c",
         accent="#36454f", accent2="#708090", border="#dde1e5",
         use="学术政策解读、数据密集页、打印分发",
         origins=[["Charcoal", "#36454f"], ["Slate Gray", "#708090"],
                  ["Light Gray", "#d3d3d3"], ["White", "#fdfdfd"]]),
    dict(id="golden", zh="金色时刻", name="Golden Hour", mode="light",
         bg="#fdf8ee", surface="#fdfdfd", surface2="#faf0dc", text="#3d342f", muted="#7b6a5d",
         accent="#8a6300", accent2="#c1666b", border="#ecdfc4",
         use="餐饮文旅、生活方式、节庆专题",
         origins=[["Mustard Yellow", "#f4a900"], ["Terracotta", "#c1666b"],
                  ["Warm Beige", "#d4b896"], ["Chocolate Brown", "#4a403a"]]),
    dict(id="arctic", zh="极地霜白", name="Arctic Frost", mode="light",
         bg="#f5f8fc", surface="#fdfdfd", surface2="#edf3fa", text="#1e3a5c", muted="#5a7592",
         accent="#3a628f", accent2="#5f86b0", border="#dbe6f2",
         use="医疗健康、技术方案、严谨型研究",
         origins=[["Ice Blue", "#d4e4f7"], ["Steel Blue", "#4a6fa5"],
                  ["Silver", "#c0c0c0"], ["Crisp White", "#fafafa"]]),
    dict(id="desert", zh="沙漠玫瑰", name="Desert Rose", mode="light",
         bg="#fdf5f1", surface="#fdfdfd", surface2="#f8ece5", text="#4a2537", muted="#8a6a78",
         accent="#9c5670", accent2="#b87d6d", border="#eeddd4",
         use="品牌设计、美学类内容、室内房产",
         origins=[["Dusty Rose", "#d4a5a5"], ["Clay", "#b87d6d"],
                  ["Sand", "#e8d5c4"], ["Deep Burgundy", "#5d2e46"]]),
    dict(id="tech", zh="科技创新", name="Tech Innovation", mode="dark",
         bg="#171717", surface="#212121", surface2="#262a33", text="#f2f6ff", muted="#9eacbd",
         accent="#4d94ff", accent2="#22d3ee", border="#333844",
         use="技术前沿综述、产品发布、AI 议题",
         origins=[["Electric Blue", "#0066ff"], ["Neon Cyan", "#00ffff"],
                  ["Dark Gray", "#1e1e1e"], ["White", "#fdfdfd"]]),
    dict(id="botanical", zh="植物园", name="Botanical Garden", mode="light",
         bg="#f6f4ee", surface="#fdfdfd", surface2="#eff1e6", text="#29382c", muted="#6a7764",
         accent="#3c6b4a", accent2="#b5780a", border="#e2dfd2",
         use="环保农业、食品与自然主题、科普",
         origins=[["Fern Green", "#4a7c59"], ["Marigold", "#f9a620"],
                  ["Terracotta", "#b7472a"], ["Cream", "#f5f3ed"]]),
    dict(id="galaxy", zh="午夜星河", name="Midnight Galaxy", mode="dark",
         bg="#241834", surface="#2f2144", surface2="#382a4f", text="#ece9f8", muted="#b1a6cf",
         accent="#a490c2", accent2="#8589e0", border="#453764",
         use="投资与财务分析、高端品牌",
         origins=[["Deep Purple", "#2b1e3e"], ["Cosmic Blue", "#4a4e8f"],
                  ["Lavender", "#a490c2"], ["Silver", "#e6e6fa"]]),
]

GATE = {"textBg": 4.5, "textSurf": 4.5, "mutedSurf": 4.5, "accentBg": 4.5,
        "accent2Bg": 3.0, "heroText": 4.5, "heroText2": 4.5, "okSurf": 4.5,
        "dangerSurf": 4.5, "onAccent": 4.5}


def build(raw):
    t = dict(raw)
    dark = t["mode"] == "dark"
    w1, w2 = (0.55, 0.72) if dark else (0.30, 0.55)
    # hero 渐变：弃用 #0e0e0e 黑色（突兀），改用各主题「接近主题色的深色」做过渡
    # 亮模式用 text（深字色），暗模式用 surface（卡片色）
    if dark:
        base1, base2 = t["surface"], t["surface2"]
    else:
        base1, base2 = t["text"], t["text"]
    t["hero1"] = mix(t["accent"], base1, w1)
    t["hero2"] = mix(t["accent2"], base2, w2)
    t["heroText"] = "#fdfdfd"
    t["ok"] = "#4ade80" if dark else "#0f7a45"
    t["danger"] = "#ff8b7b" if dark else "#c0392b"
    t["accentSoft"] = mix(t["accent"], t["bg"], 0.84 if dark else 0.88)
    t["onAccent"] = "#fdfdfd" if cr("#fdfdfd", t["accent"]) >= cr("#101418", t["accent"]) else "#101418"
    t["c"] = {
        "textBg": cr(t["text"], t["bg"]), "textSurf": cr(t["text"], t["surface"]),
        "mutedSurf": cr(t["muted"], t["surface"]), "accentBg": cr(t["accent"], t["bg"]),
        "accent2Bg": cr(t["accent2"], t["bg"]), "heroText": cr(t["heroText"], t["hero1"]),
        "heroText2": cr(t["heroText"], t["hero2"]), "okSurf": cr(t["ok"], t["surface"]),
        "dangerSurf": cr(t["danger"], t["surface"]), "onAccent": cr(t["onAccent"], t["accent"]),
    }
    t["ok_all"] = all(t["c"][k] >= v for k, v in GATE.items())
    t["fail"] = [k for k, v in GATE.items() if t["c"][k] < v]
    return t


PALETTES = [build(r) for r in RAW]
BY_ID = {p["id"]: p for p in PALETTES}
VARS = ["bg", "surface", "surface2", "text", "muted", "accent", "accent2", "accentSoft",
        "onAccent", "border", "hero1", "hero2", "heroText", "ok", "danger"]
CSSNAME = {"surface2": "surface-2", "accent2": "accent-2", "accentSoft": "accent-soft",
           "onAccent": "on-accent", "hero1": "hero-1", "hero2": "hero-2", "heroText": "hero-text"}


def css_block(t, sel=None):
    sel = sel or ('[data-theme="%s"]' % t["id"])
    body = "\n".join("  --%s: %s;" % (CSSNAME.get(v, v), t[v]) for v in VARS)
    return "%s {\n%s\n}" % (sel, body)


def cmd_list(_):
    print("%-10s %-8s %-18s %-9s %-9s %s" % ("id", "模式", "名称", "正文:底", "强调:底", "适用"))
    for p in PALETTES:
        print("%-10s %-8s %-18s %-9.2f %-9.2f %s" % (
            p["id"], "深色" if p["mode"] == "dark" else "浅色", p["zh"], p["c"]["textBg"],
            p["c"]["accentBg"], p["use"]))


def cmd_css(a):
    if a.theme:
        t = BY_ID.get(a.theme)
        if not t:
            print("未知配色：%s（可用：%s）" % (a.theme, ", ".join(BY_ID)), file=sys.stderr)
            return 2
        print(css_block(t, a.selector))
        return 0
    first = PALETTES[0]
    print(css_block(first, a.selector or (':root, [data-theme="%s"]' % first["id"])))
    for p in PALETTES[1:]:
        print(css_block(p))
    return 0


def cmd_check(a):
    rows, bad = [], []
    for p in PALETTES:
        row = dict(id=p["id"], zh=p["zh"], ok=p["ok_all"], fail=p["fail"],
                   **{k: round(v, 2) for k, v in p["c"].items()})
        rows.append(row)
        if not p["ok_all"]:
            bad.append(row)
    if a.json:
        print(json.dumps({"gate": GATE, "rows": rows, "unsatisfied": bad}, ensure_ascii=False, indent=1))
    else:
        print("WCAG 2.1 对比度校验（门禁：正文/弱化/强调/页头白字 ≥4.5，装饰辅色 ≥3.0）")
        print("%-10s %-9s %-9s %-9s %-9s %-9s %s" % ("id", "正文:底", "弱化:卡", "强调:底", "辅色:底", "页头白字", "判定"))
        for r in rows:
            print("%-10s %-9.2f %-9.2f %-9.2f %-9.2f %-9.2f %s" % (
                r["id"], r["textBg"], r["mutedSurf"], r["accentBg"], r["accent2Bg"],
                min(r["heroText"], r["heroText2"]), "通过" if r["ok"] else "需调整 " + ",".join(r["fail"])))
        print("通过 %d/%d" % (len(PALETTES) - len(bad), len(PALETTES)))
    return 1 if bad else 0


def cmd_json(_):
    print(json.dumps({"gate": GATE, "palettes": PALETTES}, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description="十套配色与对比度校验")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    p = sub.add_parser("css"); p.add_argument("--theme"); p.add_argument("--selector"); p.set_defaults(func=cmd_css)
    p = sub.add_parser("check"); p.add_argument("--json", action="store_true"); p.set_defaults(func=cmd_check)
    sub.add_parser("json").set_defaults(func=cmd_json)
    a = ap.parse_args()
    sys.exit(a.func(a) or 0)


if __name__ == "__main__":
    main()
