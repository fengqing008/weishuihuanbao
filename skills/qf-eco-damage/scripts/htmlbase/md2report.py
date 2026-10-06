#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2report.py —— Markdown 成稿 → 底座级单文件 HTML 成果页（v5.1.0）

v5.1.0 新增能力（2026-09-23）：
  · 图形围栏：```mermaid → 本地渲染内嵌 SVG（pretty-mermaid，无浏览器/无网络）；
    ```svg → 直接内嵌（任意绘图技能的 SVG 产物）
  · 通用代码围栏：```python 等 → 等宽代码块
  · 无本地渲染器的图形语言（dot/graphviz/plantuml/excalidraw/mindmap/bpmn/uml…）→ 源码卡 + 处置提示

v2.0 新增能力（2026-09-22）：
  · 数学公式：$...$ / $$...$$ 围栏 → KaTeX self-contained 渲染
  · 强化 callout：GitHub 风格 > [!info] / [!warn] / [!crit] / [!ok]
  · KPI 卡：:::kpi 围栏 → 多卡网格
  · 试题卡：:::q-card 围栏 → 题号/分值/难度/题干 三段式
  · 缺口卡：:::gap 围栏 → 缺口/影响/渠道 三列式
  · 自动 TOC：## 章节 ≥ 4 时自动挂目录
  · 来源角标扩展：识别 (P0 | 日期) 等格式

基础标注（沿用 v1.x）：
  · 来源角标 (P0)~(P4)        → <span class="src">P0</span>
  · 缺口标注 【待核：…】/【信息缺口：…】 → <span class="gap">…</span>
  · 引用块 > …                  → <div class="quote">（观点块）
  · 含「来源/参考」的末章       → 自动抽取为「参考来源」表

用法：
  python3 md2report.py 成稿.md -o 成果页.html
  python3 md2report.py 成稿.md -o 成果页.html --theme forest --audience 李云 --check --math
  python3 md2report.py --doc 成稿.md --list-themes
"""
import argparse
import base64
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from build_report import build_html, esc  # noqa
    from palettes import BY_ID, PALETTES  # noqa
    import render_diagrams as _rd  # v5.1.0：图形围栏渲染器（缺失时图形自动降级）
except Exception as e:  # pragma: no cover
    print("无法导入底座模块（需与 build_report.py / palettes.py 同目录）：%s" % e, file=sys.stderr)
    sys.exit(3)

SRC_RE = re.compile(r"[（(](P[0-4])[)）]")          # 兼容全角/半角括号
SRC_RE_LOOSE = re.compile(r"[（(](P[0-4])\b[^）)]*[）)]")  # 扩展：(P0 | 2025-11)
GAP_RE = re.compile(r"【([^】]+)】")
REF_TITLE_RE = re.compile(r"来源|参考|参考资料|信息来源")
NUM_LEAD = re.compile(r"^\s*(\d+[.、)]|[-*+])\s+")
# v3.0.4：来源章节识别（去序号后按首词匹配）+ 序号剥离
REF_HEAD_RE = re.compile(r"^(来源|参考|参考资料|信息来源)")
SEQ_STRIP_RE = re.compile(r"^[\s　]*(?:[一二三四五六七八九十百]+[、.．)）]|\d+[、.．)）]|[（(]\d+[）)])\s*")

# 围栏语法正则
FENCE_KPI = re.compile(r"^:::kpi\s*$")
FENCE_QCARD = re.compile(r"^:::q-card\s*$")
FENCE_GAP = re.compile(r"^:::\s*(?:gap|gaps)\s*$")
FENCE_END = re.compile(r"^:::\s*$")

FENCE_V3 = re.compile(r"^:::(bar|bento|timeline|phase|law|faq|tags|matrix|stat|bignum|icons|gallery)\b\s*$")
FENCE_CHART = re.compile(r"^:::chart(?:\s+(bar|donut|line|area))?(?:\s+(.+?))?\s*$")
FENCE_GALLERY = re.compile(r"^:::gallery(?:\s+(.*?))?\s*$")
IMG_RE = re.compile(r"^!\[(.*?)\]\(([^)]+)\)(?:\{([^}]*)\})?\s*$")
# v5.1.0 代码围栏（图形 / 通用代码）
FENCE_CODE = re.compile(r"^```([A-Za-z0-9_+.-]*)[ \t]*(.*)$")
DIAGRAM_LANGS = ("mermaid", "mmd", "svg", "dot", "graphviz", "gv", "plantuml", "puml",
                 "excalidraw", "mindmap", "bpmn", "uml", "network", "security", "vega")
DIAGRAM_COLORS = {}
MIME_MAP = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
            ".bmp": "image/bmp", ".tif": "image/tiff", ".tiff": "image/tiff"}


def _fence_rows(lines):
    return [ln.strip() for ln in lines if ln.strip()]


def parse_bar(lines):
    """:::bar 标签 | 数值原文 | 备注 → CSS 横向条形图（按最大值归一化）"""
    rows = []
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        if len(p) < 2:
            continue
        try:
            v = float(re.sub(r"[^\d.\-]", "", p[1]) or 0)
        except ValueError:
            v = 0.0
        rows.append((p[0], v, p[1], p[2] if len(p) > 2 else ""))
    mx = max([r[1] for r in rows], default=0) or 1
    out = ['<div class="bar-chart">']
    for lab, v, raw, note in rows:
        pct = max(2, int(round(v / mx * 100)))
        tip = (' <small>%s</small>' % esc(note)) if note else ""
        out.append('<div class="bar-row"><span class="bar-label">%s</span>'
                   '<span class="bar-track"><span class="bar-fill" style="width:%d%%"></span></span>'
                   '<span class="bar-val">%s%s</span></div>' % (esc(lab), pct, esc(raw), tip))
    out.append("</div>")
    return "".join(out)


