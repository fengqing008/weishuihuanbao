#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读者排印坊 · 成书引擎 v1.2.1
稿件清单(manifest.json) → 册页 HTML（封面/扉页/版权页/目次/栏目扉页/分栏目正文）。

v1.1：图文混排（`{wide}` 跨栏 / 栏内浮图 / 图题）、首字下沉、篇末花饰、封面增强
v1.2.1：md_to_blocks 支持无序/有序列表与表格（v1.4.0 起对接 qf-lineart 配图）
v1.2：联动 theme-factory 10 套主题换肤（--theme）、栏目扉页（manifest "column_pages": true）

用法：
  python3 book_builder.py --manifest book.json --out book.html
  python3 book_builder.py --manifest book.json --theme forest-canopy --out book_forest.html
  python3 book_builder.py --manifest book.json --part front --out front.html --pagemap pagemap.json
  python3 book_builder.py --list-themes
"""
import argparse, json, re, sys
from html import escape
from pathlib import Path

LAYOUT_CLASS = {"two-column": "col-2", "one-column": "col-1",
                "two-column-nobreak": "col-nobreak", "three-column": "col-3"}
ENDMARK = '<div class="endmark">◆ ◆ ◆</div>'
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _mix(c, tgt, k):
    a = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(tgt[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(a[i] * (1 - k) + b[i] * k) for i in range(3))


def apply_theme(css: str, theme: dict) -> str:
    pairs = {"--paper": theme["paper"], "--ink": theme["ink"], "--column": theme["column"],
             "--rule": theme["rule"], "--accent": theme["accent"],
             "--muted": _mix(theme["ink"], theme["paper"], 0.45)}
    for var, val in pairs.items():
        css = re.sub(rf"({re.escape(var)}:\s*)#[0-9A-Fa-f]{{6}}", rf"\g<1>{val}", css)
    return css


def load_themes():
    p = ASSETS / "themes.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# ---------------- 迷你 Markdown → HTML ----------------
def _inline(t: str) -> str:
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t


def md_to_blocks(md: str, img_base: Path | None = None) -> str:
    """迷你 Markdown → HTML：段落 / 标题 / 引用 / 图片 / 无序列表 / 有序列表 / 表格"""
    lines = md.replace("\r\n", "\n").split("\n")
    out, buf, quote, lst, tbl = [], [], [], [], []

    def flush_p():
        if buf:
            text = " ".join(buf).strip()
            if text:
                cls = "source" if re.match(r"^[（(]\s*(选自|摘自|原载|江江手记)", text) else ""
                attr = f' class="{cls}"' if cls else ""
                out.append(f"<p{attr}>{_inline(text)}</p>")
            buf.clear()

    def flush_q():
        if quote:
            out.append(f"<blockquote>{' '.join(quote).strip()}</blockquote>")
            quote.clear()

    def flush_lst():
        if lst:
            tag = "ol" if lst[0][0] == "ol" else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(t)}</li>" for _, t in lst) + f"</{tag}>")
            lst.clear()

    def flush_tbl():
        if tbl:
            rows, head = [], True
            for r in tbl:
                cells = [c.strip() for c in r.strip().strip("|").split("|")]
                if cells and all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    continue                                   # 分隔行
                tag = "th" if head else "td"
                rows.append("<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells) + "</tr>")
                head = False
            if rows:
                out.append('<table class="md-table">' + "".join(rows) + "</table>")
            tbl.clear()

    for ln in lines:
        s = ln.strip()
        if not s:
            flush_p(); flush_q(); flush_lst(); flush_tbl(); continue
        m_img = re.match(r"^!\[(.*?)\]\((.+?)\)(\{wide\})?\s*$", s)
        if m_img:
            flush_p(); flush_q(); flush_lst(); flush_tbl()
            cap, src, wide = m_img.group(1), m_img.group(2), bool(m_img.group(3))
            p = (img_base / src).resolve() if img_base else Path(src)
            cls = "figure-wide" if wide else "figure-inline"
            caphtml = f"<figcaption>{_inline(cap)}</figcaption>" if cap else ""
            out.append(f'<figure class="{cls}"><img src="{p}">{caphtml}</figure>')
            continue
        if re.match(r"^\|.*\|$", s):                              # 表格行
            flush_p(); flush_q(); flush_lst()
            tbl.append(s); continue
        flush_tbl()
        m_li = re.match(r"^[-*·]\s+(.*)$", s)
        if m_li:
            flush_p(); flush_q()
            if lst and lst[0][0] != "ul":
                flush_lst()
            lst.append(("ul", m_li.group(1))); continue
        m_ol = re.match(r"^\d{1,2}[.、)]\s*(.+)$", s)
        if m_ol:
            flush_p(); flush_q()
            if lst and lst[0][0] != "ol":
                flush_lst()
            lst.append(("ol", m_ol.group(1))); continue
        flush_lst()
        if s.startswith(">"):
            flush_p(); quote.append(s.lstrip("> ").strip()); continue
        flush_q()
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush_p()
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            continue
        buf.append(s)
    flush_p(); flush_q(); flush_lst(); flush_tbl()
    return "\n".join(out)


def _doc(inner: str, title: str, theme_css: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{escape(title)}</title>
<style>
{theme_css}
</style>
</head>
<body>
{inner}
</body></html>"""


