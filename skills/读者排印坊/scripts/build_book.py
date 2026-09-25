#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读者排印坊 · 一键成书（PDF 与网页版两套排版并行）

一条命令跑完七步：排正文 → 提页码 → 排前置 → 合并 PDF → 合成网页版 → 质检 → 列清单。

两套排版并行且互不干扰：
    PDF   双栏精排（@page margin + 固定 mm + 双栏）
    网页  单栏顺读（流式 + 百分比宽 + 屏幕留白，由 assets/web_theme.css 注入）

用法：
    python3 build_book.py --manifest manifest.json --name 江江手记_读者版式_52篇_v9
    python3 build_book.py --manifest manifest.json --name 样书 --auto-images auto_images_v7.json --skip-pdf
    python3 build_book.py --manifest manifest.json --name 试排 --sample 8     # 只取前 8 篇

参数：
    --manifest     稿件清单（含 articles[]：order/column/title/body，可选 theme）
    --auto-images  配图清单（{order: [{file, role, style, anchor}]}）
    --name         输出成品名（不含扩展名）
    --theme        版式主题（默认 default，见 theme-factory 的十套）
    --sample N     只排前 N 篇（试排用）
    --skip-pdf / --skip-web   只做其中一套
    --outdir       输出目录（默认清单所在目录）
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd, step):
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0
    tail = (r.stdout or r.stderr).strip().splitlines()
    print(f"  [{'OK ' if ok else 'FAIL'}] {step}  ({time.time()-t0:.0f}s)  {tail[-1] if tail else ''}")
    return ok


def page_of_title(pdf_path, articles):
    """从正文 PDF 提取各篇起始页（先见篇名者为准，逐篇单调递增）"""
    import pymupdf
    d = pymupdf.open(str(pdf_path))
    pages = [d[i].get_text() for i in range(d.page_count)]
    pm, last = {}, 1
    for a in articles:
        t = a["title"]
        found = None
        for i in range(last - 1, d.page_count):
            if t in pages[i]:
                found = i + 1; break
        if not found:
            for i in range(last - 1, d.page_count):
                if t[:8] in pages[i]:
                    found = i + 1; break
        pm[str(a.get("order"))] = found or last
        if found:
            last = found
    return pm, d.page_count


