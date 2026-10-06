#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""safety_check.py —— 安全三同时报告交付前质检（quality gate，仅标准库）

用途：对安全条件分析报告 / 安全设施设计专篇 / 安全验收评价报告 /
      职业病危害控制效果评价报告 的定稿做交付前体检：
  1) 报告类型合法性：是否属于四类法定报告之一（拼写错误即拦截）
  2) 占位符清零：【待填：...】残留即判 FAIL（残留占位等同于未完成编制）
  3) 依据年号：抽查引用的标准是否带年号（GB/GBZ/HJ/GB 5xxxx-20xx 形式）
  4) LEC 取值：核验 D = L × E × C 是否落在合法分级区间并给出危险等级

退出码：
  0  通过（无 FAIL 项）
  1  校验不通过（存在 FAIL 项）
  2  输入不足（缺参数 / 文件不存在 / 无法判定）

用法：
  python3 safety_check.py --help
  python3 safety_check.py --file 报告.md --type 安全验收评价报告 --lec 6 3 40
  python3 safety_check.py --file 报告.md --json
"""
import argparse
import json
import os
import re
import sys

REPORT_TYPES = [
    "安全条件分析报告",
    "安全设施设计专篇",
    "安全验收评价报告",
    "职业病危害控制效果评价报告",
]
PLACEHOLDER_RE = re.compile(r"【待填[:：][^】]*】")
STANDARD_RE = re.compile(r"(GB|GBZ|HJ|GB/T)\s?\d{2,6}(\.\d+)?\s*[-—–]\s?\d{4}")

LEC_LEVELS = [
    (320, "A 级（极其危险）"),
    (160, "B 级（高度危险）"),
    (70, "C 级（显著危险）"),
    (20, "D 级（一般危险）"),
    (0, "E 级（稍有危险）"),
]


def lec_level(d):
    for th, name in LEC_LEVELS:
        if d > th:
            return name
    return "E 级（稍有危险）"


def main():
    ap = argparse.ArgumentParser(
        description="安全三同时报告交付前质检（仅标准库，退出码 0/1/2）")
    ap.add_argument("--file", help="待质检的报告文本（md/txt）")
    ap.add_argument("--type", dest="rtype", default="",
                    help="报告类型：" + " / ".join(REPORT_TYPES))
    ap.add_argument("--lec", nargs=3, type=float, metavar=("L", "E", "C"),
                    help="LEC 作业条件危险性评价取值（L 可能性、E 暴露、C 后果）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结论")
    a = ap.parse_args()

    issues = []
    warnings = []
    info = {}

    if not a.file:
        issues.append("缺 --file：未提供待质检报告（退出码 2）")
    else:
        if not os.path.isfile(a.file):
            issues.append("文件不存在：%s" % a.file)
        else:
            try:
                with open(a.file, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception as e:  # 异常一律显式处理，不静默失败
                issues.append("文件读取失败：%s" % e)
                text = ""
            if text:
                info["chars"] = len(text)
                ph = len(PLACEHOLDER_RE.findall(text))
                info["placeholders"] = ph
                if ph > 0:
                    issues.append("残留【待填】占位 %d 处，等同未完成编制（FAIL）" % ph)
                st = STANDARD_RE.findall(text)
                info["standards_with_year"] = len(st)
                if len(st) == 0:
                    warnings.append("未检出带年号的标准引用（如 GB 50300-2013），请核对依据年号")

    if a.rtype:
        if a.rtype not in REPORT_TYPES:
            issues.append("非法报告类型 %s；合法值：%s"
                          % (a.rtype, " / ".join(REPORT_TYPES)))
        else:
            info["report_type"] = a.rtype

    if a.lec:
        l, e, c = a.lec
        if min(l, e, c) <= 0:
            issues.append("LEC 取值出现零值或负值 L=%s E=%s C=%s；取值须来自标准分级"
                          % (l, e, c))
        else:
            d = l * e * c
            info["lec"] = {"L": l, "E": e, "C": c, "D": d, "level": lec_level(d)}
            if d > 320:
                warnings.append("D=%s 判定 %s，须在报告中设置双重防护并留验证证据"
                                % (d, lec_level(d)))

    if not a.rtype and not a.lec and not a.file:
        issues.append("无任何可校验输入（退出码 2）")

    code = 0
    if issues:
        code = 2 if any((("缺 --" in i) or ("不存在" in i) or ("无任何" in i))
                        for i in issues) else 1

    result = dict(info)
    result["report_type_arg"] = a.rtype
    result["issues"] = issues
    result["warnings"] = warnings
    result["exit_code"] = code

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("# 安全三同时报告交付前质检")
        if "chars" in info:
            print("- 报告字符数: %d" % info["chars"])
            print("- 残留占位: %d 处" % info.get("placeholders", 0))
        if "lec" in info:
            x = info["lec"]
            print("- LEC: L=%s E=%s C=%s → D=%s（%s）"
                  % (x["L"], x["E"], x["C"], x["D"], x["level"]))
        for w in warnings:
            print("- [提示] %s" % w)
        if issues:
            for i in issues:
                print("- [不通过] %s" % i)
            print("结论：校验不通过，退出码 %d" % code)
        else:
            print("结论：校验通过，可交付（退出码 0）")
    return code


if __name__ == "__main__":
    sys.exit(main())
