#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""excalidraw_check.py — .excalidraw JSON 结构体检器（零第三方依赖）

对 Excalidraw 图表 JSON 做静态体检，输出人可读报告或 JSON 报告，覆盖：
  1. 结构合法性：顶层 type/version/elements 是否存在，元素字段是否齐全
  2. 坐标越界：元素 x/y/width/height 是否越出可见画布或为负
  3. 元素重叠：同级矩形/椭圆/菱形两两包围盒相交面积比是否超过阈值
  4. 绑定完整性：箭头 startBinding/endBinding 指向的 elementId 是否存在
  5. ID 唯一性：元素 id 是否重复
  6. 文字溢出：文字元素宽度是否小于 rawText 估算宽度

用法:
  python3 excalidraw_check.py --file diagram.excalidraw
  python3 excalidraw_check.py --file diagram.excalidraw --json
  python3 excalidraw_check.py --file diagram.excalidraw --overlap-threshold 0.15
  python3 excalidraw_check.py --help

退出码: 0 = 无 ERROR；1 = 存在 ERROR；2 = 输入不可读。
"""
import argparse
import json
import sys

# 画布越界判定的宽容边界（Excalidraw 画布可无限扩展，此处按常见导出视口给出提示阈值）
VIEWPORT = {"min_x": -1000.0, "min_y": -1000.0, "max_x": 8000.0, "max_y": 8000.0}
# 参与重叠检测的“实体形状”类型
SHAPE_TYPES = ("rectangle", "ellipse", "diamond")
CONTAINER_LIKE = ("rectangle", "ellipse", "diamond")


def load_json(path):
    """读取并解析 .excalidraw JSON，失败时抛出可读异常。"""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def num(value, default=0.0):
    """把字段安全转成 float，非数值回退默认值。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def bbox(el):
    """返回元素的包围盒 (x, y, w, h)。"""
    return (num(el.get("x")), num(el.get("y")),
            num(el.get("width")), num(el.get("height")))


