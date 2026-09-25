#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""案情陈述疑点扫描器（王洋律师视频视角 · 连线研判辅助）

输入：一段当事人陈述文本（txt/md 文件或 stdin）
输出：疑点清单 + 追问序列（Markdown）

设计原则：
- 只做「疑点提示」，不做结论。命中的每一项都只是「值得再问一句」。
- 规则来自 references/question-scripts.md 的疑点信号清单，纯正则/关键词，无外部依赖。
- 不联网、不调用模型。

用法：
    python3 case_drill.py --file statement.md
    python3 case_drill.py --file statement.md --out drill.md
    cat statement.md | python3 case_drill.py
"""
import argparse
import re
import sys

RULES = [
    ("时间线冲突嫌疑", r"(几年|多久|那年|哪年|时候|以后|之前|当时).{0,12}(一样|同一年|也是|正好|恰好|重合)",
     "陈述中出现两段时间的高度重合表述，核对两段时间的起止点是否互相印证。"),
    ("免责型自述", r"(我傻|我不懂|我不清楚|我不知道|我没想到|我是被|被忽悠|被蒙|被逼)",
     "当事人主动强调「不知情」，可能为免责铺垫，追问：你当时具体知道什么、什么时候知道的。"),
    ("利他话术", r"(我都是为了|我是为他好|我是为大家|我没想过|我从来没想过)",
     "反复强调动机利他，追问：这件事里你得到了什么。"),
    ("过程缺失", r"(反正|总之|大概|好像|记不清|差不多)",
     "关键过程被模糊带过，要求从头复述一遍，不跳步。"),
    ("转指他人", r"(朋友的朋友|我朋友|听说|别人说|有人告诉)",
     "出现转指第三人，追问：这个人是谁，你是否亲自在场。"),
    ("情绪错配", r"(崩溃|想死|活不下去|天塌|受不了)",
     "情绪强度较高，先承接情绪再回到事实；同时核对情绪与利害是否匹配。"),
    ("诉求转移", r"(公不公平|凭什么|他们领导|舆论|曝光|去死)",
     "出现与解决路径无关的目标，先把诉求锚定到「你想要的结果是什么」。"),
    ("身份未定", r"(老板|对象|朋友|合伙人|大哥|领导)",
     "关系称谓模糊，先定性：你们是什么关系，持续多久，是否有书面约定。"),
]

STEPS = [
    ("第一步 · 锚定诉求", "「你这个情况我听明白了。那你现在的诉求是什么？你想得到什么结果？」"),
    ("第二步 · 定性", "「你跟他是什么关系？持续几年了？」／「现在是行政处罚，还是刑事？」"),
    ("第三步 · 时间线", "「他妻子哪年出国？你跟他多久了？」（找时间重合点）／「把这个过程从头讲一遍，别跳。」"),
    ("第四步 · 确认关键事实", "「……是吧？」（把推断变成当事人确认）"),
    ("第五步 · 分层动作", "立刻做／必须做／可以做（条件齐备后）／不能做（明确禁止）"),
]


def scan(text):
    hits = []
    for name, pattern, tip in RULES:
        found = re.findall(pattern, text)
        if found:
            uniq = []
            for f in found:
                s = f if isinstance(f, str) else "".join(f)
                if s and s not in uniq:
                    uniq.append(s)
            hits.append((name, uniq[:5], tip))
    return hits


def build_report(text, hits):
    lines = ["# 案情陈述疑点扫描报告", ""]
    lines.append("> 本报告只输出「值得再问一句」的疑点，不构成任何法律结论。")
    lines.append("")
    lines.append("## 一、文本概况")
    lines.append("")
    lines.append("- 字数：{}".format(len(text)))
    lines.append("- 命中疑点类别：{} / {}".format(len(hits), len(RULES)))
    lines.append("")
    lines.append("## 二、疑点清单")
    lines.append("")
    if not hits:
        lines.append("未命中预设疑点类别。仍按下方追问序列逐项过一遍。")
    else:
        lines.append("| 序号 | 疑点类别 | 触发片段 | 追问方向 |")
        lines.append("|------|----------|----------|----------|")
        for i, (name, frags, tip) in enumerate(hits, 1):
            lines.append("| {} | {} | {} | {} |".format(i, name, "、".join(frags), tip))
    lines.append("")
    lines.append("## 三、追问序列（照读）")
    lines.append("")
    for title, q in STEPS:
        lines.append("**{}**".format(title))
        lines.append("")
        lines.append("> {}".format(q))
        lines.append("")
    lines.append("## 四、输出前自检")
    lines.append("")
    lines.append("- 是否已标注「初步判断，不构成正式法律意见」。")
    lines.append("- 每一个「破绽」是否都能指回原文具体句子。")
    lines.append("- 是否给出置信度与反转条件。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="案情陈述疑点扫描器（连线研判辅助）")
    ap.add_argument("--file", help="陈述文本文件（txt/md）；不传则读 stdin")
    ap.add_argument("--out", help="输出 Markdown 路径；不传则打印到终端")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("[warn] 输入为空，请提供当事人陈述文本。", file=sys.stderr)
        return 1

    hits = scan(text)
    report = build_report(text, hits)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print("[ok] 已写出：{}（命中疑点 {} 类）".format(args.out, len(hits)))
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
