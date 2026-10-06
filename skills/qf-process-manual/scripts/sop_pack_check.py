#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sop_pack_check.py —— 工程结算 SOP 交付包自检脚本（仅使用标准库）

用途：对一次结算 SOP 编制作业的交付目录做「四件齐备」与基本健壮性自检——
  · docx（SOP 制度文件）
  · mmd（流程图源）
  · png（流程图位图）
  · html（流程图集/交互页）
  · manifest.json（交付清单）
并检查 manifest 中的 degraded 降级项、空文件、命名规范与残留临时缓存。

用法：
  python3 sop_pack_check.py --dir outputs/某PPP
  python3 sop_pack_check.py --dir outputs/某PPP --json
  python3 sop_pack_check.py --dir . --allow-partial

退出码：
  0 = 四件齐备且无告警；
  1 = 存在告警（如部分缺件、命中降级项、命名不规范）；
  2 = 存在致命错误（目录不存在、交付目录为空、manifest 损坏等）。
"""
import argparse
import json
import os
import re
import sys

PIECES = {".docx": "SOP 制度文件", ".mmd": "流程图源", ".png": "流程图位图",
          ".html": "流程图集/交互页"}
TEMP_PAT = re.compile(r"(\.tmp$|\.bak$|~$|__pycache__)")
NAME_PAT = re.compile(r"^[\w\u4e00-\u9fa5（）()【】\-_.]+$")


def walk_files(root, limit=20000):
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            found.append(os.path.join(base, f))
            if len(found) >= limit:
                return found
    return found


def check(root, allow_partial=False):
    """返回 (exit_code, errors, warnings, info)。"""
    errors, warns, info = [], [], {}
    if not os.path.isdir(root):
        return 2, ["目录不存在或不可读：%s" % root], [], {}
    files = walk_files(root)
    info["file_count"] = len(files)
    if not files:
        return 2, ["交付目录为空，未见任何产物"], [], info

    buckets = {ext: [] for ext in PIECES}
    temps = []
    for p in files:
        ext = os.path.splitext(p)[1].lower()
        if ext in buckets:
            buckets[ext].append(p)
        if TEMP_PAT.search(os.path.basename(p)):
            temps.append(p)
        if os.path.getsize(p) == 0:
            warns.append("空文件（疑似生成失败）：%s" % os.path.relpath(p, root))

    info["pieces"] = {k: len(v) for k, v in buckets.items()}
    missing = [PIECES[e] for e, v in buckets.items() if not v]
    if missing:
        msg = "四件齐备检查未通过，缺件：" + "、".join(missing)
        (warns if allow_partial else errors).append(msg)

    manifest = None
    cand = [p for p in files if os.path.basename(p) == "manifest.json"]
    if not cand:
        warns.append("未找到 manifest.json，无法核对四件齐备标记与降级项")
    else:
        try:
            with open(cand[0], encoding="utf-8") as fh:
                manifest = json.load(fh)
            info["manifest"] = os.path.relpath(cand[0], root)
            deg = manifest.get("degraded") or []
            if deg:
                warns.append("manifest 记录降级项 %d 个：%s"
                             % (len(deg), "、".join(str(d) for d in deg[:5])))
            if manifest.get("four_pieces_complete") is False:
                warns.append("manifest.four_pieces_complete=false，交付需在说明中显式告知")
        except (ValueError, OSError) as exc:
            errors.append("manifest.json 无法解析：%s" % exc)

    if temps:
        warns.append("存在临时/残留缓存 %d 个（建议交付前清理临时缓存、移除残留）：%s"
                     % (len(temps), "、".join(os.path.basename(t) for t in temps[:5])))

    for p in files:
        base = os.path.basename(p)
        if not NAME_PAT.match(base):
            warns.append("命名含非常规字符，建议规范化：%s" % base)

    code = 2 if errors else (1 if warns else 0)
    return code, errors, warns, info


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="工程结算 SOP 交付包自检（四件齐备 + 降级项 + 残留缓存，仅标准库）")
    ap.add_argument("--dir", required=True, help="交付目录路径")
    ap.add_argument("--allow-partial", action="store_true",
                    help="允许部分缺件（此时缺件记为告警而非致命错误）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args(argv)

    code, errors, warns, info = check(args.dir, args.allow_partial)
    if args.json:
        print(json.dumps({"dir": args.dir, "exit": code, "errors": errors,
                          "warnings": warns, "info": info}, ensure_ascii=False))
    else:
        print("[sop_pack_check] %s" % args.dir)
        for k, v in info.get("pieces", {}).items():
            print("  件数 %s (%s)：%d" % (k, PIECES.get(k, k), v))
        for e in errors:
            print("  x 错误：%s" % e)
        for w in warns:
            print("  ! 告警：%s" % w)
        print("  结论：%s" % {0: "通过", 1: "有告警", 2: "有致命错误"}[code])
    return code


if __name__ == "__main__":
    sys.exit(main())
