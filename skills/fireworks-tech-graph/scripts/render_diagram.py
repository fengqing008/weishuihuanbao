#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_diagram.py — 技术图渲染器（JSON 规格 → SVG → PNG）

用途
    fireworks-tech-graph 技能的可执行渲染后端。读取一份分层结构 JSON 规格，
    按指定视觉风格生成符合规范的技术图 SVG（8px 网格对齐、正交路由、
    标签背景防遮挡、箭头 marker 定义齐全），校验 XML 合法性后按需导出 PNG。

用法
    # 1. 从 JSON 规格出图（推荐）
    python3 scripts/render_diagram.py --spec spec.json --out out/arch.svg --style 1 --width 1920 --png

    # 2. 内置演示规格，用于自检与冒烟测试
    python3 scripts/render_diagram.py --demo --out out/demo.svg --style 2 --png

    # 3. 只校验不导出 PNG
    python3 scripts/render_diagram.py --spec spec.json --out out/arch.svg --no-png

规格 JSON 结构
    {
      "title": "图标题（可选）",
      "legend": true,
      "layers": [
        {"name": "层名（可选）",
         "nodes": [{"id": "a", "label": "节点名", "sub": "副标题（可选）"}]}
      ],
      "edges": [
        {"from": "a", "to": "b", "label": "箭头标签（可选）",
         "kind": "primary|control|read|write|async|transform"}
      ]
    }

退出码
    0 成功；1 规格非法；2 写出或校验失败
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

# ── 7 套视觉风格的样式令牌（与 references/style-*.md 保持同源）─────────────
STYLES = {
    "1": dict(name="flat-icon", bg="#ffffff", grid="none", node_fill="#ffffff",
              node_stroke="#d1d5db", title="#111827", text="#111827", muted="#6b7280",
              radius=8, group_stroke="#9ca3af",
              accents=["#2563eb", "#dc2626", "#16a34a", "#9333ea"],
              font="'Helvetica Neue', Helvetica, Arial, 'Noto Sans CJK SC', 'PingFang SC', 'Microsoft YaHei', sans-serif"),
    "2": dict(name="dark-terminal", bg="#0f0f1a", grid="none", node_fill="#0f172a",
              node_stroke="#334155", title="#e2e8f0", text="#e2e8f0", muted="#94a3b8",
              radius=6, group_stroke="#475569",
              accents=["#a855f7", "#f97316", "#3b82f6", "#10b981"],
              font="'SF Mono', 'Fira Code', 'Cascadia Code', 'Courier New', monospace"),
    "3": dict(name="blueprint", bg="#0a1628", grid="#112240", node_fill="#0d1f3c",
              node_stroke="#00b4d8", title="#caf0f8", text="#caf0f8", muted="#90e0ef",
              radius=2, group_stroke="#0077b6",
              accents=["#00b4d8", "#48cae4", "#06d6a0", "#f77f00"],
              font="'Courier New', 'Lucida Console', 'Noto Sans CJK SC', monospace"),
    "4": dict(name="notion-clean", bg="#ffffff", grid="none", node_fill="#ffffff",
              node_stroke="#e5e7eb", title="#37352f", text="#37352f", muted="#787774",
              radius=4, group_stroke="#d3d3d0",
              accents=["#2383e2", "#eb5757", "#0f7b6c", "#9b51e0"],
              font="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans CJK SC', sans-serif"),
    "5": dict(name="glassmorphism", bg="#12122b", grid="none", node_fill="#1e1e42",
              node_stroke="#6d6df0", title="#f5f5ff", text="#eaeaff", muted="#a5a5d6",
              radius=14, group_stroke="#5b5bd6",
              accents=["#8b5cf6", "#ec4899", "#22d3ee", "#34d399"],
              font="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans CJK SC', sans-serif"),
    "6": dict(name="claude-official", bg="#f8f6f3", grid="none", node_fill="#ffffff",
              node_stroke="#d9d2c7", title="#2b2a27", text="#2b2a27", muted="#7a736a",
              radius=10, group_stroke="#c9c0b4",
              accents=["#d97757", "#6a9bcc", "#7ba05b", "#c08a3e"],
              font="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans CJK SC', sans-serif"),
    "7": dict(name="openai-official", bg="#ffffff", grid="none", node_fill="#ffffff",
              node_stroke="#e5e5e5", title="#0d0d0d", text="#0d0d0d", muted="#6e6e80",
              radius=8, group_stroke="#e5e5e5",
              accents=["#10a37f", "#1d4ed8", "#f97316", "#71717a"],
              font="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans CJK SC', sans-serif"),
}