def parse_bento(lines):
    """:::bento 跨列(1-3) | 标题 | 数值 | 描述（数值可省略）→ Bento 网格看板"""
    cells = []
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        span = 1
        if p and re.fullmatch(r"[1-3]", p[0]):
            span = int(p[0])
            p = p[1:]
        if not p:
            continue
        t = p[0]
        v, d = (p[1], p[2]) if len(p) >= 3 else ("", p[1])
        cls = "b-cell" + (" b-2" if span == 2 else " b-3" if span == 3 else "")
        cell = '<div class="%s"><b class="b-t">%s</b>' % (cls, inline(t))
        if v:
            cell += '<div class="b-v">%s</div>' % inline(v)
        if d:
            cell += '<div class="b-d">%s</div>' % inline(d)
        cells.append(cell + "</div>")
    return '<div class="bento">%s</div>' % "".join(cells)


def parse_timeline(lines):
    """:::timeline 时间 | 标题 | 说明 → 竖排时间轴"""
    out = ['<div class="timeline">']
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        tm = p[0] if p else ""
        tt = p[1] if len(p) > 1 else ""
        td = p[2] if len(p) > 2 else ""
        it = '<div class="tl-item">'
        if tm:
            it += '<div class="tl-time">%s</div>' % inline(tm)
        if tt:
            it += '<div class="tl-title">%s</div>' % inline(tt)
        if td:
            it += '<div class="tl-desc">%s</div>' % inline(td)
        out.append(it + "</div>")
    out.append("</div>")
    return "".join(out)


def parse_phase(lines):
    """:::phase 标题 | 说明 | 徽标 → 流程阶段卡（自动编号）"""
    out, no = [], 0
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        no += 1
        t = p[0] if p else ""
        d = p[1] if len(p) > 1 else ""
        meta = p[2] if len(p) > 2 else ""
        ph = '<div class="phase"><span class="phase-no">%d</span><div class="phase-main">' % no
        if t or meta:
            ph += '<div class="phase-headrow">'
            if t:
                ph += '<div class="phase-t">%s</div>' % inline(t)
            if meta:
                ph += '<span class="phase-meta">%s</span>' % inline(meta)
            ph += '</div>'
        if d:
            ph += '<div class="phase-d">%s</div>' % inline(d)
        out.append(ph + "</div></div>")
    return "".join(out)


def parse_law(lines):
    """:::law 《法规》条款 | 原文（或整行原文）→ 法条引用卡"""
    out = []
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        name = p[0] if p else ""
        text = p[1] if len(p) > 1 else ""
        if not text:
            text, name = name, ""
        out.append('<div class="law-card">%s<div class="law-text">%s</div></div>'
                   % (('<div class="law-name">%s</div>' % inline(name)) if name else "",
                      inline(text)))
    return "".join(out)


def parse_faq(lines):
    """:::faq 问题 | 答案 → 原生 details 折叠问答"""
    out = []
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        q = p[0] if p else ""
        a = p[1] if len(p) > 1 else ""
        out.append('<details class="faq"><summary>%s</summary><div class="faq-a">%s</div></details>'
                   % (inline(q), inline(a)))
    return "".join(out)


def parse_tags(lines):
    """:::tags 顿号/竖线/逗号分隔 → 标签 chips 行"""
    toks = []
    for s in _fence_rows(lines):
        for t in re.split(r"[、,，|]", s):
            t = t.strip()
            if t:
                toks.append(t)
    return '<div class="chips">%s</div>' % "".join("<i>%s</i>" % inline(t) for t in toks)


def parse_stat(lines):
    """:::stat 值|标签|副说明 → 关键数字巨幕（大号渐变数值卡）"""
    cells = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        parts = [p.strip() for p in s.split("|")]
        v = parts[0] if parts else ""
        l = parts[1] if len(parts) > 1 else ""
        d = parts[2] if len(parts) > 2 else ""
        m = re.match(r"^(.+?[\d.%])\s*([^\d.%\s].*)$", v)  # 拆数值与单位
        if m:
            vh = esc(m.group(1)) + "<small>%s</small>" % esc(m.group(2))
        else:
            vh = esc(v)
        cell = '<div class="stat-cell"><div class="stat-v">%s</div>' % vh
        if l:
            cell += '<div class="stat-l">%s</div>' % esc(l)
        if d:
            cell += '<div class="stat-d">%s</div>' % esc(d)
        cells.append(cell + "</div>")
    return '<div class="stat-row">%s</div>' % "".join(cells)


def parse_bignum(lines):
    """:::bignum 值 | 标签 → 巨幕大数（渐变超大数字，借鉴银发范本 clamp(72,15vw,150)）"""
    cells = []
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        v = p[0] if p else ""
        l = p[1] if len(p) > 1 else ""
        cells.append('<div class="bignum-cell"><div class="bignum-v">%s</div><div class="bignum-l">%s</div></div>'
                     % (esc(v), esc(l)))
    return '<div class="bignum">%s</div>' % "".join(cells)


def parse_icons(lines):
    """:::icons 图标 | 标题 | 描述 → 图标卡网格（借鉴地理教案范本 .ico）"""
    cells = []
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        ic = p[0] if p else ""
        t = p[1] if len(p) > 1 else ""
        d = p[2] if len(p) > 2 else ""
        cells.append('<div class="icon-cell"><span class="ico">%s</span><div>'
                     '<div class="ic-t">%s</div>%s</div></div>'
                     % (esc(ic), esc(t), ('<div class="ic-d">%s</div>' % esc(d)) if d else ""))
    return '<div class="icons">%s</div>' % "".join(cells)


def _fmt(x):
    """数值展示：整数千分位，非整数保留 1 位。"""
    if abs(x - round(x)) < 0.05:
        return "{:,}".format(int(round(x)))
    return "{:,.1f}".format(x)


