#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同起草审查 交付前自检脚本 hzl_check.py

用途：对起草/审查后的合同底稿做交付前自检——核对十大核心模块是否齐备、
关键数据是否以【待核】标注，输出通过/告警结论。
用法：
    python3 hzl_check.py --file <合同.md|.json> [--json]
退出码：0 通过 / 1 有告警 / 2 参数或读取错误
"""
import argparse
import json
import os
import sys

REQUIRED = ["主体", "标的", "价款", "支付", "交付", "违约", "争议解决", "不可抗力", "保密", "生效"]
PLACEHOLDER = "【待核"


def check(path):
    if not os.path.isfile(path):
        return None, [f"文件不存在：{path}"]
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError as e:
        return None, [f"读取失败：{e}"]
    warnings = []
    for kw in REQUIRED:
        if kw not in text:
            warnings.append(f"缺少核心模块关键词：{kw}")
    if PLACEHOLDER not in text:
        warnings.append("未见【待核】标注，请确认金额/日期/主体等关键数据均已核实")
    return text, warnings


def main():
    ap = argparse.ArgumentParser(description="合同起草审查 交付前自检")
    ap.add_argument("--file", required=True, help="待检合同 Markdown 或 JSON 文件")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()
    try:
        text, warnings = check(args.file)
    except Exception as e:  # 兜底防御：任何未预期异常均以退出码 2 汇报
        print(f"内部错误：{e}", file=sys.stderr)
        sys.exit(2)
    if text is None:
        print("；".join(warnings), file=sys.stderr)
        sys.exit(2)
    result = {"file": args.file, "chars": len(text), "warnings": warnings,
              "status": "pass" if not warnings else "warn"}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"文件：{args.file}（{len(text)} 字符）")
        if warnings:
            for w in warnings:
                print(f"  [告警] {w}")
        else:
            print("  通过：核心模块与【待核】标注检查无异常")
    sys.exit(0 if not warnings else 1)


if __name__ == "__main__":
    main()
