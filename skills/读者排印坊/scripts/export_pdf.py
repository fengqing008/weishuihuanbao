#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读者排印坊 · PDF 出片与合并（WeasyPrint + PyMuPDF）
成书 HTML → 精排 PDF；或把前置册与正文册合并为整册。

用法：
  python3 export_pdf.py --html book.html --out book.pdf [--size 16k|a4]
  python3 export_pdf.py --html body.html --out body.pdf --measure pagemap.json   # 量各篇起始页（页码天然从1）
  python3 export_pdf.py --merge front.pdf body.pdf --out book.pdf                # 前置册 + 正文册合并
"""
import argparse, json, re, shutil, sys, tempfile
from pathlib import Path

SIZES = {"16k": "185mm 260mm", "a4": "210mm 297mm", "32k": "130mm 184mm"}


def render(html_path: str, out_pdf: str, size: str | None = None):
    from weasyprint import HTML, CSS
    stylesheets = []
    if size and size in SIZES:
        stylesheets.append(CSS(string=f"@page{{size:{SIZES[size]};}}"))
    tmp = Path(tempfile.gettempdir()) / "duzhe_export_tmp.pdf"   # ASCII 临时路径，避开中文写盘问题
    HTML(filename=str(Path(html_path).resolve())).write_pdf(str(tmp), stylesheets=stylesheets or None)
    shutil.move(str(tmp), str(Path(out_pdf)))
    return Path(out_pdf)


def measure(html_path: str, pdf_path: str) -> dict:
    """量取各篇起始页。优先 PDF 书签(outline)，兜底按标题文本搜索。"""
    import fitz
    doc = fitz.open(pdf_path)
    h1 = [t for t in doc.get_toc() if t[0] == 1]
    html = Path(html_path).read_text(encoding="utf-8")
    orders = re.findall(r'<article[^>]*data-order="(\d+)"', html)
    page, front = {}, 0
    if h1 and len(h1) >= len(orders):
        front = 0  # 正文册页脚示 counter(page)，与物理页同号
        for i, od in enumerate(orders):
            page[str(od)] = h1[i][2]
        src = "outline"
    else:
        titles = re.findall(r'<h1 class="article-title">(.*?)</h1>', html)
        pg = []
        for t in titles:
            found = 0
            for pno in range(doc.page_count):
                if doc[pno].search_for(t):
                    found = pno + 1
                    break
            pg.append(found)
        front = 0
        for i, od in enumerate(orders):
            page[str(od)] = pg[i] if i < len(pg) else 0
        src = "search"
    doc.close()
    return {"front_pages": front, "orders": page, "source": src}


def merge(parts, out_pdf: str):
    import pymupdf
    doc = pymupdf.open()
    for f in parts:
        doc.insert_pdf(pymupdf.open(f))
    doc.save(out_pdf)
    doc.close()
    return out_pdf


def main() -> int:
    ap = argparse.ArgumentParser(description="读者排印坊·PDF 出片与合并")
    ap.add_argument("--html", help="成书 HTML")
    ap.add_argument("--out", required=True, help="输出 PDF")
    ap.add_argument("--size", default=None, choices=list(SIZES))
    ap.add_argument("--measure", help="量各篇起始页并写入 JSON")
    ap.add_argument("--merge", nargs="+", help="合并多个 PDF（如 --merge front.pdf body.pdf）")
    ap.add_argument("--pdf-only", action="store_true", help="仅出 PDF（默认行为）")
    a = ap.parse_args()

    if a.merge:
        merge(a.merge, a.out)
        import pymupdf
        n = pymupdf.open(a.out).page_count
        print(f"OK merge -> {a.out}  共 {n} 页")
        return 0

    if not a.html:
        ap.error("需提供 --html 或 --merge")

    render(a.html, a.out, a.size)
    print(f"OK PDF -> {a.out}")
    if a.measure:
        pm = measure(a.html, a.out)
        Path(a.measure).write_text(json.dumps(pm, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK pagemap -> {a.measure}  前置页={pm['front_pages']}  映射={pm['orders']}  ({pm['source']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
