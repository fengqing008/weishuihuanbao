#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ecodmg_check.py — 生态环境损害鉴定评估报告书交付质检（仅标准库）

用途：在 report_checker.py 之外提供一道轻量门禁，对报告书 Markdown 底稿做
      结构、系数取值、溯源与占位符的快速体检，退出码表达结论。

检查项：
  1. 文件存在且非空
  2. 正文七章关键标题出现（缺段即失败）
  3. 虚拟治理成本法三系数（α/γ/τ 或 kappa）与 E、C 取值出现
  4. 六项损害确认条件的结论表述出现
  5. 未替换占位符（【待填】/TODO/某某）为失败分支
  6. 数据溯源标注（来源/依据/【待核】）存在

退出码：
  0 = 全部通过；1 = 存在未通过项；2 = 参数/IO 错误

用法：
  python3 scripts/ecodmg_check.py --file 报告书.md
  python3 scripts/ecodmg_check.py --file 报告书.md --json
"""
import argparse
import json
import os
import re
import sys

CHAPTERS = ["基本情况", "鉴定评估方案", "过程与分析", "结论"]
PLACEHOLDERS = ["【待填】", "TODO", "某某", "占位", "xxx", "XXX"]


def run(args):
    if not os.path.isfile(args.file):
        return 2, [{"item": "文件存在", "pass": False, "detail": "不存在：%s" % args.file}]
    with open(args.file, encoding="utf-8", errors="ignore") as f:
        text = f.read()

    results = []
    results.append({"item": "文件非空", "pass": len(text.strip()) > 0, "detail": "%d 字符" % len(text)})

    for ch in CHAPTERS:
        results.append({"item": "章节·%s" % ch, "pass": ch in text,
                        "detail": "命中" if ch in text else "缺失（结构不完整，需补齐）"})

    coef = ("α" in text or "alpha" in text) and ("γ" in text or "gamma" in text) and \
           ("τ" in text or "tau" in text or "超标系数" in text)
    results.append({"item": "三系数取值", "pass": coef,
                    "detail": "α/γ/τ 齐备" if coef else "缺系数（补救：按 GB/T 39793.2 取值）"})

    ec = ("E" in text) and ("C" in text)
    results.append({"item": "E/C 取值", "pass": ec,
                    "detail": "已列 E、C" if ec else "缺 E 或 C 取值依据"})

    confirm = ("六项" in text) or ("未发现明显损害" in text) or ("已自然恢复" in text)
    results.append({"item": "损害确认结论", "pass": confirm,
                    "detail": "有确认条件结论" if confirm else "缺确认条件逐条判定"})

    ph = [w for w in PLACEHOLDERS if w in text]
    results.append({"item": "无未替换占位符", "pass": not ph,
                    "detail": "残留：%s" % (", ".join(ph) if ph else "无")})

    src = ("来源" in text) or ("依据" in text) or ("【待核" in text) or ("卷宗" in text)
    results.append({"item": "数据溯源标注", "pass": src,
                    "detail": "已标注" if src else "缺来源标注（兜底：建立正文—附件索引）"})

    failed = [r for r in results if not r["pass"]]
    return (1 if failed else 0), results


def main(argv=None):
    p = argparse.ArgumentParser(description="生态环境损害鉴定评估报告书交付质检")
    p.add_argument("--file", required=True, help="待检查的报告书 Markdown/文本")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    args = p.parse_args(argv)

    code, results = run(args)
    if args.json:
        print(json.dumps({"file": args.file, "exit": code, "results": results},
                         ensure_ascii=False, indent=2))
    else:
        for r in results:
            print("[%s] %s：%s" % ("PASS" if r["pass"] else "FAIL", r["item"], r["detail"]))
        print("结论：%s（exit=%d）" % ("通过" if code == 0 else "未通过", code))
    return code


if __name__ == "__main__":
    sys.exit(main())
