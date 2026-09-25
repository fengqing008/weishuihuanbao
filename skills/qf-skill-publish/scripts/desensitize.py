#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脱敏替换工具（可复用）

用法：
    # 1. 生成词表模板
    python3 desensitize.py --init-rules rules.json

    # 2. 编辑 rules.json，填入自己的敏感词与代称

    # 3. 预演（不落盘，先看会改什么）
    python3 desensitize.py --dir ./skills --rules rules.json --dry-run

    # 4. 正式执行
    python3 desensitize.py --dir ./skills --rules rules.json

rules.json 格式：
{
  "rules": [
    ["完整企业全称", "某水务项目公司"],
    ["企业简称", "某环保上市公司"],
    ["项目地名", "某市"]
  ],
  "post_fix": [
    ["某市某水务集团", "某水务集团"]
  ],
  "extensions": [".md", ".py", ".json", ".txt", ".sh", ".js", ".cjs", ".html"],
  "exclude_dirs": [".git", "__pycache__", "node_modules", ".venv"]
}

要点：
  - rules 会按字符串长度降序自动重排，避免长串被短串先吃掉。
  - post_fix 用于清理替换后的重复修饰语，在 rules 之后应用。
  - 建议先 --dry-run 预演，确认命中位置无误再正式执行。
"""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_EXTS = [".md", ".py", ".json", ".txt", ".sh", ".js", ".cjs", ".html"]
DEFAULT_EXCLUDE = [".git", "__pycache__", "node_modules", ".venv", "dist", "build"]

TEMPLATE = {
    "rules": [
        ["【最长】完整企业全称", "某项目公司"],
        ["【次长】企业简称", "某环保上市公司"],
        ["【次长】关联企业简称", "某水务集团"],
        ["【次长】央国企联合体", "某央企环境集团"],
        ["本项目名称", "示例PPP"],
        ["项目地名", "某市"],
        ["招标编号格式示例", "招标编号略"],
        ["个人姓名", "编制人"],
        ["内部知识库ID完整串", ""]
    ],
    "post_fix": [
        ["某市某水务集团", "某水务集团"],
        ["某市某市", "某市"],
        ["某县某县", "某县"],
        ["某区某区", "某区"]
    ],
    "extensions": DEFAULT_EXTS,
    "exclude_dirs": DEFAULT_EXCLUDE
}


def load_rules(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rules = [(a, b) for a, b in data.get("rules", []) if a and a != b]
    # 长度降序：长串优先，避免子串冲突
    rules.sort(key=lambda x: -len(x[0]))
    post = [(a, b) for a, b in data.get("post_fix", []) if a and a != b]
    exts = data.get("extensions") or DEFAULT_EXTS
    excl = set(data.get("exclude_dirs") or DEFAULT_EXCLUDE)
    return rules, post, [e.lower() for e in exts], excl


def iter_files(root: Path, exts, excl):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in excl for part in p.parts):
            continue
        if p.suffix.lower() not in exts:
            continue
        yield p


def main():
    ap = argparse.ArgumentParser(description="脱敏替换工具")
    ap.add_argument("--dir", help="待处理目录")
    ap.add_argument("--rules", help="词表 JSON 路径")
    ap.add_argument("--init-rules", help="生成词表模板到指定路径后退出")
    ap.add_argument("--dry-run", action="store_true", help="只报告命中，不写盘")
    args = ap.parse_args()

    if args.init_rules:
        out = Path(args.init_rules)
        out.write_text(json.dumps(TEMPLATE, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已生成词表模板：{out}")
        print("请编辑该文件，填入实际敏感词与代称后重新运行。")
        return 0

    if not args.dir or not args.rules:
        ap.error("需要 --dir 与 --rules（或使用 --init-rules 生成模板）")

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"✗ 目录不存在：{root}", file=sys.stderr)
        return 1
    rule_path = Path(args.rules)
    if not rule_path.is_file():
        print(f"✗ 词表不存在：{rule_path}", file=sys.stderr)
        return 1

    rules, post, exts, excl = load_rules(rule_path)

    # 自检：检测规则内部的子串冲突
    print(f"规则数：{len(rules)}（已按长度降序重排）｜后置修正：{len(post)}")
    warnings = []
    for i, (a, _) in enumerate(rules):
        for b, _ in rules[i + 1:]:
            if a and b and b in a:
                warnings.append(f"  ⚠️ 「{b}」是「{a}」的子串——已按长度优先处理，确认代称一致即可")
    if warnings:
        print("子串关系提示：")
        for w in warnings[:10]:
            print(w)
    print()

    total, touched, hits = 0, [], []
    for p in iter_files(root, exts, excl):
        try:
            src = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        out, n, detail = src, 0, []
        for old, new in rules + post:
            c = out.count(old)
            if c:
                out = out.replace(old, new)
                n += c
                detail.append(f"{old}→{new}×{c}")
        if n:
            rel = p.relative_to(root)
            touched.append((rel, n))
            hits.append((rel, detail))
            total += n
            if not args.dry_run:
                p.write_text(out, encoding="utf-8")

    mode = "【预演模式】未写盘" if args.dry_run else "已写入"
    print(f"{mode}｜共替换 {total} 处，涉及 {len(touched)} 个文件\n")
    for rel, n in touched:
        print(f"  {n:3d}  {rel}")
    if args.dry_run and hits:
        print("\n--- 命中明细 ---")
        for rel, detail in hits:
            print(f"\n{rel}")
            for d in detail:
                print("   ", d)
        print("\n确认无误后，去掉 --dry-run 重新运行即可落盘。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
