#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qf-lineart · AI 生图通道（提示词引擎）

把文章内容转成 AI 文生图提示词，用于生成"具体场景手绘插画"。
提示词范式引进自公众号排版技能（illustration-guide.md）：
    简约手绘线条插画 + 米白纸张质感 + 具体场景 + 双色（主色/点缀）+ 大量留白 + 负面约束

与程序化引擎的分工：
    - 程序化引擎（lineart_cli.py）：出版默认，风格统一、可复现、离线；
    - AI 通道（本脚本）：需要更丰富的质感与场景时使用，产出提示词后交由可用后端出图。

用法：
    python3 prompt_builder.py --manifest book.json --out prompts.json [--per-article 2]
    python3 prompt_builder.py --text "竣工验收这半年" --out one.json
    python3 prompt_builder.py --list-prompts
"""
import argparse
import json
import sys
from pathlib import Path

import lineart_engine as E

# 负面约束（所有提示词末尾必附，否则易生成文字与标识）
NEGATIVE = "不得出现任何文字、字母、数字、logo、水印。"

# 画面描述库（一句话把母题说成可画的场景）
PROMPTS = {
    # —— 场景母题 ——
    "steps3": "三级递升的台阶，每级台阶上站着一个前行的人影，最上方有一支向上的箭头",
    "desk": "办公工位一角：显示器、键盘、摊开的笔记本、亮着的台灯与一杯茶",
    "meeting": "一张长桌，四把椅子围坐，角落有一块写着三条要点的白板，一人站着讲解",
    "interview": "一张桌子两侧各坐一个人，桌上有纸张，两人上方浮着一对对话气泡",
    "plant": "污水处理池的剖面：水面波纹、进水管道与阀门、池底冒起的气泡",
    "blueprint": "一张展开的工程图纸：圆形详图、文字标注、带箭头的尺寸线，旁边放着直尺与铅笔",
    "lab": "化验台：一个锥形瓶、架子上三支试管、一支滴管与一台小天平",
    "checklist": "一块夹板清单，四个复选框里前三个已打勾，旁边放着笔与一枚印章",
    "contract": "两份叠放的合同文书与竖排的文字线，旁边一支签字笔和一枚红色印章",
    "scales": "一台天平：立柱、横梁与两个托盘，一端放砝码一端放文书",
    "letter": "一只信封与 V 形封盖，右上角盖着圆形邮戳，下方是桌面与信纸线",
    "archive": "一个三层抽屉式档案柜，旁边立着三个带标签的档案盒",
    "health": "一条心电图折线、一只苹果、一副哑铃并排",
    "family": "屋檐之下，三个人影大手拉小手（大人与孩子），脚下一条地平线",
    "move": "一只行李箱立在左侧，右侧是三栋高低错落的城市楼群，一条地平线",
    "handover": "两个人相对而立，中间一件文书正在递出，上方一道弧线箭头表示方向",
    # —— 象征母题 ——
    "leaf": "一片带叶脉的叶子",
    "sprout": "地平线上破土的新芽，两片小叶与一个圆点",
    "mountain": "两座远山与一轮日轮，山脚一条地平线",
    "window": "田字窗棂与窗台",
    "lamp": "一盏垂下的灯，灯罩下有一圈柔光",
    "book": "一本摊开的书，书页上有文字线",
    "bird": "三只掠空的飞鸟，翅膀简练",
    "cloud": "三朵相接的云，底端一条横线",
    "moon": "一轮弯月与三点散星",
    "ripple": "一层层散开的水波",
    "boat": "一艘带帆的小舟与水面条线",
    "pattern": "同心圆纹样与放射短线",
    "tea": "一只茶杯与托碟，杯口冒着三缕热气",
    "bridge": "一座拱桥与桥下水面",
    "star": "一枚五角星与三点散星",
    "home": "一栋带烟囱的小屋，有一扇门与一扇田字窗",
}

TEMPLATE = "简约手绘线条插画，米白色纸张质感背景，{ratio}。{scene}。以{ink_cn}线条为主，{accent_cn}点缀，线条干净疏朗，大量留白。"

PALETTE_CN = {
    "sepia": ("暖褐", "浅赭"), "ochre": ("赭石", "暖金"), "amber": ("暖金", "浅赭"),
    "terracotta": ("陶土", "暖橙"), "rosewood": ("暖玫瑰木", "浅陶"), "olive": ("暖橄榄", "浅黄"),
    "ink": ("墨黑", "灰"),
}
RATIO = {"wide": "横版 16:9 构图，主体偏左，右侧大面积留白", "inline": "竖版 3:4 构图，主体居中，四周留白充分"}


def build_prompt(motif, role, palette="sepia"):
    scene = PROMPTS.get(motif) or E.MOTIF_META.get(motif, {}).get("desc", motif)
    ink_cn, accent_cn = PALETTE_CN.get(palette, ("暖褐", "浅赭"))
    return TEMPLATE.format(ratio=RATIO.get(role, RATIO["wide"]), scene=scene,
                           ink_cn=ink_cn, accent_cn=accent_cn)


def build_prompt_from_brief(entry, role, palette="sepia"):
    """任务单模式：按该文专属的画面指令渲染提示词。

    entry 形如 {"subject":..,"scene":..,"composition":..,"mood":..}；
    画面由人（或模型）读文后写就，本函数只做模板装配。
    """
    ink_cn, accent_cn = PALETTE_CN.get(palette, ("暖褐", "浅赭"))
    subject = (entry.get("subject") or "").strip().rstrip("。")
    scene = (entry.get("scene") or "").strip().rstrip("。")
    ratio = (entry.get("composition") or "").strip() or RATIO.get(role, RATIO["wide"])
    mood = (entry.get("mood") or "").strip()
    body = f"画面主体：{subject}。" if subject else ""
    body += scene
    tail = f"，画面气息{mood}" if mood else ""
    return TEMPLATE.format(ratio=ratio, scene=body + tail, ink_cn=ink_cn, accent_cn=accent_cn)


def load_art_brief(path):
    """读取插画任务单；兼容 {"briefs":[...]} 与裸列表两种形态。"""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return d.get("briefs", d) if isinstance(d, dict) else d


def main():
    ap = argparse.ArgumentParser(description="qf-lineart · AI 生图提示词引擎")
    ap.add_argument("--manifest", help="稿件清单 JSON")
    ap.add_argument("--text", help="直接给一段文本（单条）")
    ap.add_argument("--per-article", type=int, default=2)
    ap.add_argument("--palette", default="sepia")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("-o", "--out", help="输出 JSON")
    ap.add_argument("--brief", help="插画任务单 JSON（文意提取通道，优先于 motif 选题）")
    ap.add_argument("--list-prompts", action="store_true", help="列出全部画面描述")
    a = ap.parse_args()

    if a.list_prompts:
        for m in E.MOTIFS:
            print(f"{m:10s} {E.MOTIF_META[m]['cn']:6s} {PROMPTS.get(m,'')}")
        return 0

    items = []
    if a.brief:
        for b in load_art_brief(a.brief):
            for role in ("wide", "inline"):
                if not b.get(role):
                    continue
                palette = b.get("palette", a.palette)
                items.append({
                    "order": b.get("order"), "title": b.get("title"), "column": b.get("column"),
                    "subject": b[role].get("subject"), "role": role,
                    "style": b.get("style", "hand-drawn-line-art"), "palette": palette,
                    "anchor": b.get("anchor"),
                    "prompt": build_prompt_from_brief(b[role], role, palette),
                    "negative": NEGATIVE,
                    "out": f"ai/art{b.get('order')}{'' if role == 'wide' else 'b'}.png"})
    elif a.text:
        for i, motif in enumerate(E.pick_motifs(a.text, max(1, min(3, a.per_article)), seed=a.seed)):
            role = E.plan_roles(a.per_article)[i]
            items.append({"title": a.text, "motif": motif, "role": role,
                          "prompt": build_prompt(motif, role, a.palette), "negative": NEGATIVE})
    else:
        if not a.manifest:
            ap.error("需 --manifest 或 --text")
        mp = Path(a.manifest).resolve()
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        palette = manifest.get("illustration", {}).get("palette", a.palette)
        for idx, art in enumerate(manifest.get("articles", [])):
            bp = (mp.parent / art["body"]).resolve()
            text = art.get("title", "") + (bp.read_text(encoding="utf-8") if bp.exists() else "")
            motifs = E.pick_motifs(text, max(1, min(3, a.per_article)), seed=a.seed + idx)
            roles = E.plan_roles(len(motifs))
            for motif, role in zip(motifs, roles):
                items.append({"order": art.get("order"), "title": art.get("title"),
                              "column": art.get("column"), "motif": motif, "role": role,
                              "style": "hand-drawn-line-art", "palette": palette,
                              "prompt": build_prompt(motif, role, palette),
                              "negative": NEGATIVE,
                              "out": f"ai/art{art.get('order')}_{motif}.png"})

    if a.out:
        Path(a.out).write_text(json.dumps({"items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"OK 提示词 {len(items)} 条 -> {a.out}")
    else:
        for it in items[:3]:
            print(it.get("order", "-"), it["motif"], "|", it["prompt"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
