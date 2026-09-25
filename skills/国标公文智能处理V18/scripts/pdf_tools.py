#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公文/合同 PDF 处理工具 —— 合并、拆分、旋转、提取文字、提取表格。

依赖：pypdf + pymupdf（fitz），沙箱已预装。
移植自 anthropics/skills pdf skill 的核心操作（pypdf 合并/拆分/旋转 + 表格提取）。

用法：
    python pdf_tools.py merge a.pdf b.pdf c.pdf -o merged.pdf
    python pdf_tools.py split input.pdf -o outdir/
    python pdf_tools.py rotate input.pdf 90 -o rotated.pdf
    python pdf_tools.py text input.pdf [-o out.txt]
    python pdf_tools.py tables input.pdf [-o out.csv] [--page 1]
"""
import argparse
import csv
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def cmd_merge(args):
    writer = PdfWriter()
    for f in args.files:
        if not Path(f).exists():
            print(f"Error: 文件不存在 {f}", file=sys.stderr)
            sys.exit(1)
        reader = PdfReader(f)
        for page in reader.pages:
            writer.add_page(page)
    with open(args.output, "wb") as fh:
        writer.write(fh)
    print(f"合并完成：{len(args.files)} 个文件 -> {args.output}")


def cmd_split(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(args.input)
    for i, page in enumerate(reader.pages):
        w = PdfWriter()
        w.add_page(page)
        with open(out / f"page_{i + 1:03d}.pdf", "wb") as fh:
            w.write(fh)
    print(f"拆分完成：{len(reader.pages)} 页 -> {out}/")


def cmd_rotate(args):
    reader = PdfReader(args.input)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(int(args.angle))
        writer.add_page(page)
    with open(args.output, "wb") as fh:
        writer.write(fh)
    print(f"旋转完成（{args.angle}°）-> {args.output}")


def cmd_text(args):
    import fitz
    doc = fitz.open(args.input)
    text = "".join(page.get_text() for page in doc)
    doc.close()
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"文字提取完成：{len(text)} 字符 -> {args.output}")
    else:
        print(text)


def cmd_tables(args):
    import fitz
    doc = fitz.open(args.input)
    pages = [int(args.page)] if args.page is not None else range(len(doc))
    rows = []
    for pno in pages:
        page = doc[pno]
        for t in page.find_tables().tables:
            for row in t.extract():
                rows.append(row)
    doc.close()
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8-sig") as fh:
            csv.writer(fh).writerows(rows)
        print(f"表格提取完成：{len(rows)} 行 -> {args.output}")
    else:
        for row in rows:
            print("\t".join("" if c is None else str(c) for c in row))


def main():
    ap = argparse.ArgumentParser(description="公文/合同 PDF 处理工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_merge = sub.add_parser("merge", help="合并多个 PDF")
    p_merge.add_argument("files", nargs="+")
    p_merge.add_argument("-o", "--output", required=True)

    p_split = sub.add_parser("split", help="拆分 PDF 为单页")
    p_split.add_argument("input")
    p_split.add_argument("-o", "--output", required=True)

    p_rot = sub.add_parser("rotate", help="旋转页面")
    p_rot.add_argument("input")
    p_rot.add_argument("angle", help="旋转角度（90/180/270）")
    p_rot.add_argument("-o", "--output", required=True)

    p_text = sub.add_parser("text", help="提取文字")
    p_text.add_argument("input")
    p_text.add_argument("-o", "--output", default=None)

    p_tab = sub.add_parser("tables", help="提取表格（输出 CSV）")
    p_tab.add_argument("input")
    p_tab.add_argument("-o", "--output", default=None)
    p_tab.add_argument("--page", type=int, default=None, help="只提取指定页（1-based）")

    args = ap.parse_args()
    {"merge": cmd_merge, "split": cmd_split, "rotate": cmd_rotate,
     "text": cmd_text, "tables": cmd_tables}[args.cmd](args)


if __name__ == "__main__":
    main()
