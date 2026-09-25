#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deadline_calc.py — 应诉时限计算器（纯标准库）

按送达日推算应诉各节点期限：答辩期、管辖权异议截止日、举证期限、上诉期、
财产保全复议期、执行异议期、建设工程价款优先受偿权行使期。

期间计算规则（《中华人民共和国民事诉讼法》第八十五条）：
  期间开始的时与日不计入期间，自次日起算；
  期间届满的最后一日是法定休假日的，以法定休假日结束的次日为届满日。

用法示例：
  python3 deadline_calc.py --deliver 2026-02-15 --type first-instance
  python3 deadline_calc.py --deliver 2026-02-15 --type first-instance --json
  python3 deadline_calc.py --deliver 2026-02-15 --type evidence-period --mode simplified
  python3 deadline_calc.py --deliver 2026-02-15 --type appeal-judgment --holidays 2026-04-04,2026-04-05,2026-04-06
  python3 deadline_calc.py --list

退出码：0 = 正常；2 = 参数错误（日期非法 / 类型未知）。
"""
import argparse
import json
import sys
from datetime import date, timedelta

# 期限类型 → (标签, 天数单位, 天数, 法律依据)
DEADLINE_TYPES = {
    "first-instance":     ("答辩期（一审）", "day", 15, "《中华人民共和国民事诉讼法》第一百二十八条"),
    "jurisdiction":       ("管辖权异议（提交答辩状期间）", "day", 15, "《中华人民共和国民事诉讼法》第一百三十条第一款"),
    "evidence-period":    ("举证期限（一审普通程序，不少于 15 日）", "day", 15, "《最高人民法院关于民事诉讼证据的若干规定》第五十一条"),
    "evidence-simple":    ("举证期限（简易程序，不超过 15 日）", "day", 15, "《最高人民法院关于民事诉讼证据的若干规定》第五十一条"),
    "appeal-judgment":    ("上诉期（不服判决）", "day", 15, "《中华人民共和国民事诉讼法》第一百七十一条"),
    "appeal-order":       ("上诉期（不服裁定）", "day", 10, "《中华人民共和国民事诉讼法》第一百七十一条"),
    "preservation-reconsider": ("财产保全复议期（一次）", "day", 5, "《中华人民共和国民事诉讼法》第一百一十一条"),
    "priority-18m":       ("建设工程价款优先受偿权行使期（最长）", "month", 18, "《最高人民法院关于审理建设工程施工合同纠纷案件适用法律问题的解释（一）》第四十一条"),
    "limitation-3y":      ("诉讼时效期间", "year", 3, "《中华人民共和国民法典》第一百八十八条"),
}


def parse_date(s: str) -> date:
    """解析 YYYY-MM-DD 或 YYYY/MM/DD。非法即抛 ValueError。"""
    t = s.strip().replace("/", "-").replace(".", "-")
    parts = t.split("-")
    if len(parts) != 3:
        raise ValueError(f"日期格式非法：{s}")
    y, m, d = (int(x) for x in parts)
    return date(y, m, d)


def parse_holidays(s: str):
    """解析逗号分隔的法定休假日列表。"""
    if not s:
        return set()
    out = set()
    for x in s.split(","):
        x = x.strip()
        if x:
            out.add(parse_date(x))
    return out


def add_months(d: date, n: int) -> date:
    """加 n 个月，日不存在时取当月最后一日。"""
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    day = d.day
    while day > 28:
        try:
            return date(y, m, day)
        except ValueError:
            day -= 1
    return date(y, m, day)


def next_workday(d: date, holidays) -> date:
    """若落在法定休假日或周末，顺延至次一工作日。"""
    while d.weekday() >= 5 or d in holidays:
        d += timedelta(days=1)
    return d


def compute(deliver: date, dtype: str, holidays=None, count_weekends: bool = False) -> dict:
    """核心计算：送达日次日起算，返回截止日与自然日剩余数。"""
    holidays = holidays or set()
    if dtype not in DEADLINE_TYPES:
        raise ValueError(f"未知期限类型：{dtype}（可用类型见 --list）")
    label, unit, n, law = DEADLINE_TYPES[dtype]

    start = deliver + timedelta(days=1)          # 期间开始的日不计入
    if unit == "day":
        raw = start + timedelta(days=n - 1)
        end = next_workday(raw, holidays)
    elif unit == "month":
        raw = add_months(start, n) - timedelta(days=1)
        end = next_workday(raw, holidays)
    elif unit == "year":
        raw = add_months(start, n * 12) - timedelta(days=1)
        end = next_workday(raw, holidays)
    else:
        raise ValueError(f"未知天数单位：{unit}")

    return {
        "type": dtype,
        "label": label,
        "deliver_date": deliver.isoformat(),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "duration": f"{n}{'日' if unit == 'day' else ('个月' if unit == 'month' else '年')}",
        "extended": end != raw,
        "law": law,
        "todo": f"须在 {end.isoformat()} 前完成{label.split('（')[0]}，逾期即丧失相应权利",
    }


def render(rows) -> str:
    """文本渲染。"""
    lines = ["# 应诉时限计算结果", ""]
    lines.append("| 节点 | 送达日 | 起算日 | 期限 | 届满日 | 法律依据 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['label']} | {r['deliver_date']} | {r['start_date']} | "
                     f"{r['duration']} | **{r['end_date']}** | {r['law']} |")
    lines.append("")
    for r in rows:
        flag = "（届满日已因法定休假日顺延）" if r["extended"] else ""
        lines.append(f"- 🔴 {r['todo']}{flag}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="应诉时限计算器（按送达日推算答辩期/举证期/上诉期等）")
    ap.add_argument("--deliver", help="送达日，格式 YYYY-MM-DD")
    ap.add_argument("--type", action="append", default=[],
                    help="期限类型，可重复；常用 first-instance / appeal-judgment / evidence-period")
    ap.add_argument("--mode", choices=["ordinary", "simplified"], default="ordinary",
                    help="程序类型：ordinary=普通程序，simplified=简易程序")
    ap.add_argument("--holidays", default="", help="法定休假日，逗号分隔，如 2026-04-04,2026-04-05")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--list", action="store_true", help="列出全部支持的期限类型")
    args = ap.parse_args(argv)

    if args.list:
        for k, v in DEADLINE_TYPES.items():
            print(f"{k:26s} {v[0]}　{v[2]}　{v[3]}")
        return 0

    if not args.deliver or not args.type:
        ap.error("--deliver 与 --type 均为必填（--list 除外）")
        return 2

    try:
        deliver = parse_date(args.deliver)
        holidays = parse_holidays(args.holidays)
    except ValueError as e:
        print(f"参数错误：{e}", file=sys.stderr)
        return 2

    types = []
    for t in args.type:
        types.append("evidence-simple" if (t == "evidence-period" and args.mode == "simplified") else t)

    rows = []
    for t in types:
        try:
            rows.append(compute(deliver, t, holidays))
        except ValueError as e:
            print(f"参数错误：{e}", file=sys.stderr)
            return 2

    payload = json.dumps(rows, ensure_ascii=False, indent=2) if args.json else render(rows)
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
