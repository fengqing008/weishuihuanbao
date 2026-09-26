#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""illustrate.py —— HTML 基座配图（v5.2.0，2026-09-24）

两条通道，**默认两条都不自动触发**：仅当用户明确要求配图（"配图/加图/插图/来几张图"）
时才执行；未明确要求时报告一律不配图，正文以文字化图表（:::chart / :::timeline 等）与
图形围栏（```mermaid）承担可视化。

  A. lineart（推荐，默认风格=手绘线稿）
     python3 illustrate.py lineart 成稿.md --max 3 --palette sepia
     本地线稿引擎（qf-lineart）按章节关键词选母题出图 → 确定性、风格统一、不出纯色、零成本。

  B. AI 文生图（image_gen，按需）
     plan → 出图 → apply 三段式：
     1) plan   扫描成稿 → 识别配图点 → 配图任务单（JSON + Markdown）
     2) 出图   按任务单逐张调 ima 文生图（image_gen），文件名用任务单给定值
     3) apply  像素校验 + 瘦身 + 回填 → *_illustrated.md，再交 md2report 渲染
     **AI 出图后必经 validate_image 像素校验**：低结构图（纯色/大片渐变，AI 出图失败的典型形态）
     一律拒绝落位并报错，杜绝"配图是一块纯色"。

设计约束：
  · plan / check 纯标准库；apply 瘦身与像素校验依赖 Pillow，缺失时降级为不校验/不压缩。
  · 幂等：同一份稿 plan 结果稳定；apply 重复执行不重复插图。
  · 不破坏单文件自包含：图片最终由 md2report 以 base64 内嵌。

用法：
  python3 illustrate.py lineart 成稿.md --max 3 --palette sepia --stroke pencil
  python3 illustrate.py plan  成稿.md --theme sunset --max 4 --style lineart
  python3 illustrate.py apply 成稿.md --plan illustration/plan.json
  python3 illustrate.py check 成稿_illustrated.md --plan illustration/plan.json
  python3 illustrate.py route 成稿.md
  python3 illustrate.py styles                     # 列出可选配图风格


v5.2.0 配图路由（文档类型 → 配图源）：
  调研/考察/规划/行业/项目类 → 互联网实景图（photo，真实照片，标注来源）
  散文/随笔/文章/品牌类       → ima 商业插画（ai，image_gen，默认 business-2.5d）
  技术/工艺/工程/系统类       → 本地线稿（lineart）或图形围栏（mermaid）
  数据/财务/台账类            → 文字化图表（:::chart，不配图）
  压缩已放宽（长边 ≤1920、q92、阈值 900KB），避免过度压缩损伤画质。

v5.3.0：建立「ima 生图类型库」（11 种视觉风格）与「成果文件类型路由」（17 类），
  按成果类型自动匹配配图源与生图风格；配图提示词注入文档主题色卡，
  使配图色调与全文主题色一致；线稿通道按主题色温就近映射配色。
"""
import argparse
import json
import os
import re
import sys

VERSION = "v5.3.1"

# ---------------------------------------------------------------- 语义与风格

# 命中即认为「有可视表达价值」的章节语义
ILLUS_KEYWORDS = [
    "工艺", "流程", "工序", "步骤", "环节", "时间线", "进度", "节点",
    "现场", "实景", "布置", "总平面", "布局", "平面", "鸟瞰", "管网", "系统",
    "结构", "构成", "分布", "对比", "示意", "场景", "规划", "方案", "选型",
    "设备", "装置", "构筑物", "池体", "车间", "园区", "路线", "地理",
]

# ima 生图类型库（v5.3.0）——11 种视觉风格，成果类型路由与提示词生成共用
# tone=True 表示该风格注入文档主题色卡（保证配图色调与全文主题一致）
VISION_STYLES = {
    "business-2.5d": {
        "cn": "2.5D 等距商业插画",
        "zh": "2.5D 等距视角商业插画，柔和渐变与轻微投影，画面干净通透，留白克制，细节清晰",
        "en": "isometric 2.5D business illustration, soft gradients, subtle drop shadow, "
              "clean airy composition, generous negative space, crisp detail",
        "use": "汇报总结、行业分析、方案说明", "tone": True,
    },
    "flat-vector": {
        "cn": "扁平矢量插画",
        "zh": "扁平矢量插画，几何色块与细描边，模块化分区，层次清楚，克制配色",
        "en": "flat vector illustration, geometric color blocks with thin strokes, "
              "modular sections, clear hierarchy, restrained palette",
        "use": "政务公文、政策解读、流程说明、科普", "tone": True,
    },
    "editorial": {
        "cn": "杂志编辑插画",
        "zh": "杂志编辑插画，观念化隐喻与克制配色，构图讲究，质感细腻，留白有呼吸感",
        "en": "editorial magazine illustration, conceptual metaphor, restrained palette, "
              "considered composition, fine texture, generous negative space",
        "use": "文章、散文、评论、杂谈", "tone": True,
    },
    "handdrawn-warm": {
        "cn": "暖调手绘水彩",
        "zh": "暖调手绘水彩插画，笔触松弛自然，纸感与晕染，色调温柔，情绪细腻",
        "en": "warm hand-drawn watercolor illustration, loose brushwork, paper texture and "
              "soft washes, gentle warm tones, delicate mood",
        "use": "生活、文化、游记、亲子、情感", "tone": True,
    },
    "tech-abstract": {
        "cn": "科技抽象",
        "zh": "科技抽象视觉，几何网格与光效线条，冷调渐变，未来感，秩序清晰",
        "en": "abstract tech visual, geometric grids and glowing thin lines, cool-toned "
              "gradients, futuristic, orderly and clean",
        "use": "技术前沿、AI、数字化、产品发布", "tone": True,
    },
    "infographic": {
        "cn": "信息图解",
        "zh": "信息图解插画，图标化元素与分区信息块，箭头与流程清楚，易读克制",
        "en": "infographic illustration, icon-based elements with partitioned info blocks, "
              "clear arrows and flow, readable and restrained",
        "use": "科普、教程、方法、知识卡片", "tone": True,
    },
    "ink-watercolor": {
        "cn": "水墨国风",
        "zh": "水墨国风插画，写意笔触与留白，淡彩晕染，意境含蓄，纸本质感",
        "en": "Chinese ink-wash illustration, expressive brushwork with negative space, "
              "soft light-color washes, subtle mood, rice-paper texture",
        "use": "传统文化、人文历史、国学、民俗", "tone": True,
    },
    "3d-render": {
        "cn": "3D 渲染拟物",
        "zh": "3D 渲染拟物视觉，材质与光影考究，柔和高光，景深自然，质感高级",
        "en": "3D rendered object visual, refined materials and lighting, soft highlights, "
              "natural depth of field, premium texture",
        "use": "品牌、营销、活动、产品、传播", "tone": True,
    },
    "photo": {
        "cn": "写实摄影",
        "zh": "写实摄影风格，自然光，真实质感，浅景深，杂志级构图",
        "en": "realistic photographic style, natural lighting, true-to-life texture, "
              "shallow depth of field, editorial composition",
        "use": "实景类兜底（一般走联网实景图）", "tone": False,
    },
    "lineart": {
        "cn": "手绘线稿",
        "zh": "手绘线稿插画，单色细线，暖白纸底，无填充或极简填充，克制",
        "en": "hand-drawn line art illustration, single-color fine lines, warm paper "
              "background, minimal fill, restrained style",
        "use": "技术工程、结构说明（另见 lineart 通道）", "tone": False,
    },
    "diagram": {
        "cn": "扁平信息示意",
        "zh": "扁平信息示意图，几何色块与细描边，模块化分区，箭头与层级清楚",
        "en": "flat informational diagram, geometric color blocks with thin strokes, "
              "modular sections, clear arrows and hierarchy",
        "use": "流程、层级、结构示意", "tone": True,
    },
}
STYLE_PRESETS = VISION_STYLES  # v5.3.0 起统一为 ima 生图类型库（兼容旧名）
VISION_LABEL = {k: v["cn"] for k, v in VISION_STYLES.items()}

# 章节语义命中 → 中文图注后缀
CAPTION_SUFFIX = {
    "流程": "流程示意", "工艺": "工艺示意", "步骤": "步骤示意", "工序": "工序示意",
    "现场": "现场场景", "实景": "实景示意", "布置": "布置示意", "总平面": "总平面示意",
    "布局": "布局示意", "平面": "平面示意", "时间线": "时间线示意", "进度": "进度示意",
    "对比": "对比示意", "构成": "构成示意", "分布": "分布示意", "系统": "系统构成",
    "设备": "设备示意", "管网": "管网示意", "规划": "规划示意", "场景": "场景示意",
    "结构": "结构示意", "方案": "方案示意",
}

# 结构性弱语义（标题命中即视为可视表达点，权重次之）
META_WORDS = [
    "概况", "背景", "总述", "总体", "总结", "结论", "综述", "目标", "任务",
    "成效", "亮点", "难点", "风险", "建议", "措施", "计划", "安排", "范围",
]

NEG_PROMPT_ZH = "画面中不出现任何文字、字母、数字、水印、logo、商标、边框"
NEG_PROMPT_EN = ("no text, no letters, no numbers, no watermark, no logo, "
                 "no trademark, no border, no frame")

SIZE_PRESETS = {"wide": (1536, 864), "inline": (1024, 768), "cover": (1536, 640)}


# ---------------------------------------------------------------- v5.3.0 成果类型路由

# 成果文件类型 → {配图源, ima 生图类型}（关键词投票，命中多者胜；平票按本表顺序）
# 字段：(doc_type, 中文标签, 关键词, source, vision_style, 理由)
DOC_ROUTES = [
    ("survey", "调研考察报告",
     ["调研", "考察", "踏勘", "走访", "实地", "现场", "普查", "问卷", "访谈", "摸底",
      "抽样", "一线"],
     "photo", None, "实景感强，优先联网检索真实实景图"),
    ("travel", "旅游规划",
     ["旅游", "行程", "攻略", "景区", "景点", "线路", "目的地", "自驾", "度假", "游玩",
      "一日游", "两日游", "打卡", "游线"],
     "photo", None, "目的地实景，联网检索真实实景图"),
    ("industry", "行业研究",
     ["行业", "产业", "市场", "赛道", "格局", "趋势", "竞争", "规模", "前景"],
     "photo", None, "行业一线场景，联网检索实景图"),
    ("region", "区域规划",
     ["规划", "布局", "城市", "区域", "乡村", "园区", "街区", "地理", "空间", "选址",
      "片区", "开发区"],
     "photo", None, "空间实景，联网检索实景图"),
    ("gov", "政务公文",
     ["政策", "政务", "通知", "请示", "批复", "解读", "条例", "办法", "规定", "文件",
      "纪要", "方案报批"],
     "ai", "flat-vector", "政务视觉，扁平矢量插画"),
    ("engineering", "工程方案",
     ["工艺", "工序", "流程", "系统", "结构", "规范", "技术", "设备", "管网", "选型",
      "调试", "运维", "图纸", "构筑物", "施工"],
     "lineart", None, "技术结构为主，本地线稿 / 图形围栏"),
    ("data", "数据报告",
     ["数据", "统计", "报表", "财务", "台账", "指标", "测算", "预算", "同比", "环比",
      "占比", "明细"],
     "chart", None, "数据为主，文字化图表（不配位图）"),
    ("essay", "散文随笔",
     ["散文", "随笔", "感悟", "心得", "杂谈", "心情", "夜话", "闲话", "记忆", "手记",
      "札记", "序言", "卷首语", "评论", "杂文", "观后感"],
     "ai", "editorial", "文章类，杂志编辑插画"),
    ("life", "生活文化",
     ["生活", "文化", "美食", "味道", "节气", "家乡", "年味", "回忆", "亲情", "烟火",
      "味道"],
     "ai", "handdrawn-warm", "生活叙事，暖调手绘水彩"),
    ("tripnote", "游记见闻",
     ["游记", "见闻", "行走", "路上", "山川", "旅途", "远方", "旅居"],
     "ai", "handdrawn-warm", "个人叙事，暖调手绘水彩"),
    ("science", "科普教程",
     ["科普", "教程", "指南", "入门", "原理", "怎么做", "方法", "步骤", "知识", "问答"],
     "ai", "infographic", "知识传递，信息图解"),
    ("techfront", "技术前沿",
     ["前沿", "人工智能", "算法", "数字化", "智能", "科技", "产品发布", "大模型", "自动化",
      "机器学习"],
     "ai", "tech-abstract", "科技议题，抽象科技风"),
    ("culture", "传统文化",
     ["传统", "国学", "历史", "人文", "诗词", "古籍", "儒家", "民俗", "水墨", "礼"],
     "ai", "ink-watercolor", "人文历史，水墨国风"),
    ("brand", "品牌营销",
     ["品牌", "营销", "推广", "活动", "策划", "传播", "文案", "种草", "海报", "口号",
      "引流"],
     "ai", "3d-render", "品牌传播，3D 渲染拟物"),
    ("report", "汇报总结",
     ["汇报", "总结", "述职", "季度", "年度", "工作", "成效", "完成情况"],
     "ai", "business-2.5d", "商务汇报，2.5D 等距插画"),
    ("family", "亲子教育",
     ["儿童", "孩子", "亲子", "小学", "绘本", "成长", "教育", "课堂", "小朋友", "家长"],
     "ai", "handdrawn-warm", "亲子教育，暖调手绘水彩"),
]

GOV_STRONG_MARKERS = [
    "请示", "批复", "此函", "来函", "复函", "特此报告", "特此函告", "特此函复",
    "请予批复", "贵局", "贵公司", "收悉", "主送", "抄送", "关于印发",
    "现将", "报告如下",
]

SOURCE_LABEL = {
    "photo": "互联网实景图（真实照片，标注来源）",
    "ai": "ima 商业插画（image_gen）",
    "lineart": "本地手绘线稿（qf-lineart）",
    "chart": "文字化图表（:::chart，不配图）",
}

PHOTO_REQUIREMENT = ("真实实景照片：自然光、真实质感、无 CGI/插画/渲染感；"
                     "来源可追溯（政府与官方媒体、景区官网、权威图库优先），图注须标注来源")


def _doc_text(md):
    txt = []
    for ln in md.split("\n"):
        h = HEAD_RE.match(ln)
        if h:
            txt.append(h.group(2))
    txt.append(md)
    return " ".join(txt)


def route_doc(md, override=None, style_override=None):
    """判定成果文件类型 → 配图源与 ima 生图类型。

    返回 {source, doc_type, doc_label, vision_style, reason, scores, forced}。
    """
    text = _doc_text(md)
    scores = {r[0]: sum(text.count(k) for k in r[2]) for r in DOC_ROUTES}
    gov_hits = sum(text.count(k) for k in GOV_STRONG_MARKERS)
    if gov_hits >= 2 and not (override and override != "auto"):
        doc_type, doc_label, src, style = "gov", "政务公文", "ai", "flat-vector"
        reason = "公文文种特征词命中 %d 处（文种优先于题材），扁平矢量插画" % gov_hits
    else:
        best = max(DOC_ROUTES, key=lambda r: scores[r[0]])
        doc_type, doc_label, _, src, style, reason = best
        if scores[doc_type] == 0:
            doc_type, doc_label, src, style = "survey", "调研考察报告（默认）", "photo", None
            reason = "无显著语义信号，默认实景图（报告类最常见）"
    forced = False
    if override and override != "auto":
        src, forced = override, True
        reason = "参数指定：" + SOURCE_LABEL.get(src, src)
        if src != "ai":
            style = None
    if style_override and style_override != "auto" and src == "ai":
        style = style_override
        reason += "；生图风格指定：" + VISION_LABEL.get(style, style)
    return {"source": src, "doc_type": doc_type, "doc_label": doc_label,
            "vision_style": style, "reason": reason, "scores": scores, "forced": forced}


def cmd_route(args):
    md = read_md(args.md)
    theme = getattr(args, "theme", None) or "sunset"
    r = route_doc(md, getattr(args, "source", None), getattr(args, "style", None))
    pal = load_palette(theme)
    print("[route] 成果类型：%s" % r["doc_label"])
    print("[route] 推荐配图源：%s" % SOURCE_LABEL.get(r["source"], r["source"]))
    if r["source"] == "ai":
        print("[route] ima 生图类型：%s（%s）"
              % (r["vision_style"], VISION_STYLES.get(r["vision_style"], {}).get("use", "")))
    print("[route] 配色：%s（主 %s / 辅 %s / 底 %s）"
          % (theme, pal.get("accent", "?"), pal.get("accent2", "?"), pal.get("bg", "?")))
    print("[route] 依据：%s" % r["reason"])
    print("[route] 关键词得分：%s" % r["scores"])
    if r["source"] == "chart":
        print("[route] 建议：用 :::chart / 表格承载数据，不配位图。")
    elif r["source"] == "lineart":
        print("[route] 建议：illustrate.py lineart \"%s\" --max 3 --palette %s --theme %s"
              % (args.md, lineart_palette_for(theme), theme))
    elif r["source"] == "photo":
        print("[route] 建议：illustrate.py plan \"%s\" --source photo --theme %s  （再联网检索实景图）"
              % (args.md, theme))
    else:
        print("[route] 建议：illustrate.py plan \"%s\" --source ai --style %s --theme %s"
              % (args.md, r["vision_style"] or "business-2.5d", theme))
    return 0


STAGE_WORDS = ("来源", "参考", "参考资料", "信息来源", "附录", "目录", "修订记录")
SEQ_STRIP_RE = re.compile(r"^[\s　]*(?:[一二三四五六七八九十百]+[、.．)）]|\d+[、.．)）]|[（(]\d+[）)])\s*")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
IMG_LINE_RE = re.compile(r"^!\[[^\]]*\]\([^)]+\)")
FENCE_LINE_RE = re.compile(r"^:::")


def strip_seq(s):
    return SEQ_STRIP_RE.sub("", (s or "").strip()).strip()


def read_md(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def md_topic(md, fallback=""):
    """取文首 frontmatter title 或首个一级标题作为报告主题。"""
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n", md, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if line.strip().lower().startswith("title:"):
                t = line.split(":", 1)[1].strip().strip("\"'")
                if t:
                    return t
    for line in md.split("\n"):
        h = HEAD_RE.match(line)
        if h and len(h.group(1)) == 1:
            return strip_seq(h.group(2))
    return fallback


def scan_sections(md):
    """返回 [(level, title, body_lines, has_visual)]，含首个标题前的正文（title 为空）。"""
    lines = md.split("\n")
    # 跳过 frontmatter
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1:]
                break
    secs = []
    cur = {"level": 0, "title": "", "body": []}
    for ln in lines:
        h = HEAD_RE.match(ln)
        if h:
            secs.append(cur)
            cur = {"level": len(h.group(1)), "title": h.group(2), "body": []}
        else:
            cur["body"].append(ln)
    secs.append(cur)
    out = []
    for s in secs:
        body = s["body"]
        has_visual = any(IMG_LINE_RE.match(x.strip()) or x.strip().startswith(":::chart")
                         or FENCE_LINE_RE.match(x.strip()) for x in body)
        chars = sum(len(x.strip()) for x in body if x.strip())
        out.append((s["level"], s["title"], body, has_visual, chars))
    return out


def hit_keywords(title, body_text):
    text = title + " " + body_text
    return [k for k in ILLUS_KEYWORDS if k in text]


def caption_for(title, hits):
    """图注：章节名 + 语义后缀；后缀词若已含于章节名则去重，避免叠字。"""
    base = strip_seq(title)
    for k in (hits or []):
        suf = CAPTION_SUFFIX.get(k)
        if not suf:
            continue
        if k in base:
            return "%s示意" % base
        return "%s%s" % (base, suf)
    return "%s示意" % base


def build_prompts(topic, caption, style_key, palette):
    """生成中英提示词。palette 为 dict（accent/accent2/bg）或空；仅 tone=True 风格注入色卡。"""
    st = VISION_STYLES.get(style_key, VISION_STYLES["business-2.5d"])
    pal = palette or {}
    tone = st.get("tone", True) and (pal.get("accent") or pal.get("bg"))
    if tone:
        c_main = pal.get("accent") or "低饱和商务色"
        c_sub = pal.get("accent2") or c_main
        c_bg = pal.get("bg") or "中性底色"
        zh_tone = ("色调：整体以 %s（主）、%s（辅）为基调，底色接近 %s，"
                   "低饱和、与文档主题色统一协调，避免与色卡冲突的高饱和杂色"
                   % (c_main, c_sub, c_bg))
        en_tone = ("color palette: primary %s, secondary %s, background %s; "
                   "low saturation, harmonious with the document theme, no clashing neon colors"
                   % (c_main, c_sub, c_bg))
    else:
        zh_tone = "色调：以内容真实性为先，自然色调"
        en_tone = "color: natural, true-to-life tones"
    zh = ("%s；主题：%s；画面内容：%s；%s；构图：主体突出、留白充足、层次清晰、光线柔和统一；%s"
          % (st["zh"], topic or "行业主题", caption, zh_tone, NEG_PROMPT_ZH))
    en = ("%s; subject: %s; scene: %s; %s; composition: clear focal subject, generous "
          "negative space, balanced layout, soft consistent lighting; %s"
          % (st["en"], topic or "industry topic", caption, en_tone, NEG_PROMPT_EN))
    return zh, en


def load_palette(theme):
    """取该主题色卡（accent/accent2/bg/hero1/hero2/mode/zh），失败返回空 dict。"""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        if here not in sys.path:
            sys.path.insert(0, here)
        from palettes import BY_ID  # noqa
        p = BY_ID.get(theme) or {}
        return {k: p.get(k, "") for k in
                ("accent", "accent2", "bg", "hero1", "hero2", "mode", "zh")}
    except Exception:
        return {}


def load_accent(theme):
    """兼容旧调用：取主题强调色。"""
    return (load_palette(theme) or {}).get("accent", "")


# 主题 → qf-lineart 线稿配色（按主题色温就近映射，保证线稿色调与全文一致）
THEME_TO_LINEART = {
    "ocean": "ink", "sunset": "terracotta", "forest": "olive", "minimal": "ink",
    "golden": "amber", "arctic": "ink", "desert": "rosewood", "tech": "ink",
    "botanical": "olive", "galaxy": "ink",
}


def lineart_palette_for(theme):
    return THEME_TO_LINEART.get(theme or "", "sepia")


# ------------------------------------------------- 配图点识别（plan/lineart 共用）

def pick_points(md, min_chars=160, max_n=4, relax=False):
    """识别配图点，返回 [{anchor, raw_title, hits, chars, score, caption, body_text}]（原文顺序）。"""
    secs = scan_sections(md)
    cand = []
    for idx, (level, title, body, has_visual, chars) in enumerate(secs):
        if level == 0 or not title:
            continue
        if any(w in title for w in STAGE_WORDS):
            continue
        if has_visual:
            continue
        if chars < 60:
            continue
        body_text = " ".join(x.strip() for x in body if x.strip())[:600]
        title_strong = [k for k in ILLUS_KEYWORDS if k in title]
        title_meta = [k for k in META_WORDS if k in title]
        body_hits = [k for k in ILLUS_KEYWORDS if k in body_text]
        if not (title_strong or title_meta or chars >= min_chars
                or (relax and chars >= 60)):
            continue
        score = (len(title_strong) * 4 + len(title_meta) * 2
                 + len(body_hits) + min(chars // 150, 4) + (1 if relax else 0))
        hits = title_strong or title_meta or body_hits
        cand.append({"anchor": strip_seq(title), "raw_title": title, "hits": hits,
                     "chars": chars, "score": score,
                     "caption": (caption_for(title, hits) if hits else strip_seq(title)),
                     "body_text": body_text})
    cand.sort(key=lambda x: (-x["score"], x["chars"]))
    picked = cand[:max(1, max_n)]
    order = {strip_seq(t): i for i, (_, t, _, _, _) in enumerate(secs)}
    picked.sort(key=lambda x: order.get(x["anchor"], 999))
    return picked


# ------------------------------------------------- 像素校验（防纯色/空白）

def validate_image(path, min_edge=5.0, min_uniq=140):
    """检测低结构图（纯色/大片渐变）——AI 出图失败的典型表现。返回 (ok, detail)。

    判据以「边缘均值」为主（画面结构密度），唯一色数作辅助参考。
    实测校准基准（240px 缩略 + FIND_EDGES 均值）：
      · AI 渐变块（低信息量，视觉即一片色）：边缘均值 ≈ 2.6，唯一色 80–94
      · 手绘线稿（白底+线条，方差低但结构清晰）：边缘均值 9.3–14.1，唯一色 108–181
      · 真实照片：边缘均值 18–25，唯一色 1700+
    故阈值取 5.0：可拦 AI 渐变块，不误伤线稿与照片。
    """
    try:
        from PIL import Image, ImageFilter
    except Exception:
        return True, "Pillow 缺失，跳过像素校验"
    try:
        im = Image.open(path).convert("RGB")
    except Exception as e:
        return False, "无法读取图片：%s" % e
    im.thumbnail((240, 240))
    px = list(im.getdata())
    step = max(1, len(px) // 3000)
    uniq = len(set(px[::step]))
    try:
        edges = list(im.convert("L").filter(ImageFilter.FIND_EDGES).getdata())
        edge_mean = sum(edges) / float(len(edges))
    except Exception:
        edge_mean = 999.0
    detail = "边缘均值 %.2f，唯一色 %d" % (edge_mean, uniq)
    if edge_mean < min_edge:
        return False, ("低结构图·疑似纯色/大片渐变（%s；阈值 边缘均值≥%.1f）"
                       % (detail, min_edge))
    return True, detail


# ------------------------------------------------- 本地线稿引擎（qf-lineart）

def load_lineart_engine():
    """三级探测 qf-lineart 线稿引擎（随包副本 → 技能目录 → 工作区软链）。"""
    import importlib
    root = os.path.dirname(os.path.abspath(__file__))
    for d in (os.path.join(root, "vendors", "qf-lineart", "scripts"),
              "/root/.skills/qf-lineart/scripts",
              "/sandbox/workspace/skills/qf-lineart/scripts"):
        if not os.path.exists(os.path.join(d, "lineart_engine.py")):
            continue
        if d not in sys.path:
            sys.path.insert(0, d)
        try:
            return importlib.import_module("lineart_engine")
        except Exception:
            continue
    return None


def pick_motif(engine, title, body_text, fallback="leaf"):
    """按母题关键词命中数选题（命中数相同取清单靠前者）。"""
    text = (title or "") + " " + (body_text or "")
    meta = getattr(engine, "MOTIF_META", {}) or {}
    best, best_n = fallback, 0
    for m in getattr(engine, "MOTIFS", []):
        kws = (meta.get(m) or {}).get("kw", [])
        n = sum(1 for k in kws if k in text)
        if n > best_n:
            best, best_n = m, n
    return best


def _cmd_styles(_a):
    print("ima 生图类型库（--style）：")
    for k, v in VISION_STYLES.items():
        print("  - %-16s %-12s %s%s" % (k, v["cn"], v["use"],
                                        "" if v["tone"] else "（不注入色卡）"))
    print("\n成果类型路由（自动匹配，--source/--style 可覆盖）：")
    for dt, label, _kw, src, style, _r in DOC_ROUTES:
        print("  - %-12s → %-8s %s" % (label, src, ("（%s）" % style) if style else ""))
    print("\n线稿主题映射（--theme → --palette）：")
    print("  " + "；".join("%s→%s" % (k, v) for k, v in THEME_TO_LINEART.items()))
    print("\n示例：illustrate.py route 成稿.md --theme sunset")
    print("      illustrate.py plan 成稿.md --source ai --style editorial --theme sunset")
    return 0


def cmd_lineart(args):
    """本地手绘线稿出图（推荐通道）：确定性渲染、整册风格统一、不会出纯色。"""
    E = load_lineart_engine()
    if E is None:
        print("[lineart][FAIL] 未找到 qf-lineart 引擎（lineart_engine.py）。"
              "请确认 /root/.skills/qf-lineart/scripts 可用。", file=sys.stderr)
        return 2
    md = read_md(args.md)
    base = os.path.dirname(os.path.abspath(args.md))
    idir = os.path.join(base, args.images_dir)
    os.makedirs(idir, exist_ok=True)
    pal = args.palette if args.palette != "auto" else lineart_palette_for(args.theme)
    pts = pick_points(md, args.min_chars, args.max)
    if not pts:
        print("[lineart] 未识别到配图点（章节均已有图，或篇幅与语义不足）")
        return 0
    try:
        W, H = (int(x) for x in args.size.lower().split("x"))
    except Exception:
        W, H = 1500, 820
    made = []
    for k, p in enumerate(pts, 1):
        motif = pick_motif(E, p["raw_title"], p.get("body_text", ""))
        fn = "%s/%s_%02d.png" % (args.images_dir, args.prefix, k)
        fp = os.path.join(base, fn)
        try:
            im = E.render(motif, size=(W, H), style=args.stroke, palette=pal,
                          seed=args.seed + k, paper=True, shade=not args.no_shade)
            im.save(fp)
        except Exception as e:
            print("[lineart][warn] #%d 渲染失败（母题 %s）：%s" % (k, motif, e))
            continue
        ok, detail = validate_image(fp)
        made.append({"id": k, "anchor": p["anchor"], "caption": p["caption"],
                     "motif": motif, "filename": fn, "valid": ok, "detail": detail})
        print("[lineart] #%d %s → %s（母题 %s，%s）%s"
              % (k, p["caption"], fn, motif, detail, "" if ok else "  校验未过，不落位"))
    out_md = md
    placed = 0
    for m in made:
        if not m["valid"]:
            continue
        out_md, st = insert_after_heading(
            out_md, m["anchor"], "![%s](%s){wide}" % (m["caption"], m["filename"]))
        if st == "ok":
            placed += 1
    stem = os.path.splitext(os.path.basename(args.md))[0]
    out = args.out or os.path.join(base, stem + "_lineart.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(out_md)
    print("[lineart] 出图 %d 张（落位 %d 张，线稿配色 %s）→ %s" % (len(made), placed, pal, idir))
    print("[lineart] 回填稿 → %s" % out)
    print("[下一步] python3 md2report.py \"%s\" -o \"%s\" --theme %s --check --max-kb 1200"
          % (out, os.path.join(base, stem + "_成果页.html"), args.theme or "sunset"))
    return 0


# ---------------------------------------------------------------- plan

def cmd_plan(args):
    md = read_md(args.md)
    IDIR = getattr(args, "images_dir", "images") or "images"
    topic = args.topic or md_topic(md, os.path.splitext(os.path.basename(args.md))[0])
    theme = args.theme or "sunset"
    palette = load_palette(theme)
    route = route_doc(md, getattr(args, "source", "auto"), getattr(args, "style", "auto"))
    source = route["source"]
    style = route["vision_style"] or "business-2.5d"
    if getattr(args, "style", "auto") != "auto":
        style = args.style
    if source == "lineart":
        print("[plan] 路由判定：%s" % SOURCE_LABEL["lineart"])
        print("[plan] ⚠️ 默认应走 image_gen：建议改用 --source ai 出图（illustrate.py plan --source ai ...）")
        print("[plan] lineart 通道仅作离线兜底；如确需可用：illustrate.py lineart \"%s\" --max %d --palette %s --theme %s"
              % (args.md, args.max, lineart_palette_for(theme), theme))
        return 0
    if source == "chart":
        print("[plan] 路由判定：%s（不作配图）" % SOURCE_LABEL["chart"])
        return 0
    if source == "ai":
        picked = pick_points(md, min(args.min_chars, 60), args.max, relax=True)
    else:
        picked = pick_points(md, args.min_chars, args.max)

    items = []
    n = 0
    if source == "photo":
        for c in picked:
            n += 1
            w, h = SIZE_PRESETS["wide"]
            items.append({"id": n, "anchor": c["anchor"], "position": "after_heading",
                          "mode": "wide", "caption": c["caption"], "width": w, "height": h,
                          "filename": "%s/photo_%02d.jpg" % (IDIR, n),
                          "search_query": "%s %s" % (topic, c["caption"]),
                          "requirement": PHOTO_REQUIREMENT,
                          "rationale": "章节含「%s」，正文 %d 字且无图" % ("、".join(c["hits"]) or "场景", c["chars"]),
                          "priority": c["score"]})
    else:
        if args.cover:
            n += 1
            w, h = SIZE_PRESETS["cover"]
            czh, cen = build_prompts(topic, "%s 封面视觉" % topic, style, palette)
            items.append({"id": n, "anchor": "__cover__", "position": "cover", "mode": "wide",
                          "caption": "%s 视觉封面" % topic, "prompt_zh": czh, "prompt_en": cen,
                          "width": w, "height": h, "filename": "%s/ai_%02d.jpg" % (IDIR, n),
                          "rationale": "封面首屏视觉", "priority": 10})
        for c in picked:
            n += 1
            w, h = SIZE_PRESETS["wide"]
            pzh, pen = build_prompts(topic, c["caption"], style, palette)
            items.append({"id": n, "anchor": c["anchor"], "position": "after_heading",
                          "mode": "wide", "caption": c["caption"],
                          "prompt_zh": pzh, "prompt_en": pen, "width": w, "height": h,
                          "filename": "%s/ai_%02d.jpg" % (IDIR, n),
                          "rationale": "章节含「%s」，正文 %d 字且无图" % ("、".join(c["hits"]) or "场景", c["chars"]),
                          "priority": c["score"]})
    plan = {"version": VERSION, "source_md": os.path.abspath(args.md), "topic": topic,
            "theme": theme, "palette": palette, "accent": (palette or {}).get("accent", ""),
            "vision_style": (style if source == "ai" else "photo"),
            "style": (style if source == "ai" else "photo"),
            "doc_type": route.get("doc_type"), "doc_label": route.get("doc_label"),
            "source": source, "route_reason": route["reason"],
            "max": args.max, "images_dir": args.images_dir,
            "prompt_note": "photo：按 search_query 检索实景图；ai：prompt_en 用于 image_gen",
            "items": items}

    outdir = args.out or os.path.join(os.path.dirname(os.path.abspath(args.md)), "illustration")
    os.makedirs(outdir, exist_ok=True)
    jpath = os.path.join(outdir, "plan.json")
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=2)
    mpath = os.path.join(outdir, "plan.md")
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write(_plan_md(plan, args.md))
    if source == "ai":
        print("[plan] ima 生图类型：%s（%s）"
              % (style, VISION_STYLES.get(style, {}).get("use", "")))
    print("[plan] 配色：%s（主 %s / 辅 %s）"
          % (theme, palette.get("accent", "-"), palette.get("accent2", "-")))
    print("[plan] 配图点 %d 处 → %s" % (len(items), jpath))
    print("[plan] 任务单（人读）→ %s" % mpath)
    print("[下一步] 按任务单逐张调用 ima 文生图 image_gen：")
    for it in items:
        print("   · #%d  %s  →  %s  (%dx%d)" % (it["id"], it["caption"], it["filename"],
                                                it["width"], it["height"]))
    print("[再下一步] python3 %s apply %s --plan %s" % (os.path.basename(__file__), args.md, jpath))
    return 0


def _plan_md(plan, md_path):
    src = plan.get("source", "ai")
    L = ["# 配图任务单（illustrate %s）" % plan["version"], "",
         "- 源稿：`%s`" % os.path.basename(md_path),
         "- 主题：%s" % plan["topic"],
         "- 成果类型：%s" % (plan.get("doc_label") or "-"),
         "- 配图源：%s" % SOURCE_LABEL.get(src, src),
         "- ima 生图类型：%s" % (VISION_LABEL.get(plan.get("vision_style"), "-") if src == "ai" else "—"),
         "- 配色：%s（主 %s / 辅 %s / 底 %s）" % (
             plan.get("theme", "-"), plan.get("accent", "-"),
             plan.get("accent2", "-"), plan.get("bg", "-")),
         "- 配图数：%d（上限 %d）" % (len(plan["items"]), plan["max"]),
         "- 图片目录：`%s`" % plan["images_dir"], ""]
    if src == "photo":
        L += ["## 出图方法（实景图检索）", "",
              "按下表 `search_query` 联网检索**真实实景照片**，下载原图后按 `文件名` 存到源稿同级的 `%s/` 目录；" % plan["images_dir"],
              "要求：%s" % PHOTO_REQUIREMENT, "",
              "```bash", "python3 illustrate.py apply <源稿.md> --plan <本目录>/plan.json", "```", ""]
    else:
        L += ["## 出图方法（ima 文生图）", "",
              "对下表逐张调用 ima 文生图（image_gen），`file_name` 用表中文件名（去扩展名亦可），",
              "图片保存到源稿同级的 `%s/` 目录；出图完成后执行：" % plan["images_dir"], "",
              "```bash", "python3 illustrate.py apply <源稿.md> --plan <本目录>/plan.json", "```", ""]
    for it in plan["items"]:
        L += ["### #%d %s" % (it["id"], it["caption"]), "",
              "- 落位：%s（锚点：%s）" % (it["position"], it["anchor"]),
              "- 文件名：`%s`" % it["filename"],
              "- 建议尺寸：%dx%d" % (it["width"], it["height"]),
              "- 入选理由：%s" % it["rationale"], ""]
        if src == "photo":
            L += ["**检索关键词**", "", "```", it.get("search_query", ""), "```", "",
                  "**检索要求**", "", "```", it.get("requirement", PHOTO_REQUIREMENT), "```", ""]
        else:
            L += ["**英文提示词（推荐）**", "", "```", it["prompt_en"], "```", "",
                  "**中文提示词**", "", "```", it["prompt_zh"], "```", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- apply

def compress_image(path, max_side=1920, quality=92, threshold_kb=900):
    """超过阈值的图：长边 ≤ max_side、JPEG q92；返回 (新路径, 是否压缩)。v5.2.0 已放宽（1920/q92/900KB），避免过度压缩损伤画质。"""
    if os.path.getsize(path) / 1024.0 <= threshold_kb:
        return path, False
    try:
        from PIL import Image
    except Exception:
        print("[apply][warn] 未安装 Pillow，跳过瘦身：%s" % os.path.basename(path))
        return path, False
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    scale = min(1.0, float(max_side) / max(w, h))
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    out = os.path.splitext(path)[0] + ".jpg"
    im.save(out, "JPEG", quality=quality, optimize=True)
    if out != path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
    return out, True


def insert_after_heading(md, anchor, img_line):
    """在标题匹配 anchor（去序号后相等）的标题行之后插入一行；返回 (新md, ok)。"""
    lines = md.split("\n")
    if img_line.strip() in md:
        return md, "exists"
    for i, ln in enumerate(lines):
        h = HEAD_RE.match(ln)
        if h and strip_seq(h.group(2)) == anchor:
            lines.insert(i + 1, "")
            lines.insert(i + 2, img_line)
            return "\n".join(lines), "ok"
    return md, "miss"


def cmd_apply(args):
    md = read_md(args.md)
    with open(args.plan, encoding="utf-8") as fh:
        plan = json.load(fh)
    base = os.path.dirname(os.path.abspath(args.md))
    idir = os.path.join(base, plan.get("images_dir", "images"))
    done, missing, skipped, invalid = [], [], [], []
    for it in plan["items"]:
        if it.get("position") == "cover":
            skipped.append((it["id"], "封面（由 hero 区承载，不插入正文）"))
            continue
        fp = os.path.join(base, it["filename"])
        if not os.path.exists(fp):
            missing.append((it["id"], it["filename"]))
            continue
        # v5.1.0：出图像素校验——疑似纯色/空白一律拒绝落位（防"配图是一块纯色"）
        if not args.allow_solid:
            _ok, _detail = validate_image(fp)
            if not _ok:
                invalid.append((it["id"], "%s：%s" % (it["filename"], _detail)))
                continue
        if not args.no_compress:
            fp, comp = compress_image(fp, max_side=getattr(args, "max_side", 1920),
                                      quality=getattr(args, "quality", 92),
                                      threshold_kb=getattr(args, "threshold_kb", 900))
            it["filename"] = os.path.relpath(fp, base).replace(os.sep, "/")
        _tag = "wide" if (args.no_ai_tag or plan.get("source") == "photo") else "wide,ai"
        line = "![%s](%s){%s}" % (it["caption"], it["filename"], _tag)
        md, status = insert_after_heading(md, it["anchor"], line)
        if status == "ok":
            done.append(it["id"])
        elif status == "exists":
            skipped.append((it["id"], "已存在，跳过"))
        else:
            missing.append((it["id"], "锚点未匹配：" + it["anchor"]))
    stem = os.path.splitext(os.path.basename(args.md))[0]
    out = args.out or os.path.join(base, stem + "_illustrated.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print("[apply] 插图 %d 张：%s" % (len(done), done))
    if skipped:
        print("[apply] 跳过 %d 项：%s" % (len(skipped), skipped))
    if invalid:
        print("[apply][FAIL] 像素校验未过 %d 项（已拒绝落位）：" % len(invalid))
        for _i, _d in invalid:
            print("   · #%d %s" % (_i, _d))
        print("         处置：重出该图，或改用本地线稿通道 illustrate.py lineart（不出纯色）；")
        print("         确认图片实为低对比正片时可用 --allow-solid 放行。")
    if missing:
        print("[apply][warn] 未完成 %d 项：%s" % (len(missing), missing))
        print("         请确认已按任务单出图到 %s/" % plan.get("images_dir", "images"))
    print("[apply] 输出 → %s" % out)
    print("[下一步] python3 md2report.py \"%s\" -o \"%s\" --theme %s --check"
          % (out, os.path.join(base, stem + "_成果页.html"), plan.get("theme", "sunset")))
    return 0 if not (missing or invalid) else 1


# ---------------------------------------------------------------- check

def cmd_check(args):
    md = read_md(args.md)
    plan = None
    if args.plan:
        with open(args.plan, encoding="utf-8") as fh:
            plan = json.load(fh)
    figs = re.findall(r"^!\[([^\]]*)\]\(([^)]+)\)", md, re.M)
    base = os.path.dirname(os.path.abspath(args.md))
    problems = []
    for cap, p in figs:
        if not cap.strip():
            problems.append("图注为空：%s" % p)
        if not (p.startswith("http") or p.startswith("data:")):
            _fp = os.path.join(base, p)
            if not os.path.exists(_fp):
                problems.append("图片文件缺失：%s" % p)
            else:
                _ok, _detail = validate_image(_fp)
                if not _ok:
                    problems.append("图片疑似纯色/空白：%s（%s）" % (p, _detail))
    if plan:
        for it in plan["items"]:
            if it.get("position") == "cover":
                continue
            if it["filename"] not in md and os.path.basename(it["filename"]) not in md:
                problems.append("任务单 #%d 未落位：%s" % (it["id"], it["filename"]))
    if problems:
        print("[check] FAIL %d 项：" % len(problems))
        for x in problems:
            print("   · " + x)
        return 1
    print("[check] PASS：%d 张配图齐备、图注非空、文件可达" % len(figs))
    return 0


def main():
    ap = argparse.ArgumentParser(description="HTML 基座智能配图（ima 文生图全自动链路）%s" % VERSION)
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("plan", help="识别配图点并输出任务单")
    p1.add_argument("md", help="Markdown 成稿")
    p1.add_argument("-o", "--out", help="任务单输出目录（默认 <md目录>/illustration）")
    p1.add_argument("--max", type=int, default=4, help="配图数量上限，默认 4")
    p1.add_argument("--theme", default=None, help="配色 id（影响提示词主色）")
    p1.add_argument("--style", default="auto", choices=["auto"] + list(VISION_STYLES),
                    help="AI 通道配图风格，默认 business-2.5d（商业插画）")
    p1.add_argument("--source", default="ai", choices=["auto", "photo", "ai", "lineart", "chart"],
                    help="配图源（默认 ai=严格走 ima image_gen；auto=按文档类型路由【含 lineart 兜底】；photo=实景；lineart=本地线稿兜底非 image_gen）")
    p1.add_argument("--min-chars", type=int, default=160,
                    help="无标题语义时的章节字数下限，默认 160")
    p1.add_argument("--images-dir", default="images", help="图片目录名，默认 images")
    p1.add_argument("--cover", action="store_true", help="额外生成 1 张封面视觉")
    p1.add_argument("--topic", default=None, help="报告主题（默认取 frontmatter title 或 H1）")
    p1.set_defaults(func=cmd_plan)

    p2 = sub.add_parser("apply", help="瘦身并回填图片到 Markdown")
    p2.add_argument("md", help="Markdown 成稿")
    p2.add_argument("--plan", required=True, help="plan.json 路径")
    p2.add_argument("-o", "--out", help="输出 md（默认 <stem>_illustrated.md）")
    p2.add_argument("--no-compress", action="store_true", help="跳过图片瘦身（保留原图）")
    p2.add_argument("--max-side", type=int, default=1920, help="瘦身时长边上限，默认 1920")
    p2.add_argument("--quality", type=int, default=92, help="JPEG 质量，默认 92（画质优先）")
    p2.add_argument("--threshold-kb", type=int, default=900, help="触发瘦身的体积阈值 KB，默认 900")
    p2.add_argument("--no-ai-tag", action="store_true",
                    help="不添加「AI 配图」角标（默认添加）")
    p2.add_argument("--allow-solid", action="store_true",
                    help="放行像素校验（默认拒绝疑似纯色/空白图落位）")
    p2.set_defaults(func=cmd_apply)

    p3 = sub.add_parser("check", help="校验配图完整性")
    p3.add_argument("md", help="待校验的 Markdown")
    p3.add_argument("--plan", help="plan.json（可选，用于核对落位）")
    p3.set_defaults(func=cmd_check)

    p4 = sub.add_parser("styles", help="列出 ima 生图类型库与成果类型路由表")
    p4.set_defaults(func=_cmd_styles)

    p5 = sub.add_parser("lineart", help="本地手绘线稿出图（推荐：确定性、风格统一、不出纯色）")
    p5.add_argument("md", help="Markdown 成稿")
    p5.add_argument("-o", "--out", help="输出 md（默认 <stem>_lineart.md）")
    p5.add_argument("--max", type=int, default=3, help="配图数量上限，默认 3")
    p5.add_argument("--theme", default=None, help="配色 id（仅用于下一步命令提示）")
    p5.add_argument("--palette", default="auto",
                    help="线稿配色 auto（随 --theme 映射）/sepia/ochre/amber/terracotta/rosewood/olive/ink")
    p5.add_argument("--stroke", default="pencil",
                    help="笔触 fountain/pencil/brush/marker/charcoal")
    p5.add_argument("--size", default="1500x820", help="尺寸 WxH（跨栏 1500x820 / 栏内 760x980）")
    p5.add_argument("--seed", type=int, default=2026)
    p5.add_argument("--prefix", default="lineart", help="文件名前缀，默认 lineart")
    p5.add_argument("--images-dir", default="images", help="图片目录名，默认 images")
    p5.add_argument("--min-chars", type=int, default=160)
    p5.add_argument("--no-shade", action="store_true", help="关闭体量排线")
    p5.set_defaults(func=cmd_lineart)

    p6 = sub.add_parser("route", help="判定成果类型并推荐配图源与 ima 生图类型")
    p6.add_argument("md", help="Markdown 成稿")
    p6.add_argument("--source", default=None, choices=["auto", "photo", "ai", "lineart", "chart"],
                    help="覆盖自动路由结果")
    p6.add_argument("--style", default="auto", choices=["auto"] + list(VISION_STYLES),
                    help="覆盖 ai 通道的 ima 生图类型")
    p6.add_argument("--theme", default=None, help="配色 id（用于色卡与线稿色映射）")
    p6.set_defaults(func=cmd_route)

    a = ap.parse_args()
    if not getattr(a, "cmd", None):
        ap.print_help()
        return 2
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
