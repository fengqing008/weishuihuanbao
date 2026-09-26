#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三级人口测算：全国 / 省级 / 地区级。

用法：
  python3 scripts/pop_calc.py --surname 王
  python3 scripts/pop_calc.py --surname 王 --province 陕西
  python3 scripts/pop_calc.py --surname 王 --province 陕西 --city 西安

口径说明：
  全国：公安部姓名报告 + 第七次全国人口普查（官方约数）
  省级：若该姓为本省第一大姓（官方），直接标注；否则按「全国占比 × 省常住人口」估算并标注【估算值】
  地区级：需配合 place_scan.py 以姓氏地名密度侧面反映，不在本脚本内断言人口
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(BASE), "assets")

# 2020年第七次全国人口普查·各省(区、市)常住人口（万人，约数）
PROVINCE_POP = {
    "广东": 12601, "山东": 10153, "河南": 9937, "江苏": 8475, "四川": 8367,
    "河北": 7461, "湖南": 6644, "浙江": 6457, "安徽": 6103, "湖北": 5775,
    "广西": 5013, "云南": 4721, "江西": 4519, "辽宁": 4259, "福建": 4154,
    "陕西": 3953, "贵州": 3856, "山西": 3492, "重庆": 3205, "黑龙江": 3185,
    "新疆": 2585, "甘肃": 2502, "上海": 2487, "吉林": 2407, "内蒙古": 2400,
    "北京": 2189, "天津": 1387, "海南": 1008, "宁夏": 720, "青海": 592,
    "西藏": 365,
}


def load(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return json.load(f)


def calc(surname, province=None):
    rank = load("surname_rank.json")
    prov = load("province_first.json")

    entry = next((r for r in rank["ranks"] if r["surname"] == surname), None)
    if entry is None:
        print("【暂未收录】'{}' 不在前100大姓数据集。".format(surname), file=sys.stderr)
        sys.exit(2)

    result = {
        "surname": surname,
        "national": {
            "rank": entry["rank"],
            "pop_wan": entry.get("pop_wan"),
            "share": entry.get("share"),
            "source": rank["meta"]["rank_source"],
        },
        "province": None,
        "note": [],
    }

    # 全国占比数值（用于省级估算）
    share_val = None
    if entry.get("share"):
        try:
            share_val = float(entry["share"].rstrip("%")) / 100.0
        except ValueError:
            share_val = None
    if share_val is None and entry.get("pop_wan"):
        # 以约14.1亿户籍人口反推
        share_val = entry["pop_wan"] / 141000.0

    if province:
        first_map = prov["province_to_surname"]
        is_first = first_map.get(province) == surname
        p_pop = PROVINCE_POP.get(province)
        if p_pop is None:
            result["note"].append("省份 '{}' 未收录常住人口，无法估算。".format(province))
        else:
            if is_first:
                result["province"] = {
                    "name": province,
                    "is_first_surname": True,
                    "province_pop_wan": p_pop,
                    "note": "官方：{}为{}第一大姓（来源：公安部《二〇一九年全国姓名报告》）。".format(surname, province),
                }
            else:
                est = round(p_pop * (share_val or 0), 1)
                result["province"] = {
                    "name": province,
                    "is_first_surname": False,
                    "province_pop_wan": p_pop,
                    "est_pop_wan": est,
                    "note": "【估算值】按全国占比×省常住人口估算，非官方统计，仅供参考。",
                }
                result["note"].append("省级为该姓非本省第一大姓，采用估算口径。")
    else:
        result["note"].append("未指定 --province，仅给出全国口径。")

    return result


def render_md(r):
    L = ["# {}姓人口分布（全国·省级）".format(r["surname"]), ""]
    n = r["national"]
    pop = "约{:,}万人".format(n["pop_wan"]) if n.get("pop_wan") else "未公布"
    L.append("## 全国")
    L.append("- 排名：第{}位".format(n["rank"]))
    L.append("- 人口：{}".format(pop))
    if n.get("share"):
        L.append("- 占比：全国约{}".format(n["share"]))
    L.append("- 来源：{}".format(n["source"]))
    L.append("")
    if r["province"]:
        p = r["province"]
        L.append("## 省级（{}）".format(p["name"]))
        L.append("- 省常住人口：约{:,}万人".format(p["province_pop_wan"]))
        if p.get("is_first_surname"):
            L.append("- 结论：{}为{}**第一大姓**（官方）".format(r["surname"], p["name"]))
        else:
            L.append("- 估算人口：约{:,}万人".format(p.get("est_pop_wan", 0)))
        L.append("- 说明：{}".format(p["note"]))
        L.append("")
    if r["note"]:
        L.append("## 口径说明")
        for x in r["note"]:
            L.append("- {}".format(x))
        L.append("")
    L.append("> 本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="姓氏三级人口测算")
    ap.add_argument("--surname", required=True, help="姓氏，如 王")
    ap.add_argument("--province", help="省份，如 陕西")
    ap.add_argument("--city", help="城市（地区级请配合 place_scan.py）")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    args = ap.parse_args()

    r = calc(args.surname, args.province)
    if args.city:
        r["note"].append("地区级（{}）：请运行 place_scan.py 以姓氏地名密度侧面反映，不作人口断言。".format(args.city))
    if args.format == "json":
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(render_md(r))


if __name__ == "__main__":
    main()
