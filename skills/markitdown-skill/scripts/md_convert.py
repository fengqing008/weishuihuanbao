#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md_convert.py — MarkItDown 技能配套的零依赖 Markdown 转换与批量调度脚本。

仅使用 Python 标准库（argparse / csv / html.parser / os / sys / datetime / re），
把本地纯文本类文件（.txt / .log / .md 以外的 .csv / .html / .htm）转为 Markdown，
并支持按目录批量转换与运行日志落盘。用途：
  1. 未安装 markitdown 依赖时，对纯文本类文件做兜底转换；
  2. 对混合目录做调度与日志，输出可追溯的转换清单。

用法示例：
  python3 md_convert.py --input a.txt
  python3 md_convert.py --input ./docs --outdir ./out --log run.log
  python3 md_convert.py --input ./docs --ext txt,html,csv --dry-run

本脚本不联网、不写缓存、不修改输入文件。
"""
import argparse
import csv
import datetime as _dt
import os
import re
import sys
from html.parser import HTMLParser

SUPPORTED_EXT = (".txt", ".text", ".log", ".html", ".htm", ".csv")

# HTML 中被整体丢弃的标签（脚本、样式、页头页脚等与正文无关的节点）
DROP_TAGS = {"script", "style", "noscript", "head", "iframe", "svg", "template"}
# 行内强调标签到 Markdown 的映射
INLINE_MAP = {"b": "**", "strong": "**", "i": "*", "em": "*", "code": "`"}
# 块级标签，遇到时补空行，保证 Markdown 段落分离
BLOCK_TAGS = {
    "p", "div", "section", "article", "header", "footer", "main", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "tr",
    "blockquote", "pre", "br", "hr",
}


class _HtmlToMarkdown(HTMLParser):
    """把 HTML 片段转成 Markdown 的轻量解析器。

    覆盖标题、段落、列表、链接、粗斜体、代码、分隔线与简单表格，
    其余未知标签按纯文本穿透，避免内容丢失。
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._drop_depth = 0
        self._list_stack = []
        self._in_pre = False
        self._in_table = False
        self._row = []
        self._cell = None
        self._link = None

    # ---- 内部工具 ----
    def _newline(self, count=1):
        text = "".join(self.parts)
        if not text.endswith("\n" * count):
            self.parts.append("\n" * count)

    def _emit(self, s):
        self.parts.append(s)

    # ---- HTMLParser 回调 ----
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in DROP_TAGS:
            self._drop_depth += 1
            return
        if self._drop_depth:
            return
        adict = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newline(2)
            self._emit("#" * int(tag[1]) + " ")
        elif tag == "p":
            self._newline(2)
        elif tag == "br":
            self._emit("  \n")
        elif tag == "hr":
            self._newline(2)
            self._emit("---\n")
        elif tag in ("ul", "ol"):
            self._newline(1)
            self._list_stack.append(tag)
        elif tag == "li":
            self._newline(1)
            depth = max(1, len(self._list_stack))
            marker = "- " if (not self._list_stack or self._list_stack[-1] == "ul") else "1. "
            self._emit("  " * (depth - 1) + marker)
        elif tag == "pre":
            self._in_pre = True
            self._newline(2)
            self._emit("```\n")
        elif tag == "blockquote":
            self._newline(2)
            self._emit("> ")
        elif tag in INLINE_MAP:
            self._emit(INLINE_MAP[tag])
        elif tag == "a":
            self._link = adict.get("href", "")
        elif tag == "table":
            self._in_table = True
            self._newline(2)
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []
        elif tag in BLOCK_TAGS:
            self._newline(1)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in DROP_TAGS:
            if self._drop_depth:
                self._drop_depth -= 1
            return
        if self._drop_depth:
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newline(2)
        elif tag == "p":
            self._newline(2)
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._newline(2)
        elif tag == "pre":
            self._in_pre = False
            self._newline(1)
            self._emit("```\n")
            self._newline(2)
        elif tag in INLINE_MAP:
            self._emit(INLINE_MAP[tag])
        elif tag == "a":
            if self._link:
                self._emit("](%s)" % self._link)
            self._link = None
        elif tag == "table":
            self._in_table = False
            self._newline(2)
        elif tag in ("td", "th"):
            cell = re.sub(r"\s+", " ", "".join(self._cell or [])).strip()
            self._row.append(cell)
            self._cell = None
        elif tag == "tr":
            if self._row:
                self._emit("| " + " | ".join(self._row) + " |\n")
                if len([p for p in self.parts if p.startswith("| ")]) == 1:
                    self._emit("|" + " --- |" * len(self._row) + "\n")
                self._row = []

    def handle_data(self, data):
        if self._drop_depth:
            return
        if self._cell is not None:
            self._cell.append(data)
            return
        if self._in_pre:
            self._emit(data)
            return
        # 折叠 HTML 源码中的换行与多余空白
        self._emit(re.sub(r"[ \t\r\n]+", " ", data))

    def result(self):
        text = "".join(self.parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        return text.strip() + "\n"


def convert_txt(path):
    """纯文本文件转 Markdown：整体包成一段，保留原始换行。"""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    title = os.path.basename(path)
    return "# %s\n\n%s\n" % (title, raw.rstrip() + "\n")


def convert_html(path):
    """HTML 文件转 Markdown：丢弃脚本样式后提取正文结构。"""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    parser = _HtmlToMarkdown()
    parser.feed(raw)
    parser.close()
    return parser.result()


def convert_csv(path):
    """CSV 文件转 Markdown 表格：首行作表头，其余作数据行。"""
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(fh, dialect))
    if not rows:
        return "<!-- 空 CSV -->\n"
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    head = rows[0]
    out = ["| " + " | ".join(c.replace("|", "\\|") for c in head) + " |",
           "|" + " --- |" * width]
    for r in rows[1:]:
        out.append("| " + " | ".join(c.replace("|", "\\|") for c in r) + " |")
    title = os.path.basename(path)
    return "# %s\n\n%s\n" % (title, "\n".join(out))


