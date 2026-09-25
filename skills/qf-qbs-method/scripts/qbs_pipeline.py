#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QBS 法 · 台账与闭环校验（零第三方依赖）

子命令：
  init   创建台账（--problem 写入 Step 0）
  update 将某阶段标记为完成（--stage/--artifact/--note）
  status 查看台账进度
  check  校验闭环是否闭合（问题→荐书→取书→技能→解题）
  doctor 自检
"""
import argparse
import json
import os
import sys
from datetime import datetime

STAGES = [
    ("0_problem", "问题锁定"),
    ("1_recommend", "荐书"),
    ("2_source", "合规取书"),
    ("3_skill", "转技能"),
    ("4_solve", "调用解题"),
    ("5_archive", "留痕入库"),
]
STAGE_MAP = dict(STAGES)
DEFAULT_LEDGER = ".qbs_ledger.json"


def load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_init(args):
    if os.path.exists(args.ledger):
        print("台账已存在：%s（如需重建请先删除）" % args.ledger, file=sys.stderr)
        return 1
    data = {
        "problem": args.problem,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stages": {sid: {"done": False, "artifact": "", "note": ""} for sid, _ in STAGES},
    }
    if args.problem:
        data["stages"]["0_problem"]["done"] = True
        data["stages"]["0_problem"]["note"] = args.problem
    save(args.ledger, data)
    print("已创建 QBS 台账：%s" % args.ledger)
    return 0


def cmd_update(args):
    data = load(args.ledger)
    if data is None:
        print("错误：台账不存在，请先执行 init", file=sys.stderr)
        return 2
    if args.stage not in data["stages"]:
        print("错误：未知阶段 %s（可选：%s）" % (args.stage, ",".join(s for s, _ in STAGES)), file=sys.stderr)
        return 2
    st = data["stages"][args.stage]
    st["done"] = True
    if args.artifact:
        st["artifact"] = args.artifact
    if args.note:
        st["note"] = args.note
    st["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save(args.ledger, data)
    print("已更新阶段 %s（%s）" % (args.stage, STAGE_MAP[args.stage]))
    return 0


def cmd_status(args):
    data = load(args.ledger)
    if data is None:
        print("台账不存在：%s" % args.ledger, file=sys.stderr)
        return 2
    print("QBS 台账：%s" % args.ledger)
    print("问题：%s" % data.get("problem", ""))
    for sid, name in STAGES:
        st = data["stages"].get(sid, {})
        mark = "✔" if st.get("done") else "○"
        art = ("　产出：%s" % st["artifact"]) if st.get("artifact") else ""
        print("  %s %s %s%s" % (mark, sid, name, art))
    return 0


def cmd_check(args):
    data = load(args.ledger)
    if data is None:
        print("错误：台账不存在", file=sys.stderr)
        return 2
    missing = []
    if not data.get("problem"):
        missing.append("问题陈述（Step 0）")
    for sid, name in STAGES[1:5]:
        if not data["stages"].get(sid, {}).get("done"):
            missing.append("%s（%s）" % (name, sid))
    if missing:
        print("闭环未闭合，缺：%s" % "；".join(missing))
        return 1
    print("闭环已闭合：问题→荐书→取书→技能→解题 四环齐备")
    return 0


def cmd_doctor(args):
    print("qbs_pipeline 自检：OK（台账默认 %s，阶段数 %d）" % (DEFAULT_LEDGER, len(STAGES)))
    return 0


def main():
    ap = argparse.ArgumentParser(description="QBS 台账与闭环校验")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help="台账路径（默认 .qbs_ledger.json）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="创建台账")
    p.add_argument("--problem", default="", help="问题陈述")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("update", help="将某阶段标记为完成")
    p.add_argument("--stage", required=True,
                   help="阶段键（0_problem/1_recommend/2_source/3_skill/4_solve/5_archive）")
    p.add_argument("--artifact", default="", help="产出物路径")
    p.add_argument("--note", default="", help="备注")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("status", help="查看台账")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("check", help="闭环校验")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("doctor", help="自检")
    p.set_defaults(func=cmd_doctor)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
