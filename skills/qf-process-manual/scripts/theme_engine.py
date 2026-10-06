#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""theme_engine.py — 自包含主题引擎（theme-factory v1.1.0 内嵌版）

给任意生成的 HTML 做一次主题换肤，不依赖任何外部文件，可整份复制到其他技能目录使用。
色板为 theme-factory/themes/*.md 的数据快照，源文件改动后须同步本文件（见 verify_engine.py）。

用法：
    from theme_engine import apply, slots, list_themes
    html, mapping = apply(html, "ocean-depths")              # 浅色模式
    html, mapping = apply(html, "midnight-galaxy", "dark")   # 深色模式
"""
from __future__ import annotations

CN_NAME = {
    "ocean-depths": "深海之境", "sunset-boulevard": "落日大道", "forest-canopy": "森林之冠",
    "modern-minimalist": "现代极简", "golden-hour": "金色时刻", "arctic-frost": "极地霜华",
    "desert-rose": "沙漠玫瑰", "tech-innovation": "科技创新", "botanical-garden": "植物园",
    "midnight-galaxy": "午夜星河",
}

THEMES = {
    "ocean-depths":      ["#1a2332", "#2d8b8b", "#a8dadc", "#f1faee"],
    "sunset-boulevard":  ["#e76f51", "#f4a261", "#e9c46a", "#264653"],
    "forest-canopy":     ["#2d4a2b", "#7d8471", "#a4ac86", "#faf9f6"],
    "modern-minimalist": ["#36454f", "#708090", "#d3d3d3", "#ffffff"],
    "golden-hour":       ["#f4a900", "#c1666b", "#d4b896", "#4a403a"],
    "arctic-frost":      ["#d4e4f7", "#4a6fa5", "#c0c0c0", "#fafafa"],
    "desert-rose":       ["#d4a5a5", "#b87d6d", "#e8d5c4", "#5d2e46"],
    "tech-innovation":   ["#0066ff", "#00ffff", "#1e1e1e", "#ffffff"],
    "botanical-garden":  ["#4a7c59", "#f9a620", "#b7472a", "#f5f3ed"],
    "midnight-galaxy":   ["#2b1e3e", "#4a4e8f", "#a490c2", "#e6e6fa"],
}

FONTS = {
    "ocean-depths": ("DejaVu Sans Bold", "DejaVu Sans"),
    "sunset-boulevard": ("DejaVu Serif Bold", "DejaVu Sans"),
    "forest-canopy": ("FreeSerif Bold", "FreeSans"),
    "modern-minimalist": ("DejaVu Sans Bold", "DejaVu Sans"),
    "golden-hour": ("FreeSans Bold", "FreeSans"),
    "arctic-frost": ("DejaVu Sans Bold", "DejaVu Sans"),
    "desert-rose": ("FreeSans Bold", "FreeSans"),
    "tech-innovation": ("DejaVu Sans Bold", "DejaVu Sans"),
    "botanical-garden": ("DejaVu Serif Bold", "DejaVu Sans"),
    "midnight-galaxy": ("FreeSans Bold", "FreeSans"),
}

SLOT_TABLE = {
    "ocean-depths":      {"bg": "#f1faee", "ink": "#1a2332", "primary": "#2d8b8b", "accent": "#a8dadc"},
    "sunset-boulevard":  {"bg": "#fdf4e3", "ink": "#264653", "primary": "#e76f51", "accent": "#f4a261"},
    "forest-canopy":     {"bg": "#faf9f6", "ink": "#2d4a2b", "primary": "#7d8471", "accent": "#a4ac86"},
    "modern-minimalist": {"bg": "#ffffff", "ink": "#36454f", "primary": "#708090", "accent": "#d3d3d3"},
    "golden-hour":       {"bg": "#f7efe4", "ink": "#4a403a", "primary": "#c1666b", "accent": "#f4a900"},
    "arctic-frost":      {"bg": "#fafafa", "ink": "#4a6fa5", "primary": "#5c7dae", "accent": "#c0c0c0"},
    "desert-rose":       {"bg": "#f5ece3", "ink": "#5d2e46", "primary": "#6e4b41", "accent": "#d4a5a5"},
    "tech-innovation":   {"bg": "#ffffff", "ink": "#1e1e1e", "primary": "#0066ff", "accent": "#00ffff"},
    "botanical-garden":  {"bg": "#f5f3ed", "ink": "#4a7c59", "primary": "#b7472a", "accent": "#f9a620"},
    "midnight-galaxy":   {"bg": "#e6e6fa", "ink": "#2b1e3e", "primary": "#4a4e8f", "accent": "#a490c2"},
}

# 语义色（警示红 / 通过绿 / 提示黄）不随主题变化，保证"达标 / 预警"判断含义一致
SEMANTIC_KEEP = {
    "#c0392b", "#7d2b23", "#fff5f5", "#fdecea", "#e74c3c",
    "#6da33f", "#e6f2e2", "#2e7d32", "#e8f5e9",
    "#d99b1a", "#fff3cd", "#f7f8e6", "#a9ab63", "#8a5a00",
}
PURE = {"#fff", "#ffffff", "#fefefe", "#000", "#000000"}

CJK_SANS = '"Noto Sans CJK SC","Source Han Sans SC","PingFang SC","Microsoft YaHei",sans-serif'
CJK_SERIF = '"Noto Serif CJK SC","Source Han Serif SC","SimSun","Songti SC",serif'

VAR_KEYS = {
    "bg": ("bg", "background", "canvas", "page", "base"),
    "card": ("card", "surface", "panel", "box", "block", "white"),
    "line": ("line", "border", "divider", "rule", "stroke", "edge"),
    "ink": ("ink", "text", "fg", "font", "title", "dark", "main-text"),
    "sub": ("sub", "muted", "secondary", "gray", "grey", "hint", "desc"),
    "primary": ("primary", "accent", "main", "brand", "theme", "key", "link"),
}


def h2r(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def r2h(r):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(x)))) for x in r)


def luminance(h):
    c = [x / 255 for x in h2r(h)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def saturation(h):
    r, g, b = h2r(h)
    mx, mn = max(r, g, b), min(r, g, b)
    return 0 if mx == 0 else (mx - mn) / mx


def mix(a, b, t):
    return r2h([h2r(a)[i] * (1 - t) + h2r(b)[i] * t for i in range(3)])


def slots(slug, mode="light"):
    """返回主题的完整槽位：bg/card/line/ink/sub/primary/accent + 字体栈。"""
    if slug not in THEMES:
        raise KeyError("未知主题：%s（可选：%s）" % (slug, ", ".join(THEMES)))
    heading, body = FONTS[slug]
    if mode == "dark":
        cols = sorted(THEMES[slug], key=luminance)
        bg, ink = cols[0], cols[-1]
        rest = cols[1:-1] or [ink]
        primary = max(rest, key=lambda c: contrast(c, bg))
        accent = max([h for h in rest if h != primary] or rest, key=saturation)
        card, line, sub = mix(bg, ink, 0.10), mix(bg, ink, 0.22), mix(ink, bg, 0.40)
    else:
        tbl = SLOT_TABLE[slug]
        bg, ink, primary, accent = tbl["bg"], tbl["ink"], tbl["primary"], tbl["accent"]
        card, line, sub = "#ffffff", mix(bg, ink, 0.14), mix(ink, bg, 0.42)
    is_serif = "Serif" in body
    cjk_h = CJK_SERIF if "Serif" in heading else CJK_SANS
    cjk_b = CJK_SERIF if is_serif else CJK_SANS
    return {
        "bg": bg, "card": card, "line": line, "ink": ink, "sub": sub,
        "primary": primary, "accent": accent, "cn": CN_NAME[slug], "slug": slug,
        "heading_font": heading, "body_font": body,
        "heading_stack": "%s,%s,sans-serif" % (cjk_h, heading),
        "body_stack": "%s,%s,sans-serif" % (cjk_b, body),
    }


def build_color_map(html, s, keep=None):
    import re
    keep = {k.lower() for k in (keep or [])} | SEMANTIC_KEEP | PURE
    found = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", html)}
    mapping, used_primary = {}, False
    for hx in sorted(found):
        if hx in keep:
            continue
        sat, lum = saturation(hx), luminance(hx)
        if sat > 0.30:
            if not used_primary and contrast(hx, "#ffffff") > 1.6:
                mapping[hx] = s["primary"]; used_primary = True
            else:
                mapping[hx] = s["accent"]
        elif lum >= 0.92:
            mapping[hx] = s["bg"]
        elif lum >= 0.55:
            mapping[hx] = s["line"]
        elif lum <= 0.10:
            mapping[hx] = s["ink"]
        else:
            mapping[hx] = s["sub"]
    return mapping


def rewrite_root_vars(html, s):
    import re
    m = re.search(r":root\s*\{([^}]*)\}", html)
    decl = ";".join("--%s:%s" % (k, s[k]) for k in ("bg", "card", "line", "ink", "sub", "primary", "accent"))
    if not m:
        return html.replace("<style>", "<style>\n:root{%s}\n" % decl, 1) if "<style>" in html else html
    body, changed = m.group(1), False

    def repl(mm):
        nonlocal changed
        name = mm.group(1).lower()
        for slot, keys in VAR_KEYS.items():
            if any(k in name for k in keys):
                changed = True
                return "--%s:%s" % (mm.group(1), s[slot])
        return mm.group(0)

    newbody = re.sub(r"--([A-Za-z0-9_-]+)\s*:\s*[^;\n]+", repl, body)
    return (html[:m.start()] + ":root{%s}" % newbody + html[m.end():]) if changed else html


def apply(html, slug, mode="light", keep=None):
    """给 HTML 换肤。返回 (新 HTML, 色值映射表)。顺序：先映射色值，后注入变量。"""
    import re
    s = slots(slug, mode)
    mapping = build_color_map(html, s, keep)
    for old in sorted(mapping, key=len, reverse=True):
        html = re.sub(re.escape(old), mapping[old], html, flags=re.I)
    html = rewrite_root_vars(html, s)
    font_css = ("\n/* theme-factory 字体槽位（中文字体回退链已补齐） */\n"
                "body,td,th,p,li,div,span{font-family:%s}\n"
                "h1,h2,h3,h4,h5,th,.kpi-num,.metric{font-family:%s}\n") % (s["body_stack"], s["heading_stack"])
    if "</style>" in html:
        html = html.replace("</style>", font_css + "</style>", 1)
    return html, mapping


def list_themes():
    return [(k, CN_NAME[k], THEMES[k]) for k in CN_NAME]