def _toc_html(arts, groups, page_of) -> str:
    """目次页：PDF（print）双栏、HTML（screen）单列——见 theme.css 的 .toc-col 与 @media screen。"""
    flat = []
    for col, items in groups:
        flat.append(("col", col))
        for a in items:
            flat.append(("item", a))
    # 按加权行数均分（栏目标题占 1.6 行），避免一栏过挤、一栏过空
    def _w(kind):
        return 1.6 if kind == "col" else 1.0
    total = sum(_w(k) for k, _ in flat)
    acc, split = 0.0, len(flat)
    for i, (kind, _) in enumerate(flat):
        acc += _w(kind)
        if acc >= total / 2.0:
            split = i + 1
            break
    while split < len(flat) and flat[split][0] == "col":
        split += 1
    while split > 1 and flat[split - 1][0] == "col":
        split -= 1
    left, right = flat[:split], flat[split:]

    def render_col(rows):
        out = []
        for kind, val in rows:
            if kind == "col":
                out.append('<div class="toc-col-title">%s</div>' % escape(val))
            else:
                out.append(
                    '<a class="toc-line" href="#art-%s">'
                    '<span class="toc-name">%s</span>'
                    '<span class="toc-dots"></span>'
                    '<span class="toc-pg">%s</span>'
                    '</a>' % (val.get("order"), escape(val["title"]), page_of(val)))
        return "\n".join(out)

    toc = ['<section class="toc-page" style="width:152mm">', '<div class="toc-title">目 次</div>',
           '<div class="toc-two">',
           '<div class="toc-td">%s</div>' % render_col(left),
           '<div class="toc-td">%s</div>' % render_col(right),
           '</div>']
    return "\n".join(toc)


