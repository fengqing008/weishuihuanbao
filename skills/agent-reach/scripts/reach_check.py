#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reach_check.py — agent-reach 交付前门禁自检（仅用 Python 标准库）

检查项：
  1) 技能结构：SKILL.md / references / scripts 齐备；
  2) frontmatter：name / version / description（英文触发词）齐备；
  3) 红线纪律：SKILL.md 不得出现破坏性短语；
  4) 体积门禁：SKILL.md 字符数 < 45000；
  5) 路由完整性：七分类 references（search/social/career/dev/web/video/finance）存在；
  6) 案例库：references/case-library.md 含 ≥3 个案例；
  7) 14 个降级/容错关键词是否齐备。

退出码：0=全部通过；1=存在警告级问题；2=存在阻断级问题。
用法：python3 reach_check.py --skill agent-reach [--strict]
"""
import argparse
import os
import re
import sys

DANGER = ["rm" + " -rf", "shutil" + ".rmtree", "os" + ".remove",
          "批量" + "删除", "删除" + "文件", "上传" + "外传", "发送" + "至", "邮件" + "发送"]
FAIL_WORDS = ["失败模式", "fallback", "回退", "重试", "降级", "兜底", "异常",
              "错误处理", "失败分支", "边界条件", "补救", "断点续跑", "容错", "防御"]
ROUTE_DOCS = ["search.md", "social.md", "career.md", "dev.md", "web.md", "video.md", "finance.md"]


def read(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def main():
    ap = argparse.ArgumentParser(description="agent-reach 交付前门禁自检")
    ap.add_argument("--skill", default="agent-reach", help="技能目录")
    ap.add_argument("--strict", action="store_true", help="警告也按阻断处理")
    a = ap.parse_args()

    root = a.skill
    blockers, warnings = [], []
    if not os.path.isdir(root):
        print("[BLOCK] 技能目录不存在：%s" % root)
        return 2

    text = read(os.path.join(root, "SKILL.md"))
    if not text:
        blockers.append("缺 SKILL.md 或不可读")
    for sub in ("scripts", "references"):
        if not os.path.isdir(os.path.join(root, sub)):
            blockers.append("缺 %s/ 目录" % sub)

    fm = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not fm:
        blockers.append("frontmatter 缺失")
    else:
        head = fm.group(1)
        for k in ("name", "version", "description"):
            if not re.search(r"^%s\s*:" % k, head, re.M):
                blockers.append("frontmatter 缺字段：%s" % k)
        if not re.search(r"(English triggers|英文触发|triggers:)", text):
            warnings.append("未见英文触发词声明")

    hit = [d for d in DANGER if d in text]
    if hit:
        blockers.append("出现破坏性短语：%s" % "、".join(hit))

    n = len(text)
    if n >= 45000:
        blockers.append("SKILL.md 超限：%d 字符（上限 45000）" % n)
    else:
        print("[OK] SKILL.md 体积 %d 字符（<45000）" % n)

    miss = [w for w in FAIL_WORDS if w not in text]
    if miss:
        warnings.append("降级关键词缺：%s" % "、".join(miss))

    rdir = os.path.join(root, "references")
    if os.path.isdir(rdir):
        miss_doc = [d for d in ROUTE_DOCS if not os.path.isfile(os.path.join(rdir, d))]
        if miss_doc:
            warnings.append("缺分类文档：%s" % "、".join(miss_doc))
        else:
            print("[OK] 七分类 references 齐备")

    cl = os.path.join(rdir, "case-library.md")
    if not os.path.isfile(cl):
        warnings.append("缺 references/case-library.md")
    else:
        cnt = len(re.findall(r"^##\s*案例", read(cl), re.M))
        if cnt < 3:
            warnings.append("案例库案例数不足：%d（需≥3）" % cnt)

    for b in blockers:
        print("[BLOCK] " + b)
    for w in warnings:
        print("[WARN] " + w)

    if blockers:
        print("结论：{0} 项阻断，{1} 项警告".format(len(blockers), len(warnings)))
        return 2
    if warnings and a.strict:
        print("结论：strict 模式按阻断处理（{0} 项警告）".format(len(warnings)))
        return 2
    if warnings:
        print("结论：通过（{0} 项警告）".format(len(warnings)))
        return 1
    print("结论：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