def _num(s):
    """从「12.5%」「19,500 m3/d」这类文本里抽出第一个数值。"""
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", s or "")
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def parse_figure(path, cap="", mode="", base="", counter=None, ai=False):
    """v4.1：图片 base64 内嵌 + 自动图注编号；mode=inline 收窄；ai=True 加 AI 配图角标。"""
    fp = (path or "").strip()
    if not os.path.isabs(fp):
        fp = os.path.join(base or os.getcwd(), fp)
    if not os.path.exists(fp):
        return ('<div class="fig-missing">【图片未找到：%s】——路径按 Markdown 文件所在目录解析。</div>'
                % esc(path))
    ext = os.path.splitext(fp)[1].lower()
    size = os.path.getsize(fp)
    with open(fp, "rb") as fh:
        raw = fh.read()
    if ext == ".svg":
        data = "data:image/svg+xml;base64," + base64.b64encode(raw).decode()
    else:
        data = "data:%s;base64,%s" % (MIME_MAP.get(ext, "image/png"),
                                      base64.b64encode(raw).decode())
    if counter is not None:
        counter[0] += 1
        no = counter[0]
    else:
        no = 1
    note = ('<span class="fig-note">原图 %.1f MB，已内嵌为单文件，离线可看。</span>'
            % (size / 1048576.0)) if size > 1048576 else ""
    cls = "fig fig-inline" if mode == "inline" else "fig"
    if ai:
        cls += " fig-ai"
    aid = '<span class="fig-ai-tag">AI 配图</span>' if ai else ""
    return ('<figure class="%s"><img src="%s" alt="%s">'
            '<figcaption><b>图 %s</b>%s%s%s</figcaption></figure>'
            % (cls, data, esc(cap or "插图"), no, esc(cap), aid, note))


def parse_gallery(lines, base="", counter=None):
    """v5.0：:::gallery 标题 / 行「路径 | 图注」→ 2~3 列自适应图组（图片 base64 内嵌）。"""
    rows = _fence_rows(lines)
    title, items = "", []
    for r in rows:
        if "|" in r:
            p, cap = r.split("|", 1)
            items.append((p.strip(), cap.strip()))
        elif not items and not title:
            title = r
        else:
            items.append((r.strip(), ""))
    if not items:
        return ""
    cells = []
    for p, cap in items:
        fp = (p or "").strip()
        if not os.path.isabs(fp):
            fp = os.path.join(base or os.getcwd(), fp)
        if not os.path.exists(fp):
            cells.append('<figure class="g-cell"><div class="fig-missing">【图片未找到：%s】</div>'
                         '<figcaption>%s</figcaption></figure>' % (esc(p), esc(cap)))
            continue
        ext = os.path.splitext(fp)[1].lower()
        with open(fp, "rb") as fh:
            raw = fh.read()
        if ext == ".svg":
            data = "data:image/svg+xml;base64," + base64.b64encode(raw).decode()
        else:
            data = "data:%s;base64,%s" % (MIME_MAP.get(ext, "image/png"),
                                          base64.b64encode(raw).decode())
        if counter is not None:
            counter[0] += 1
            no = counter[0]
        else:
            no = 1
        cells.append('<figure class="g-cell"><img src="%s" alt="%s">'
                     '<figcaption><b>图 %s</b>%s</figcaption></figure>'
                     % (data, esc(cap or "插图"), no, esc(cap)))
    head = '<div class="gallery-title">%s</div>' % inline(title) if title else ""
    cls = "gallery g-3" if len(cells) >= 3 else "gallery"
    return '<div class="%s">%s<div class="g-grid">%s</div></div>' % (cls, head, "".join(cells))


_DIAGRAM_HINTS = {
    "dot": "graphviz 技能", "graphviz": "graphviz 技能", "gv": "graphviz 技能",
    "plantuml": "uml / bpmn / network 技能", "puml": "uml / bpmn / network 技能",
    "excalidraw": "excalidraw-diagram 技能", "mindmap": "mindmap 技能",
    "bpmn": "bpmn 技能", "uml": "uml 技能", "network": "network 技能",
    "security": "security 技能", "vega": "vega 技能",
}


def _diagram_fallback(lang, code, reason, cap=""):
    """无本地渲染器的图形语言 → 源码卡 + 处置提示（不静默丢内容）。"""
    hint = _DIAGRAM_HINTS.get(lang, "对应绘图技能")
    title = ('<div class="df-head"><b>%s</b></div>' % esc(cap)) if cap else ""
    head = ('<div class="df-head"><span class="df-tag">%s</span>'
            '本图未渲染：%s。沙箱无该语言的本地渲染器，可用 %s 导出 SVG/PNG 后，'
            '以 <code>```svg</code> 围栏或 <code>![图注](x.svg)</code> 贴入本页。</div>'
            % (esc((lang or "").upper()), esc(reason or "缺少本地渲染器"), esc(hint)))
    return ('<div class="diagram-fallback">%s%s<pre><code>%s</code></pre></div>'
            % (title, head, esc(code)))


_CODE_FENCE_ALIASES = {
    # v9.0.0：反引号围栏与冒号围栏等价——```timeline 与 :::timeline 同效，
    # 使各技能文档（如 travel-planner）既有的 ```timeline 写法可直接渲染为时间轴与画板。
    "timeline": "parse_timeline", "bar": "parse_bar", "bento": "parse_bento",
    "phase": "parse_phase", "law": "parse_law", "faq": "parse_faq",
    "tags": "parse_tags", "matrix": "parse_matrix", "stat": "parse_stat",
    "bignum": "parse_bignum", "icons": "parse_icons", "kpi": "parse_kpi_grid",
    "gap": "parse_gap_block", "gaps": "parse_gap_block",
}


def parse_code_fence(lang, caption, code, base="", counter=None):
    """v5.1.0：```lang 围栏。
    图形语言 → mermaid 本地渲染 / svg 直嵌；无渲染器 → 源码卡；其他语言 → 等宽代码块。"""
    lang = (lang or "").strip().lower()
    code = (code or "").rstrip("\n")
    if not lang and not code.strip():
        return None

    _fn_name = _CODE_FENCE_ALIASES.get(lang)
    if _fn_name:
        _fn = globals().get(_fn_name)
        if _fn is not None:
            try:
                return _fn(code.split("\n"))
            except Exception:  # 解析异常降级为等宽代码块，不阻断整篇渲染
                return '<pre class="code"><code>%s</code></pre>' % esc(code)

    is_diagram = lang in DIAGRAM_LANGS
    svg, reason = None, ""

    if lang in ("mermaid", "mmd"):
        try:
            svg, reason = _rd.render_svg(code, DIAGRAM_COLORS)
        except Exception as e:  # 渲染异常不得阻断整篇渲染
            svg, reason = None, "渲染异常：%s" % e
    elif lang == "svg":
        if code.lstrip().startswith("<svg"):
            svg = code
        else:
            reason = "未识别到 <svg> 根元素"

    if svg is not None:
        data = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()
        if counter is not None:
            counter[0] += 1
            no = counter[0]
        else:
            no = 1
        return ('<figure class="fig fig-diagram"><img src="%s" alt="%s">'
                '<figcaption><b>图 %s</b>%s</figcaption></figure>'
                % (data, esc(caption or "图形"), no, esc(caption)))

    if is_diagram:
        return _diagram_fallback(lang, code, reason, caption)

    return '<pre class="code"><code>%s</code></pre>' % esc(code)


