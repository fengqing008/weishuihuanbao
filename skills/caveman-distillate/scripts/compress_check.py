#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compress_check.py — 压缩率量化校验器（caveman-distillate 专用）

读入两份文本（正常版 normal 与压缩版 compressed），用 Python 标准库统计字符数，
输出压缩率（compressed / normal * 100%）与是否达标（默认阈值 60%，即压缩率 ≤ 60% 算达标）。

零第三方依赖，仅用 os / sys / argparse / json / re。

用法：
  python3 scripts/compress_check.py --normal normal.txt --compressed distilled.txt
  python3 scripts/compress_check.py normal.txt distilled.txt --threshold 55
  python3 scripts/compress_check.py --normal a.txt --compressed b.txt --json
  python3 scripts/compress_check.py --help

退出码：
  0 = 达标（压缩率 ≤ 阈值）
  1 = 未达标（压缩率 > 阈值）
  2 = 输入异常（文件缺失 / 路径为空 / 无法读取）
"""
import argparse
import json
import os
import re
import sys

DEFAULT_THRESHOLD = 60.0


def read_text(path):
    """读取文本，自动按 UTF-8 解码；失败时退回 errors=replace 兜底。"""
    if not path:
        raise ValueError("路径为空")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()


def count_chars(text):
    """字符数（含空白），排除末尾换行带来的抖动。"""
    return len(text.rstrip("\n"))


def count_nonspace(text):
    """非空白字符数：剔除空格/制表/换行后计数，抗排版差异。"""
    return len(re.sub(r"\s+", "", text))


def count_words(text):
    """词数近似：按空白切分，中文按字符块松散估计。"""
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def ratio(part, whole):
    """返回百分比；分母为 0 时返回 0.0，避免除零异常。"""
    if whole <= 0:
        return 0.0
    return round(part / whole * 100.0, 1)


def build_report(normal, compressed, threshold):
    n_chars = count_chars(normal)
    c_chars = count_chars(compressed)
    n_nonspace = count_nonspace(normal)
    c_nonspace = count_nonspace(compressed)
    n_words = count_words(normal)
    c_words = count_words(compressed)

    r_char = ratio(c_chars, n_chars)
    r_nonspace = ratio(c_nonspace, n_nonspace)
    r_word = ratio(c_words, n_words)

    qualified = r_char <= threshold
    return {
        "normal_chars": n_chars,
        "compressed_chars": c_chars,
        "normal_nonspace": n_nonspace,
        "compressed_nonspace": c_nonspace,
        "normal_words": n_words,
        "compressed_words": c_words,
        "ratio_chars_pct": r_char,
        "ratio_nonspace_pct": r_nonspace,
        "ratio_words_pct": r_word,
        "threshold_pct": threshold,
        "qualified": qualified,
        "verdict": "达标" if qualified else "未达标",
    }


def render_text(rep):
    lines = []
    lines.append("压缩率校验报告")
    lines.append("-" * 40)
    lines.append("正常版字符数        : %d" % rep["normal_chars"])
    lines.append("压缩版字符数        : %d" % rep["compressed_chars"])
    lines.append("正常版非空白字符数  : %d" % rep["normal_nonspace"])
    lines.append("压缩版非空白字符数  : %d" % rep["compressed_nonspace"])
    lines.append("正常版词数(近似)    : %d" % rep["normal_words"])
    lines.append("压缩版词数(近似)    : %d" % rep["compressed_words"])
    lines.append("-" * 40)
    lines.append("压缩率(字符)        : %.1f%%" % rep["ratio_chars_pct"])
    lines.append("压缩率(非空白字符)  : %.1f%%" % rep["ratio_nonspace_pct"])
    lines.append("压缩率(词数)        : %.1f%%" % rep["ratio_words_pct"])
    lines.append("达标阈值(字符口径)  : ≤ %.1f%%" % rep["threshold_pct"])
    lines.append("结论                : %s" % rep["verdict"])
    if not rep["qualified"]:
        lines.append("提示                : 回到 L2—L4 重压一轮；两轮仍不达标则回退正常模式。")
    return "\n".join(lines)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        prog="compress_check.py",
        description="压缩率量化校验器：比较正常版与压缩版文本，输出压缩率与达标结论（默认阈值 60%）。",
        epilog="示例：python3 compress_check.py --normal normal.txt --compressed distilled.txt --threshold 60",
    )
    ap.add_argument("paths", nargs="*", help="位置参数：normal.txt compressed.txt（与 --normal/--compressed 二选一）")
    ap.add_argument("--normal", help="正常版文本文件路径")
    ap.add_argument("--compressed", help="压缩版文本文件路径")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help="达标阈值百分比（默认 60，压缩率 ≤ 阈值即达标）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    return ap.parse_args(argv)


def resolve_paths(args):
    normal = args.normal
    compressed = args.compressed
    rest = list(args.paths)
    if normal is None and rest:
        normal = rest.pop(0)
    if compressed is None and rest:
        compressed = rest.pop(0)
    return normal, compressed


def main(argv=None):
    args = parse_args(argv)
    normal_path, compressed_path = resolve_paths(args)

    if not normal_path or not compressed_path:
        sys.stderr.write("错误：需提供正常版与压缩版两个文本路径。用 --help 查看用法。\n")
        return 2

    try:
        normal = read_text(normal_path)
        compressed = read_text(compressed_path)
    except FileNotFoundError as exc:
        sys.stderr.write("异常：文件不存在 -> %s\n" % exc)
        return 2
    except (ValueError, OSError) as exc:
        sys.stderr.write("异常：读取失败 -> %s\n" % exc)
        return 2

    rep = build_report(normal, compressed, args.threshold)

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(render_text(rep))

    return 0 if rep["qualified"] else 1


if __name__ == "__main__":
    sys.exit(main())
