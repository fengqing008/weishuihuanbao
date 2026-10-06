#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui_consult.py — 设计决策咨询薄封装（Design Consultation Adapter）

接入「UI设计智能」技能（nextlevelbuilder/ui-ux-pro-max-skill 移植版）的 BM25 设计库：
把中文场景自动路由为英文查询，取回可落地的配色 / 风格 / 字体 / 图表 / 动效参数，
并内置 WCAG 对比度自检，供 HTML 基座 / 公众号推文 / 社交卡片 / 信息看板 / PPT 直接消费。

用法:
  python3 ui_consult.py "数据看板"                       # 综合咨询（配色+风格+字体+图表）
  python3 ui_consult.py "数据看板" --domain color        # 只取配色
  python3 ui_consult.py "汇报PPT" --all                  # 取全部相关域
  python3 ui_consult.py "data dashboard" --json          # 英文直查 + JSON 输出
  python3 ui_consult.py --scene 数据看板                  # 指定场景路由
  python3 ui_consult.py --list                           # 列出内置场景路由表

依赖: 本机已安装「UI设计智能」技能（含 scripts/search.py 与 data/*.csv）。
"""
import argparse
import json
import os
import subprocess
import sys

# ---------------------------------------------------------------- 路径定位
_ENV_DIR = os.environ.get("UI_UX_PRO_MAX_DIR", "").strip()


def locate_ui_dir():
    """三级定位「UI设计智能」技能根目录。"""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        _ENV_DIR,
        "UI设计智能",
        "skills/UI设计智能",
        os.path.join(os.path.dirname(here), "UI设计智能"),
    ]
    for d in candidates:
        if d and os.path.isfile(os.path.join(d, "scripts", "search.py")):
            return d
    return None


# ---------------------------------------------------------------- 场景路由
# 中文/中英混合关键词 -> 英文查询（贴合数据库真实取值）
SCENE_MAP = [
    (["看板", "仪表盘", "监控", "大屏", "数据可视", "dashboard", "analytics"],
     {"color": "Analytics Dashboard", "style": "Data-Dense Dashboard",
      "chart": "Trend Over Time", "typography": "Sans + Mono"}),
    (["财务", "会计", "成本", "预算", "结算", "financial"],
     {"color": "Financial Dashboard", "style": "Financial Dashboard",
      "chart": "Performance vs Target", "typography": "Sans + Sans"}),
    (["政务", "政府", "公共", "机关", "事业", "government"],
     {"color": "Government/Public Service", "style": "Accessible & Ethical",
      "chart": "Compare Categories", "typography": "Sans (System Default)"}),
    (["汇报", "管理层", "高管", "董事", "年度", "executive", "年会"],
     {"color": "B2B Service", "style": "Executive Dashboard",
      "chart": "Compare Categories", "typography": "Serif + Sans"}),
    (["公众号", "推文", "微信", "文章", "编辑", "杂志", "长文", "wechat"],
     {"color": "Creative Agency", "style": "Hero-Centric Design",
      "chart": "Part-to-Whole", "typography": "Display + Serif"}),
    (["社交", "小红书", "卡片", "海报", "封面", "social"],
     {"color": "Social Media App", "style": "Vibrant & Block-based",
      "chart": "Part-to-Whole", "typography": "Display + Sans"}),
    (["落地页", "官网", "首页", "landing"],
     {"color": "SaaS (General)", "style": "Conversion-Optimized",
      "chart": "Funnel / Flow", "typography": "Sans + Sans"}),
    (["电商", "商城", "购物", "e-commerce"],
     {"color": "E-commerce", "style": "Conversion-Optimized",
      "chart": "Funnel / Flow", "typography": "Sans + Sans"}),
    (["教育", "培训", "课件", "课程"],
     {"color": "Educational App", "style": "Minimal & Direct",
      "chart": "Part-to-Whole", "typography": "Sans + Sans"}),
    (["文档", "知识库", "说明书", "手册", "manual"],
     {"color": "Knowledge Base/Documentation", "style": "Minimalism & Swiss Style",
      "chart": "Hierarchical / Nested Data", "typography": "Serif + Sans"}),
    (["暗色", "深色", "夜间", "dark"],
     {"color": "Fintech/Crypto", "style": "Dark Mode (OLED)",
      "chart": "Real-Time Streaming", "typography": "Mono + Sans"}),
    (["极简", "简约", "克制", "minimal", "swiss"],
     {"color": "Design System/Component Library", "style": "Minimalism & Swiss Style",
      "chart": "Compare Categories", "typography": "Sans + Sans"}),
]

DEFAULT_ROUTE = {"color": "SaaS (General)", "style": "Minimalism & Swiss Style",
                 "chart": "Trend Over Time", "typography": "Sans + Sans"}

ALL_DOMAINS = ["color", "style", "typography", "chart"]
DOMAIN_TITLES = {
    "color": "配色方案（槽位 hex，可直接作设计变量）",
    "style": "界面风格（含复杂度/可访问性/实现清单）",
    "typography": "字体搭配",
    "chart": "图表类型建议",
    "gsap": "动效预设（GSAP）",
    "ux": "UX 准则",
    "landing": "落地页结构",
}

# ---------------------------------------------------------------- 对比度
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hexs):
    h = hexs.lstrip("#")
    if len(h) != 6:
        return None
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg, bg):
    la, lb = _luminance(fg), _luminance(bg)
    if la is None or lb is None:
        return None
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


CONTRAST_PAIRS = [
    ("Foreground", "Background"), ("Card Foreground", "Card"),
    ("Muted Foreground", "Muted"), ("On Primary", "Primary"),
    ("On Secondary", "Secondary"), ("On Accent", "Accent"),
    ("On Destructive", "Destructive"),
]


def audit_contrast(row):
    out = []
    for fg_k, bg_k in CONTRAST_PAIRS:
        ratio = contrast_ratio(row.get(fg_k, ""), row.get(bg_k, ""))
        if ratio is None:
            continue
        out.append({"pair": f"{fg_k} on {bg_k}", "ratio": round(ratio, 2),
                    "pass": ratio >= 4.5})
    return out


# ---------------------------------------------------------------- 检索
def route_scene(text):
    joined = (text or "").lower()
    for kws, route in SCENE_MAP:
        for kw in kws:
            if kw.lower() in joined:
                return route, kw
    return dict(DEFAULT_ROUTE), None


def call_search(ui_dir, query, domain, n=3):
    search_py = os.path.join(ui_dir, "scripts", "search.py")
    cmd = [sys.executable, search_py, query, "--domain", domain,
           "--max-results", str(n), "--json"]
    try:
        p = subprocess.run(cmd, cwd=os.path.join(ui_dir, "scripts"),
                           capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa
        return {"error": str(e)}
    if p.returncode != 0:
        return {"error": (p.stderr or p.stdout or "search failed").strip()[:300]}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"error": "返回非 JSON，可能 search.py 版本不匹配"}


# ---------------------------------------------------------------- 渲染
def render_text(scene, matched, results):
    lines = [f"## 设计决策咨询 · {scene}",
             f"**场景路由:** {'命中关键词「' + matched + '」' if matched else '未命中内置路由，使用通用默认'}",
             ""]
    for domain, res in results.items():
        lines.append(f"### {DOMAIN_TITLES.get(domain, domain)}")
        if res.get("error"):
            lines.append(f"- ⚠️ 检索失败：{res['error']}\n")
            continue
        rows = res.get("results", [])
        if not rows:
            lines.append("- 未命中数据库，建议换同义词重试\n")
            continue
        row = rows[0]
        if domain == "color":
            slots = ["Primary", "Secondary", "Accent", "Background", "Foreground",
                     "Card", "Card Foreground", "Muted", "Muted Foreground",
                     "Border", "Destructive", "On Primary", "On Accent"]
            lines.append("| 槽位 | 值 |")
            lines.append("| --- | --- |")
            for s in slots:
                if row.get(s):
                    lines.append(f"| {s} | `{row[s]}` |")
            lines.append("")
            lines.append("**对比度自检（WCAG，阈值 4.5）:**")
            for item in audit_contrast(row):
                mark = "✓" if item["pass"] else "⚠ 不足"
                lines.append(f"- {item['pair']}: {item['ratio']} {mark}")
            if row.get("Notes"):
                lines.append(f"- 备注: {row['Notes']}")
            lines.append("")
        elif domain == "sty" or domain == "style":
            keep = ["Style Category", "Type", "Complexity", "Accessibility",
                    "Best For", "Primary Colors", "Effects & Animation"]
            for k in keep:
                if row.get(k):
                    lines.append(f"- **{k}:** {str(row[k])[:220]}")
            lines.append("")
        elif domain == "typography":
            for k in ["Font Pairing Name", "Heading Font", "Body Font",
                      "Mood/Style Keywords", "Best For"]:
                if row.get(k):
                    lines.append(f"- **{k}:** {str(row[k])[:200]}")
            lines.append("")
        elif domain == "chart":
            for k in ["Data Type", "Best Chart Type", "When to Use",
                      "Library Recommendation", "Accessibility Grade"]:
                if row.get(k):
                    lines.append(f"- **{k}:** {str(row[k])[:200]}")
            lines.append("")
        else:
            for k, v in list(row.items())[:8]:
                lines.append(f"- **{k}:** {str(v)[:200]}")
            lines.append("")
    lines.append("> 数据源：UI设计智能（ui-ux-pro-max-skill）。英文库，检索须用英文关键词；"
                 "引用配色前务必核对对比度。")
    return "\n".join(lines)


def render_json(scene, matched, results):
    payload = {"scene": scene, "matched_keyword": matched, "domains": {}}
    for domain, res in results.items():
        if res.get("error"):
            payload["domains"][domain] = {"error": res["error"]}
            continue
        rows = res.get("results", [])
        entry = {"count": res.get("count", 0), "top": rows[0] if rows else None}
        if domain == "color" and rows:
            entry["contrast"] = audit_contrast(rows[0])
        payload["domains"][domain] = entry
    return json.dumps(payload, ensure_ascii=False, indent=2)


def cmd_list():
    print("内置场景路由表（关键词 -> 配色/风格/字体/图表）:\n")
    for kws, route in SCENE_MAP:
        print(f"• {', '.join(kws)}")
        print(f"    配色={route['color']} | 风格={route['style']} | 字体={route['typography']}")
    print("\n默认路由:", DEFAULT_ROUTE)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description="设计决策咨询薄封装（接入 UI设计智能）")
    ap.add_argument("query", nargs="?", default="", help="场景描述（中文或英文）")
    ap.add_argument("--scene", help="显式指定场景词（同 query）")
    ap.add_argument("--domain", "-d", choices=ALL_DOMAINS + ["gsap", "ux", "landing"],
                    help="只咨询某个域")
    ap.add_argument("--all", action="store_true", help="咨询全部相关域")
    ap.add_argument("-n", "--max-results", type=int, default=3)
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--list", action="store_true", help="列出场景路由表")
    args = ap.parse_args()

    if args.list:
        cmd_list()
        return 0

    text = args.scene or args.query
    if not text:
        ap.error("请提供场景描述，例如: ui_consult.py \"数据看板\"")

    ui_dir = locate_ui_dir()
    if not ui_dir:
        print("⚠ 未找到「UI设计智能」技能目录。请确认该技能已安装，"
              "或设置环境变量 UI_UX_PRO_MAX_DIR 指向其根目录。", file=sys.stderr)
        return 2

    route, matched = route_scene(text)

    # 组装 (domain, query)
    if args.domain:
        # 指定域：若该域在路由中有对应英文则用之，否则回落到原文本
        targets = [(args.domain, route.get(args.domain, text))]
    else:
        domains = ALL_DOMAINS if args.all else ["color", "style", "typography"]
        # 数据/看板类场景自动补 chart
        if not args.all and any(k in text for k in ["看板", "图表", "数据", "dashboard", "chart"]):
            domains = domains + ["chart"]
        targets = [(d, route.get(d, text)) for d in domains]

    results = {}
    for domain, query in targets:
        results[domain] = call_search(ui_dir, query, domain, args.max_results)

    if args.json:
        print(render_json(text, matched, results))
    else:
        print(render_text(text, matched, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
