#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rembg_check.py — 抠图成品对账与 alpha 通道自检（纯标准库，退出码 0/1/2）

抠图交付前跑一遍，确认：①输出数量与输入对得上（批量不漏张）；
②每个 PNG 都带 alpha 通道（不是被导出成 jpg 丢了透明底）。

用法:
  python3 scripts/rembg_check.py --out ./nobg/
  python3 scripts/rembg_check.py --in ./photos/ --out ./nobg/ --ext png
  python3 scripts/rembg_check.py --out ./nobg/ --json

退出码:
  0  全部通过
  1  校验不通过（数量不符 / 有输出缺 alpha）
  2  输入不足或目录不可读

设计原则：只需标准库即可运行；输入非法时显式报错并非零退出，绝不静默降级。
"""
from __future__ import annotations
import argparse
import json
import os
import sys

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def png_color_type(path):
    """读取 PNG IHDR 的 color type；色型 4/6 含 alpha，其余不含。
    返回 True/False（是否含 alpha），None 表示非 PNG 或不可解析。"""
    try:
        with open(path, "rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
            f.read(4)              # 第一个 chunk 长度
            if f.read(4) != b"IHDR":
                return None
            data = f.read(13)
            if len(data) < 10:
                return None
            return data[9] in (4, 6)
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="rembg 抠图成品自检")
    ap.add_argument("--out", required=True, help="输出目录（含 *_nobg.png 等抠图结果）")
    ap.add_argument("--in", dest="indir", help="输入目录（可选，用于数量对账）")
    ap.add_argument("--ext", default="png", help="输出扩展名（默认 png）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结论")
    a = ap.parse_args(argv)

    if not a.out or not os.path.isdir(a.out):
        _emit(a.json, 2, ["输入不足：输出目录不存在或未指定：%s" % a.out])
        return 2

    ext = "." + a.ext.lower().lstrip(".")
    outs = sorted(f for f in os.listdir(a.out) if f.lower().endswith(ext))
    problems = []
    if not outs:
        problems.append("输出目录无 %s 文件" % ext)

    no_alpha = []
    for f in outs:
        if ext != ".png":
            continue
        r = png_color_type(os.path.join(a.out, f))
        if r is False:
            no_alpha.append(f)
        elif r is None:
            no_alpha.append(f + "（非 PNG / 不可解析）")
    if no_alpha:
        problems.append("缺 alpha 通道或异常：%s" % "，".join(no_alpha[:10]))

    if a.indir:
        if not os.path.isdir(a.indir):
            _emit(a.json, 2, ["输入不足：输入目录不存在：%s" % a.indir])
            return 2
        ins = [f for f in os.listdir(a.indir)
               if os.path.splitext(f)[1].lower() in IMG_EXT]
        if len(outs) < len(ins):
            problems.append("输出数量 %d 少于输入图片 %d（批量可能漏张）"
                            % (len(outs), len(ins)))

    if problems:
        _emit(a.json, 1, problems)
        return 1
    _emit(a.json, 0, ["通过：输出 %d 张，alpha 通道齐全%s"
                      % (len(outs), "，数量对账一致" if a.indir else "")])
    return 0


def _emit(as_json, code, messages):
    if as_json:
        print(json.dumps({"exit_code": code, "messages": messages}, ensure_ascii=False))
    else:
        for m in messages:
            print("[%d] %s" % (code, m))


if __name__ == "__main__":
    sys.exit(main())
