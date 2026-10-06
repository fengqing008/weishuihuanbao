#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""excalidraw_deliver_check.py — 手绘图交付自检器（仅标准库，零第三方依赖）

在 excalidraw_check.py（结构体检）之外，做交付级齐备性检查，覆盖：
  1. 文件齐备：.excalidraw 是否存在、是否为合法 JSON
  2. 顶层结构：type/version/elements/appState/files 是否齐备
  3. 交付物齐备：可选校验渲染预览 PNG 是否已生成
  4. 规范抽查：元素数量、容器占比、text 是否混入 JSON 结构、opacity/fontFamily
  5. 缺口提示：统计遗留占位词（待填/待查证/TODO）

用法:
  python3 excalidraw_deliver_check.py --file diagram.excalidraw
  python3 excalidraw_deliver_check.py --file diagram.excalidraw --expect-png
  python3 excalidraw_deliver_check.py --file diagram.excalidraw --json
  python3 excalidraw_deliver_check.py --help

退出码: 0 = 无 ERROR；1 = 存在 ERROR；2 = 输入不可读。
"""
import argparse
import json
import os
import re
import sys

TOP_KEYS = ["type", "version", "elements", "appState", "files"]
PLACEHOLDER = re.compile(r"(待填|待查证|待补充|TODO|占位)")


def main():
    ap = argparse.ArgumentParser(description="Excalidraw 交付自检器")
    ap.add_argument("--file", required=True, help=".excalidraw 文件路径")
    ap.add_argument("--expect-png", action="store_true", help="要求同目录已生成渲染 PNG")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    path = os.path.abspath(args.file)
    if not os.path.isfile(path):
        print("[ERROR] 文件不可读：%s" % path)
        return 2
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as exc:
        print("[ERROR] JSON 解析异常：%s" % exc)
        return 2

    errors, warnings, info = [], [], {}
    if not isinstance(doc, dict):
        errors.append("顶层不是 JSON 对象")
        doc = {}
    for k in TOP_KEYS:
        if k not in doc:
            errors.append("顶层缺字段：%s" % k)
    if doc.get("type") != "excalidraw":
        warnings.append("顶层 type 建议为 \"excalidraw\"，当前为 %r" % doc.get("type"))

    els = doc.get("elements") if isinstance(doc.get("elements"), list) else []
    info["element_count"] = len(els)
    if not els:
        errors.append("elements 为空，图为空")
    containers = sum(1 for e in els if isinstance(e, dict) and e.get("type") in ("rectangle", "ellipse", "diamond"))
    texts = [e for e in els if isinstance(e, dict) and e.get("type") == "text"]
    info["container_count"] = containers
    info["text_count"] = len(texts)
    if texts:
        ratio = containers / float(len(texts))
        info["container_text_ratio"] = round(ratio, 2)
        if ratio > 0.3:
            warnings.append("带容器文字占比 %.2f > 0.30，建议改自由文本" % ratio)

    bad_text, bad_opacity, bad_font = [], [], []
    for e in els:
        if not isinstance(e, dict):
            continue
        t = e.get("text") or ""
        if t and ("{" in t or "}" in t or ":" in t and '"' in t):
            bad_text.append(e.get("id"))
        if e.get("opacity") not in (None, 100):
            bad_opacity.append(e.get("id"))
        if e.get("type") == "text" and e.get("fontFamily") not in (None, 3):
            bad_font.append(e.get("id"))
    if bad_text:
        errors.append("text 疑似混入 JSON 结构：%s" % "、".join(map(str, bad_text[:6])))
    if bad_opacity:
        warnings.append("存在 opacity != 100 的元素：%s" % "、".join(map(str, bad_opacity[:6])))
    if bad_font:
        warnings.append("存在 fontFamily != 3 的文字：%s" % "、".join(map(str, bad_font[:6])))

    raw = json.dumps(doc, ensure_ascii=False)
    info["placeholder_hits"] = len(PLACEHOLDER.findall(raw))
    if info["placeholder_hits"]:
        warnings.append("存在未清理占位词 %d 处【待填：待查证】" % info["placeholder_hits"])

    if args.expect_png:
        png = os.path.splitext(path)[0] + ".png"
        info["png_exists"] = os.path.isfile(png)
        if not info["png_exists"]:
            errors.append("未找到渲染预览 PNG：%s（目视校验未完成）" % png)

    verdict = "FAIL" if errors else "PASS"
    result = {"file": path, "info": info, "errors": errors, "warnings": warnings, "verdict": verdict}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("== Excalidraw 交付自检 ==")
        for k, v in info.items():
            print("  %s: %s" % (k, v))
        for w in warnings:
            print("[WARN ] " + w)
        for e in errors:
            print("[ERROR] " + e)
        print("结论：%s（ERROR %d / WARN %d）" % (verdict, len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
