#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motifs.py —— 版式母题（Design Motif）与设计纪律层 CSS

与 palettes.py 的十套配色正交：配色决定「用什么颜色」，母题决定
「如何排版与用色」——字体配对、字阶、圆角策略、强调是否用渐变、
动效节奏、Hero 形态。

设计依据：frontend-design（Anthropic 官方 Skill）列出的 AI 生成页面
五类「模板痕迹」——① 统一圆角＋统一灰阴影＋渐变装饰的卡片套装；
② 每节 fade-and-slide-up 入场＋每卡片 hover；③ Hero 恒为「大数字＋
小标签＋渐变」；④ 全大写标签／eyebrow；⑤ 与内容无关的 01/02/03 编号。
以及《The Elements of Typographic Style》的模块化字阶建议。

用法：
  python3 motifs.py list                     十二套母题一览
  python3 motifs.py css --motif editorial    输出设计纪律层 CSS
  python3 motifs.py json                     导出 JSON（供 build_report.py 调用）
"""
import argparse
import json

# 模块化字阶（1.25 比率，ratio 可被母题覆盖）
BASE_FS = 16.5
SCALE = [0.80, 0.90, 1.00, 1.20, 1.45, 1.80, 2.30, 3.00]  # xs..3xl

MOTIFS = {
    "editorial": dict(
        zh="编辑长文", en="Editorial",
        desc="报刊式长文。直角、单色强调、衬线标题配无衬线正文，整页一次编排，无装饰性渐变与粒子。",
        use="年度报告、深度长文、调研报告、专题特稿",
        radius={"xs": 0, "sm": 0, "md": 0, "lg": 0, "pill": 0},
        grad=False, motion="orchestrated", hero="editorial",
        display='"Georgia","Noto Serif SC","Songti SC","SimSun",serif',
        body='"Noto Sans SC","PingFang SC",-apple-system,"Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#d8d2c6",
    ),
    "blueprint": dict(
        zh="工程图纸", en="Blueprint",
        desc="工程制图风。全直角、等宽标注、网格感、无动效（图纸不该流动），线条皆为标注。",
        use="工艺说明、技术方案、工程报告、图纸说明",
        radius={"xs": 0, "sm": 0, "md": 0, "lg": 0, "pill": 0},
        grad=False, motion="off", hero="blueprint",
        display='"Noto Sans SC","PingFang SC",-apple-system,sans-serif',
        body='"Noto Sans SC","PingFang SC",-apple-system,"Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#4e6b84",
    ),
    "narrative": dict(
        zh="数据叙事", en="Narrative",
        desc="以数据为主角。大留白、极微圆角、单色强调，图表用真实比例，全页一次滚动编排。",
        use="经营分析、运营数据故事、指标复盘、财务解读",
        radius={"xs": 2, "sm": 4, "md": 4, "lg": 6, "pill": 999},
        grad=False, motion="orchestrated", hero="narrative",
        display='"Inter","Noto Sans SC","PingFang SC",-apple-system,sans-serif',
        body='"Noto Sans SC","PingFang SC",-apple-system,"Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#e6e6e2",
    ),
    "classic": dict(
        zh="经典报告", en="Classic",
        desc="既有多主题卡片风格（保留渐变强调与错峰入场），适合需要更强视觉层次的汇报。",
        use="汇报材料、宣发长图、品牌文档",
        radius={"xs": 4, "sm": 6, "md": 10, "lg": 14, "pill": 999},
        grad=True, motion="staggered", hero="badge",
        display='"PingFang SC","Microsoft YaHei","Source Han Sans SC",sans-serif',
        body='"PingFang SC","Microsoft YaHei","Hiragino Sans GB","Source Han Sans SC",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#dde1e5",
    ),
    "briefing": dict(
        zh="执行简报", en="Briefing",
        desc="一页决策风。紧凑单栏、结论置顶、无装饰，信息密度高而无压迫感。",
        use="决策备忘、一页结论、请示要点",
        radius={"xs": 2, "sm": 4, "md": 6, "lg": 8, "pill": 999},
        grad=False, motion="off", hero="badge",
        display='"PingFang SC","Microsoft YaHei","Source Han Sans SC",sans-serif',
        body='"PingFang SC","Microsoft YaHei","Hiragino Sans GB",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#d7d7d2",
    ),
    "runbook": dict(
        zh="工程手册", en="Runbook",
        desc="操作细则风。全直角、等宽主导、步骤编号与告警表并置，强调可执行性。",
        use="运行手册、操作规程、应急处置",
        radius={"xs": 0, "sm": 0, "md": 0, "lg": 0, "pill": 0},
        grad=False, motion="off", hero="blueprint",
        display='"Noto Sans SC","PingFang SC",-apple-system,sans-serif',
        body='"Noto Sans SC","PingFang SC",-apple-system,"Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#4e6b84",
    ),
    "weekly": dict(
        zh="周期周报", en="Weekly",
        desc="进度通报风。横向状态条、徽章分档、每项一句话，便于快速扫读。",
        use="周报、进度通报、例会材料",
        radius={"xs": 3, "sm": 6, "md": 8, "lg": 12, "pill": 999},
        grad=False, motion="orchestrated", hero="badge",
        display='"Inter","Noto Sans SC","PingFang SC",-apple-system,sans-serif',
        body='"Noto Sans SC","PingFang SC",-apple-system,"Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#e3e4e0",
    ),
    "datareport": dict(
        zh="数据报告", en="Data Report",
        desc="指标盘点风。KPI 网格先行、图表居中、口径注释紧随，数字为主角。",
        use="数据盘点、指标报告、测算说明",
        radius={"xs": 2, "sm": 6, "md": 10, "lg": 14, "pill": 999},
        grad=False, motion="orchestrated", hero="narrative",
        display='"Inter","Noto Sans SC","PingFang SC",-apple-system,sans-serif',
        body='"Noto Sans SC","PingFang SC",-apple-system,"Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#e8e8e4",
    ),
    "teardown": dict(
        zh="竞品拆解", en="Teardown",
        desc="对标评比风。矩阵表为核心、维度对齐、结论与差距并列，克制而锐利。",
        use="竞品分析、对标评估、选型比较",
        radius={"xs": 2, "sm": 4, "md": 6, "lg": 8, "pill": 999},
        grad=False, motion="off", hero="blueprint",
        display='"Inter","PingFang SC","Noto Sans SC",-apple-system,sans-serif',
        body='"Noto Sans SC","PingFang SC",-apple-system,"Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#dfe3e8",
    ),
    "deck": dict(
        zh="幻灯片", en="Deck",
        desc="一屏一卡风。大字号、少对象、每屏一个论点，导航常驻可翻页。",
        use="演讲、路演、培训课件",
        radius={"xs": 6, "sm": 10, "md": 16, "lg": 20, "pill": 999},
        grad=True, motion="staggered", hero="badge",
        display='"Inter","PingFang SC","Microsoft YaHei",-apple-system,sans-serif',
        body='"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#2f3640",
    ),
    "magazine": dict(
        zh="杂志长文", en="Magazine",
        desc="特稿排印风。衬线大标题、单栏长文、页眉页脚与篇末花饰，重阅读节奏。",
        use="特稿、深度长文、行业观察",
        radius={"xs": 0, "sm": 0, "md": 0, "lg": 0, "pill": 0},
        grad=False, motion="orchestrated", hero="editorial",
        display='"Georgia","Noto Serif SC","Songti SC","SimSun",serif',
        body='"Noto Serif SC","Songti SC","PingFang SC",serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#ded8cc",
    ),
    "card": dict(
        zh="社媒卡片", en="Card",
        desc="方形图文风。单图单观点、圆角胶囊、留白充足，适配竖屏滑动浏览。",
        use="小红书图文、社媒配图、知识卡片",
        radius={"xs": 8, "sm": 12, "md": 20, "lg": 24, "pill": 999},
        grad=True, motion="staggered", hero="badge",
        display='"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif',
        body='"PingFang SC","Noto Sans SC","Hiragino Sans GB",sans-serif',
        mono='"SFMono-Regular",ui-monospace,Menlo,Consolas,monospace',
        rule="#ece7df",
    ),
}

DEFAULT = "editorial"


def scale_css(ratio=1.0):
    out = []
    names = ["xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl"]
    for n, f in zip(names, SCALE):
        px = round(BASE_FS * f * ratio, 1)
        px = int(px) if float(px).is_integer() else px
        out.append("--fs-%s: %spx;" % (n, px))
    return " ".join(out)


def css(motif_id):
    m = MOTIFS.get(motif_id) or MOTIFS[DEFAULT]
    r = m["radius"]
    accent_grad = ("linear-gradient(135deg, var(--accent), var(--accent-2))"
                   if m["grad"] else "var(--accent)")
    bar_grad = ("linear-gradient(90deg, var(--accent), var(--accent-2))"
                if m["grad"] else "var(--accent)")
    # 直角母题下，pill 型元素也收为直角（去「什么都圆」的模板感）
    return """/* ===== 设计纪律层 v6.2.0 · motif=%s（frontend-design 方法论） ===== */
