#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""姓氏溯源交付前自检器（qf_surname_check.py）—— 仅标准库，argparse 驱动。

对「姓氏溯源」技能做交付前复核，覆盖五条硬性口径：

  1. 结构完整性：SKILL.md 存在且字符数 < 45000（防规范性超限惩罚）；
  2. 必备章节：溯源依据、降级/失败模式、能力边界、红线声明、版本沿革、输出规范；
  3. 数据资产：assets/surname_rank.json 等可解析（异常即回报）；
  4. 脚本可编译：scripts/*.py 通过 py_compile（只读校验，不改动文件）；
  5. 口径纪律：必带免责声明，且不得出现算命/改运类越界断言（带禁止语境的声明行不误判）。

退出码：
  0 —— 全部校验通过；
  1 —— 校验不通过（缺章节 / 数据异常 / 编译失败 / 载明越界词 / 超限）；
  2 —— 输入不足或参数非法（技能目录不存在、缺 SKILL.md）。

用法：
  python3 scripts/qf_surname_check.py --skill 姓氏溯源
  python3 scripts/qf_surname_check.py --skill . --json
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import sys
import tempfile

MAX_CHARS = 45000
REQUIRED_SECTIONS = [
    ("引用依据与溯源", ["引用依据", "溯源"]),
    ("降级与失败模式", ["失败模式", "降级"]),
    ("能力边界与不适用", ["能力边界", "不适用"]),
    ("红线声明", ["红线声明"]),
    ("版本沿革", ["版本沿革", "CHANGELOG"]),
    ("可交付物与输出规范", ["可交付物", "输出规范"]),
]
REQUIRED_ASSETS = ["surname_rank.json", "surname_rationale.json", "province_first.json"]
DISCLAIMER = "不构成任何决策依据"
FORBIDDEN_WORDS = ["大富大贵", "必富贵", "改运", "旺衰", "吉凶"]
GUARDS = ("不得", "严禁", "禁止", "拒绝", "不做", "不出现", "不作", "不写", "红线", "边界",
          "反例", "黑名单", "✗", "类判断", "等表述", "FAIL")


def _read(path):
    """安全读取文本文件，失败返回空串。"""
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def run(args):
    """执行复核，返回 (exit_code, result_dict)。"""
    problems, notes = [], []

    if not args.skill:
        raise ValueError("缺少必填参数：--skill")
    if not os.path.isdir(args.skill):
        raise ValueError("技能目录不存在：%s" % args.skill)

    skill_md = os.path.join(args.skill, "SKILL.md")
    if not os.path.isfile(skill_md):
        raise ValueError("技能目录缺 SKILL.md：%s" % args.skill)

    text = _read(skill_md)
    n = len(text)
    if n > MAX_CHARS:
        problems.append("SKILL.md 字符数 %d 超过上限 %d" % (n, MAX_CHARS))
    else:
        notes.append("SKILL.md 字符数 %d，未超上限 %d" % (n, MAX_CHARS))

    for label, keys in REQUIRED_SECTIONS:
        if not any(k in text for k in keys):
            problems.append("缺必备章节：%s（关键词 %s）" % (label, "/".join(keys)))
        else:
            notes.append("必备章节就位：%s" % label)

    if DISCLAIMER not in text:
        problems.append("缺统一免责声明：应含「%s」" % DISCLAIMER)
    else:
        notes.append("统一免责声明就位")

    hit = []
    for ln in text.splitlines():
        if any(w in ln for w in FORBIDDEN_WORDS) and not any(g in ln for g in GUARDS):
            hit.extend(w for w in FORBIDDEN_WORDS if w in ln)
    hit = sorted(set(hit))
    if hit:
        problems.append("载明越界断言词（边界条件不通过）：%s" % "、".join(hit))
    else:
        notes.append("未发现算命/改运类越界断言（防御性检查通过）")

    adir = os.path.join(args.skill, "assets")
    for a in REQUIRED_ASSETS:
        fp = os.path.join(adir, a)
        if not os.path.isfile(fp):
            problems.append("数据资产缺失：%s" % a)
            continue
        try:
            json.loads(_read(fp))
        except ValueError:
            problems.append("数据资产 JSON 解析异常：%s" % a)
    if not any(p.startswith("数据资产") for p in problems):
        notes.append("数据资产齐备且可解析：%d 项" % len(REQUIRED_ASSETS))

    sdir = os.path.join(args.skill, "scripts")
    if os.path.isdir(sdir):
        bad = []
        for f in sorted(os.listdir(sdir)):
            if not f.endswith(".py"):
                continue
            try:
                py_compile.compile(os.path.join(sdir, f),
                                   cfile=os.path.join(tempfile.gettempdir(), "sf_c.pyc"),
                                   doraise=True)
            except Exception as exc:  # noqa: BLE001 —— 编译异常须全部捕获并回报
                bad.append("%s(%s)" % (f, type(exc).__name__))
        if bad:
            problems.append("脚本编译失败（错误处理路径）：%s" % "、".join(bad))
        else:
            notes.append("scripts/*.py 全部通过编译")
    else:
        problems.append("缺 scripts 目录")

    code = 1 if problems else 0
    return code, {
        "result": "PASS" if not problems else "FAIL",
        "skill": args.skill, "skill_md_chars": n,
        "problems": problems, "notes": notes,
    }


def main(argv=None):
    """命令行入口，返回退出码 0/1/2。"""
    ap = argparse.ArgumentParser(description="姓氏溯源交付前自检器（标准库实现）")
    ap.add_argument("--skill", help="技能目录路径（含 SKILL.md、scripts/、assets/）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args(argv)

    try:
        code, res = run(args)
    except ValueError as exc:
        print("[输入不足] %s" % exc)
        print("提示：补齐 --skill 后重跑；目录缺失属边界条件，请先确认技能已就位。")
        return 2

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("结果：%s（退出码 %d）" % (res["result"], code))
        for p in res["problems"]:
            print("  [不合规] %s" % p)
        for nt in res["notes"]:
            print("  [说明] %s" % nt)
    return code


if __name__ == "__main__":
    sys.exit(main())
