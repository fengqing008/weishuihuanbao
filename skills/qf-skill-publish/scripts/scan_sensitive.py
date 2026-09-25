#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描工具：按多维度排查仓库中的敏感信息，输出报告。

用法：
    # 用默认通用维度扫描
    python3 scan_sensitive.py --dir ./skills

    # 追加自定义词表（企业名、项目地名等）
    python3 scan_sensitive.py --dir ./skills --words words.txt

    # 输出 JSON 报告
    python3 scan_sensitive.py --dir ./skills --json report.json

words.txt 每行一个敏感词，# 开头为注释。

检查维度：
    1. 自定义词表（企业名 / 项目地名 / 人名）
    2. 密钥凭证（API Key、Token、私钥）
    3. 本地绝对路径与系统用户名
    4. 内部平台域名
    5. 内部知识库 ID
    6. 内部台账文件名（含日期戳、内部命名）
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_EXTS = {".md", ".py", ".json", ".txt", ".sh", ".js", ".cjs", ".html",
                ".yml", ".yaml", ".toml", ".ini", ".cfg", ".env"}
DEFAULT_EXCLUDE = {".git", "__pycache__", "node_modules", ".venv", "dist", "build"}

# 通用维度：正则 -> 维度名
PATTERNS = [
    ("密钥凭证", re.compile(
        r"(sk-[A-Za-z0-9]{20,}"
        r"|ghp_[A-Za-z0-9]{20,}"
        r"|github_pat_[A-Za-z0-9_]{20,}"
        r"|AKIA[0-9A-Z]{16}"
        r"|-----BEGIN[A-Z ]*PRIVATE KEY-----"
        r"|(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*[\"'][^\"'\s]{16,}[\"'])", re.I)),
    ("本地绝对路径", re.compile(
        r"(/Users/[A-Za-z0-9._\-]+"
        r"|/home/[A-Za-z0-9._\-]+"
        r"|[A-Z]:\\Users\\[A-Za-z0-9._\-]+"
        r"|/var/folders/[A-Za-z0-9._\-/]+)")),
    ("内部平台域名", re.compile(
        r"[a-z0-9\-]+\.(?:woa|oa|tapd|iwiki|internal|local|corp)\.[a-z]+", re.I)),
    ("内部知识库ID", re.compile(r"(kb_id|knowledge_base_id|space_id)\s*[:=]\s*[A-Za-z0-9_\-=]{16,}", re.I)),
    ("疑似内部台账文件名", re.compile(r"[\u4e00-\u9fa5A-Za-z0-9_\-]{4,}_\d{12,}\.(docx?|xlsx?|pdf)", re.I)),
    ("疑似内网IP", re.compile(r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b")),
]


def load_words(path: Path | None):
    if not path:
        return []
    if not path.is_file():
        print(f"✗ 词表不存在：{path}", file=sys.stderr)
        sys.exit(1)
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.append(line)
    return sorted(set(words), key=len, reverse=True)


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
    ap = argparse.ArgumentParser(description="敏感信息扫描工具")
    ap.add_argument("--dir", required=True, help="待扫描目录")
    ap.add_argument("--words", help="自定义敏感词表（每行一个）")
    ap.add_argument("--json", help="输出 JSON 报告路径")
    ap.add_argument("--quiet", action="store_true", help="仅输出汇总")
    args = ap.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"✗ 目录不存在：{root}", file=sys.stderr)
        return 1

    words = load_words(Path(args.words) if args.words else None)
    if words:
        PATTERNS.insert(0, ("自定义词表", re.compile("|".join(re.escape(w) for w in words))))

    findings = {}
    scanned = 0
    for p in iter_files(root, DEFAULT_EXTS, DEFAULT_EXCLUDE):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        lines = text.split("\n")
        for dim, pat in PATTERNS:
            for i, line in enumerate(lines, 1):
                for m in pat.finditer(line):
                    findings.setdefault(dim, []).append({
                        "file": str(p.relative_to(root)),
                        "line": i,
                        "match": m.group(0)[:120],
                    })

    print(f"扫描文件：{scanned} 个｜目录：{root}")
    if words:
        print(f"自定义词表：{len(words)} 个词")
    print()

    if not findings:
        print("✅ 未发现敏感信息")
    else:
        print("发现问题：\n")
        for dim, items in findings.items():
            print(f"【{dim}】{len(items)} 处")
            if not args.quiet:
                seen = set()
                for it in items[:30]:
                    key = (it["file"], it["line"])
                    if key in seen:
                        continue
                    seen.add(key)
                    print(f"  {it['file']}:{it['line']}  ->  {it['match']}")
                if len(items) > 30:
                    print(f"  ... 另有 {len(items) - 30} 处")
            print()

    if args.json:
        out = Path(args.json)
        summary = {k: len(v) for k, v in findings.items()}
        out.write_text(json.dumps(
            {"dir": str(root), "scanned": scanned, "summary": summary, "findings": findings},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON 报告已写入：{out}")

    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())
