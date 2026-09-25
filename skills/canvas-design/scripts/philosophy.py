#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
canvas-design 设计哲学生成器（scripts/philosophy.py）

按主题与情绪词生成一份 4—6 段的设计哲学 markdown 底稿，并命名一个 1—2 词的艺术运动。
纯文本模板合成，不调用任何外部接口，同 seed 输出一致。

示例
----
python3 scripts/philosophy.py --theme "城市夜雨" --mood "克制" -o philosophy.md
python3 scripts/philosophy.py --theme "工业遗址" --segments 6 --lang zh
python3 scripts/philosophy.py --list-movements

依赖：仅 Python 3 标准库。
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sys

ADJECTIVES = [
    "Chromatic", "Brutalist", "Silent", "Luminous", "Tidal", "Mineral",
    "Organic", "Gridded", "Ashen", "Verdant", "Kinetic", "Static",
    "Basalt", "Hollow", "Radiant", "Latent", "Fallow", "Civic",
]

NOUNS = [
    "Silence", "Tide", "Reverie", "Monolith", "Field", "Interval",
    "Verdict", "Chorus", "Margin", "Signal", "Basin", "Vertex",
    "Threshold", "Residue", "Column", "Passage", "Ledger", "Aperture",
]

CN_ADJ = ["色度", "粗野", "静默", "流明", "潮汐", "矿质", "有机", "网格", "灰烬", "苍绿"]
CN_NOUN = ["静默", "潮汐", "冥想", "碑体", "原野", "间隙", "裁决", "复调", "余像", "微光"]

DEFAULT_THEME = "未命名主题"
DEFAULT_MOOD = "克制"


def seed_of(*parts) -> int:
    text = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def make_movement(theme: str, mood: str, lang: str, seed: int):
    rng = random.Random(seed)
    if lang == "en":
        word_count = 2 if rng.random() < 0.8 else 1
        if word_count == 1:
            return rng.choice(NOUNS)
        return "%s %s" % (rng.choice(ADJECTIVES), rng.choice(NOUNS))
    word_count = 2 if rng.random() < 0.8 else 1
    if word_count == 1:
        return rng.choice(CN_NOUN)
    return "%s%s" % (rng.choice(CN_ADJ), rng.choice(CN_NOUN))


def segment_claim(mv, theme, mood):
    return (
        "## 一 · 主张\n\n"
        "我们把「{mv}」定义为一种把冗余压到最低、再把力气集中在一处的手段。"
        "画面不承担解释任务，只承担举证责任：{theme}在这张纸上被还原为可度量的几何关系、"
        "可复核的色值与可复现的坐标。任何无法用一句话说明其作用的元素都撤走，"
        "留下来的每一笔都对整体节奏负责。情绪基调锚定在「{mood}」二字上，"
        "所有取舍以它为唯一裁判。\n"
    ).format(mv=mv, theme=theme, mood=mood)


def segment_color(mv, theme, mood):
    return (
        "## 二 · 色彩立场\n\n"
        "色板限定在四个席位之内：一支底色、一支图案色、一支强调色、一支辅助色。"
        "底色承担 70% 以上的面积，图案色以 8%—15% 的不透明度铺陈肌理，"
        "强调色只出现在一处几何主体上，面积不超过画面的 12%。"
        "强调色取色板中饱和度最高的一支，其余色相的饱和与明度向底色收拢，"
        "以此保证视线在零点几秒内落定到唯一的重心。"
        "文字色的选择服从对比度公式，正文不低于 4.5∶1，大标题不低于 3∶1。\n"
    )


def segment_form(mv, theme, mood):
    return (
        "## 三 · 形态语言\n\n"
        "形态只用三类母题：圆、方、三角，以及由此派生的环与弧。"
        "主体外接半径取画布短边的 0.17—0.20 倍，同心外环半径取 0.24—0.28 倍，"
        "以此形成「一大一细」的层级对位。重复图案的步长吸附到可整除画布的值，"
        "避免末行出现半格接缝。所有元素收在短边 6% 的安全边距之内，"
        "笔画不贴边、不裁切，留下呼吸的余地。\n"
    )


def segment_craft(mv, theme, mood):
    return (
        "## 四 · 材质与工艺\n\n"
        "画面以纸面质感为底，叠加不超过 3 级强度的细颗粒，"
        "让大面积纯色区域在近距离观察时仍保留物质感。"
        "笔画对齐同一条隐形网格，圆心、边缘、基线都落在整数像素上。"
        "导出执行 90/10 配比：图形承担九成信息量，"
        "文字总量控制在 25 个汉字或 40 个拉丁字符以内，"
        "由一处眉标、一行主标题、一行副题、一处角落微标记构成。\n"
    )


def segment_link(mv, theme, mood):
    return (
        "## 五 · 与主题的关联\n\n"
        "「{theme}」在本宣言中不作为插图对象出现，而作为结构关系出现。"
        "主题的节奏被换算成图案步长，主题的重量被换算成主体尺度，"
        "主题的温度被换算成强调色的色相角度。"
        "当画面刻意不描摹主题时，观者反而被推到关系层面去读它，"
        "这正是「{mv}」希望达成的效果。\n"
    ).format(theme=theme, mv=mv)


