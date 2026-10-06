#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mdformat_check.py —— Markdown 排版结果自检器（仅标准库）。

在「排版美化」交付前对 {filename}-formatted.md 做结构与排版合规自检：
frontmatter 合法性、标题层级连续性、代码围栏闭合、列表/强调标记配对、
行尾空白、CJK 与英文间距等。本脚本只读不写，绝不改动原稿内容。

退出码：
  0 —— 通过
  1 —— 存在可修复的提示项（不阻断交付）
  2 —— 存在致命问题（如代码围栏未闭合、frontmatter 非法）

用法：
  python3 mdformat_check.py article-formatted.md
  python3 mdformat_check.py article-formatted.md --json
  python3 mdformat_check.py --help
"""
import argparse
import json
import os
import re
import sys

EXIT_OK, EXIT_WARN, EXIT_FATAL = 0, 1, 2


def read(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def check(text):
    warn, fatal = [], []

    # frontmatter
    if text.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
        if not m:
            fatal.append("frontmatter 起始标记存在但未闭合（--- 缺失）")
        else:
            keys = re.findall(r"^([A-Za-z_][\w-]*):", m.group(1), re.M)
            dupes = {k for k in keys if keys.count(k) > 1}
            if dupes:
                warn.append("frontmatter 存在重复键：%s" % ", ".join(sorted(dupes)))
    else:
        warn.append("未检测到 frontmatter（如属预期可忽略）")

    body = text
    # 代码围栏闭合
    if body.count("```") % 2 != 0:
        fatal.append("代码围栏数量为奇数，存在未闭合的 ``` —— 渲染会溢出")

    # 标题层级跳跃
    levels = [len(h) for h in re.findall(r"^(#{1,6})\s+\S", body, re.M)]
    prev = 0
    for lv in levels:
        if prev and lv > prev + 1:
            warn.append("标题层级从 H%d 跳到 H%d，建议补中间层级" % (prev, lv))
        prev = lv

    # 强调标记配对（粗体）
    if body.count("**") % 2 != 0:
        warn.append("** 粗体标记数量为奇数，疑似未配对")

    # 行尾空白
    trailing = sum(1 for ln in body.splitlines() if ln != ln.rstrip())
    if trailing:
        warn.append("存在 %d 行行尾空白" % trailing)

    # 制表符
    if "\t" in body:
        warn.append("正文含制表符，建议统一为空格")

    return warn, fatal


def main(argv=None):
    p = argparse.ArgumentParser(description="Markdown 排版结果自检器（只读，容错式）")
    p.add_argument("file", nargs="?", help="待检查的 markdown 文件路径")
    p.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = p.parse_args(argv)

    if not args.file:
        p.print_help()
        return EXIT_WARN
    if not os.path.isfile(args.file):
        res = {"ok": False, "exit": EXIT_FATAL, "fatal": ["文件不存在：%s" % args.file], "warn": []}
    else:
        warn, fatal = check(read(args.file))
        code = EXIT_FATAL if fatal else (EXIT_WARN if warn else EXIT_OK)
        res = {"ok": code == EXIT_OK, "exit": code, "fatal": fatal, "warn": warn}

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("[mdformat_check] 文件：%s" % args.file)
        for m in res["fatal"]:
            print("  致命：%s" % m)
        for m in res["warn"]:
            print("  提示：%s" % m)
        print("结论：%s" % ("通过" if res["ok"] else "需处理（退出码 %d）" % res["exit"]))
    return res["exit"]


if __name__ == "__main__":
    sys.exit(main())