def main():
    ap = argparse.ArgumentParser(description="一键成书：PDF 双栏 + 网页版单栏")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--auto-images")
    ap.add_argument("--name", required=True)
    ap.add_argument("--theme", default=None, help="theme-factory 主题名（换肤）；缺省用内置读者经典")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--skip-pdf", action="store_true")
    ap.add_argument("--skip-web", action="store_true")
    ap.add_argument("--outdir")
    a = ap.parse_args()

    mf = Path(a.manifest).resolve()
    base = Path(a.outdir).resolve() if a.outdir else mf.parent
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    if a.sample:
        manifest["articles"] = sorted(manifest["articles"], key=lambda x: x.get("order", 0))[:a.sample]
    arts = manifest["articles"]
    sample_mf = base / f"_cmp_{a.name}.json"
    sample_mf.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    print(f"[1/7] 稿件 {len(arts)} 篇｜主题 {a.theme or '读者经典'}｜输出 {base}/{a.name}")

    # ---- 2) 正文（双栏）----
    body_html = base / f"_body_{a.name}.html"
    body_pdf = base / f"_body_{a.name}.pdf"
    if not a.skip_pdf:
        cmd = [sys.executable, str(HERE / "book_builder.py"), "--manifest", str(sample_mf),
               "--part", "body", "--out", str(body_html)]
        if a.theme: cmd += ["--theme", a.theme]
        if a.auto_images:
            cmd += ["--auto-images", str(Path(a.auto_images).resolve())]
        print("[2/7] 排正文（双栏）")
        if not run(cmd, "body HTML"): return 1
        if not run([sys.executable, str(HERE / "export_pdf.py"), "--html", str(body_html), "--out", str(body_pdf)], "body PDF"): return 1

        # ---- 3) 页码 ----
        print("[3/7] 提取页码")
        pm, npage = page_of_title(body_pdf, arts)
        pmf = base / f"_pagemap_{a.name}.json"
        pmf.write_text(json.dumps({"front_pages": 0, "orders": pm}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [OK ] 正文 {npage} 页｜页码 {len(pm)} 篇")

        # ---- 4) 前置（封面/目次/版权）----
        front_html = base / f"_front_{a.name}.html"
        front_pdf = base / f"_front_{a.name}.pdf"
        print("[4/7] 排前置（封面/扉页/目次/版权）")
        if not run([sys.executable, str(HERE / "book_builder.py"), "--manifest", str(sample_mf),
                    "--part", "front", "--pagemap", str(pmf), "--out", str(front_html)] + (["--theme", a.theme] if a.theme else []), "front HTML"): return 1
        if not run([sys.executable, str(HERE / "export_pdf.py"), "--html", str(front_html), "--out", str(front_pdf)], "front PDF"): return 1

        # ---- 5) 合并成书 ----
        book_pdf = base / f"{a.name}.pdf"
        print("[5/7] 合并成书 PDF")
        if not run([sys.executable, str(HERE / "export_pdf.py"), "--merge", str(front_pdf), str(body_pdf), "--out", str(book_pdf)], "merge PDF"): return 1
        try:
            import pymupdf, os
            d = pymupdf.open(str(book_pdf)); n = d.page_count; d.close()
            d = pymupdf.open(str(book_pdf))
            d.save(str(book_pdf) + ".tmp", garbage=4, deflate=True, deflate_images=True, clean=True); d.close()
            os.replace(str(book_pdf) + ".tmp", str(book_pdf))
            print(f"  [OK ] {book_pdf.name}  {n} 页  {book_pdf.stat().st_size/1048576:.1f} MB")
        except Exception as e:
            print(f"  [warn] PDF 重压缩跳过：{e}")
    else:
        body_html = base / f"_body_{a.name}.html"
        front_html = base / f"_front_{a.name}.html"
        for p, part in ((body_html, "body"), (front_html, "front")):
            cmd = [sys.executable, str(HERE / "book_builder.py"), "--manifest", str(sample_mf),
                   "--part", part, "--out", str(p)]
            if a.theme: cmd += ["--theme", a.theme]
            if a.auto_images and part == "body":
                cmd += ["--auto-images", str(Path(a.auto_images).resolve())]
            if part == "front":
                pmf = base / f"_pagemap_{a.name}.json"
                if pmf.exists(): cmd += ["--pagemap", str(pmf)]
            run(cmd, f"{part} HTML")

    if a.skip_pdf and not front_html.exists():
        cmd = [sys.executable, str(HERE / "book_builder.py"), "--manifest", str(sample_mf),
               "--part", "front", "--out", str(front_html)]
        if a.theme: cmd += ["--theme", a.theme]
        pmf = base / f"_pagemap_{a.name}.json"
        if pmf.exists(): cmd += ["--pagemap", str(pmf)]
        run(cmd, "front HTML")

    # ---- 6) 网页版（单栏，注入 web_theme.css）----
    web_html = base / f"{a.name}_网页版.html"
    if not a.skip_web:
        print("[6/7] 合成网页版（单栏）")
        comp = base / "build_selfcontained.py"
        if not comp.exists():
            comp.write_text(WEBSITE_BUILDER, encoding="utf-8")
        ok = run([sys.executable, str(comp), str(body_html), str(front_html), str(web_html)], "网页版 HTML")
        if not ok:
            print("  [hint] 可用 -h 查看 build_selfcontained 用法，或先跑 PDF 再合成")

    # ---- 7) 质检 ----
    print("[7/7] 版式质检")
    target = web_html if web_html.exists() else body_html
    if target.exists():
        run([sys.executable, str(HERE / "layout_check.py"), "--html", str(target)], f"G1–G7（{target.name}）")

    print("\n交付清单：")
    for f in (base / f"{a.name}.pdf", web_html):
        if f.exists():
            print(f"  {f.name}  {f.stat().st_size/1048576:.2f} MB")
    print(f"  过程件：_body_{a.name}.html / _front_{a.name}.html / _pagemap_{a.name}.json")
    return 0


WEBSITE_BUILDER = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 body/front HTML 合成单文件自包含网页版（注入 assets/web_theme.css）

用法：python3 build_selfcontained.py <body.html> <front.html> <out.html>
"""
import base64, io, re, pathlib, sys

body_p = pathlib.Path(sys.argv[1]).resolve()
front_p = pathlib.Path(sys.argv[2]).resolve()
out_p = pathlib.Path(sys.argv[3]).resolve()

front = front_p.read_text(encoding="utf-8")
body = body_p.read_text(encoding="utf-8")
css = re.search(r"<style>(.*?)</style>", front, re.S).group(1)
web = pathlib.Path("读者排印坊/assets/web_theme.css")
if web.exists():
    css += "\\n/* ===== 网页版样式（web_theme.css）===== */\\n" + web.read_text(encoding="utf-8").replace("</style>", "<\\/style>")


def inner(h):
    return re.search(r"<body>(.*)</body>", h, re.S).group(1)


html = ("<!DOCTYPE html>\\n<html lang=\\"zh-CN\\">\\n<head>\\n<meta charset=\\"utf-8\\">\\n"
        "<meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1\\">\\n"
        "<title>读者版式 · 网页版</title>\\n"
        f"<style>{css}</style>\\n</head>\\n<body>\\n{inner(front)}\\n{inner(body)}\\n</body>\\n</html>")

MAXW, Q = 860, 78


def embed(m):
    src = m.group(1)
    p = pathlib.Path(src.replace("file://", ""))
    if not p.exists():
        return m.group(0)
    try:
        from PIL import Image
        im = Image.open(p).convert("RGB")
        if im.width > MAXW:
            im = im.resize((MAXW, max(1, round(im.height * MAXW / im.width))), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=Q, optimize=True)
        return 'src="data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode("ascii") + '"'
    except Exception:
        ext = p.suffix.lower().lstrip("."); ext = "jpeg" if ext in ("jpg", "jpeg") else ext
        return 'src="data:image/' + ext + ';base64,' + base64.b64encode(p.read_bytes()).decode("ascii") + '"'


html, n = re.subn(r'src="([^"]+\\.(?:png|jpg|jpeg|webp))"', embed, html)
html = html.replace('class="toc-page" style="width:152mm"', 'class="toc-page"')
out_p.write_text(html, encoding="utf-8")
print(f"[OK] {out_p.name}  {out_p.stat().st_size/1024/1024:.2f} MB  内嵌图 {n} 张")
'''


if __name__ == "__main__":
    sys.exit(main())
