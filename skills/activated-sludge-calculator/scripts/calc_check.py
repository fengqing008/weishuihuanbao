#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""活性污泥工艺计算器自检器（calc_check.py）

对 activated-sludge-calculator 技能做结构与交付前自检：frontmatter、必备章节、
失败模式关键词覆盖、脚本与 references 资产、关键公式与参数存在性。

用法:
  python3 calc_check.py --dir activated-sludge-calculator
  python3 calc_check.py --dir activated-sludge-calculator --json

退出码: 0=通过, 1=存在问题需整改, 2=路径/用法错误
"""
import argparse
import json
import os
import sys

REQUIRED_SECTIONS = [
    "引用依据与溯源", "红线声明", "场景路由表", "能力边界",
    "降级路径与失败模式", "可交付物与输出规范", "版本沿革",
]
REQUIRED_ASSETS = [
    "scripts/activated_sludge_calculator.py",
    "references/case-library.md",
]
KEY_TERMS = ["Y_obs", "SRT_crit", "AOR", "SNDR", "SDNR", "膜面积", "物料平衡", "温度校正"]
FAIL_WORDS = ["失败模式", "fallback", "回退", "重试", "降级", "兜底", "异常",
              "错误处理", "失败分支", "边界条件", "补救", "断点续跑", "容错", "防御"]


def check(d):
    res = {"dir": d, "pass": [], "warn": [], "fail": []}
    md = os.path.join(d, "SKILL.md")
    if not os.path.isfile(md):
        res["fail"].append("缺 SKILL.md")
        res["ok"] = False
        return res
    text = open(md, encoding="utf-8", errors="ignore").read()

    if text.startswith("---") and text.count("---") >= 2:
        head = text.split("---", 2)[1]
        for k in ("name", "version", "description"):
            ok = (k + ":") in head
            (res["pass"] if ok else res["fail"]).append(
                f"frontmatter {'含' if ok else '缺'} {k}")
    else:
        res["fail"].append("缺 YAML frontmatter")

    miss = [s for s in REQUIRED_SECTIONS if s not in text]
    (res["fail"] if miss else res["pass"]).append(
        "缺章节: " + "、".join(miss) if miss else "必备章节齐全")

    hit = [w for w in FAIL_WORDS if w in text]
    (res["pass"] if len(hit) >= 10 else res["warn"]).append(
        f"失败模式关键词覆盖 {len(hit)}/{len(FAIL_WORDS)}")

    for p in REQUIRED_ASSETS:
        ap = os.path.join(d, p)
        (res["pass"] if os.path.exists(ap) else res["fail"]).append(
            f"{'存在' if os.path.exists(ap) else '缺'} {p}")

    term_hit = [t for t in KEY_TERMS if t in text]
    (res["pass"] if len(term_hit) >= 5 else res["warn"]).append(
        f"核心公式/参数词覆盖 {len(term_hit)}/{len(KEY_TERMS)}")

    if len(text) > 45000:
        res["warn"].append(f"SKILL.md {len(text)} 字符，超 45000 触发规范性惩罚")
    else:
        res["pass"].append(f"SKILL.md 长度 {len(text)} 字符（合规）")

    res["ok"] = len(res["fail"]) == 0
    return res


def main():
    ap = argparse.ArgumentParser(description="activated-sludge-calculator 自检器")
    ap.add_argument("--dir", required=True, help="技能目录")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    a = ap.parse_args()
    if not os.path.isdir(a.dir):
        print(json.dumps({"error": "目录不存在", "dir": a.dir}, ensure_ascii=False))
        return 2
    r = check(a.dir)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"=== activated-sludge-calculator 自检: {r['dir']} ===")
        for p in r["pass"]:
            print(f"  [PASS] {p}")
        for w in r["warn"]:
            print(f"  [WARN] {w}")
        for f in r["fail"]:
            print(f"  [FAIL] {f}")
        print("结论:", "通过" if r["ok"] else "未通过，需整改")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
