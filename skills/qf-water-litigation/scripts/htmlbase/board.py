#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""board.py —— 数据指标看板：JSON → 底座级单文件 HTML 看板（KPI 卡 + 条形对比 + 阈值预警）

定位：为「数据/测算/台账」类技能提供 HTML 看板伴生交付，纯 CSS 可视化（无外链图表库），
复用 html-report-builder 的十套配色、主题切换、返回顶部与打印适配。

用法：
  python3 board.py --init --out board.json                 生成数据模板
  python3 board.py --data board.json -o 看板.html          构建看板
  python3 board.py --data board.json -o 看板.html --theme galaxy --check

看板 JSON 结构：
  title/subtitle/audience/date/theme
  kpis   : [{label,value,unit,delta,status(ok|warn|crit)}]
  groups : [{title, bars:[{label,value,max,status}], table:{head:[],rows:[[]]}}]
  alerts : [{item,rule,level(ok|warn|crit)}]
  footer : {unit,author,note}
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from build_report import CSS_FIXED, JS_FIXED, esc  # noqa
    from palettes import PALETTES, BY_ID, css_block  # noqa
except Exception as e:  # pragma: no cover
    print("无法导入底座模块：%s" % e, file=sys.stderr)
    sys.exit(3)

BOARD_CSS = """
:root{--ok:#1f9d63;--warn:#c07f00;--crit:#c0392b}
.kpi-grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));margin:18px 0}
.kpi{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--accent);
  border-radius:12px;padding:14px 16px}
.kpi.st-ok{border-left-color:var(--ok)} .kpi.st-warn{border-left-color:var(--warn)} .kpi.st-crit{border-left-color:var(--crit)}
.kpi .lb{font-size:12.5px;color:var(--muted)}
.kpi .v{font-size:26px;font-weight:700;color:var(--accent);line-height:1.15;margin:5px 0 2px}
.kpi .foot{font-size:12.5px;color:var(--muted)}
.kpi .foot .up{color:var(--crit)} .kpi .foot .down{color:var(--ok)}
.barrow{display:grid;grid-template-columns:150px 1fr 72px;gap:10px;align-items:center;margin:7px 0}
.bartrack{height:13px;background:var(--surface-2);border:1px solid var(--border);border-radius:7px;overflow:hidden}
.barfill{height:100%;border-radius:7px;background:linear-gradient(90deg,var(--accent),var(--accent-2))}
.barfill.st-ok{background:var(--ok)} .barfill.st-warn{background:var(--warn)} .barfill.st-crit{background:var(--crit)}
.barval{font-size:12.5px;color:var(--muted);text-align:right}
.alert td:first-child{font-weight:600}
.badge{display:inline-block;border-radius:5px;padding:0 7px;font-size:12px;font-weight:600}
.badge.b-ok{color:var(--ok);background:rgba(31,157,99,.14)}
.badge.b-warn{color:var(--warn);background:rgba(192,127,0,.16)}
.badge.b-crit{color:var(--crit);background:rgba(192,57,43,.14)}
.alert tr.lv-crit td{background:rgba(192,57,43,.10)}
.alert tr.lv-warn td{background:rgba(192,127,0,.10)}
.alert tr.lv-ok td{background:rgba(31,157,99,.10)}
"""

TMPL = {
    "_说明": "填好后执行：python3 board.py --data board.json -o 看板.html --check",
    "title": "污水处理项目投资测算看板", "subtitle": "一句话说明本看板回答什么问题",
    "audience": "股东会", "date": "2026-09-21", "theme": "galaxy",
    "kpis": [
        {"label": "总投资", "value": "12,480", "unit": "万元", "delta": "+2.1%", "status": "ok"},
        {"label": "全投资 IRR", "value": "7.85", "unit": "%", "delta": "目标 7.5%", "status": "ok"},
        {"label": "吨水成本", "value": "1.28", "unit": "元/m³", "delta": "+0.06", "status": "warn"},
    ],
    "groups": [
        {"title": "一、成本结构（元/m³）",
         "bars": [{"label": "能源", "value": 0.42, "max": 0.6, "status": "ok"},
                  {"label": "药剂", "value": 0.18, "max": 0.6, "status": "ok"},
                  {"label": "人工", "value": 0.31, "max": 0.6, "status": "warn"}],
         "table": {"head": ["科目", "金额(元/m³)", "占比", "状态"],
                   "rows": [["能源", "0.42", "33%", "ok"], ["药剂", "0.18", "14%", "ok"]]}},
    ],
    "alerts": [{"item": "吨水电耗 0.31 kWh/m³", "rule": "超阈值 0.30", "level": "crit"}],
    "footer": {"unit": "ima.copilot", "author": "小邦", "note": "数据来源：测算模型（内部）"},
}


