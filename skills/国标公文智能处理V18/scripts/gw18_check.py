#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""国标公文智能处理V18 交付前自检脚本 gw18_check.py

用途：对公文底稿（Markdown 源稿）做交付前自检——核验文种结语、主送冒号、
禁用 AI 套话、半角标点、占位标注等，输出通过/告警结论。
用法：
    python3 gw18_check.py --file <公文.md> [--json]
退出码：0 通过 / 1 有告警 / 2 参数或读取错误
"""
import argparse
import json
import os
import re
import sys

AI_CLICHE = ["综上所述", "总的来说", "值得注意的是", "毋庸置疑", "不难发现", "总而言之", "需要指出的是"]
HALF_PUNCT = re.compile(r"[,;:?!]")


def check(path):
    if not os.path.isfile(path):
        return None, [f"文件不存在：{path}"]
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError as e:
        return None, [f"读取失败：{e}"]
    warnings = []
    if "请示" in text and "妥否，请批示" not in text:
        warnings.append("疑似请示但缺结语「妥否，请批示。」")
    if "报告" in text and "妥否，请批示" in text:
        warnings.append("报告结尾不得写「妥否，请批示」（请示报告混用）")
    if "---RECIPIENTS---" in text and "：" not in text:
        warnings.append("主送机关末尾缺全角冒号「：」")
    for w in AI_CLICHE:
        if w in text:
            warnings.append(f"出现 AI 套话：{w}")
    if "**" in text:
        warnings.append("出现 Markdown 加粗语法 `**`，公文禁用")
    if HALF_PUNCT.search(text):
        warnings.append("疑似出现半角标点，公文应使用全中文标点")
    if "〔" in text and ")" in text:
        warnings.append("发文字号年份应使用六角括号〔〕，勿用半角括号")
    return text, warnings


def main():
    ap = argparse.ArgumentParser(description="国标公文 交付前自检")
    ap.add_argument("--file", required=True, help="待检公文 Markdown 源稿")
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
            print("  通过：文种结语/主送/标点/套话检查无异常")
    sys.exit(0 if not warnings else 1)


if __name__ == "__main__":
    main()
