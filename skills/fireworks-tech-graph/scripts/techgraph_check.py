#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""techgraph_check.py —— 技术图交付前质量门（仅标准库，无第三方依赖）。

对渲染产物做写入前自检与交付前复核：
  * SVG 结构检查（标签平衡、属性引号、特殊字符转义、marker 引用、</svg> 闭合）
  * 中文字体栈检查（缺 CJK 字体栈时导出 PNG 易缺字形）
  * 视图盒(viewBox)检查
  * 规格 JSON 合法性检查（layers/nodes/edges 三元结构）

退出码约定：
  0 = 全部通过（放行交付）
  1 = 发现问题（须先修复，禁止未修复交付）
  2 = 用法错误 / 输入文件缺失 / 解析异常（进入降级路径，由人工复核）

用法：
  python3 techgraph_check.py --svg out/arch.svg
  python3 techgraph_check.py --svg out/arch.svg --cjk --json
  python3 techgraph_check.py --spec specs/order-arch.json
  python3 techgraph_check.py --svg out/arch.svg --spec specs/order-arch.json
  python3 techgraph_check.py --help

边界条件：本脚本只做静态检查，不做像素级渲染比对；渲染失败须回退到
render_diagram.py 或命令行渲染后端（rsvg-convert/cairosvg/inkscape）。
"""
import argparse
import json
import os
import re
import sys

TAGS = ["rect", "text", "g", "line", "path", "circle", "polygon", "ellipse"]
CJK_STACK = ["Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", "SimSun", "Source Han Sans"]
CJK_MISSING_NOTE = "标题/标签含中文但字体栈未声明 CJK 字体，导出 PNG 可能缺字形"


def read_text(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def check_svg(path, need_cjk=False):
    """返回 (errors, warnings)。"""
    errors, warnings = [], []
    if not os.path.isfile(path):
        errors.append("文件不存在：%s" % path)
        return errors, warnings
    text = read_text(path)
    if not text.strip():
        errors.append("文件为空")
        return errors, warnings

    if "</svg>" not in text:
        errors.append("缺少 </svg> 闭合标签（Quick Fix：在文件末尾追加 </svg>）")
    if "<svg" not in text:
        errors.append("未找到 <svg 根元素")

    # 1) 标签平衡
    for tag in TAGS:
        opens = len(re.findall(r"<%s[\s>]" % tag, text))
        closes = len(re.findall(r"</%s>" % tag, text))
        selfclose = len(re.findall(r"<%s[^>]*/>" % tag, text))
        if opens and closes + selfclose < opens:
            errors.append("标签不平衡：<%s> 开 %d / 闭 %d / 自闭合 %d" % (tag, opens, closes, selfclose))

    # 2) 属性引号
    bad_quote = re.findall(r"\s(?:fill|stroke|x|y|width|height|font-size)=[^\"'\s>]+", text)
    if bad_quote:
        errors.append("属性值未加引号 %d 处，例如 %s" % (len(bad_quote), bad_quote[0][:40]))

    # 3) 特殊字符转义
    for m in re.finditer(r"<text[^>]*>(.*?)</text>", text, re.S):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        if re.search(r"(?<!&lt;)<(?![/a-zA-Z])|(?<!&gt;)>|(?<!&amp;)&(?!amp;|lt;|gt;|#)", inner):
            warnings.append("文本节点可能含未转义特殊字符：%s" % inner.strip()[:30])
            break

    # 4) marker 引用
    used = set(re.findall(r'url\(#([\w-]+)\)', text))
    defined = set(re.findall(r'<marker[^>]*id="([\w-]+)"', text))
    missing = used - defined
    if missing:
        errors.append("marker 引用无定义：%s（须在 <defs> 补 <marker id=...>）" % ", ".join(sorted(missing)))

    # 5) viewBox
    if "viewBox" not in text:
        warnings.append("缺少 viewBox，缩放行为不可预期")

    # 6) 中文字体栈
    has_cjk_font = any(f in text for f in CJK_STACK)
    has_cjk_text = bool(re.search(r"[\u4e00-\u9fff]", text))
    if (need_cjk or has_cjk_text) and not has_cjk_font:
        warnings.append(CJK_MISSING_NOTE)

    return errors, warnings


def check_spec(path):
    errors, warnings = [], []
    if not os.path.isfile(path):
        errors.append("规格文件不存在：%s" % path)
        return errors, warnings
    raw = read_text(path)
    try:
        spec = json.loads(raw)
    except Exception as exc:  # 失败分支：规格非法直接进入修复路径
        errors.append("规格 JSON 解析失败：%s" % exc)
        return errors, warnings

    nodes = spec.get("nodes") or []
    layers = spec.get("layers") or []
    edges = spec.get("edges") or []
    if not isinstance(nodes, list):
        errors.append("nodes 不是数组")
        nodes = []
    if not layers:
        warnings.append("缺 layers 数组，渲染器将按单层处理")
    ids = set()
    for n in nodes:
        if not isinstance(n, dict):
            errors.append("nodes 元素不是对象")
            continue
        if not n.get("id"):
            errors.append("节点缺 id：%r" % n)
        if not n.get("label"):
            warnings.append("节点 %s 缺 label" % n.get("id"))
        ids.add(str(n.get("id")))
    for e in edges:
        if not isinstance(e, dict):
            errors.append("edges 元素不是对象")
            continue
        for k in ("from", "to"):
            if e.get(k) not in ids:
                errors.append("边 %s->%s 引用了不存在的节点 %s" % (e.get("from"), e.get("to"), e.get(k)))
    if not nodes:
        warnings.append("规格未含任何节点")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="技术图交付前质量门：SVG 结构自检 + 规格 JSON 校验（仅标准库）",
        epilog="退出码 0=通过 / 1=发现问题 / 2=用法或输入异常")
    ap.add_argument("--svg", help="待检查的 SVG 文件路径")
    ap.add_argument("--spec", help="待检查的规格 JSON 文件路径")
    ap.add_argument("--cjk", action="store_true", help="强制要求声明 CJK 字体栈")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    ap.add_argument("--strict", action="store_true", help="把警告也视为失败（退出码 1）")
    args = ap.parse_args(argv)

    if not args.svg and not args.spec:
        ap.print_help(sys.stderr)
        print("\n错误：至少指定 --svg 或 --spec 之一。", file=sys.stderr)
        return 2

    errors, warnings = [], []
    if args.svg:
        e, w = check_svg(args.svg, need_cjk=args.cjk)
        errors += e
        warnings += w
    if args.spec:
        e, w = check_spec(args.spec)
        errors += e
        warnings += w

    ok = not errors and (not warnings or not args.strict)
    if args.json:
        print(json.dumps({"ok": ok, "errors": errors, "warnings": warnings},
                         ensure_ascii=False, indent=2))
    else:
        for x in errors:
            print("[错误] %s" % x)
        for x in warnings:
            print("[警告] %s" % x)
        print("结果：%s（错误 %d / 警告 %d）" % ("通过" if ok else "未通过", len(errors), len(warnings)))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # 异常兜底：解析异常不崩溃，转交人工复核
        print("异常：%s（请检查输入文件与参数，或改用 --help 查看用法）" % exc, file=sys.stderr)
        sys.exit(2)