def _kv(v, u):
    return esc(v) + ('<span class="foot"> %s</span>' % esc(u) if u else "")


def render_kpis(kpis):
    if not kpis:
        return ""
    out = ['<div class="kpi-grid">']
    for k in kpis:
        st = k.get("status", "ok")
        d = k.get("delta", "")
        cls = "up" if d.startswith("+") else ("down" if d.startswith("-") else "")
        foot = ('<div class="foot"><span class="%s">%s</span></div>' % (cls, esc(d))) if d else ""
        out.append('<div class="kpi st-%s"><div class="lb">%s</div><div class="v">%s<span class="foot">%s</span></div>%s</div>'
                   % (esc(st), esc(k.get("label", "")), esc(k.get("value", "")),
                      (" " + esc(k.get("unit", "")) if k.get("unit") else ""), foot))
    out.append("</div>")
    return "".join(out)


def render_bars(bars):
    if not bars:
        return ""
    out = []
    for b in bars:
        try:
            v, mx = float(b.get("value", 0)), float(b.get("max", 0) or 0)
            pct = max(0.0, min(100.0, v / mx * 100 if mx else v))
        except Exception:
            pct = 0
        out.append('<div class="barrow"><span>%s</span><div class="bartrack"><div class="barfill st-%s" style="width:%.1f%%"></div></div>'
                   '<span class="barval">%s</span></div>'
                   % (esc(b.get("label", "")), esc(b.get("status", "ok")), pct, esc(b.get("value", ""))))
    return '<div class="barblock">%s</div>' % "".join(out)


def render_table(t):
    if not t or not t.get("head"):
        return ""
    th = "".join("<th>%s</th>" % esc(c) for c in t["head"])
    rows = ""
    for r in t.get("rows", []):
        tds = ""
        for i, c in enumerate(r):
            st = c if (i == len(r) - 1 and str(c) in ("ok", "warn", "crit")) else None
            tds += "<td>%s</td>" % ('<span class="badge b-%s">%s</span>' % (st, st) if st else esc(c))
        rows += "<tr>%s</tr>" % tds
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, rows)



def render_timeline(items):
    if not items:
        return ""
    out = ['<div class="timeline">']
    for it in items:
        out.append('<div class="tl-item"><div class="tl-time">%s</div>'
                   '<div class="tl-title">%s</div><div class="tl-desc">%s</div></div>'
                   % (esc(it.get("time", "")), esc(it.get("title", "")), esc(it.get("desc", ""))))
    out.append("</div>")
    return "".join(out)


def render_bento(cells):
    if not cells:
        return ""
    out = ['<div class="bento">']
    for c in cells:
        span = int(c.get("span", 1) or 1)
        cls = "b-cell" + (" b-2" if span == 2 else " b-3" if span == 3 else "")
        cell = '<div class="%s"><b class="b-t">%s</b>' % (cls, esc(c.get("title", "")))
        if c.get("value"):
            cell += '<div class="b-v">%s</div>' % esc(c["value"])
        if c.get("desc"):
            cell += '<div class="b-d">%s</div>' % esc(c["desc"])
        out.append(cell + "</div>")
    out.append("</div>")
    return "".join(out)


