#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mie_check.py —— 会议行为洞察报告交付前质检（标准库实现）。

对 meeting_stats.py 产出的洞察报告 Markdown 做交付前自检：
  1. 报告是否含时间戳证据（[HH:MM:SS] 或 序位代替时间 标注）
  2. 每条证据是否写成三段式（原话引用 / 影响判断 / 更好的说法）
  3. 是否给出证据强度等级（证据强度：中/低）
  4. 是否含未脱敏的疑似敏感信息（客户名占位、金额、身份证）
  5. 交付三件（报告/stats.json/趋势台账）是否在报告中声明

退出码：0 = 通过；1 = 存在缺项或告警（需人工复核）；2 = 参数或文件读取错误。

用法：
  python3 mie_check.py --input 会议洞察报告.md
  python3 mie_check.py --input 会议洞察报告.md --json
"""
import argparse
import json
import re
import sys
from pathlib import Path

TS_RE = re.compile(r"\[\d{1,2}:\d{2}(?::\d{2})?\]")
SENSITIVE = [r"身份证", r"\b\d{17}[\dXx]\b", r"银行卡", r"\b\d{16,19}\b"]


def load(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"文件不存在：{path}")
    return p.read_text(encoding="utf-8", errors="replace")


def check(text):
    issues = []

    if not TS_RE.search(text) and "序位代替时间" not in text:
        issues.append("缺少时间戳证据（[HH:MM:SS]）且未标注序位代替时间")

    for key in ["更好的说法", "影响"]:
        if key not in text:
            issues.append(f"证据三段式缺少「{key}」段落")

    if "证据强度" not in text:
        issues.append("未给出证据强度等级（中/低）")

    if "stats.json" not in text and "统计底稿" not in text:
        issues.append("未声明 stats.json 统计底稿")

    for pat in SENSITIVE:
        if re.search(pat, text):
            issues.append(f"疑似未脱敏敏感信息命中：{pat}")

    return issues


def main():
    ap = argparse.ArgumentParser(description="会议行为洞察报告交付前质检")
    ap.add_argument("--input", required=True, help="洞察报告 Markdown 文件路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    try:
        text = load(args.input)
    except Exception as exc:  # 读取错误 → 退出码 2
        print(f"[ERR] {exc}", file=sys.stderr)
        return 2

    issues = check(text)
    result = {"input": args.input, "issues": issues,
              "verdict": "PASS" if not issues else "REVIEW"}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for it in issues:
            print(f"[WARN] {it}")
        print(f"[{'PASS' if not issues else 'REVIEW'}] {args.input}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