:root{
  --ds-r-xs:%spx; --ds-r-sm:%spx; --ds-r-md:%spx; --ds-r-lg:%spx; --ds-r-pill:%spx;
  --ds-accent-fill:%s; --ds-bar-fill:%s;
  --font-display:%s; --font-body:%s; --font-mono:%s;
  --ds-rule:%s;
  %s
}
body{ font-family: var(--font-body); }
h1,h2,h3,.title,.hero h1,.sec-title{ font-family: var(--font-display); }
code,pre,kbd,.mono,td.num,th.num{ font-family: var(--font-mono); }

/* 圆角分级收口：容器统一走 token，不再「一个圆角套所有」 */
.card,.kpi-card,.b-cell,.stat-cell,.hero-stat,.quote,.concl,.tl-item,
.phase,.matrix-wrap,.tablewrap,.fig,figure,.law-card,.src,.gap,.chip,
.chips i,.q-diff,details.faq,.bento,.hero-badge,.hero-pills i,.swatch,
.sec-no,.b-t,.pp-dot,.pp,.bar-track,.bar-fill,#toTop,.toc a,.sop-step{
  border-radius: var(--ds-r-md) !important;
}
.hero-badge,.hero-pills i,.chip,.chips i,.q-diff,.pp,#toTop,.bar-track,.bar-fill,.src{
  border-radius: var(--ds-r-pill) !important;
}
.blockquote,blockquote{ border-radius: 0 var(--ds-r-sm) var(--ds-r-sm) 0 !important; }

