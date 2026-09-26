#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
theme_apply.py — theme-factory 主题落地器（v1.0.0）

把 themes/*.md 的成套主题（四色 + 两字体）注入任意 HTML，一次调用完成"生成 → 换肤"。
双策略：① 重写目标 :root 通用 CSS 变量；② 对硬编码色值做映射替换（语义色豁免）。
中文字体回退链自动补齐（拉丁字体不充当中文正文字体）。

子命令
  list                        列出 10 套主题及四色
  info   <theme>              显示单套主题完整规格（含派生槽位与对比度）
  apply  -t <theme> -i in.html [-o out.html] [--mode light|dark] [--keep #hex,#hex]
                              给 HTML 换肤，输出映射表 + 对比度校验
  demo   -o out.html          生成"10 套主题实时切换"演示页
  check  <hex> [#hex2]        对比度校验（正文/背景须 ≥4.5:1，大字/图形 ≥3:1）
  palette -o out.png          生成 10 套主题色板总览图
"""
import argparse, json, re, sys, pathlib

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
THEME_DIR = SKILL_DIR / "themes"

CN_NAME = {
    "ocean-depths": "深海之境", "sunset-boulevard": "落日大道", "forest-canopy": "森林之冠",
    "modern-minimalist": "现代极简", "golden-hour": "金色时刻", "arctic-frost": "极地霜华",
    "desert-rose": "沙漠玫瑰", "tech-innovation": "科技创新", "botanical-garden": "植物园",
    "midnight-galaxy": "午夜星河",
}
# 10 套主题的槽位标定（light 模式）。色值取自 themes/*.md 四色色板或其明度派生（mix 白/黑），
# 保证主色在成品中始终可辨；表外主题自动按"对比度驱动"规则分配。
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

# 语义色（警示红 / 通过绿 / 提示黄）不随主题变化，保持判断含义稳定
SEMANTIC_KEEP = {
    "#c0392b", "#7d2b23", "#fff5f5", "#fdecea", "#e74c3c",
    "#6da33f", "#e6f2e2", "#2e7d32", "#e8f5e9",
    "#d99b1a", "#fff3cd", "#f7f8e6", "#a9ab63", "#8a5a00",
}
PURE = {"#fff", "#ffffff", "#fefefe", "#000", "#000000"}  # 纯黑纯白不动

CJK_SANS = '"Noto Sans CJK SC","Source Han Sans SC","PingFang SC","Microsoft YaHei",sans-serif'
CJK_SERIF = '"Noto Serif CJK SC","Source Han Serif SC","SimSun","Songti SC",serif'


# ---------- 色彩工具 ----------
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


# ---------- 主题解析与槽位派生 ----------
def parse_theme(slug):
    p = THEME_DIR / (slug + ".md")
    if not p.exists():
        raise SystemExit("未找到主题：%s（可选：%s）" % (slug, ", ".join(CN_NAME)))
    txt = p.read_text(encoding="utf-8")
    cols = re.findall(r"\*\*(.+?)\*\*:\s*`(#[0-9a-fA-F]{6})`\s*-\s*(.+)", txt)
    head = re.search(r"Headers\*\*:\s*(.+)", txt)
    body = re.search(r"Body Text\*\*:\s*(.+)", txt)
    return {
        "slug": slug, "cn": CN_NAME.get(slug, slug),
        "colors": [{"label": a.strip(), "hex": b.lower(), "desc": c.strip()} for a, b, c in cols],
        "heading": (head.group(1).strip() if head else "Noto Sans CJK SC"),
        "body": (body.group(1).strip() if body else "Noto Sans CJK SC"),
    }


def derive_slots(t, mode="light"):
    """把主题四色映射到 background/primary/accent/text 槽位，并派生 line/sub。
    分配原则：底色取最亮色；正文取与底色对比度最高者；主色在剩余色中取对比度最高者，
    不足 3:1 时压暗兜底，保证主色在成品中始终可辨。"""
    hexes = list(dict.fromkeys(c["hex"] for c in t["colors"]))
    if mode == "dark":
        bg = min(hexes, key=luminance)
        ink = max(hexes, key=luminance)
        rest = [h for h in hexes if h != bg] or [ink]
        primary = max(rest, key=lambda c: contrast(c, bg))
        accent = max([h for h in rest if h != primary] or rest, key=saturation)
        card, line, sub = mix(bg, ink, 0.10), mix(bg, ink, 0.22), mix(ink, bg, 0.40)
    else:
        tbl = SLOT_TABLE.get(t["slug"])
        if tbl:
            bg, ink, primary, accent = tbl["bg"], tbl["ink"], tbl["primary"], tbl["accent"]
        else:
            bg = max(hexes, key=luminance)
            if saturation(bg) > 0.22:        # 高饱和亮色（暖沙/芥末黄等）提亮为底色
                bg = mix(bg, "#ffffff", 0.60)
            ink = max(hexes, key=lambda c: contrast(c, bg))
            rest = [h for h in hexes if h != ink]
            primary = max(rest, key=lambda c: contrast(c, bg))
            if contrast(primary, bg) < 3:    # 主色可读性兜底
                primary = mix(primary, "#000000", 0.40)
            accent = max([h for h in rest if h != primary] or rest, key=saturation)
        card, line, sub = "#ffffff", mix(bg, ink, 0.14), mix(ink, bg, 0.42)
    is_serif = "serif" in t["body"].lower() or "Serif" in t["body"]
    s = {
        "bg": bg, "card": card, "line": line, "ink": ink, "sub": sub,
        "primary": primary, "accent": accent,
        "heading_font": t["heading"], "body_font": t["body"],
        "cjk_head": CJK_SERIF if "Serif" in t["heading"] else CJK_SANS,
        "cjk_body": CJK_SERIF if is_serif else CJK_SANS,
    }
    s["heading_stack"] = "%s,%s,sans-serif" % (s["cjk_head"], t["heading"])
    s["body_stack"] = "%s,%s,sans-serif" % (s["cjk_body"], t["body"])
    return s


# ---------- 换肤 ----------
VAR_KEYS = {
    "bg": ("bg", "background", "canvas", "page", "base"),
    "card": ("card", "surface", "panel", "box", "block", "white"),
    "line": ("line", "border", "divider", "rule", "stroke", "edge"),
    "ink": ("ink", "text", "fg", "font", "title", "dark", "main-text"),
    "sub": ("sub", "muted", "secondary", "gray", "grey", "hint", "desc"),
    "primary": ("primary", "accent", "main", "brand", "theme", "key", "link"),
}


def rewrite_root_vars(html, s):
    """重写/补齐目标 :root 中的通用变量，非通用变量原样保留。"""
    m = re.search(r":root\s*\{([^}]*)\}", html)
    if not m:
        inject = ":root{%s}\n" % ";".join("--%s:%s" % (k, s[k]) for k in
                                          ("bg", "card", "line", "ink", "sub", "primary", "accent"))
        return html.replace("<style>", "<style>\n" + inject, 1) if "<style>" in html else html
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
    if changed:
        return html[:m.start()] + ":root{%s}" % newbody + html[m.end():]
    return html


def build_color_map(html, s, keep=None):
    """扫描硬编码色值并按色相/明度归类到主题槽位。返回 {old:new}。"""
    keep = {k.lower() for k in (keep or [])} | SEMANTIC_KEEP | PURE
    found = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", html)}
    mapping, used_primary = {}, False
    for hx in sorted(found):
        if hx in keep:
            continue
        sat, lum = saturation(hx), luminance(hx)
        if sat > 0.30:                       # 彩色 → 主色/强调色
            if not used_primary and contrast(hx, "#ffffff") > 1.6:
                mapping[hx] = s["primary"]; used_primary = True
            else:
                mapping[hx] = s["accent"]
        elif lum >= 0.92:                    # 浅底 → 页面底色
            mapping[hx] = s["bg"]
        elif lum >= 0.55:                    # 浅灰 → 分隔线
            mapping[hx] = s["line"]
        elif lum <= 0.10:                    # 深灰 → 正文
            mapping[hx] = s["ink"]
        else:                                # 中间灰 → 次要文字
            mapping[hx] = s["sub"]
    return mapping


def apply_theme(html, s, keep=None):
    # 顺序不可颠倒：先基于原始 HTML 做色值映射，再注入/重写 CSS 变量，
    # 否则注入的主题色会被映射器二次替换（链式替换）。
    mapping = build_color_map(html, s, keep)
    for old in sorted(mapping, key=len, reverse=True):
        html = re.sub(re.escape(old), mapping[old], html, flags=re.I)
    html = rewrite_root_vars(html, s)
    font_css = (
        "\n/* theme-factory 字体槽位（中文字体回退链已补齐） */\n"
        "body,td,th,p,li,div,span{font-family:%s}\n"
        "h1,h2,h3,h4,h5,th,.kpi-num,.metric{font-family:%s}\n"
    ) % (s["body_stack"], s["heading_stack"])
    if "</style>" in html:
        html = html.replace("</style>", font_css + "</style>", 1)
    return html, mapping


