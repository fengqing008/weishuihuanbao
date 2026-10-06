#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梦象解读交付质检器（dream_check.py）。

仅使用 Python 标准库（argparse / json / os / re / sys），不依赖第三方包。
对梦象解读的产出做交付前自检，覆盖：数据资产可用性、三层结构完整性、
免责声明齐全、章节正文密度、越界断言红线、反兆并列提示。

自检项：
  A. 数据资产（assets/dream_symbols.json、classics.json、gua_map.json）存在且可解析；
  B. 输出正文含统一免责声明；
  C. 三层结构齐备（典籍 → 民俗（传统解读）→ 心理象征）；
  D. 报告型产出的每个章节正文字数不少于阈值（默认 300 中文字）；
  E. 越界红线：不得出现「必发财 / 必离婚 / 一定会 / 注定 / 必然」等断言词；
  F. 反兆条目（梦哭主喜 / 见棺主官财 / 梦死反主更生）须与常义并列，不得单取。

退出码：
  0 —— 全部通过；
  1 —— 校验不通过（缺免责 / 密度不足 / 红线命中）；
  2 —— 输入不足或文件非法（文件不存在、JSON 不可解析、缺资产）。

用法：
  python3 scripts/dream_check.py --selfcheck
  python3 scripts/dream_check.py --file 梦象解读报告.html
  python3 scripts/dream_check.py --file report.md --min-chars 300 --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = ["dream_symbols.json", "classics.json", "gua_map.json"]

DISCLAIMER_KEYS = ["不构成任何决策依据", "传统文化研究范畴", "免责"]
LAYERS = {"典籍": ["典籍", "出处", "古籍"], "民俗": ["民俗", "传统解读", "传统解梦"], "心理": ["心理象征", "心理"]}
ASSERT_PAT = re.compile(r"必发财|必离婚|一定能|必定|注定|必然发生|一定会出事|必定发财")
FANZHAO = ["梦哭主喜", "见棺主官财", "梦死反主更生"]


def count_cjk(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def selfcheck():
    problems = []
    for name in ASSETS:
        p = os.path.join(BASE, "assets", name)
        if not os.path.isfile(p):
            problems.append(f"缺数据资产：assets/{name}")
            continue
        try:
            with open(p, encoding="utf-8") as f:
                json.load(f)
        except Exception as exc:
            problems.append(f"数据资产不可解析：assets/{name}（{exc}）")
    return problems


def check_text(text, min_chars):
    problems, warns = [], []

    if not any(k in text for k in DISCLAIMER_KEYS):
        problems.append("缺统一免责声明：输出末尾必须带「不构成任何决策依据」类声明。")

    for layer, keys in LAYERS.items():
        if not any(k in text for k in keys):
            problems.append(f"三层结构缺「{layer}」层。")

    hit = sorted(set(ASSERT_PAT.findall(text)))
    if hit:
        problems.append("越界断言红线命中：" + "、".join(hit) + "；须回到文化定位。")

    for fz in FANZHAO:
        if fz in text and ("常义" not in text and "亦" not in text):
            warns.append(f"反兆条目「{fz}」未见与常义并列，请复核。")

    sections = re.split(r"\n(?=##\s)", text)
    thin = []
    for sec in sections:
        m = re.match(r"##\s*(.+)", sec)
        if not m:
            continue
        title = m.group(1).strip()
        if "免责" in title or "说明" in title:
            continue
        if count_cjk(sec) < min_chars:
            thin.append(f"{title}（{count_cjk(sec)} 字）")
    if thin:
        problems.append("章节正文密度不足：" + "、".join(thin))
    return problems, warns


def main(argv=None):
    ap = argparse.ArgumentParser(description="梦象解读交付质检器（dream_check.py）")
    ap.add_argument("--file", help="待检文件（.md / .html / .txt）")
    ap.add_argument("--text", help="待检文本（与 --file 二选一）")
    ap.add_argument("--min-chars", type=int, default=300, help="每章中文字数下限，默认 300")
    ap.add_argument("--selfcheck", action="store_true", help="仅校验数据资产可用性")
    ap.add_argument("--json", dest="as_json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args(argv)

    problems, warns = [], []

    if args.selfcheck or not (args.file or args.text):
        problems += selfcheck()

    if args.file:
        if not os.path.isfile(args.file):
            msg = f"输入不足：文件不存在 {args.file}"
            print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False) if args.as_json else msg)
            return 2
        try:
            with open(args.file, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as exc:
            msg = f"输入不足：文件不可读（{exc}）"
            print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False) if args.as_json else msg)
            return 2
        if args.file.lower().endswith((".html", ".htm")):
            text = re.sub(r"<[^>]+>", " ", text)
        p, w = check_text(text, args.min_chars)
        problems += p
        warns += w
    elif args.text:
        p, w = check_text(args.text, args.min_chars)
        problems += p
        warns += w

    code = 1 if problems else 0
    if args.as_json:
        print(json.dumps({"status": "pass" if code == 0 else "fail", "exit_code": code,
                          "problems": problems, "warnings": warns,
                          "assets_ok": not selfcheck()}, ensure_ascii=False, indent=2))
    else:
        for w in warns:
            print("⚠️ ", w)
        for pbm in problems:
            print("❌ ", pbm)
        print("质检结论：", "PASS（FAIL=0，可交付）" if code == 0 else "FAIL，先整改再交付")
    return code


if __name__ == "__main__":
    sys.exit(main())