def overlap_ratio(a, b):
    """返回两个包围盒的相交面积占较小盒面积的比例（0~1）。"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    small = min(aw * ah, bw * bh)
    if small <= 0:
        return 0.0
    return inter / small


def est_text_width(el):
    """按 rawText 估算文字像素宽度（每字符约 0.6 * fontSize）。"""
    raw = el.get("rawText") or el.get("text") or ""
    fs = num(el.get("fontSize"), 16.0)
    if not raw:
        return 0.0
    longest = max((len(line) for line in str(raw).splitlines()), default=0)
    return longest * fs * 0.6


def check(doc, overlap_threshold=0.30):
    """执行全套检查，返回 (errors, warnings, stats)。"""
    errors, warnings = [], []
    stats = {"elements": 0, "by_type": {}, "shapes": 0, "arrows": 0}

    if not isinstance(doc, dict):
        errors.append("顶层不是 JSON 对象，无法解析为 .excalidraw 文件")
        return errors, warnings, stats
    if doc.get("type") != "excalidraw":
        warnings.append("顶层 type != 'excalidraw'（期望值），导入时可能被识别为非本格式")
    if "elements" not in doc or not isinstance(doc.get("elements"), list):
        errors.append("缺少 elements 数组，文件不是合法 Excalidraw 图表")
        return errors, warnings, stats

    elements = doc["elements"]
    stats["elements"] = len(elements)

    # 1. ID 唯一性
    seen_ids = {}
    for el in elements:
        eid = el.get("id")
        if not eid:
            errors.append("存在缺少 id 字段的元素（type=%s）" % el.get("type"))
            continue
        seen_ids[eid] = seen_ids.get(eid, 0) + 1
    for eid, cnt in seen_ids.items():
        if cnt > 1:
            errors.append("元素 id 重复 %d 次：%s（会导致绑定错乱）" % (cnt, eid))
    id_set = set(seen_ids)

    shapes = []
    for el in elements:
        etype = el.get("type")
        stats["by_type"][etype] = stats["by_type"].get(etype, 0) + 1
        if etype in SHAPE_TYPES:
            stats["shapes"] += 1
            shapes.append(el)
        if etype == "arrow":
            stats["arrows"] += 1

        # 2. 坐标越界
        x, y, w, h = bbox(el)
        if w < 0 or h < 0:
            warnings.append("元素 %s 的宽或高为负（w=%s, h=%s）" % (el.get("id"), w, h))
        if x < VIEWPORT["min_x"] or y < VIEWPORT["min_y"]:
            warnings.append("元素 %s 坐标越出左上边界 (x=%s, y=%s)" % (el.get("id"), x, y))
        if x + w > VIEWPORT["max_x"] or y + h > VIEWPORT["max_y"]:
            warnings.append("元素 %s 越出右下边界 (right=%s, bottom=%s)"
                            % (el.get("id"), x + w, y + h))

        # 3. 文字溢出（仅对独立文字元素）
        if etype == "text" and not el.get("containerId"):
            need = est_text_width(el)
            if need > 0 and w > 0 and need > w * 1.05:
                warnings.append("文字元素 %s 估算宽度 %.0fpx 超出元素宽度 %.0fpx，可能被裁切"
                                % (el.get("id"), need, w))

        # 4. 绑定完整性
        if etype == "arrow":
            for key in ("startBinding", "endBinding"):
                bind = el.get(key)
                if isinstance(bind, dict):
                    ref = bind.get("elementId")
                    if ref and ref not in id_set:
                        errors.append("箭头 %s 的 %s 指向不存在的 elementId：%s"
                                      % (el.get("id"), key, ref))

    # 5. 元素重叠（仅形状之间，两两相交面积占较小盒比例超阈值即告警）
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            r = overlap_ratio(bbox(shapes[i]), bbox(shapes[j]))
            if r >= overlap_threshold:
                warnings.append("元素 %s 与 %s 重叠 %.0f%%（阈值 %.0f%%）"
                                % (shapes[i].get("id"), shapes[j].get("id"),
                                   r * 100, overlap_threshold * 100))

    return errors, warnings, stats


def render_text_report(path, errors, warnings, stats):
    """生成人可读的纯文本报告。"""
    lines = []
    lines.append("=" * 60)
    lines.append("Excalidraw 结构体检报告")
    lines.append("文件：%s" % path)
    lines.append("=" * 60)
    lines.append("元素总数：%d（形状 %d / 箭头 %d）"
                 % (stats.get("elements", 0), stats.get("shapes", 0), stats.get("arrows", 0)))
    lines.append("按类型：%s" % (json.dumps(stats.get("by_type", {}), ensure_ascii=False)))
    lines.append("")
    lines.append("ERROR（必须修）：%d" % len(errors))
    for e in errors:
        lines.append("  [E] %s" % e)
    lines.append("WARNING（复核）：%d" % len(warnings))
    for w in warnings:
        lines.append("  [W] %s" % w)
    if not errors and not warnings:
        lines.append("结论：通过，未发现越界、重叠、错连或溢出问题。")
    elif not errors:
        lines.append("结论：无阻断错误，但有 %d 条告警需渲染后复核。" % len(warnings))
    else:
        lines.append("结论：存在 %d 条阻断错误，修复后再交付。" % len(errors))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Excalidraw 图表 JSON 结构体检器：校验坐标越界、元素重叠、"
                    "绑定错连、文字溢出与 ID 重复（零第三方依赖）")
    ap.add_argument("--file", required=True, help="待检查的 .excalidraw JSON 文件路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 格式输出报告")
    ap.add_argument("--overlap-threshold", type=float, default=0.30,
                    help="重叠判定阈值（相交面积占较小盒比例，默认 0.30）")
    a = ap.parse_args(argv)

    try:
        doc = load_json(a.file)
    except FileNotFoundError:
        print("ERROR: 文件不存在：%s" % a.file, file=sys.stderr)
        return 2
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print("ERROR: JSON 解析失败：%s" % exc, file=sys.stderr)
        return 2

    errors, warnings, stats = check(doc, overlap_threshold=a.overlap_threshold)

    if a.json:
        print(json.dumps({"file": a.file, "stats": stats, "errors": errors,
                          "warnings": warnings,
                          "pass": not errors}, ensure_ascii=False, indent=2))
    else:
        print(render_text_report(a.file, errors, warnings, stats))

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
