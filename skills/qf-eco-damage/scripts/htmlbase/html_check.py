#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""html_check.py —— 单文件 HTML 成果页结构级自检

用法：
  python3 html_check.py 页面.html                 结构检查 + 配色对比度校验
  python3 html_check.py 页面.html --json          机器可读结果
  python3 html_check.py 页面.html --node          追加 JS 语法校验（需 node）
  python3 html_check.py 页面.html --text-out plain.txt   抽正文纯文本（送写作质量校验）
  python3 html_check.py 页面.html --max-kb 300    体积上限（默认 300KB）

退出码：0 通过（可为 WARN）；1 存在 FAIL。

检查项分三级：FAIL 为交付阻断项，WARN 为需复核项，OK 为通过项。
"""
import argparse
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from palettes import lum, cr  # noqa
except Exception:  # 独立运行时的回退实现
    def lum(c):
        c = c.lstrip("#")
        r, g, b = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        f = lambda u: u / 12.92 if u <= 0.03928 else ((u + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    def cr(a, b):
        la, lb = lum(a), lum(b)
        if la < lb:
            la, lb = lb, la
        return (la + 0.05) / (lb + 0.05)

VOID = {"br", "hr", "img", "meta", "link", "input", "source", "col", "area", "base", "embed", "track", "wbr"}
RES = []


def add(level, code, msg, fix=""):
    RES.append({"level": level, "code": code, "msg": msg, "fix": fix})


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.err, self.h = [], [], []
        self.imgs_no_alt = 0
        self.style_text = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.h.append(int(tag[1]))
        if tag == "img" and not d.get("alt"):
            self.imgs_no_alt += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            self.err.append("交叉闭合 </%s>" % tag)
            while self.stack and self.stack.pop() != tag:
                pass
        else:
            self.err.append("多余闭合 </%s>" % tag)


def parse_theme_blocks(html):
    """从 <style> 中解析 :root 与 [data-theme=x] 的变量"""
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    blocks = {}
    for m in re.finditer(r"(?::root|\[data-theme=[\"']?([\w-]+)[\"']?\])\s*\{([^}]*)\}", css):
        name = m.group(1) or "_root"
        vars_ = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", m.group(2)))
        blocks.setdefault(name, {}).update({k.strip(): v.strip() for k, v in vars_.items()})
    if "_root" in blocks:
        for k, v in blocks["_root"].items():
            for other in blocks:
                if other != "_root":
                    blocks[other].setdefault(k, v)
    return blocks


def theme_contrast(vars_):
    """对一组变量做对比度校验，返回 [(项, 比值, 门禁, 是否达标)]"""
    def g(*names):
        for n in names:
            if vars_.get(n):
                return vars_[n].strip()
        return None

    bg, sf, tx, mu = g("--bg"), g("--surface"), g("--text"), g("--muted")
    ac, ac2 = g("--accent"), g("--accent-2", "--accent2")
    h1, h2, ht = g("--hero-1"), g("--hero-2"), g("--hero-text")
    items = [("正文:底色", tx, bg, 4.5), ("正文:卡片", tx, sf, 4.5), ("弱化:卡片", mu, sf, 4.5),
             ("强调:底色", ac, bg, 4.5), ("辅色:底色", ac2, bg, 3.0),
             ("页头白字:渐变1", ht, h1, 4.5), ("页头白字:渐变2", ht, h2, 4.5)]
    out = []
    for label, f, b, gate in items:
        if f and b and re.match(r"^#[0-9a-fA-F]{6}$", f) and re.match(r"^#[0-9a-fA-F]{6}$", b):
            out.append((label, round(cr(f, b), 2), gate, cr(f, b) >= gate))
    return out


def extract_text(html):
    src = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", html, flags=re.S)
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    BLOCK = {"br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "td", "th",
             "section", "footer", "header", "table", "figure", "blockquote"}

    class T(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.buf = []

        def handle_starttag(self, tag, attrs):
            if tag in BLOCK:
                self.buf.append("\n")

        def handle_endtag(self, tag):
            if tag in BLOCK:
                self.buf.append("\n")

        def handle_data(self, d):
            d = d.strip()
            if d:
                self.buf.append(d + " ")

    t = T()
    t.feed(src)
    txt = re.sub(r"[ \t]+", " ", "".join(t.buf))
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", txt).strip()


def main():
    ap = argparse.ArgumentParser(description="单文件 HTML 成果页结构级自检")
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--node", action="store_true", help="启用 JS 语法校验（需 node）")
    ap.add_argument("--text-out", help="抽正文纯文本到指定文件")
    ap.add_argument("--max-kb", type=int, default=300, help="体积上限（KB），默认 300")
    ap.add_argument("--density-min", type=int, default=300, help="每章最少中文字数（密度门禁 WARN 线），默认 300")
    ap.add_argument("--no-density", action="store_true", help="关闭内容密度检查")
    ap.add_argument("--no-tone", action="store_true", help="关闭文风（黑话/序列化路标）检查")
    a = ap.parse_args()

    p = a.file
    if not os.path.isfile(p):
        print("文件不存在：%s" % p, file=sys.stderr)
        return 1
    html = open(p, encoding="utf-8").read()
    kb = os.path.getsize(p) / 1024

    # 1 必备声明
    for pat, code, ok_msg, fail_msg, fix in [
        (r'<meta[^>]+charset=["\']?utf-8', "META_CHARSET", "字符集声明齐备", "缺少字符集声明", '补 <meta charset="UTF-8">'),
        (r'<meta[^>]+name=["\']viewport', "META_VIEWPORT", "视口声明齐备", "缺少视口声明", '补 <meta name="viewport" content="width=device-width, initial-scale=1.0">'),
        (r"<html[^>]+lang=", "HTML_LANG", "语言声明齐备", "html 标签缺 lang", '补 lang="zh-CN"'),
        (r"<title>[^<]{2,}</title>", "TITLE", "页面标题齐备", "缺少页面标题", "补 <title>"),
    ]:
        if re.search(pat, html, re.I):
            add("OK", code, ok_msg)
        else:
            add("FAIL", code, fail_msg, fix)

    # 2 外链资源（白名单：KaTeX CDN 视为可接受的数学公式引入）
    ext = re.findall(r"<(?:link|script|img|iframe|audio|video|source)[^>]+(?:href|src)\s*=\s*[\"'](https?:)?//", html, re.I)
    ext += re.findall(r"url\(\s*[\"']?https?://", html, re.I)
    ext += re.findall(r"@import", html, re.I)
    katex_in_html = bool(re.search(r"katex|katex\.min", html, re.I))
    if ext:
        # 检查每处外链 URL 是否全部为 KaTeX/jsdelivr（白名单）
        all_katex = bool(re.search(r"katex", html, re.I)) and \
            not re.search(r"<(?:link|script|img|iframe)[^>]+(?:href|src)\s*=\s*[\"'](https?:)?//(?!cdn\.jsdelivr\.net/npm/katex)", html, re.I)
        if all_katex:
            add("OK", "EXTERNAL_RES", "外部资源 %d 处均为 KaTeX（数学公式必需），离线时数学块降级为字面量"
                % len(ext))
        else:
            add("FAIL", "EXTERNAL_RES", "存在 %d 处外部资源引用（离线打开会残缺）" % len(ext),
                "内嵌样式与素材：图片转 base64 或改用 CSS／字符／内联 SVG")
    else:
        add("OK", "EXTERNAL_RES", "无外部资源引用，离线可打开")

    if re.search(r"<style", html) and re.search(r"<script", html):
        add("OK", "SELF_CONTAINED", "样式与脚本已内嵌")
    else:
        add("WARN", "SELF_CONTAINED", "未同时检测到内嵌 <style> 与 <script>", "确认自包含与交互是否为页面必需")

    # 3 占位符残留
    ph = re.findall(r"__[A-Z_]{2,}__", html)
    todo = re.findall(r"\bTODO\b|\bFIXME\b|待补充|待填写", html)
    if ph:
        add("FAIL", "PLACEHOLDER", "存在 %d 处未替换占位符：%s" % (len(ph), set(ph)), "替换为空值或真实内容")
    else:
        add("OK", "PLACEHOLDER", "无未替换占位符")
    if todo:
        add("WARN", "TODO_LEFT", "存在 %d 处待办/待补字样" % len(todo), "定稿前替换为缺口徽标或补齐内容")
    else:
        add("OK", "TODO_LEFT", "无待办残留")

    # 4 标签配对与标题层级
    b = Balance()
    b.feed(html)
    if b.err or b.stack:
        detail = (b.err[:3] or []) + (["未闭合：%s" % b.stack] if b.stack else [])
        add("FAIL", "TAG_BALANCE", "标签不配对：%s" % "；".join(detail), "修闭合后再交付")
    else:
        add("OK", "TAG_BALANCE", "标签配对正常")

    h1n = b.h.count(1)
    hs = b.h
    if h1n == 1:
        add("OK", "H1_UNIQUE", "一级标题唯一")
    else:
        add("FAIL", "H1_UNIQUE", "一级标题数量为 %d（应为 1）" % h1n, "保留一个 h1，其余降级")
    jump = [(hs[i], hs[i + 1]) for i in range(len(hs) - 1) if hs[i + 1] - hs[i] > 1]
    if jump:
        add("WARN", "H_SKIP", "标题层级跳级：%s" % jump[:3], "补齐中间层级")
    else:
        add("OK", "H_SKIP", "标题层级连续")

    _emb = re.findall(r'<img[^>]+src="data:image', html)
    if _emb:
        add("OK", "IMG_EMBED", "%d 张图片已 base64 内嵌，离线可看" % len(_emb))
    _ai = len(re.findall(r'<span class="fig-ai-tag">', html))
    if _ai:
        add("OK", "AI_FIG", "%d 张 AI 生成配图已加「AI 配图」角标" % _ai)
    if b.imgs_no_alt:
        add("WARN", "IMG_ALT", "%d 张图片缺 alt" % b.imgs_no_alt, "补 alt（装饰性图片用 alt=\"\"）")
    else:
        add("OK", "IMG_ALT", "图片 alt 齐备或无图片")

    # 5 CSS 变量完整性
    used = set(re.findall(r"var\((--[\w-]+)", html))
    defined = set(re.findall(r"(--[\w-]+)\s*:", html))
    miss = used - defined
    if miss:
        add("FAIL", "CSS_VAR", "调用了未定义的变量：%s" % sorted(miss)[:6], "补齐变量定义")
    else:
        add("OK", "CSS_VAR", "CSS 变量定义完整（%d 个）" % len(defined))

    # 6 配色对比度
    blocks = parse_theme_blocks(html)
    if not blocks:
        add("WARN", "CONTRAST", "未解析到主题变量块，无法做对比度校验",
            "按 palettes.py 生成的变量块接入配色")
    else:
        worst, total, bad = [], 0, []
        for name, vs in blocks.items():
            rows = theme_contrast(vs)
            for label, ratio, gate, ok in rows:
                total += 1
                worst.append(ratio)
                if not ok:
                    bad.append("%s/%s=%.2f<%s" % (name, label, ratio, gate))
        if bad:
            add("FAIL", "CONTRAST", "对比度未达标：%s" % "；".join(bad[:5]), "换用达标配色或加深对应颜色")
        else:
            add("OK", "CONTRAST", "对比度全部达标（%d 项，最低 %.2f）" % (total, min(worst) if worst else 0))

    # 7 打印适配 / 目录 / 来源 / 缺口
    add("OK", "PRINT_CSS", "含 @media print 打印样式") if "@media print" in html else \
        add("WARN", "PRINT_CSS", "缺少 @media print 打印样式", "补打印规则并隐藏交互控件")

    n_h2 = len(re.findall(r"<h2", html))
    if n_h2 >= 4 and 'href="#' not in html:
        add("WARN", "TOC", "章节 %d 个但无锚点导航" % n_h2, "补目录或返回顶部导航")
    else:
        add("OK", "TOC", "章节导航就绪（章节 %d 个）" % n_h2)

    if re.search(r'class="src"|参考来源|数据来源', html):
        add("OK", "SOURCE_BLOCK", "含来源标注或来源区块")
    else:
        add("WARN", "SOURCE_BLOCK", "未见来源区块与数据来源行", "含数据的页面需挂来源区块")

    if "【待核" in html and not re.search(r'class="gap|信息缺口', html):
        add("WARN", "GAP_BLOCK", "正文含【待核】但无缺口区块", "补缺口区块，注明影响与补充渠道")
    else:
        add("OK", "GAP_BLOCK", "缺口标注与区块一致")

    # 8 体积
    if kb > a.max_kb:
        add("WARN", "SIZE", "体积 %.1fKB 超上限 %dKB" % (kb, a.max_kb), "压缩内嵌图片或精简样式")
    else:
        add("OK", "SIZE", "体积 %.1fKB（上限 %dKB）" % (kb, a.max_kb))

    # 8.5 内容密度（防空架子：组件多、正文少）
    try:
        _body = extract_text(html)
    except Exception:
        _body = ""
    _zh = len(re.findall(r"[\u4e00-\u9fff]", _body))
    _sec = max(1, len(re.findall(r"<h2", html)) - (1 if "参考来源" in html else 0))
    _per = _zh / float(_sec)
    if not a.no_density:
        if _per < a.density_min * 0.75:
            add("FAIL", "DENSITY", "正文密度不足：%d 章均 %.0f 字/章（下限 %d）" % (_sec, _per, a.density_min),
                "每章补充至 %d 字以上，避免只有组件骨架没有内容" % a.density_min)
        elif _per < a.density_min:
            add("WARN", "DENSITY", "正文密度接近下限：%d 章均 %.0f 字/章（目标 %d+）" % (_sec, _per, a.density_min),
                "补充章节内容或精简章节数")
        else:
            add("OK", "DENSITY", "正文密度充足：%d 章均 %.0f 字/章" % (_sec, _per))

    # 8.6 文风（黑话与序列化路标）
    if not a.no_tone:
        _JARGON = ["赋能", "抓手", "闭环", "链路", "颗粒度", "底层逻辑", "拉通", "沉淀", "对标对表"]
        _SERIAL = ["综上所述", "值得注意的是", "众所周知", "需要注意的是", "首先", "其次", "再次", "最后"]
        _hits = [w for w in (_JARGON + _SERIAL) if w in _body]
        if len(_hits) >= 3:
            add("FAIL", "AI_TONE", "文风命中黑话/序列化路标 %d 处：%s" % (len(_hits), "、".join(_hits)),
                "黑话改实指词，序列化改「一是…二是…」")
        elif _hits:
            add("WARN", "AI_TONE", "文风命中黑话/序列化路标：%s" % "、".join(_hits), "确认是否替换为平实表达")
        else:
            add("OK", "AI_TONE", "未见黑话与序列化路标")

    # 9 JS 语法（可选）
    if a.node:
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
        if scripts:
            tmp = os.path.join(os.path.dirname(os.path.abspath(p)), "_html_check_tmp.js")
            open(tmp, "w", encoding="utf-8").write("\n".join(scripts))
            try:
                r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True, timeout=30)
                if r.returncode == 0:
                    add("OK", "JS_SYNTAX", "JS 语法通过（node --check）")
                else:
                    add("FAIL", "JS_SYNTAX", "JS 语法错误：%s" % (r.stderr or "")[:200], "修正脚本语法")
            except FileNotFoundError:
                add("WARN", "JS_SYNTAX", "未安装 node，跳过 JS 语法校验")
            finally:
                os.path.exists(tmp) and os.remove(tmp)
        else:
            add("OK", "JS_SYNTAX", "无内嵌脚本")

    # 10 抽正文文本
    if a.text_out:
        txt = extract_text(html)
        open(a.text_out, "w", encoding="utf-8").write(txt)
        add("OK", "TEXT_OUT", "正文文本已导出（%d 字符）" % len(txt))

    # ===== v2.0 新增校验 =====
    # 11 callout 闭合校验（开标签数 vs callout-body 数）
    n_callout_open = len(re.findall(r'<div class="callout\s+callout-(?:info|warn|crit|ok)">', html))
    n_callout_body = len(re.findall(r'class="callout-body">', html))
    if n_callout_open and n_callout_open != n_callout_body:
        add("FAIL", "CALLOUT", "callout 容器不平衡：开 %d / callout-body %d"
            % (n_callout_open, n_callout_body), "检查 > [!info] 等语法是否完整闭合")
    elif n_callout_open:
        add("OK", "CALLOUT", "callout 容器平衡（%d 个）" % n_callout_open)

    # 12 锚点完整性：href="#xxx" 对应的 id 必须存在
    href_ids = set(re.findall(r'href="#([^"]+)"', html))
    body_ids = set(re.findall(r'<section\s+id="([^"]+)"', html))
    body_ids |= set(m[1] for m in re.findall(r'<h([1-6])\s+id="([^"]+)"', html))  # 也接受标题内 id
    body_ids |= set(re.findall(r'<[a-zA-Z][a-zA-Z0-9]*[^>]*\sid="([^"]+)"', html))  # 任意元素 id（含 #content 等）
    missing = href_ids - body_ids
    if missing:
        add("WARN", "ANCHORS", "锚点指向不存在：%s" % ",".join(sorted(missing)),
            "补齐 section id 或删除悬空 href")
    elif href_ids:
        add("OK", "ANCHORS", "锚点 %d 个全部存在" % len(href_ids))

    # 13 TOC 链接数与章节数一致性
    toc_links = re.findall(r'<a href="#(s\d+)">', html)
    sec_count = len(re.findall(r'<section\s+id="s\d+"', html))
    if toc_links and sec_count and len(toc_links) != sec_count:
        add("WARN", "TOC_MATCH", "TOC 链接 %d 个与章节 %d 个不一致" % (len(toc_links), sec_count),
            "保持 TOC 与章节同步")
    elif toc_links:
        add("OK", "TOC_MATCH", "TOC 链接 %d 个与章节 %d 个一致" % (len(toc_links), sec_count))

    # 14 数学公式容器平衡
    n_math_inline = len(re.findall(r'<span class="math-inline">', html))
    n_math_block = len(re.findall(r'<div class="math-block">', html))
    if n_math_inline + n_math_block:
        add("OK", "MATH", "数学公式 %d 行内 + %d 块" % (n_math_inline, n_math_block))

    # ===== v2.1 新增校验 =====
    # 15 胶囊目录栏（章节 ≥ 3 时必挂）
    sec_count_new = len(re.findall(r'<section id="s\d+"', html))
    has_tabbar = '<div class="fixed-toc" id="chapterNav"' in html
    _mnav = re.search(r'<div class="fixed-toc" id="chapterNav">(.*?)</div>', html, re.S)
    n_tabs = len(re.findall(r'<a class="chapter-tab"', _mnav.group(1) if _mnav else ""))
    if sec_count_new >= 3:
        if not has_tabbar:
            add("FAIL", "TABBAR", "章节 ≥ 3 但未生成顶部胶囊目录",
                "检查 build_html 是否正常生成 chapter-nav")
        elif n_tabs != sec_count_new:
            add("WARN", "TABBAR", "胶囊目录 %d 项与章节 %d 个不一致" % (n_tabs, sec_count_new),
                "保持 tabbar 与章节同步")
        else:
            add("OK", "TABBAR", "顶部胶囊目录 %d 项与章节 %d 个一致" % (n_tabs, sec_count_new))
    if 'id="tocDrawer"' in html and 'id="tocBtn"' in html:
        add("OK", "MOBILE_TOC", "移动端抽屉式目录已注入（≤640px 启用，含配色行）")
    # 15b 内容动效层（v4.11.0，仅提示不判 FAIL）
    has_fx_layer = 'anim-ready' in html
    has_fx_comp = bool(re.search(r'class="(?:kpi-card|b-cell|stat-cell|bar-fill|tl-item|phase|law-card)"', html))
    if has_fx_layer:
        add("OK", "FX", "内容动效层已注入（卡片错峰淡入/条形生长/图表淡入/数字滚动）")
    elif has_fx_comp:
        add("WARN", "FX", "页面含数据卡等组件但未注入内容动效层",
            "检查 CSS_FIXED/JS_FIXED 是否含 anim-ready 动效层")

    # 16 章节 hero 卡（每节必备 STEP 徽标 + chapter-hero 容器）
    n_hero = len(re.findall(r'<div class="chapter-hero">', html))
    n_step = len(re.findall(r'<span class="step-badge">STEP ', html))
    if n_hero and n_hero != sec_count_new:
        add("WARN", "HERO", "chapter-hero %d 个，章节 %d 个不一致" % (n_hero, sec_count_new))
    elif n_hero:
        add("OK", "HERO", "章节 hero 卡 %d 个（含 STEP 徽标 %d 个）" % (n_hero, n_step))

    # 17 scroll-spy JS 注入（章节 ≥ 3 时必备）
    if sec_count_new >= 3:
        has_spy = "scroll-spy" in html or "setActive" in html
        if has_spy:
            add("OK", "SCROLL_SPY", "滚动联动 JS 已注入")
        else:
            add("WARN", "SCROLL_SPY", "章节 ≥ 3 但未注入 scroll-spy JS",
                "确认 build_report JS_FIXED 包含 IntersectionObserver 联动逻辑")

    # ===== v3.0 新增校验 =====
    # 18 章节编号方块（v3 章节头 sec-no 数应与章节数一致）
    n_secno = len(re.findall(r'<span class="sec-no">', html))
    if sec_count_new >= 3:
        if n_secno == sec_count_new:
            add("OK", "SEC_NO", "章节编号方块 %d 个与章节一致" % n_secno)
        elif n_secno:
            add("WARN", "SEC_NO", "sec-no %d 个与章节 %d 个不一致" % (n_secno, sec_count_new),
                "检查 build_html 章节头模板是否统一渲染")

    # 19 章内二次目录（h3 自动收集为「本节要点」）
    n_h3id = len(re.findall(r'<h3 id="', html))
    n_subtoc = len(re.findall(r'<div class="sub-toc">', html))
    if n_subtoc:
        add("OK", "SUB_TOC", "章内二次目录 %d 处（h3 锚点 %d 个）" % (n_subtoc, n_h3id))
    elif n_h3id >= 2:
        add("OK", "SUB_TOC", "h3 锚点 %d 个（未触发章内二次目录，需单章 h3 ≥ 2）" % n_h3id)

    # 20 围栏残留（:::xxx 未解析即渲染进正文）
    # 先剥离 <style>/<script>，避免 CSS 注释与 JS 字符串中的 ::: 误报
    _bo = re.sub(r'<style\b.*?</style>', '', html, flags=re.S)
    _bo = re.sub(r'<script\b.*?</script>', '', _bo, flags=re.S)
    leak = re.findall(r'(?<![\w:]):::[a-zA-Z][\w-]*', _bo)
    if leak:
        add("FAIL", "FENCE_LEAK", "围栏未解析，正文残留 %d 处：%s" % (len(leak), sorted(set(leak))),
            "检查围栏开（:::name）与闭（单独一行 :::）标记成对")
    else:
        add("OK", "FENCE_LEAK", "无未解析围栏残留")

    # ===== v6.0.0 无障碍与工程校验（提示项，不判 FAIL） =====
    add("OK", "FOCUS_VISIBLE", "含 :focus-visible 焦点样式（键盘导航可见）") if ":focus-visible" in html else \
        add("WARN", "FOCUS_VISIBLE", "缺少 :focus-visible 焦点样式", "补键盘焦点可见样式")
    if 'class="skip-link"' in html and 'href="#content"' in html:
        add("OK", "SKIP_LINK", "含「跳至正文」链接")
    else:
        add("WARN", "SKIP_LINK", "缺少「跳至正文」链接", "补 skip-link 与 #content 锚点")
    if 'property="og:title"' in html:
        add("OK", "OG_META", "含 Open Graph 分享元信息（转发有标题卡）")
    else:
        add("WARN", "OG_META", "缺少 og:title 等分享元信息", "补 og:title/og:description 便于转发")
    add("OK", "THEME_COLOR", "含 theme-color（移动端地址栏配色）") if 'name="theme-color"' in html else \
        add("WARN", "THEME_COLOR", "缺少 theme-color", "补 <meta name=\"theme-color\">")
    _nth = len(re.findall(r"<th\b", html))
    _nsco = len(re.findall(r"<th[^>]*\bscope=", html))
    if _nth and _nsco == _nth:
        add("OK", "TH_SCOPE", "表头 scope 齐备（%d 个）" % _nth)
    elif _nth:
        add("WARN", "TH_SCOPE", "表头 %d 个中 %d 个缺 scope" % (_nth, _nth - _nsco),
            '给表头 th 补 scope="col"')
    # ===== v7.0.0 设计纪律检查（提示项，不判 FAIL） =====
    def _strip_print(h):
        out = h
        i = out.find('@media print')
        while i != -1:
            j = out.find('{', i)
            if j == -1:
                break
            depth = 0
            k = j
            while k < len(out):
                if out[k] == '{':
                    depth += 1
                elif out[k] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            out = out[:i] + out[k + 1:]
            i = out.find('@media print')
        return out

    _screen = _strip_print(html)
    _pure = re.findall(r'#(?:0{3}|0{6}|f{3}|f{6})\b', _screen, re.I)
    _pure += re.findall(r'(?:color|background|background-color)\s*:\s*(?:black|white)\b', _screen, re.I)
    if _pure:
        add("WARN", "PURE_BW", "使用纯黑或纯白 %d 处" % len(_pure),
            "改用近黑近白（如 #0d1117 / #f7f6f3）")
    else:
        add("OK", "PURE_BW", "未使用纯黑纯白")
    _cjk_needed = re.search(r'[\u4e00-\u9fff]', html)
    _cjk_font = re.search(r'PingFang|Microsoft YaHei|Noto Sans SC|Noto Serif SC|Source Han|Songti|SimSun|Hiragino|YaHei', html)
    if _cjk_needed and not _cjk_font:
        add("WARN", "CJK_FONT", "中文页面未声明中文字体栈",
            '字体栈补 "PingFang SC" / "Microsoft YaHei" 等中文回退')
    else:
        add("OK", "CJK_FONT", "字体栈含中文回退")
    if "aria-current" in html:
        add("OK", "ARIA_CURRENT", "当前章节标注 aria-current（读屏可感知位置）")
    add("OK", "PAGE_RULE", "含 @page 打印页边距规则") if "@page" in html else \
        add("WARN", "PAGE_RULE", "缺少 @page 规则", "补 @page 设置打印页边距与版心")

    fails = [r for r in RES if r["level"] == "FAIL"]
    warns = [r for r in RES if r["level"] == "WARN"]

    if a.json:
        print(json.dumps({"file": p, "kb": round(kb, 1), "fail": len(fails),
                          "warn": len(warns), "result": "FAIL" if fails else "PASS",
                          "items": RES}, ensure_ascii=False, indent=1))
    else:
        print("=" * 66)
        print("HTML 结构级自检　%s　%.1fKB" % (os.path.basename(p), kb))
        print("=" * 66)
        for lv in ("FAIL", "WARN", "OK"):
            for r in [x for x in RES if x["level"] == lv]:
                print("[%s] %-14s %s" % (lv, r["code"], r["msg"]))
                if r["fix"] and lv != "OK":
                    print("      → 修复：%s" % r["fix"])
        print("-" * 66)
        print("FAIL=%d  WARN=%d  RESULT=%s" % (len(fails), len(warns), "FAIL" if fails else "PASS"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
