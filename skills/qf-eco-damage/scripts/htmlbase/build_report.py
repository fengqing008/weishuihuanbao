#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_report.py —— 从数据文件构建单文件自包含 HTML 成果页

用法：
  python3 build_report.py --init --out spec.json                     生成数据模板
  python3 build_report.py --data spec.json --out 成果页.html          构建页面
  python3 build_report.py --data spec.json --out 成果页.html --theme ocean --check
        --theme 指定默认配色（也可在 spec.json 的 theme 字段给出）
        --check 构建后自动跑 html_check.py 自检

页面自带：十套配色切换、目录、返回顶部、来源区块、缺口徽标、观点块、打印样式。
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palettes import PALETTES, BY_ID, css_block, VARS, CSSNAME  # noqa
import re

HERE = os.path.dirname(os.path.abspath(__file__))

SPEC_TMPL = {
    "_说明": "填好本文件后执行：python3 build_report.py --data spec.json --out 成果页.html --check",
    "title": "报告标题",
    "subtitle": "副标题：一句话说明这份材料解决什么问题",
    "audience": "交付对象",
    "date": "2026-09-21",
    "theme": "ocean",
    "conclusion": "一句话结论（不超过 40 字）",
    "items": ["核心发现一（附来源角标）", "核心发现二"],
    "sections": [
        {"title": "一、章节标题", "html": "<p>段落内容。数据后置来源角标，例如 <b>12.5%</b><span class=\"src\">P0</span>。未证实信息用 <span class=\"gap\">【待核：说明】</span>。观点进观点块：</p><div class=\"quote\">观点叙述，与事实分开呈现。</div>"}
    ],
    "sources": [{"label": "来源名称", "level": "P0", "note": "发布日期或备注"}],
    "gaps": [{"item": "缺口描述", "impact": "不填补的影响", "channel": "建议补充渠道"}],
    "footer": {"unit": "ima.copilot", "author": "小邦", "note": "数据来源：XXX（P0）"}
}