def _bar_svg(rows, title=""):
    W, H, PL, PR, PT, PB = 760, 360, 56, 22, 46, 80
    pw, ph = W - PL - PR, H - PT - PB
    mx = max(v for _, _, v in rows) or 1.0
    n = len(rows)
    slot = pw / n
    bw = min(slot * 0.56, 74)
    base = PT + ph
    parts = []
    for k in range(3):
        y = PT + ph * k / 2.0
        parts.append('<line class="c-grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>' % (PL, y, W - PR, y))
        parts.append('<text class="c-lab" x="%d" y="%.1f" text-anchor="end">%s</text>'
                     % (PL - 12, y + 4, _fmt(mx * (2 - k) / 2.0)))
    for idx, (lab, raw, v) in enumerate(rows):
        h = max(ph * v / mx, 2)
        x = PL + slot * idx + (slot - bw) / 2.0
        y = base - h
        parts.append('<rect class="c-bar" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="5" '
                     'fill="var(--accent)" fill-opacity="%.2f"><title>%s：%s</title></rect>'
                     % (x, y, bw, h, max(0.3, 1 - idx * 0.13), esc(lab), esc(raw)))
        parts.append('<text class="c-val" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                     % (x + bw / 2.0, y - 7, esc(raw[:14])))
        short = lab if len(lab) <= 7 else lab[:6] + "…"
        parts.append('<text class="c-lab" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                     % (x + bw / 2.0, base + 22, esc(short)))
    svg = ('<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>'
           % (W, H, esc(title or "柱状对比图"), "".join(parts)))
    return svg, ""


def _donut_svg(rows, title=""):
    import math
    S, cx, cy, r, sw = 340, 170, 168, 114, 46
    total = sum(v for _, _, v in rows) or 1.0
    circ = 2 * math.pi * r
    off, parts = 0.0, []
    for idx, (lab, raw, v) in enumerate(rows):
        seg = circ * v / total
        parts.append('<circle class="donut-seg" cx="%d" cy="%d" r="%d" fill="none" stroke="var(--accent)" '
                     'stroke-opacity="%.2f" stroke-width="%d" stroke-dasharray="%.2f %.2f" '
                     'stroke-dashoffset="%.2f" transform="rotate(-90 %d %d)">'
                     '<title>%s：%s（%.1f%%）</title></circle>'
                     % (cx, cy, r, max(0.24, 1 - idx * 0.13), sw, seg, circ - seg, -off,
                        cx, cy, esc(lab), esc(raw), 100.0 * v / total))
        off += seg
    parts.append('<text class="c-sum" x="%d" y="%d" text-anchor="middle">%s</text>'
                 % (cx, cy + 4, esc(_fmt(total))))
    parts.append('<text class="c-sum-lab" x="%d" y="%d" text-anchor="middle">合计</text>'
                 % (cx, cy + 28))
    svg = ('<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>'
           % (S, S, esc(title or "构成占比图"), "".join(parts)))
    legend = '<div class="chart-legend">' + "".join(
        '<span><i style="opacity:%.2f"></i>%s %s（%.1f%%）</span>'
        % (max(0.24, 1 - i * 0.13), esc(lab), esc(raw), 100.0 * v / total)
        for i, (lab, raw, v) in enumerate(rows)) + '</div>'
    return svg, legend


def _line_svg(rows, title="", area=False):
    W, H, PL, PR, PT, PB = 760, 360, 56, 26, 46, 80
    pw, ph = W - PL - PR, H - PT - PB
    vals = [v for _, _, v in rows]
    mx = max(vals) if vals else 1.0
    lo = min(0.0, min(vals) if vals else 0.0)
    rng = (mx - lo) or 1.0
    n = len(rows)
    step = pw / (n - 1) if n > 1 else pw
    base = PT + ph
    parts = []
    for k in range(3):
        y = PT + ph * k / 2.0
        parts.append('<line class="c-grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>' % (PL, y, W - PR, y))
        parts.append('<text class="c-lab" x="%d" y="%.1f" text-anchor="end">%s</text>'
                     % (PL - 12, y + 4, _fmt(mx - (mx - lo) * k / 2.0)))
    pts = []
    for idx, (lab, raw, v) in enumerate(rows):
        x = PL + step * idx
        y = base - ph * (v - lo) / rng
        pts.append((x, y, lab, raw))
    poly = " ".join("%.1f,%.1f" % (x, y) for x, y, _, _ in pts)
    if area and pts:
        ar = poly + " %.1f,%.1f %.1f,%.1f" % (pts[-1][0], base, pts[0][0], base)
        parts.append('<polygon points="%s" fill="var(--accent)" fill-opacity="0.16"/>' % ar)
    parts.append('<polyline points="%s" fill="none" stroke="var(--accent)" stroke-width="3" '
                 'stroke-linejoin="round" stroke-linecap="round"/>' % poly)
    for x, y, lab, raw in pts:
        parts.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="var(--accent)">'
                     '<title>%s：%s</title></circle>' % (x, y, esc(lab), esc(raw)))
        short = lab if len(lab) <= 7 else lab[:6] + "…"
        parts.append('<text class="c-lab" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                     % (x, base + 22, esc(short)))
    svg = ('<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>'
           % (W, H, esc(title or ("面积趋势图" if area else "趋势折线图")), "".join(parts)))
    return svg, ""


def _area_svg(rows, title=""):
    return _line_svg(rows, title, area=True)


def parse_chart(lines, kind="bar", title=""):
    """v4.1 图表围栏：行格式「标签 | 值」，值可为 1,234 / 12.5% / 19500 m3/d。"""
    rows = []
    for s in _fence_rows(lines):
        p = [x.strip() for x in s.split("|")]
        lab = p[0] if p else ""
        raw = p[1] if len(p) > 1 else ""
        v = _num(raw)
        if lab and v is not None:
            rows.append((lab, raw or str(v), v))
    if not rows:
        return ""
    if kind == "donut":
        svg, legend = _donut_svg(rows, title)
    elif kind == "line":
        svg, legend = _line_svg(rows, title)
    elif kind == "area":
        svg, legend = _area_svg(rows, title)
    else:
        svg, legend = _bar_svg(rows, title)
    head = ('<div class="chart-title">%s</div>' % esc(title)) if title else ""
    note = ('<p class="chart-note">按各行「标签 | 值」渲染；鼠标悬停可见原值。</p>'
            if kind == "bar" else "")
    return '<div class="chart">%s%s%s%s</div>' % (head, svg, legend, note)


def parse_matrix(lines):
    """:::matrix 围栏内为 Markdown 表格 → sticky 首列对比矩阵（横向滚动）"""
    tbl = split_table(lines, wrap_long=False)
    return ('<div class="matrix-wrap"><div class="matrix-scroll">%s</div>'
            '<div class="scroll-hint">← 可左右滑动查看全部列（手机端在框内滑动，页面不动）</div></div>' % tbl)



CALLOUT_RE = re.compile(r"^>\s*\[!(\w+)\]\s*(.*)$")


def inline(t):
    """行内语义着色（先转义，再加标签）。"""
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", t)  # 去外链保文本
    # 来源角标扩展（先匹配宽松，再回退严格）
    t = SRC_RE_LOOSE.sub(lambda m: '<span class="src">%s</span>' % m.group(1), t)
    t = SRC_RE.sub(r'<span class="src">\1</span>', t)
    # 缺口标注
    t = re.sub(r"【([^】]+)】", r'<span class="gap">\1</span>', t)
    # 行内数学公式 $...$ （非贪婪、不跨行）
    t = re.sub(r"(?<![\\$])\$([^$\n]+?)\$(?!\$)", r'<span class="math-inline">\1</span>', t)
    return t


def split_table(lines, wrap_long=True):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    head, body = rows[0], rows[1:]
    th = "".join('<th scope="col">%s</th>' % inline(c) for c in head)
    trs = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in body)
    inner = ('<div class="tablewrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
             % (th, trs))
    if wrap_long and len(body) >= 12:
        return ('<div class="table-scroll">%s</div>'
                '<p class="chart-note">共 %d 行，表头随滚动固定。</p>' % (inner, len(body)))
    return inner


def parse_kpi_grid(lines):
    """解析 :::kpi 围栏，渲染为 KPI 卡网格。
    每行格式：主标签 | 大数字 | 单位 | 趋势/说明
    """
    items = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(":::"):
            continue
        parts = [p.strip() for p in s.split("|")]
        if len(parts) < 2:
            continue
        items.append(parts)
    cards = []
    for parts in items:
        label = esc(parts[0])
        value = esc(parts[1]) if len(parts) > 1 else ""
        unit = esc(parts[2]) if len(parts) > 2 else ""
        note = esc(parts[3]) if len(parts) > 3 else ""
        # 自动检测趋势符号
        trend_cls = ""
        if value.startswith("+") or "↑" in value:
            trend_cls = "kpi-up"
        elif value.startswith("-") or "↓" in value:
            trend_cls = "kpi-down"
        cards.append(
            '<div class="kpi-card">'
            '<div class="kpi-label">%s</div>'
            '<div class="kpi-value %s">%s<span class="kpi-unit">%s</span></div>'
            '<div class="kpi-note">%s</div>'
            '</div>' % (label, trend_cls, value, unit, note)
        )
    return '<div class="kpi-grid">' + "".join(cards) + '</div>'


def parse_qcard(lines):
    """解析 :::q-card 围栏，渲染为试题三段式。
    必填：第 1 行 = 题号/分值/难度（如 "Q1 | 4分 | 易"）
    第 2 行 = 题干
    第 3+ 行 = 子问题（以 (1)/(2)/(3) 或 1./2. 开头）
    """
    lines = [l for l in lines if l.strip() and not l.strip().startswith(":::")]
    if not lines:
        return ""
    # 第一行：题号 + 分值 + 难度
    head_parts = [p.strip() for p in lines[0].split("|")]
    qid = esc(head_parts[0]) if len(head_parts) > 0 else "Q"
    points = esc(head_parts[1]) if len(head_parts) > 1 else ""
    diff = esc(head_parts[2]) if len(head_parts) > 2 else ""
    diff_cls = "diff-easy" if "易" in diff or "易" in (head_parts[2] if len(head_parts) > 2 else "") else \
               "diff-mid" if "中" in diff else "diff-hard" if "难" in diff else ""
    # 题干（第 2 行）
    stem = inline(lines[1].strip()) if len(lines) > 1 else ""
    # 子问题
    sub_html = ""
    if len(lines) > 2:
        sub_items = []
        for ln in lines[2:]:
            s = ln.strip()
            m = re.match(r"^[(（](\d+)[)）]\s*(.*)$", s)
            if m:
                sub_items.append('<li><b>(%s)</b> %s</li>' % (m.group(1), inline(m.group(2))))
            else:
                sub_items.append('<li>%s</li>' % inline(s))
        sub_html = '<ol class="q-sub">%s</ol>' % "".join(sub_items)
    return (
        '<div class="q-card">'
        '<div class="q-head">'
        '<span class="q-id">%s</span>'
        '<span class="q-points">%s</span>'
        '<span class="q-diff %s">%s</span>'
        '</div>'
        '<div class="q-stem">%s</div>'
        '<div class="q-subs">%s</div>'
        '</div>'
    ) % (qid, points, diff_cls, diff, stem, sub_html)


def parse_gap_block(lines):
    """解析 :::gap 围栏，每行：缺口描述 | 影响 | 补充渠道"""
    rows = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(":::"):
            continue
        parts = [p.strip() for p in s.split("|")]
        if len(parts) >= 3:
            rows.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                        % (esc(parts[0]), esc(parts[1]), esc(parts[2])))
    if not rows:
        return ""
    return (
        '<div class="gap-table">'
        '<table><thead><tr><th scope="col">缺口</th><th scope="col">不填补的影响</th>'
        '<th scope="col">建议补充渠道</th></tr></thead>'
        '<tbody>%s</tbody></table></div>'
    ) % "".join(rows)


