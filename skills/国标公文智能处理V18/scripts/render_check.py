#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公文排版渲染验证 —— 将 docx 转为 PDF 再渲染成图片，用于"亲眼检查"排版效果。

移植自 anthropics/skills docx skill 的验证流程（soffice → pdftoppm）。
生成公文后，用它把 docx 渲染成 JPG，逐页检查字体/行距/缩进/表格是否符合 GB/T 9704-2012。

用法：
    python render_check.py 公文.docx [--out 输出目录] [--dpi 100]
输出：输出目录下 page-01.jpg ... page-NN.jpg（页码按位数补零）
"""
import argparse
import subprocess
import sys
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="渲染 docx 为图片，验证公文排版")
    ap.add_argument("input", help="输入 .docx 文件")
    ap.add_argument("--out", default=None, help="输出目录（默认：输入同目录下 _render/）")
    ap.add_argument("--dpi", type=int, default=100, help="渲染 DPI（默认 100，越高越清晰越慢）")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists() or src.suffix.lower() != ".docx":
        print(f"Error: 输入必须是 .docx 文件: {src}", file=sys.stderr)
        sys.exit(1)

    out = Path(args.out) if args.out else src.parent / "_render"
    out.mkdir(parents=True, exist_ok=True)

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("Error: 未找到 LibreOffice (soffice)", file=sys.stderr)
        sys.exit(1)

    # 1. docx -> pdf
    r = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(src)],
        capture_output=True, text=True, timeout=180,
    )
    pdf_path = out / (src.stem + ".pdf")
    if r.returncode != 0 or not pdf_path.exists():
        print(f"Error: PDF 转换失败: {r.stderr}", file=sys.stderr)
        sys.exit(1)

    # 2. pdf -> jpg
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        print("Error: 未找到 pdftoppm", file=sys.stderr)
        sys.exit(1)
    r2 = subprocess.run(
        [pdftoppm, "-jpeg", "-r", str(args.dpi), str(pdf_path), str(out / "page")],
        capture_output=True, text=True,
    )
    if r2.returncode != 0:
        print(f"Error: 渲染失败: {r2.stderr}", file=sys.stderr)
        sys.exit(1)

    imgs = sorted(out.glob("page-*.jpg"))
    print(f"渲染完成：共 {len(imgs)} 页，输出目录 {out}/")
    for im in imgs:
        print(f"  {im.name}")


if __name__ == "__main__":
    main()