CSS_FIXED = """
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--bg); color: var(--text);
  font-family: "PingFang SC","Microsoft YaHei","Hiragino Sans GB","Source Han Sans SC",sans-serif;
  line-height: 1.78; font-size: 15px; transition: background .28s ease, color .28s ease; }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent-soft); }
h1,h2,h3,h4 { line-height: 1.35; }
#progress { position: fixed; top: 0; left: 0; height: 3px; width: 0;
  background: linear-gradient(90deg,var(--accent),var(--accent-2)); z-index: 99; }
.top-fixed { position: sticky; top: 0; z-index: 80; background: color-mix(in srgb, var(--surface) 90%, transparent);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border); box-shadow: 0 2px 12px rgba(0,0,0,.05); }
.tf-row1 { display: flex; align-items: center; gap: 12px;
  max-width: 1100px; margin: 0 auto; padding: 8px 22px 0; }
/* 置顶目录条（第一行独占，物理上不与配色同容器） */
.fixed-toc { flex: 1 1 auto; min-width: 0; display: flex; gap: 6px; overflow-x: auto;
  align-items: center; scrollbar-width: none; -ms-overflow-style: none; padding: 3px 0;
  scroll-behavior: smooth; -webkit-overflow-scrolling: touch; touch-action: pan-x;
  overscroll-behavior-x: contain; cursor: grab; user-select: none; -webkit-user-select: none; }
.fixed-toc::-webkit-scrollbar { display: none; }
.fixed-toc.dragging { cursor: grabbing; scroll-behavior: auto; }
.fixed-toc.dragging .chapter-tab { pointer-events: none; }
/* 第二行：主题色胶囊靠右 */
.tf-row2 { display: flex; align-items: center; justify-content: flex-end; gap: 10px;
  max-width: 1100px; margin: 0 auto; padding: 5px 22px 8px; }
.tf-label { font-size: 11.5px; color: var(--muted); letter-spacing: .1em; }

/* ===== v3.0.2 排版美化 ===== */
.fixed-toc .chapter-tab.active { background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border-color: transparent; }
.b-v, .kpi-value { background: linear-gradient(135deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.tl-desc, .phase-d, .b-d, .step-sub, h2 + .sub { color: color-mix(in srgb, var(--text) 76%, var(--muted)); }
table thead th { background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 9%, var(--surface-2)), var(--surface-2)); }
.chapter-hero h2 { letter-spacing: .015em; }
.phase-headrow { display: flex; align-items: center; gap: 10px; }
.phase-headrow .phase-meta { margin-left: auto; }
details.faq summary:hover { background: color-mix(in srgb, var(--accent) 5%, var(--surface)); }
@media (max-width: 640px) { .tf-row2 .tf-label { display: none; } }
@media print {
  .tf-row2 { display: none !important; }
  .b-v, .kpi-value { -webkit-text-fill-color: currentColor; background: none; }
}
/* v3.0.1 配色单胶囊 + 色板浮层 */
.palette { position: relative; flex: 0 0 auto; }
.palette-pill { display: inline-flex; align-items: center; gap: 7px; cursor: pointer;
  border: 1px solid var(--border); background: var(--surface); border-radius: 999px;
  padding: 3px 11px 3px 5px; font-size: 12px; color: var(--text); line-height: 1.4; }
.palette-pill:hover { border-color: var(--accent); }
.pp-dot { width: 18px; height: 18px; border-radius: 50%; flex: 0 0 auto; border: 1px solid var(--border);
  background: linear-gradient(135deg, var(--accent) 50%, var(--accent-2) 50%); }
.pp-caret { font-size: 10px; color: var(--muted); transition: transform .25s; }
.palette.open .pp-caret { transform: rotate(180deg); }
.palette-pop { position: absolute; right: 0; top: calc(100% + 8px); display: none; z-index: 90;
  width: 208px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 12px 14px; box-shadow: 0 12px 34px rgba(0,0,0,.16);
  grid-template-columns: repeat(5, 1fr); gap: 10px; }
.palette.open .palette-pop { display: grid; }
.palette-pop .swatch { width: 26px; height: 26px; margin: 0 auto; }
.switcher { display: flex; align-items: center; gap: 7px; margin-left: auto; flex-wrap: wrap; }
.switcher .label, .theme-name { font-size: 12px; color: var(--muted); }
.swatch { width: 22px; height: 22px; border-radius: 50%; cursor: pointer; padding: 0;
  border: 2px solid var(--border); transition: transform .16s ease; }
.swatch:hover { transform: scale(1.18); }
.swatch[aria-pressed="true"] { border-color: var(--text); }
.hero { background: linear-gradient(135deg,var(--hero-1),var(--hero-2)); color: var(--hero-text);
  padding: 52px 22px 46px; }
.hero .inner, .wrap { max-width: 1100px; margin: 0 auto; }
.hero h1 { font-size: clamp(28px, 4.6vw, 44px); margin: 0 0 10px; }
.hero .lead { opacity: .92; max-width: 780px; margin: 0 0 18px; }
.hero .meta { font-size: 13px; opacity: .86; }
.wrap { padding: 0 22px 72px; }
section { margin-top: 46px; }
h2 { font-size: clamp(19px, 3vw, 24px); margin: 0 0 6px; }
h2 + .sub { color: var(--muted); font-size: 13.5px; margin: 0 0 18px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 12px 0; }
th, td { border: 1px solid var(--border); padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: var(--surface-2); font-size: 12.5px; }
tbody tr:nth-child(even) td { background: var(--surface-2); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }
.grid2 { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit,minmax(280px,1fr)); }
.toc { display: flex; flex-wrap: wrap; gap: 8px; }
.toc a { border: 1px solid var(--border); border-radius: 16px; padding: 4px 12px; font-size: 13px; }
.src { display: inline-block; margin-left: 5px; padding: 0 6px; border-radius: 4px;
  font-size: 11px; font-weight: 700; color: var(--accent); background: var(--accent-soft);
  vertical-align: 1px; }
.gap { background: #fff3b0; color: #6a4b00; border-radius: 4px; padding: 0 5px; font-weight: 700; }
.quote { border-left: 3px solid var(--accent); background: var(--surface); border-radius: 0 8px 8px 0;
  padding: 12px 18px; margin: 12px 0; }
.quote::before { content: "观点"; display: block; font-size: 11px; letter-spacing: .08em;
  color: var(--accent); font-weight: 700; margin-bottom: 2px; }
.concl { background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--accent);
  border-radius: 10px; padding: 18px 20px; }
.concl b { color: var(--accent); }
ul.plain { margin: 8px 0 0; padding-left: 20px; }
#toTop { position: fixed; right: 20px; bottom: 24px; width: 40px; height: 40px; border-radius: 50%;
  border: 1px solid var(--border); background: var(--surface); color: var(--accent); cursor: pointer;
  font-size: 16px; display: none; z-index: 60; }
footer { margin-top: 56px; padding-top: 16px; border-top: 1px solid var(--border);
  font-size: 12.5px; color: var(--muted); }

/* ===== v2.0 新增组件 ===== */
/* 强化 callout（GitHub 风格） */
.callout { border-left: 4px solid var(--accent); background: var(--surface);
  border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 14px 0;
  border: 1px solid var(--border); border-left-width: 4px; }
.callout-head { font-size: 12px; font-weight: 700; letter-spacing: .08em;
  color: var(--accent); margin-bottom: 6px; text-transform: uppercase; }
.callout-body { font-size: 14px; line-height: 1.7; color: var(--text); }
.callout-info { border-left-color: var(--accent); }
.callout-info .callout-head { color: var(--accent); }
.callout-warn { border-left-color: #b8770c; background: #fffaef; }
.callout-warn .callout-head { color: #b8770c; }
[data-theme="midnight"] .callout-warn,
[data-theme="sunset"] .callout-warn { background: var(--surface-2); }
.callout-crit { border-left-color: #c0392b; background: #fef5f3; }
.callout-crit .callout-head { color: #c0392b; }
[data-theme="midnight"] .callout-crit,
[data-theme="sunset"] .callout-crit { background: var(--surface-2); }
.callout-ok { border-left-color: #2e7d32; background: #f3faf3; }
.callout-ok .callout-head { color: #2e7d32; }
[data-theme="midnight"] .callout-ok { background: var(--surface-2); }

/* KPI 数据卡 */
.kpi-grid { display: grid; gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin: 18px 0; }
.kpi-card { background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 18px; transition: transform .16s ease; }
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.06); }
.kpi-label { font-size: 12.5px; color: var(--muted); margin-bottom: 6px;
  letter-spacing: .04em; }
.kpi-value { font-size: 28px; font-weight: 700; color: var(--accent);
  line-height: 1.1; margin: 4px 0; }
.kpi-up { color: #2e7d32; }
.kpi-down { color: #c0392b; }
.kpi-unit { font-size: 13px; font-weight: 500; color: var(--muted);
  margin-left: 4px; }
.kpi-note { font-size: 12px; color: var(--muted); margin-top: 4px; }

/* 试题卡（Q-card 三段式） */
.q-card { background: var(--surface); border: 1px solid var(--border);
  border-left: 4px solid var(--accent); border-radius: 10px;
  padding: 18px 20px; margin: 16px 0; }
.q-head { display: flex; gap: 12px; align-items: center;
  margin-bottom: 12px; flex-wrap: wrap; }
.q-id { font-weight: 700; color: var(--accent); font-size: 16px; }
.q-points { background: var(--surface-2); color: var(--text);
  padding: 2px 10px; border-radius: 12px; font-size: 12.5px; }
.q-diff { padding: 2px 10px; border-radius: 12px; font-size: 12.5px;
  font-weight: 600; }
.diff-easy { background: #e8f5e9; color: #2e7d32; }
.diff-mid { background: #fff8e1; color: #b8770c; }
.diff-hard { background: #fdecea; color: #c0392b; }
[data-theme="midnight"] .diff-easy,
[data-theme="midnight"] .diff-mid,
[data-theme="midnight"] .diff-hard { background: var(--surface-2); }
.q-stem { font-size: 15px; line-height: 1.75; margin-bottom: 10px;
  color: var(--text); }
.q-subs { font-size: 14px; }
.q-sub { padding-left: 22px; }
.q-sub li { margin: 6px 0; line-height: 1.7; }

/* 缺口卡（三列式） */
.gap-table { margin: 14px 0; overflow-x: auto; }
.gap-table table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.gap-table th { background: var(--surface-2); color: var(--text);
  font-size: 12.5px; padding: 9px 12px; border: 1px solid var(--border);
  text-align: left; }
.gap-table td { padding: 9px 12px; border: 1px solid var(--border);
  vertical-align: top; }
.gap-table tbody tr:nth-child(even) td { background: var(--surface-2); }

/* 数学公式（KaTeX 容器） */
.math-inline { background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 4px; padding: 0 6px; font-family: "KaTeX_Main","Cambria Math",serif;
  font-size: 0.95em; color: var(--accent); white-space: nowrap; }
.math-block { background: var(--surface-2); border: 1px solid var(--border);
  border-left: 3px solid var(--accent); border-radius: 0 8px 8px 0;
  padding: 14px 20px; margin: 14px 0; text-align: center;
  font-family: "KaTeX_Main","Cambria Math",serif; font-size: 1.05em;
  color: var(--text); overflow-x: auto; }

/* 表格强化 */
.tablewrap { overflow-x: auto; margin: 14px 0; border-radius: 8px; }
.tablewrap table { border-collapse: collapse; width: 100%; font-size: 14px; }
.tablewrap th { background: var(--accent); color: var(--surface);
  text-align: left; padding: 10px 12px; font-size: 13px;
  font-weight: 600; white-space: nowrap; border: 1px solid var(--border); }
.tablewrap td { padding: 9px 12px; border: 1px solid var(--border);
  vertical-align: top; }
.tablewrap tbody tr:nth-child(even) td { background: var(--surface-2); }
.tablewrap tbody tr:hover td { background: color-mix(in srgb, var(--accent) 8%, var(--surface)); }

/* 章节锚点偏移（避开两行置顶栏） */
section[id] { scroll-margin-top: calc(var(--topH, 88px) + 14px); }

/* ===== 移动端强化 ===== */
@media (max-width: 768px) {
  .hero h1 { font-size: 24px; }
  .hero { padding: 36px 18px 30px; }
  .wrap { padding: 0 16px 56px; }
  .kpi-grid { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
  .kpi-value { font-size: 22px; }
  .q-head { gap: 8px; }
  .tablewrap th { position: static; }  /* 关闭 sticky 避免移动端错位 */
  .callout { padding: 12px 14px; }
  section[id] { scroll-margin-top: calc(var(--topH, 88px) + 14px); }
}


/* ===== v2.1 新增：顶部 sticky 胶囊目录 + 章节 hero 美化 ===== */

/* 顶部胶囊目录栏（横向滚动 sticky） */
.chapter-nav {
  position: sticky; top: 56px; z-index: 40;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 6px 16px;
  margin: 0 -16px 18px;
  display: flex; gap: 6px; flex-wrap: nowrap;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  transition: box-shadow .22s ease, background .22s ease;
}
.chapter-nav.scrolled {
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 4px 14px rgba(0,0,0,.06);
}
.chapter-nav::-webkit-scrollbar { height: 4px; }
.chapter-nav::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.chapter-tab {
  flex: 0 0 auto;
  display: inline-flex; align-items: center; gap: 4px;
  min-height: 28px; box-sizing: border-box;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1.5px solid var(--border);
  background: var(--surface);
  color: var(--muted);
  font-size: 13px; font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all .2s ease;
  text-decoration: none;
}
.chapter-tab:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 6%, var(--surface));
}
.chapter-tab .tab-num {
  font-weight: 700; font-size: 12px;
  opacity: .85;
}
.chapter-tab.active {
  color: #fdfdfd;
  background: var(--accent);
  border-color: var(--accent);
  font-weight: 600;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--accent) 32%, transparent);
}
.chapter-tab.active .tab-num { opacity: 1; }

/* 章节 hero 卡（每节标题区） */
.chapter-hero {
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--accent) 12%, var(--surface)),
    var(--surface));
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 12px;
  padding: 22px 26px 20px;
  margin-bottom: 20px;
  display: flex; align-items: center; gap: 18px;
  flex-wrap: nowrap;
}
.chapter-hero .step-badge {
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--accent);
  color: var(--surface);
  font-weight: 700; font-size: 15px;
  padding: 8px 16px;
  border-radius: 999px;
  letter-spacing: .08em;
  flex: 0 0 auto;
}
.chapter-hero .step-text { flex: 1 1 auto; min-width: 0; }   /* 取消 200px 下限，防编号与标题折行 */
.chapter-hero h2 {
  margin: 0 0 6px; font-size: 22px; color: var(--text); border: none; padding: 0;
  line-height: 1.35;
}
.chapter-hero .step-sub { color: var(--muted); font-size: 13.5px; margin: 0; }

/* 章节正文卡片化（继承原有 .card 样式 + 强化） */
section[id] {
  margin-top: 38px;
  scroll-margin-top: calc(var(--topH, 88px) + 14px);  /* 让出置顶栏高度（自适应） */
  transition: margin-top .2s ease;
}
section[id]:first-of-type { margin-top: 16px; }
section[id] .chapter-body {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px 26px;
  line-height: 1.78;
}

/* 章节内子卡片（用于丰富内容层次） */
.subcard {
  background: color-mix(in srgb, var(--accent) 4%, var(--surface));
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 0 8px 8px 0;
  padding: 14px 18px;
  margin: 14px 0;
}
.subcard-head {
  font-size: 12.5px; font-weight: 700;
  color: var(--accent); letter-spacing: .06em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.subcard-body { font-size: 14px; line-height: 1.75; }

/* 章节内分隔虚线 */
.divider-dash {
  border: none;
  border-top: 1px dashed var(--border);
  margin: 18px 0;
}

/* bullet 美化（蓝色实心圆点） */
.chapter-body ul { padding-left: 22px; }
.chapter-body ul li {
  position: relative;
  list-style: none;
  margin: 8px 0;
  padding-left: 18px;
}
.chapter-body ul li::before {
  content: "";
  position: absolute; left: 0; top: 12px;
  width: 6px; height: 6px;
  background: var(--accent);
  border-radius: 50%;
}

/* STEP 子标题（h3 章节内小节） */
.chapter-body h3 {
  font-size: clamp(15.5px, 2.3vw, 18px); color: var(--accent);
  margin: 22px 0 10px;
  padding-left: 12px;
  border-left: 3px solid var(--accent);
  line-height: 1.4;
}
.chapter-body h3:first-child { margin-top: 6px; }
.chapter-body h4 {
  font-size: 14.5px; color: var(--text);
  margin: 16px 0 6px;
  font-weight: 600;
}

/* 章节内引用条 */
.chapter-body blockquote {
  margin: 14px 0;
  padding: 12px 16px;
  background: color-mix(in srgb, var(--accent) 5%, var(--surface));
  border-left: 3px solid var(--accent);
  border-radius: 0 6px 6px 0;
  color: var(--text); font-size: 14px;
}

/* 移动端：章节 nav 不再吸顶，避免遮挡 */
@media (max-width: 768px) {
  .chapter-nav {
    top: 52px;
    padding: 8px 16px;
    margin: 0 -16px 18px;
  }
  .chapter-tab { padding: 6px 11px; font-size: 12px; }
  .chapter-hero { padding: 16px 18px; gap: 12px; }
  .chapter-hero h2 { font-size: 18px; }
  .chapter-hero .step-badge { font-size: 13px; padding: 6px 12px; }
  section[id] { scroll-margin-top: calc(var(--topH, 88px) + 14px); }
  section[id] .chapter-body { padding: 16px 18px; }
}

@media (max-width: 640px) { .hero h1 { font-size: 26px; } .wrap { padding: 0 16px 56px; } }

/* ================= v3.0 画板组件与设计系统（范本融合版） ================= */
/* ---- Hero v3：徽章 / 玻璃数据卡 / 标签 / 几何装饰 / 底部波浪 ---- */
.hero { position: relative; overflow: hidden; padding: 56px 22px 64px; }
.hero::before { content: ""; position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(115deg, rgba(255,255,255,.055) 0 2px, transparent 2px 24px); }
.hero h1 { font-size: clamp(28px, 4.6vw, 44px); font-weight: 800; letter-spacing: .01em; }
.hero-badge { display: inline-block; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.38);
  color: var(--hero-text); font-size: 12.5px; letter-spacing: .2em; padding: 4px 15px; border-radius: 999px;
  margin-bottom: 14px; }
.hero .lead { font-size: 15px; }
.hero-stats { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  max-width: 880px; margin: 22px 0 0; }
.hero-stat { background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.28);
  border-radius: 12px; padding: 13px 16px; backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.hero-stat b { display: block; font-size: 24px; font-weight: 800; color: var(--hero-text); line-height: 1.2; }
.hero-stat span { font-size: 12px; opacity: .9; letter-spacing: .05em; }
.hero-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.hero-pills i { font-style: normal; font-size: 12px; padding: 3px 12px; border-radius: 999px;
  background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.32); color: var(--hero-text); }
.hero-deco { position: absolute; border-radius: 24%; pointer-events: none; }
.hero-deco-1 { width: 190px; height: 190px; right: -54px; top: -50px; transform: rotate(24deg);
  background: rgba(255,255,255,.10); }
.hero-deco-2 { width: 110px; height: 110px; right: 12%; bottom: 14%; transform: rotate(-18deg);
  background: rgba(255,255,255,.08); }
.hero-deco-3 { width: 64px; height: 64px; left: 5%; top: 24%; transform: rotate(38deg);
  background: rgba(255,255,255,.10); }
.hero-wave { position: absolute; left: 0; right: 0; bottom: -1px; width: 100%; height: 38px; display: block; }

/* ===== v4.13.0 Hero 双栏 + 数据卡 2×2（结构方案，不依赖 :has，全浏览器可用） ===== */
.hero-grid { display: flex; gap: 34px; align-items: center; }
.hero-col-l { flex: 1 1 auto; min-width: 0; }
.hero-col-r { flex: 0 0 400px; min-width: 0; }
.hero-col-r:empty { display: none; }            /* 无数据卡时右列整列隐藏 */
.hero-stats { display: grid; gap: 12px; margin: 0; max-width: none;
  grid-template-columns: repeat(2, minmax(0, 1fr)); }   /* 固定 2 列 → 2 行 2 列 */
.hero-stat { padding: 15px 17px; }
.hero-stat b { font-size: 26px; }
@media (max-width: 959px) {                      /* 窄屏回落单列，卡片仍为 2×2 */
  .hero-grid { flex-direction: column; align-items: stretch; gap: 20px; }
  .hero-col-r { flex: 1 1 auto; }
}
section:first-of-type { margin-top: 30px; }
@media (max-width: 768px) {
  .hero-wave { height: 30px; }
  section:first-of-type { margin-top: 22px; }
}

/* ---- 章节头 v3：渐变编号方块 + 副描述 + 折叠箭头 ---- */
.chapter-hero { cursor: pointer; user-select: none; }
.sec-no { display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto;
  width: 52px; height: 52px; border-radius: 14px; font-weight: 800; font-size: 19px;
  color: var(--surface); background: linear-gradient(135deg, var(--accent), var(--accent-2));
  box-shadow: 0 6px 16px color-mix(in srgb, var(--accent) 32%, transparent); letter-spacing: .02em;
  line-height: 1; padding-top: 1px; }
.sec-fold { flex: 0 0 auto; color: var(--muted); font-size: 13px; transition: transform .3s; }
section.folded .sec-fold { transform: rotate(-90deg); }
section.folded .chapter-body { display: none; }

/* ---- 二次目录：章节内小节导航条 ---- */
.sub-toc { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; margin: 0 0 18px; padding: 11px 14px;
  background: color-mix(in srgb, var(--accent) 5%, var(--surface)); border: 1px dashed var(--border);
  border-radius: 10px; }
.sub-toc .st-label { font-size: 12px; font-weight: 800; color: var(--accent); letter-spacing: .12em;
  margin-right: 3px; padding-top: 3px; }
.sub-toc a { border: 1px solid var(--border); background: var(--surface); border-radius: 999px;
  padding: 3px 12px; font-size: 12.5px; color: var(--text); }
.sub-toc a:hover { border-color: var(--accent); color: var(--accent); }
.chapter-body h3 { scroll-margin-top: calc(var(--topH, 88px) + 44px); }

/* ---- 画板：Bento 网格看板 ---- */
.bento { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); margin: 16px 0; }
.bento .b-cell { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 16px 18px; transition: transform .18s ease, box-shadow .18s ease; }
.bento .b-cell:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
.bento .b-2 { grid-column: span 2; }
.bento .b-3 { grid-column: span 3; }
.b-cell b.b-t { display: flex; align-items: center; gap: 8px; font-size: 14.5px; margin-bottom: 8px; }
.b-t::before { content: ""; width: 8px; height: 8px; border-radius: 2px; flex: 0 0 auto;
  background: linear-gradient(135deg, var(--accent), var(--accent-2)); }
.b-cell .b-v { font-size: 26px; font-weight: 800; color: var(--accent); margin: 2px 0 6px; line-height: 1.2; }
.b-cell .b-d { font-size: 13.5px; color: var(--muted); line-height: 1.72; }

/* ---- 画板：关键数字巨幕 ---- */
.stat-row { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); margin: 18px 0; }
.stat-cell { background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: 20px 22px; position: relative; overflow: hidden; }
.stat-cell::after { content: ""; position: absolute; right: -22px; top: -22px; width: 84px; height: 84px;
  border-radius: 50%; background: linear-gradient(135deg, var(--accent), var(--accent-2)); opacity: .10; }
.stat-v { font-size: clamp(38px, 7vw, 64px); font-weight: 800; line-height: 1.05;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text; background-clip: text; color: transparent; }
.stat-v small { font-size: .42em; font-weight: 700; margin-left: 4px; }
.stat-l { font-size: 13.5px; color: var(--muted); margin-top: 8px; }
.stat-d { font-size: 12.5px; color: var(--muted); margin-top: 6px; line-height: 1.6; }

/* ---- 画板：横向条形图 ---- */
.bar-chart { display: flex; flex-direction: column; gap: 10px; margin: 16px 0; }
.bar-row { display: grid; grid-template-columns: 150px 1fr 110px; gap: 10px; align-items: center; }
.bar-label { font-size: 13px; text-align: right; }
.bar-track { height: 14px; border-radius: 999px; background: var(--surface-2); overflow: hidden; }
.bar-fill { display: block; height: 100%; border-radius: 999px; min-width: 4px;
  background: linear-gradient(90deg, var(--accent), var(--accent-2)); }
.bar-val { font-size: 12.5px; font-weight: 700; color: var(--accent); }
.bar-val small { font-weight: 400; color: var(--muted); }

/* ---- 画板：竖排时间轴 ---- */
.timeline { position: relative; margin: 16px 0 16px 6px; padding-left: 26px;
  border-left: 2px solid color-mix(in srgb, var(--accent) 35%, transparent);
  display: flex; flex-direction: column; gap: 18px; }
.tl-item { position: relative; }
.tl-item::before { content: ""; position: absolute; left: -33px; top: 8px; width: 12px; height: 12px;
  border-radius: 50%; background: var(--surface); border: 3px solid var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 16%, transparent); }
.tl-time { font-size: 12px; font-weight: 800; color: var(--accent); letter-spacing: .06em;
  line-height: 1.45; }
.tl-title { font-size: 14.5px; font-weight: 700; margin: 2px 0 4px; }
.tl-desc { font-size: 13.5px; color: var(--muted); line-height: 1.7; }

/* ---- 画板：对比矩阵（sticky 首列 + 横向滚动） ---- */
.matrix-wrap { position: relative; margin: 16px 0; border: 1px solid var(--border);
  border-radius: 12px; overflow: hidden; }
.matrix-scroll { overflow-x: auto; }
.matrix-wrap table { margin: 0; min-width: 660px; }
.matrix-wrap th:first-child, .matrix-wrap td:first-child { position: sticky; left: 0; z-index: 2;
  background: var(--surface-2); box-shadow: 2px 0 0 var(--border); font-weight: 700; }
.scroll-hint { font-size: 12px; color: var(--muted); padding: 8px 12px;
  border-top: 1px dashed var(--border); background: var(--surface-2); }

/* ---- 画板：流程阶段卡 ---- */
.phase { display: flex; gap: 14px; align-items: flex-start; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px; padding: 14px 18px; margin: 10px 0; }
.phase-no { flex: 0 0 auto; width: 34px; height: 34px; border-radius: 50%; display: inline-flex;
  align-items: center; justify-content: center; font-weight: 800; font-size: 15px;
  color: var(--surface); background: linear-gradient(135deg, var(--accent), var(--accent-2)); }
.phase-main { flex: 1 1 auto; min-width: 0; }
.phase-t { font-size: 14.5px; font-weight: 700; margin-bottom: 4px; }
.phase-d { font-size: 13.5px; color: var(--muted); line-height: 1.7; }
.phase-meta { flex: 0 0 auto; font-size: 12px; font-weight: 700; color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, var(--surface)); border-radius: 999px; padding: 3px 12px; }

/* ---- 法条引用卡 ---- */
.law-card { background: color-mix(in srgb, var(--accent) 4%, var(--surface));
  border: 1px solid var(--border); border-left: 4px solid var(--accent);
  border-radius: 0 10px 10px 0; padding: 14px 18px; margin: 12px 0; }
.law-name { font-family: "Songti SC","STSong","SimSun",serif; font-weight: 700; font-size: 14.5px;
  color: var(--accent); margin-bottom: 6px; }
.law-text { font-size: 13.5px; line-height: 1.8; }

/* ---- FAQ 折叠问答 ---- */
details.faq { border: 1px solid var(--border); border-radius: 10px; margin: 10px 0;
  overflow: hidden; background: var(--surface); }
details.faq summary { cursor: pointer; list-style: none; padding: 12px 16px; font-weight: 700;
  font-size: 14px; display: flex; align-items: center; gap: 10px; }
details.faq summary::-webkit-details-marker { display: none; }
details.faq summary::before { content: "Q"; flex: 0 0 auto; width: 22px; height: 22px; border-radius: 6px;
  background: var(--accent); color: var(--surface); font-size: 12px; display: inline-flex;
  align-items: center; justify-content: center; font-weight: 800; }
details.faq summary::after { content: "▾"; margin-left: auto; color: var(--muted);
  transition: transform .25s; font-size: 12px; }
details.faq[open] summary::after { transform: rotate(180deg); }
details.faq .faq-a { padding: 0 16px 14px 48px; font-size: 13.5px; line-height: 1.75; }

/* ---- 标签 chips ---- */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.chips i { font-style: normal; font-size: 12.5px; padding: 3px 12px; border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 8%, var(--surface));
  border: 1px solid color-mix(in srgb, var(--accent) 22%, var(--border)); color: var(--accent); }

@media (max-width: 720px) {
  .bento { grid-template-columns: 1fr; }
  .bento .b-2, .bento .b-3 { grid-column: auto; }
  .bar-row { grid-template-columns: 96px 1fr 84px; }
  .bar-label { font-size: 12px; }
  .sec-no { width: 42px; height: 42px; font-size: 15px; border-radius: 11px; }
  .hero-stats { grid-template-columns: repeat(2, 1fr); }
}
@media print {
  .sub-toc, .hero-deco, .hero-wave, .hero-pills, .sec-fold, .scroll-hint, .hero-stats { display: none !important; }
  section.folded .chapter-body { display: block !important; }
  .chapter-hero { cursor: default; }
  details.faq .faq-a { display: block; }
  .matrix-wrap, .matrix-scroll { overflow: visible; }
  .bento .b-cell, .phase, details.faq { border-color: #999; }
  .hero { padding: 0 0 12px; }
}

/* ===== v8.0.0 时间轴卡片化（对齐移动端行程卡版式：圆点 + 渐变竖线 + 圆角卡 + 宽松留白） ===== */
.timeline { position: relative; margin: 18px 0; padding-left: 0; border-left: none;
  display: flex; flex-direction: column; gap: 12px; }
.timeline::before { content: ""; position: absolute; left: 11px; top: 12px; bottom: 12px; width: 2px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 60%, transparent),
    color-mix(in srgb, var(--accent) 12%, transparent)); border-radius: 2px; }
/* v9.0.0：卡片内改为「左时间 + 右内容」两列，时间列等宽数字右对齐，贴近移动端行程卡版式 */
.tl-item { position: relative; margin-left: 32px; padding: 11px 14px 12px;
  display: grid; grid-template-columns: minmax(50px, auto) minmax(0, 1fr);
  column-gap: 12px; align-items: start;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--ds-r-md, 12px);
  transition: box-shadow .24s ease, transform .24s ease, border-color .24s ease; }
.tl-item:hover { transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--accent) 38%, var(--border));
  box-shadow: 0 4px 14px color-mix(in srgb, var(--accent) 12%, transparent); }
.tl-item > .tl-time { grid-column: 1; grid-row: 1 / span 2; margin: 0; padding-top: 1px;
  font-variant-numeric: tabular-nums; white-space: nowrap; }
.tl-item > .tl-title { grid-column: 2; margin: 0 0 3px; }
.tl-item > .tl-desc { grid-column: 2; }
.tl-item::before { left: -27px; top: 14px; transition: transform .24s ease; }
.tl-item:hover::before { transform: scale(1.2); }
@media (max-width: 640px) {
  .timeline { gap: 10px; }
  .tl-item { margin-left: 28px; padding: 10px 12px 11px;
    grid-template-columns: minmax(42px, auto) minmax(0, 1fr); column-gap: 9px; }
  .tl-item::before { left: -25px; }
}

/* ===== v8.0.0 动效升级：CSS 滚动驱动（渐进增强 · 合成器线程运行，不占用主线程） ===== */
@keyframes hrbProgress { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes hrbLineGrow { from { transform: scaleY(0.02); } to { transform: scaleY(1); } }
@supports (animation-timeline: scroll()) {
  /* 阅读进度条改由原生滚动时间轴驱动：更顺滑，且无需 JS 逐帧计算 */
  #progress { width: 100% !important; transform-origin: 0 50%; transform: scaleX(0);
    animation: hrbProgress linear both; animation-timeline: scroll(root block);
    transition: none !important; }
}
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    /* 时间轴竖线随卡片进入视口逐步生长 */
    .anim-ready .timeline::before { transform-origin: 50% 0;
      animation: hrbLineGrow linear both; animation-timeline: view(block);
      animation-range: entry 0% cover 60%; }
  }
}
/* 卡片微交互（仅指针设备，避免触屏粘滞态） */
@media (hover: hover) {
  .kpi-card, .b-cell, .stat-cell, .hero-stat, .phase, .law-card, .tl-item {
    transition: transform .24s ease, box-shadow .24s ease, border-color .24s ease; }
  .kpi-card:hover, .b-cell:hover, .stat-cell:hover, .phase:hover, .law-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px color-mix(in srgb, var(--accent) 11%, transparent); }
}
@media (prefers-reduced-motion: reduce) {
  #progress { animation: none !important; transform: none !important; }
  .anim-ready .timeline::before { animation: none !important; transform: none !important; }
  .kpi-card:hover, .b-cell:hover, .stat-cell:hover, .phase:hover, .law-card:hover { transform: none !important; }
}
@media print {
  #progress { display: none !important; }
  .timeline::before { animation: none !important; transform: none !important; }
}

@media print {
  .topbar, .top-fixed, .palette-pop, #toTop, #progress, .switcher, .toc, .chapter-nav { display: none !important; }
  body { background: #fdfdfd; color: #0e0e0e; font-size: 11.5pt; }
  .hero { background: none !important; color: #0e0e0e !important; padding: 0 0 12px; }
  .card, .concl, .quote { border-color: #999; }
  section { page-break-inside: avoid; }
  a { color: #0e0e0e; border: none; }
  .stat-v { background: none !important; color: var(--accent) !important; -webkit-text-fill-color: var(--accent); }
}

/* ===== v3.0.4 渐入动画（滚动进入，参考范本 reveal）===== */
.reveal-ready .reveal { opacity: 0; transform: translateY(22px); transition: opacity .6s ease, transform .6s cubic-bezier(.2,.75,.3,1); }
.reveal-ready .reveal.in { opacity: 1; transform: none; }
:root { --shadow-sm: 0 2px 10px rgba(0,0,0,.05); --shadow-lg: 0 16px 42px rgba(0,0,0,.13);
  --topH: 88px; /* v4.6.0：顶部栏实际高度，由 JS 实时回写 */ }
@media (prefers-reduced-motion: reduce) { .reveal-ready .reveal { opacity: 1 !important; transform: none !important; } }
@media print { .reveal-ready .reveal { opacity: 1 !important; transform: none !important; } }
/* ===== v4.11.0 内容动效（按内容类型；reduced-motion 与打印自动还原静态） ===== */
:root { --fxd: 0ms; } /* 动效错峰延迟默认值，由 JS 按序覆盖 */
.anim-ready .fx { opacity: 0; transform: translateY(16px);
  transition: opacity .62s ease, transform .62s cubic-bezier(.2,.75,.3,1);
  transition-delay: var(--fxd, 0ms); }
.anim-ready .fx.in { opacity: 1; transform: none; }
.anim-ready .bar-fill { transform-origin: left center; transform: scaleX(0);
  transition: transform .9s cubic-bezier(.22,.8,.28,1); transition-delay: var(--fxd, 0ms); }
.anim-ready .bar-fill.in { transform: scaleX(1); }
.anim-ready .chart svg { opacity: 0; transform: translateY(14px);
  transition: opacity .7s ease, transform .7s cubic-bezier(.2,.75,.3,1); }
.anim-ready .chart svg.in { opacity: 1; transform: none; }
@keyframes fxPop { from { opacity: 0; transform: scale(.97); } to { opacity: 1; transform: none; } }
.anim-ready details.faq[open] > *:not(summary) { animation: fxPop .34s ease both; }
@media (prefers-reduced-motion: reduce) {
  .anim-ready .fx, .anim-ready .bar-fill, .anim-ready .chart svg { opacity: 1 !important; transform: none !important; transition: none !important; }
  .anim-ready details.faq[open] > *:not(summary) { animation: none !important; }
}
@media print {
  .anim-ready .fx, .anim-ready .bar-fill, .anim-ready .chart svg { opacity: 1 !important; transform: none !important; }
  .anim-ready details.faq[open] > *:not(summary) { animation: none !important; }
}
/* ===== v4.0：布局与细节（借鉴咖啡/茶饮/银发/地理教案/新媒体 5 份范本）===== */
/* A 侧栏目录布局 --layout sidebar */
.wrap.layout-sidebar { display: grid; grid-template-columns: 232px minmax(0, 1fr); gap: 28px; align-items: start; }
.wrap.layout-sidebar > #toc { grid-column: 1; grid-row: 1 / span 99; position: sticky; top: 72px; margin: 0;
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px 12px; }
.wrap.layout-sidebar > #toc h2 { font-size: 12.5px; letter-spacing: 2px; color: var(--muted); margin: 0 0 10px; padding-left: 8px; }
.wrap.layout-sidebar > #toc .toc { display: block; }
.wrap.layout-sidebar > #toc .toc a { display: block; padding: 8px 11px; border-radius: 9px; font-size: 13.5px;
  color: var(--muted); text-decoration: none; margin-bottom: 2px; border-left: 2px solid transparent; }
.wrap.layout-sidebar > #toc .toc a:hover { color: var(--accent); background: var(--accent-soft); }
.wrap.layout-sidebar > #toc .toc a.on { color: var(--accent); background: var(--accent-soft); font-weight: 600; border-left-color: var(--accent); }
.wrap.layout-sidebar > :not(#toc) { grid-column: 2; }
@media (max-width: 900px) {
  .wrap.layout-sidebar { grid-template-columns: 1fr; }
  .wrap.layout-sidebar > #toc { grid-column: 1; grid-row: auto; position: static; }
  .wrap.layout-sidebar > :not(#toc) { grid-column: 1; }
  .wrap.layout-sidebar > #toc .toc { display: flex; flex-wrap: wrap; gap: 6px; }
  .wrap.layout-sidebar > #toc .toc a { border-radius: 999px; margin-bottom: 0; }
}
/* B hero 反向斜纹 + 卡片悬停 */
.hero::after { content: ""; position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(-22deg, rgba(255,255,255,.055) 0 2px, transparent 2px 42px); }
.hero-stat { transition: transform .25s ease, box-shadow .25s ease; }
.hero-stat:hover { transform: translateY(-4px); }
/* C 巨幕大数 bignum */
.bignum { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; margin: 24px 0; text-align: center; }
.bignum-cell { padding: 10px 6px; }
.bignum-v { font-size: clamp(48px, 11vw, 108px); font-weight: 900; line-height: 1; letter-spacing: -.02em;
  background: linear-gradient(180deg, var(--accent) 18%, var(--accent-2) 96%);
  -webkit-background-clip: text; background-clip: text; color: transparent; }
.bignum-l { margin-top: 10px; font-size: 14px; font-weight: 700; color: var(--muted); letter-spacing: 1px; }
@media print { .bignum-v { background: none !important; color: var(--accent) !important; -webkit-text-fill-color: var(--accent); } }
/* D 章节头深色渐变 --style dark */
.style-dark .chapter-hero { background: linear-gradient(120deg, var(--hero-1), var(--hero-2)); color: var(--hero-text);
  border-radius: 14px; padding: 15px 20px; }
.style-dark .chapter-hero h2, .style-dark .chapter-hero .step-sub { color: var(--hero-text); }
.style-dark .chapter-hero .step-sub { opacity: .88; }
.style-dark .chapter-hero .sec-no { background: rgba(255,255,255,.2); color: var(--hero-text); }
.style-dark .chapter-hero .sec-fold { color: var(--hero-text); opacity: .85; }
@media print { .style-dark .chapter-hero { background: none !important; color: #0e0e0e !important; border-left: 3px solid var(--accent); border-radius: 0; padding-left: 14px; } .style-dark .chapter-hero h2 { color: #0e0e0e !important; } }
/* E 图标卡 icons */
.icons { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 18px 0; }
.icon-cell { display: flex; gap: 12px; align-items: flex-start; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px; padding: 15px 16px; }
.icon-cell .ico { flex: 0 0 auto; width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center;
  font-size: 17px; background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #fdfdfd; }
.icon-cell .ic-t { font-weight: 700; color: var(--text); }
.icon-cell .ic-d { font-size: 13.5px; color: var(--muted); margin-top: 3px; line-height: 1.6; }
@media print { .icons { break-inside: avoid; } }

/* ===== v4.1：新增图片 / 数据图表 / 长表粘性表头（零外部依赖，单文件离线可用）===== */
/* F 图片与图注 */
.fig { margin: 22px 0; }
.fig img { display: block; width: 100%; height: auto; border-radius: 12px;
  border: 1px solid var(--border); box-shadow: var(--shadow-sm); }
.fig-inline { max-width: 620px; margin: 22px auto; }
.fig figcaption { margin-top: 9px; font-size: 12.5px; color: var(--muted);
  text-align: center; line-height: 1.65; }
.fig figcaption b { color: var(--accent); font-weight: 700; margin-right: 6px; letter-spacing: .5px; }
.fig-note { display: block; font-size: 11.5px; color: var(--muted); opacity: .88; margin-top: 4px; }
.fig-missing { margin: 16px 0; padding: 14px 16px; border: 1px dashed var(--border);
  border-radius: 10px; font-size: 13px; color: var(--muted); background: var(--surface-2); }
@media print { .fig { break-inside: avoid; } .fig img { box-shadow: none; } }
/* G 数据图表 */
.chart { background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: 18px 20px 16px; margin: 22px 0; }
.chart-title { font-size: 14px; font-weight: 700; color: var(--text); line-height: 1.35;
  margin: 0 0 14px; padding-left: 10px; border-left: 3px solid var(--accent); }
.chart svg { display: block; width: 100%; height: auto; overflow: visible; }
.chart .c-val { font-size: 12.5px; font-weight: 700; fill: var(--text); }
.chart .c-lab { font-size: 12px; fill: var(--muted); }
.chart .c-sum { font-size: 26px; font-weight: 900; fill: var(--accent); }
.chart .c-sum-lab { font-size: 12px; fill: var(--muted); letter-spacing: 1px; }
.chart .c-grid { stroke: var(--border); stroke-width: 1; stroke-dasharray: 3 5; }
.chart-legend { display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 14px 0 0; }
.chart-legend span { display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--muted); }
.chart-legend i { width: 11px; height: 11px; border-radius: 3px; background: var(--accent); flex: 0 0 auto; }
.chart-note { margin: 10px 0 0; font-size: 12px; color: var(--muted); }
@media print { .chart { break-inside: avoid; } }
/* H 长表粘性表头（长表自动套 .table-scroll） */
.table-scroll { max-height: 74vh; overflow: auto; border: 1px solid var(--border);
  border-radius: 12px; margin: 18px 0; background: var(--surface); }
.table-scroll > .tablewrap { overflow: visible; margin: 0; border-radius: 0; }
.table-scroll table { margin: 0; }
.table-scroll thead th { position: sticky; top: 0; z-index: 3;
  background: var(--surface-2); box-shadow: inset 0 -1px 0 var(--border); }
@media (max-width: 720px) { .table-scroll { max-height: none; }
  .table-scroll thead th { position: static; } }
@media print { .table-scroll { max-height: none; overflow: visible; border-radius: 0; }
  .table-scroll thead th { position: static; } }
/* v5.0：AI 配图角标 + 图组 gallery */
.fig .fig-ai-tag { display: inline-block; margin-left: 8px; padding: 1px 8px; border-radius: 20px;
  font-size: 11px; letter-spacing: .06em; color: var(--accent); border: 1px solid var(--accent);
  background: var(--surface-2); vertical-align: 1px; }
.gallery { margin: 22px 0; }
.gallery-title { font-size: 14px; font-weight: 700; color: var(--text); line-height: 1.35;
  margin: 0 0 12px; padding-left: 10px; border-left: 3px solid var(--accent); }
.g-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.gallery.g-3 .g-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.g-cell { margin: 0; }
.g-cell img { display: block; width: 100%; height: auto; border-radius: 10px;
  border: 1px solid var(--border); box-shadow: var(--shadow-sm); }
.g-cell figcaption { margin-top: 7px; font-size: 12px; color: var(--muted);
  text-align: center; line-height: 1.6; }
.g-cell figcaption b { color: var(--accent); font-weight: 700; margin-right: 5px; }
@media (max-width: 720px) { .g-grid, .gallery.g-3 .g-grid { grid-template-columns: 1fr; } }
@media print { .gallery { break-inside: avoid; } .g-cell img { box-shadow: none; } }

/* ===== v5.1.0 图形围栏（mermaid 内嵌 SVG / SVG 直嵌）与代码块 ===== */
.fig-diagram img { background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 12px; padding: 10px; box-sizing: border-box; }
.fig-diagram figcaption { text-align: center; }
.diagram-fallback { margin: 16px 0; border: 1px dashed var(--border); border-radius: 12px;
  background: var(--surface-2); padding: 12px 14px; }
.diagram-fallback .df-head { font-size: 12.5px; color: var(--muted); margin-bottom: 8px; line-height: 1.65; }
.diagram-fallback .df-head b { color: var(--text); }
.diagram-fallback .df-tag { display: inline-block; padding: 1px 8px; margin-right: 6px; border-radius: 999px;
  border: 1px solid var(--border); background: var(--surface); font-size: 11.5px; color: var(--accent); }
.diagram-fallback pre, pre.code { background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 12px; overflow-x: auto; font-size: 12.5px; line-height: 1.55;
  margin: 0; }
pre.code { margin: 14px 0; }
pre.code code, .diagram-fallback code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: pre; }
@media print { .fig-diagram img { break-inside: avoid; } }

/* ===== v4.3.0 移动端抽屉式目录（≤640px） ===== */
.toc-btn { display: none; }
.toc-drawer { position: fixed; inset: 0; z-index: 96; display: none; }
.toc-drawer.open { display: block; }
.toc-mask { position: absolute; inset: 0; background: rgba(6,12,20,.48);
  -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px); }
.toc-panel { position: absolute; left: 0; right: 0; top: 0; max-height: 88vh; overflow-y: auto;
  -webkit-overflow-scrolling: touch; background: var(--surface);
  border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;
  padding: 16px 16px 22px; box-shadow: 0 18px 44px rgba(0,0,0,.3); animation: tocdrop .22s ease; }
@keyframes tocdrop { from { transform: translateY(-16px); opacity: .5; }
  to { transform: translateY(0); opacity: 1; } }
.toc-panel .dp-head { display: flex; align-items: flex-start; justify-content: space-between; margin: 0 0 2px; }
.toc-panel .dp-head h3.dp-title { flex: 1 1 auto; min-width: 0; margin: 0 10px 0 0; font-size: 16px;
  font-weight: 700; letter-spacing: 0; line-height: 1.35; color: var(--text); text-align: left;
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden;
  word-break: break-word; }
.toc-panel .dp-kicker { margin: 0 0 14px; font-size: 12px; letter-spacing: .14em; color: var(--muted); }
.toc-panel .dp-head h3 { margin: 0; font-size: 13px; letter-spacing: .14em; color: var(--muted); }
.toc-panel .dp-close { border: 1px solid var(--border); background: var(--surface-2); color: var(--text);
  width: 34px; height: 34px; border-radius: 50%; font-size: 15px; line-height: 1; cursor: pointer; }
.toc-list { display: grid; gap: 8px; }
.toc-list .chapter-tab { display: flex; align-items: center; gap: 10px; width: 100%; min-height: 46px;
  padding: 12px 14px; border: 1px solid var(--border); border-radius: 12px; font-size: 15px;
  color: var(--text); background: var(--surface-2); }
.toc-list .chapter-tab .tab-num { flex: 0 0 auto; font-size: 12px; color: var(--muted); }
.toc-list .chapter-tab.active { color: #fdfdfd; border-color: transparent;
  background: linear-gradient(135deg, var(--accent), var(--accent-2)); }
.toc-list .chapter-tab.active .tab-num { color: rgba(255,255,255,.86); }

.dp-sub { margin: 18px 0 8px; font-size: 12.5px; letter-spacing: .14em; color: var(--muted); }
.dp-sw { display: flex; flex-wrap: wrap; gap: 12px; }
@media (max-width: 640px) {
  .tf-row2 { display: none; }
  .tf-row1 { gap: 8px; padding: 8px 16px 0; }
  .fixed-toc { display: flex; align-items: center; gap: 5px; padding: 2px 0; }
  .fixed-toc .chapter-tab { min-height: 30px; padding: 6px 11px; font-size: 12px; }
  .toc-btn { display: inline-flex; align-items: center; gap: 4px; margin-left: 4px; flex: 0 0 auto;
    min-height: 30px; box-sizing: border-box; padding: 5px 10px;
    border: 1px solid var(--border); background: var(--surface);
    color: var(--text); border-radius: 999px; font-size: 13px; cursor: pointer; }
  .toc-btn:active { transform: scale(.97); }
  section[id] { scroll-margin-top: calc(var(--topH, 88px) + 14px); }
  .chapter-body h3 { scroll-margin-top: calc(var(--topH, 88px) + 44px); }
/* ===== v6.0.0 细节升级：无障碍 / 打印 / 交互 / 动画增强 ===== */
/* --- 无障碍：焦点可见（键盘导航） --- */
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
a:focus-visible, button:focus-visible, input:focus-visible, summary:focus-visible,
[tabindex]:focus-visible, .chapter-tab:focus-visible, .palette-pill:focus-visible,
.toc-btn:focus-visible, .dp-close:focus-visible, .swatch:focus-visible, #toTop:focus-visible,
th[data-sort]:focus-visible, .chapter-hero:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
/* --- 无障碍：跳至正文 --- */
.skip-link { position: absolute; left: -9999px; top: 0; z-index: 999; padding: 8px 14px;
  background: var(--accent); color: var(--on-accent); border-radius: 0 0 8px 0; font-size: 13px; }
.skip-link:focus { left: 0; }
/* --- 无障碍：读屏专用文本 --- */
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
/* --- 目录搜索（抽屉内） --- */
.dp-search { width: 100%; box-sizing: border-box; margin: 0 0 12px; padding: 9px 12px;
  border: 1px solid var(--border); border-radius: 10px; background: var(--surface-2);
  color: var(--text); font-size: 14px; -webkit-appearance: none; }
.dp-search:focus { border-color: var(--accent); outline: none; }
.dp-empty { display: none; padding: 14px 4px; color: var(--muted); font-size: 13px; }
/* --- 长表点击排序 --- */
th[data-sort] { cursor: pointer; user-select: none; -webkit-user-select: none; white-space: nowrap; }
th[data-sort]::after { content: "\21C5"; margin-left: 6px; opacity: .35; font-size: 11px; }
th[data-sort][data-dir="asc"]::after { content: "\2191"; opacity: .9; }
th[data-sort][data-dir="desc"]::after { content: "\2193"; opacity: .9; }
/* --- 图片点击放大（lightbox） --- */
.fig img, .g-cell img, .fig-diagram img { cursor: zoom-in; }
#lightbox { position: fixed; inset: 0; z-index: 120; display: none; align-items: center;
  justify-content: center; background: rgba(6,12,20,.9); padding: 24px; }
#lightbox.open { display: flex; }
#lightbox img { max-width: 96vw; max-height: 92vh; border-radius: 10px; box-shadow: 0 24px 60px rgba(0,0,0,.5); }
#lightbox .lb-close { position: absolute; top: 16px; right: 20px; width: 42px; height: 42px;
  border-radius: 50%; border: 1px solid rgba(255,255,255,.4); background: rgba(0,0,0,.35);
  color: #fdfdfd; font-size: 20px; line-height: 1; cursor: pointer; }
#lightbox .lb-cap { position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%);
  color: #fdfdfd; font-size: 13px; max-width: 88vw; text-align: center; opacity: .9; }
/* --- 打印：页边距 + 局部避断（取消整章避断，避免大片空白） --- */
@page { size: A4; margin: 16mm 13mm 16mm; }
@media print {
  section { page-break-inside: auto; break-inside: auto; }
  table, .tablewrap, .table-scroll { break-inside: auto; }
  thead { display: table-header-group; }
  tr, .card, .concl, .quote, .kpi-card, .b-cell, .stat-cell, .tl-item, .phase,
  .law-card, details.faq, .fig, .chart, .gallery, .bignum-cell, .icons .ic-cell,
  .callout { break-inside: avoid; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 9pt; color: #555; word-break: break-all; }
  .skip-link { display: none !important; }
}
/* --- 动画增强：整体过渡与细节 --- */
.chapter-tab { transition: background .28s ease, border-color .28s ease, color .28s ease, transform .18s ease; }
.hero-stat, .kpi-card, .b-cell, .chapter-hero, .top-fixed, .toc-panel, .card, .phase, .law-card,
details.faq, .tl-title { transition: background-color .3s ease, border-color .3s ease, color .3s ease; }
#progress { transition: width .12s linear; }
#toTop { opacity: 0; transform: translateY(10px); transition: opacity .28s ease, transform .28s ease; }
#toTop.show { opacity: 1; transform: none; }
@keyframes unfoldIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: none; } }
/* 时间轴节点弹出 */
.anim-ready .tl-item::before { transform: scale(0); transition: transform .46s cubic-bezier(.3,1.4,.5,1) .12s; }
.anim-ready .tl-item.in::before { transform: scale(1); }
/* hero 装饰缓慢漂浮（用 translate 属性，保留既有 rotate） */
@keyframes floatSlow { 0%,100% { translate: 0 0; } 50% { translate: 0 -8px; } }
@media (prefers-reduced-motion: no-preference) {
  .hero-deco { animation: floatSlow 7s ease-in-out infinite; }
  .hero-deco-2 { animation-duration: 9.5s; animation-delay: -2s; }
  .hero-deco-3 { animation-duration: 11.5s; animation-delay: -4s; }
}
@media (prefers-reduced-motion: reduce) {
  .hero-deco { animation: none !important; }
  .anim-ready .tl-item::before { transform: none !important; transition: none !important; }
  #toTop { transition: none !important; }
}
@media print {
  .hero-deco { animation: none !important; }
  .anim-ready .tl-item::before { transform: none !important; }
  #toTop { display: none !important; }
}
  .wrap { padding: 0 16px 56px; }
}
"""