def parse_math_block(lines):
    """收集 $$ ... $$ 围栏数学公式"""
    out = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            # 单行公式
            out.append('<div class="math-block">%s</div>' % esc(s[2:-2].strip()))
        elif s.startswith("$$"):
            out.append('<div class="math-block">' + esc(s[2:].strip()))
        elif s.endswith("$$"):
            out.append(esc(s[:-2].strip()) + '</div>')
        else:
            out.append(esc(s))
    return "".join(out)


def _plain_inline(t):
    """把 Markdown 行内标记剥成纯文本（副标题/导语只做纯文本展示，不注入 HTML）。"""
    t = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'`([^`]*)`', r'\1', t)
    t = re.sub(r'(\*\*|__)(.+?)\1', r'\2', t)
    t = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'\1', t)
    t = t.replace('~~', '').replace('&nbsp;', ' ')
    return t.strip()


def blocks_to_html(lines, enable_math=True, sec_prefix="s0", img_base="", fig_n=None):
    """块级渲染（升级版：含 callout / 围栏 / 数学块）。"""
    out, i, n = [], 0, len(lines)
    h3_n = [0]
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue

        # ===== v5.1.0 代码围栏（```lang：图形渲染 / 通用代码块）=====
        _mc = FENCE_CODE.match(s)
        if _mc:
            j = i + 1
            while j < n and not lines[j].strip().startswith("```"):
                j += 1
            _h = parse_code_fence(_mc.group(1), _mc.group(2).strip(),
                                  "\n".join(lines[i + 1:j]), img_base, fig_n)
            if _h:
                out.append(_h)
            i = j + 1
            continue

        # ===== 围栏语法 =====
        # :::gallery（v5.0：带标题图组，标题可省略）
        _fg = FENCE_GALLERY.match(s)
        if _fg:
            j = i + 1
            while j < n and not FENCE_END.match(lines[j].strip()):
                j += 1
            _tl = (_fg.group(1) or "").strip()
            _body = ([_tl] if _tl else []) + lines[i + 1:j]
            out.append(parse_gallery(_body, img_base, fig_n))
            i = j + 1
            continue
        # :::kpi
        if FENCE_KPI.match(s):
            j = i + 1
            while j < n and not FENCE_END.match(lines[j].strip()):
                j += 1
            out.append(parse_kpi_grid(lines[i + 1:j]))
            i = j + 1
            continue
        # :::q-card
        if FENCE_QCARD.match(s):
            j = i + 1
            while j < n and not FENCE_END.match(lines[j].strip()):
                j += 1
            out.append(parse_qcard(lines[i + 1:j]))
            i = j + 1
            continue
        # :::gap
        if FENCE_GAP.match(s):
            j = i + 1
            while j < n and not FENCE_END.match(lines[j].strip()):
                j += 1
            out.append(parse_gap_block(lines[i + 1:j]))
            i = j + 1
            continue
        # ===== v4.1 数据图表围栏 =====
        _fc = FENCE_CHART.match(s)
        if _fc:
            j = i + 1
            while j < n and not FENCE_END.match(lines[j].strip()):
                j += 1
            out.append(parse_chart(lines[i + 1:j], (_fc.group(1) or "bar"),
                                   (_fc.group(2) or "")))
            i = j + 1
            continue

        # ===== v3 画板围栏（bar/bento/timeline/phase/law/faq/tags/matrix）=====
        fv = FENCE_V3.match(s)
        if fv:
            kind = fv.group(1)
            j = i + 1
            while j < n and not FENCE_END.match(lines[j].strip()):
                j += 1
            fn = {"bar": parse_bar, "bento": parse_bento, "timeline": parse_timeline,
                  "phase": parse_phase, "law": parse_law, "faq": parse_faq,
                  "tags": parse_tags, "matrix": parse_matrix, "stat": parse_stat,
                  "bignum": parse_bignum, "icons": parse_icons,
                  "gallery": (lambda _ls: parse_gallery(_ls, img_base, fig_n))}[kind]
            out.append(fn(lines[i + 1:j]))
            i = j + 1
            continue

        # ===== 未识别围栏兜底（::: 开头但未匹配任何围栏）→ 当普通文本，防死循环 =====
        if s.startswith(":::"):
            out.append("<p>%s</p>" % inline(s))
            i += 1
            continue

        # ===== 表格 =====
        if s.startswith("|"):
            j = i
            while j < n and lines[j].strip().startswith("|"):
                j += 1
            out.append(split_table(lines[i:j]))
            i = j
            continue

        # ===== 引用块 → 强化 callout =====
        if s.startswith(">"):
            j = i
            buf = []
            callout_kind = None
            while j < n and lines[j].strip().startswith(">"):
                ln_strip = lines[j].strip()
                m = CALLOUT_RE.match(ln_strip)
                if m:
                    if callout_kind is None:
                        callout_kind = m.group(1).lower()
                    buf.append(m.group(2))
                else:
                    buf.append(ln_strip.lstrip(">").strip())
                j += 1
            body = "<br>".join(inline(x) for x in buf if x)
            if callout_kind in ("info", "warn", "crit", "ok"):
                cn = {"info": "提示", "warn": "警示", "crit": "风险", "ok": "达标"}.get(callout_kind, "提示")
                out.append('<div class="callout callout-%s"><div class="callout-head">%s</div><div class="callout-body">%s</div></div>'
                            % (callout_kind, cn, body))
            else:
                out.append('<div class="quote">%s</div>' % body)
            i = j
            continue

        # ===== 数学块 $$ ... $$ =====
        if enable_math and s.startswith("$$"):
            j = i + 1
            math_buf = [s[2:].strip()]
            closed = s.endswith("$$") and len(s) > 4
            if closed:
                math_buf = [s[2:-2].strip()]
            else:
                while j < n and not lines[j].strip().endswith("$$"):
                    math_buf.append(lines[j].rstrip())
                    j += 1
                if j < n:
                    math_buf.append(lines[j].strip()[:-2].rstrip())
                    closed = True
            if closed:
                out.append('<div class="math-block">' + esc(" ".join(math_buf)) + '</div>')
                i = j + 1 if not (s.endswith("$$") and len(s) > 4) else i + 1
            else:
                i = j
            continue

        # ===== 列表 =====
        if NUM_LEAD.match(s):
            j, items = i, []
            while j < n and NUM_LEAD.match(lines[j].strip()):
                items.append(re.sub(NUM_LEAD, "", lines[j].strip()))
                j += 1
            out.append("<ul class=\"plain\">%s</ul>"
                       % "".join("<li>%s</li>" % inline(x) for x in items))
            i = j
            continue

        # ===== 小标题 =====
        if s.startswith("#### "):
            out.append("<h4>%s</h4>" % inline(s[5:])); i += 1; continue
        if s.startswith("### "):
            h3_n[0] += 1
            out.append('<h3 id="h3-%s-%d">%s</h3>' % (sec_prefix, h3_n[0], inline(s[4:])))
            i += 1; continue

        # ===== 图片（v4.1：base64 内嵌 + 自动图注编号）=====
        _im = IMG_RE.match(s)
        if _im:
            _opts = (_im.group(3) or "").lower()
            _mode = "inline" if "inline" in _opts else "wide"
            out.append(parse_figure(_im.group(2), _im.group(1), _mode, img_base,
                                    fig_n, ai=("ai" in _opts)))
            i += 1
            continue

        # ===== 段落 =====
        j, buf = i, []
        while j < n and lines[j].strip() \
                and not lines[j].strip().startswith(("|", ">", "#", "$", ":::", "![")) \
                and not NUM_LEAD.match(lines[j].strip()):
            buf.append(lines[j].strip()); j += 1
        if j == i:
            # 兜底：当前非空行以 | > # $ ::: ![ 开头却未被任何专用分支消费
            # （典型：--math 关闭时的 $$ 块级公式行），若不推进指针将造成死循环
            buf.append(lines[i].strip()); j = i + 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
        i = j
    return "\n".join(out)


