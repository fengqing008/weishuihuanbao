#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""policy_check.py —— 水务政策引用合规自检（仅标准库）

用途：对政策引用材料（Markdown/文本）或单条政策卡片字段做合规自检，
检查引用是否齐备「文件全称 + 文号 + 条款」三要件、是否标注时效状态、
是否出现「根据相关政策规定」这类无依据泛指。

退出码：
  0  全部通过
  1  存在缺项/告警（可交付前需补齐）
  2  输入错误或用法错误（文件不存在、参数非法）

用法：
  python3 policy_check.py --file draft.md
  python3 policy_check.py --name "关于推进全省乡镇生活污水治理提质增效行动的通知" --docno "鄂建文〔2023〕4号" --status 现行有效
  python3 policy_check.py --help
"""
import argparse
import os
import re
import sys

DOCNO_RE = re.compile(r"[〔(（]\d{4}[〕)）]\s?\d+\s?号")
LAWNAME_RE = re.compile(r"《[^》]{2,60}》")
VAGUE_PATTERNS = [
    "根据相关政策规定", "根据有关政策", "相关规定", "有关文件精神",
    "按照相关政策", "依据相关文件",
]
VALID_STATUS = ["现行有效", "已修订", "已废止", "试行", "征求意见"]


def check_text(text):
    """返回 (errors, warnings) 列表。"""
    errors, warnings = [], []
    names = LAWNAME_RE.findall(text)

    # 1) 文件全称
    if not names:
        errors.append("未检出《文件全称》：引用须写文件全称，不得只写简称或口头指代")

    # 2) 文号
    if not DOCNO_RE.search(text):
        errors.append("未检出文号（如〔2023〕4号）：[待核：文号]，不得臆造文号")

    # 3) 时效状态
    if not any(s in text for s in VALID_STATUS):
        warnings.append("未标注时效状态：应注明 现行有效/已修订/已废止/试行/征求意见")

    # 4) 泛指表述
    for p in VAGUE_PATTERNS:
        if p in text:
            errors.append("出现无依据泛指「%s」：改为文件全称+文号+条款" % p)

    # 5) 条款序号
    if not re.search(r"第[一二三四五六七八九十百零\d]+条", text):
        warnings.append("未检出条款序号（如第X条）：关键条款建议注明序号")

    # 6) 待核标注是否残留
    pending = re.findall(r"【待核[^】]*】", text)
    if pending:
        warnings.append("存在未闭环的【待核】项 %d 处：交付前须补核" % len(pending))

    return errors, warnings


def check_fields(name, docno, status, level):
    errors, warnings = [], []
    if not name:
        errors.append("缺文件名（--name）")
    elif not LAWNAME_RE.search(name) and "《" not in name:
        warnings.append("文件名建议用《》括起全称")
    if not docno:
        errors.append("缺文号（--docno）：须标【待核：文号】")
    elif not DOCNO_RE.search(docno):
        warnings.append("文号格式疑似不规范：期望形如〔2023〕4号")
    if not status:
        warnings.append("缺时效状态（--status）")
    elif status not in VALID_STATUS:
        warnings.append("时效状态取值建议为：%s" % "/".join(VALID_STATUS))
    if not level:
        warnings.append("缺发文层级（--level）：国家级/省级/市县级")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser(
        description="水务政策引用合规自检（文件全称+文号+条款三要件、时效状态、泛指排查）")
    ap.add_argument("--file", help="待检查的引用材料路径（md/txt）")
    ap.add_argument("--name", help="政策文件名称（字段模式）")
    ap.add_argument("--docno", help="政策文号（字段模式）")
    ap.add_argument("--status", help="时效状态：现行有效/已修订/已废止/试行/征求意见")
    ap.add_argument("--level", help="发文层级：国家级/省级/市县级")
    args = ap.parse_args()

    if not args.file and not args.name:
        ap.print_help()
        print("\n[错误] 需提供 --file 或 --name 之一")
        return 2

    if args.file:
        if not os.path.isfile(args.file):
            print("[错误] 文件不存在：%s" % args.file)
            return 2
        try:
            with open(args.file, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError as exc:
            print("[错误] 读取失败：%s" % exc)
            return 2
        if not text.strip():
            print("[错误] 文件内容为空")
            return 2
        errors, warnings = check_text(text)
        print("模式：引用材料自检 -> %s" % args.file)
    else:
        errors, warnings = check_fields(args.name, args.docno, args.status, args.level)
        print("模式：政策卡片字段自检")

    print("-" * 52)
    for e in errors:
        print("[缺项] %s" % e)
    for w in warnings:
        print("[告警] %s" % w)
    print("-" * 52)
    if errors:
        print("结论：不通过（缺项 %d，告警 %d）" % (len(errors), len(warnings)))
        return 1
    if warnings:
        print("结论：有条件通过（告警 %d，建议补齐后再交付）" % len(warnings))
        return 1
    print("结论：通过（三要件齐备，可交付）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
