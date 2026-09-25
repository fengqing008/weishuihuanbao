#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""污水厂竣工环保验收工作清单生成器。

用法：
    python3 acceptance_checklist.py --project "项目名称" --out 清单.md
    python3 acceptance_checklist.py --project "项目名称" --format csv --out 清单.csv
    python3 acceptance_checklist.py --project "项目名称" --stage 监测
"""
import argparse
import csv
import datetime
import os
import sys

STAGES = [
    ("一、前期准备与资料收集", [
        ("1.1", "梳理环评报告书及所有批复文件", "明确建设内容、规模、工艺、环保措施、排放标准、总量指标、风险防范、监测计划；核对特征污染物要求", "建设单位/运维单位"),
        ("1.2", "收集项目设计文件（可研、初设、施工图环保部分）", "核查环保设施设计是否符合环评及批复", "建设单位（设计单位配合）"),
        ("1.3", "收集重大设计变更及变更说明", "确认环保设施按图施工，重大变更须有合规手续", "建设单位（施工单位配合）"),
        ("1.4", "整理运行管理制度与记录", "操作规程、维护台账、药剂记录、污泥产生贮存转移处置联单、试运行监测数据、应急预案及演练记录", "建设单位（运营单位）"),
        ("1.5", "收集排污许可证副本", "核对许可内容与项目一致性", "建设单位/运维单位"),
        ("1.6", "收集危废处置合同及接收单位资质", "确保合规处置", "建设单位/运维单位"),
        ("1.7", "污泥开展危险废物鉴定", "确定污泥属性，明确处置去向", "建设单位"),
        ("1.8", "卫生防护距离内敏感点处置", "核实防护距离范围内居民搬迁或安置进展", "建设单位"),
    ]),
    ("二、现场踏勘与核查", [
        ("2.1", "核查建设内容与规模", "地点、规模、工艺、主要构筑物与环评批复一致性", "验收组（建设单位/运维单位）"),
        ("2.2", "核查废水处理设施", "逐单元检查建成、运行、效果；中控系统；在线监测安装联网运行；排污口规范；事故应急池", "验收组"),
        ("2.3", "核查废气处理设施", "臭气收集加盖密封、除臭设施运行效果、厂界无组织控制", "验收组"),
        ("2.4", "核查噪声防治设施", "泵、风机等噪声源隔声消声减振措施；厂界噪声", "验收组"),
        ("2.5", "核查固废处理处置设施", "污泥脱水设备运行；污泥贮存场所防渗；危废暂存间规范标识台账；一般固废场所", "验收组"),
        ("2.6", "核查地下水与土壤防渗", "管线、池体、事故池、污泥场、危废间等重点区域防渗措施落实情况", "验收组"),
        ("2.7", "核查环境风险防范设施", "事故应急池、围堰、切换阀有效性；应急物资储备", "验收组"),
        ("2.8", "核查环境管理", "机构人员、制度执行台账、标识标牌、雨污清污分流、防护距离内敏感点", "验收组"),
    ]),
    ("三、验收监测", [
        ("3.1", "委托具备CMA资质的检测机构", "核查资质与能力范围", "建设单位/第三方"),
        ("3.2", "确定监测因子与点位频次", "废水、废气、噪声、地下水、地表水、土壤；工况与负荷符合要求", "检测机构"),
        ("3.3", "实施验收监测并记录工况", "≥2天，废水每天4次、废气每天3次；如实记录生产负荷", "检测机构"),
        ("3.4", "编制CMA认证的验收监测报告", "含方案、数据、质控、达标分析结论，重点分析特征污染物", "检测机构"),
    ]),
    ("四、编制验收报告", [
        ("4.1", "编制建设项目竣工环境保护验收报告", "十一章齐备：概况、依据、建设情况、环保设施、环评结论与审批决定、执行标准、监测内容、质控、监测结果、监测结论、三同时登记表", "第三方/建设单位"),
        ("4.2", "整理附件、附图与附表", "批复、监测报告、排污许可证、危废合同、应急预案备案表、设计关键页、现场照片、验收组名单等", "第三方/建设单位"),
        ("4.3", "排查九条不合格情形", "逐条对照，命中条款先整改", "建设单位"),
    ]),
    ("五、组织验收会议", [
        ("5.1", "成立验收工作组", "建设、环评、监测、编制单位及特邀专家（环保工程、环境监测、环境管理）", "建设单位"),
        ("5.2", "召开验收会议", "现场复查、听取汇报、质询讨论", "建设单位（验收组组长主持）"),
        ("5.3", "形成建设项目竣工环境保护验收意见", "六要素完整，结论明确合格与否，成员签字", "建设单位"),
    ]),
    ("六、整改落实与信息公开", [
        ("6.1", "落实验收组提出的整改要求", "限期完成整改并形成整改报告", "建设单位"),
        ("6.2", "根据验收意见修改完善报告", "最终定稿", "第三方/建设单位"),
        ("6.3", "信息公开", "三项文件公示≥20个工作日；完成全国信息平台填报", "建设单位"),
        ("6.4", "资料归档与报送", "全套资料一项目一档长期保存；报属地生态环境部门", "建设单位"),
    ]),
]


def build_rows(stage_filter=None):
    rows = []
    for stage_name, tasks in STAGES:
        if stage_filter and stage_filter not in stage_name:
            continue
        for no, task, req, owner in tasks:
            rows.append([stage_name, no, task, req, owner, ""])
    return rows


def write_md(rows, project, out):
    today = datetime.date.today().isoformat()
    lines = []
    lines.append("# {} 竣工环境保护验收工作清单".format(project))
    lines.append("")
    lines.append("生成日期：{}".format(today))
    lines.append("")
    lines.append("说明：状态列由项目现场填写（已完成/部分完成/未完成），缺失项在备注中标注【待核：补齐路径】。")
    lines.append("")
    cur = None
    idx = 0
    for row in rows:
        if row[0] != cur:
            cur = row[0]
            lines.append("")
            lines.append("## {}".format(cur))
            lines.append("")
            lines.append("| 序号 | 主要工作内容 | 关键要求/注意事项 | 责任主体 | 状态 |")
            lines.append("|---|---|---|---|---|")
        lines.append("| {} | {} | {} | {} | {} |".format(row[1], row[2], row[3], row[4], row[5] or "□"))
        idx += 1
    lines.append("")
    lines.append("## 统计")
    lines.append("")
    lines.append("- 任务总数：{}".format(len(rows)))
    by_stage = {}
    for row in rows:
        by_stage[row[0]] = by_stage.get(row[0], 0) + 1
    for k, v in by_stage.items():
        lines.append("- {}：{} 项".format(k, v))
    content = "\n".join(lines) + "\n"
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
        return "已生成：{}（{} 项任务）".format(out, len(rows))
    return content


def write_csv(rows, project, out):
    buf = []
    header = ["工作阶段", "序号", "主要工作内容", "关键要求/注意事项", "责任主体", "状态"]
    if out:
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        return "已生成：{}（{} 项任务）".format(out, len(rows))
    sio = csv.writer(sys.stdout)
    sio.writerow(header)
    sio.writerows(rows)
    return ""


def main():
    ap = argparse.ArgumentParser(description="污水厂竣工环保验收工作清单生成器")
    ap.add_argument("--project", default="污水处理厂建设项目", help="项目名称")
    ap.add_argument("--out", default="", help="输出文件路径（.md 或 .csv）")
    ap.add_argument("--format", choices=["md", "csv"], default="md", help="输出格式")
    ap.add_argument("--stage", default="", help="仅输出含该关键词的阶段，如 监测")
    args = ap.parse_args()

    rows = build_rows(args.stage or None)
    if not rows:
        print("未匹配到阶段：{}".format(args.stage))
        sys.exit(1)

    if args.format == "csv":
        msg = write_csv(rows, args.project, args.out)
    else:
        msg = write_md(rows, args.project, args.out)
    if msg:
        print(msg)


if __name__ == "__main__":
    main()
