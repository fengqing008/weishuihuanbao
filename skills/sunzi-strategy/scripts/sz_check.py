#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""孙子谋略博弈策略自检器（sz_check.py）。

仅使用 Python 标准库（argparse / json / sys / textwrap），不依赖第三方包。
依据《孙子兵法》始计篇「道天地将法」五事与谋攻篇「伐谋＞伐交＞伐兵＞攻城」
行动优先级，对一份「局势卡」做规则校验，确保推演前的输入要素齐备、
合法性红线未被触碰，并可对五维评估做差值复算。

校验项：
  1. 五事齐备：道（共识）/ 天（时机）/ 地（场域）/ 将（主事者）/ 法（组织机制）五项均须有值；
  2. 双方对照：我方与对方均须填写五维，方可算差值；
  3. 合法性红线：目标、手段不得含违法 / 暴力 / 欺诈 / 侵害他人权益等关键词；
  4. 度量口径：目标须可衡量（含数字、比例或时间节点之一）；
  5. 退出条件：须给出「宜避 / 待势 / 可争」之外的退出条件描述。

退出码：
  0 —— 全部校验通过（可进入主推演流程）；
  1 —— 校验不通过（存在缺项 / 红线命中 / 目标不可衡量）；
  2 —— 输入不足或参数非法（文件不存在、JSON 不可解析、关键字段缺失）。

用法：
  python3 scripts/sz_check.py --canvas situation.json
  python3 scripts/sz_check.py --canvas situation.json --json
  python3 scripts/sz_check.py --demo            # 输出一份示例局势卡并自检

局势卡 JSON 结构：
  {
    "objective": "争取在 3 个月内把采购单价压到 12 万元以内",
    "deadline": "2026-12-31",
    "exit_condition": "若对方拒绝让步超过两轮则暂缓谈判",
    "legal": true,
    "us":   {"道": "目标一致", "天": "窗口上升", "地": "主场", "将": "授权清晰", "法": "流程明确"},
    "them": {"道": "内部有分歧", "天": "持平", "地": "客场", "将": "决策慢", "法": "标准不清"}
  }
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

DIMS = ["道", "天", "地", "将", "法"]
DIMS_ALIAS = {
    "道": ["道", "正当性", "共识"],
    "天": ["天", "时机"],
    "地": ["地", "场域", "地形"],
    "将": ["将", "主事者", "主将"],
    "法": ["法", "组织机制", "制度"],
}
REDLINE_PAT = re.compile(
    r"违法|暴力|欺诈|诈骗|胁迫|行贿|受贿|伪造|侵害他人|窃取|打击报复|人身伤害"
)
MEASURABLE_PAT = re.compile(r"\d+\s*(%|％|万|亿|元|天|日|周|月|年|个|次|倍|%)|提升|下降|降低|控制在")


def _get(d, names):
    for n in names:
        if n in d and str(d[n]).strip():
            return str(d[n]).strip()
    return ""


def check(canvas):
    """返回 (issues, warns, detail)。issues 非空即判不通过。"""
    issues, warns, detail = [], [], {}

    obj = _get(canvas, ["objective", "目标", "诉求"])
    if not obj:
        issues.append("缺「目标」：未给出要达成的结果。")
    elif not MEASURABLE_PAT.search(obj):
        issues.append("「目标」不可衡量：须含数字 / 比例 / 时间节点之一。")

    if not _get(canvas, ["deadline", "期限", "时间"]):
        warns.append("缺「期限」：无时间约束，推演结论易失效。")

    if not _get(canvas, ["exit_condition", "退出条件", "止损"]):
        issues.append("缺「退出条件」：须预设宜避 / 待势之外的止损线。")

    legal = canvas.get("legal", canvas.get("合法", True))
    if legal is False:
        issues.append("「合法性」自述为否：红线命中，停止推演。")

    for side_key, side_name in (("us", "我方"), ("them", "对方")):
        side = canvas.get(side_key) or {}
        if not isinstance(side, dict):
            issues.append(f"{side_name}五维格式非法：应为对象。")
            continue
        got = {}
        for d in DIMS:
            v = _get(side, DIMS_ALIAS[d])
            if not v:
                issues.append(f"{side_name}缺「{d}」：五事须齐备。")
            got[d] = v if v else "——"
        detail[side_name] = got

    blob = json.dumps(canvas, ensure_ascii=False)
    hit = sorted(set(REDLINE_PAT.findall(blob)))
    if hit:
        issues.append("红线命中：" + "、".join(hit) + "；应停止推演并说明边界。")

    return issues, warns, detail


def render(detail):
    if not detail:
        return ""
    out = ["| 维度 | 我方 | 对方 | 差值判读 |", "|---|---|---|---|"]
    for d in DIMS:
        a = detail.get("我方", {}).get(d, "——")
        b = detail.get("对方", {}).get(d, "——")
        diff = "持平" if a == b else "有差"
        out.append(f"| {d} | {a} | {b} | {diff} |")
    return "\n".join(out)


DEMO = {
    "objective": "争取在 3 个月内把采购单价压到 12 万元以内",
    "deadline": "2026-12-31",
    "exit_condition": "若对方拒绝让步超过两轮则暂缓谈判",
    "legal": True,
    "us": {"道": "内部目标一致", "天": "需求窗口上升", "地": "主场谈判", "将": "授权边界清晰", "法": "审批流程明确"},
    "them": {"道": "内部有分歧", "天": "行情持平", "地": "客场应酬", "将": "决策链较长", "法": "标准不统一"},
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="孙子谋略局势卡自检器（sz_check.py）")
    ap.add_argument("--canvas", help="局势卡 JSON 文件路径")
    ap.add_argument("--demo", action="store_true", help="以内置示例局势卡运行自检")
    ap.add_argument("--json", dest="as_json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args(argv)

    if args.demo:
        canvas = DEMO
    elif args.canvas:
        if not os.path.isfile(args.canvas):
            msg = f"输入不足：文件不存在 {args.canvas}"
            print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False) if args.as_json else msg)
            return 2
        try:
            with open(args.canvas, encoding="utf-8") as f:
                canvas = json.load(f)
        except Exception as exc:  # 输入非法
            msg = f"输入不足：JSON 不可解析（{exc}）"
            print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False) if args.as_json else msg)
            return 2
    else:
        msg = "输入不足：请提供 --canvas <file> 或 --demo"
        print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False) if args.as_json else msg)
        return 2

    if not isinstance(canvas, dict):
        msg = "输入不足：局势卡根节点应为对象。"
        print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False) if args.as_json else msg)
        return 2

    issues, warns, detail = check(canvas)
    code = 1 if issues else 0
    if args.as_json:
        print(json.dumps({
            "status": "pass" if code == 0 else "fail",
            "exit_code": code,
            "issues": issues,
            "warnings": warns,
            "detail": detail,
        }, ensure_ascii=False, indent=2))
    else:
        print("局势卡：", canvas.get("objective", "（未命名）"))
        print(render(detail))
        for w in warns:
            print("⚠️ ", w)
        for i in issues:
            print("❌ ", i)
        print("结论：", "通过，可进入主推演流程" if code == 0 else "不通过，先补齐再推演")
    return code


if __name__ == "__main__":
    sys.exit(main())
