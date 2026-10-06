#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语音转写结果契约自检器（asr_check.py）——ali-asr 交付质检工具。

仅使用 Python 标准库（argparse / json / os / re / sys），不依赖第三方包、不联网。
用于在交付前对 transcribe.py 产出的结果 JSON 做结构自检，确保与上层链路
（meeting-minutes-pipeline / link-report-archiver）的契约一致，并检出时间轴异常。

检查项：
  1. JSON 可解析且为对象；
  2. 顶层含 text 字段（字符串）；
  3. 含 sentences[] 或 transcripts[].sentences[]（句中至少一项）；
  4. sentences[] 结构完整：text / begin_time / end_time（speaker_id 可选）；
  5. 时间轴单调性：begin_time <= end_time，且整体非递减（子序列允许重复）；
  6. 句数为 0 时给出「无有效语音」提示（非硬失败）；
  7. 顶层 text 与 sentences 拼接长度粗比对（截断告警）。

退出码：
  0 —— 全部检查通过（含仅告警）；
  1 —— 存在硬性检查不通过（字段缺失、时间轴逆序、JSON 不可解析等）；
  2 —— 输入不足或参数非法（未指定文件、文件不存在）。

用法：
  python3 asr_check.py --json 结果.json
  python3 asr_check.py --json 结果.json --json-out   # 同名冲突请用 --mode
"""
from __future__ import annotations

import argparse
import json
import os
import sys

SENT_KEYS = ("text", "begin_time", "end_time")


def load(path: str):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return json.load(f), None
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def collect_sentences(data: dict) -> list:
    sents = []
    if isinstance(data.get("sentences"), list):
        sents.extend(data["sentences"])
    for tr in data.get("transcripts", []) or []:
        if isinstance(tr, dict) and isinstance(tr.get("sentences"), list):
            sents.extend(tr["sentences"])
    return sents


def check(data) -> tuple[list, list, list]:
    passed, failed, notes = [], [], []

    if not isinstance(data, dict):
        failed.append(("顶层结构", "JSON 顶层不是对象"))
        return passed, failed, notes
    passed.append(("JSON 解析", "顶层为对象"))

    if isinstance(data.get("text"), str):
        passed.append(("text 字段", "存在且为字符串"))
    else:
        failed.append(("text 字段", "缺失或非字符串"))

    sents = collect_sentences(data)
    if not sents:
        notes.append(("句数", "sentences 为 0，判定音频无有效语音（非硬失败）"))
    else:
        passed.append(("句数", "%d 句" % len(sents)))

    bad_struct = 0
    for s in sents:
        if not isinstance(s, dict) or not all(k in s for k in SENT_KEYS):
            bad_struct += 1
    if bad_struct:
        failed.append(("句子结构", "%d 句缺 %s 字段" % (bad_struct, "/".join(SENT_KEYS))))
    elif sents:
        passed.append(("句子结构", "全部句子含 text/begin_time/end_time"))

    reversals = 0
    prev_end = None
    prev_begin = None
    for s in sents:
        if not isinstance(s, dict):
            continue
        b, e = s.get("begin_time"), s.get("end_time")
        try:
            b, e = int(b), int(e)
        except (TypeError, ValueError):
            continue
        if b > e:
            reversals += 1
        if prev_end is not None and b < prev_end:
            reversals += 1
        prev_end = e
        prev_begin = b
    if reversals:
        failed.append(("时间轴", "发现 %d 处逆序或重叠，需人工复核" % reversals))
    elif sents:
        passed.append(("时间轴", "begin<=end 且整体非递减"))

    if isinstance(data.get("text"), str) and sents:
        joined = "".join(str(s.get("text", "")) for s in sents if isinstance(s, dict))
        if data["text"] and len(joined) < len(data["text"]) * 0.5:
            notes.append(("截断告警", "sentences 拼接长度远小于 text，疑似截断"))
        else:
            passed.append(("一致性", "text 与 sentences 长度量级一致"))

    return passed, failed, notes


def main() -> int:
    ap = argparse.ArgumentParser(description="语音转写结果契约自检器（ali-asr）")
    ap.add_argument("--json", dest="json_path", default="", help="转写结果 JSON 路径")
    ap.add_argument("--mode", choices=["text", "report"], default="text", help="输出模式")
    args = ap.parse_args()

    if not args.json_path:
        print("ERROR: 未指定 --json 结果文件路径")
        return 2
    if not os.path.isfile(args.json_path):
        print("ERROR: 文件不存在: %s" % args.json_path)
        return 2

    data, err = load(args.json_path)
    if err:
        print("FAIL: JSON 解析失败 -> %s" % err)
        return 1

    passed, failed, notes = check(data)
    if args.mode == "report":
        print(json.dumps({"status": "PASS" if not failed else "FAIL",
                          "passed": passed, "failed": failed, "notes": notes},
                         ensure_ascii=False, indent=2))
    else:
        print("=== 转写结果契约自检 @ %s ===" % args.json_path)
        for k, v in passed:
            print("  [OK]   %s：%s" % (k, v))
        for k, v in notes:
            print("  [WARN] %s：%s" % (k, v))
        for k, v in failed:
            print("  [FAIL] %s：%s" % (k, v))
        print("结论：%s（通过 %d / 失败 %d / 提示 %d）"
              % ("PASS" if not failed else "FAIL", len(passed), len(failed), len(notes)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