def segment_verify(mv, theme, mood):
    return (
        "## 六 · 检验与复现\n\n"
        "宣言落地后按七项检查点逐条核验：边界无溢出、无元素重叠、配色对比度达标、"
        "字体回退可用、图案节奏一致、文字量在上限内、记录 seed 可复现。"
        "任一项不过，回到精修环节删元素而不是加元素。"
        "同一 seed 与同一参数组重复运行，输出的画面在像素层面保持一致，"
        "使这张作品可以被批量延展为风格统一的系列。\n"
    )


SEGMENT_ORDER = ["claim", "color", "form", "craft", "link", "verify"]
SEGMENT_FUNCS = {
    "claim": segment_claim,
    "color": segment_color,
    "form": segment_form,
    "craft": segment_craft,
    "link": segment_link,
    "verify": segment_verify,
}


def build_markdown(theme, mood, mv, lang, segments, palette, size, pattern):
    body = []
    for key in SEGMENT_ORDER[:segments]:
        body.append(SEGMENT_FUNCS[key](mv, theme, mood))

    header = [
        "# 设计哲学 · %s" % mv,
        "",
        "- **艺术运动命名**：%s" % mv,
        "- **主题**：%s" % theme,
        "- **情绪基调**：%s" % mood,
        "- **段落数**：%d" % segments,
        "- **色板提案**：%s" % palette,
        "- **画幅提案**：%s" % size,
        "- **图案族提案**：%s" % pattern,
        "- **声明状态**：【待填：由设计者确认后定稿】",
        "",
        "> 本宣言为该视觉作品的唯一裁判文书。画面中每一个元素都须在本文件中找到出处。",
        "",
        "---",
        "",
    ]

    footer = [
        "---",
        "",
        "## 落地参数",
        "",
        "把上述立场交给画布引擎执行：",
        "",
        "```bash",
        "python3 scripts/canvas.py \\",
        '  --philosophy-phrase "%s" \\' % mv,
        '  --palette "%s" \\' % palette,
        '  --title "<主标题>" \\',
        '  --subtitle "<一行副题>" \\',
        '  --pattern %s \\' % pattern,
        '  --size %s \\' % size,
        "  -o out.png",
        "```",
        "",
        "## 版本记录",
        "",
        "| 版本 | 日期 | 改动 | 定稿人 |",
        "|---|---|---|---|",
        "| v0.1 | 【待填：日期】 | 模板生成底稿 | 【待填】 |",
        "",
    ]

    return "\n".join(header) + "\n".join(body) + "\n" + "\n".join(footer)


def build_parser():
    p = argparse.ArgumentParser(
        prog="philosophy.py",
        description="canvas-design 设计哲学生成器：按主题产出 4—6 段美学宣言并命名艺术运动。",
        epilog="示例：python3 scripts/philosophy.py --theme \"城市夜雨\" --mood \"克制\" -o philosophy.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--theme", default=DEFAULT_THEME, help="作品主题，中英文均可")
    p.add_argument("--mood", default=DEFAULT_MOOD, help="情绪基调，如 克制／汹涌／温润")
    p.add_argument("--movement", default=None, help="自定义艺术运动名，缺省时按 seed 合成")
    p.add_argument("--segments", type=int, default=5, choices=[4, 5, 6],
                   help="宣言段落数，4—6，默认 5")
    p.add_argument("--lang", default="zh", choices=["zh", "en"],
                   help="运动命名所用语言，默认 zh")
    p.add_argument("--palette", default="#0f172a,#1d283a,#e2b34a,#f8fafc",
                   help="写入宣言的色板提案，逗号分隔")
    p.add_argument("--size", default="post", help="写入宣言的画幅提案")
    p.add_argument("--pattern", default="grid", help="写入宣言的图案族提案")
    p.add_argument("--seed", type=int, default=None, help="随机种子，缺省由主题与情绪派生")
    p.add_argument("-o", "--out", default="philosophy.md", help="输出 markdown 路径")
    p.add_argument("--quiet", action="store_true", help="只输出结果路径")
    p.add_argument("--list-movements", action="store_true", help="打印可用的运动命名词库后退出")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_movements:
        print("形容词词库：%s" % ", ".join(ADJECTIVES))
        print("名词词库  ：%s" % ", ".join(NOUNS))
        print("中文词库  ：%s / %s" % ("、".join(CN_ADJ), "、".join(CN_NOUN)))
        return 0

    seed = args.seed if args.seed is not None else seed_of(args.theme, args.mood, args.segments)
    movement = args.movement or make_movement(args.theme, args.mood, args.lang, seed)

    md = build_markdown(
        theme=args.theme,
        mood=args.mood,
        mv=movement,
        lang=args.lang,
        segments=args.segments,
        palette=args.palette,
        size=args.size,
        pattern=args.pattern,
    )

    import os
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(md)

    if args.quiet:
        print(out_path)
    else:
        print("设计哲学已生成")
        print("  运动命名 : %s" % movement)
        print("  主题     : %s" % args.theme)
        print("  情绪     : %s" % args.mood)
        print("  段落数   : %d" % args.segments)
        print("  seed     : %d" % seed)
        print("  路径     : %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
