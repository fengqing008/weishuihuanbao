#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""姓氏基础查询：排名 / 人口 / 源流 / 郡望 / 堂号 / 名人。

用法：
  python3 scripts/surname_query.py --surname 王
  python3 scripts/surname_query.py --surname 王 --format json
  python3 scripts/surname_query.py --list 20

数据来源：assets/surname_rank.json（公安部姓名报告 + 第七次全国人口普查）
          assets/surname_rationale.json（公版姓氏学典籍整理）
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(BASE), "assets")


def load_json(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return json.load(f)


def query(surname):
    rank = load_json("surname_rank.json")
    ratio = load_json("surname_rationale.json")

    entry = None
    for r in rank["ranks"]:
        if r["surname"] == surname:
            entry = r
            break

    detail = ratio["surnames"].get(surname)

    if entry is None and detail is None:
        return None

    result = {
        "surname": surname,
        "rank": entry["rank"] if entry else None,
        "pop_wan": entry["pop_wan"] if entry else None,
        "share": entry["share"] if entry else None,
        "in_top100": entry is not None,
    }
    if detail:
        result.update({
            "pinyin": detail.get("pinyin"),
            "origin_summary": detail.get("origin_summary"),
            "origins": detail.get("origins", []),
            "junwang": detail.get("junwang", []),
            "tanghao": detail.get("tanghao", []),
            "celebrities": detail.get("celebrities", []),
            "migration": detail.get("migration"),
        })
    return result


def render_md(r):
    lines = []
    lines.append("# {}姓溯源".format(r["surname"]))
    lines.append("")
    if r.get("pinyin"):
        lines.append("**拼音**：{}".format(r["pinyin"]))
    if r["rank"]:
        pop = "约{:,}万人".format(r["pop_wan"]) if r.get("pop_wan") else "人口未公布"
        share = "，占全国约{}".format(r["share"]) if r.get("share") else ""
        lines.append("**全国排名**：第{}位，{}{}".format(r["rank"], pop, share))
    else:
        lines.append("**全国排名**：未进入前100大姓")
    lines.append("")

    if r.get("origin_summary"):
        lines.append("## 源流概述")
        lines.append(r["origin_summary"])
        lines.append("")
        lines.append("## 主要源流")
        for o in r.get("origins", []):
            lines.append("- {}".format(o))
        lines.append("")

    if r.get("junwang"):
        lines.append("## 郡望")
        lines.append("、".join(r["junwang"]))
        lines.append("")

    if r.get("tanghao"):
        lines.append("## 堂号")
        for t in r["tanghao"]:
            lines.append("- **{}**：{}".format(t["name"], t["story"]))
        lines.append("")

    if r.get("celebrities"):
        lines.append("## 历史名人")
        for c in r["celebrities"]:
            lines.append("- {}（{}）：{}".format(c["name"], c["era"], c["brief"]))
        lines.append("")

    if r.get("migration"):
        lines.append("## 迁徙与分布")
        lines.append(r["migration"])
        lines.append("")

    lines.append("> 本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="姓氏基础查询")
    ap.add_argument("--surname", help="要查询的姓氏，如 王")
    ap.add_argument("--list", type=int, metavar="N", help="列出前 N 大姓排名")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    args = ap.parse_args()

    if args.list:
        rank = load_json("surname_rank.json")
        rows = rank["ranks"][:args.list]
        if args.format == "json":
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print("全国百家姓 TOP{}（公安部姓名报告排序）".format(args.list))
            print("-" * 46)
            for r in rows:
                pop = "约{:,}万人".format(r["pop_wan"]) if r.get("pop_wan") else ""
                share = r["share"] or ""
                print("{:>3}. {:<4} {} {}".format(r["rank"], r["surname"], pop, share))
        return

    if not args.surname:
        ap.error("请指定 --surname <姓氏> 或 --list <N>")

    r = query(args.surname)
    if r is None:
        print("【暂未收录】'{}' 不在前100大姓数据集与详细源流库中。".format(args.surname), file=sys.stderr)
        print("可作通用说明：该姓之具体源流请以《中国姓氏大辞典》等权威辞书为准。", file=sys.stderr)
        sys.exit(2)

    if args.format == "json":
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(render_md(r))


if __name__ == "__main__":
    main()
