#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排污许可证申领及填报助手 出件自检脚本（permit_check.py）。

仅使用 Python 标准库（argparse / re / os / json / sys），不依赖第三方包。
用途：在排污许可申报材料定稿前，对两类关键产出做自检——
  1. 许可排放量核算复核：按 E = Q × h × C × 10⁻⁶（Q 处理能力 m³/d，h 年运行小时，
     C 限值 mg/L，E 吨/年）复算，并与环评批复量逐项取严（min），口径与
     scripts/permit_form_builder.py 的 limit-calc 子命令一致；
  2. 申报底稿齐套检查：核对管理类别判定、排放口信息、自行监测方案、台账要求、
     执行报告要求等必备章节是否齐备。

退出码：
  0 —— 全部核对通过；
  1 —— 核对不通过（取严失败 / 超环评批复量 / 底稿缺项）；
  2 —— 参数缺失、类型非法或文件不可读。

用法：
  python3 permit_check.py --design-flow 5000 --hours 8760 \
      --pollutants COD,氨氮,总氮,总磷 --limits 50,8,15,0.5 --env-batch 80,9
  python3 permit_check.py --draft 申报底稿.md --management key --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REQUIRED_SECTIONS = {
    "key": ["管理类别", "排放口", "自行监测", "台账", "执行报告"],
    "simple": ["管理类别", "排放口", "自行监测", "台账", "执行报告"],
    "registration": ["管理类别", "排放口", "登记"],
}


def _read(path: str) -> str:
    """读取文本文件（失败抛 ValueError）。"""
    if not path or not os.path.isfile(path):
        raise ValueError("文件不存在或不可读：%s" % path)
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception as exc:  # noqa: BLE001
        raise ValueError("文件不可解析：%s（%s）" % (path, exc))


def _split(text):
    """把逗号分隔串切成列表，空串返回空列表。"""
    if not text:
        return []
    return [x.strip() for x in str(text).replace("，", ",").split(",") if x.strip()]


def check_limits(design_flow, hours, pollutants, limits, env_batch):
    """复算许可排放量并与环评批复量取严，返回 (rows, problems)。"""
    rows = []
    problems = []
    if design_flow is None or design_flow <= 0:
        raise ValueError("--design-flow 须为正数（m³/d）")
    if not pollutants:
        raise ValueError("缺少 --pollutants（污染物列表）")
    if not limits:
        raise ValueError("缺少 --limits（浓度限值 mg/L）")
    if len(limits) != len(pollutants):
        raise ValueError("--limits 个数（%d）与 --pollutants 个数（%d）不一致"
                         % (len(limits), len(pollutants)))
    if env_batch and len(env_batch) != len(pollutants):
        raise ValueError("--env-batch 个数（%d）与 --pollutants 个数（%d）不一致"
                         % (len(env_batch), len(pollutants)))

    for i, name in enumerate(pollutants):
        try:
            c = float(limits[i])
        except ValueError:
            raise ValueError("--limits 第 %d 项非数值：%s" % (i + 1, limits[i]))
        calc = design_flow * hours * c * 1e-6
        env_val = None
        if env_batch:
            try:
                env_val = float(env_batch[i])
            except ValueError:
                raise ValueError("--env-batch 第 %d 项非数值：%s" % (i + 1, env_batch[i]))
        final = calc if env_val is None else min(calc, env_val)
        if env_val is not None and calc > env_val:
            problems.append("%s：公式值 %.4f 大于环评批复量 %.4f，须取严为 %.4f，未取严即驳回"
                            % (name, calc, env_val, final))
        rows.append({"pollutant": name, "limit_mg_L": c, "calc_t": round(calc, 4),
                     "env_batch_t": env_val, "final_t": round(final, 4)})
    return rows, problems


def check_draft(text, management):
    """核对申报底稿必备章节，返回缺失项。"""
    keywords = REQUIRED_SECTIONS.get(management, REQUIRED_SECTIONS["key"])
    missing = [k for k in keywords if k not in text]
    return missing


def run_check(args: argparse.Namespace) -> dict:
    """执行自检，返回结构化结果。"""
    problems = []
    notes = []
    rows = []

    if not args.draft and args.design_flow is None:
        raise ValueError("至少提供 --design-flow 或 --draft 之一")

    if args.design_flow is not None:
        rows, lim_problems = check_limits(args.design_flow, args.hours,
                                          _split(args.pollutants), _split(args.limits),
                                          _split(args.env_batch))
        problems.extend(lim_problems)
        notes.append("许可排放量核算 %d 项，取严问题 %d 项" % (len(rows), len(lim_problems)))

    if args.draft:
        text = _read(args.draft)
        missing = check_draft(text, args.management)
        if len(missing) > args.max_missing:
            problems.append("申报底稿缺失必备章节 %d 项，超阈值 %d：%s"
                            % (len(missing), args.max_missing, "、".join(missing)))
        notes.append("底稿章节核对：缺 %d 项" % len(missing))

    return {
        "management": args.management,
        "draft": args.draft or "",
        "limits": rows,
        "result": "PASS" if not problems else "FAIL",
        "problems": problems,
        "notes": notes,
    }


def main(argv=None) -> int:
    """命令行入口。返回退出码 0/1/2。"""
    parser = argparse.ArgumentParser(description="排污许可申报出件自检脚本（标准库实现）")
    parser.add_argument("--design-flow", type=float, help="设计处理能力，单位 m³/d")
    parser.add_argument("--hours", type=float, default=8760, help="年运行小时数，默认 8760")
    parser.add_argument("--pollutants", help="污染物列表，逗号分隔，如 COD,氨氮")
    parser.add_argument("--limits", help="浓度限值列表（mg/L），逗号分隔")
    parser.add_argument("--env-batch", help="环评批复排放量列表（吨/年），用于取严")
    parser.add_argument("--draft", help="申报底稿 Markdown 路径（可选）")
    parser.add_argument("--management", choices=["key", "simple", "registration"],
                        default="key", help="管理类别，默认 key")
    parser.add_argument("--max-missing", type=int, default=0, help="可容忍的底稿缺项数，默认 0")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args(argv)

    try:
        report = run_check(args)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"result": "ERROR", "problems": [str(exc)]},
                             ensure_ascii=False, indent=2))
        else:
            print("输入不足：%s" % exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("出件自检结果：%s" % report["result"])
        for note in report["notes"]:
            print("  " + note)
        for row in report["limits"]:
            print("  %s：限值 %s mg/L，公式值 %s t，批复 %s t，取严后 %s t"
                  % (row["pollutant"], row["limit_mg_L"], row["calc_t"],
                     row["env_batch_t"], row["final_t"]))
        for prob in report["problems"]:
            print("  [问题] " + prob)

    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