def build_front(manifest, theme_css, pagemap) -> str:
    book = manifest.get("book", {})
    arts = sorted(manifest.get("articles", []), key=lambda x: x.get("order", 0))
    groups = []
    for a in arts:
        if groups and groups[-1][0] == a["column"]:
            groups[-1][1].append(a)
        else:
            groups.append((a["column"], [a]))

    def page_of(a):
        if pagemap and "orders" in pagemap:
            v = pagemap["orders"].get(str(a.get("order")))
            return str(v) if v else "__PAGE__"
        return "__PAGE__"

    cover = (
        '<section class="cover">'
        '<div class="cover-topline"></div>'
        '<div class="cover-deco"></div>'
        f'<div class="book-title">{escape(book.get("title","无题"))}</div>'
        f'<div class="book-subtitle">{escape(book.get("subtitle",""))}</div>'
        f'<div class="issue-box">{escape(book.get("issue",""))}</div>'
        f'<div class="cover-blurb">{escape(book.get("blurb",""))}</div>'
        f'<div class="book-editor">编者：{escape(book.get("editor",""))}</div>'
        f'<div class="publish-line">{escape(book.get("publisher","自编样本"))}　·　读者排印坊 版式</div>'
        '</section>')
    fly = '<section class="matter flyleaf"></section>'
    copyr = (
        '<section class="matter copyright">'
        '<h2>版本记录</h2>'
        f'<span class="rec-row"><b>书名</b>　{escape(book.get("title",""))}</span>'
        f'<span class="rec-row"><b>副题</b>　{escape(book.get("subtitle",""))}</span>'
        f'<span class="rec-row"><b>编者</b>　{escape(book.get("editor",""))}</span>'
        f'<span class="rec-row"><b>期号</b>　{escape(book.get("issue",""))}</span>'
        f'<span class="rec-row"><b>出版</b>　{escape(book.get("publisher","自编样本"))}</span>'
        f'<span class="rec-row"><b>版式</b>　16开 · 正文宋体五号 · 双栏{("　·　主题：" + book["theme"]) if book.get("theme") else ""}</span>'
        '</section>')
    toc = _toc_html(arts, groups, page_of)
    version = (f'<div class="toc-version">书名：{escape(book.get("title",""))}　'
               f'编者：{escape(book.get("editor",""))}　期号：{escape(book.get("issue",""))}<br>'
               f'共 {len(arts)} 篇　版式：16开双栏（读者经典体例）</div>')
    return cover + fly + copyr + toc + version + '</section>'



# ---------------- 自动配图落位（v1.3） ----------------
def _figure_html(item: dict) -> str:
    role = item.get("role", "inline")
    cls = ("figure-wide" if role == "wide" else "figure-inline") + f" img-{item.get('style', 'fade')}"
    cap = item.get("caption", "")
    caphtml = f"<figcaption>{escape(cap)}</figcaption>" if cap else ""
    return f'<figure class="{cls}"><img src="{item["file"]}">{caphtml}</figure>'


def _insert_after_nth_p(html: str, snippet: str, n: int) -> str:
    idx = -1
    for _ in range(n):
        idx = html.find('</p>', idx + 1)
        if idx < 0:
            break
    if idx < 0:
        return html + snippet
    k = idx + len('</p>')
    return html[:k] + snippet + html[k:]


def _insert_after_keyword(html: str, snippet: str, kw: str):
    """图跟文走：插在首个含关键词的段落之后。找不到返回 None。"""
    i = html.find(kw)
    if i < 0:
        return None
    end = html.find('</p>', i)
    if end < 0:
        return None
    k = end + len('</p>')
    return html[:k] + snippet + html[k:]


