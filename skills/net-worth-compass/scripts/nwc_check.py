#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""身价罗盘资产清单校验器（nwc_check.py）。

仅使用 Python 标准库（argparse / json / sys），不依赖第三方包、不联网。
对净资产归集输入（资产/负债清单 JSON）做规则校验，防住"危险假输出"：

  1. 结构与必需字段：assets 非空、每项含 name 与数值型 value；
  2. 数值合法性：金额为数值且非负，拒绝 NaN / Infinity 等异常值；
  3. 口径提示：region_code 位数、owner / scope 是否声明；
  4. 归集复核：区分公积金与存款类条目，提示重复计入风险；
  5. 汇总：总资产、总负债、净资产。

退出码：
  0 —— 全部校验通过；
  1 —— 校验不通过（存在非法条目 / 负数 / 疑似重复计入等硬性告警）；
  2 —— 输入不足或参数非法（文件缺失、JSON 不可解析、assets 为空、缺 name/value）。

用法：
  python3 nwc_check.py --input assets.json --json
  python3 nwc_check.py --input assets.json --expect-region 610115
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

GROUP_HINTS = {
    "房产": ("房", "住宅", "商铺", "车位", "写字楼", "别墅", "公寓"),
    "车辆": ("车", "汽车", "摩托车"),
    "现金存款": ("存款", "储蓄", "活期", "定期", "余额", "零钱", "现金", "支付宝", "微信"),
    "理财投资": ("理财", "基金", "股票", "债券", "保险", "黄金", "信托"),
    "公积金": ("公积金",),
    "股权出资": ("股权", "出资", "股份"),
    "应收借出": ("借出", "应收", "欠款"),
}


def _num(x, field):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError("字段 %s 不是数值：%r" % (field, x))
    v = float(x)
    if math.isnan(v) or math.isinf(v):
        raise ValueError("字段 %s 为 NaN / Infinity 异常值" % field)
    return v


def classify(name: str) -> str:
    for grp, hints in GROUP_HINTS.items():
        for h in hints:
            if h in name:
                return grp
    return "其他资产"


def check(args: argparse.Namespace) -> dict:
    path = args.input
    if not path or not os.path.isfile(path):
        raise ValueError("输入文件不存在：%r" % path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("JSON 不可解析：%s" % exc) from exc

    if not isinstance(data, dict):
        raise ValueError("顶层结构须为对象（含 assets / liabilities）")
    assets = data.get("assets")
    if not assets:
        raise ValueError("assets 为空或缺省，无法估值（拒绝输出空结果）")
    if not isinstance(assets, list):
        raise ValueError("assets 须为数组")

    problems, notes = [], []
    owner = data.get("owner")
    scope = data.get("scope")
    region = data.get("region_code")

    if not owner:
        notes.append("未声明 owner（资产归属人），报告口径可能含糊")
    if not scope:
        notes.append("未声明 scope（个人 / 家庭），分位分母口径不明")
    if region:
        if not re.fullmatch(r"\d{6}", str(region)):
            problems.append("region_code=%r 不是 6 位行政区划代码" % region)
        elif args.expect_region and str(region) != str(args.expect_region):
            notes.append("region_code=%s 与期望值 %s 不一致" % (region, args.expect_region))
    else:
        notes.append("未提供 region_code，将只能出全国口径")

    total = 0.0
    groups = {}
    for i, item in enumerate(assets, 1):
        if not isinstance(item, dict):
            problems.append("第 %d 项不是对象" % i)
            continue
        name = (item.get("name") or "").strip()
        if not name:
            raise ValueError("第 %d 项缺 name（拒绝按 0 计算，避免假输出）" % i)
        v = _num(item.get("value"), "assets[%d].value" % i)
        if v < 0:
            problems.append("第 %d 项 %s 金额为负（%.2f）" % (i, name, v))
        total += v
        groups.setdefault(classify(name), []).append(name)

    if "公积金" in groups and "现金存款" in groups:
        notes.append("同时存在「公积金」与「现金存款」条目，请复核是否重复计入同一账户")

    liabilities = data.get("liabilities") or []
    if not isinstance(liabilities, list):
        problems.append("liabilities 须为数组")
        liabilities = []
    else:
        if not liabilities:
            notes.append("未提供负债条目，请主动确认房贷 / 车贷 / 消费贷 / 信用卡")

    liab_total = 0.0
    for i, item in enumerate(liabilities, 1):
        if not isinstance(item, dict):
            problems.append("负债第 %d 项不是对象" % i)
            continue
        name = (item.get("name") or "").strip() or "未命名负债"
        v = _num(item.get("value"), "liabilities[%d].value" % i)
        if v < 0:
            problems.append("负债第 %d 项 %s 金额为负（%.2f）" % (i, name, v))
        liab_total += v

    return {
        "owner": owner,
        "scope": scope,
        "region_code": region,
        "asset_count": len(assets),
        "liability_count": len(liabilities),
        "total_assets": round(total, 2),
        "total_liabilities": round(liab_total, 2),
        "net_worth": round(total - liab_total, 2),
        "groups": {k: len(v) for k, v in groups.items()},
        "problems": problems,
        "notes": notes,
        "result": "PASS" if not problems else "FAIL",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="身价罗盘资产清单校验器（标准库实现）")
    parser.add_argument("--input", help="资产清单 JSON 路径")
    parser.add_argument("--expect-region", dest="expect_region", help="期望的 6 位行政区划代码（可选）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args(argv)

    try:
        res = check(args)
    except ValueError as exc:
        print("[输入不足] %s" % exc)
        print("提示：补齐 assets（含 name 与数值 value）后重跑；分位数值未核实的请标【待核】。")
        return 2

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("总资产：%.2f 元（%d 项）" % (res["total_assets"], res["asset_count"]))
        print("总负债：%.2f 元（%d 项）" % (res["total_liabilities"], res["liability_count"]))
        print("净资产：%.2f 元" % res["net_worth"])
        for p in res["problems"]:
            print("  [告警] %s" % p)
        for n in res["notes"]:
            print("  [提示] %s" % n)
        print("结论：%s" % res["result"])
    return 0 if res["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