JS_FIXED = """
(function(){
  var THEMES = /*@THEME_LIST@*/[];
  var root = document.documentElement;
  function apply(id){
    var t = THEMES.filter(function(x){return x.id===id;})[0]; if(!t) return;
    root.setAttribute('data-theme', t.id);
    var tn = document.getElementById('themeName'); if (tn) tn.textContent = t.zh;
    var mt = document.getElementById('metaTheme');
    if (mt && t.bg) mt.setAttribute('content', t.bg);
    Array.prototype.forEach.call(document.querySelectorAll('.swatch'), function(b){
      b.setAttribute('aria-pressed', String(b.dataset.id===t.id)); });
    try { localStorage.setItem('hrb-theme', t.id); } catch(e){}
  }
  var box = document.getElementById('swatches');
  var boxD = document.getElementById('swatchesDrawer');
  THEMES.forEach(function(t){
    [box, boxD].forEach(function(host){
      if (!host) return;
      var b = document.createElement('button');
      b.className='swatch'; b.dataset.id=t.id; b.title=t.zh; b.setAttribute('aria-label',t.zh);
      b.style.background='linear-gradient(135deg,'+t.accent+' 50%,'+t.accent2+' 50%)';
      b.addEventListener('click', function(){ apply(t.id); });
      host.appendChild(b);
    });
  });
  var saved=null; try{ saved=localStorage.getItem('hrb-theme'); }catch(e){}
  var hasSaved = saved && THEMES.some(function(t){ return t.id === saved; });
  var sysDark = !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  var autoId = '/*@DEFAULT_THEME@*/';
  if (sysDark && THEMES.some(function(t){ return t.id === 'galaxy'; })) autoId = 'galaxy';
  /* v8.0.0：主题切换走 View Transitions，跨主题淡变；不支持或用户已开启减弱动效时静默回退 */
  (function(){
    var rawApply = apply;
    apply = function(id){
      var reduce = false;
      try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch(e){}
      if (!reduce && document.startViewTransition && root.getAttribute('data-theme')) {
        try { document.startViewTransition(function(){ rawApply(id); }); return; } catch(e){}
      }
      rawApply(id);
    };
  })();
  apply(hasSaved ? saved : autoId);
  var bar=document.getElementById('progress'), top=document.getElementById('toTop');

  /* ===== v2.1 新增：滚动联动 + 胶囊目录吸顶 ===== */
  /* ===== v4.6.0 顶部栏高度自适应（大标题可多行，锚点偏移随之同步） ===== */
  var topFixed = document.getElementById('topFixed');
  function syncTopH(){
    if (!topFixed) return;
    try { root.style.setProperty('--topH', topFixed.offsetHeight + 'px'); } catch(e){}
  }
  function topOffset(){ return topFixed ? Math.max(60, topFixed.offsetHeight + 10) : 84; }
  syncTopH();
  window.addEventListener('load', syncTopH);
  window.addEventListener('resize', syncTopH);
  setTimeout(syncTopH, 200);
  try { if (document.fonts && document.fonts.ready) document.fonts.ready.then(syncTopH); } catch(e){}

  var nav = document.getElementById('chapterNav');
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.chapter-tab'));
  var sections = tabs.map(function(t){ return document.getElementById(t.dataset.target); })
                     .filter(function(x){ return !!x; });

  function setActive(id){
    if (!tabs.length) return;
    tabs.forEach(function(t){
      var on = t.dataset.target === id;
      t.classList.toggle('active', on);
      if (on) { t.setAttribute('aria-current', 'true'); } else { t.removeAttribute('aria-current'); }
      if (on && t.closest && t.closest('.fixed-toc')) {
        // v4.5.0：把当前激活的 tab 精确滚到胶囊栏正中（只动横向，不动页面纵向）
        var nb = t.closest('.fixed-toc');
        var nr = nb.getBoundingClientRect(), tr = t.getBoundingClientRect();
        var delta = (tr.left + tr.width / 2) - (nr.left + nr.width / 2);
        try { nb.scrollBy({left: delta, behavior: 'smooth'}); } catch(e){ nb.scrollLeft += delta; }
      }
    });
    if (id) { try { history.replaceState(null, '', '#'+id); } catch(e){} }
  }

  function onScroll(){
    var h=document.documentElement.scrollHeight-window.innerHeight;
    bar.style.width=(h>0?window.scrollY/h*100:0)+'%';
    var showTop = window.scrollY > 500;
    if (showTop) {
      if (top.style.display !== 'block') { top.style.display = 'block';
        requestAnimationFrame(function(){ top.classList.add('show'); }); }
    } else {
      top.classList.remove('show');
      if (top.style.display !== 'none') {
        setTimeout(function(){ if (!top.classList.contains('show')) top.style.display = 'none'; }, 300);
      }
    }

    /* tabbar 吸顶后变玻璃态 */
    if (nav) {
      var navTop = nav.getBoundingClientRect().top;
      nav.classList.toggle('scrolled', navTop <= 56 && window.scrollY > 200);
    }

    /* scroll-spy：找出最接近视口顶部的章节 */
    if (sections.length) {
      var probe = window.scrollY + 200;  /* 偏移 200px 让激活区更靠下 */
      var cur = sections[0].id;
      for (var i=0;i<sections.length;i++){
        if (sections[i].offsetTop <= probe) cur = sections[i].id;
        else break;
      }
      /* 如果滚到了最底部，强制激活最后一个 */
      if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 8) {
        cur = sections[sections.length-1].id;
      }
      setActive(cur);
    }
  }
  window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  top.addEventListener('click', function(){ window.scrollTo({top:0,behavior:'smooth'}); });

  /* 点击胶囊 tab → 平滑滚动 + 立即激活 + 写 hash */
  if (nav) {
    nav.addEventListener('click', function(e){
      var t = (e.target && e.target.closest) ? e.target.closest('.chapter-tab') : null;
      if (!t) t = dragTab;   /* v8.0.0：捕获/拖动后 click.target 可能不是胶囊，用按下时记录的元素兜底 */
      if (!t) return;
      e.preventDefault();
      var sec = document.getElementById(t.dataset.target);
      if (!sec) return;
      setActive(t.dataset.target);
      window.scrollTo({top: sec.offsetTop - topOffset(), behavior: 'smooth'});
    });
  }



  /* v3.0.1 配色胶囊：点击展开/收起色板浮层；选中后自动收起 */
  var pill = document.getElementById('palettePill');
  var pal = document.getElementById('palette');
  if (pill && pal) {
    pill.addEventListener('click', function(e){
      e.stopPropagation();
      var open = pal.classList.toggle('open');
      pill.setAttribute('aria-expanded', String(open));
    });
    box.addEventListener('click', function(){
      pal.classList.remove('open');
      pill.setAttribute('aria-expanded', 'false');
    });
    document.addEventListener('click', function(e){
      if (pal.classList.contains('open') && !(e.target.closest && e.target.closest('#palette'))) {
        pal.classList.remove('open');
        pill.setAttribute('aria-expanded', 'false');
      }
    });
  }
  var reduceMotionFold = false;
  try { reduceMotionFold = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch(e){}
  /* v3：章节折叠（点击章节头切换；折叠后 scroll-spy 按新布局重算） */
  document.addEventListener('click', function(e){
    var h = e.target && e.target.closest ? e.target.closest('.chapter-hero') : null;
    if (!h || e.target.closest('a')) return;
    var sec = h.closest('section');
    if (sec) {
      sec.classList.toggle('folded');
      if (!sec.classList.contains('folded')) {
        var cb = sec.querySelector('.chapter-body');
        if (cb && !reduceMotionFold) cb.style.animation = 'unfoldIn .32s ease';
      }
      if (sec.__foldTimer) clearTimeout(sec.__foldTimer);
      sec.__foldTimer = setTimeout(function(){
        var cb2 = sec.querySelector('.chapter-body');
        if (cb2) cb2.style.animation = '';
      }, 600);
    }
  });

  /* 初始 hash 跳转 */
  if (location.hash) {
    var sec0 = document.getElementById(location.hash.slice(1));
    if (sec0) { setTimeout(function(){ window.scrollTo({top: sec0.offsetTop - topOffset(), behavior:'smooth'}); }, 50); }
  }

  /* v3.0.4 渐入动画（滚动进入；无 IO 或 reduced-motion 时直接显示） */
  try {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduce) {
      root.classList.add('reveal-ready');
      var rvs = document.querySelectorAll('.reveal');
      if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function(es){
          es.forEach(function(en){ if (en.isIntersecting){ en.target.classList.add('in'); io.unobserve(en.target); } });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
        Array.prototype.forEach.call(rvs, function(el){ io.observe(el); });
      } else {
        Array.prototype.forEach.call(rvs, function(el){ el.classList.add('in'); });
      }
    }
  } catch(err){}

  /* ===== v4.11.0 内容动效：卡片错峰淡入 / 条形生长 / 图表淡入 / 数字滚动 ===== */
  try {
    var reduceFx = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduceFx && 'IntersectionObserver' in window) {
      root.classList.add('anim-ready');
      var countUp = function(el){
        if (!el || el.dataset.fxDone) return;
        el.dataset.fxDone = '1';
        if (el.children.length) return;   /* 含子元素（如单位 <small>）不滚动，避免破坏结构 */
        var raw = (el.textContent || '').trim();
        var m = raw.match(/-?[0-9][0-9,]*(?:[.][0-9]+)?/);
        if (!m) return;
        var numStr = m[0];
        var target = parseFloat(numStr.split(',').join(''));
        if (!isFinite(target) || target === 0) return;
        var dec = (numStr.split('.')[1] || '').length;
        var comma = numStr.indexOf(',') >= 0;
        var pre = raw.slice(0, m.index), suf = raw.slice(m.index + numStr.length);
        var grp = function(str){
          var neg = str.charAt(0) === '-';
          var body = neg ? str.slice(1) : str;
          var parts = body.split('.');
          var ip = parts[0], out = '', c = 0;
          for (var i = ip.length - 1; i >= 0; i--) {
            out = ip.charAt(i) + out;
            c++;
            if (c % 3 === 0 && i > 0) out = ',' + out;
          }
          return (neg ? '-' : '') + out + (parts.length > 1 ? '.' + parts[1] : '');
        };
        var dur = 760, start = null;
        var fmt = function(val){
          var t = val.toFixed(dec);
          if (comma) t = grp(t);
          return pre + t + suf;
        };
        var step = function(ts){
          if (start === null) start = ts;
          var p = Math.min((ts - start) / dur, 1);
          el.textContent = fmt(target * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(target);
        };
        el.textContent = fmt(0);
        requestAnimationFrame(step);
      };

      var fxEls = [];
      Array.prototype.forEach.call(
        document.querySelectorAll('.kpi-card, .b-cell, .stat-cell, .tl-item, .phase, .matrix-wrap, details.faq, .law-card, .hero-stat, .fig, .g-cell'),
        function(el){ el.classList.add('fx'); fxEls.push(el); });
      /* 同父容器内错峰 */
      var gcount = {};
      fxEls.forEach(function(el){
        var key = (el.parentNode && el.parentNode.className) ? el.parentNode.className : 'r';
        gcount[key] = (gcount[key] || 0) + 1;
        el.style.setProperty('--fxd', Math.min((gcount[key] - 1) * 65, 320) + 'ms');
      });
      var bars = document.querySelectorAll('.bar-fill');
      Array.prototype.forEach.call(bars, function(el, i){ el.style.setProperty('--fxd', Math.min(i * 55, 300) + 'ms'); });
      var svgs = document.querySelectorAll('.chart svg');

      var ioFx = new IntersectionObserver(function(es){
        es.forEach(function(en){
          if (!en.isIntersecting) return;
          var t = en.target;
          t.classList.add('in');
          var isBar = t.classList && t.classList.contains('bar-fill');
          var isSvg = (t.tagName || '').toLowerCase() === 'svg';
          if (!isBar && !isSvg) {
            var v = t.querySelector('.kpi-value, .b-v, .stat-v, .hero-stat b, b');
            if (v) countUp(v);
          }
          ioFx.unobserve(t);
        });
      }, { rootMargin: '0px 0px -6% 0px', threshold: 0.12 });

      fxEls.concat(Array.prototype.slice.call(bars), Array.prototype.slice.call(svgs))
           .forEach(function(el){ ioFx.observe(el); });
    }
  } catch(err){}

  /* ===== v4.5.0 顶部目录条：左右拖动 + 拖动后抑制误点 ===== */
  var suppressClick = false;
  if (nav) {
    var dragging = false, dragMoved = false, dragX = 0, dragLeft = 0, dragId = null;
    nav.addEventListener('click', function(e){
      if (suppressClick) { e.preventDefault(); e.stopPropagation(); suppressClick = false; return; }
    }, true);
    var dragTab = null;
    nav.addEventListener('pointerdown', function(e){
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      dragging = true; dragMoved = false; dragX = e.clientX; dragLeft = nav.scrollLeft; dragId = e.pointerId;
      dragTab = (e.target && e.target.closest) ? e.target.closest('.chapter-tab') : null;
      /* v8.0.0 修复：不在按下瞬间 setPointerCapture，也不立即加 .dragging。
         指针捕获会把后续 click 的 target 改写成容器本身，.dragging 又会给胶囊设 pointer-events:none，
         二者叠加导致首次点击落空（须点两次才跳转）。改为位移超过阈值后才捕获。 */
    });
    nav.addEventListener('pointermove', function(e){
      if (!dragging) return;
      var dx = e.clientX - dragX;
      if (!dragMoved && Math.abs(dx) > 8) {
        dragMoved = true;
        nav.classList.add('dragging');
        try { nav.setPointerCapture(dragId); } catch(err){}
      }
      if (dragMoved) { nav.scrollLeft = dragLeft - dx; if (e.cancelable) e.preventDefault(); }
    }, {passive: false});
    var endDrag = function(){
      if (!dragging) return;
      dragging = false;
      nav.classList.remove('dragging');
      if (dragMoved) {
        try { nav.releasePointerCapture(dragId); } catch(err){}
        suppressClick = true; setTimeout(function(){ suppressClick = false; }, 80);
      }
    };
    nav.addEventListener('pointerup', endDrag);
    nav.addEventListener('pointercancel', endDrag);
  }

  /* ===== v4.3.0 移动端抽屉式目录 ===== */
  var tocBtn = document.getElementById('tocBtn');
  var drawer = document.getElementById('tocDrawer');
  function openDrawer(){
    if (!drawer) return;
    drawer.classList.add('open'); drawer.setAttribute('aria-hidden','false');
    if (tocBtn) tocBtn.setAttribute('aria-expanded','true');
    document.body.style.overflow='hidden';
  }
  function closeDrawer(){
    if (!drawer) return;
    drawer.classList.remove('open'); drawer.setAttribute('aria-hidden','true');
    if (tocBtn) tocBtn.setAttribute('aria-expanded','false');
    document.body.style.overflow='';
  }
  if (tocBtn && drawer) {
    tocBtn.addEventListener('click', function(){
      drawer.classList.contains('open') ? closeDrawer() : openDrawer();
    });
    drawer.addEventListener('click', function(e){
      if (e.target.closest && e.target.closest('[data-close]')) { closeDrawer(); return; }
      var t = e.target.closest ? e.target.closest('.chapter-tab') : null;
      if (!t) return;
      e.preventDefault();
      var sec = document.getElementById(t.dataset.target);
      if (sec) { setActive(t.dataset.target); window.scrollTo({top: sec.offsetTop - topOffset(), behavior: 'smooth'}); }
      closeDrawer();
    });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeDrawer(); });
    window.addEventListener('resize', function(){ if (window.innerWidth > 640) closeDrawer(); });
  /* ===== v6.0.0 无障碍：scroll-spy 当前章 aria-current（由 setActive 写入） ===== */
  /* ===== v6.0.0 图片点击放大（lightbox；键盘 Esc 关闭） ===== */
  try {
    var zoomImgs = document.querySelectorAll('.fig img, .g-cell img, .fig-diagram img');
    if (zoomImgs.length) {
      var lb = document.createElement('div');
      lb.id = 'lightbox'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true');
      lb.setAttribute('aria-label', '图片预览');
      lb.innerHTML = '<button class="lb-close" aria-label="关闭预览">✕</button><img alt=""><div class="lb-cap"></div>';
      document.body.appendChild(lb);
      var lbImg = lb.querySelector('img'), lbCap = lb.querySelector('.lb-cap');
      var closeLb = function(){ lb.classList.remove('open'); lbImg.removeAttribute('src');
        lbCap.textContent = ''; document.body.style.overflow = ''; };
      var openLb = function(src, cap){
        if (!src) return;
        lbImg.setAttribute('src', src); lbCap.textContent = cap || '';
        lb.classList.add('open'); document.body.style.overflow = 'hidden';
        var c = lb.querySelector('.lb-close'); if (c) c.focus();
      };
      Array.prototype.forEach.call(zoomImgs, function(im){
        im.addEventListener('click', function(){
          var cap = '';
          var fig = im.closest('figure') || im.closest('.g-cell');
          if (fig) { var c = fig.querySelector('figcaption'); if (c) cap = (c.textContent || '').trim(); }
          openLb(im.currentSrc || im.src, cap);
        });
      });
      lb.addEventListener('click', function(e){
        if (e.target === lb || (e.target.closest && e.target.closest('.lb-close'))) closeLb();
      });
      document.addEventListener('keydown', function(e){
        if (e.key === 'Escape' && lb.classList.contains('open')) closeLb();
      });
    }
  } catch(err){}

  /* ===== v6.0.0 目录搜索（抽屉内过滤章节） ===== */
  try {
    var tlBox = document.getElementById('tocList');
    if (tlBox) {
      var swBox = document.createElement('input');
      swBox.type = 'search'; swBox.className = 'dp-search';
      swBox.setAttribute('aria-label', '搜索章节'); swBox.setAttribute('placeholder', '搜索章节…');
      var emptyTip = document.createElement('p');
      emptyTip.className = 'dp-empty'; emptyTip.textContent = '未找到匹配章节';
      tlBox.parentNode.insertBefore(swBox, tlBox);
      tlBox.parentNode.insertBefore(emptyTip, tlBox.nextSibling);
      swBox.addEventListener('input', function(){
        var q = (swBox.value || '').trim().toLowerCase();
        var tabs = tlBox.querySelectorAll('.chapter-tab'); var shown = 0;
        Array.prototype.forEach.call(tabs, function(t){
          var hit = !q || (t.textContent || '').toLowerCase().indexOf(q) >= 0;
          t.style.display = hit ? '' : 'none'; if (hit) shown++;
        });
        emptyTip.style.display = shown ? 'none' : 'block';
      });
    }
  } catch(err){}

  /* ===== v6.0.0 长表点击表头排序（数值列自动识别） ===== */
  try {
    Array.prototype.forEach.call(
      document.querySelectorAll('.tablewrap table, .table-scroll table, .matrix-wrap table'),
      function(tb){
        var head = tb.querySelector('thead tr'); if (!head) return;
        var body = tb.querySelector('tbody'); if (!body) return;
        var ths = Array.prototype.slice.call(head.children);
        var rows = Array.prototype.slice.call(body.children);
        if (rows.length < 3) return;
        var numOf = function(txt){
          var s = String(txt || '').replace(/,/g, '').replace(/%/g, '').trim();
          var v = parseFloat(s);
          return isFinite(v) ? v : null;
        };
        ths.forEach(function(th, ci){
          var vals = rows.map(function(r){ return r.children[ci] ? numOf(r.children[ci].textContent) : null; });
          var ok = vals.every(function(v){ return v !== null; });
          if (!ok) return;
          th.setAttribute('data-sort', '');
          th.setAttribute('role', 'button'); th.setAttribute('tabindex', '0'); th.setAttribute('title', '点击排序');
          var doSort = function(){
            var dir = th.getAttribute('data-dir') === 'asc' ? 'desc' : 'asc';
            ths.forEach(function(o){ o.removeAttribute('data-dir'); });
            th.setAttribute('data-dir', dir);
            rows.sort(function(a, b){
              var av = numOf(a.children[ci].textContent); if (av === null) av = 0;
              var bv = numOf(b.children[ci].textContent); if (bv === null) bv = 0;
              return dir === 'asc' ? av - bv : bv - av;
            });
            rows.forEach(function(r){ body.appendChild(r); });
          };
          th.addEventListener('click', doSort);
          th.addEventListener('keydown', function(e){
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); doSort(); }
          });
        });
      });
  } catch(err){}

  /* ===== v6.0.0 环形图分段错峰淡入 ===== */
  try {
    var reduceFx2 = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var segs = document.querySelectorAll('.chart svg .donut-seg');
    if (segs.length && !reduceFx2 && 'IntersectionObserver' in window) {
      Array.prototype.forEach.call(segs, function(el, i){
        el.setAttribute('data-op', el.getAttribute('stroke-opacity') || '1');
        el.setAttribute('stroke-opacity', '0');
        el.style.transition = 'stroke-opacity .55s ease';
        el.style.transitionDelay = Math.min(i * 95, 520) + 'ms';
      });
      var ioSeg = new IntersectionObserver(function(es){
        es.forEach(function(en){
          if (!en.isIntersecting) return;
          Array.prototype.forEach.call(en.target.querySelectorAll('.donut-seg'), function(el){
            el.setAttribute('stroke-opacity', el.getAttribute('data-op') || '1');
          });
          ioSeg.unobserve(en.target);
        });
      }, {threshold: 0.2});
      Array.prototype.forEach.call(document.querySelectorAll('.chart svg'), function(s){ ioSeg.observe(s); });
    }
  } catch(err){}
  }
})();
"""


