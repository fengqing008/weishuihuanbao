#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qbs_check.py —— QBS 法台账与四环闭合自检器（仅标准库）

对 QBS 台账 JSON 做交付前门禁自检：五阶段是否留痕、每阶段关键产出是否齐备、
「问题—书—技能—答案」四环是否闭合、是否存在来源缺口与降级事实未标注。

用法：
  python3 scripts/qbs_check.py --ledger qbs_ledger.json
  python3 scripts/qbs_check.py --ledger qbs_ledger.json --strict --json
  python3 scripts/qbs_check.py --self-test

退出码：0 = 全部通过；1 = 检出问题；2 = 参数或文件异常。
"""
import argparse
import json
import os
import sys

STAGES = [
    ("step0", "问题锁定", ["problem", "domain", "criteria"]),
    ("step1", "荐书", ["books", "scores"]),
    ("step2", "合规取书", ["source_type", "legal_basis", "fallback"]),
    ("step3", "转技能", ["skill_name", "skill_dir", "safety_scan"]),
    ("step4", "调用解题", ["answer", "trace_frames", "coverage_gap"]),
    ("step5", "留痕入库", ["ledger_path", "archive_path", "timestamp"]),
]
RULES = [
    ("Q1", "五阶段（Step 0—5）逐段留痕，缺段即失败分支"),
    ("Q2", "每阶段关键字段齐备，缺字段须在报告中标注为缺口而非补写"),
    ("Q3", "四环闭合：问题→书→技能→答案须能逐环回溯"),
    ("Q4", "取书路径须写明合法依据；无全文时降级事实必须显式标注"),
    ("Q5", "生成的技能须过安全扫描后才可注册；未过不进 Step 4"),
]


def _dig(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return True
    return False


def check_ledger(path, strict=False):
    problems, warn, notes = [], [], []
    if not os.path.isfile(path):
        return ["台账文件不存在或不可读：" + path], [], ["先执行 scripts/qbs_pipeline.py init 建台账"]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # 异常处理：解析失败不应中断流程
        return ["台账 JSON 解析异常：" + str(exc)], [], ["修复 JSON；无法修复时回退为空台账重跑 Step 0"]

    stages = data.get("stages", data)
    if not isinstance(stages, dict):
        return ["台账结构异常：缺少 stages 字典"], [], ["按 output-template.md 重建台账骨架"]

    missing_stage = []
    for key, label, fields in STAGES:
        node = stages.get(key)
        if not isinstance(node, dict) or not node:
            missing_stage.append("%s(%s) 未留痕（R1/Q1）" % (key, label))
            continue
        lack = [f for f in fields if not _dig(node, [f])]
        if lack:
            warn.append("%s(%s) 缺字段：%s（Q2：须在报告中标注为缺口）" % (key, label, "、".join(lack)))
        if node.get("degraded") and not node.get("degraded_note"):
            problems.append("%s(%s) 标记了降级但未写降级事实说明（Q4）" % (key, label))
    problems.extend(missing_stage)

    s0 = stages.get("step0") if isinstance(stages.get("step0"), dict) else {}
    s1 = stages.get("step1") if isinstance(stages.get("step1"), dict) else {}
    s3 = stages.get("step3") if isinstance(stages.get("step3"), dict) else {}
    s4 = stages.get("step4") if isinstance(stages.get("step4"), dict) else {}
    if s0 and not s1:
        problems.append("有问题陈述卡却无荐书评分（Q3：四环断裂于「问题→书」）")
    if s1 and not s3.get("skill_name"):
        problems.append("有选定书目却无生成的技能（Q3：四环断裂于「书→技能」）")
    if s3.get("skill_name") and not s3.get("safety_scan"):
        problems.append("生成的技能未经安全扫描即进入解题（Q5）")
    if s4 and not s4.get("trace_frames"):
        problems.append("解题结论未标注溯源框架（Q3：四环断裂于「技能→答案」）")

    if s1:
        books = s1.get("books") or s1.get("scores") or []
        if isinstance(books, list) and len(books) > 6:
            warn.append("候选书目 %d 本，超出黄金窗口 3—5 本，收敛不足（容错：可在 Step 1 复核点收敛）" % len(books))
    notes.append("已核对阶段 %d 个；阶段键：%s" % (len([k for k, _, _ in STAGES if isinstance(stages.get(k), dict)]),
                                              "、".join(k for k, _, _ in STAGES if isinstance(stages.get(k), dict)) or "无"))
    if strict:
        problems.extend(warn)
        warn = []
    return problems, warn, notes


def self_test():
    import tempfile
    tmp = tempfile.mkdtemp()
    good = {"stages": {k: {f: "x" for f in fields} for k, _, fields in STAGES}}
    good["stages"]["step3"]["skill_name"] = "sunzi-strategy"
    good["stages"]["step3"]["safety_scan"] = "pass"
    good["stages"]["step4"]["trace_frames"] = ["ch04", "ch06"]
    bad = {"stages": {"step0": {"problem": "如何破局"}}}
    p1 = os.path.join(tmp, "good.json")
    p2 = os.path.join(tmp, "bad.json")
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(good, f, ensure_ascii=False)
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(bad, f, ensure_ascii=False)
    probs_ok, _, _ = check_ledger(p1)
    probs_bad, _, _ = check_ledger(p2)
    print("[自检] 完整台账问题数 =", len(probs_ok), "(期望 0)")
    print("[自检] 残缺台账问题数 =", len(probs_bad), "(期望 >0)")
    ok = (not probs_ok) and bool(probs_bad)
    print("[自检] 结果：", "通过" if ok else "未通过")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="QBS 法台账与四环闭合自检器（Q1—Q5 门禁；仅标准库）",
        epilog="退出码：0 通过 / 1 检出问题 / 2 参数异常")
    ap.add_argument("--ledger", help="QBS 台账 JSON 路径")
    ap.add_argument("--strict", action="store_true", help="严格模式：警告一并计为问题")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结论")
    ap.add_argument("--self-test", action="store_true", help="内置自检")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.ledger:
        print("错误：需指定 --ledger，或使用 --self-test。", file=sys.stderr)
        return 2

    problems, warn, notes = check_ledger(args.ledger, args.strict)
    if args.json:
        print(json.dumps({"ledger": args.ledger, "problems": problems, "warnings": warn,
                          "notes": notes, "verdict": "pass" if not problems else "fail"},
                         ensure_ascii=False, indent=2))
    else:
        print("== QBS 台账四环闭合自检 ==")
        print("台账：", args.ledger)
        for n in notes:
            print("  ·", n)
        for w in warn:
            print("  [警告]", w)
        for p in problems:
            print("  [问题]", p)
        print("门禁规则：")
        for code, desc in RULES:
            print("  %s %s" % (code, desc))
        print("结论：", "通过" if not problems else "未通过（按提示补录后重跑，不必重跑全链路）")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
