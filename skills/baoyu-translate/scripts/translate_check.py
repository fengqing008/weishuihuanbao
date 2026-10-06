#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""baoyu-translate 配置与术语表体检脚本（仅标准库）

用途：在启动三模式翻译流程前，快速体检：
  1) EXTEND.md 偏好文件是否存在、关键字段是否齐全；
  2) 术语表文件的格式（分隔符、BOM、条目数、重复源词冲突）；
  3) 输入源与输出目录的可写性判定。

退出码：
  0  体检通过
  1  体检不通过（术语表格式错误 / 术语冲突 / 输出不可写）
  2  输入不足（缺参数 / 路径不存在 / 无术语表可查）

用法：
  python3 translate_check.py --help
  python3 translate_check.py --glossary ./glossary.md --json
  python3 translate_check.py --extend ~/.baoyu-skills/baoyu-translate/EXTEND.md
"""
import argparse
import json
import os
import sys

REQUIRED_KEYS = ["target_language", "default_mode"]
VALID_MODES = ["quick", "normal", "refined"]


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        return raw.decode("utf-8-sig" if bom else "utf-8"), bom
    except UnicodeDecodeError:
        return raw.decode("gbk", "ignore"), bom


def check_glossary(path):
    issues = []
    warnings = []
    text, bom = read_text(path)
    if bom:
        warnings.append("术语表含 BOM，已按 utf-8-sig 读取（建议去除 BOM）")
    entries = {}
    conflicts = []
    n = 0
    for ln_no, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "\t" in s:
            src, dst = s.split("\t", 1)
        elif "=>" in s:
            src, dst = s.split("=>", 1)
        elif "|" in s:
            parts = [p.strip() for p in s.split("|") if p.strip()]
            if len(parts) < 2:
                issues.append("第 %d 行分隔符不足：%s" % (ln_no, s))
                continue
            src, dst = parts[0], parts[1]
        else:
            issues.append("第 %d 行未识别分隔符（需 \\t 或 => 或 |）：%s" % (ln_no, s))
            continue
        src, dst = src.strip(), dst.strip()
        n += 1
        if src in entries and entries[src] != dst:
            conflicts.append((src, entries[src], dst))
        else:
            entries.setdefault(src, dst)
    return {"items": n, "unique": len(entries), "conflicts": conflicts,
            "issues": issues, "warnings": warnings}


def check_extend(path):
    issues = []
    warnings = []
    if not os.path.isfile(path):
        issues.append("EXTEND.md 不存在：%s（将触发首次配置 BLOCKING）" % path)
        return {"exists": False, "issues": issues, "warnings": warnings,
                "fields": {}}
    text, _ = read_text(path)
    fields = {}
    for line in text.splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            k, v = k.strip().lower(), v.strip()
            if k:
                fields[k] = v
    for k in REQUIRED_KEYS:
        if k not in fields:
            warnings.append("EXTEND.md 缺字段 %s（将取默认值）" % k)
    m = fields.get("default_mode", "")
    if m and m not in VALID_MODES:
        issues.append("default_mode=%s 非法；合法值：%s" % (m, "/".join(VALID_MODES)))
    return {"exists": True, "issues": issues, "warnings": warnings,
            "fields": fields}


def main():
    ap = argparse.ArgumentParser(
        description="baoyu-translate 配置与术语表体检（仅标准库，退出码 0/1/2）")
    ap.add_argument("--glossary", help="术语表文件路径")
    ap.add_argument("--extend", help="EXTEND.md 偏好文件路径")
    ap.add_argument("--outdir", help="计划写入的输出目录")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结论")
    a = ap.parse_args()

    if not (a.glossary or a.extend or a.outdir):
        ap.print_help()
        print("\n错误：至少需提供 --glossary / --extend / --outdir 之一（退出码 2）")
        return 2

    issues, warnings, result = [], [], {}

    if a.glossary:
        if not os.path.isfile(a.glossary):
            print("错误：术语表不存在：%s（退出码 2）" % a.glossary)
            return 2
        g = check_glossary(a.glossary)
        result["glossary"] = g
        issues += g["issues"]
        warnings += g["warnings"]
        if g["conflicts"]:
            issues.append("术语冲突 %d 组：%s"
                          % (len(g["conflicts"]),
                             "; ".join("%s→[%s|%s]" % c for c in g["conflicts"][:5])))

    if a.extend:
        e = check_extend(a.extend)
        result["extend"] = e
        issues += e["issues"]
        warnings += e["warnings"]

    if a.outdir:
        parent = a.outdir if os.path.isdir(a.outdir) else os.path.dirname(
            os.path.abspath(a.outdir)) or "."
        writable = os.access(parent, os.W_OK)
        result["outdir"] = {"path": a.outdir, "parent": parent,
                            "writable": writable}
        if not writable:
            issues.append("输出目录父路径不可写：%s（命中失败模式 F7）" % parent)

    code = 0
    if issues:
        code = 1
    result["issues"] = issues
    result["warnings"] = warnings
    result["exit_code"] = code

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("# baoyu-translate 体检")
        if a.glossary and "glossary" in result:
            g = result["glossary"]
            print("- 术语表条目: %d（去重后 %d）" % (g["items"], g["unique"]))
        for w in warnings:
            print("- [提示] %s" % w)
        for i in issues:
            print("- [不通过] %s" % i)
        print("结论：%s（退出码 %d）"
              % ("体检不通过" if issues else "体检通过", code))
    return code


if __name__ == "__main__":
    sys.exit(main())