# ---------- 演示页 ----------
DEMO_TPL = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>专业视觉主题工厂 · 10 套主题实时切换演示</title>
<style>
:root{--bg:#f1faee;--card:#ffffff;--line:#dfe7e2;--ink:#1a2332;--sub:#6b7a86;--primary:#2d8b8b;--accent:#a8dadc;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.65;
     font-family:"Noto Sans CJK SC",sans-serif;transition:background .25s,color .25s}
.wrap{max-width:940px;margin:0 auto;padding:26px 22px 46px}
.switch{position:sticky;top:0;z-index:9;background:var(--card);border:1px solid var(--line);
        border-radius:12px;padding:12px 14px;margin-bottom:22px;box-shadow:0 2px 10px rgba(0,0,0,.05)}
.switch .lb{font-size:12.5px;color:var(--sub);margin-bottom:9px;letter-spacing:.4px}
.tbtn{display:inline-flex;align-items:center;gap:7px;margin:0 8px 8px 0;padding:6px 11px;border-radius:20px;
      border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer;font-size:12.5px;
      font-family:inherit;transition:.18s}
.tbtn:hover{transform:translateY(-1px)}
.tbtn .sw{width:13px;height:13px;border-radius:50%;display:inline-block}
.tbtn.on{border-color:var(--primary);box-shadow:0 0 0 2px var(--accent) inset,0 0 0 1px var(--primary)}
header{border-bottom:3px solid var(--primary);padding-bottom:16px;margin-bottom:22px}
h1{margin:0;font-size:26px;letter-spacing:.5px}
.sub2{color:var(--sub);font-size:14px;margin-top:7px}
.meta{color:var(--sub);font-size:12.5px;margin-top:12px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin:22px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 16px;
     border-top:3px solid var(--primary)}
