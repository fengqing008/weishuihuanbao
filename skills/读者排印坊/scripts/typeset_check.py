#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读者排印坊 · 版式结构自检器（typeset_check.py）

仅使用 Python 标准库（argparse / json / os / re / sys），不联网、不依赖第三方包。
用于在交付前对成书 HTML 做版式层面的结构自检，把 G1–G7 门禁里可由静态扫描判定的项先过一遍。

检查项（对应质量门禁）：
  G1 正文字号 ≥ 五号（10.5pt）；
  G2 目次四要素：栏目 / 篇名 / 作者 / 页码（.toc-line 条目须含页码数字）；
  G3 页码起始为 1（检出 counter-reset 与 @page 页码约定）；
  G4 页眉奇偶镜像（同时存在 @page :left 与 @page :right）；
  G6 无缺字（不得出现 □ / tofu / U+FFFD 占位）；
  G7 未冒用刊号（不得出现 CN/ISSN 等刊号标识）。

退出码：0 = 通过（可含仅告警）；1 = 存在硬性不通过；2 = 用法或读取错误。

用法：
  python3 typeset_check.py --html book.html
  python3 typeset_check.py --html book.html --mode json
  python3 typeset_check.py --help
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

BODY_FONT_RE = re.compile(r"\.(?:col-body|article|body)[^{}]*\{[^{}]*font-size\s*:\s*([\d.]+)pt", re.I)
TOC_LINE_RE = re.compile(r"class\s*=\s*[\"'][^\"']*toc-line[^\"']*[\"']", re.I)
ISSUE_RE = re.compile(r"\b(ISSN|CN)\s?[\d\-Xx]{4,}", re.I)


def read_text(path: str) -> str:
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def check(html: str):
    passed, warn, fail = [], [], []

    if html.strip():
        passed.append(("文件非空", "%d 字符" % len(html)))
    else:
        fail.append(("文件非空", "HTML 为空，疑似导出异常（回退：重跑 book_builder.py）"))
        return passed, warn, fail

    sizes = [float(x) for x in BODY_FONT_RE.findall(html)]
    if sizes:
        mn = min(sizes)
        if mn < 10.5:
            fail.append(("G1 正文字号", "检出正文 font-size %.2fpt < 五号 10.5pt（降级：调回 10.5pt 重排）" % mn))
        else:
            passed.append(("G1 正文字号", "正文最小 font-size %.2fpt ≥ 10.5pt" % mn))
    else:
        warn.append(("G1 正文字号", "未解析到正文 font-size 声明，建议人工核对"))

    toc_lines = TOC_LINE_RE.findall(html)
    if toc_lines:
        missing = 0
        for m in re.finditer(r"class\s*=\s*[\"'][^\"']*toc-line[^\"']*[\"'][^>]*>(.*?)</", html, re.S | re.I):
            body = re.sub(r"<[^>]+>", "", m.group(1))
            if not re.search(r"\d", body):
                missing += 1
        if missing:
            fail.append(("G2 目次四要素", "%d 条目次缺页码（补救：两遍编译回填页码）" % missing))
        else:
            passed.append(("G2 目次四要素", "%d 条目均含页码" % len(toc_lines)))
        if ("作者" in html) or ("author" in html.lower()):
            passed.append(("G2 作者列", "检出作者信息位"))
        else:
            warn.append(("G2 作者列", "未见作者信息位，人工核对目次是否含作者"))
    else:
        warn.append(("G2 目次四要素", "未检出 .toc-line 条目，若为单篇样张可忽略"))

    if ("counter-reset" in html) or ("@page" in html and "page" in html):
        passed.append(("G3 页码", "检出页码计数约定（@page / counter-reset）"))
    else:
        warn.append(("G3 页码", "未见页码计数约定，人工核对页码起始与连续性"))

    has_left = bool(re.search(r"@page\s*:left", html, re.I))
    has_right = bool(re.search(r"@page\s*:right", html, re.I))
    if has_left and has_right:
        passed.append(("G4 页眉镜像", "同时存在 @page :left 与 :right，奇偶镜像成立"))
    elif has_left or has_right:
        fail.append(("G4 页眉镜像", "仅存在单侧页规则，奇偶镜像不成立（补救：补齐 :left/:right）"))
    else:
        warn.append(("G4 页眉镜像", "未见 @page :left/:right 规则，网页版单栏可忽略"))

    if ("□" in html) or ("tofu" in html.lower()) or ("\ufffd" in html):
        fail.append(("G6 无缺字", "检出 tofu / 替换符占位，字体链未覆盖中文字形（降级：补中文字体栈）"))
    else:
        passed.append(("G6 无缺字", "未检出缺字占位"))

    hits = ISSUE_RE.findall(html)
    if hits:
        fail.append(("G7 未冒用刊号", "检出 %d 处疑似刊号标识，须移除（红线：不得冒用刊名刊号）" % len(hits)))
    else:
        passed.append(("G7 未冒用刊号", "未检出刊号标识"))

    return passed, warn, fail


def main() -> int:
    ap = argparse.ArgumentParser(description="读者排印坊 · 版式结构自检器")
    ap.add_argument("--html", required=True, help="成书 HTML 路径")
    ap.add_argument("--mode", choices=["text", "json"], default="text", help="输出模式")
    ap.add_argument("--strict", action="store_true", help="严格模式：告警也视为不通过")
    args = ap.parse_args()

    if not os.path.isfile(args.html):
        print("ERROR: 文件不存在：%s" % args.html)
        return 2
    try:
        html = read_text(args.html)
    except Exception as e:  # noqa: BLE001
        print("ERROR: 读取失败：%s" % e)
        return 2

    passed, warn, fail = check(html)

    if args.mode == "json":
        print(json.dumps({"html": args.html, "status": "PASS" if not fail else "FAIL",
                          "passed": passed, "warnings": warn, "failed": fail},
                         ensure_ascii=False, indent=2))
    else:
        print("=== 版式结构自检 @ %s ===" % args.html)
        for k, v in passed:
            print("  [OK]   %s：%s" % (k, v))
        for k, v in warn:
            print("  [WARN] %s：%s" % (k, v))
        for k, v in fail:
            print("  [FAIL] %s：%s" % (k, v))
        print("结论：%s（通过 %d / 告警 %d / 失败 %d）"
              % ("PASS" if not fail else "FAIL", len(passed), len(warn), len(fail)))
    return 0 if (not fail and not (args.strict and warn)) else 1


if __name__ == "__main__":
    sys.exit(main())