def _md_inline(t):
    """转义后处理行内标记（**粗体** / `代码`），用于来源表等纯文本单元格。"""
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


# ===== v6.2.0 设计纪律层：版式母题 =====
try:
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from motifs import css as motif_css, DEFAULT as MOTIF_DEFAULT, MOTIFS as MOTIF_TABLE
except Exception:  # 母题模块缺失时优雅降级，不影响既有能力
    def motif_css(_m): return ""
    MOTIF_DEFAULT = "editorial"
    MOTIF_TABLE = {"editorial": {"motion": "orchestrated"}, "classic": {"motion": "staggered"}}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_html(spec):
    theme = spec.get("theme", "sunset")
    if theme not in BY_ID:
        theme = "sunset"
    hero_badge = spec.get("hero_badges", "")
    hero_stats = spec.get("hero_stats") or []
    hero_pills = spec.get("hero_pills") or []
    f = spec.get("footer", {}) or {}
    date = spec.get("date", "")
    # v4.0：布局与章节头样式开关
    _lay = (spec.get("layout") or "").strip()
    layout_class = ("layout-" + _lay) if _lay in ("sidebar",) else ""
    _sty = (spec.get("style") or "").strip()
    style_class = ("style-" + _sty) if _sty in ("dark",) else ""
    # v6.2.0 版式母题
    _mot = (spec.get("motif") or MOTIF_DEFAULT).strip()
    if _mot not in MOTIF_TABLE:
        _mot = MOTIF_DEFAULT
    style_class = (style_class + " motif-%s motion-%s" % (_mot, MOTIF_TABLE[_mot].get("motion", "orchestrated"))).strip()

    themes_css = "\n".join([css_block(PALETTES[0], ':root, [data-theme="%s"]' % PALETTES[0]["id"])]
                           + [css_block(p) for p in PALETTES[1:]])
    themes_css = themes_css + "\n" + motif_css(_mot)

    sections = spec.get("sections", []) or []
    secs = []
    nav_tabs = []
    total = len(sections)
    for i, s in enumerate(sections, 1):
        sid = s.get("id") or "s%d" % i
        title = s.get("title", "")
        body_html = s.get("html", "")
        # 章节头 v3：渐变编号方块 + 副标题 + 折叠箭头
        hero = '<div class="chapter-hero" title="点击折叠/展开本节">'
        hero += '<span class="sec-no">%02d</span>' % i
        hero += '<div class="step-text"><h2>%s</h2>' % esc(title)
        sub = s.get("subtitle", "")
        if sub:
            hero += '<p class="step-sub">%s</p>' % esc(sub)
        hero += '</div><span class="sec-fold">▾</span></div>'
        # v3 二次目录：收集章节内 h3 锚点生成小节导航
        subs = re.findall(r'<h3 id="([^"]+)"[^>]*>(.*?)</h3>', body_html)
        stoc = ""
        if len(subs) >= 2:
            links = "".join('<a href="#%s">%s</a>' % (h_id, re.sub(r"<[^>]+>", "", h_t))
                            for h_id, h_t in subs)
            stoc = '<div class="sub-toc"><span class="st-label">本节要点</span>%s</div>' % links
        secs.append('<section id="%s" class="reveal">%s%s<div class="chapter-body">%s</div></section>' % (
            esc(sid), hero, stoc, body_html))
        # 胶囊目录项
        nav_tabs.append(
            '<a class="chapter-tab" href="#%s" data-target="%s">'
            '<span class="tab-num">%02d</span><span>%s</span></a>' % (
                esc(sid), esc(sid), i, esc(title))
        )
    body = "\n".join(secs)
    # 胶囊目录栏（章节 ≥ 3 时启用，否则用旧 toc 链接块）
    if total >= 3:
        nav = "".join(nav_tabs)  # v3.0.1：胶囊 tab 直排入置顶栏 fixed-toc
    else:
        nav = ""

    toc = ""
    fixed_blocks = (1 if (spec.get("conclusion") or spec.get("items")) else 0) \
        + (1 if spec.get("sources") else 0) + (1 if spec.get("gaps") else 0)
    if len(secs) + fixed_blocks >= 4:
        toc = '<section id="toc"><h2>目录</h2><div class="toc">%s</div></section>' % "".join(
            '<a href="#%s">%s</a>' % (esc(s.get("id") or "s%d" % i), esc(s.get("title", "")))
            for i, s in enumerate(spec.get("sections", []) or [], 1))

    concl = ""
    if spec.get("conclusion") or spec.get("items"):
        lis = "".join("<li>%s</li>" % it for it in (spec.get("items") or []))
        concl = ('<section id="conclusion"><h2>结论与核心发现</h2><div class="concl"><p><b>一句话结论：</b>%s</p>'
                 '%s</div></section>') % (esc(spec.get("conclusion", "")),
                                          "<ul class=\"plain\">%s</ul>" % lis if lis else "")

    src = ""
    if spec.get("sources"):
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            _md_inline(s.get("label", "")), esc(s.get("level", "")), _md_inline(s.get("note", "")))
            for s in spec["sources"])
        src = ('<section id="sources"><h2>参考来源</h2><p class="sub">按来源级别标注：P0 政府与财报，'
               'P1 权威咨询，P2 主流财经媒体，P3 行业媒体，P4 社交媒体（仅作情绪参考）。</p>'
               '<table><thead><tr><th scope="col" style="width:52%">来源</th>'
               '<th scope="col" style="width:12%">级别</th><th scope="col">备注</th></tr></thead><tbody>') + rows + '</tbody></table></section>'

    gap = ""
    if spec.get("gaps"):
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(g.get("item", "")), esc(g.get("impact", "")), esc(g.get("channel", "")))
            for g in spec["gaps"])
        gap = ('<section id="gaps"><h2>信息缺口与风险</h2><table><thead><tr>'
               '<th scope="col" style="width:30%">缺口</th>'
               '<th scope="col" style="width:36%">不填补的影响</th>'
               '<th scope="col">建议补充渠道</th></tr></thead><tbody>') + rows + \
              '</tbody></table></section>'

    foot_bits = []
    if f.get("note"):
        foot_bits.append("数据来源：%s" % esc(f["note"]))
    if f.get("unit"):
        foot_bits.append("落款单位：%s" % esc(f["unit"]))
    if date:
        y, m, d = (date.split("-") + ["", "", ""])[:3]
        foot_bits.append("成文日期：%s年%s月%s日" % (y, m.lstrip("0"), d.lstrip("0")))
    if f.get("author"):
        foot_bits.append("制作者：%s" % esc(f["author"]))

    theme_list = [{"id": p["id"], "zh": p["zh"], "accent": p["accent"], "accent2": p["accent2"],
                   "bg": p.get("bg", "#fdfdfd")}
                  for p in PALETTES]

    html = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="__THEME__">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="__SUBTITLE__">
