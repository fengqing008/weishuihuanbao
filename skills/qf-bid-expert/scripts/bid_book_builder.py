#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标书骨架生成器 —— 生成技术标或商务标的 Markdown 骨架。

用法:
    python3 bid_book_builder.py --type technical --project "XX项目" --out 技术标骨架.md
    python3 bid_book_builder.py --type commercial --project "XX项目" --out 商务标骨架.md
"""
import argparse
import sys

TECH = [
    ("一、项目理解与总体筹划", ["1.1 项目概况与总体认识", "1.2 项目总体目标", "1.3 对现有方案的优化建议", "1.4 项目总体筹划"]),
    ("二、项目公司组建与管理方案", ["2.1 项目公司情况", "2.2 组建原则与组建计划", "2.3 组织架构与人员配置", "2.4 管理职能与制度", "2.5 拟派人员"]),
    ("三、设计方案（工艺方案）", ["3.1 设计方案完整性与响应说明", "3.2 工艺选择与路径比选", "3.3 核心材料及设备比选", "3.4 工艺设计参数", "3.5 污染物去除率论证"]),
    ("四、建设方案（施工组织）", ["4.1 前期准备与资源配置", "4.2 总体施工部署", "4.3 工期安排与进度保证", "4.4 质量与安全保障", "4.5 造价成本控制", "4.6 环境保护与文明施工", "4.7 合同、档案与风险管理"]),
    ("五、运营方案", ["5.1 运营总则与目标", "5.2 组织架构与岗位职责", "5.3 生产运行管理", "5.4 水质质量保障", "5.5 设备与管网运维", "5.6 成本控制与绩效考核", "5.7 安全环保与应急预案", "5.8 智慧运维与移交"]),
    ("六、移交方案", ["6.1 移交范围与时间安排", "6.2 移交程序与验收", "6.3 恢复性大修方案", "6.4 人员培训", "6.5 缺陷责任期与质量保证"]),
    ("七、法律方案", ["7.1 法律协议修改对照表", "7.2 条款响应声明"]),
]

BIZ = [
    ("一、投标核心文件", ["1.1 投标函", "1.2 投标承诺书", "1.3 投标报价表", "1.4 报价合理性分析表"]),
    ("二、主体资格与授权", ["2.1 营业执照", "2.2 法定代表人身份证明书", "2.3 法定代表人授权书", "2.4 资格条件承诺书"]),
    ("三、财务、税务与社保", ["3.1 财务状况报告与声明函", "3.2 审计报告", "3.3 纳税证明", "3.4 社保证明"]),
    ("四、业绩", ["4.1 类似项目业绩证明", "4.2 投标人业绩表"]),
    ("五、项目管理机构与人员", ["5.1 项目负责人资格证书", "5.2 项目团队人员名单及配置表", "5.3 劳动合同与人员资格证明"]),
    ("六、声明与承诺", ["6.1 无重大违法记录声明函", "6.2 未参加同一合同项下采购活动声明函", "6.3 未被列入失信名单声明函及查询截图", "6.4 无拖欠劳动者工资承诺函", "6.5 廉洁保证书与保密承诺书"]),
]


def build(kind, project):
    blocks = TECH if kind == "technical" else BIZ
    label = "技术标" if kind == "technical" else "商务标"
    out = []
    out.append(f"# {project} {label}（骨架）")
    out.append("")
    out.append(f"> 项目：{project}｜类型：{label}｜生成：eco-bid-expert")
    out.append("> 本骨架按招标文件与评分办法裁剪，成稿前先完成废标红线排查与评分响应表编制。")
    out.append("")
    for h1, subs in blocks:
        out.append(f"## {h1}")
        out.append("")
        for s in subs:
            out.append(f"### {s}")
            out.append("")
            out.append("- 【待填：本小节内容，按评分标准最高档组织】")
            out.append("")
    out.append("---")
    out.append("")
    out.append("## 附：评分响应表（置于分册最前）")
    out.append("")
    out.append("| 序号 | 评审因素(含分值) | 评分标准(分档原文) | 响应情况 | 响应位置 |")
    out.append("|---|---|---|---|---|")
    out.append("| 1 | | | 完全响应 | 详见第__章第__节 |")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="标书骨架生成器")
    ap.add_argument("--type", required=True, choices=["technical", "commercial"], help="technical 或 commercial")
    ap.add_argument("--project", required=True, help="项目名称")
    ap.add_argument("--out", required=True, help="输出文件（md）")
    args = ap.parse_args()

    content = build(args.type, args.project)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)
    label = "技术标" if args.type == "technical" else "商务标"
    print(f"OK {label}骨架已写入 {args.out}")


if __name__ == "__main__":
    sys.exit(main())