def parse_frontmatter(md):
    """解析文首 YAML frontmatter（简单键值 + 行内列表），返回 (meta, 去掉头的正文)"""
    m = re.match(r"^\ufeff?---\s*\n(.*?)\n---\s*\n?", md, re.S)
    if not m:
        return {}, md
    meta = {}
    for line in m.group(1).split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        k, v = s.split(":", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1]
            quoted = re.findall(r'"([^"]*)"', inner) + re.findall(r"'([^']*)'", inner)
            v = [x.strip() for x in quoted if x.strip()] if quoted else \
                [x.strip() for x in inner.split(",") if x.strip()]
        meta[k] = v
    return meta, md[m.end():]


def to_list(v):
    """字符串/列表 → 去空列表（分隔符：分号/顿号/竖线）"""
    if not v:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in re.split(r"[;；、|·・]+", str(v)) if x.strip()]


def to_stats(v):
    """值|标签 ;; 值|标签 → [{'v','l'}]（亦可为列表）"""
    out = []
    if not v:
        return out
    items = v if isinstance(v, list) else re.split(r"[;；]+", str(v))
    for it in items:
        it = str(it).strip()
        if not it:
            continue
        if "|" in it:
            a, b = it.split("|", 1)
            out.append({"v": a.strip(), "l": b.strip()})
        else:
            out.append({"v": it, "l": ""})
    return out


