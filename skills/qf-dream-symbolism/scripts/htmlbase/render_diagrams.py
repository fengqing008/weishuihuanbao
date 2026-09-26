#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_diagrams.py —— 图形围栏渲染器（html-report-builder v5.1.0）

职责：把 Markdown 代码围栏中的图形源码渲染为可内嵌单文件 HTML 的图形。

  mermaid / mmd             → 调 pretty-mermaid（本地 JS 渲染，无浏览器、无网络）
  svg                       → 直接内嵌（任意绘图技能产物：baoyu-diagram / fireworks-tech-graph /
                              moai-tool-svg / qf-lineart / graphviz 导出的 SVG 均可）
  dot/graphviz/plantuml/…   → 沙箱无本地渲染器 → 由调用方降级为「源码卡 + 处置提示」

依赖：Node.js（沙箱已装）+ pretty-mermaid 技能（含 node_modules，21MB，不随基座复制，
      由三级探测定位）。渲染器缺失时全部图形自动降级为源码卡，不阻断渲染。

CLI：
  python3 render_diagrams.py check                          # 渲染器可用性
  python3 render_diagrams.py render in.mmd -o out.svg [--theme ocean]
"""
import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# 三级探测：随包副本 → 技能目录 → 工作区软链
PM_CANDIDATES = (
    os.path.join(HERE, "vendors", "pretty-mermaid"),
    "/root/.skills/pretty-mermaid",
    "/sandbox/workspace/skills/pretty-mermaid",
)


def find_renderer():
    """返回 (技能根, render.mjs 绝对路径)；未找到返回 (None, None)。"""
    for root in PM_CANDIDATES:
        rjs = os.path.join(root, "scripts", "render.mjs")
        if os.path.exists(rjs):
            return root, rjs
    return None, None


def available():
    """渲染链是否可用（Node + render.mjs）。"""
    import shutil as _sh
    _, rjs = find_renderer()
    return bool(rjs) and bool(_sh.which("node"))


def render_svg(mmd_text, colors=None, timeout=180):
    """渲染 Mermaid 源码 → SVG 字符串。失败返回 (None, 原因)。"""
    _, rjs = find_renderer()
    if not rjs:
        return None, "未找到 pretty-mermaid 渲染器（render.mjs）"
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "diagram.mmd")
        out = os.path.join(td, "diagram.svg")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(mmd_text)
        cmd = ["node", rjs, "-i", src, "-o", out, "-f", "svg"]
        c = colors or {}
        for key, flag in (("bg", "--bg"), ("fg", "--fg"), ("line", "--line"),
                          ("accent", "--accent"), ("muted", "--muted"),
                          ("surface", "--surface"), ("border", "--border")):
            if c.get(key):
                cmd += [flag, str(c[key])]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, "渲染超时（>%d 秒）" % timeout
        except FileNotFoundError:
            return None, "未找到 node 运行时"
        if p.returncode != 0 or not os.path.exists(out):
            msg = (p.stderr or p.stdout or "").strip().replace("\n", " ")[:240]
            return None, msg or "渲染失败（退出码 %s）" % p.returncode
        with open(out, encoding="utf-8") as fh:
            svg = fh.read()
        if not svg.lstrip().startswith("<svg"):
            return None, "渲染产物不是 SVG"
        return svg, ""


def theme_colors(palette):
    """把报告配色映射为 Mermaid 主题色，保证图与页面同调。"""
    if not palette:
        return {}
    g = palette.get
    return {
        "bg": g("surface"), "fg": g("text"), "line": g("border"),
        "accent": g("accent"), "muted": g("muted"),
        "surface": g("surface2") or g("surface"), "border": g("border"),
    }


def _main():
    ap = argparse.ArgumentParser(description="图形围栏渲染器（v5.1.0）")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check", help="渲染器可用性")
    r = sub.add_parser("render", help="渲染 .mmd → .svg")
    r.add_argument("input")
    r.add_argument("-o", "--out", required=True)
    r.add_argument("--theme", default=None, help="报告配色 id（取 palettes.BY_ID）")
    a = ap.parse_args()

    if a.cmd == "check":
        root, rjs = find_renderer()
        print("Node 运行时   : %s" % ("OK" if __import__("shutil").which("node") else "缺失"))
        print("pretty-mermaid: %s" % (root or "未找到"))
        print("render.mjs    : %s" % (rjs or "未找到"))
        print("结论          : %s" % ("可用（mermaid 可内嵌渲染）" if available() else "不可用（mermaid 将降级为源码卡）"))
        return 0 if available() else 1

    if a.cmd == "render":
        colors = {}
        if a.theme:
            try:
                sys.path.insert(0, HERE)
                from palettes import BY_ID
                colors = theme_colors(BY_ID.get(a.theme))
            except Exception:
                pass
        with open(a.input, encoding="utf-8") as fh:
            text = fh.read()
        svg, err = render_svg(text, colors)
        if not svg:
            print("渲染失败：%s" % err, file=sys.stderr)
            return 1
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("已渲染：%s（%.1fKB）" % (a.out, len(svg) / 1024.0))
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(_main())
