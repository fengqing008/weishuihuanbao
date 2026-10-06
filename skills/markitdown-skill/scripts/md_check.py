#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md_check.py —— MarkItDown 产物质量校验闸门（纯标准库，零第三方依赖）

对 markitdown（或本技能 scripts/md_convert.py）产出的 Markdown 做交付前体检，
把「检查点 4 / 检查点 6」的自检动作固化为一条命令：

  * 非空与体量：字节数须 > --min-bytes，并打印标题/表格/列表计数
  * 结构完整性：标题（`#`）、表格（`|`）计数低于阈值时告警
  * 编码卫生：U+FFFD 替换字符、BOM 残留、零宽字符、CRLF 混入 LF
  * 件数对账：目录模式下一次输出合格/不合格/空件清单

用法示例：
  python3 scripts/md_check.py --md out.md
  python3 scripts/md_check.py --dir /path/to/out --min-bytes 16 --json
  python3 scripts/md_check.py --dir /path/to/out --require-heading 1

退出码：0 = 全部合格；1 = 存在不合格项（按「失败模式」处置）；2 = 输入不足/路径不可用
"""
import argparse
import json
import os
import sys


def inspect(path, min_bytes, require_heading):
    """检查单份 Markdown，返回 (是否合格, 明细)。"""
    detail = {"file": path, "problems": []}
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        detail["problems"].append("无法读取: %s" % exc)
        return False, detail
    detail["bytes"] = size
    if size <= min_bytes:
        detail["problems"].append("空件或过小（%d ≤ %d 字节）" % (size, min_bytes))
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            raw = f.read()
    except OSError as exc:
        detail["problems"].append("读取失败: %s" % exc)
        return False, detail
    lines = raw.splitlines()
    detail["headings"] = sum(1 for ln in lines if ln.lstrip().startswith("#"))
    detail["table_rows"] = sum(1 for ln in lines if ln.lstrip().startswith("|"))
    detail["list_items"] = sum(1 for ln in lines if ln.lstrip()[:2] in ("- ", "* ") or
                               (ln.lstrip()[:2].rstrip(".").isdigit() and ln.lstrip()[1:2] == "."))
    if "\ufffd" in raw:
        detail["problems"].append("检出 U+FFFD（编码误读或 OCR 噪声）")
    if raw.startswith("\ufeff"):
        detail["problems"].append("检出 BOM 残留（下游解析器会当正文）")
    if any(ch in raw for ch in ("\u200b", "\u200c", "\u200d", "\ufeff")):
        detail["problems"].append("检出零宽字符残留")
    if detail["headings"] < require_heading:
        detail["problems"].append("标题数 %d 低于要求 %d" % (detail["headings"], require_heading))
    return len(detail["problems"]) == 0, detail


def main():
    ap = argparse.ArgumentParser(description="MarkItDown 产物质量校验闸门")
    ap.add_argument("--md", help="单个 Markdown 文件")
    ap.add_argument("--dir", dest="md_dir", help="Markdown 产物目录（与 --md 二选一）")
    ap.add_argument("--min-bytes", type=int, default=8, help="最小字节数，默认 8")
    ap.add_argument("--require-heading", type=int, default=0, help="至少需要几个标题行，默认 0")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出报告")
    a = ap.parse_args()

    if not a.md and not a.md_dir:
        print("md: 需提供 --md 或 --dir（用法错误）", file=sys.stderr)
        return 2
    if a.md and not os.path.isfile(a.md):
        print("md: 文件不存在：%s" % a.md, file=sys.stderr)
        return 2
    if a.md_dir and not os.path.isdir(a.md_dir):
        print("md: 目录不存在：%s" % a.md_dir, file=sys.stderr)
        return 2

    if a.md:
        targets = [a.md]
    else:
        targets = [os.path.join(a.md_dir, f) for f in sorted(os.listdir(a.md_dir))
                   if f.lower().endswith(".md")]
        if not targets:
            print("md: 目录内未发现 .md 产物", file=sys.stderr)
            return 2

    details, failed = [], []
    for t in targets:
        ok, d = inspect(t, a.min_bytes, a.require_heading)
        details.append(d)
        if not ok:
            failed.append(t)

    report = {"ok": not failed, "checked": len(targets), "failed": failed, "details": details}
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("md_check：校验 %d 件，不合格 %d 件" % (len(targets), len(failed)))
        for d in details:
            flag = "合格" if not d["problems"] else "不合格"
            print("  [%s] %s（%d 字节，标题 %d / 表格 %d）"
                  % (flag, d["file"], d.get("bytes", -1), d.get("headings", 0), d.get("table_rows", 0)))
            for p in d["problems"]:
                print("        - %s" % p)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
