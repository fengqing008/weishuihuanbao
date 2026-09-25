#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motif_check.py —— 设计纪律检查器（frontend-design 方法论）

对单文件 HTML 成果页做「去模板化」体检。检查为 OK/WARN 级，不判 FAIL、
不阻断既有交付流程，用于提醒而非拦截。

分层感知：若页面已由 v6.2.0 设计纪律层渲染（含 `设计纪律层 v6.2.0` 标记），
则圆角收口、强调单色、动效编排等已被母题统一处理，对应项直接判 OK；
未接入纪律层的旧页面则按源码实际统计并提示。

用法：
  python3 motif_check.py page.html [--json] [--strict]
  退出码：默认恒 0；--strict 时存在 WARN 退出 1
"""
import argparse
import json
import re
import sys

DS_MARK = "设计纪律层 v6.2.0"


def analyse(html):
    items = []
    has_ds = DS_MARK in html
    single_accent = "--ds-accent-fill:var(--accent)" in html
    motion_orch = bool(re.search(r"\.anim-ready\s*\.fx\{\s*opacity:1\s*!important", html))
    has_motif = bool(re.search(r"motif-(editorial|blueprint|narrative|classic)", html))

    # 1. 圆角层级
    if has_ds:
        items.append(("ROUNDING", "OK", "已由纪律层收口为 sm/md/lg 三级 token"))
    else:
        radii = set()
        for m in re.finditer(r"border-radius:\s*([^;\"]+)", html):
            for tok in re.split(r"[\s/]+", m.group(1).strip()):
                mm = re.match(r"^(\d+(?:\.\d+)?)px$", tok)
                if mm and float(mm.group(1)) != 0:
                    radii.add(float(mm.group(1)))
        n = len(radii)
        items.append(("ROUNDING", "OK" if n <= 5 else "WARN",
                      "%d 种圆角像素值（>5 建议收敛为三级）" % n))

    # 2. 装饰性渐变
    if has_ds:
        items.append(("GRADIENT", "OK",
                      "单色强调（纪律层已关闭装饰性渐变）" if single_accent
                      else "渐变经母题有意开启"))
    else:
        n = len(re.findall(r"(?:repeating-)?linear-gradient\(", html))
        items.append(("GRADIENT", "OK" if n <= 8 else "WARN",
                      "%d 处 linear-gradient（>8 建议改单色强调）" % n))

    # 3. 动效策略（纪律层存在时由母题决定，即视为合规）
    if has_ds:
        mm = re.search(r"motion-(orchestrated|off|staggered)", html)
        desc = {"orchestrated": "一次编排", "off": "无动效", "staggered": "错峰入场"}.get(
            mm.group(1) if mm else "", "已声明")
        items.append(("ENTRANCE", "OK", "动效策略由母题决定：%s" % desc))
    else:
        e = bool(re.search(r"\.anim-ready\s+\.fx\s*\{[^}]*opacity:\s*0", html))
        items.append(("ENTRANCE", "WARN" if e else "OK",
                      "存在逐节淡入，建议改为一次编排" if e else "未使用逐节淡入"))

    # 4. 宽字距／全大写标签
    if has_ds:
        items.append(("CAPS", "OK", "标签字距已按母题规范"))
    else:
        n = len(re.findall(r"letter-spacing:\s*\.?2em", html))
        items.append(("CAPS", "OK" if n == 0 else "WARN",
                      "无宽字距标签" if n == 0 else "%d 处 tracked-out 宽字距标签" % n))

    # 5. 母题声明
    items.append(("MOTIF", "OK" if has_motif else "WARN",
                  "已声明版式母题" if has_motif else "未声明版式母题（默认 editorial）"))
    return items


def main():
    ap = argparse.ArgumentParser(description="单文件 HTML 设计纪律检查")
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="存在 WARN 时退出码 1")
    a = ap.parse_args()
    html = open(a.file, encoding="utf-8").read()
    items = analyse(html)
    warns = [i for i in items if i[1] == "WARN"]
    if a.json:
        print(json.dumps({"file": a.file, "items": items, "warn": len(warns),
                          "result": "WARN" if warns else "PASS"}, ensure_ascii=False, indent=2))
    else:
        print("设计纪律检查：%s" % a.file)
        print("-" * 58)
        for k, lv, msg in items:
            print("  [%s] %-10s %s" % (lv, k, msg))
        print("-" * 58)
        print("RESULT=%s  WARN=%d" % ("WARN" if warns else "PASS", len(warns)))
    if warns and a.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