.kpi-num{font-size:25px;font-weight:700;color:var(--primary);letter-spacing:.3px}
.kpi-lab{font-size:12.5px;color:var(--sub);margin-top:5px}
h2{font-size:17px;margin:28px 0 12px;padding-left:11px;border-left:4px solid var(--primary)}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden;
      border:1px solid var(--line);font-size:14px}
th{background:var(--bg);color:var(--ink);text-align:left;padding:10px 12px;font-weight:600;
   border-bottom:2px solid var(--line)}
td{padding:9px 12px;border-top:1px solid var(--line)}
tbody tr:nth-child(even){background:var(--bg)}
.alert{background:#fff5f5;border-left:4px solid #c0392b;border-radius:10px;padding:13px 15px;
       margin:18px 0;color:#7d2b23;font-size:14px}
.bars{margin:14px 0}
.bar{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 14px;margin-bottom:9px}
.bar .t{display:flex;justify-content:space-between;font-size:13.5px;margin-bottom:7px}
.bar .track{height:9px;background:var(--line);border-radius:6px;overflow:hidden}
.bar .fill{height:100%;background:linear-gradient(90deg,var(--primary),var(--accent));border-radius:6px}
.legend{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;color:var(--sub);margin-top:10px}
.legend i{width:12px;height:12px;border-radius:3px;display:inline-block;margin-right:6px;vertical-align:-1px}
footer{margin-top:34px;padding-top:16px;border-top:1px solid var(--line);color:var(--sub);font-size:12.5px;text-align:center}
@media(max-width:760px){.kpis{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class="wrap">

<div class="switch">
  <div class="lb">当前主题：<b id="tname">深海之境 Ocean Depths</b>　— 点击下方按钮实时换肤</div>
  <div id="tbar"></div>
</div>

<header>
  <h1>某市项目污水处理厂 · 运营季度分析报告</h1>
  <div class="sub2">本页为「主题工厂 × A 档技能」编排效果模拟 · 数据为示意值</div>
  <div class="meta">编制：某水务项目公司　|　报告期：2026 年第三季度　|　主题：<span id="tname2">深海之境</span></div>
</header>

<div class="kpis">
  <div class="kpi"><div class="kpi-num">18,420</div><div class="kpi-lab">处理水量（万吨）</div></div>
  <div class="kpi"><div class="kpi-num">98.6%</div><div class="kpi-lab">水质达标率</div></div>
  <div class="kpi"><div class="kpi-num">0.312</div><div class="kpi-lab">吨水电耗（kW·h/t）</div></div>
  <div class="kpi"><div class="kpi-num">1.086</div><div class="kpi-lab">吨水成本（元/t）</div></div>
</div>

<h2>一、各厂运行指标对比</h2>
<table>
<thead><tr><th>厂区</th><th>处理量（万吨）</th><th>达标率</th><th>吨水电耗</th><th>状态</th></tr></thead>
<tbody>
<tr><td>城区污水处理厂</td><td>6,820</td><td>99.2%</td><td>0.298</td><td>达标</td></tr>
<tr><td>某镇污水处理厂（一）</td><td>3,150</td><td>98.4%</td><td>0.316</td><td>达标</td></tr>
<tr><td>某镇污水处理厂（二）</td><td>2,940</td><td>97.1%</td><td>0.341</td><td>达标</td></tr>
<tr><td>某镇污水处理厂（三）</td><td>1,860</td><td>96.8%</td><td>0.352</td><td>达标</td></tr>
</tbody></table>

<h2>二、指标完成度</h2>
<div class="bars">
  <div class="bar"><div class="t"><span>水质达标率</span><span>98.6% / 目标 95%</span></div><div class="track"><div class="fill" style="width:98%"></div></div></div>
  <div class="bar"><div class="t"><span>设备完好率</span><span>96.3% / 目标 95%</span></div><div class="track"><div class="fill" style="width:96%"></div></div></div>
  <div class="bar"><div class="t"><span>吨水电耗控制</span><span>0.312 / 目标 0.330</span></div><div class="track"><div class="fill" style="width:88%"></div></div></div>
</div>

<div class="alert">提示：本页语义色（警示红 / 通过绿 / 提示黄）不随主题变化，确保"达标 / 预警"判断含义在任何主题下都一致。</div>
<div class="legend"><span><i style="background:var(--primary)"></i>主色 primary</span>
<span><i style="background:var(--accent)"></i>强调色 accent</span>
<span><i style="background:var(--ink)"></i>正文 text</span>
<span><i style="background:var(--bg);border:1px solid var(--line)"></i>底色 background</span></div>

<footer>theme-factory · 专业视觉主题工厂　|　四色色板 + 标题/正文字体配对　|　对比度已按 WCAG 校验</footer>
</div>
<script>
const THEMES = __THEMES__;
const root = document.documentElement;
function applyTheme(k){
  const t = THEMES[k];
  ["bg","card","line","ink","sub","primary","accent"].forEach(s=>root.style.setProperty("--"+s,t[s]));
  document.getElementById("tname").textContent = t.cn + " " + t.en;
  document.getElementById("tname2").textContent = t.cn;
  document.querySelectorAll(".tbtn").forEach(b=>b.classList.toggle("on", b.dataset.k===k));
}
const bar = document.getElementById("tbar");
Object.keys(THEMES).forEach(k=>{
  const t=THEMES[k], b=document.createElement("button");
  b.className="tbtn"; b.dataset.k=k;
  b.innerHTML='<span class="sw" style="background:linear-gradient(135deg,'+t.primary+','+t.accent+')"></span>'+t.cn;
  b.onclick=()=>applyTheme(k); bar.appendChild(b);
});
applyTheme(__DEFAULT__);
</script></body></html>"""


def cmd_demo(out):
    data = {}
    for slug in CN_NAME:
        t = parse_theme(slug)
        s = derive_slots(t, "light")
        data[slug] = {"cn": t["cn"], "en": slug.replace("-", " ").title(),
                      **{k: s[k] for k in ("bg", "card", "line", "ink", "sub", "primary", "accent")}}
    html = DEMO_TPL.replace("__THEMES__", json.dumps(data, ensure_ascii=False)).replace("__DEFAULT__", '"ocean-depths"')
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out).write_text(html, encoding="utf-8")
    print("已生成演示页：%s（%d 套主题可实时切换）" % (out, len(data)))


# ---------- 命令 ----------
def cmd_list():
    print("%-20s %-8s %s" % ("主题 slug", "中文名", "四色色板"))
    for slug in CN_NAME:
        t = parse_theme(slug)
        print("%-20s %-8s %s" % (slug, t["cn"], " ".join(c["hex"] for c in t["colors"])))


def cmd_info(slug):
    t = parse_theme(slug)
    s = derive_slots(t, "light")
    print("主题：%s（%s）" % (t["cn"], slug))
    print("四色色板：")
    for c in t["colors"]:
        print("  %-12s %s  %s" % (c["label"], c["hex"], c["desc"]))
    print("字体：标题=%s / 正文=%s" % (t["heading"], t["body"]))
    print("派生槽位（light 模式）：")
    for k in ("bg", "card", "line", "ink", "sub", "primary", "accent"):
        print("  %-9s %s" % (k, s[k]))
    print("对比度校验：正文/背景=%.2f（须≥4.5）  主色/背景=%.2f（大字须≥3）"
          % (contrast(s["ink"], s["bg"]), contrast(s["primary"], s["bg"])))


def cmd_apply(t_slug, inp, out, mode, keep):
    t = parse_theme(t_slug)
    s = derive_slots(t, mode)
    src = pathlib.Path(inp).read_text(encoding="utf-8")
    new_html, mapping = apply_theme(src, s, keep)
    out = out or (str(pathlib.Path(inp).with_suffix("")) + "_" + t_slug + ".html")
    pathlib.Path(out).write_text(new_html, encoding="utf-8")
    print("换肤完成：%s → %s" % (inp, out))
    print("主题：%s（%s，%s 模式）" % (t["cn"], t_slug, mode))
    print("色值映射（%d 条，语义色已豁免）：" % len(mapping))
    for k in sorted(mapping):
        print("  %s → %s" % (k, mapping[k]))
    print("对比度：正文/背景=%.2f  主色/背景=%.2f"
          % (contrast(s["ink"], s["bg"]), contrast(s["primary"], s["bg"])))


def cmd_check(hexes):
    if len(hexes) == 1:
        print("用法：check <前景色> <背景色>")
        return
    r = contrast(hexes[0], hexes[1])
    print("对比度 %s / %s = %.2f　%s" % (hexes[0], hexes[1], r,
          "通过（正文≥4.5）" if r >= 4.5 else ("通过（大字/图形≥3）" if r >= 3 else "不达标")))


def cmd_palette(out):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise SystemExit("需安装 Pillow：pip install pillow")
    fp = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    fb = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    def F(sz, bold=False):
        try:
            return ImageFont.truetype(fb if bold else fp, sz, index=0)
        except Exception:
            return ImageFont.load_default()
    W, RH, PAD = 1180, 108, 34
    H = PAD * 2 + 74 + len(CN_NAME) * RH
    img = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(img)
    d.text((PAD, PAD), "专业视觉主题工厂 · 10 套主题色板总览", font=F(27, True), fill="#1a2332")
    d.text((PAD, PAD + 40), "四色色板（background / primary / accent / text）+ 标题·正文字体配对，可一键落到 HTML / PPT / Word",
           font=F(14), fill="#6b7a86")
    y = PAD + 74
    for slug in CN_NAME:
        t = parse_theme(slug)
        s = derive_slots(t, "light")
        d.text((PAD, y + 10), t["cn"], font=F(17, True), fill=s["ink"])
        d.text((PAD, y + 38), slug, font=F(12), fill="#8a97a3")
        x = 250
        for slot, lab in (("bg", "bg"), ("primary", "primary"), ("accent", "accent"), ("ink", "text")):
            hexv = s[slot]
            d.rounded_rectangle([x, y + 8, x + 150, y + 78], radius=9, fill=hexv,
                                outline="#e2e6ea" if luminance(hexv) > 0.9 else None, width=1)
            tc = "#ffffff" if luminance(hexv) < 0.62 else "#2b3138"
            d.text((x + 12, y + 22), hexv.upper(), font=F(13, True), fill=tc)
            d.text((x + 12, y + 46), lab, font=F(11), fill=tc)
            x += 162
        d.text((x + 6, y + 16), t["heading"], font=F(13, True), fill=s["ink"])
        d.text((x + 6, y + 38), t["body"], font=F(12), fill="#8a97a3")
        d.text((x + 6, y + 58), "对比度 %.2f" % contrast(s["ink"], s["bg"]), font=F(11), fill="#8a97a3")
        d.line([PAD, y + RH - 2, W - PAD, y + RH - 2], fill="#eef2f7", width=1)
        y += RH
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("已生成色板总览图：%s（%d×%d）" % (out, W, H))


def main():
    ap = argparse.ArgumentParser(description="theme-factory 主题落地器")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    p = sub.add_parser("info"); p.add_argument("theme")
    p = sub.add_parser("apply")
    p.add_argument("-t", "--theme", required=True)
    p.add_argument("-i", "--input", required=True)
    p.add_argument("-o", "--output")
    p.add_argument("--mode", choices=["light", "dark"], default="light")
    p.add_argument("--keep", default="")
    p = sub.add_parser("demo"); p.add_argument("-o", "--output", default="主题工厂演示.html")
    p = sub.add_parser("check"); p.add_argument("colors", nargs="*")
    p = sub.add_parser("palette"); p.add_argument("-o", "--output", default="主题色板总览.png")
    a = ap.parse_args()
    if a.cmd == "list": cmd_list()
    elif a.cmd == "info": cmd_info(a.theme)
    elif a.cmd == "apply":
        cmd_apply(a.theme, a.input, a.output, a.mode, [x.strip() for x in a.keep.split(",") if x.strip()])
    elif a.cmd == "demo": cmd_demo(a.output)
    elif a.cmd == "check": cmd_check(a.colors)
    elif a.cmd == "palette": cmd_palette(a.output)
    else: ap.print_help()


if __name__ == "__main__":
    main()
