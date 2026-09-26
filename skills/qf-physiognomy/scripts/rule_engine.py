#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rule_engine.py —— 特征 → 相学条文匹配（相学文化技能）

把 features JSON 中的形态描述词，匹配到 assets/rules.json 中的相学论述，
输出结构化 result.json，供 report_render.py 生成报告。

用法：
  python3 scripts/rule_engine.py --features f.json
  python3 scripts/rule_engine.py --features f.json --out result.json
  python3 scripts/rule_engine.py --list-palaces          # 列十二宫
  python3 scripts/rule_engine.py --list-rules            # 列规则条目
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

PART_ORDER = ["face_shape", "forehead", "brow", "eye", "nose", "mouth", "ear", "chin"]
PART_CN = {"face_shape": "脸型", "forehead": "额部", "brow": "眉部", "eye": "眼部",
           "nose": "鼻部", "mouth": "口部", "ear": "耳部", "chin": "颏部"}

DISCLAIMER = ("本报告为中国传统相学文化的知识介绍与形态描述整理，不构成任何判断、"
              "预测或决策依据。面部形态识别存在误差，结果仅供文化了解。")


def load(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return json.load(f)


def match_part(part, value, rules):
    """在指定部位下匹配特征词，返回条文 dict 或 None。"""
    node = rules.get(part)
    if not node:
        return None
    item = node["items"].get(value)
    if not item:
        return None
    return {
        "feature": value,
        "desc": item.get("desc", ""),
        "palace": item.get("palace", ""),
        "classic": item.get("classic", ""),
        "reading": item.get("reading", ""),
        "source": item.get("source", ""),
    }


def build(features, rules, palace12, classics):
    parts = []

    # 脸型
    fs = features.get("face_shape")
    fs_val = fs.get("value") if isinstance(fs, dict) else (fs or "")
    if fs_val:
        m = match_part("face_shape", fs_val, rules)
        if m:
            node = rules["face_shape"]
            parts.append({"part": "face_shape", "part_cn": PART_CN["face_shape"],
                          "intro": node["intro"], "matched": [m]})

    # 三停（单独一节，不属五官）
    santing = features.get("santing") or {}

    # 其余部位按固定顺序
    skipped = []
    for part in PART_ORDER:
        if part == "face_shape":
            continue
        raw = features.get("features", {}).get(part)
        if raw is None:
            continue
        val = raw.get("value") if isinstance(raw, dict) else (raw or "")
        if not val:
            continue
        m = match_part(part, val, rules)
        if m:
            node = rules[part]
            parts.append({"part": part, "part_cn": PART_CN[part],
                          "intro": node["intro"], "matched": [m]})
        else:
            skipped.append("%s「%s」" % (PART_CN[part], val))

    result = {
        "source_image": features.get("source_image", ""),
        "filled_by": features.get("filled_by", "manual"),
        "face_shape": fs_val,
        "santing": santing,
        "parts": parts,
        "palace12": palace12,
        "classics": classics,
        "skipped": skipped,
        "warnings": features.get("warnings", []),
        "disclaimer": DISCLAIMER,
    }
    return result


def cmd_list_palaces():
    p = load("palace12.json")
    print(p["说明"])
    for x in p["palaces"]:
        print("  %-6s %-16s %s" % (x["name"], x["pos"], x["desc"]))
    return 0


def cmd_list_rules():
    r = load("rules.json")
    total = 0
    for k, v in r.items():
        print("【%s】%s" % (v["label"], v["intro"]))
        for name, it in v["items"].items():
            total += 1
            print("    %-10s %-8s %s" % (name, it.get("palace", ""), it.get("desc", "")))
    print("\n条目合计：%d" % total)
    return 0


def main():
    ap = argparse.ArgumentParser(description="特征到相学条文的匹配（相学文化）")
    ap.add_argument("--features", help="特征 JSON（face_analyze.py 输出）")
    ap.add_argument("--out", help="输出 result.json 路径")
    ap.add_argument("--list-palaces", action="store_true")
    ap.add_argument("--list-rules", action="store_true")
    a = ap.parse_args()

    if a.list_palaces:
        return cmd_list_palaces()
    if a.list_rules:
        return cmd_list_rules()
    if not a.features:
        ap.print_help()
        return 2

    with open(a.features, encoding="utf-8") as f:
        features = json.load(f)
    rules = load("rules.json")
    palace12 = load("palace12.json")
    classics = load("classics.json")

    res = build(features, rules, palace12, classics)
    txt = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(txt + "\n")
        print("[OK] 匹配完成，命中部位 %d 处，写入 %s" % (len(res["parts"]), a.out))
    else:
        print(txt)
    if res["skipped"]:
        print("[WARN] 未匹配到条文的特征：%s" % "、".join(res["skipped"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