<meta name="theme-color" content="#fdf7f1" id="metaTheme">
<meta property="og:type" content="article">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__SUBTITLE__">
<meta property="og:locale" content="zh_CN">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23202734'/%3E%3Crect x='7' y='17' width='4' height='8' rx='1.2' fill='%2356c1c1'/%3E%3Crect x='14' y='12' width='4' height='13' rx='1.2' fill='%2356c1c1'/%3E%3Crect x='21' y='8' width='4' height='17' rx='1.2' fill='%23a8dadc'/%3E%3C/svg%3E">
<title>__TITLE__</title>
<style>
/*@THEMES@*/
/*@BASE@*/
</style>
</head>
<body class="__STYLE__">
<a class="skip-link" href="#content">跳至正文</a>
<div id="progress"></div>
<nav class="top-fixed" id="topFixed">
  <div class="tf-row1">
    <div class="fixed-toc" id="chapterNav">__NAV__</div>
    <button class="toc-btn" id="tocBtn" aria-expanded="false" aria-controls="tocDrawer" aria-label="打开章节目录">☰ 目录</button>
  </div>
  <div class="tf-row2"><span class="tf-label">主题色</span>
    <div class="palette" id="palette"><button class="palette-pill" id="palettePill" aria-expanded="false" aria-label="切换配色"><span class="pp-dot"></span><span class="theme-name" id="themeName"></span><span class="pp-caret">▾</span></button>
      <div class="palette-pop" id="palettePop"><span id="swatches" style="display:contents"></span></div>
    </div>
  </div>
