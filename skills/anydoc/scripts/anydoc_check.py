#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anydoc_check.py —— anydoc 转换产物质检与对账（纯标准库，零第三方依赖）

用途：把「任意文档转 Markdown」的产物做交付前质检，四类检查一次跑完：
  1. 一一对应：源文件与 .md 产物按文件名干（stem）匹配，找缺件与多余件
  2. 非空校验：产物字节数须大于 --min-bytes（默认 8），拦截空产物
  3. 结构抽检：统计标题行（`#`）与表格行（`|`），结构全丢时告警
  4. 乱码探测：U+FFFD 替换字符、BOM（\\ufeff）、零宽字符残留

用法示例：
  python3 anydoc_check.py --source ./合同 --md-dir ./合同_md
  python3 anydoc_check.py --sample out.md --json
  python3 anydoc_check.py --source ./合同 --md-dir ./合同_md --min-bytes 32

退出码：0 = 全部通过；1 = 存在不合格项（需按降级路径处置）；2 = 输入不足/路径不可用
"""
import argparse
import json
import os
import sys

SUPPORTED = {
    ".doc", ".docx", ".docm", ".odt", ".rtf", ".epub", ".pdf",
    ".ppt", ".pps", ".pot", ".pptx", ".pptm", ".ppsx", ".ppsm", ".odp",
    ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods", ".csv",
}


def read_text(path):
    """按 UTF-8 宽松读取（errors=ignore），文件不可读时返回 None。"""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return None


def inspect_md(path, min_bytes):
    """检查单个 .md 产物，返回 (是否合格, 明细 dict)。"""
    detail = {"file": path, "problems": []}
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        detail["problems"].append("无法读取: %s" % exc)
        return False, detail
    detail["bytes"] = size
    if size <= min_bytes:
        detail["problems"].append("产物为空或过小（%d ≤ %d 字节）" % (size, min_bytes))
    text = read_text(path)
    if text is None:
        detail["problems"].append("文件不可读（权限或编码）")
        return False, detail
    detail["headings"] = sum(1 for ln in text.splitlines() if ln.lstrip().startswith("#"))
    detail["table_rows"] = sum(1 for ln in text.splitlines() if ln.lstrip().startswith("|"))
    if "\ufffd" in text:
        detail["problems"].append("检出 U+FFFD 替换字符（疑似编码误读）")
    if text.startswith("\ufeff"):
        detail["problems"].append("检出 BOM 残留")
    if any(ch in text for ch in ("\u200b", "\u200c", "\u200d")):
        detail["problems"].append("检出零宽字符残留")
    if detail["headings"] == 0 and detail["table_rows"] == 0 and size > 2000:
        detail["problems"].append("未见标题与表格结构（大产物需人工抽查）")
    return len(detail["problems"]) == 0, detail


def pair_sources(sources, md_dir):
    """源文件与产物配对，返回 (缺件列表, 多余列表, 配对列表)。"""
    stems = {}
    for f in os.listdir(md_dir):
        if f.lower().endswith(".md"):
            stems[os.path.splitext(f)[0]] = os.path.join(md_dir, f)
    missing, pairs = [], []
    src_stems = set()
    for s in sources:
        stem = os.path.splitext(os.path.basename(s))[0]
        src_stems.add(stem)
        if stem in stems:
            pairs.append((s, stems[stem]))
        else:
            missing.append(s)
    extra = [v for k, v in stems.items() if k not in src_stems]
    return missing, extra, pairs


def main():
    ap = argparse.ArgumentParser(description="anydoc 转换产物质检与对账")
    ap.add_argument("--source", help="源文档目录（与 --md-dir 配对使用）")
    ap.add_argument("--md-dir", help="Markdown 产物目录")
    ap.add_argument("--sample", help="单份 .md 抽查（与 --source 二选一）")
    ap.add_argument("--min-bytes", type=int, default=8, help="产物最小字节数，默认 8")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出报告")
    a = ap.parse_args()

    if not a.source and not a.sample:
        print("anydoc: 需提供 --sample 或 --source/--md-dir（用法错误）", file=sys.stderr)
        return 2
    if a.source and not (a.md_dir and os.path.isdir(a.md_dir)):
        print("anydoc: --md-dir 不存在或未提供", file=sys.stderr)
        return 2
    if a.sample and not os.path.isfile(a.sample):
        print("anydoc: --sample 文件不存在", file=sys.stderr)
        return 2

    report = {"ok": True, "checked": 0, "failed": [], "notes": []}

    if a.sample:
        ok, detail = inspect_md(a.sample, a.min_bytes)
        report["checked"] = 1
        report["details"] = [detail]
        if not ok:
            report["ok"] = False
            report["failed"].append(a.sample)
    else:
        sources = []
        for root, _dirs, files in os.walk(a.source):
            for f in files:
                if os.path.splitext(f)[1].lower() in SUPPORTED:
                    sources.append(os.path.join(root, f))
        if not sources:
            print("anydoc: 源目录未发现受支持格式文件", file=sys.stderr)
            return 2
        missing, extra, pairs = pair_sources(sources, a.md_dir)
        report["source_files"] = len(sources)
        report["missing"] = missing
        report["extra"] = extra
        if extra:
            report["notes"].append("产物目录存在无源文件对应的多余 .md（可能是历史遗留）")
        details = []
        for _src, md in pairs:
            ok, detail = inspect_md(md, a.min_bytes)
            details.append(detail)
            if not ok:
                report["failed"].append(md)
        report["checked"] = len(pairs)
        report["details"] = details
        if missing or report["failed"]:
            report["ok"] = False

    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("anydoc 质检：抽查/配对 %d 件，失败 %d 件" % (report["checked"], len(report["failed"])))
        for p in report.get("missing", []):
            print("  [缺件] %s" % p)
        for p in report["failed"]:
            print("  [不合格] %s" % p)
        for d in report.get("details", []):
            if d["problems"]:
                print("    %s → %s" % (d["file"], "；".join(d["problems"])))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
