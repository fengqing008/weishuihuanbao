#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读者排印坊 · 排印质检
对成书 HTML 逐条核对 G1–G7 门禁，输出 JSON 报告与终端表。

用法：
  python3 layout_check.py --html book.html --report qc.json [--strict]
退出码：0 全过；1 存在 🔴 阻断项。
"""
import argparse, json, re, sys
from pathlib import Path

CJK_FONTS = ("Noto Serif CJK", "Noto Sans CJK", "Songti", "SimSun", "SimHei", "Heiti", "Kaiti", "KaiTi")
FORBIDDEN = ["62-1118", "62-1190", "1005-1805", "1673-3274"]  # 期刊刊号（禁止冒用）


def _block(html: str, marker: str) -> str:
    """取 marker 之后的成对花括号块（括号配平，避开内部 } 干扰）。"""
    i = html.find(marker)
    if i < 0:
        return ""
    j = html.find("{", i)
    if j < 0:
        return ""
    depth = 0
    for k in range(j, len(html)):
        if html[k] == "{":
            depth += 1
        elif html[k] == "}":
            depth -= 1
            if depth == 0:
                return html[j:k + 1]
    return html[j:]


def check(html: str) -> list:
    rows = []

    def add(code, name, ok, detail):
        rows.append({"gate": code, "name": name, "pass": bool(ok), "detail": detail})

    # G1 正文≥五号
    m = re.search(r"--size-body:\s*([\d.]+)pt", html)
    pt = float(m.group(1)) if m else 0.0
    add("G1", "正文不小于五号(10.5pt)", pt >= 10.5, f"正文 {pt}pt")

    # G2 目次四要素（栏目行 + 篇名/作者/页码）
    entries = re.findall(r'<a class="toc-line"[^>]*>(.*?)</a>', html, re.S) or \
        re.findall(r'<div class="toc-line">(.*?)</div>', html, re.S) or \
        re.findall(r'<tr class="toc-entry">(.*?)</tr>', html, re.S)
    cols = re.findall(r'<div class="toc-col-title">', html) or \
        re.findall(r'<tr class="toc-column-row">', html)
    ok2 = bool(entries) and bool(cols) and all(
        ("toc-name" in e and ("toc-pg" in e or "toc-page" in e)) for e in entries)
    add("G2", "目次要素齐全(栏目/篇名/页码)", ok2,
        f"栏目 {len(cols)} 组 / 条目 {len(entries)} 条")

    # G3 页码回填且递增
    pages = []
    for e in entries:
        pm = re.search(r'toc-p(?:g|age)[^>]*>\s*([0-9]+|__PAGE__|—)\s*<', e)
        pages.append(pm.group(1) if pm else "")
    numeric = [int(p) for p in pages if p.isdigit()]
    placeholder = any(p in ("__PAGE__", "—", "") for p in pages)
    ok3 = (not placeholder) and len(numeric) == len(pages) \
        and numeric == sorted(numeric) and len(set(numeric)) == len(numeric)
    detail3 = "全部回填且递增" if ok3 else ("存在未回填占位" if placeholder else "页码缺失/重复/乱序")
    add("G3", "页码已回填、连续、无重复", ok3, detail3)

    # G4 页眉奇偶镜像（括号配平取块）
    r = _block(html, "@page article:right")
    l = _block(html, "@page article:left")
    ok4 = ("@top-left" in r and "article-title" in r and "@top-right" in r and "column-name" in r
           and "@top-right" in l and "article-title" in l and "@top-left" in l and "column-name" in l)
    add("G4", "页眉奇偶镜像(奇:篇名左/栏目右)", ok4, "镜像规则正确" if ok4 else "未检测到正确镜像规则")

    # G5 卷首语不分栏
    juan = re.findall(r'<article class="article ([^"]*)"[^>]*data-column="卷首语"', html)
    ok5 = bool(juan) and all("col-nobreak" in c for c in juan)
    add("G5", "卷首语标题/作者/出处不分栏", ok5, f"卷首语篇数 {len(juan)}")

    # G6 中文字体链覆盖
    ok6 = any(f in html for f in CJK_FONTS)
    add("G6", "中文字体链覆盖(防豆腐块)", ok6, "字体链含 CJK 字体" if ok6 else "字体链缺中文字体")

    # G7 未冒用刊号
    hit = [f for f in FORBIDDEN if f in html]
    add("G7", "未冒用《读者》刊号", not hit, ("命中禁项:" + ",".join(hit)) if hit else "未见刊号冒用")

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="读者排印坊·排印质检")
    ap.add_argument("--html", required=True)
    ap.add_argument("--report", default="qc.json")
    ap.add_argument("--strict", action="store_true", help="有红项即退出 1")
    a = ap.parse_args()

    html = Path(a.html).read_text(encoding="utf-8")
    rows = check(html)
    failed = [r for r in rows if not r["pass"]]

    print(f"{'门禁':<4}{'结果':<6}说明")
    for r in rows:
        print(f"{r['gate']:<4}{'通过' if r['pass'] else '阻断':<6}{r['name']} — {r['detail']}")
    print(f"\n小结：{len(rows)-len(failed)}/{len(rows)} 通过" + ("（存在阻断项）" if failed else "（全部通过）"))

    Path(a.report).write_text(json.dumps({"gates": rows, "failed": [r["gate"] for r in failed]},
                                         ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"报告已写入：{a.report}")
    return 1 if (failed and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
