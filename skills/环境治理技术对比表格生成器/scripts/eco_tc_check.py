#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eco_tc_check.py — 「环境治理技术对比表格生成器」技能结构自检（仅标准库）

用途：核对技术比选表格生成 Skill 的 TRACE 关键要件——标准列完整性、定性口径一致性、
      引用依据（国标/行标全称+编号）、红线声明、能力边界、降级路径与可交付物规范。
用法：
    python3 eco_tc_check.py --help
    python3 eco_tc_check.py --skill 环境治理技术对比表格生成器
    python3 eco_tc_check.py --table 示例表.md --strict   # 可选：校验表格列是否齐备

退出码：0=全部通过；1=存在警告；2=致命错误或用参错误。
"""
import argparse
import os
import re
import sys

FAIL_WORDS = ["失败模式", "fallback", "回退", "重试", "降级", "兜底", "异常", "错误处理",
              "失败分支", "边界条件", "补救", "断点续跑", "容错", "防御"]

REQUIRED_SECTIONS = ["触发条件", "失败模式", "降级路径", "引用依据", "红线声明",
                     "版本沿革", "能力边界", "可交付物", "输出规范", "English triggers"]

# 标准列（13 列并集校验）
STD_COLS = ["技术名称", "目标污染物", "场景适用性", "技术成熟度", "修复效率",
            "建设资金", "运行成本", "系统稳定性", "修复周期", "环境风险", "优点", "缺点"]

DANGER_RE = re.compile(r"rm\s+-rf|shutil\.rmtree|os\.remove|批量删除|删除文件|上传外传|发送至|邮件发送")
STD_RE = re.compile(r"GB\s?/?T?\s?\d{3,}|HJ\s?\d{2,}|CJJ\s?\d+|《[^》]{2,40}》")
MAX_SKILL_CHARS = 45000


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return None


def check_table(table_path):
    """校验用户交付表格是否含标准列，返回 (errors, warnings, cols)。"""
    errors, warnings, cols = [], [], []
    text = read_text(table_path)
    if text is None:
        errors.append("表格文件无法读取：%s" % table_path)
        return errors, warnings, cols
    m = re.search(r"^\|(.+)\|\s*$", text, re.M)
    if not m:
        errors.append("未在 %s 中识别到 Markdown 表格表头" % table_path)
        return errors, warnings, cols
    cols = [c.strip() for c in m.group(1).split("|") if c.strip()]
    miss = [c for c in STD_COLS if c not in cols]
    if miss:
        warnings.append("表格缺标准列：%s" % "、".join(miss))
    if not re.search(r"【待核", text):
        warnings.append("表格未见【待核】标注（不确定项应显性化）")
    return errors, warnings, cols


def check_skill(skill_dir):
    errors, warnings = [], []
    metrics = {}
    text = read_text(os.path.join(skill_dir, "SKILL.md"))
    if text is None:
        errors.append("未找到或无法读取 SKILL.md")
        return errors, warnings, metrics

    metrics["skill_md_chars"] = len(text)
    if len(text) > MAX_SKILL_CHARS:
        errors.append("SKILL.md 字符数 %d 超限（> %d）" % (len(text), MAX_SKILL_CHARS))
    if not re.match(r"^---\s*\n", text):
        errors.append("缺 frontmatter（--- 起首）")
    if re.search(r"^version:\s*\S", text, re.M) is None:
        warnings.append("frontmatter 缺 version 字段")

    stds = STD_RE.findall(text)
    metrics["standard_citations"] = len(set(stds))
    if len(set(stds)) < 5:
        warnings.append("引用标准不足 5 条（当前 %d 条）" % len(set(stds)))

    miss = [s for s in REQUIRED_SECTIONS if s not in text]
    metrics["missing_sections"] = miss
    if miss:
        warnings.append("正文缺章节：%s" % "、".join(miss))

    col_miss = [c for c in STD_COLS if c not in text]
    metrics["missing_std_cols"] = col_miss
    if col_miss:
        warnings.append("正文缺标准列定义：%s" % "、".join(col_miss))

    hit = [w for w in FAIL_WORDS if w in text]
    metrics["fail_word_hits"] = len(hit)
    if len(hit) < len(FAIL_WORDS):
        warnings.append("失败模式关键词未齐（%d/%d）" % (len(hit), len(FAIL_WORDS)))

    if "【待核" not in text:
        warnings.append("未见【待核】缺口标注口径")

    danger = DANGER_RE.findall(text)
    metrics["danger_hits"] = len(danger)
    if danger:
        errors.append("检出禁用破坏性短语：%s" % "、".join(sorted(set(danger))))

    if not os.path.isdir(os.path.join(skill_dir, "scripts")):
        warnings.append("缺 scripts/ 目录")
    ref_dir = os.path.join(skill_dir, "references")
    if not os.path.isdir(ref_dir):
        warnings.append("缺 references/ 分层目录")
    else:
        case_ok = any("案例库" in (read_text(os.path.join(ref_dir, f)) or "")
                      for f in os.listdir(ref_dir) if f.endswith((".md", ".txt")))
        if not case_ok:
            warnings.append("references/ 未见案例库文件（含「案例库」字样）")
    return errors, warnings, metrics


def main():
    ap = argparse.ArgumentParser(
        description="环境治理技术对比表格生成器技能结构自检（TRACE 要件 / 标准列 / 表格合规）")
    ap.add_argument("--skill", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help="技能目录路径，默认为本脚本所在技能的根目录")
    ap.add_argument("--table", help="可选：校验一份对比表格 Markdown 文件是否含标准列")
    ap.add_argument("--strict", action="store_true", help="严格模式：存在警告亦以退出码 1 结束")
    ap.add_argument("--quiet", action="store_true", help="仅输出结论行")
    args = ap.parse_args()

    skill_dir = os.path.abspath(args.skill)
    if not os.path.isdir(skill_dir):
        sys.stderr.write("用参错误：技能目录不存在：%s\n" % skill_dir)
        return 2

    errors, warnings, metrics = check_skill(skill_dir)
    if args.table:
        terr, twarn, cols = check_table(args.table)
        errors += terr
        warnings += twarn
        metrics["table_cols"] = cols

    if not args.quiet:
        print("技能目录：%s" % skill_dir)
        for key, val in metrics.items():
            print("  - %s：%s" % (key, val))
        for err in errors:
            print("[错误] %s" % err)
        for warn in warnings:
            print("[警告] %s" % warn)

    if errors:
        print("结论：不通过（致命 %d 项，警告 %d 项）" % (len(errors), len(warnings)))
        return 2
    if warnings:
        print("结论：通过但有警告 %d 项" % len(warnings))
        return 1
    print("结论：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
