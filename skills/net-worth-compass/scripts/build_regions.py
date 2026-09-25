#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身价罗盘 · 地区基准批量导入器
================================
把一份 CSV（行政区划代码, 名称, 常住人口万人, 城镇居民人均可支配收入）批量折算为
baseline.json 的 regions 记录，自动计算 收入比 / 密度比 / coef / 家庭户数。

用法：
  python3 build_regions.py --csv regions.csv --dry          # 预览
  python3 build_regions.py --csv regions.csv --merge        # 合并写入正式基准库
  python3 build_regions.py --csv regions.csv --out x.json   # 独立输出

CSV 列（表头须含 code,name,population_wan,urban_income；可选 household_600w）：
  code,name,population_wan,urban_income,household_600w
  610115,某市区,68.67,41387,
  610800,榆林市,360.13,47143,10802

规则：
  - level 由代码自动判定（末4位0000=省；末2位00=市；否则县区）
  - 家庭户数 = 常住人口 ÷ 2.62
  - 收入比 = 城镇居民收入 ÷ 56,502
  - 密度比 = 600万家庭密度 ÷ 1.024%（给 household_600w 用真值；否则按上级折算，标【估】）
  - coef = √(收入比 × 密度比)
"""
import csv
import json
import math
import os
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(BASE_DIR, "assets", "baseline.json")
NAT_URBAN_INCOME = 56502.0
NAT_DENSITY = 0.01024


def level_of(code):
    if code.endswith("0000"):
        return "省"
    if code.endswith("00"):
        return "市"
    return "县区"


def parent_of(code):
    lv = level_of(code)
    if lv == "市":
        return code[:2] + "0000"
    if lv == "县区":
        return code[:4] + "00"
    return None


def main():
    ap = argparse.ArgumentParser(description="身价罗盘 · 地区基准批量导入器")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default=BASELINE)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    with open(BASELINE, "r", encoding="utf-8") as f:
        bl = json.load(f)
    existing = bl["regions"]

    rows = []
    with open(args.csv, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if str(r.get("code", "")).strip():
                rows.append(r)

    newreg = {}
    missing = []
    for r in rows:
        code = str(r["code"]).strip()
        name = r["name"].strip()
        lv = level_of(code)
        pop = float(r["population_wan"])
        inc = float(r["urban_income"])
        households = int(round(pop * 10000 / 2.62))
        income_ratio = round(inc / NAT_URBAN_INCOME, 3)

        h600 = str(r.get("household_600w") or "").strip()
        if h600:
            density_ratio = round((float(h600) / households) / NAT_DENSITY, 3)
            src = f"600万家庭 {int(float(h600)):,} 户；城镇收入 {inc:,.0f} 元"
        else:
            par = parent_of(code)
            base = None
            if par and par in existing:
                base = existing[par]["density_ratio"]
            elif par and par in newreg:
                base = newreg[par]["density_ratio"]
            if base is None:
                missing.append(code)
                base = 0.25
            density_ratio = round(base * income_ratio, 3)
            src = f"密度按上级折算【估】；城镇收入 {inc:,.0f} 元"

        coef = round(math.sqrt(income_ratio * density_ratio), 3)
        newreg[code] = {
            "name": name, "level": lv, "households": households,
            "income_ratio": income_ratio, "density_ratio": density_ratio,
            "coef": coef, "urban_income": int(inc), "source": src,
        }

    print(f"解析 {len(newreg)} 条；{'合并入现有 ' + str(len(existing)) if args.merge else '独立输出'}")
    if missing:
        print(f"⚠ {len(missing)} 条未找到上级密度基准，按 0.25 兜底")
    for c in list(newreg)[:8]:
        v = newreg[c]
        print(f"  {c} {v['name']} [{v['level']}] coef={v['coef']} "
              f"(收入比{v['income_ratio']} × 密度比{v['density_ratio']})")
    if len(newreg) > 8:
        print(f"  ... 共 {len(newreg)} 条")

    if args.dry:
        print("[dry-run] 未写盘")
        return

    if args.merge:
        existing.update(newreg)
        bl["regions"] = existing
        out = args.out
    else:
        out = args.out if args.out != BASELINE else "myregions.json"
        bl = {"regions": newreg}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(bl, f, ensure_ascii=False, indent=2)
    print(f"已写入：{out}")


if __name__ == "__main__":
    main()
