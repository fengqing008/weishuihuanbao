#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eia_check.py — 环评法规导则速查专家 · 输出稿防御式自检脚本（仅用标准库）

用途：对一份环评速查 / 类别判定 / 限值查询输出稿做交付前自检，
落实「不核验不出稿」的数据纪律，为引用失败模式做兜底闸门。

退出码约定：
  0 = 通过（无告警）
  1 = 告警（存在需人工复核项，如【待核】或强断言未附来源）
  2 = 硬错误（文件不存在 / 读取异常 / 输入为空）

用法：
  python3 eia_check.py --help
  python3 eia_check.py --file draft.md
  python3 eia_check.py --text "GB 18918-2002 一级A COD≤50"
  python3 eia_check.py --file draft.md --strict
"""
import argparse
import os
import re
import sys

SOURCE_KEYS = ["来源", "出处", "依据", "溯", "检索日期", "kb_id", "media_id"]
CITE_RE = re.compile(r"《[^》]{2,40}》|GB\s?/?T?\s?\d{3,}|HJ\s?\d{2,}|国务院令第\d+号|〔\d{4}〕")
PENDING = "【待核"
STRONG_ASSERT = ["现行有效", "确定为", "一定是", "必然现行"]


def load(args):
    if args.file:
        if not os.path.isfile(args.file):
            return None, "文件不存在：%s" % args.file
        try:
            with open(args.file, encoding="utf-8", errors="ignore") as fh:
                return fh.read(), None
        except OSError as exc:
            return None, "文件读取异常：%s" % exc
    if args.text is not None:
        return args.text, None
    return "", None


def main(argv=None):
    parser = argparse.ArgumentParser(description="环评速查输出稿防御式自检（标准库实现）")
    parser.add_argument("--file", help="待检输出稿路径（Markdown/文本）")
    parser.add_argument("--text", help="直接传入待检文本")
    parser.add_argument("--strict", action="store_true", help="严格模式：出现任一告警即返回 1")
    args = parser.parse_args(argv)

    text, err = load(args)
    if err:
        print("[硬错误] " + err)
        return 2
    if text is None or not text.strip():
        print("[硬错误] 输入为空或未提供 --file / --text")
        return 2

    body = text.strip()
    warns = []

    if not any(key in body for key in SOURCE_KEYS):
        warns.append("未见来源 / 出处标记，请补「数据来源」行（来源 + 检索日期）")

    cites = CITE_RE.findall(body)
    if not cites:
        warns.append("未检出标准号或法规文号，请补引用依据（标准号 + 表号 / 条目号）")

    if PENDING in body:
        warns.append("含【待核】项，交付前须人工复核或重新检索补齐")

    for word in STRONG_ASSERT:
        if word in body:
            warns.append("检出强断言「%s」，须附来源或改写为【待核】" % word)

    print("引用命中数：%d" % len(cites))
    if warns:
        for item in warns:
            print("[告警] " + item)
        return 1

    print("[通过] 输出稿自检无告警")
    return 0


if __name__ == "__main__":
    sys.exit(main())
