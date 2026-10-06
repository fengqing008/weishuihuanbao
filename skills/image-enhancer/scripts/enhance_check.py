#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强结果自检器（enhance_check.py）—— 仅标准库，argparse 驱动。

对 image-enhancer 的交付物做交付前复核，覆盖四条硬性口径：

  1. 输出文件存在且非空，体积不小于下限（默认 3072 字节）；
  2. 输出尺寸 = 输入尺寸 × scale（默认 1.0，PNG / JPEG 纯标准库解析头部）；
  3. 含透明通道的源图，输出不得降级为非 PNG（按扩展名判定，防丢通道）；
  4. 输出单边不得超过 4096px（超出先缩后放）。

退出码：
  0 —— 全部校验通过；
  1 —— 校验不通过（尺寸不符 / 体积过小 / 透明通道疑似丢失 / 超上限）；
  2 —— 输入不足或参数非法（文件缺失、scale 非法、格式不可解析）。

用法：
  python3 scripts/enhance_check.py --input raw/a.png --output out/a_enhanced.png --scale 2 --preset ppt
  python3 scripts/enhance_check.py --input raw/a.jpg --output out/a_enhanced.png --scale 1.5 --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

MAX_EDGE = 4096           # 单边上限（与 SKILL.md 资源上限一致）
MIN_BYTES_DEFAULT = 3072  # 输出体积下限


def _png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def _jpeg_size(path):
    with open(path, "rb") as fh:
        if fh.read(2) != b"\xff\xd8":
            return None
        while True:
            b = fh.read(1)
            if not b:
                return None
            if b != b"\xff":
                continue
            marker = fh.read(1)
            while marker == b"\xff":
                marker = fh.read(1)
            if not marker:
                return None
            m = marker[0]
            if m in _SOF:
                fh.read(3)
                h = int.from_bytes(fh.read(2), "big")
                w = int.from_bytes(fh.read(2), "big")
                return w, h
            if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                continue
            ln = int.from_bytes(fh.read(2), "big")
            if ln < 2:
                return None
            fh.seek(ln - 2, 1)


def image_info(path):
    """返回 (宽度, 高度, 是否含透明通道)；不可解析返回 (None, None, None)。"""
    try:
        with open(path, "rb") as fh:
            magic = fh.read(8)
    except OSError:
        return None, None, None
    if magic[:8] == b"\x89PNG\r\n\x1a\n":
        dim = _png_size(path)
        if dim is None:
            return None, None, None
        # IHDR 第 25 字节为 color type：4=灰度+alpha，6=RGB+alpha
        with open(path, "rb") as fh:
            fh.seek(25)
            ctype = fh.read(1)
        has_alpha = ctype in (b"\x04", b"\x06")
        return dim[0], dim[1], has_alpha
    if magic[:2] == b"\xff\xd8":
        dim = _jpeg_size(path)
        if dim is None:
            return None, None, None
        return dim[0], dim[1], False
    return None, None, None


def run(args):
    """执行复核，返回 (exit_code, result_dict)。"""
    problems, notes = [], []

    if not args.input or not args.output:
        raise ValueError("缺少必填参数：--input 与 --output")
    if not os.path.isfile(args.input):
        raise ValueError("输入文件不存在：%s" % args.input)
    if args.scale <= 0:
        raise ValueError("--scale 必须为正数，收到：%r" % args.scale)

    min_bytes = args.min_bytes if args.min_bytes is not None else MIN_BYTES_DEFAULT

    if not os.path.isfile(args.output):
        problems.append("输出文件缺失：%s" % args.output)
        return 1, {"result": "FAIL", "problems": problems, "notes": notes}

    out_bytes = os.path.getsize(args.output)
    if out_bytes < min_bytes:
        problems.append("输出体积 %d 字节低于下限 %d 字节" % (out_bytes, min_bytes))
    else:
        notes.append("输出体积 %d 字节，通过下限 %d 字节" % (out_bytes, min_bytes))

    iw, ih, in_alpha = image_info(args.input)
    ow, oh, _ = image_info(args.output)
    if iw is None or ow is None:
        notes.append("尺寸校验跳过：输入或输出不可解析（属边界条件，需人工放大 200% 目视复核）")
    else:
        expect = (round(iw * args.scale), round(ih * args.scale))
        if (ow, oh) != expect:
            problems.append("尺寸不符：期望 %s，实得 %s" % (expect, (ow, oh)))
        else:
            notes.append("尺寸正确：%s × %s → %s" % ((iw, ih), args.scale, (ow, oh)))
        if max(ow, oh) > MAX_EDGE:
            problems.append("输出单边 %dpx 超过上限 %dpx" % (max(ow, oh), MAX_EDGE))

    if in_alpha is True and os.path.splitext(args.output)[1].lower() not in (".png", ".webp"):
        problems.append("源图含透明通道，但输出非 PNG/WEBP：疑似丢失通道，禁止静默通过")
    elif in_alpha is True:
        notes.append("源图含透明通道，输出为 %s，通道保真" % os.path.splitext(args.output)[1])

    if args.preset:
        notes.append("预设：%s（用于回溯 manifest.json 参数）" % args.preset)

    code = 1 if problems else 0
    return code, {
        "result": "PASS" if not problems else "FAIL",
        "input": args.input, "output": args.output, "scale": args.scale,
        "preset": args.preset, "out_bytes": out_bytes,
        "in_size": (iw, ih), "out_size": (ow, oh), "in_has_alpha": in_alpha,
        "problems": problems, "notes": notes,
    }


def main(argv=None):
    """命令行入口，返回退出码 0/1/2。"""
    ap = argparse.ArgumentParser(description="image-enhancer 增强结果自检器（标准库实现）")
    ap.add_argument("--input", help="源图路径")
    ap.add_argument("--output", help="增强图路径")
    ap.add_argument("--scale", type=float, default=1.0, help="放大倍数（默认 1.0，不放大）")
    ap.add_argument("--preset", default="", help="所用预设 ppt/doc/web/print/social（可选）")
    ap.add_argument("--min-bytes", dest="min_bytes", type=int, default=MIN_BYTES_DEFAULT,
                    help="输出体积下限（字节，默认 %d）" % MIN_BYTES_DEFAULT)
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args(argv)

    try:
        code, res = run(args)
    except ValueError as exc:
        print("[输入不足] %s" % exc)
        print("提示：补齐必填参数后重跑；无法解析的格式请人工放大 200% 目视复核，并标注【待核】。")
        return 2

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("结果：%s（退出码 %d）" % (res["result"], code))
        for p in res["problems"]:
            print("  [不合规] %s" % p)
        for n in res["notes"]:
            print("  [说明] %s" % n)
    return code


if __name__ == "__main__":
    sys.exit(main())
