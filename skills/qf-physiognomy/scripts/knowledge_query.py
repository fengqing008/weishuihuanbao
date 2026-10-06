#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""knowledge_query.py —— 相学文化知识全集查询入口（仅标准库）

把 assets/ 下的知识件统一成可检索的入口，供「相学知识全集」报告与人工查阅使用。
不承担对具体个人的判断，全部输出为知识史陈述。

用法：
  python3 scripts/knowledge_query.py --palaces-full        # 十二宫逐宫通论
  python3 scripts/knowledge_query.py --show-palace 命宫
  python3 scripts/knowledge_query.py --themes              # 议题史清单
  python3 scripts/knowledge_query.py --show-theme 寿夭      # 单议题（含现代审视）
  python3 scripts/knowledge_query.py --schools             # 流派
  python3 scripts/knowledge_query.py --timeline            # 典籍年表
  python3 scripts/knowledge_query.py --qise                # 气色论
  python3 scripts/knowledge_query.py --shengu              # 神骨论
  python3 scripts/knowledge_query.py --wuguan              # 五官详论
  python3 scripts/knowledge_query.py --classics            # 所引典籍
  python3 scripts/knowledge_query.py --overview --json     # 汇总（JSON）
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")


def load(name):
    p = os.path.join(ASSETS, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _hr(title):
    print("\n" + "=" * 66)
    print(title)
    print("=" * 66)


def cmd_palaces_full():
    d = load("palaces_full.json") or {}
    _hr("十二宫逐宫通论")
    for p in d.get("palaces", []):
        print("\n【%s】%s" % (p["name"], p["pos"]))
        print("  传统所主：%s" % p["sizhu"])
        print("  典籍原文：%s（%s）" % (p["classic"], p["source"]))
        print("  形态名目：%s" % "、".join(p["morphology"]))
        print("  各派差异：%s" % p["schools"])
        print("  文化说明：%s" % p["culture"])
    return 0


def cmd_show_palace(name):
    d = load("palaces_full.json") or {}
    for p in d.get("palaces", []):
        if name in (p["name"], p["name"].replace("宫", "")):
            print(json.dumps(p, ensure_ascii=False, indent=2))
            return 0
    print("[未找到] %s（可用 --palaces-full 查看全部）" % name)
    return 1


def cmd_themes():
    d = load("themes.json") or {}
    _hr("传统相学议题史（清单）")
    print(d.get("说明", ""))
    for t in d.get("themes", []):
        print("  [%s] %s —— %s" % (t["key"], t["name"], t["summary"]))
        print("        结语：%s" % t["status"])
    return 0


def cmd_show_theme(key):
    d = load("themes.json") or {}
    for t in d.get("themes", []):
        if key in (t["key"], t["name"]) or key in t["name"]:
            _hr(t["name"])
            print("命题概要：%s\n" % t["summary"])
            print("古人论说：")
            for v in t["classic_views"]:
                print("  · %s —— %s" % (v["text"], v["source"]))
            print("\n流变：%s" % t["history"])
            print("\n现代审视：%s" % t["critique"])
            print("\n结语：%s" % t["status"])
            return 0
    print("[未找到] %s（可用 --themes 查看全部议题）" % key)
    return 1


def cmd_schools():
    d = load("schools.json") or {}
    _hr("相学流派")
    for s in d.get("schools", []):
        print("\n【%s】%s" % (s["name"], s["period"]))
        print("  代表：%s" % "、".join(s["representatives"]))
        print("  主张：%s" % s["method"])
        print("  说明：%s" % s["note"])
    return 0


def cmd_timeline():
    d = load("schools.json") or {}
    _hr("典籍源流年表")
    for t in d.get("timeline", []):
        print("  %-8s %s" % (t["era"], t["work"]))
        print("           %s" % t["note"])
    print("\n%s" % d.get("托名说明", ""))
    return 0


def cmd_qise():
    d = load("qise.json") or {}
    _hr("气色论")
    print("五色配五行：")
    for w in d.get("wuse", []):
        print("  %s—%s（望诊多应%s）%s" % (w["color"], w["element"], w["tcm_organ"], w["note"]))
    print("\n四时配色（相书说）：")
    for s in d.get("siji", []):
        print("  %s：%s" % (s["season"], s["note"]))
    print("\n分部气色（相书说）：")
    for b in d.get("bufen", []):
        print("  %s：%s" % (b["part"], b["note"]))
    print("\n现代审视：%s" % d.get("critique", ""))
    return 0


def cmd_shengu():
    d = load("shengu.json") or {}
    _hr("神骨论（《冰鉴》一派）")
    for it in d.get("items", []):
        print("\n【%s】%s（%s）" % (it["name"], it["content"], it["source"]))
        print("  按：%s" % it["note"])
    print("\n现代审视：%s" % d.get("critique", ""))
    return 0


def cmd_wuguan():
    d = load("wuguan.json") or {}
    _hr("五官详论")
    for o in d.get("organs", []):
        print("\n【%s】%s｜配五行：%s" % (o["name"], o["guan"], o["wuxing"]))
        print("  论说：%s" % o["function"])
        print("  形态名目：%s" % "、".join(o["morphology"]))
        print("  出处：%s" % o["source"])
    return 0


def cmd_classics():
    d = load("classics.json") or {}
    _hr("所引典籍")
    print(d.get("说明", ""))
    for x in d.get("items", []):
        print("  %-8s %-22s %s" % (x["name"], x["attr"], x["era"]))
    print("\n合计 %d 部。" % len(d.get("items", [])))
    return 0


def cmd_overview(json_out):
    ov = {
        "十二宫": len((load("palaces_full.json") or {}).get("palaces", [])),
        "五官": len((load("wuguan.json") or {}).get("organs", [])),
        "议题": len((load("themes.json") or {}).get("themes", [])),
        "流派": len((load("schools.json") or {}).get("schools", [])),
        "典籍": len((load("classics.json") or {}).get("items", [])),
        "气色条目": len((load("qise.json") or {}).get("wuse", [])) + len((load("qise.json") or {}).get("bufen", [])),
        "神骨条目": len((load("shengu.json") or {}).get("items", [])),
    }
    if json_out:
        print(json.dumps(ov, ensure_ascii=False, indent=2))
    else:
        _hr("相学文化知识全景")
        for k, v in ov.items():
            print("  %-8s %d" % (k, v))
    return 0


def main():
    ap = argparse.ArgumentParser(description="相学文化知识全集查询")
    ap.add_argument("--palaces-full", action="store_true")
    ap.add_argument("--show-palace")
    ap.add_argument("--themes", action="store_true")
    ap.add_argument("--show-theme")
    ap.add_argument("--schools", action="store_true")
    ap.add_argument("--timeline", action="store_true")
    ap.add_argument("--qise", action="store_true")
    ap.add_argument("--shengu", action="store_true")
    ap.add_argument("--wuguan", action="store_true")
    ap.add_argument("--classics", action="store_true")
    ap.add_argument("--overview", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.palaces_full:
        return cmd_palaces_full()
    if a.show_palace:
        return cmd_show_palace(a.show_palace)
    if a.themes:
        return cmd_themes()
    if a.show_theme:
        return cmd_show_theme(a.show_theme)
    if a.schools:
        return cmd_schools()
    if a.timeline:
        return cmd_timeline()
    if a.qise:
        return cmd_qise()
    if a.shengu:
        return cmd_shengu()
    if a.wuguan:
        return cmd_wuguan()
    if a.classics:
        return cmd_classics()
    if a.overview:
        return cmd_overview(a.json)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
