#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""caveman_check.py — 极简压缩交付前自检（仅标准库）。

对压缩稿做交付前静态自检：压缩率是否达标、代码围栏是否完整、
安全关键词是否被压缩、否定词/条件从句是否保留、客套前缀是否清除。
退出码：
  0 = 全部通过
  1 = 存在未达标项
  2 = 输入异常（文件缺失 / 参数错误）

用法：
  python3 caveman_check.py --help
  python3 caveman_check.py --normal normal.txt --compressed distilled.txt [--threshold 60] [--json]
"""
import argparse
import json
import os
import re
import sys

NEG_WORDS = ["not", "never", "unless", "禁止", "不可", "不得", "仅", "只在"]
SAFETY_WORDS = ["生产环境", "不可逆", "清空", "回滚", "备份", "生产库", "DROP", "DELETE"]
POLITE = ["当然", "好的", "没问题", "我很乐意", "很高兴", "当然可以"]


def read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="极简压缩交付前自检")
    ap.add_argument("--normal", required=True, help="正常版文本路径")
    ap.add_argument("--compressed", required=True, help="压缩稿文本路径")
    ap.add_argument("--threshold", type=float, default=60.0, help="目标压缩率上限(%%)，默认 60")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    normal = read(args.normal)
    comp = read(args.compressed)
    if normal is None or comp is None:
        miss = [p for p, v in [(args.normal, normal), (args.compressed, comp)] if v is None]
        msg = "输入文件缺失：%s" % ",".join(miss)
        if args.json:
            print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
        else:
            print("[ERR] " + msg)
        return 2

    n_len = len(normal)
    c_len = len(comp)
    ratio = (c_len / n_len * 100.0) if n_len else 100.0

    issues = []
    if n_len == 0:
        issues.append("正常版为空，压缩无意义 → 走正常模式")
    if ratio > args.threshold:
        issues.append("压缩率 %.1f%% 未达阈值 %.1f%%" % (ratio, args.threshold))

    if normal.count("```") != comp.count("```"):
        issues.append("代码围栏数量不一致，代码块可能被压缩")

    for w in SAFETY_WORDS:
        if w in normal and w not in comp:
            issues.append("安全关键词被压缩丢失：%s" % w)
    for w in NEG_WORDS:
        if w in normal and w not in comp:
            issues.append("否定/条件词被压缩丢失：%s" % w)
    if comp.strip().startswith(tuple(POLITE)):
        issues.append("开头存在客套前缀，须以实质内容起首")

    ok = len(issues) == 0
    result = {"ok": ok, "normal_chars": n_len, "compressed_chars": c_len,
              "ratio": round(ratio, 1), "threshold": args.threshold, "issues": issues}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print("极简压缩交付自检：%s（压缩率 %.1f%% / 阈值 %.1f%%）"
              % ("通过" if ok else "存在未达标项", ratio, args.threshold))
        for i in issues:
            print("  [WARN] " + i)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
