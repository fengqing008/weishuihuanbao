#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lineart_check.py —— 手绘线稿插图交付自检器（仅标准库）

对「配图清单 JSON」做交付前门禁自检：母题合法性、风格与配色一致性、
尺寸与 role 匹配、seed 可复现性、文件是否落盘、是否符合米白纸实底口径。

用法：
  python3 scripts/lineart_check.py --manifest images/auto_images.json
  python3 scripts/lineart_check.py --manifest out.json --strict --json
  python3 scripts/lineart_check.py --self-test

退出码：0 = 全部通过；1 = 检出问题（含失败分支提示）；2 = 调用参数或文件异常。
"""
import argparse
import json
import os
import sys

SYMBOL_MOTIFS = ["leaf", "sprout", "mountain", "window", "lamp", "book", "bird",
                 "cloud", "moon", "ripple", "boat", "pattern", "tea", "bridge",
                 "star", "home"]
SCENE_MOTIFS = ["steps3", "desk", "meeting", "interview", "plant", "blueprint",
                "lab", "checklist", "contract", "scales", "letter", "archive",
                "health", "family", "move", "handover"]
MOTIFS = set(SYMBOL_MOTIFS + SCENE_MOTIFS)
PALETTES = {"sepia", "ochre", "warmgold", "terracotta", "rosewood",
            "warmolive", "ink"}
STYLES = {"fountain", "pencil", "brush", "marker", "charcoal"}
ROLE_SIZE = {"wide": (1500, 820), "inline": (760, 980), "inline-end": (760, 980)}

RULES = [
    ("R1", "母题须在 32 母题库内（非法母题无法渲染，属失败分支）"),
    ("R2", "同批图必须同笔触同配色（跨篇换色破坏整册观感）"),
    ("R3", "role 与尺寸须匹配（wide 1500×820 / inline 760×980）"),
    ("R4", "交付版须有固定 seed，保证可复现（同种子逐像素一致）"),
    ("R5", "清单指向的图片文件应已落盘，缺位要能走兜底通道补位"),
]


def _iter_items(data):
    """兼容两种清单形态：{order: [ {..} ]} 或 [ {..} ]。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, list):
                for it in val:
                    if isinstance(it, dict):
                        yield it
    return


def check(manifest_path, strict=False):
    problems = []
    warn = []
    notes = []
    if not os.path.isfile(manifest_path):
        return ["清单文件不存在或不可读：" + manifest_path], [], ["请先批量出图生成清单，再执行自检"]
    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # 异常：JSON 解析失败属错误处理分支
        return ["清单 JSON 解析异常：" + str(exc)], [], ["修复 JSON 后重试；不可解析时回退到单张 --motif 直出"]

    items = list(_iter_items(data))
    if not items:
        return ["清单内未检出任何配图条目（空清单视为失败）"], [], ["核对清单结构 articles/order 字段"]

    palettes = set()
    styles = set()
    base = os.path.dirname(os.path.abspath(manifest_path))
    for idx, it in enumerate(items, 1):
        tag = "条目#%d" % idx
        motif = it.get("motif")
        role = it.get("role", "wide")
        if motif not in MOTIFS:
            problems.append("%s 母题非法：%r（R1）" % (tag, motif))
        if it.get("palette"):
            palettes.add(it["palette"])
        if it.get("style"):
            styles.add(it["style"])
        if it.get("palette") and it["palette"] not in PALETTES:
            problems.append("%s 配色不在 7 套配色内：%r" % (tag, it["palette"]))
        if it.get("style") and it["style"] not in STYLES:
            problems.append("%s 笔触不在 5 档笔触内：%r" % (tag, it["style"]))
        size = it.get("size")
        if role in ROLE_SIZE and size:
            try:
                w, h = [int(x) for x in (size if isinstance(size, (list, tuple)) else str(size).lower().split("x"))]
                if (w, h) != ROLE_SIZE[role]:
                    problems.append("%s role=%s 尺寸 %dx%d 与契约 %dx%d 不符（R3）"
                                    % (tag, role, w, h, ROLE_SIZE[role][0], ROLE_SIZE[role][1]))
            except Exception:
                warn.append("%s size 字段无法解析：%r（容错：跳过尺寸校验）" % (tag, size))
        if it.get("seed") in (None, ""):
            warn.append("%s 未记录 seed，交付版不可复现（R4）" % tag)
        fpath = it.get("file") or it.get("path")
        if fpath:
            full = fpath if os.path.isabs(fpath) else os.path.join(base, fpath)
            if not os.path.isfile(full):
                warn.append("%s 图片缺位：%s（触发兜底通道：程序化引擎补位）" % (tag, fpath))
            else:
                try:
                    if os.path.getsize(full) <= 0:
                        problems.append("%s 图片字节数为 0，非有效产物：%s" % (tag, fpath))
                except Exception:
                    warn.append("%s 文件尺寸读取异常：%s（补救：重跑该张）" % (tag, fpath))
        else:
            warn.append("%s 未记录 file 字段，无法核对落盘" % tag)

    if len(palettes) > 1:
        problems.append("同批出现多套配色 %s（R2：整册须锁定单一配色）" % sorted(palettes))
    if len(styles) > 1:
        problems.append("同批出现多种笔触 %s（R2：整册须锁定单一笔触）" % sorted(styles))
    notes.append("已核对条目 %d 条；配色 %s；笔触 %s" % (len(items), sorted(palettes) or "未记录", sorted(styles) or "未记录"))
    if strict:
        problems.extend(warn)
        warn = []
    return problems, warn, notes