</nav>
<div class="toc-drawer" id="tocDrawer" aria-hidden="true">
  <div class="toc-mask" data-close="1"></div>
  <div class="toc-panel" role="dialog" aria-label="章节目录">
    <div class="dp-head"><h3 class="dp-title">__TITLE__</h3><button class="dp-close" data-close="1" aria-label="关闭目录">✕</button></div>
    <p class="dp-kicker">章节目录</p>
    <div class="toc-list" id="tocList">__NAV__</div>
    <p class="dp-sub">配色主题</p>
    <div class="dp-sw" id="swatchesDrawer"></div>
  </div>
</div>
<div class="hero">
  <span class="hero-deco hero-deco-1"></span><span class="hero-deco hero-deco-2"></span><span class="hero-deco hero-deco-3"></span>
  <div class="inner">
  <div class="hero-grid">
  <div class="hero-col-l">
  __HERO_BADGE__
  <h1>__TITLE__</h1>
  <p class="lead">__SUBTITLE__</p>
  <p class="meta">交付对象：__AUDIENCE__　·　成文日期：__DATE__</p>
  __HERO_PILLS__
  </div>
  <div class="hero-col-r">__HERO_STATS__</div>
  </div>
</div>
  <svg class="hero-wave" viewBox="0 0 1440 46" preserveAspectRatio="none" aria-hidden="true"><path d="M0,46 L0,22 C240,4 480,0 720,10 C960,20 1200,40 1440,26 L1440,46 Z" fill="var(--bg)"></path></svg>