def parse_md(md, auto_toc=True, enable_math=True, img_base=""):
    """解析 Markdown → (title, sections, sources, gaps, toc_needed, lead)"""
    lines = md.replace("\r\n", "\n").split("\n")
    title, sections, cur, pre, i, n = None, [], None, [], 0, len(lines)
    while i < n:
        ln = lines[i]
        if ln.startswith("# ") and title is None:
            title = ln[2:].strip(); i += 1; continue
        if ln.startswith("## "):
            if cur:
                sections.append(cur)
            cur = [ln[3:].strip(), []]
            i += 1; continue
        if cur is None:
            pre.append(ln)      # h1 之后、首个 ## 之前 → 前导段
        else:
            cur[1].append(ln)
        i += 1
    if cur:
        sections.append(cur)
    # 全文无 ## 章节时，前导段自成一节，避免正文丢失
    if not sections and any(x.strip() for x in pre):
        sections.append(["正文", pre]); pre = []

    # 前导首段 → 首屏 lead（供 subtitle 兜底）；跳过围栏行
    lead = ""
    for ln in pre:
        s = ln.strip()
        if s and not s.startswith(("#", "|", ":")):
            lead = _plain_inline(s); break

    # 抽取「来源/参考」章节为 sources（去序号后首词匹配，取首个匹配章）
    sources, kept, done = [], [], False
    for t, body in sections:
        tt = SEQ_STRIP_RE.sub("", t).strip()
        if (not done) and REF_HEAD_RE.match(tt):
            done = True
            for ln in body:
                s = ln.strip()
                m = re.match(r"^\s*(?:\d+[.、)]|[-*+])\s*(.+)$", s)
                if not m:
                    continue
                item = m.group(1)
                lm = SRC_RE.search(item) or SRC_RE_LOOSE.search(item)
                label = (SRC_RE.sub("", item) or item).strip(" 　-—").split("|")[0].strip()[:80]
                sources.append({"label": label, "level": lm.group(1) if lm else "—", "note": ""})
        else:
            kept.append((t, body))
    if sources:
        sections = kept

    # 自动 TOC 触发条件：## 章节 ≥ 4
    toc_needed = auto_toc and len(sections) >= 4

    # 抽取 :::gap 围栏为 gaps（自动识别缺口区）
    gaps = []
    final_sections = []
    for t, body in sections:
        if t.strip() == "信息缺口与风险" or "缺口" in t:
            n0 = len(gaps)
            j = 0
            in_fence = False
            fence_lines = []
            extra = 0
            while j < len(body):
                st = body[j].strip()
                if FENCE_GAP.match(st):
                    in_fence = True; fence_lines = []; j += 1; continue
                if in_fence:
                    if FENCE_END.match(st):
                        for fl in fence_lines:
                            ps = fl.strip()
                            if not ps:
                                continue
                            pp = [p.strip() for p in ps.split("|")]
                            if len(pp) >= 3:
                                gaps.append({"item": pp[0], "impact": pp[1], "channel": pp[2]})
                        in_fence = False; fence_lines = []
                    else:
                        fence_lines.append(body[j])
                elif st:
                    extra += 1
                j += 1
            # 该章已抽为独立缺口区块且无额外正文 → 移除，避免重复渲染
            if len(gaps) > n0 and extra <= 1:
                continue
        final_sections.append((t, body))

    spec_sections = []
    fig_n = [0]
    for i, (t, body) in enumerate(final_sections, 1):
        sid = "s%d" % i
        # 章节副标题：首个非空非标题、非表格、非围栏行
        subtitle = ""
        for ln in body:
            s = ln.strip()
            if not s or s.startswith(("#", "|", ":")):
                continue
            sp = _plain_inline(s)
            subtitle = sp[:80].rstrip("。. \t") + ("..." if len(sp) > 80 else "")
            break
        spec_sections.append({"id": sid, "title": t, "subtitle": subtitle,
                             "html": blocks_to_html(body, enable_math, sid, img_base, fig_n)})
    return title, spec_sections, sources, gaps, toc_needed, lead


