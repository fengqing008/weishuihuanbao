#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
env_tax_calc.py — 环境保护税（水污染物）测算器（纯标准库）

依据《中华人民共和国环境保护税法》及其实施条例：
  - 应税水污染物按污染当量数从大到小排序，只对前三项计征；
  - 污染当量数 = 污染物排放量(kg) ÷ 污染当量值(kg)；
  - 应纳税额 = Σ(污染当量数) × 单位税额(元/污染当量)；
  - 城乡污水集中处理场所达标排放相应应税污染物，免征；
  - 其他排污单位浓度值低于排放标准 30% 减按 75% 征收，低于 50% 减按 50% 征收；
  - 超标排放全额计征，不适用减免。

两种输入方式（二选一）：
  A. 直接给排放量（kg）：--cod 1200 --nh3n 180 ...
  B. 给废水排放量(m³)与浓度(mg/L)：--volume 900000 --conc "COD=18,氨氮=0.9"

用法示例：
    python3 env_tax_calc.py --plant 城区厂 --period 2026Q2 --tax-rate 1.4 \
        --cod 1200 --nh3n 180 --tp 25 --tn 260 --std 一级A
    python3 env_tax_calc.py --plant 城区厂 --period 2026Q2 --tax-rate 1.4 \
        --volume 900000 --conc "COD=18,氨氮=0.9,总磷=0.3,总氮=8" --std 一级A --json
    python3 env_tax_calc.py --plant 医药园厂 --tax-rate 1.4 --type 工业废水集中处理 \
        --volume 60000 --conc "COD=45,氨氮=4,总氮=12" --std 一级A

