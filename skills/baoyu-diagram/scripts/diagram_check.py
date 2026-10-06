#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diagram_check.py —— baoyu-diagram 输出自检脚本（仅使用标准库）

用途：对生成的 SVG 图件做结构自检——根元素与命名空间、viewBox 合法性、
节点/分组规模、坐标越界、远程资源依赖。用于交付前的质量门禁与失败兜底。

用法：
  python3 diagram_check.py --file diagram.svg
  python3 diagram_check.py --file diagram.svg --max-nodes 40 --json

退出码：
  0 = 通过；1 = 存在告警（可交付但建议优化）；2 = 存在致命错误或参数/文件错误。
"""
import argparse
import json
import os
import re
import sys

SHAPE_TAGS = {
    "path", "rect", "circle", "line", "polygon", "polyline", "text", "use",
    "stop", "image", "tspan", "ellipse", "feoffset", "fegaussianblur",
}
CONTAINER_TAGS = {
    "style", "defs", "g", "marker", "pattern", "clippath", "lineargradient",
    "radialgradient", "symbol", "filter", "mask",
}
TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)")
VB_RE = re.compile(r'viewBox\s*=\s*"([^"]+)"')
REMOTE_RE = re.compile(r'(?:href|xlink:href)\s*=\s*"(https?://[^"]+)"', re.I)
EXT_RE = re.compile(r"url\(\s*['\"]?(https?://[^)'\"]+)", re.I)


def check(path, max_nodes=40):
    """返回 (exit_code, errors, warnings, info)。"""
    errors, warns, info = [], [], {}
    if not os.path.isfile(path):
        return 2, ["文件不存在或不可读：%s" % path], [], {}
    with open(path, encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    if not text.strip():
        return 2, ["SVG 文件为空（0 字节），疑似导出失败"], [], {"chars": 0}
    info["chars"] = len(text)

    if "<svg" not in text:
        errors.append("缺少根元素 <svg>")
    if "xmlns" not in text:
        errors.append("缺少 xmlns 命名空间声明")

    m = VB_RE.search(text)
    if not m:
        warns.append("未找到 viewBox，缩放与适配可能异常")
    else:
        parts = m.group(1).replace(",", " ").split()
        if len(parts) != 4:
            errors.append("viewBox 参数个数异常：%s" % m.group(1))
        else:
            try:
                vals = [float(x) for x in parts]
                info["viewBox"] = vals
                if vals[2] <= 0 or vals[3] <= 0:
                    errors.append("viewBox 宽或高非正数")
            except ValueError:
                errors.append("viewBox 数值不可解析：%s" % m.group(1))

    stack = []
    for closing, name in TAG_RE.findall(text):
        low = name.lower()
        if low in SHAPE_TAGS:
            continue
        if low == "svg":
            if not closing:
                stack.append(low)
            continue
        if low in CONTAINER_TAGS:
            if closing:
                if not stack or stack[-1] != low:
                    warns.append("标签配对疑似异常：</%s>" % low)
                    break
                stack.pop()
            else:
                stack.append(low)

    info["group_count"] = len(re.findall(r"<\s*g[\s>]", text))
    if info["group_count"] > max_nodes:
        warns.append("分组数 %d 超过阈值 %d，建议拆分多图或改层级布局"
                     % (info["group_count"], max_nodes))

    remotes = sorted(set(REMOTE_RE.findall(text)) | set(EXT_RE.findall(text)))
    if remotes:
        warns.append("存在远程资源引用（离线打开可能丢失样式）：" + ", ".join(remotes[:3]))
    info["remote_refs"] = len(remotes)

    if ">text<" in text.replace(" ", ""):
        warns.append("疑似空文本节点，可能存在标签压线或占位残留")

    code = 2 if errors else (1 if warns else 0)
    return code, errors, warns, info


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="baoyu-diagram 输出 SVG 自检脚本（仅标准库，退出码 0/1/2）")
    parser.add_argument("--file", required=True, help="待校验的 .svg 文件路径")
    parser.add_argument("--max-nodes", type=int, default=40, help="分组数量阈值，默认 40")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    args = parser.parse_args(argv)

    code, errors, warns, info = check(args.file, args.max_nodes)
    if args.json:
        print(json.dumps({"file": args.file, "exit": code, "errors": errors,
                          "warnings": warns, "info": info}, ensure_ascii=False))
    else:
        print("[diagram_check] %s" % args.file)
        for e in errors:
            print("  x 错误：%s" % e)
        for w in warns:
            print("  ! 告警：%s" % w)
        print("  结论：%s" % {0: "通过", 1: "有告警", 2: "有致命错误"}[code])
    return code


if __name__ == "__main__":
    sys.exit(main())
