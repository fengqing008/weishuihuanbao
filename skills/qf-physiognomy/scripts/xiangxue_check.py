#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xiangxue_check.py — 相学文化 · 报告合规自检脚本（仅用标准库）

两套模式：
  1) physiognomy（默认，个人特征解读报告）：严格拦截禁止判断词与交易性暗示，
     核对引文出处、免责声明与识别误差声明。
  2) themes（议题史 / 知识全集报告）：议题史必然涉及「寿夭/禄命」等命题词，
     故对禁止判断词改为「登记提示」，重点转为拦截「对个人的判断痕迹」
     （人称、对读者断言），并要求含命题史声明与免责声明。

退出码约定：
  0 = 通过（无告警）
  1 = 告警（命中禁止项 / 缺声明 / 出现对个人作论痕迹）
  2 = 硬错误（文件不存在 / 读取异常 / 输入为空）

用法：
  python3 xiangxue_check.py --file 相学文化解读.html
  python3 xiangxue_check.py --file 知识全集.html --mode themes
  python3 xiangxue_check.py --text "……"
"""
import argparse
import os
import sys

BAN_WORDS = ["运势", "命运", "吉凶", "富贵", "克夫", "克妻", "旺夫", "注定", "必然"]
TRADE_WORDS = ["请符", "开光", "大师指导", "付费化解", "改运收费"]
NEED_SECTIONS = ["免责声明", "识别误差"]
# 仅在 themes 模式使用：对个人作论的痕迹（人称 / 指代具体人）
PERSON_WORDS = ["你", "您", "此人", "这个人", "该人", "对方此人", "本命", "你的命", "他的命"]
# themes 模式必须出现的命题史声明
THEME_DECLARATION = ["命题史", "文化史", "知识史"]
MODE_CHOICES = ("physiognomy", "themes")


def load(args):
    if args.file:
        if not os.path.isfile(args.file):
            return None, "文件不存在：%s" % args.file
        try:
            with open(args.file, encoding="utf-8", errors="ignore") as fh:
                return fh.read(), None
        except OSError as exc:
            return None, "文件读取异常：%s" % exc
    if args.text is not None:
        return args.text, None
    return "", None


def check_physiognomy(body, warns):
    for word in BAN_WORDS:
        if word in body:
            warns.append("命中禁止判断词「%s」，须改写为「古籍以……为论」" % word)
    for word in TRADE_WORDS:
        if word in body:
            warns.append("命中交易性暗示「%s」，须移除" % word)
    if "source" not in body and "出处" not in body and "《" not in body:
        warns.append("未见引文出处，无出处条目不得进入报告")
    for section in NEED_SECTIONS:
        if section not in body:
            warns.append("缺少「%s」声明" % section)


def check_themes(body, warns, infos):
    # 命题词：登记提示，不判失败（命题史必然出现）
    hit = [w for w in BAN_WORDS if w in body]
    if hit:
        infos.append("议题模式·命题词出现（须确保均在命题标题或古籍引述语境）：%s" % "、".join(hit))
    # 交易性暗示：仍硬拦
    for word in TRADE_WORDS:
        if word in body:
            warns.append("命中交易性暗示「%s」，须移除" % word)
    # 对个人作论痕迹：硬拦
    for word in PERSON_WORDS:
        if word in body:
            warns.append("命中对个人作论的痕迹「%s」，议题/知识报告须保持第三人称，不得指向具体个人" % word)
    # 命题史声明
    if not any(k in body for k in THEME_DECLARATION):
        warns.append("缺少命题史声明（须含「命题史 / 文化史 / 知识史」字样，声明本报告为文化史陈述）")
    # 免责声明
    if "免责声明" not in body:
        warns.append("缺少「免责声明」")
    # 出处
    if "source" not in body and "出处" not in body and "《" not in body:
        warns.append("未见引文出处，无出处条目不得进入报告")


def main(argv=None):
    parser = argparse.ArgumentParser(description="相学文化报告合规自检（标准库实现）")
    parser.add_argument("--file", help="待检报告路径（HTML / 文本）")
    parser.add_argument("--text", help="直接传入待检文本")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="physiognomy",
                        help="physiognomy=个人特征解读（默认，严格）；themes=议题史/知识全集")
    parser.add_argument("--strict", action="store_true", help="严格模式：出现任一告警即返回 1")
    args = parser.parse_args(argv)

    text, err = load(args)
    if err:
        print("[硬错误] " + err)
        return 2
    if text is None or not text.strip():
        print("[硬错误] 输入为空或未提供 --file / --text")
        return 2

    body = text
    warns = []
    infos = []

    if args.mode == "themes":
        check_themes(body, warns, infos)
    else:
        check_physiognomy(body, warns)

    for item in infos:
        print("[提示] " + item)
    if warns:
        for item in warns:
            print("[告警] " + item)
        return 1

    print("[通过] 报告合规自检无告警（模式：%s）" % args.mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