def build(spec):
    theme = spec.get("theme", "ocean")
    if theme not in BY_ID:
        theme = "ocean"
    themes_css = "\n".join([css_block(PALETTES[0], ':root, [data-theme="%s"]' % PALETTES[0]["id"])]
                           + [css_block(p) for p in PALETTES[1:]])
    theme_list = [{"id": p["id"], "zh": p["zh"], "accent": p["accent"], "accent2": p["accent2"]} for p in PALETTES]

    secs = ['<section id="kpis"><h2>关键指标</h2>%s</section>' % render_kpis(spec.get("kpis"))]
    for i, g in enumerate(spec.get("groups", []) or [], 1):
        secs.append('<section id="g%d"><h2>%s</h2>%s%s%s%s</section>'
                    % (i, esc(g.get("title", "")), render_bars(g.get("bars")), render_table(g.get("table")),
                       render_timeline(g.get("timeline")), render_bento(g.get("bento"))))
    if spec.get("alerts"):
        rows = "".join('<tr class="lv-%s"><td>%s</td><td>%s</td><td>%s</td></tr>'
                       % (esc(a.get("level", "warn")), esc(a.get("item", "")), esc(a.get("rule", "")),
                          {"crit": "超标", "warn": "关注", "ok": "正常"}.get(a.get("level", "warn"), "关注"))
                       for a in spec["alerts"])
        secs.append('<section id="alerts"><h2>阈值预警</h2><table class="alert"><thead><tr>'
                    '<th style="width:44%%">指标</th><th style="width:38%%">规则</th><th>级别</th>'
                    '</tr></thead><tbody>%s</tbody></table></section>' % rows)

    toc = ('<section id="toc"><h2>目录</h2><div class="toc">%s</div></section>'
           % "".join('<a href="#%s">%s</a>' % (sid, ti)
                     for sid, ti in [("kpis", "关键指标")] + [("g%d" % i, esc(g.get("title", "")))
                                                              for i, g in enumerate(spec.get("groups", []) or [], 1)]
                     + ([("alerts", "阈值预警")] if spec.get("alerts") else []))) if len(secs) >= 3 else ""

    f = spec.get("footer", {}) or {}
    foot = "　·　".join(x for x in [
        ("数据来源：%s" % esc(f["note"])) if f.get("note") else "",
        ("落款单位：%s" % esc(f["unit"])) if f.get("unit") else "",
        ("制作者：%s" % esc(f["author"])) if f.get("author") else ""] if x)

    html = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="__THEME__"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title><style>
/*@THEMES@*/ /*@BASE@*/ /*@BOARD@*/
</style></head><body>
<div id="progress"></div>
<nav class="top-fixed" id="topFixed">
<div class="tf-row1"><div class="brand">__TITLE__</div><div class="fixed-toc" id="chapterNav"></div></div>
<div class="tf-row2"><span class="tf-label">主题色</span><div class="palette" id="palette"><button class="palette-pill" id="palettePill" aria-expanded="false" aria-label="切换配色"><span class="pp-dot"></span><span class="theme-name" id="themeName"></span><span class="pp-caret">▾</span></button>
<div class="palette-pop" id="palettePop"><span id="swatches" style="display:contents"></span></div></div></div></nav>
<div class="hero"><div class="inner"><h1>__TITLE__</h1><p class="lead">__SUB__</p>
<p class="meta">交付对象：__AUD__　·　成文日期：__DATE__</p></div></div>
<div class="wrap">__TOC____BODY__<footer>__FOOT__</footer></div>
<button id="toTop" aria-label="返回顶部">↑</button><script>
/*@JS@*/
</script></body></html>"""
    rep = {"__THEME__": theme, "__TITLE__": esc(spec.get("title", "数据看板")),
           "__SUB__": esc(spec.get("subtitle", "")), "__AUD__": esc(spec.get("audience", "")),
           "__DATE__": esc(spec.get("date", "")), "__TOC__": toc, "__BODY__": "\n".join(secs),
           "__FOOT__": foot, "/*@THEMES@*/": themes_css, "/*@BASE@*/": CSS_FIXED, "/*@BOARD@*/": BOARD_CSS}
    for k, v in rep.items():
        html = html.replace(k, v)
    js = JS_FIXED.replace("/*@THEME_LIST@*/[]", json.dumps(theme_list, ensure_ascii=False))
    js = js.replace("/*@DEFAULT_THEME@*/", theme)
    return html.replace("/*@JS@*/", js)


def main():
    ap = argparse.ArgumentParser(description="数据指标看板构建器")
    ap.add_argument("--init", action="store_true"); ap.add_argument("--data"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--theme"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.init:
        open(a.out, "w", encoding="utf-8").write(json.dumps(TMPL, ensure_ascii=False, indent=2))
        print("已生成看板数据模板：", a.out); print("配色：", ", ".join(BY_ID)); return 0
    if not a.data:
        print("缺少 --data（或用 --init 生成模板）", file=sys.stderr); return 2
    spec = json.load(open(a.data, encoding="utf-8"))
    if a.theme:
        spec["theme"] = a.theme
    html = build(spec)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成：%s（%.1fKB，配色 %s，KPI %d 个）" % (a.out, os.path.getsize(a.out) / 1024,
          spec.get("theme", "ocean"), len(spec.get("kpis", []) or [])))
    if a.check:
        return subprocess.run([sys.executable, os.path.join(HERE, "html_check.py"), a.out, "--node"]).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