</div>
<div class="wrap __LAYOUT__" id="content">
__TOC__
__CONCL__
__BODY__
__SRC__
__GAP__
<footer>__FOOT__</footer>
</div>
<button id="toTop" aria-label="返回顶部">↑</button>
<script>
/*@JS@*/
</script>
</body>
</html>
"""
    rep = {
        "__THEME__": theme, "__TITLE__": esc(spec.get("title", "成果页")),
        "__SUBTITLE__": esc(spec.get("subtitle", "")), "__AUDIENCE__": esc(spec.get("audience", "")),
        "__DATE__": esc(date), "__TOC__": toc, "__CONCL__": concl, "__BODY__": body, "__NAV__": nav,
        "__SRC__": src, "__GAP__": gap, "__FOOT__": "　·　".join(foot_bits),
        "__HERO_BADGE__": ('<span class="hero-badge">%s</span>' % esc(spec.get("hero_badges", "")))
                          if spec.get("hero_badges") else "",
        "__HERO_STATS__": ('<div class="hero-stats">%s</div>' % "".join(
            '<div class="hero-stat"><b>%s</b><span>%s</span></div>' % (
                esc(st.get("v", st) if isinstance(st, dict) else st),
                esc(st.get("l", "") if isinstance(st, dict) else ""))
            for st in (spec.get("hero_stats") or []))) if (spec.get("hero_stats") or []) else "",
        "__HERO_PILLS__": ('<div class="hero-pills">%s</div>' % "".join(
            "<i>%s</i>" % esc(x) for x in spec.get("hero_pills") or []))
                          if spec.get("hero_pills") else "",
        "__LAYOUT__": layout_class, "__STYLE__": style_class,
        "/*@THEMES@*/": themes_css, "/*@BASE@*/": CSS_FIXED,
    }
    for k, v in rep.items():
        html = html.replace(k, v)
    js = JS_FIXED.replace("/*@THEME_LIST@*/[]", json.dumps(theme_list, ensure_ascii=False))
    js = js.replace("/*@DEFAULT_THEME@*/", theme)
    html = html.replace("/*@JS@*/", js)
    # ===== v2.0: KaTeX self-contained 注入（仅当 spec.get('math')=True 时）=====
    if spec.get("math"):
        katex_head = (
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" '
            'integrity="sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+" '
            'crossorigin="anonymous">'
            '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js" '
            'integrity="sha384-7zkQWkzN08G0l7B2C2lpoRO3K1z3+Qz3QzcDq3m8a4Gp9eFc6xC5p6HhMc6N8j+L" '
            'crossorigin="anonymous"></script>'
            '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" '
            'integrity="sha384-43gviWU0YVjaDtb/GhzOouOXtZMP/7XU4OcL8N3a9rA4Hk2b+P7Dj8UrPqfdJe" '
            'crossorigin="anonymous" '
            'onload="renderMathInElement(document.body,{delimiters:['
            "'{left:'$',right:'$',display:false}',"
            "'{left:'$$',right:'$$',display:true}'],"
            'throwOnError:false});"></script>'
        )
        # 注入到 </style> 后（即 head 结束之前）
        html = html.replace('</style>', '</style>\n' + katex_head, 1)
    return html


def main():
    ap = argparse.ArgumentParser(description="单文件 HTML 成果页构建器")
    ap.add_argument("--init", action="store_true", help="生成数据模板")
    ap.add_argument("--data", help="数据文件 JSON")
    ap.add_argument("--out", required=True, help="输出文件")
    ap.add_argument("--theme", help="默认配色 id（覆盖数据文件）")
    ap.add_argument("--motif", help="版式母题 editorial|blueprint|narrative|classic（默认 editorial）")
    ap.add_argument("--check", action="store_true", help="构建后跑结构自检")
    a = ap.parse_args()

    if a.init:
        open(a.out, "w", encoding="utf-8").write(json.dumps(SPEC_TMPL, ensure_ascii=False, indent=2))
        print("已生成数据模板：", a.out)
        print("可用配色：", ", ".join(BY_ID))
        return 0

    if not a.data:
        print("缺少 --data 参数（或用 --init 生成模板）", file=sys.stderr)
        return 2
    spec = json.load(open(a.data, encoding="utf-8"))
    if a.theme:
        spec["theme"] = a.theme
    if getattr(a, "motif", None):
        spec["motif"] = a.motif
    html = build_html(spec)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成：%s（%.1fKB，配色 %s）" % (a.out, os.path.getsize(a.out) / 1024, spec.get("theme", "ocean")))
    if a.check:
        r = subprocess.run([sys.executable, os.path.join(HERE, "html_check.py"), a.out, "--node"])
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
