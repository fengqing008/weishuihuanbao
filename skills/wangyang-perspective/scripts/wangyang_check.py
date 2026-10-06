#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wangyang-perspective 研判成稿交付前自检脚本。

对一份「连线研判表」成稿做静态自检，确保四步法齐备、疑点未被写成结论、
结论带置信度、素材与身份边界被保留。

用法：
    python3 wangyang_check.py --file 研判.md
    python3 wangyang_check.py --file 研判.md --json

退出码约定：
    0  全部通过，可交付
    1  存在警告项（可交付但需人工复核）
    2  存在阻断项（不得交付，须先整改）

仅依赖 Python 标准库（argparse / re / json / sys），无第三方依赖。
"""
import argparse
import json
import re
import sys

FOUR_STEPS = {
    "诉求锚定": ["诉求锚定", "诉求是什么", "要什么结果"],
    "定性": ["定性", "案由方向"],
    "时间线": ["时间线", "时间轴"],
    "分层动作": ["分层动作", "当下", "下一步"],
}
CONCLUSION_WORDS = ["他一定在撒谎", "肯定在撒谎", "一定构成", "绝对构成", "必然是", "百分之百"]
BOUNDARY_KEYS = ["【待核", "不得照搬", "不构成法律意见", "剧本化"]


def check(text):
    blockers = []
    warnings = []
    for name, keys in FOUR_STEPS.items():
        if not any(k in text for k in keys):
            warnings.append("四步法缺项：%s" % name)
    for w in CONCLUSION_WORDS:
        if w in text:
            blockers.append("疑点被写成确定结论：%s" % w)
    if not any(k in text for k in ["判断：", "置信", "概率"]):
        warnings.append("结论未见置信度表述（判断：/置信/概率）")
    for k in BOUNDARY_KEYS:
        if k not in text:
            warnings.append("缺少素材/身份边界保留：%s" % k)
    if not re.search(r"《[^》]{2,40}》", text):
        warnings.append("未检出法规全称引用（《…》），法条须核验现行有效版本")
    return blockers, warnings


def main():
    ap = argparse.ArgumentParser(description="连线研判成稿交付前自检")
    ap.add_argument("--file", required=True, help="待检 Markdown/文本文件路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    a = ap.parse_args()
    try:
        with open(a.file, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError as e:
        print("读取失败：%s" % e, file=sys.stderr)
        sys.exit(2)
    blockers, warnings = check(text)
    if a.json:
        print(json.dumps({"file": a.file, "blockers": blockers,
                          "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        print("自检文件：%s" % a.file)
        for x in blockers:
            print("  [阻断] %s" % x)
        for x in warnings:
            print("  [警告] %s" % x)
        if not blockers and not warnings:
            print("  通过：未发现阻断或警告项。")
    if blockers:
        sys.exit(2)
    if warnings:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
