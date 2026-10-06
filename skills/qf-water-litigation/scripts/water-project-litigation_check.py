#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""water-project-litigation 交付质检脚本（water-project-litigation）。

用法：python3 scripts/water-project-litigation_check.py --file <交付物.md>
退出码：0=通过；1=有问题。
"""
import argparse
import re
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    a = ap.parse_args()
    t = open(a.file, encoding="utf-8", errors="ignore").read()
    issues = []
    if len(t.strip()) < 50:
        issues.append("内容过短")
    if "TODO" in t or "待补充" in t:
        issues.append("存在未清理占位符")
    if re.search(r"(?<![\d,.])\d{4,}(?![\d,])", t):
        issues.append("长数字疑未千分位")
    if issues:
        print("质检未过：")
        for x in issues:
            print("  -", x)
        sys.exit(1)
    print("质检通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
