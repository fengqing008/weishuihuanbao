#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_docx_builder.py — 报告类文档 Word 生成器（嵌套大纲标题 + 一键目录）

通用母版：由各环保水务技能按需微调标题识别规则与字体点值。
依赖：pandoc、python-docx（沙箱已预装）；--pdf 另需 LibreOffice(soffice)。

用法：
  python3 report_docx_builder.py -i 报告.md -o 报告.docx [--pdf] [--no-toc]
                                 [--title 报告名称] [--toc-depth 3]
                                 [--body-font 仿宋_GB2312] [--heading-font 黑体]
                                 [--spec gbt|report]

行为：
  1) 调用 pandoc 将 Markdown 转 docx，标题自动获得 Heading 1/2/3 大纲级别；
  2) 后处理：为各级标题与正文设置中文字体、字号、行距、对齐；
  3) 插入可一键更新的目录域 TOC \\o "1-3"，Word/WPS 打开后“更新域”即生成目录；
  4) 页脚插入页码；可选 --pdf 同步导出 PDF。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

try:
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
except ImportError:
    sys.exit("缺少依赖 python-docx：pip install python-docx")

# ------- 字体与字号预设（report=通用报告；gbt=党政机关公文风格）
PRESETS = {
    "report": dict(title="黑体", h1="黑体", h2="黑体", h3="黑体",
                   body="宋体", s_title=18, s_h1=16, s_h2=14, s_h3=12, s_body=12,
                   lh_body=1.5),
    "gbt": dict(title="方正小标宋简体", h1="黑体", h2="楷体_GB2312", h3="仿宋_GB2312",
                body="仿宋_GB2312", s_title=22, s_h1=16, s_h2=16, s_h3=16, s_body=16,
                lh_body=None),  # gbt 用固定 28 磅行距
}


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("命令失败: %s\n%s" % (" ".join(cmd), r.stderr))
    return r.stdout


def _style(doc, name):
    for s in doc.styles:
        if s.name == name:
            return s
    ln = (name or "").lower()
    for s in doc.styles:
        if (s.name or "").lower() == ln:
            return s
    return None


def _set_font(run, cn_font, size_pt, bold=False):
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.name = "Times New Roman"
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), "Times New Roman")
    rf.set(qn("w:hAnsi"), "Times New Roman")
    rf.set(qn("w:eastAsia"), cn_font)


def md_to_raw(md, out_docx):
    """pandoc md -> docx（#/##/### 自动挂 Heading 1/2/3）。"""
    _run(["pandoc", md, "-f", "markdown-smart", "-o", out_docx, "--wrap=none"])


def add_toc(doc, depth=3, placeholder="右键→更新域 生成目录"):
    """在文档开头插入目录域段落（含 TOC 域 + dirty 标记）。"""
    body = doc.element.body
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("目　　录")
    _set_font(r, "黑体", 15, bold=True)

    tp = doc.add_paragraph()
    run = tp.add_run()
    fld_begin = OxmlElement("w:fldChar"); fld_begin.set(qn("w:fldCharType"), "begin")
    fld_begin.set(qn("w:dirty"), "true")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-%d" \\h \\z \\u' % depth
    fld_sep = OxmlElement("w:fldChar"); fld_sep.set(qn("w:fldCharType"), "separate")
    hint = OxmlElement("w:t"); hint.text = placeholder
    fld_end = OxmlElement("w:fldChar"); fld_end.set(qn("w:fldCharType"), "end")
    for el in (fld_begin, instr, fld_sep, hint, fld_end):
        run._element.append(el)
    # 目录后分页
    pb = doc.add_paragraph()
    pr = pb.add_run(); br = OxmlElement("w:br"); br.set(qn("w:type"), "page")
    pr._element.append(br)
    # 将三段移到文档最前，保持「目录标题→目录域→分页」顺序
    for el in (pb._element, tp._element, p._element):
        body.insert(0, el)
    # settings 开 updateFields，Word 打开时提示更新目录
    settings = doc.settings.element
    uf = settings.find(qn("w:updateFields"))
    if uf is None:
        uf = OxmlElement("w:updateFields"); uf.set(qn("w:val"), "true"); settings.append(uf)