/* 强调填充：默认单色（去装饰性渐变），classic 母题仍保留渐变 */
.b-v,.kpi-value,.stat-v,.bignum b,.hero-stat b,.bar-fill,
.b-t::before,.stat-cell::before,.pp-dot,.sec-no,.phase-no,.tl-item::before,
.chapter-tab.active,.q-diff,.toTop,.hero-badge{ background: var(--ds-accent-fill); }
.bar-fill{ background: var(--ds-bar-fill); }
.b-v,.kpi-value,.stat-v,.sec-no,.phase-no{ background: var(--ds-accent-fill); }
.b-v,.kpi-value,.stat-v,.bignum b,.hero-stat b{ -webkit-background-clip: initial; background-clip: initial;
  color: var(--accent); }
.b-v,.kpi-value,.stat-v{ color: #fdfdfd; }
.sec-no,.phase-no{ color: var(--surface); }

/* 去掉与内容无关的装饰：编辑／图纸／叙事母题隐藏 Hero 几何装饰与波浪 */
%s

/* 动效策略：orchestrated＝整页一次编排（章节内容不做逐节淡入）；
   off＝无动效；staggered＝旧错峰行为 */
%s
/* ===================== end 设计纪律层 ===================== */
""" % (
        m["en"],
        r["xs"], r["sm"], r["md"], r["lg"], r["pill"],
        accent_grad, bar_grad,
        m["display"], m["body"], m["mono"], m["rule"], scale_css(),
        _hero_css(m), _motion_css(m),
    )


def _hero_css(m):
    if m["hero"] == "badge":
        return ""
    hide = ".hero-deco,.hero-wave{ display:none !important; }\n" \
           ".hero{ background: var(--surface) !important; color: var(--text) !important;"
    if m["hero"] == "editorial":
        return (hide + " border-bottom: 2px solid var(--ds-rule); padding: 46px 22px 30px; }\n"
                ".hero h1{ font-size: clamp(30px,5vw,58px); font-weight: 700; letter-spacing: .005em;"
                " line-height: 1.06; text-align: left; }\n"
                ".hero-badge{ background: transparent !important; color: var(--muted) !important;"
                " border: 0 !important; letter-spacing: .02em !important; padding: 0 !important;"
                " margin-bottom: 10px; }\n"
                ".hero-stat{ background: var(--surface-2) !important; backdrop-filter: none !important;"
                " color: var(--text) !important; border: 0 !important; border-top: 2px solid var(--accent) !important; }\n"
                ".hero-stat b{ color: var(--text) !important; }\n"
                ".hero-pills i{ background: transparent !important; border-color: var(--ds-rule) !important;"
                " color: var(--muted) !important; letter-spacing: .02em !important; }\n"
                ".hero .inner,.hero-grid{ text-align: left; }\n")
    if m["hero"] == "blueprint":
        return (hide + " border: 1px solid var(--ds-rule); padding: 22px 24px; }\n"
                ".hero h1{ font-family: var(--font-body); font-size: clamp(22px,3.4vw,32px);"
                " font-weight: 700; letter-spacing: .02em; }\n"
                ".hero-badge{ background: transparent !important; border: 1px dashed var(--accent) !important;"
                " color: var(--accent) !important; letter-spacing: .06em !important; }\n"
                ".hero-stat{ background: transparent !important; border: 1px solid var(--ds-rule) !important;"
                " border-radius: 0 !important; color: var(--text) !important; }\n")
    if m["hero"] == "narrative":
        return (hide + " background: var(--bg) !important; color: var(--text) !important;"
                " padding: 64px 22px 30px; }\n"
                ".hero h1{ font-size: clamp(24px,3.6vw,40px); text-align: left; font-weight: 600; }\n"
                ".hero-badge{ background: transparent !important; border: 0 !important;"
                " color: var(--muted) !important; padding: 0 !important; }\n"
                ".hero-stat{ background: transparent !important; border: 0 !important;"
                " border-top: 2px solid var(--text) !important; backdrop-filter: none !important; }\n")
    return ""


def _motion_css(m):
    if m["motion"] == "staggered":
        return ""
    if m["motion"] == "off":
        return (".anim-ready .fx,.anim-ready .bar-fill,.anim-ready .chart svg{"
                " opacity:1 !important; transform:none !important; transition:none !important; }\n"
                ".hero-deco{ animation:none !important; }\n")
    # orchestrated：内容不做逐节淡入；仅保留 Hero 一次入场与图表/条形生长
    return (".anim-ready .fx{ opacity:1 !important; transform:none !important; transition:none !important; }\n"
            "@media (prefers-reduced-motion:no-preference){\n"
            "  .anim-ready .hero .fx{ animation: dsHeroIn .78s cubic-bezier(.2,.72,.28,1) both; }\n"
            "  @keyframes dsHeroIn{ from{ opacity:0; transform:translateY(12px);} to{ opacity:1; transform:none;} }\n"
            "}\n")


def by_id(motif_id):
    return MOTIFS.get(motif_id) or MOTIFS[DEFAULT]


def main():
    ap = argparse.ArgumentParser(description="HTML 基座版式母题与设计纪律层")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    c = sub.add_parser("css")
    c.add_argument("--motif", default=DEFAULT)
    sub.add_parser("json")
    a = ap.parse_args()
    if a.cmd == "list":
        for k, v in MOTIFS.items():
            print("%-11s %-4s 圆角%-6s 渐变%-5s 动效%-13s hero=%-10s %s"
                  % (k, v["zh"], v["radius"]["md"], v["grad"], v["motion"], v["hero"], v["desc"]))
    elif a.cmd == "css":
        print(css(a.motif))
    elif a.cmd == "json":
        print(json.dumps(MOTIFS, ensure_ascii=False, indent=2))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
