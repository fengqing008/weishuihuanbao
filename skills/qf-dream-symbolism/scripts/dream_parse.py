# -*- coding: utf-8 -*-
"""dream_parse.py — 梦境意象解析（文化解读视角）

从梦境描述中识别传统意象，输出典籍释义、心理象征与文化解读。
用法:
  python3 dream_parse.py --text "我梦见一条大蛇入怀"
  python3 dream_parse.py --file dream.txt --json
  python3 dream_parse.py --list
  python3 dream_parse.py --category 动物
"""
import os
import sys
import json
import argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "assets", "dream_symbols.json")


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def match(text, syms):
    """按触发词最长优先匹配，返回命中的意象列表。"""
    hits = []
    for s in syms["symbols"]:
        kws = sorted([s["name"]] + s["aliases"], key=len, reverse=True)
        for k in kws:
            if k in text:
                hits.append((len(k), s, k))
                break
    hits.sort(key=lambda x: -x[0])
    seen, out = set(), []
    for _, s, k in hits:
        if s["name"] in seen:
            continue
        seen.add(s["name"])
        out.append({"symbol": s, "matched": k})
    return out


def brief(item):
    s = item["symbol"]
    return {
        "name": s["name"],
        "category": s["category"],
        "matched": item["matched"],
        "classics": s["classics"],
        "meaning": s["meaning"],
        "psych": s["psych"],
    }


def main():
    ap = argparse.ArgumentParser(description="梦境意象解析（文化解读视角）")
    ap.add_argument("--text", default="", help="梦境描述文本")
    ap.add_argument("--file", default="", help="梦境描述文件")
    ap.add_argument("--list", action="store_true", help="列出全部意象")
    ap.add_argument("--category", default="", help="按类别列出")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    syms = load()

    if a.list:
        cats = {}
        for s in syms["symbols"]:
            cats.setdefault(s["category"], []).append(s["name"])
        for c, ns in cats.items():
            print("%s（%d）：%s" % (c, len(ns), "、".join(ns)))
        print("\n共 %d 个意象" % syms["count"])
        return

    if a.category:
        rs = [s for s in syms["symbols"] if s["category"] == a.category]
        if not rs:
            print("无此类别：%s" % a.category, file=sys.stderr)
            sys.exit(1)
        for s in rs:
            print("【%s】%s\n  %s\n" % (s["category"], s["name"], s["meaning"]))
        return

    text = a.text
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            text = f.read()
    if not text.strip():
        ap.error("请用 --text 或 --file 提供梦境描述")

    items = match(text, syms)
    if not items:
        print("未识别到传统意象。可尝试更具体的描述（如：蛇、水、飞、牙、考试……）。")
        print("可用意象：", "、".join(s["name"] for s in syms["symbols"][:24]) + " 等")
        return

    if a.json:
        print(json.dumps({"dream": text, "count": len(items),
                          "items": [brief(i) for i in items]},
                         ensure_ascii=False, indent=1))
        return

    print("梦境意象解读（文化视角，共 %d 项）\n" % len(items))
    for it in items:
        b = brief(it)
        print("【%s】%s（识别词：%s）" % (b["category"], b["name"], b["matched"]))
        for c in b["classics"]:
            print("  典籍：" + c)
        print("  传统解读：" + b["meaning"])
        print("  心理象征：" + b["psych"])
        print()
    print("说明：本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")


if __name__ == "__main__":
    main()
