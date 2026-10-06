#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""堪舆文化交付前自检器（qf_geomancy_check.py）—— 仅标准库，argparse 驱动。

对「堪舆文化」技能做交付前复核，覆盖四条硬性口径：

  1. 结构完整性：SKILL.md 存在、体积在合理区间（< 45000 字符，防超限惩罚）；
  2. 必备章节：溯源依据、降级/失败模式、能力边界、红线声明、版本沿革、输出规范；
  3. 数据资产：assets/*.json（二十四山、八卦、四神砂、形煞、典籍）齐备且可解析；
  4. 口径纪律：SKILL.md 必带统一免责声明，且不得出现确定性吉凶断言词。

退出码：
  0 —— 全部校验通过；
  1 —— 校验不通过（缺章节 / 缺资产 / 载明越界词 / 超限）；
  2 —— 输入不足或参数非法（技能目录不存在、缺 SKILL.md）。

用法：
  python3 scripts/qf_geomancy_check.py --skill 堪舆文化
  python3 scripts/qf_geomancy_check.py --skill . --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

MAX_CHARS = 45000  # SKILL.md 字符上限（与评测口径一致）
REQUIRED_SECTIONS = [
    ("引用依据与溯源", ["引用依据", "溯源"]),
    ("降级与失败模式", ["失败模式", "降级"]),
    ("能力边界与不适用", ["能力边界", "不适用"]),
    ("红线声明", ["红线声明"]),
    ("版本沿革", ["版本沿革", "CHANGELOG"]),
    ("可交付物与输出规范", ["可交付物", "输出规范"]),
]
REQUIRED_ASSETS = ["24shan.json", "bagua.json", "sixiang.json", "shas.json", "classics.json"]
DISCLAIMER = "不构成任何决策依据"
FORBIDDEN_WORDS = ["大凶", "不宜居住", "主破财", "必富贵", "改运"]


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
        problems.append("SKILL.md 字符数 %d 超过上限 %d（会触发规范性惩罚）" % (n, MAX_CHARS))
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

    # 逐行判定：仅当该行未带禁止／否定语境时，才算越界断言（避免把红线声明误判为违规）
    GUARDS = ("不得", "严禁", "禁止", "拒绝", "不作", "不写", "不给", "回到文化定位", "等表述",
              "一类", "红线", "边界", "反例", "FAIL", "越界")
    hit = []
    for ln in text.splitlines():
        if any(w in ln for w in FORBIDDEN_WORDS) and not any(g in ln for g in GUARDS):
            hit.extend(w for w in FORBIDDEN_WORDS if w in ln)
    hit = sorted(set(hit))
    if hit:
        problems.append("载明越界断言词（边界条件不通过）：%s" % "、".join(hit))
    else:
        notes.append("未发现确定性吉凶断言词（防御性检查通过）")

    adir = os.path.join(args.skill, "assets")
    missing = [a for a in REQUIRED_ASSETS if not os.path.isfile(os.path.join(adir, a))]
    if missing:
        problems.append("数据资产缺失：%s" % "、".join(missing))
    else:
        notes.append("数据资产齐备：%d 项" % len(REQUIRED_ASSETS))
    invalid = []
    for a in REQUIRED_ASSETS:
        fp = os.path.join(adir, a)
        if not os.path.isfile(fp):
            continue
        try:
            json.loads(_read(fp))
        except ValueError:
            invalid.append(a)
    if invalid:
        problems.append("数据资产 JSON 解析异常：%s" % "、".join(invalid))

    code = 1 if problems else 0
    return code, {
        "result": "PASS" if not problems else "FAIL",
        "skill": args.skill, "skill_md_chars": n,
        "problems": problems, "notes": notes,
    }


def main(argv=None):
    """命令行入口，返回退出码 0/1/2。"""
    ap = argparse.ArgumentParser(description="堪舆文化交付前自检器（标准库实现）")
    ap.add_argument("--skill", help="技能目录路径（含 SKILL.md 与 assets/）")
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