def _insert_auto_figures(blocks: str, items: list) -> str:
    """落位：wide 走篇首；inline 优先按 anchor（kn:关键词）随文插入，无锚点再回退中段。

    约定 anchor 取「kn:关键词」，命中该关键词所在段落之后——对齐图书版式惯例句
    「先文后图，图跟文走，图文紧靠」。
    """
    if not items:
        return blocks
    for it in items:
        role = it.get("role", "inline")
        fig = _figure_html(it)
        anchor = (it.get("anchor") or "").strip()
        if role != "wide" and anchor.startswith("kn:"):
            landed = _insert_after_keyword(blocks, fig, anchor[3:].strip())
            if landed is not None:
                blocks = landed
                continue
        n_p = blocks.count('</p>')
        if role == "wide":
            pos = 2 if n_p >= 3 else max(1, n_p - 1)
        elif role == "inline":
            pos = max(1, n_p // 2)
        else:                       # inline-end：靠后
            pos = max(1, n_p - 1)
        blocks = _insert_after_nth_p(blocks, fig, pos)
    return blocks


def build_body(manifest, theme_css, base_dir, auto_images=None) -> str:
    arts = sorted(manifest.get("articles", []), key=lambda x: x.get("order", 0))
    col_pages = bool(manifest.get("column_pages"))
    intros = manifest.get("columns_intro", {})
    body = ['<main class="body-matter">']
    prev_col = None
    for a in arts:
        # 栏目扉页
        if col_pages and a["column"] != prev_col:
            intro = intros.get(a["column"], "")
            body.append(
                '<section class="column-title-page">'
                f'<div class="ctp-name">{escape(a["column"])}</div>'
                '<div class="ctp-rule"></div>'
                f'<div class="ctp-intro">{escape(intro)}</div>'
                '</section>')
        prev_col = a["column"]

        lay = LAYOUT_CLASS.get(a.get("layout", "two-column"), "col-2")
        bp = (base_dir / a["body"]).resolve()
        md = bp.read_text(encoding="utf-8") if bp.exists() else f"（缺稿件文件：{a.get('body')}）"
        blocks = md_to_blocks(md, bp.parent)
        if auto_images:
            blocks = _insert_auto_figures(blocks, auto_images.get(str(a.get("order")), []))
        drop = a.get("dropcap", a.get("layout") == "two-column-nobreak")
        if drop:
            blocks = re.sub(r"<p>(\S)", r'<p><span class="dropcap">\1</span>', blocks, count=1)
        blocks += ENDMARK
        body.append(
            f'<article class="article {lay}" id="art-{a.get("order")}" '
            f'data-column="{escape(a["column"])}" data-order="{a.get("order")}"'
            + (f' data-theme="{escape(a["theme"])}"' if a.get("theme") else "") + '>'
            '<div class="col-head">'
            f'<div class="column-name">{escape(a["column"])}</div>'
            f'<h1 class="article-title">{escape(a["title"])}</h1>'
            f'<p class="article-author">{escape(a.get("author",""))}</p>'
            '</div>'
            f'<div class="col-body">{blocks}</div>'
            '</article>')
    body.append('</main>')
    return "".join(body)


def main() -> int:
    ap = argparse.ArgumentParser(description="读者排印坊·成书引擎")
    ap.add_argument("--manifest", help="稿件清单 JSON")
    ap.add_argument("--theme", help="theme-factory 主题名（换肤）")
    ap.add_argument("--out", default="book.html")
    ap.add_argument("--part", default="all", choices=["all", "front", "body"])
    ap.add_argument("--pagemap", help="回填目次页码 JSON")
    ap.add_argument("--auto-images", help="自动配图清单 JSON（illustration_draw.py 产出）")
    ap.add_argument("--sample", action="store_true", help="仅取第一篇试排")
    ap.add_argument("--list-themes", action="store_true", help="列出 10 套主题")
    a = ap.parse_args()

    if a.list_themes:
        for k, v in load_themes().items():
            if not k.startswith("_"):
                print(f"{k:20s} {v['title']}")
        return 0

    if not a.manifest:
        ap.error("需提供 --manifest")

    mp = Path(a.manifest).resolve()
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    if a.sample:
        manifest["articles"] = manifest["articles"][:1]

    theme_css = (ASSETS / "theme.css").read_text(encoding="utf-8")
    if a.theme:
        themes = load_themes()
        if a.theme not in themes:
            ap.error(f"未知主题 {a.theme}")
        theme_css = apply_theme(theme_css, themes[a.theme])
        manifest.setdefault("book", {})["theme"] = a.theme

    pm = json.loads(Path(a.pagemap).read_text(encoding="utf-8")) if a.pagemap else None
    ai = json.loads(Path(a.auto_images).read_text(encoding="utf-8")) if a.auto_images else None
    title = manifest.get("book", {}).get("title", "")

    if a.part == "front":
        inner = build_front(manifest, theme_css, pm)
    elif a.part == "body":
        inner = build_body(manifest, theme_css, mp.parent, ai)
    else:
        inner = build_front(manifest, theme_css, pm) + build_body(manifest, theme_css, mp.parent, ai)

    Path(a.out).write_text(_doc(inner, title, theme_css), encoding="utf-8")
    print(f"OK {a.out}  part={a.part}  theme={a.theme or 'default'}  篇数={len(manifest['articles'])}  页码={'已回填' if pm else '占位(首遍)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
