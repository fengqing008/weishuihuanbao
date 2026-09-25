#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验收监测报告十一章框架生成器。

用法：
    python3 report_builder.py --project "项目名称" --capacity 5000 --out 报告框架.md
"""
import argparse
import datetime
import os
import sys

CHAPTERS = [
    ("1", "建设项目概况", [
        "建设背景（园区或区域沿革、排水压力）",
        "环评委托与批复过程（编制单位、批复机关、批复文号、批复日期）",
        "建设起止时间、投资总额、用地面积",
        "环评阶段与实际建设内容的对比说明",
        "验收监测工作的委托与报告编制过程",
    ]),
    ("2", "验收依据", [
        "建设项目环境保护相关法律、法规、规章和规范",
        "建设项目竣工环境保护验收技术规范",
        "建设项目环境影响报告书（表）及审批部门审批决定",
        "其他相关文件（排污许可证、在线监测验收报告、危废协议等）",
    ]),
    ("3", "项目建设情况", [
        "3.1 地理位置及平面布置（含环境敏感保护目标表）",
        "3.2 建设内容（环评阶段与实际建设对比表、主要设备设施一览表）",
        "3.3 主要原辅材料及燃料",
        "3.4 水源及水平衡",
        "3.5 生产工艺（工艺流程图、产污环节汇总表）",
        "3.6 项目变动情况（对照水处理重大变动清单逐条判定）",
    ]),
    ("4", "环境保护设施", [
        "4.1 污染物治理设施（废水、废气、噪声、固废及危废暂存间）",
        "4.2 其他环境保护设施（分区防渗、地下水监测井、围堰与事故应急池、排污口规范化、在线监测、卫生防护距离）",
        "4.3 环保设施投资及三同时落实情况（实际环保投资、占总投资比例、与环评概算对比、三同时验收清单表）",
    ]),
    ("5", "环评报告书（表）主要结论与审批决定", [
        "5.1 环境影响报告书（表）主要结论与要求（各环境要素影响结论、主要环保措施）",
        "5.2 审批部门审批决定（批复要求逐条列出）",
    ]),
    ("6", "验收执行标准", [
        "6.1 验收执行标准选取原则",
        "6.2 环境质量标准（空气、地表水、地下水、声、土壤）及限值表",
        "6.3 污染物排放标准（废水、废气、噪声、固废）及限值表",
    ]),
    ("7", "验收监测内容", [
        "7.1 环境保护设施调试运行效果（废水、有组织废气、无组织废气、厂界噪声的点位因子频次）",
        "7.2 环境质量监测（环境空气、地表水、地下水、声环境、土壤的点位因子频次）",
    ]),
    ("8", "质量保证和质量控制", [
        "8.1 监测分析方法与监测仪器（方法标准号、检出限）",
        "8.2 人员能力与持证情况",
        "8.3 监测分析过程中的质量保证和质量控制（空白、平行样、加标回收等结果）",
    ]),
    ("9", "验收监测结果", [
        "9.1 生产工况（监测期间生产负荷率、环保设施运行状态）",
        "9.2 环保设施调试运行效果（废水、废气、厂界噪声监测结果）",
        "9.3 工程建设对环境的影响（环境空气、地表水、地下水、声环境、土壤；污染物排放总量核算）",
    ]),
    ("10", "验收监测结论", [
        "10.1 环保设施调试运行效果",
        "10.2 工程建设对环境的影响",
    ]),
    ("11", "建设项目环境保护“三同时”竣工验收登记表", [
        "按登记表格式填写项目基本信息、环保设施与投资、验收结论等",
    ]),
]

ATTACHMENTS = [
    "环境影响报告书批复文件", "入河排污口设置论证报告审批意见", "项目立项批复",
    "建设用地文件", "排污许可证", "验收检测报告", "水污染源在线监测设备验收报告",
    "污泥鉴定情况说明", "相关事项承诺函", "危险废物收集处置协议", "营业执照",
]

FIGURES = [
    "项目地理位置图", "项目平面布置图", "项目敏感目标分布图",
    "项目监测布点图", "项目卫生防护距离包络线图", "项目服务范围图",
]


def main():
    ap = argparse.ArgumentParser(description="污水厂竣工环保验收监测报告框架生成器")
    ap.add_argument("--project", default="污水处理厂建设项目", help="项目名称")
    ap.add_argument("--capacity", default="", help="设计处理能力（m³/d）")
    ap.add_argument("--out", default="", help="输出 Markdown 路径")
    args = ap.parse_args()

    cap = "（设计处理能力 {} m³/d）".format(args.capacity) if args.capacity else ""
    lines = []
    lines.append("# {}竣工环境保护验收监测报告{}".format(args.project, cap))
    lines.append("")
    lines.append("编制日期：{}".format(datetime.date.today().isoformat()))
    lines.append("")
    lines.append("> 本文件为报告框架，【待填：】处由编制人据实填写，涉及数据须溯源，未核实项标注【待核：具体说明】。")
    lines.append("")
    for no, title, points in CHAPTERS:
        lines.append("## {} {}".format(no, title))
        lines.append("")
        for p in points:
            lines.append("- 【待填：{}】".format(p))
        lines.append("")
    lines.append("## 附件清单")
    lines.append("")
    for i, a in enumerate(ATTACHMENTS, 1):
        lines.append("{}. {}".format(i, a))
    lines.append("")
    lines.append("## 附图清单")
    lines.append("")
    for i, f in enumerate(FIGURES, 1):
        lines.append("{}. {}".format(i, f))
    lines.append("")
    lines.append("## 编制自检")
    lines.append("")
    for item in ["数据一致性（同一指标各章数值一致）", "标准一致性（编号与类别全文统一）",
                 "时间一致性（监测日期与报告周期匹配）", "表格编号无重号跳号",
                 "计量单位与标准限值单位一致", "结论明确合格与否"]:
        lines.append("- [ ] {}".format(item))
    lines.append("")

    content = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(content)
        print("已生成：{}（{} 章）".format(args.out, len(CHAPTERS)))
    else:
        print(content)


if __name__ == "__main__":
    main()
