#!/usr/bin/env python3
"""环境治理技术对比表格生成器：按标准列生成 Markdown 对比表骨架。

只生成骨架与维度提示，定性判断（高/中/低）由使用者或 agent 依据行业共识填写。
用法：
  python3 gen_compare_table.py --domain 污水处理 --techs AAO,MBR,SBR,氧化沟
  python3 gen_compare_table.py --domain 污泥处置 --techs 厌氧消化,干化焚烧,建材利用 --cols 措施 -o table.md
"""
import argparse
import datetime
import sys

STANDARD_COLS = [
    ("技术名称", "主流/常见的技术方法"),
    ("目标污染物", "该技术主要针对的污染物"),
    ("场景适用性", "适用场景（原位/异位、市政/工业等）"),
    ("技术成熟度", "高/中/低"),
    ("修复效率", "高/中/低（相对统一描述）"),
    ("建设资金", "高/中/低"),
    ("运行成本", "高/中/低"),
    ("系统稳定性", "高/中/低"),
    ("修复周期", "短/中/长"),
    ("环境风险", "高/中/低"),
    ("优点", "简明列出主要优势"),
    ("缺点", "简明列出主要局限性"),
]

OPTIONAL_COL = ("措施", "用户提及\"措施/具体措施\"时增加")


def build_table(domain: str, techs: list, extra_cols: list) -> str:
    cols = [c for c, _ in STANDARD_COLS]
    notes = [f"- {c}：{d}" for c, d in STANDARD_COLS]
    for c in extra_cols:
        cols.append(c)
        notes.append(f"- {c}：{OPTIONAL_COL[1] if c == OPTIONAL_COL[0] else '用户指定列'}")

    lines = []
    lines.append(f"# {domain}治理技术对比表（骨架）")
    lines.append("")
    lines.append(f"> 对比范围：{domain}；生成日期：{datetime.date.today().isoformat()}")
    lines.append("> 定性判断（高/中/低、短/中/长）由填写人依据行业共识与规范给出，不确定项标【待核】。")
    lines.append("")
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["------"] * len(cols)) + "|")
    for t in techs:
        row = [t] + ["【待填】"] * (len(cols) - 1)
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## 列定义说明")
    lines.extend(notes)
    lines.append("")
    lines.append("## 填写规则")
    lines.append("- 评估指标用\"高/中/低\"等相对统一描述，各列口径一致")
    lines.append("- 不遗漏用户指定列，不编造不存在的列")
    lines.append("- 有争议的定性结论标【待核】；深化计算联动 wastewater-optimization / membrane-system-design / activated-sludge-calculator")
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="生成环境治理技术对比表骨架（Markdown）")
    p.add_argument("--domain", required=True, help="治理领域，如：污水处理/污泥处置/黑臭水体/VOCs")
    p.add_argument("--techs", required=True, help="逗号分隔的技术清单")
    p.add_argument("--cols", default="", help="追加列，逗号分隔（如：措施）")
    p.add_argument("-o", "--out", default="", help="输出文件路径；缺省打印到终端")
    args = p.parse_args()

    techs = [t.strip() for t in args.techs.split(",") if t.strip()]
    extra = [c.strip() for c in args.cols.split(",") if c.strip()]
    if not techs:
        sys.exit("错误：--techs 至少提供一个技术名称")
    content = build_table(args.domain, techs, extra)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"已写入：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