def main():
    ap = argparse.ArgumentParser(description="Markdown → 底座级单文件 HTML（v2.0）")
    ap.add_argument("input", nargs="?", help="输入 Markdown 文件")
    ap.add_argument("-o", "--out", help="输出 HTML 文件")
    ap.add_argument("--doc", dest="input_doc", help="同 --input（兼容旧参数）")
    ap.add_argument("--title"); ap.add_argument("--subtitle")
    ap.add_argument("--audience"); ap.add_argument("--date")
    ap.add_argument("--conclusion"); ap.add_argument("--theme", default=None)
    ap.add_argument("--motif", default=None,
                    help="版式母题 editorial|blueprint|narrative|classic（默认 editorial）")
    ap.add_argument("--hero-badge", dest="hero_badge", help="首屏徽章文案")
    ap.add_argument("--hero-stats", dest="hero_stats", help="首屏数据卡：值|标签 ;; 值|标签")
    ap.add_argument("--hero-pills", dest="hero_pills", help="首屏标签行（顿号/竖线/分号分隔）")
    ap.add_argument("--list-themes", action="store_true", help="列出可用配色并退出")
    ap.add_argument("--check", action="store_true", help="构建后跑 html_check.py")
    ap.add_argument("--math", action="store_true", help="启用 KaTeX 数学公式渲染")
    ap.add_argument("--no-toc", action="store_true", help="关闭自动 TOC")
    ap.add_argument("--layout", default=None, help="布局：sidebar=侧栏目录（长报告），默认顶部胶囊")
    ap.add_argument("--style", default=None, help="章节头样式：dark=深色渐变头")
    ap.add_argument("--max-kb", type=int, default=None,
                    help="体积上限 KB（含配图页建议 1200；默认 300）")
    a = ap.parse_args()
    a.input = a.input or a.input_doc

    if a.list_themes:
        for p in PALETTES:
            print("  %-9s %s\t%s" % (p["id"], p["zh"], p.get("use", "")))
        return 0
    if not a.input or not a.out:
        print("用法：md2report.py 成稿.md -o 成果页.html [--theme ocean] [--check] [--math]",
              file=sys.stderr)
        return 2

    import datetime
    md = open(a.input, encoding="utf-8").read()
    meta, md_body = parse_frontmatter(md)

    def pick(cli, *keys):
        if cli:
            return cli
        for k in keys:
            if meta.get(k):
                return meta[k]
        return ""

    # v5.1.0：图形配色随报告主题（先定主题，再解析正文，保证 mermaid 图与页面同调）
    theme_v = a.theme or meta.get("theme") or "sunset"
    if theme_v not in BY_ID:
        theme_v = "sunset"
    try:
        DIAGRAM_COLORS.clear()
        DIAGRAM_COLORS.update(_rd.theme_colors(BY_ID.get(theme_v)))
    except Exception:
        pass
    md_title, sections, sources, gaps, toc_needed, lead = parse_md(
        md_body, auto_toc=(not a.no_toc), enable_math=a.math,
        img_base=os.path.dirname(os.path.abspath(a.input)))
    spec = {
        "title": pick(a.title, "title") or md_title or "成果页",
        "subtitle": pick(a.subtitle, "subtitle", "lead") or lead,
        "audience": pick(a.audience, "audience", "deliver_to", "to"),
        "date": pick(a.date, "date") or datetime.date.today().isoformat(),
        "theme": theme_v if theme_v in BY_ID else "sunset",
        "conclusion": pick(a.conclusion, "conclusion"),
        "hero_badges": pick(a.hero_badge, "hero_badges", "badge"),
        "hero_stats": to_stats(pick(a.hero_stats, "hero_stats")),
        "hero_pills": to_list(pick(a.hero_pills, "hero_pills")),
        "items": [],
        "layout": pick(a.layout, "layout"),
        "style": pick(a.style, "style"),
        "motif": pick(getattr(a, "motif", None), "motif"),
        "sections": sections,
        "sources": sources,
        "gaps": gaps,
        "math": a.math,
        "footer": {"unit": "ima.copilot", "author": "小邦",
                   "note": "由 md2report.py v4.13.1 渲染（底座 html-report-builder）"},
    }
    html = build_html(spec)
    open(a.out, "w", encoding="utf-8").write(html)
    sz = os.path.getsize(a.out) / 1024
    extras = []
    if a.math:
        extras.append("KaTeX数学公式")
    if toc_needed:
        extras.append("自动TOC(%d节)" % len(sections))
    if sources:
        extras.append("来源%d条" % len(sources))
    if gaps:
        extras.append("缺口%d项" % len(gaps))
    print("已生成：%s（%.1fKB，配色 %s，%d 节%s）" % (
        a.out, sz, spec["theme"] + "/" + (spec.get("motif") or "editorial"), len(sections),
        "，" + "，".join(extras) if extras else ""))
    if a.check:
        _cmd = [sys.executable, os.path.join(HERE, "html_check.py"), a.out, "--node"]
        if a.max_kb:
            _cmd += ["--max-kb", str(a.max_kb)]
        return subprocess.run(_cmd).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
