#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验收合规判定器：对照九条不合格情形与水处理项目重大变动清单逐条判定。

用法：
    python3 compliance_checker.py --out 合规判定.md
    python3 compliance_checker.py --answers answers.json --out 合规判定.md

answers.json 格式（存在该情形填 true，不存在填 false，未核定留空或 null）：
    {"f1": false, "f2": false, "f3": true, "c1": false}

条款键：
    九条不合格情形 f1~f9；水处理重大变动 c1~c6。
"""
import argparse
import datetime
import json
import os
import sys

FAIL_ITEMS = [
    ("f1", "未按环评及审批决定建成环保设施，或不能与主体工程同时投产使用"),
    ("f2", "污染物排放不符合国家地方标准、环评及审批决定或重点污染物总量控制指标"),
    ("f3", "性质、规模、地点、生产工艺或防治污染措施发生重大变动，未重新报批或报批未获批"),
    ("f4", "造成重大环境污染未治理完成，或重大生态破坏未恢复"),
    ("f5", "纳入排污许可管理却无证排污或不按证排污"),
    ("f6", "分期验收项目环保设施能力不能满足相应主体工程需要"),
    ("f7", "因本项目违反环保法规被责令改正，尚未改正完成"),
    ("f8", "验收报告基础资料数据明显不实、重大缺项遗漏或结论不明确不合理"),
    ("f9", "其他环保法规规定不得通过验收的情形"),
]

CHANGE_ITEMS = [
    ("c1", "规模：污水设计日处理能力增加30%及以上"),
    ("c2", "地点：重新选址，或原厂址附近调整导致大气环境防护距离内新增环境敏感点"),
    ("c3", "工艺：处理工艺变化，或进水水质水量变化导致污染物项目或排放量增加"),
    ("c4", "措施：新增废水排放口，间接改直排，或直排口位置变化加重不利影响"),
    ("c5", "措施：废气处理设施变化导致排放量增加，或排气筒高度降低10%及以上"),
    ("c6", "措施：污泥产生量增加且自行处置能力不足，或处置方式变化加重不利影响"),
]

EXTRA_CHECKS = [
    ("x1", "环保设施竣工日期已公开并报属地生态环境部门"),
    ("x2", "调试起止日期已公开"),
    ("x3", "排污许可证已取得且证载内容与项目一致"),
    ("x4", "应急预案已在生态环境部门备案并留存演练记录"),
    ("x5", "污泥危险废物属性已鉴定"),
    ("x6", "验收监测在工况稳定、设施正常运行且如实记录负荷条件下完成"),
    ("x7", "验收报告公示不少于20个工作日且渠道合规"),
    ("x8", "公示期满后5个工作日内完成全国信息平台填报"),
]


def verdict(answers, keys):
    hit, clear, unknown = [], [], []
    for key, desc in keys:
        v = answers.get(key)
        if v is True:
            hit.append((key, desc))
        elif v is False:
            clear.append((key, desc))
        else:
            unknown.append((key, desc))
    return hit, clear, unknown


def main():
    ap = argparse.ArgumentParser(description="污水厂竣工环保验收合规判定器")
    ap.add_argument("--answers", default="", help="answers.json 路径，缺省则输出空白检查表")
    ap.add_argument("--out", default="", help="输出 Markdown 路径")
    ap.add_argument("--project", default="污水处理厂建设项目", help="项目名称")
    args = ap.parse_args()

    answers = {}
    if args.answers:
        if not os.path.exists(args.answers):
            print("answers 文件不存在：{}".format(args.answers))
            sys.exit(1)
        with open(args.answers, "r", encoding="utf-8") as f:
            answers = json.load(f)

    fh, fc, fu = verdict(answers, FAIL_ITEMS)
    ch, cc, cu = verdict(answers, CHANGE_ITEMS)
    xh, xc, xu = verdict(answers, EXTRA_CHECKS)

    lines = []
    lines.append("# {} 竣工环境保护验收合规判定".format(args.project))
    lines.append("")
    lines.append("判定日期：{}".format(datetime.date.today().isoformat()))
    lines.append("")
    lines.append("## 一、结论")
    lines.append("")
    if not args.answers:
        lines.append("未提供 answers.json，以下为空白检查表，请逐条核定后重新运行判定。")
    elif fh:
        lines.append("命中不合格情形 {} 项，不得出具验收合格意见，须先整改。".format(len(fh)))
    elif fu:
        lines.append("有 {} 项未核定，补齐后再出结论；当前无一票否决项命中。".format(len(fu)))
    else:
        lines.append("九条不合格情形均未命中，可出具验收合格意见（仍须补齐未核定项）。")
    if ch:
        lines.append("")
        lines.append("构成或疑似构成重大变动 {} 项，须核对是否已重新报批环评。".format(len(ch)))
    lines.append("")

    def block(title, hits, clears, unknowns, note):
        lines.append("## {}".format(title))
        lines.append("")
        if hits:
            lines.append("### 命中项（须处置）")
            lines.append("")
            for k, d in hits:
                lines.append("- **{}** {}".format(k.upper(), d))
            lines.append("")
        if unknowns:
            lines.append("### 未核定项")
            lines.append("")
            for k, d in unknowns:
                lines.append("- [ ] **{}** {}".format(k.upper(), d))
            lines.append("")
        if clears:
            lines.append("### 已排除项")
            lines.append("")
            for k, d in clears:
                lines.append("- [x] **{}** {}".format(k.upper(), d))
            lines.append("")
        if note:
            lines.append(note)
            lines.append("")

    block("二、九条验收不合格情形", fh, fc, fu,
          "命中任一条即不得出具合格意见；未核定项须补齐后判定。")
    block("三、水处理项目重大变动清单", ch, cc, cu,
          "构成重大变动且未重新报批的，同时命中不合格情形第(F3)条。")
    block("四、程序与时效检查", xh, xc, xu,
          "本组为程序性检查，未完成项不直接导致不合格，但影响验收程序有效性。")

    content = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(content)
        print("已生成：{}".format(args.out))
        if fh:
            print("提示：命中不合格情形 {} 项".format(len(fh)))
    else:
        print(content)


if __name__ == "__main__":
    main()