def add_page_number(doc):
    sec = doc.sections[0]
    footer = sec.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.text = "— "
    run = p.add_run()
    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"
    e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end")
    for el in (b, it, e):
        run._element.append(el)
    p.add_run(" —")


def post_process(doc, spec):
    heads = {"Heading 1": (spec["h1"], spec["s_h1"], True),
             "Heading 2": (spec["h2"], spec["s_h2"], True),
             "Heading 3": (spec["h3"], spec["s_h3"], True),
             "Title": (spec["title"], spec["s_title"], True)}
    for para in doc.paragraphs:
        st = (para.style.name or "") if para.style else ""
        if st in heads:
            font, size, bold = heads[st]
            for run in para.runs:
                _set_font(run, font, size, bold)
            if st in ("Title", "Heading 1"):
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif st not in heads and not st.startswith("Heading"):
            for run in para.runs:
                _set_font(run, spec["body"], spec["s_body"], False)
            if spec["lh_body"]:
                para.paragraph_format.line_spacing = spec["lh_body"]
            if para.runs:
                para.paragraph_format.first_line_indent = Pt(spec["s_body"] * 2)
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            _set_font(run, spec["body"], spec["s_body"] - 1.5, False)


def main():
    ap = argparse.ArgumentParser(description="报告 Markdown → Word（嵌套大纲 + 一键目录）")
    ap.add_argument("-i", "--input", required=True, help="输入 Markdown 文件")
    ap.add_argument("-o", "--output", required=True, help="输出 docx 路径")
    ap.add_argument("--pdf", action="store_true", help="同时导出 PDF")
    ap.add_argument("--no-toc", action="store_true", help="不生成目录域")
    ap.add_argument("--title", default=None, help="覆盖文档大标题")
    ap.add_argument("--toc-depth", type=int, default=3)
    ap.add_argument("--spec", choices=["report", "gbt"], default="report")
    ap.add_argument("--body-font", default=None)
    ap.add_argument("--heading-font", default=None)
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        sys.exit("输入文件不存在：%s" % args.input)
    if not shutil.which("pandoc"):
        sys.exit("未找到 pandoc，请先安装")

    spec = dict(PRESETS[args.spec])
    if args.body_font:
        spec["body"] = args.body_font
    if args.heading_font:
        spec["h1"] = spec["h2"] = spec["h3"] = args.heading_font

    tmp = tempfile.mkdtemp(prefix="repdocx_")
    raw = os.path.join(tmp, "raw.docx")
    try:
        md_to_raw(args.input, raw)
        doc = Document(raw)
        post_process(doc, spec)
        if not args.no_toc:
            add_toc(doc, args.toc_depth)
        add_page_number(doc)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
        doc.save(args.output)
        print("OK docx -> %s" % args.output)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if args.pdf:
        outdir = os.path.dirname(os.path.abspath(args.output)) or "."
        ascii_dir = tempfile.mkdtemp(prefix="repdocxpdf_")
        shutil.copy(args.output, os.path.join(ascii_dir, "d.docx"))
        try:
            _run(["soffice", "--headless",
                  "-env:UserInstallation=file:///tmp/lo_profile",
                  "--convert-to", "pdf", "--outdir", ascii_dir,
                  os.path.join(ascii_dir, "d.docx")])
            pdf_src = os.path.join(ascii_dir, "d.pdf")
            pdf_dst = os.path.splitext(args.output)[0] + ".pdf"
            shutil.copy(pdf_src, pdf_dst)
            print("OK pdf  -> %s" % pdf_dst)
        finally:
            shutil.rmtree(ascii_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