CONVERTERS = {
    ".txt": convert_txt, ".text": convert_txt, ".log": convert_txt,
    ".html": convert_html, ".htm": convert_html, ".csv": convert_csv,
}


def convert_one(path, outdir=None):
    """转换单个文件，返回 (源路径, 产物路径, 状态)。"""
    ext = os.path.splitext(path)[1].lower()
    fn = CONVERTERS.get(ext)
    if fn is None:
        return (path, None, "跳过: 扩展名 %s 由 markitdown 主程序处理" % (ext or "无"))
    try:
        md = fn(path)
    except Exception as exc:  # noqa: BLE001 兜底，保证批量不中断
        return (path, None, "失败: %s" % exc)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(path))[0]
        dst = os.path.join(outdir, stem + ".md")
    else:
        dst = os.path.splitext(path)[0] + ".md"
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(md)
    return (path, dst, "成功")


def iter_files(root, exts):
    """按扩展名收集文件清单；root 为文件时直接判断。"""
    exts = set(e.lower() if e.startswith(".") else "." + e.lower() for e in exts)
    if os.path.isfile(root):
        return [root] if os.path.splitext(root)[1].lower() in exts else []
    found = []
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() in exts:
                found.append(os.path.join(base, name))
    return sorted(found)


def build_parser():
    ap = argparse.ArgumentParser(
        prog="md_convert.py",
        description="零依赖 Markdown 转换与批量调度（MarkItDown 技能配套脚本）",
    )
    ap.add_argument("--input", "-i", required=True,
                    help="输入文件或目录路径")
    ap.add_argument("--outdir", "-o", default=None,
                    help="产物输出目录；省略时与源文件同目录")
    ap.add_argument("--ext", default="txt,html,htm,csv",
                    help="批量模式下处理的扩展名，逗号分隔，默认 txt,html,htm,csv")
    ap.add_argument("--log", default=None,
                    help="运行日志落盘路径")
    ap.add_argument("--dry-run", action="store_true",
                    help="只列出待处理文件，不写产物")
    ap.add_argument("--version", action="version", version="md_convert.py 0.3.0")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not os.path.exists(args.input):
        print("[ERROR] 输入路径不存在: %s" % args.input, file=sys.stderr)
        return 2
    exts = [e.strip() for e in args.ext.split(",") if e.strip()]
    files = iter_files(args.input, exts)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["# md_convert 运行日志", "", "- 时间: %s" % stamp,
             "- 输入: %s" % args.input, "- 候选文件: %d" % len(files), ""]
    print("[INFO] 候选项 %d 个（%s）" % (len(files), ",".join(exts)))
    if not files:
        lines.append("未发现可处理的纯文本类文件。")
    ok = fail = 0
    for path in files:
        if args.dry_run:
            print("  [DRY] %s" % path)
            lines.append("- DRY  %s" % path)
            continue
        src, dst, status = convert_one(path, args.outdir)
        flag = "OK " if status == "成功" else "!! "
        print("  %s%s -> %s (%s)" % (flag, src, dst, status))
        lines.append("- %s%s -> %s (%s)" % (flag, src, dst, status))
        if status == "成功":
            ok += 1
        else:
            fail += 1
    lines += ["", "- 成功: %d" % ok, "- 未成功: %d" % fail]
    if args.log:
        with open(args.log, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("[INFO] 日志写入 %s" % args.log)
    print("[DONE] 成功 %d / 未成功 %d" % (ok, fail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
