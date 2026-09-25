#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_national.py — 生成全国省份 / 地级市 / 县区 全量基准
==========================================================
数据来源：
  - 行政区划骨架：scripts/data/pca-code.json（省市区三级）
  - 省级收入：国家统计局 2025 年 31 省份居民人均可支配收入（全体口径）
  - 省级人口：2025 年各省常住人口
  - 市级 / 县级：无全国统一收入数据，按「省级收入 × 城市等级系数」代理【估】

规则：
  省 income_ratio = 省居民收入 ÷ 43,377
  市 income_ratio = 省收入 ×（省会/计划单列市 1.15，普通地级市 1.00）÷ 43,377
  县 income_ratio = 市收入 × 0.92 ÷ 43,377
  省 density_ratio = 0.640 × income_ratio^3.096   （用陕西、上海两点标定）【估】
  市/县 density_ratio = 上级密度比 ×（本级收入 ÷ 上级收入）
  coef = √(income_ratio × density_ratio)

已有的陕西省 25 条（含西安 13 区县、实测密度）保留不覆盖。
"""
import json
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
PJ = os.path.join(HERE, "data", "pca-code.json")
BASE = os.path.normpath(os.path.join(HERE, "..", "assets", "baseline.json"))
NAT = 43377.0

PROV_INCOME = {
    "11": 89090, "12": 55918, "13": 36439, "14": 33923, "15": 41921,
    "21": 41703, "22": 32881, "23": 32851, "31": 91987, "32": 57971,
    "33": 70240, "34": 38755, "35": 50302, "36": 37846, "37": 44180,
    "41": 33215, "42": 38881, "43": 39545, "44": 53669, "45": 32721,
    "46": 36306, "50": 41580, "51": 36120, "52": 30001, "53": 31311,
    "54": 33600, "61": 35790, "62": 28224, "63": 31661, "64": 35184,
    "65": 32881,
}
PROV_POP = {
    "11": 2183, "12": 1316, "13": 7378, "14": 3446, "15": 2388,
    "21": 4155, "22": 2317, "23": 3029, "31": 2480, "32": 8518,
    "33": 6701, "34": 6082, "35": 4190, "36": 4502, "37": 10043,
    "41": 9785, "42": 5811, "43": 6492, "44": 12859, "45": 4989,
    "46": 1055, "50": 3190, "51": 8318, "52": 3857, "53": 4655,
    "54": 370, "61": 3953, "62": 2458, "63": 592, "64": 732,
    "65": 2639,
}
CAPITALS = {
    "1301", "1401", "1501", "2101", "2102", "2201", "2301", "3201",
    "3301", "3302", "3401", "3501", "3502", "3601", "3701", "3702",
    "4101", "4201", "4301", "4401", "4403", "4501", "4601", "5101",
    "5201", "5301", "5401", "6101", "6201", "6301", "6401", "6501",
}
VIRTUAL = {"市辖区", "县", "省直辖县级行政区划", "自治区直辖县级行政区划", "直辖县级行政区划"}


def dr_prov(ir):
    return max(0.05, min(8.0, 0.640 * (ir ** 3.096)))


def main():
    pca = json.load(open(PJ, encoding="utf-8"))
    bl = json.load(open(BASE, encoding="utf-8"))
    regions = dict(bl["regions"])
    before = len(regions)
    added = {"省": 0, "市": 0, "县区": 0}

    for p in pca:
        p2 = p["code"].zfill(2)
        pcode = p2 + "0000"
        pinc = PROV_INCOME.get(p2)
        if pinc is None:
            continue
        pir = round(pinc / NAT, 3)
        pdr = round(dr_prov(pir), 3)
        ppop = PROV_POP.get(p2, 0)

        if pcode not in regions:
            regions[pcode] = {
                "name": p["name"], "level": "省",
                "households": int(ppop * 10000 / 2.62),
                "income_ratio": pir, "density_ratio": pdr,
                "coef": round(math.sqrt(pir * pdr), 3), "urban_income": pinc,
                "source": f"省居民人均可支配收入 {pinc:,} 元（国家统计局 2025）；密度按收入幂律代理【估】",
            }
            added["省"] += 1

        # 统计有效市级数（用于人口分摊）
        valid_cities = [c for c in p["children"] if c["name"] not in VIRTUAL]
        nc = max(1, len(valid_cities))
        prov_hh = ppop * 10000 / 2.62

        for c in p["children"]:
            cname = c["name"]
            c4 = c["code"].zfill(4)
            if cname in VIRTUAL:
                nx = max(1, len(c["children"]))
                xinc = pinc * 0.95
                xir = round(xinc / NAT, 3)
                xdr = round(pdr * 0.95, 3)
                for x in c["children"]:
                    xc = x["code"]
                    if xc in regions:
                        continue
                    regions[xc] = {
                        "name": x["name"], "level": "县区",
                        "households": int(prov_hh / nc / nx),
                        "income_ratio": xir, "density_ratio": xdr,
                        "coef": round(math.sqrt(xir * xdr), 3), "urban_income": int(xinc),
                        "source": "收入按省级×0.95 代理【估】；户数按省人口分摊【估】",
                    }
                    added["县区"] += 1
                continue

            ccode = c4 + "00"
            cinc = pinc * (1.15 if c4 in CAPITALS else 1.0)
            cir = round(cinc / NAT, 3)
            cdr = round(pdr * (cir / pir), 3)
            city_hh = int(prov_hh / nc)
            if ccode not in regions:
                regions[ccode] = {
                    "name": cname, "level": "市",
                    "households": city_hh,
                    "income_ratio": cir, "density_ratio": cdr,
                    "coef": round(math.sqrt(cir * cdr), 3), "urban_income": int(cinc),
                    "source": ("省会/计划单列市" if c4 in CAPITALS else "地级市")
                              + "代理：省级收入×"
                              + ("1.15" if c4 in CAPITALS else "1.00") + "【估】",
                }
                added["市"] += 1

            nx = max(1, len(c["children"]))
            xinc = cinc * 0.92
            xir = round(xinc / NAT, 3)
            xdr = round(cdr * 0.92, 3)
            for x in c["children"]:
                xc = x["code"]
                if xc in regions:
                    continue
                regions[xc] = {
                    "name": x["name"], "level": "县区",
                    "households": int(city_hh / nx),
                    "income_ratio": xir, "density_ratio": xdr,
                    "coef": round(math.sqrt(xir * xdr), 3), "urban_income": int(xinc),
                    "source": "收入按所属市×0.92 代理【估】；户数按市人口分摊【估】",
                }
                added["县区"] += 1

    bl["regions"] = regions
    bl["_comment"] = (bl.get("_comment", "").split("｜")[0] +
                      f"｜v2.0 全国全量：{len(regions)} 个地区（省级31 + 地级市 + 县区）")
    with open(BASE, "w", encoding="utf-8") as f:
        json.dump(bl, f, ensure_ascii=False, indent=1)

    print(f"完成：{before} → {len(regions)} 条（新增 省{added['省']} 市{added['市']} 县区{added['县区']}）")
    print("写入：", BASE)


if __name__ == "__main__":
    main()
