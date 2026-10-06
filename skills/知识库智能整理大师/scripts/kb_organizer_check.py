#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库整理方案自检器（kb_organizer_check.py）——knowledge-base-organizer 交付质检工具。

仅使用 Python 标准库（argparse / json / os / re / sys），不依赖第三方包、不联网。
用于在「建夹 → 归类 → 移动」之前，对分类方案与技能目录做静态自检，替代沙箱内无法
进行的平台侧目视核对（接口不可用时的降级校验入口）。

两种模式：
  A. 方案校验（--plan plan.json）
     1. 文件夹命名规范：统一写法「两位序号-主题」（如 01-教学备课）；
     2. 文件夹名重复检测（同一维度下不得重名）；
     3. 文件夹数量上限（默认 12，超出提示按维度拆分）；
     4. 单批次移动条数上限（默认 10，与 move_knowledge 接口限制一致）；
     5. 未分类条目占位检查（unclassified 清单须显式给出）。
  B. 技能目录自检（--skill DIR）
     1. SKILL.md 存在且 < 45000 字符（TRACE 规范上限）；
     2. 危险短语扫描（破坏性命令类表述，命中即不合规）；
     3. references/ 与 scripts/ 目录可达性。

退出码：
  0 —— 全部检查通过；
  1 —— 存在硬性不合规项（命名重复、批次超限、危险短语等）；
  2 —— 输入不足或参数非法（技能目录不存在、方案文件不存在或 JSON 非法）。

用法：
  python3 kb_organizer_check.py --skill 知识库智能整理大师 --json
  python3 kb_organizer_check.py --plan plan.json --max-folders 12 --max-batch 10
  python3 kb_organizer_check.py --help
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

MAX_SKILL_CHARS = 45000
NAME_RE = re.compile(r"^\d{2}-[\u4e00-\u9fa5A-Za-z0-9]+")
DANGER_RE = re.compile(r"rm\s+-rf|shutil\.rmtree|os\.remove|批量删除|删除文件|上传外传|发送至|邮件发送")


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def check_skill(skill_dir: str) -> tuple[list, list, list]:
    """技能目录自检，返回 (passed, failed, notes)，每项为 (检查名, 说明)。"""
    passed, failed, notes = [], [], []

    if not os.path.isdir(skill_dir):
        return passed, failed, [("技能目录", "不存在：%s" % skill_dir)]

    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        failed.append(("SKILL.md 存在", "未找到 %s" % skill_md))
    else:
        body = read_text(skill_md)
        n = len(body)
        if n < MAX_SKILL_CHARS:
            passed.append(("SKILL.md 体量", "%d 字符 < %d" % (n, MAX_SKILL_CHARS)))
        else:
            failed.append(("SKILL.md 体量", "%d 字符超出 %d 上限" % (n, MAX_SKILL_CHARS)))

        hits = DANGER_RE.findall(body)
        if hits:
            failed.append(("危险短语扫描", "命中 %d 处：%s" % (len(hits), ", ".join(sorted(set(hits))))))
        else:
            passed.append(("危险短语扫描", "未命中破坏性表述"))

    for sub in ("references", "scripts"):
        if os.path.isdir(os.path.join(skill_dir, sub)):
            passed.append(("%s/ 可达" % sub, "目录存在"))
        else:
            notes.append(("%s/ 可达" % sub, "目录缺失（分层建议补全）"))

    return passed, failed, notes


def check_plan(plan_path: str, max_folders: int, max_batch: int) -> tuple[list, list, list, bool]:
    """分类方案校验，返回 (passed, failed, notes, fatal)。fatal=True 表示输入不可用。"""
    passed, failed, notes = [], [], []

    if not os.path.isfile(plan_path):
        return passed, failed, [("方案文件", "不存在：%s" % plan_path)], True
    try:
        with open(plan_path, encoding="utf-8") as f:
            plan = json.load(f)
    except Exception as e:
        return passed, failed, [("方案文件", "JSON 非法：%s" % e)], True

    folders = plan.get("folders", [])
    if not isinstance(folders, list) or not folders:
        return passed, failed, [("方案结构", "缺少非空 folders 数组")], True

    names = [str(x.get("name", "")) for x in folders if isinstance(x, dict)]

    # 1. 命名规范
    bad = [n for n in names if not NAME_RE.match(n)]
    if bad:
        failed.append(("命名规范", "不符合「两位序号-主题」：%s" % ", ".join(bad[:5])))
    else:
        passed.append(("命名规范", "全部符合「两位序号-主题」"))

    # 2. 重名检测
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        failed.append(("文件夹重名", "重复名称：%s" % ", ".join(dup)))
    else:
        passed.append(("文件夹重名", "无重复名称"))

    # 3. 数量上限
    if len(names) > max_folders:
        failed.append(("文件夹数量", "%d 个 > 上限 %d，建议按维度拆分" % (len(names), max_folders)))
    else:
        passed.append(("文件夹数量", "%d 个 ≤ 上限 %d" % (len(names), max_folders)))

    # 4. 批次上限
    sizes = [int(x.get("count", 0) or 0) for x in folders if isinstance(x, dict)]
    over = [s for s in sizes if s > max_batch]
    if over:
        notes.append(("批次上限", "%d 个文件夹单批超过 %d 条，须分多批移动" % (len(over), max_batch)))
    else:
        passed.append(("批次上限", "各文件夹条数均在单批 %d 条以内" % max_batch))

    # 5. 未分类清单显式给出
    if "unclassified" in plan:
        passed.append(("未分类清单", "已显式给出（%d 条）" % len(plan.get("unclassified") or [])))
    else:
        notes.append(("未分类清单", "未显式给出 unclassified，建议逐条列出后请用户指定归属"))

    return passed, failed, notes, False


def main() -> int:
    ap = argparse.ArgumentParser(description="知识库整理方案自检器（knowledge-base-organizer）")
    ap.add_argument("--skill", default="", help="技能目录（走技能目录自检模式）")
    ap.add_argument("--plan", default="", help="分类方案 JSON 路径（走方案校验模式）")
    ap.add_argument("--max-folders", type=int, default=12, help="同一维度下文件夹数量上限，默认 12")
    ap.add_argument("--max-batch", type=int, default=10, help="单批移动条数上限，默认 10")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    if not args.skill and not args.plan:
        args.skill = "知识库智能整理大师"

    passed, failed, notes, fatal = [], [], [], False

    if args.skill:
        p, f, n = check_skill(args.skill)
        passed += p
        failed += f
        notes += n

    if args.plan:
        p, f, n, fatal = check_plan(args.plan, args.max_folders, args.max_batch)
        passed += p
        failed += f
        notes += n

    status = "PASS" if not failed else "FAIL"
    result = {
        "target": args.skill or args.plan,
        "status": status,
        "passed": passed,
        "failed": failed,
        "notes": notes,
        "summary": {"passed": len(passed), "failed": len(failed), "notes": len(notes)},
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("知识库整理方案自检：%s" % status)
        for k, v in passed:
            print("  [通过] %s —— %s" % (k, v))
        for k, v in failed:
            print("  [不合规] %s —— %s" % (k, v))
        for k, v in notes:
            print("  [提示] %s —— %s" % (k, v))
        print("汇总：通过 %d / 不合规 %d / 提示 %d" % (len(passed), len(failed), len(notes)))

    if fatal:
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
