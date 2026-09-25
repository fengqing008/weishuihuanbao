#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""术语表校验 glossary_check.py

用途
  1. 校验术语表格式：`源词 = 译词`、`源词: 译词`、`源词<Tab>译词` 三种写法
  2. 检出同一源词的冲突译法、重复条目、源译相同的未翻译条目
  3. 统计条目数，并在给出源文本时统计术语命中数与未命中词

用法
  python3 glossary_check.py --file 术语表.md
  python3 glossary_check.py --file 术语表.md --source 原文.md --json

退出码
  0 校验通过
  1 检出格式或一致性问题，须回退修正后重试
  2 未解析到任何术语条目
  3 文件不可读
"""
import argparse
import json
import os
import re
import sys

SEPARATORS = ["\t", "=", "：", ":"]
COMMENT_PREFIXES = ("#", "//", ">")


def load_lines(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as fh:
        return fh.read().splitlines()


def split_pair(line):
    """把一行拆成 (源词, 译词)；无合法分隔符时返回 (None, None)。"""
    for sep in SEPARATORS:
        idx = line.find(sep)
        if idx > 0:
            return line[:idx].strip(), line[idx + len(sep):].strip()
    return None, None


def parse_glossary(lines):
    entries = []
    issues = []
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIXES) or line.startswith("|"):
            continue
        source, target = split_pair(line)
        if source is None:
            issues.append({"line": lineno, "kind": "缺分隔符",
                           "detail": "该行无 = 、: 或制表符分隔，解析失败"})
            continue
        if not source or not target:
            issues.append({"line": lineno, "kind": "空值",
                           "detail": "源词或译词为空"})
            continue
        if source == target:
            issues.append({"line": lineno, "kind": "源译相同",
                           "detail": "「%s」源词与译词一致，确认是否为无需翻译的专名" % source})
        entries.append({"line": lineno, "source": source, "target": target})
    return entries, issues


def check_consistency(entries):
    issues = []
    mapping = {}
    seen = set()
    for item in entries:
        key = item["source"]
        pair = (key, item["target"])
        if pair in seen:
            issues.append({"line": item["line"], "kind": "重复条目",
                           "detail": "「%s → %s」重复登记" % pair})
        seen.add(pair)
        if key in mapping and mapping[key]["target"] != item["target"]:
            issues.append({"line": item["line"], "kind": "译法冲突",
                           "detail": "「%s」已有译法「%s」，本行又给「%s」"
                                     % (key, mapping[key]["target"], item["target"])})
        else:
            mapping.setdefault(key, item)
    return issues, mapping


def check_source(source_text, mapping):
    """统计术语命中数与未命中词。"""
    hit = []
    for term in sorted(mapping, key=len, reverse=True):
        count = len(re.findall(re.escape(term), source_text))
        if count:
            hit.append({"term": term, "target": mapping[term]["target"], "count": count})
    return hit


def main():
    parser = argparse.ArgumentParser(description="术语表校验")
    parser.add_argument("--file", required=True, help="术语表文件路径")
    parser.add_argument("--source", default=None, help="源文本路径，用于统计命中")
    parser.add_argument("--json", action="store_true", help="以 JSON 形式输出")
    args = parser.parse_args()

    result = {"file": args.file, "exit_code": 0, "entries": 0,
              "issues": [], "hits": [], "messages": []}

    try:
        lines = load_lines(args.file)
    except OSError as exc:
        result["messages"].append("术语表不可读（%s）：核对路径与编码后重试。" % exc)
        result["exit_code"] = 3
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 3

    entries, fmt_issues = parse_glossary(lines)
    consistency_issues, mapping = check_consistency(entries)
    issues = fmt_issues + consistency_issues
    result["entries"] = len(entries)
    result["issues"] = issues
    result["messages"].extend("第 %d 行 %s：%s" % (i["line"], i["kind"], i["detail"])
                              for i in issues)

    if args.source:
        try:
            with open(args.source, "r", encoding="utf-8-sig", errors="ignore") as fh:
                source_text = fh.read()
        except OSError as exc:
            result["messages"].append("源文本不可读（%s）：跳过命中统计。" % exc)
            source_text = ""
        if source_text:
            hits = check_source(source_text, mapping)
            result["hits"] = hits
            result["hit_terms"] = len(hits)
            result["hit_total"] = sum(h["count"] for h in hits)
            if not hits:
                result["messages"].append("术语未在源文本中命中：核对术语表与源文语言是否匹配。")

    if not entries:
        result["exit_code"] = 2
        result["messages"].append("未解析到任何术语条目：核对分隔符与文件编码。")
    elif issues:
        result["exit_code"] = 1
        result["messages"].append("检出问题 %d 项：按报错行回退修正后重跑本校验。" % len(issues))
    else:
        result["messages"].append("术语表校验通过：可加载用于翻译环节。")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("file        %s" % result["file"])
        print("entries     %d" % result["entries"])
        print("issues      %d" % len(issues))
        if result.get("hits"):
            print("hit_terms   %d  hit_total %d" % (result["hit_terms"], result["hit_total"]))
            for item in result["hits"][:10]:
                print("  - %-20s → %-20s 出现 %d 次" % (item["term"], item["target"], item["count"]))
        for msg in result["messages"]:
            print("- " + msg)
        print("exit_code   %d" % result["exit_code"])
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
