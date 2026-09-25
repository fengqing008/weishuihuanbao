#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读者排印坊 · 版式样式生成器 v1.2
由参数派生 theme.css 与规格 JSON；支持联动 theme-factory 10 套主题换肤。

用法：
  python3 style_builder.py --json
  python3 style_builder.py --size 16k --columns 2 --out theme.css
  python3 style_builder.py --list-themes
  python3 style_builder.py --theme forest-canopy --out theme_forest.css
"""
import argparse, json, re, sys
from pathlib import Path

SIZES = {"16k": (185, 260), "a4": (210, 297), "32k": (130, 184)}
ASSETS = Path(__file__).resolve().parent.parent / "assets"

SPEC = {
    "font_song": '"Noto Serif CJK SC","Songti SC","STSong","SimSun",serif',
    "font_hei":  '"Noto Sans CJK SC","Heiti SC","STHeiti","SimHei",sans-serif',
    "font_kai":  '"Kaiti SC","STKaiti","KaiTi","Noto Serif CJK SC",serif',
    "body_pt": 10.5, "line_height": 1.55, "indent_em": 2,
    "margin_mm": {"top": 22, "bottom": 18, "inner": 18, "outer": 15},
    "min_body_pt": 10.5,
}


def load_themes():
    p = ASSETS / "themes.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _mix(c, tgt, k):
    a = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(tgt[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(a[i] * (1 - k) + b[i] * k) for i in range(3))


def apply_theme(css: str, theme: dict) -> str:
    """把主题 5 色写入 theme.css 的 :root 变量。"""
    pairs = {
        "--paper": theme["paper"], "--ink": theme["ink"], "--column": theme["column"],
        "--rule": theme["rule"], "--accent": theme["accent"],
        "--muted": _mix(theme["ink"], theme["paper"], 0.45),
    }
    for var, val in pairs.items():
        css = re.sub(rf"({re.escape(var)}:\s*)#[0-9A-Fa-f]{{6}}", rf"\g<1>{val}", css)
    return css


def build_css(size: str, columns: int, theme: str | None) -> str:
    css = (ASSETS / "theme.css").read_text(encoding="utf-8")
    w, h = SIZES[size]
    css = re.sub(r"size:\s*\d+mm \d+mm;", f"size: {w}mm {h}mm;", css)
    if columns != 2:
        css = css.replace("column-count: 2;", f"column-count: {columns};")
    if theme:
        themes = load_themes()
        if theme not in themes:
            raise SystemExit(f"未知主题：{theme}（可用：{', '.join(k for k in themes if not k.startswith('_'))}）")
        css = apply_theme(css, themes[theme])
    return css


def main() -> int:
    ap = argparse.ArgumentParser(description="读者排印坊·版式样式生成器")
    ap.add_argument("--size", default="16k", choices=list(SIZES))
    ap.add_argument("--columns", default="2", choices=["1", "2", "3"])
    ap.add_argument("--theme", help="theme-factory 主题名（换肤）")
    ap.add_argument("--list-themes", action="store_true", help="列出 10 套可用主题")
    ap.add_argument("--out", help="输出 theme.css 路径")
    ap.add_argument("--json", action="store_true", help="打印规格 JSON")
    a = ap.parse_args()

    if a.list_themes:
        themes = load_themes()
        for k, v in themes.items():
            if k.startswith("_"):
                continue
            print(f"{k:20s} {v['title']:26s} 底{v['paper']} 正文{v['ink']} 栏目{v['column']} 对比{v['ratio_ink_paper']}")
        return 0

    spec = dict(SPEC)
    spec["size"] = a.size
    spec["size_mm"] = SIZES[a.size]
    spec["columns"] = int(a.columns)
    spec["theme"] = a.theme or "default"

    if a.json or not a.out:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        return 0
    css = build_css(a.size, int(a.columns), a.theme)
    Path(a.out).write_text(css, encoding="utf-8")
    w, h = SIZES[a.size]
    print(f"OK theme.css -> {a.out}  size={w}x{h}mm columns={a.columns} theme={spec['theme']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