退出码：0 正常；1 输入错误（未识别污染物 / 参数缺失）。
"""
import argparse
import json
import sys

# 水污染物污染当量值（kg），取自《环境保护税法》附表二（节选）
EQUIV = {
    "COD": 1, "化学需氧量": 1,
    "BOD5": 0.5, "生化需氧量": 0.5,
    "SS": 4, "悬浮物": 4,
    "氨氮": 0.8,
    "总磷": 0.25,
    "总氮": 0.8,
    "石油类": 0.1,
    "动植物油": 0.16,
    "挥发酚": 0.08,
    "硫化物": 0.125,
    "氟化物": 0.5,
    "甲醛": 0.25,
    "总汞": 0.0005,
    "总镉": 0.005,
    "总铬": 0.04,
    "六价铬": 0.02,
    "总砷": 0.02,
    "总铅": 0.025,
}
# 排放标准限值（mg/L），用于达标判断与减免判定
STD_LIMITS = {
    "一级A": {"COD": 50, "BOD5": 10, "SS": 10, "氨氮": 5, "总磷": 0.5, "总氮": 15},
    "一级B": {"COD": 60, "BOD5": 20, "SS": 20, "氨氮": 8, "总磷": 1, "总氮": 20},
}
ARG_MAP = {"cod": "COD", "bod5": "BOD5", "ss": "SS", "nh3n": "氨氮",
           "tp": "总磷", "tn": "总氮", "petroleum": "石油类"}


def build_amounts(args):
    """返回 ({污染物: 排放量kg}, 是否由体积×浓度推算)。"""
    amounts = {}
    if args.conc and args.volume:
        for pair in args.conc.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if "=" not in pair:
                raise ValueError("--conc 格式应为 名称=浓度(mg/L)，收到：%s" % pair)
            name, val = pair.split("=", 1)
            name = name.strip()
            if name not in EQUIV:
                raise ValueError("未识别的污染物：%s（当量值表无此项，请核对名称）" % name)
            try:
                conc = float(val)
            except ValueError:
                raise ValueError("浓度非数值：%s=%s" % (name, val))
            amounts[name] = args.volume * conc / 1000.0  # m³ × mg/L → kg
        return amounts, True
    for attr, name in ARG_MAP.items():
        v = getattr(args, attr)
        if v is not None:
            amounts[name] = float(v)
    if not amounts:
        raise ValueError("须提供排放量（--cod 等）或 体积+浓度（--volume 与 --conc）")
    return amounts, False


def evaluate(amounts, concs, std, tax_rate, tax_type):
    """计算当量数、按前三项计征的应纳税额，并给出免征/减免判定。"""
    items = []
    for name, kg in amounts.items():
        items.append({"污染物": name, "排放量kg": round(kg, 3),
                      "当量值kg": EQUIV[name], "污染当量数": round(kg / EQUIV[name], 3)})
    items.sort(key=lambda x: x["污染当量数"], reverse=True)
    taxable = items[:3]  # 只对当量数前三项计征

    std_limits = STD_LIMITS.get(std, {})
    have_conc = any(v is not None for v in concs.values())
    over_item, worst_ratio = None, 0.0
    for it in items:
        lim = std_limits.get(it["污染物"])
        c = concs.get(it["污染物"])
        if lim is None or c is None:
            continue
        if c > lim:
            over_item = (it["污染物"], c, lim)
        worst_ratio = max(worst_ratio, c / lim)

    discount, exempt, note = 1.0, False, ""
    if not have_conc:
        note = "缺浓度数据，无法判定达标与减免，按全额计征保守估算"
    elif over_item:
        note = "%s 浓度 %s 超过 %s 限值 %s，超标排放，全额计征且不适用减免" % (
            over_item[0], over_item[1], std, over_item[2])
    elif tax_type == "城乡污水集中处理":
        exempt = True
        note = "各项浓度均不超 %s 限值，属城乡污水集中处理场所达标排放，相应应税污染物免征环保税" % std
    else:
        if worst_ratio <= 0.5:
            discount = 0.5
            note = "达标且浓度低于标准 50% 以上，减按 50% 征收"
        elif worst_ratio <= 0.7:
            discount = 0.75
            note = "达标且浓度低于标准 30% 以上，减按 75% 征收"
        else:
            note = "达标但无减免条件，全额计征"

    units = sum(it["污染当量数"] for it in taxable)
    raw = units * tax_rate
    payable = 0.0 if exempt else round(raw * discount, 2)
    return {
        "明细": items,
        "计征项": [it["污染物"] for it in taxable],
        "合计污染当量数": round(units, 3),
        "单位税额": tax_rate,
        "未减免税额": round(raw, 2),
        "减免比例": discount,
        "应纳（缴）税额": payable,
        "免税": exempt,
        "判定说明": note,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="环境保护税（水污染物）测算器")
    ap.add_argument("--plant", required=True, help="厂名/纳税主体")
    ap.add_argument("--period", help="所属期，如 2026Q2")
    ap.add_argument("--tax-rate", type=float, required=True, dest="tax_rate",
                    help="单位税额 元/污染当量（由省级确定）")
    ap.add_argument("--std", default="一级A", choices=list(STD_LIMITS), help="排放标准档")
    ap.add_argument("--type", dest="tax_type", default="城乡污水集中处理",
                    choices=["城乡污水集中处理", "工业废水集中处理"], help="场所类型")
    ap.add_argument("--volume", type=float, help="废水排放量 m³（配合 --conc）")
    ap.add_argument("--conc", help='浓度串，如 "COD=18,氨氮=0.9,总磷=0.3"（mg/L）')
    ap.add_argument("--cod", type=float, help="COD 排放量 kg")
    ap.add_argument("--bod5", type=float, help="BOD5 排放量 kg")
    ap.add_argument("--ss", type=float, help="SS 排放量 kg")
    ap.add_argument("--nh3n", type=float, help="氨氮 排放量 kg")
    ap.add_argument("--tp", type=float, help="总磷 排放量 kg")
    ap.add_argument("--tn", type=float, help="总氮 排放量 kg")
    ap.add_argument("--petroleum", type=float, help="石油类 排放量 kg")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args(argv)

    try:
        amounts, from_conc = build_amounts(args)
    except ValueError as e:
        print("[ERROR] %s" % e, file=sys.stderr)
        return 1

    concs = {}
    if from_conc:
        for pair in args.conc.split(","):
            n, v = pair.split("=", 1)
            concs[n.strip()] = float(v)
    else:
        for name in amounts:
            if name in STD_LIMITS.get(args.std, {}):
                concs[name] = None  # 直接给量时无浓度，不做减免判定

    res = evaluate(amounts, concs, args.std, args.tax_rate, args.tax_type)
    res["厂名"] = args.plant
    res["所属期"] = args.period or ""
    res["场所类型"] = args.tax_type

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    print("环境保护税测算｜%s｜%s｜%s" % (args.plant, args.period or "", args.tax_type))
    print("-" * 60)
    for it in res["明细"]:
        mark = "★计征" if it["污染物"] in res["计征项"] else "  排序外"
        print("  %-8s 排放 %10.3f kg | 当量值 %-7s | 当量数 %10.3f | %s"
              % (it["污染物"], it["排放量kg"], it["当量值kg"], it["污染当量数"], mark))
    print("-" * 60)
    print("  合计污染当量数：%.3f" % res["合计污染当量数"])
    print("  未减免税额：    %.2f 元（单位税额 %.4f 元/当量）" % (res["未减免税额"], res["单位税额"]))
    print("  减免比例：      %s" % res["减免比例"])
    print("  应纳（缴）税额：%.2f 元" % res["应纳（缴）税额"])
    print("  判定：%s" % res["判定说明"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