def self_test():
    import tempfile
    ok = True
    good = {"order": [{"file": __file__, "motif": "lamp", "role": "inline",
                       "size": [760, 980], "palette": "sepia", "style": "pencil", "seed": 2026}]}
    bad = {"order": [{"file": "nope.png", "motif": "unicorn", "role": "wide",
                      "size": [800, 600], "palette": "neon", "style": "crayon"}]}
    tmp = tempfile.mkdtemp()
    p1 = os.path.join(tmp, "good.json")
    p2 = os.path.join(tmp, "bad.json")
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(good, f)
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(bad, f)
    probs_ok, _, _ = check(p1)
    probs_bad, _, _ = check(p2)
    print("[自检] 合规清单问题数 =", len(probs_ok), "(期望 0)")
    print("[自检] 违规清单问题数 =", len(probs_bad), "(期望 >0)")
    if probs_ok:
        ok = False
    if not probs_bad:
        ok = False
    print("[自检] 结果：", "通过" if ok else "未通过")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="手绘线稿插图交付自检器（R1–R5 门禁；仅标准库）",
        epilog="退出码：0 通过 / 1 检出问题 / 2 参数异常")
    ap.add_argument("--manifest", help="配图清单 JSON 路径")
    ap.add_argument("--strict", action="store_true", help="严格模式：警告一并计为问题")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结论")
    ap.add_argument("--self-test", action="store_true", help="内置自检（不读外部文件）")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.manifest:
        print("错误：需指定 --manifest，或使用 --self-test。", file=sys.stderr)
        return 2

    problems, warn, notes = check(args.manifest, args.strict)
    if args.json:
        print(json.dumps({"manifest": args.manifest, "problems": problems,
                          "warnings": warn, "notes": notes,
                          "verdict": "pass" if not problems else "fail"},
                         ensure_ascii=False, indent=2))
    else:
        print("== 线稿配图交付自检 ==")
        print("清单：", args.manifest)
        for n in notes:
            print("  ·", n)
        for w in warn:
            print("  [警告]", w)
        for p in problems:
            print("  [问题]", p)
        print("门禁规则：")
        for code, desc in RULES:
            print("  %s %s" % (code, desc))
        print("结论：", "通过" if not problems else "未通过（先按提示补救后重跑，不必整批重出）")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