EDGE_KINDS = {
    "primary":   (0, 2.0, None),
    "control":   (1, 1.5, None),
    "read":      (2, 1.5, None),
    "write":     (2, 1.5, "5,3"),
    "async":     (3, 1.5, "4,2"),
    "transform": (0, 1.0, "2,2"),
}

NODE_W, NODE_H = 180, 88
COL_GAP, ROW_GAP = 120, 120
MARGIN, TITLE_H, LEGEND_H = 40, 64, 96
MIN_W, MIN_H = 960, 600


def esc(s):
    """XML 转义，禁止未转义的 < > & 进入文本节点。"""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def load_spec(path):
    with open(path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    if not isinstance(spec, dict) or "layers" not in spec:
        raise ValueError("规格缺少 layers 数组")
    ids = []
    for layer in spec["layers"]:
        for node in layer.get("nodes", []):
            if "id" not in node or "label" not in node:
                raise ValueError("节点必须同时具备 id 与 label")
            if node["id"] in ids:
                raise ValueError("节点 id 重复：%s" % node["id"])
            ids.append(node["id"])
    for edge in spec.get("edges", []):
        for key in ("from", "to"):
            if edge.get(key) not in ids:
                raise ValueError("边引用了不存在的节点：%s" % edge.get(key))
    return spec


def demo_spec():
    return {
        "title": "在线监测数据链路（演示）",
        "legend": True,
        "layers": [
            {"name": "接入层", "nodes": [
                {"id": "user", "label": "业务人员", "sub": "Web / 移动端"},
                {"id": "cron", "label": "定时任务", "sub": "数据同步"}]},
            {"name": "服务层", "nodes": [
                {"id": "api", "label": "网关", "sub": "鉴权 / 限流"},
                {"id": "core", "label": "核算服务", "sub": "指标计算"}]},
            {"name": "数据层", "nodes": [
                {"id": "db", "label": "业务库", "sub": "PostgreSQL"},
                {"id": "obj", "label": "对象存储", "sub": "附件 / 图纸"}]},
        ],
        "edges": [
            {"from": "user", "to": "api", "label": "请求", "kind": "primary"},
            {"from": "cron", "to": "core", "label": "批量拉取", "kind": "async"},
            {"from": "api", "to": "core", "label": "调用", "kind": "primary"},
            {"from": "core", "to": "db", "label": "读取", "kind": "read"},
            {"from": "core", "to": "db", "label": "写入", "kind": "write"},
            {"from": "core", "to": "obj", "label": "归档", "kind": "transform"},
        ],
    }


def layout(spec):
    """分层布局：层自上而下，节点在层内等距分布，中心对齐 8px 网格网格。"""
    layers = spec["layers"]
    max_cols = max(len(l.get("nodes", [])) for l in layers)
    content_w = max_cols * NODE_W + max(0, max_cols - 1) * COL_GAP
    width = max(MIN_W, content_w + MARGIN * 2 + 200)
    rows = len(layers)
    height = max(MIN_H, MARGIN + TITLE_H + rows * (NODE_H + ROW_GAP) + LEGEND_H)
    placed, layer_boxes = {}, []
    y = MARGIN + TITLE_H + ROW_GAP // 2
    for layer in layers:
        nodes = layer.get("nodes", [])
        n = len(nodes)
        span = n * NODE_W + max(0, n - 1) * COL_GAP
        x0 = (width - span) / 2.0
        for i, node in enumerate(nodes):
            x = x0 + i * (NODE_W + COL_GAP)
            placed[node["id"]] = dict(x=round(x / 8) * 8, y=round(y / 8) * 8, node=node)
        if layer.get("name"):
            layer_boxes.append((layer["name"], round(x0 / 8) * 8 - 16, y - 24, span + 32, NODE_H + 34))
        y += NODE_H + ROW_GAP
    return width, height, placed, layer_boxes


def build_svg(spec, style_id):
    st = STYLES[style_id]
    width, height, placed, layer_boxes = layout(spec)
    accents = st["accents"]
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
               'viewBox="0 0 %d %d" font-family="%s">' % (width, height, width, height, st["font"]))
    out.append('  <defs>')
    for idx, color in enumerate(accents):
        out.append('    <marker id="arrow-%d" markerWidth="10" markerHeight="7" refX="9" refY="3.5" '
                   'orient="auto" markerUnits="strokeWidth">' % idx)
        out.append('      <path d="M 0 0 L 10 3.5 L 0 7 z" fill="%s"/>' % color)
        out.append('    </marker>')
    if st["grid"] != "none":
        out.append('    <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">')
        out.append('      <path d="M 30 0 L 0 0 L 0 30" fill="none" stroke="%s" stroke-width="0.5"/>'
                   % st["grid"])
        out.append('    </pattern>')
    out.append('  </defs>')
    out.append('  <rect x="0" y="0" width="%d" height="%d" fill="%s"/>' % (width, height, st["bg"]))
    if st["grid"] != "none":
        out.append('  <rect x="0" y="0" width="%d" height="%d" fill="url(#grid)" opacity="0.6"/>'
                   % (width, height))
    if spec.get("title"):
        out.append('  <text x="%d" y="%d" font-size="24" font-weight="700" text-anchor="middle" '
                   'fill="%s">%s</text>' % (width // 2, MARGIN + 24, st["title"], esc(spec["title"])))
    for name, gx, gy, gw, gh in layer_boxes:
        out.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="none" stroke="%s" '
                   'stroke-width="1" stroke-dasharray="6,4" opacity="0.6"/>'
                   % (gx, gy, gw, gh, st["radius"], st["group_stroke"]))
        out.append('  <text x="%d" y="%d" font-size="13" fill="%s">%s</text>'
                   % (gx + 8, gy + 16, st["muted"], esc(name)))
    for edge in spec.get("edges", []):
        src, dst = placed[edge["from"]], placed[edge["to"]]
        kind = edge.get("kind", "primary")
        ai, sw, dash = EDGE_KINDS.get(kind, EDGE_KINDS["primary"])
        color = accents[ai % len(accents)]
        x1, y1 = src["x"] + NODE_W // 2, src["y"] + NODE_H
        x2, y2 = dst["x"] + NODE_W // 2, dst["y"]
        mid_y = round(((y1 + y2) / 2.0) / 8) * 8
        dash_attr = ' stroke-dasharray="%s"' % dash if dash else ''
        out.append('  <path d="M %d,%d L %d,%d L %d,%d L %d,%d" fill="none" stroke="%s" '
                   'stroke-width="%.1f"%s marker-end="url(#arrow-%d)"/>'
                   % (x1, y1, x1, mid_y, x2, mid_y, x2, y2, color, sw, dash_attr, ai))
        if edge.get("label"):
            lx, ly = (x1 + x2) // 2, mid_y - 8
            lw = max(40, len(str(edge["label"])) * 8 + 8)
            out.append('  <rect x="%d" y="%d" width="%d" height="18" fill="%s" opacity="0.95"/>'
                       % (lx - lw // 2, ly - 13, lw, st["bg"]))
            out.append('  <text x="%d" y="%d" font-size="12" text-anchor="middle" fill="%s">%s</text>'
                       % (lx, ly, st["text"], esc(edge["label"])))
    for item in placed.values():
        x, y, node = item["x"], item["y"], item["node"]
        out.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" stroke="%s" '
                   'stroke-width="1.5"/>' % (x, y, NODE_W, NODE_H, st["radius"],
                                             st["node_fill"], st["node_stroke"]))
        out.append('  <text x="%d" y="%d" font-size="15" font-weight="600" text-anchor="middle" '
                   'fill="%s">%s</text>' % (x + NODE_W // 2, y + 38, st["text"], esc(node["label"])))
        if node.get("sub"):
            out.append('  <text x="%d" y="%d" font-size="12" text-anchor="middle" fill="%s">%s</text>'
                       % (x + NODE_W // 2, y + 60, st["muted"], esc(node["sub"])))
    if spec.get("legend"):
        lx, ly = width - 216, height - LEGEND_H
        out.append('  <rect x="%d" y="%d" width="176" height="72" rx="6" fill="none" stroke="%s"/>'
                   % (lx, ly, st["group_stroke"]))
        out.append('  <text x="%d" y="%d" font-size="11" font-weight="600" fill="%s">图例</text>'
                   % (lx + 10, ly + 18, st["text"]))
        for i, kind in enumerate(["primary", "control", "async", "write"]):
            yy = ly + 34 + i * 9
            ai = EDGE_KINDS[kind][0]
            out.append('  <line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5"/>'
                       % (lx + 10, yy, lx + 34, yy, accents[ai % len(accents)]))
            out.append('  <text x="%d" y="%d" font-size="10" fill="%s">%s</text>'
                       % (lx + 40, yy + 3, st["muted"], kind))
    out.append('</svg>')
    return "\n".join(out) + "\n", width, height


def rasterize(svg_path, png_path, width):
    """按可用渲染后端导出 PNG；全部缺失时保持 SVG 交付并提示降级。"""
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-w", str(width), svg_path, "-o", png_path], check=True)
        return "rsvg-convert"
    try:
        import cairosvg  # noqa: F401
        cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=width)
        return "cairosvg"
    except Exception:
        pass
    if shutil.which("inkscape"):
        subprocess.run(["inkscape", svg_path, "-w", str(width), "-o", png_path], check=True)
        return "inkscape"
    if shutil.which("convert"):
        subprocess.run(["convert", "-density", "144", svg_path, png_path], check=True)
        return "imagemagick"
    print("[降级] 未检测到 rsvg-convert / cairosvg / inkscape / convert，仅交付 SVG。")
    return None


def main():
    ap = argparse.ArgumentParser(description="技术图渲染器：JSON 规格 → SVG → PNG")
    ap.add_argument("--spec", help="规格 JSON 路径")
    ap.add_argument("--demo", action="store_true", help="使用内置演示规格")
    ap.add_argument("--out", required=True, help="输出 SVG 路径")
    ap.add_argument("--style", default="1", choices=sorted(STYLES), help="风格编号 1-7")
    ap.add_argument("--width", type=int, default=1920, help="PNG 宽度像素，默认 1920")
    ap.add_argument("--png", action="store_true", help="同时导出 PNG")
    ap.add_argument("--no-png", action="store_true", help="只出 SVG，不导出 PNG")
    args = ap.parse_args()

    if args.demo:
        spec = demo_spec()
    elif args.spec:
        try:
            spec = load_spec(args.spec)
        except (OSError, ValueError) as exc:
            print("[失败] 规格非法：%s" % exc, file=sys.stderr)
            return 1
    else:
        print("[失败] 需要 --spec 或 --demo 之一", file=sys.stderr)
        return 1

    svg, w, h = build_svg(spec, args.style)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    try:
        ET.parse(args.out)
    except ET.ParseError as exc:
        print("[失败] SVG 语法校验不通过：%s" % exc, file=sys.stderr)
        return 2
    print("[通过] SVG 语法校验 OK  %s  (%dx%d, style %s / %s)"
          % (args.out, w, h, args.style, STYLES[args.style]["name"]))

    if args.png:
        png_path = os.path.splitext(args.out)[0] + ".png"
        backend = rasterize(args.out, png_path, args.width)
        if backend and os.path.exists(png_path) and os.path.getsize(png_path) > 0:
            print("[通过] PNG 导出 OK  %s  (%s, %dpx)" % (png_path, backend, args.width))
        else:
            print("[降级] PNG 未生成，SVG 仍为有效交付物。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
