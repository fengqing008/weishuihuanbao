#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
acceptance_tools.py —— 工程验收全套资料生成工具

面向市政工程（含污水处理厂 PPP 项目）竣工验收场景，提供四个子命令：
  checklist  生成分部分项验收资料核对清单（Word）
  records    生成检验批/隐蔽工程/分项/分部工程质量验收记录模板包（Word）
  report     生成竣工验收报告框架（Word）
  meeting    生成竣工验收会议全套文件（Word）

依据：
  - 《建设工程质量管理条例》（国务院令第279号）
  - 《房屋建筑工程和市政基础设施工程竣工验收暂行规定》（建质〔2000〕142号）
  - GB 50300-2013《建筑工程施工质量验收统一标准》

用法示例：
  python acceptance_tools.py checklist -o ./output --project-name "某市区污水处理厂PPP项目"
  python acceptance_tools.py records   -o ./output --project-name "某市区污水处理厂PPP项目"
  python acceptance_tools.py report    -o ./output --project-name "某市区污水处理厂PPP项目" --location "西安市某市区"
  python acceptance_tools.py meeting   -o ./output --project-name "某市区污水处理厂PPP项目"
"""

import argparse
import os
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# ---------------------------------------------------------------
# 常量
# ---------------------------------------------------------------
CN_FONT = "宋体"          # 中文正文默认字体
HEI_FONT = "黑体"         # 标题字体
EN_FONT = "Times New Roman"  # 西文字体


# ---------------------------------------------------------------
# 通用工具：字体 / 段落 / 表格辅助
# ---------------------------------------------------------------
def _set_run(run, size=10.5, bold=False, cn_font=CN_FONT, color=None):
    """统一设置 run 的字体：西文 Times New Roman，中文指定字体（宋体/黑体）。"""
    run.font.name = EN_FONT
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    r_fonts.set(qn("w:eastAsia"), cn_font)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def add_para(doc, text, size=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT,
             cn_font=CN_FONT, space_after=6, color=None, indent=None):
    """向文档添加一个段落并设置格式。"""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    _set_run(run, size=size, bold=bold, cn_font=cn_font, color=color)
    return p


def add_title(doc, text, size=16):
    """文档大标题（居中、黑体加粗）。"""
    return add_para(doc, text, size=size, bold=True,
                    align=WD_ALIGN_PARAGRAPH.CENTER, cn_font=HEI_FONT, space_after=12)


def add_h1(doc, text):
    """一级标题（黑体加粗）。"""
    return add_para(doc, text, size=14, bold=True, cn_font=HEI_FONT, space_after=8)


def add_h2(doc, text):
    """二级标题（宋体加粗）。"""
    return add_para(doc, text, size=12, bold=True, space_after=6)


def make_table(doc, headers, rows, widths=None):
    """创建表格：表头行黑体加粗居中，数据行宋体居中；可选列宽（单位 cm）。"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 表头
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        _set_run(run, size=10.5, bold=True, cn_font=HEI_FONT)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    # 数据行
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(val))
            _set_run(run, size=10.5)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    # 列宽
    if widths:
        for j, w in enumerate(widths):
            for row in table.rows:
                row.cells[j].width = Cm(w)
    return table


def make_info_table(doc, pairs, widths=None):
    """创建两列（名称/内容）的信息表，用于工程名称、施工单位等表头信息。"""
    table = doc.add_table(rows=len(pairs), cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate(pairs):
        c0, c1 = table.cell(i, 0), table.cell(i, 1)
        for c, text, bold in ((c0, k, True), (c1, v, False)):
            c.text = ""
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(text)
            _set_run(run, size=10.5, bold=bold)
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    if widths:
        for row in table.rows:
            row.cells[0].width = Cm(widths[0])
            row.cells[1].width = Cm(widths[1])
    return table


def ensure_dir(path):
    """确保输出目录存在。"""
    os.makedirs(path, exist_ok=True)
    return path


def save(doc, out_dir, filename):
    """保存文档并返回完整路径。"""
    path = os.path.join(out_dir, filename)
    doc.save(path)
    return path


# ---------------------------------------------------------------
# 子命令 a) checklist：验收资料核对清单
# ---------------------------------------------------------------
# 五大类资料，依据《建设工程质量管理条例》、建质〔2000〕142号、
# GB 50300-2013 附录 G/H 整理，并结合市政污水工程特点补充。
CHECKLIST = [
    {
        "category": "一、施工管理资料",
        "intro": "由施工单位整理、监理单位审核，随工程进度同步形成并归档。",
        "items": [
            ("工程开工报告及开工报审表", "1", "施工单位"),
            ("施工组织设计及专项施工方案（含专家论证，如有）", "1", "施工单位/监理单位"),
            ("图纸会审记录、设计变更通知单、工程洽商记录", "1", "施工单位/设计单位"),
            ("施工测量放线及复核记录（定位、标高、轴线）", "1", "施工单位"),
            ("施工日志（含冬雨季施工、特殊天气记录）", "1", "施工单位"),
            ("施工技术交底记录", "1", "施工单位"),
            ("工程质量事故处理报告（如有）", "1", "施工单位/监理单位"),
            ("见证取样和送检台账", "1", "施工单位/监理单位"),
            ("施工现场质量管理检查记录（GB50300 附录A）", "1", "施工单位/监理单位"),
        ],
    },
    {
        "category": "二、质量控制资料",
        "intro": "对应 GB 50300-2013 附录 G《单位工程质量控制资料核查》，由施工单位提供原始记录与检测报告。",
        "items": [
            ("钢材出厂合格证及进场复试报告", "1", "施工单位/监理单位"),
            ("水泥、砂、石、外加剂、掺合料出厂合格证及复试报告", "1", "施工单位/监理单位"),
            ("混凝土配合比设计报告及试块抗压/抗渗试验报告", "1", "检测单位"),
            ("砂浆配合比及试块强度试验报告", "1", "检测单位"),
            ("钢筋连接（焊接/机械连接）工艺评定及试验报告", "1", "施工单位/检测单位"),
            ("防水材料出厂合格证、复试报告及蓄水/淋水试验记录", "1", "施工单位/监理单位"),
            ("预制构件、管材、阀门、设备出厂合格证及进场检验记录", "1", "施工单位/监理单位"),
            ("隐蔽工程验收记录（土方、钢筋、防水、管道等）", "1", "施工单位/监理单位"),
            ("检验批、分项、分部工程质量验收记录", "1", "施工单位/监理单位"),
            ("污水处理构筑物满水试验记录（市政污水工程）", "1", "施工单位/监理单位"),
            ("管道系统水压试验、闭水（闭气）试验记录", "1", "施工单位/监理单位"),
            ("设备安装工程单机试运转及调试记录", "1", "施工单位/监理单位"),
            ("电气工程绝缘电阻、接地电阻测试记录", "1", "施工单位/检测单位"),
            ("沉降观测记录（构筑物、建筑物）", "1", "检测单位"),
        ],
    },
    {
        "category": "三、安全和功能检验资料",
        "intro": "对应 GB 50300-2013《单位工程安全和功能检验资料核查及主要功能抽查记录》，含市政污水工程专项检验。",
        "items": [
            ("给排水管道通水、通球（通水能力）试验记录", "1", "施工单位"),
            ("电气照明全负荷试运行记录", "1", "施工单位"),
            ("消防系统联动调试及检测报告", "1", "施工单位/检测单位"),
            ("污水厂联动试运行（带负荷）记录及72小时满负荷试运行报告", "1", "施工单位/建设单位"),
            ("竣工环保验收监测报告（水质、废气、噪声、污泥）", "1", "建设单位/检测单位"),
            ("防雷接地检测报告", "1", "检测单位"),
            ("特种设备（起重机械、压力容器等）检验报告（如有）", "1", "检测单位"),
        ],
    },
    {
        "category": "四、观感质量检查资料",
        "intro": "按 GB 50300-2013 附录 H 执行，由验收组会同参建单位现场检查填写。",
        "items": [
            ("单位（子单位）工程观感质量检查记录", "1", "验收组"),
            ("室外附属工程（道路、绿化、围墙、大门）观感检查记录", "1", "验收组"),
            ("观感质量问题整改及复查记录", "1", "施工单位/监理单位"),
        ],
    },
    {
        "category": "五、竣工验收文件",
        "intro": "依据建质〔2000〕142号第八条，由建设单位组织、各参建单位配合形成。",
        "items": [
            ("工程竣工验收报告", "4", "建设单位"),
            ("竣工验收备案表", "4", "建设单位"),
            ("勘察、设计、施工、监理单位质量检查（合格）报告", "各1", "各参建单位"),
            ("施工单位签署的工程保修书", "1", "施工单位"),
            ("工程竣工图（含电子版）", "4", "施工单位"),
            ("竣工结算书及审核（审计）报告", "4", "建设单位"),
            ("竣工验收会议纪要及验收意见书", "4", "建设单位/验收组"),
            ("工程质量监督报告", "1", "质量监督机构"),
            ("移交清单（含备品备件、技术资料）", "4", "施工单位"),
            ("PPP项目绩效评价/可用性付费相关资料（如适用）", "1", "项目公司/实施机构"),
        ],
    },
]


def cmd_checklist(args):
    """生成验收资料核对清单 Word 文档。"""
    out_dir = ensure_dir(args.output)
    doc = Document()
    add_title(doc, "工程竣工验收资料核对清单", size=18)
    add_para(doc, f"工程名称：{args.project_name}", size=12, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_para(doc, "编制依据：《建设工程质量管理条例》（国务院令第279号）、《房屋建筑工程和市政基础设施"
                  "工程竣工验收暂行规定》（建质〔2000〕142号）、GB 50300-2013《建筑工程施工质量验收统一标准》",
             size=9, align=WD_ALIGN_PARAGRAPH.CENTER, color=RGBColor(0x66, 0x66, 0x66), space_after=8)

    no = 0
    for cat in CHECKLIST:
        add_h1(doc, cat["category"])
        add_para(doc, cat["intro"], size=10, color=RGBColor(0x59, 0x59, 0x59), space_after=4)
        rows = []
        for name, copies, unit in cat["items"]:
            no += 1
            rows.append((no, name, copies, unit, "□ 已备　□ 未备"))
        make_table(doc,
                   ["序号", "资料名称", "份数要求", "责任单位", "完成情况"],
                   rows, widths=[1.0, 7.5, 1.8, 2.6, 2.6])
        add_para(doc, "", size=6, space_after=4)

    add_h1(doc, "核对说明")
    for t in (
        "1. 本清单为依据国家法规/标准整理的通用清单，具体项目按施工合同、地方质监机构要求增删；",
        "2. “份数要求”为归档最低要求，涉及备案的按备案部门要求提供；",
        "3. 资料齐全后由施工单位整理成册、监理单位审核签认，竣工验收时提交验收组核查；",
        "4. 市政污水工程应特别注意满水试验、联动试运行、环保验收监测等专项资料；",
        "5. PPP 项目应按 PPP 合同约定附绩效评价、可用性付费相关资料。",
    ):
        add_para(doc, t, size=10, space_after=2)

    path = save(doc, out_dir, "验收资料核对清单.docx")
    print(f"[checklist] 已生成：{path}")


# ---------------------------------------------------------------
# 子命令 b) records：检验批/隐蔽工程/分项/分部验收记录模板包
# ---------------------------------------------------------------
def cmd_records(args):
    """生成 4 个验收记录 Word 模板（字段以【待填：...】占位）。"""
    out_dir = ensure_dir(args.output)
    pn = args.project_name
    tpl = "【待填：{0}】"

    # ---- 1. 检验批质量验收记录 ----
    doc = Document()
    add_title(doc, "检验批质量验收记录", size=16)
    add_para(doc, "（依据 GB 50300-2013 附录 B、D）", size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER, color=RGBColor(0x66, 0x66, 0x66), space_after=8)
    make_info_table(doc, [
        ("工程名称", pn),
        ("检验批部位", tpl.format("检验批部位/区段")),
        ("施工单位", tpl.format("施工单位")),
        ("监理单位", tpl.format("监理单位")),
        ("验收依据", "GB 50300-2013 及相应专业验收规范"),
    ], widths=[4.0, 11.5])
    add_para(doc, "")
    add_h2(doc, "主控项目检查")
    make_table(doc,
               ["序号", "检验项目", "规范要求", "施工单位检查评定记录", "监理（建设）单位验收记录"],
               [(i, tpl.format("检验项目"), tpl.format("规范要求"), tpl.format("检查评定"), tpl.format("验收记录"))
                for i in range(1, 4)],
               widths=[1.0, 3.4, 3.4, 3.9, 3.8])
    add_para(doc, "")
    add_h2(doc, "一般项目检查")
    make_table(doc,
               ["序号", "检验项目", "规范要求（允许偏差）", "施工单位检查评定记录", "监理（建设）单位验收记录"],
               [(i, tpl.format("检验项目"), tpl.format("允许偏差"), tpl.format("检查评定"), tpl.format("验收记录"))
                for i in range(1, 5)],
               widths=[1.0, 3.4, 3.4, 3.9, 3.8])
    add_para(doc, "")
    make_info_table(doc, [
        ("施工单位检查结果", tpl.format("项目专业质量检查员：合格/不合格，签字、日期")),
        ("监理（建设）单位验收结论", tpl.format("专业监理工程师：合格/不合格，签字、日期")),
    ], widths=[4.0, 11.5])
    save(doc, out_dir, "检验批质量验收记录模板.docx")

    # ---- 2. 隐蔽工程验收记录 ----
    doc = Document()
    add_title(doc, "隐蔽工程验收记录", size=16)
    add_para(doc, "（市政工程隐蔽部位：土方、钢筋、防水、管道、基础等）", size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER, color=RGBColor(0x66, 0x66, 0x66), space_after=8)
    make_info_table(doc, [
        ("工程名称", pn),
        ("隐蔽部位", tpl.format("隐蔽部位（桩号/构筑物名称）")),
        ("隐蔽日期", tpl.format("年 月 日")),
        ("施工图号", tpl.format("图纸编号")),
        ("隐蔽内容", tpl.format("隐蔽内容（材质、规格、数量、做法等）")),
        ("检查方法", "观察 / 量测 / 试验（按实际情况填写）"),
        ("检查结论", "□ 合格　□ 不合格"),
    ], widths=[3.4, 12.1])
    add_para(doc, "")
    add_h2(doc, "附图（示意图、照片粘贴处）")
    make_table(doc, ["附图及说明"], [("【待填：粘贴隐蔽部位示意图或照片，并注明拍摄位置与日期】",)], widths=[15.5])
    add_para(doc, "")
    make_table(doc,
               ["单位", "施工单位", "监理单位", "建设单位"],
               [("验收意见及签字", tpl.format("质检员/施工员签字"), tpl.format("监理工程师签字"), tpl.format("项目负责人签字")),
                ("日期", tpl.format("年 月 日"), tpl.format("年 月 日"), tpl.format("年 月 日"))],
               widths=[2.6, 4.3, 4.3, 4.3])
    save(doc, out_dir, "隐蔽工程验收记录模板.docx")

    # ---- 3. 分项工程质量验收记录 ----
    doc = Document()
    add_title(doc, "分项工程质量验收记录", size=16)
    add_para(doc, "（依据 GB 50300-2013 附录 E）", size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER, color=RGBColor(0x66, 0x66, 0x66), space_after=8)
    make_info_table(doc, [
        ("单位（子单位）工程名称", pn),
        ("分项工程名称", tpl.format("分项工程名称")),
        ("检验批数量", tpl.format("数量（个）")),
        ("施工单位项目负责人", tpl.format("姓名")),
        ("项目技术负责人", tpl.format("姓名")),
    ], widths=[4.5, 11.0])
    add_para(doc, "")
    make_table(doc,
               ["序号", "检验批部位、区段", "施工单位检查评定结果", "监理（建设）单位验收结论"],
               [(i, tpl.format("检验批部位"), "□ 合格　□ 不合格", "□ 合格　□ 不合格") for i in range(1, 5)],
               widths=[1.2, 5.2, 4.5, 4.6])
    add_para(doc, "")
    make_info_table(doc, [
        ("施工单位检查结果", tpl.format("项目专业技术负责人：合格/不合格，签字、日期")),
        ("监理（建设）单位验收结论", tpl.format("监理工程师：合格/不合格，签字、日期")),
        ("建设单位项目专业技术负责人", tpl.format("签字、日期")),
    ], widths=[4.5, 11.0])
    save(doc, out_dir, "分项工程质量验收记录模板.docx")

    # ---- 4. 分部工程质量验收记录 ----
    doc = Document()
    add_title(doc, "分部工程质量验收记录", size=16)
    add_para(doc, "（依据 GB 50300-2013 附录 F）", size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER, color=RGBColor(0x66, 0x66, 0x66), space_after=8)
    make_info_table(doc, [
        ("单位（子单位）工程名称", pn),
        ("分部（子分部）工程名称", tpl.format("分部工程名称")),
        ("分项工程数量", tpl.format("数量（项）")),
        ("施工单位项目负责人", tpl.format("姓名")),
        ("项目经理", tpl.format("姓名")),
    ], widths=[4.5, 11.0])
    add_para(doc, "")
    make_table(doc,
               ["序号", "分项工程名称", "检验批数量", "施工单位检查评定", "监理（建设）单位验收结论"],
               [(i, tpl.format("分项工程名称"), tpl.format("数量"), "□ 合格　□ 不合格", "□ 合格　□ 不合格")
                for i in range(1, 5)],
               widths=[1.2, 4.6, 2.2, 3.7, 3.8])
    add_para(doc, "")
    make_info_table(doc, [
        ("质量控制资料", "□ 完整　□ 基本完整　□ 不完整　" + tpl.format("核查意见")),
        ("安全和功能检验（检测）报告", "□ 齐全　□ 基本齐全　□ 缺项　" + tpl.format("核查意见")),
        ("观感质量验收", "□ 好　□ 一般　□ 差　" + tpl.format("验收意见")),
        ("验收结论", tpl.format("合格/不合格，验收组签字、日期")),
    ], widths=[4.5, 11.0])
    add_para(doc, "")
    make_table(doc,
               ["验收单位", "施工单位", "勘察单位*", "设计单位", "监理单位", "建设单位"],
               [("签字", tpl.format("项目负责人"), tpl.format("项目负责人"), tpl.format("项目负责人"),
                 tpl.format("总监理工程师"), tpl.format("项目负责人")),
                ("日期", tpl.format("年 月 日"), tpl.format("年 月 日"), tpl.format("年 月 日"),
                 tpl.format("年 月 日"), tpl.format("年 月 日"))],
               widths=[2.4, 2.7, 2.6, 2.6, 2.6, 2.6])
    add_para(doc, "* 勘察单位仅在地基与基础分部验收时参加。", size=9,
             color=RGBColor(0x66, 0x66, 0x66))
    save(doc, out_dir, "分部工程质量验收记录模板.docx")

    print(f"[records] 已生成 4 个模板到：{out_dir}")


# ---------------------------------------------------------------
# 子命令 c) report：竣工验收报告框架
# ---------------------------------------------------------------
def cmd_report(args):
    """生成竣工验收报告框架 Word 文档。"""
    out_dir = ensure_dir(args.output)
    doc = Document()
    add_title(doc, "工程竣工验收报告", size=18)
    add_para(doc, f"工程名称：{args.project_name}", size=12, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    add_h1(doc, "一、工程概况")
    make_info_table(doc, [
        ("工程名称", args.project_name),
        ("工程地点", args.location),
        ("建设规模", "【待填：建设规模（处理规模/建筑面积/管线长度等）】"),
        ("结构类型", "【待填：结构类型】"),
        ("层数/构筑物数量", "【待填：层数/构筑物数量】"),
        ("工程造价", args.cost),
        ("开工日期", "【待填：年 月 日】"),
        ("竣工日期", "【待填：年 月 日】"),
        ("合同编号", "【待填：合同编号】"),
        ("质量目标", "【待填：合格/优良等】"),
    ], widths=[4.5, 11.0])
    add_para(doc, "")

    add_h1(doc, "二、勘察、设计、施工、监理单位情况")
    make_table(doc,
               ["参建单位", "单位名称", "资质等级", "项目负责人", "联系电话"],
               [("建设单位", "【待填：名称】", "【待填】", "【待填】", "【待填】"),
                ("勘察单位", "【待填：名称】", "【待填】", "【待填】", "【待填】"),
                ("设计单位", "【待填：名称】", "【待填】", "【待填】", "【待填】"),
                ("施工单位", "【待填：名称】", "【待填】", "【待填】", "【待填】"),
                ("监理单位", "【待填：名称】", "【待填】", "【待填】", "【待填】"),
                ("质量监督机构", "【待填：名称】", "—", "—", "【待填】")],
               widths=[2.6, 4.4, 2.2, 2.6, 3.7])
    add_para(doc, "")

    add_h1(doc, "三、验收范围及内容")
    add_para(doc, "【待填：本次验收范围（单位/子单位工程、主要构筑物及设备系统）及验收内容】", size=11, space_after=4)
    add_para(doc, "【待填：含污水处理构筑物、工艺设备安装调试、电气自控、室外附属工程等验收内容】", size=11, space_after=8)

    add_h1(doc, "四、验收依据")
    for t in (
        "1. 《建设工程质量管理条例》（国务院令第279号）；",
        "2. 《房屋建筑工程和市政基础设施工程竣工验收暂行规定》（建质〔2000〕142号）；",
        "3. GB 50300-2013《建筑工程施工质量验收统一标准》及相应专业验收规范；",
        "4. 经审查合格的施工图设计文件及设计变更文件；",
        "5. 工程承包合同及补充协议、PPP项目合同及实施机构相关要求；",
        "6. 国家和地方现行有关法律法规、标准规范。",
    ):
        add_para(doc, t, size=11, space_after=2)

    add_h1(doc, "五、工程质量评定")
    add_para(doc, "（一）分部工程质量情况：", size=11, bold=True, space_after=2)
    add_para(doc, "【待填：各分部工程质量验收情况汇总】", size=11, space_after=4)
    add_para(doc, "（二）质量控制资料核查情况：", size=11, bold=True, space_after=2)
    add_para(doc, "【待填：资料核查结论（完整/基本完整）】", size=11, space_after=4)
    add_para(doc, "（三）安全和功能检验情况：", size=11, bold=True, space_after=2)
    add_para(doc, "【待填：主要功能检验、联动试运行、环保监测结论】", size=11, space_after=4)
    add_para(doc, "（四）观感质量情况：", size=11, bold=True, space_after=2)
    add_para(doc, "【待填：观感质量评定（好/一般/差）】", size=11, space_after=4)
    add_para(doc, "（五）综合评定：", size=11, bold=True, space_after=2)
    add_para(doc, "【待填：本工程质量综合评定结论】", size=11, space_after=8)

    add_h1(doc, "六、验收意见")
    add_para(doc, "□ 本工程竣工验收合格，同意交付使用。", size=11, space_after=2)
    add_para(doc, "□ 本工程存在下列问题，验收不合格：＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿，待整改后重新组织验收。",
             size=11, space_after=8)

    add_h1(doc, "七、参加验收人员签字栏")
    make_table(doc,
               ["单位", "姓名", "职务/职称", "验收意见", "签名"],
               [("建设单位", "", "", "", ""), ("勘察单位", "", "", "", ""),
                ("设计单位", "", "", "", ""), ("施工单位", "", "", "", ""),
                ("监理单位", "", "", "", ""), ("质量监督机构", "", "", "", "")],
               widths=[2.8, 2.4, 2.6, 4.2, 3.5])
    add_para(doc, "")
    add_para(doc, "报告编制单位（建设单位）：＿＿＿＿＿＿＿＿＿＿＿＿　　编制日期：＿＿＿＿年＿＿月＿＿日",
             size=11, space_after=0)

    path = save(doc, out_dir, "竣工验收报告框架.docx")
    print(f"[report] 已生成：{path}")


# ---------------------------------------------------------------
# 子命令 d) meeting：竣工验收会议全套文件
# ---------------------------------------------------------------
def cmd_meeting(args):
    """生成竣工验收会议全套文件（议程/名单/签到表/意见书框架）。"""
    out_dir = ensure_dir(args.output)
    pn = args.project_name

    # ---- 1. 验收会议议程 ----
    doc = Document()
    add_title(doc, "工程竣工验收会议议程", size=16)
    make_info_table(doc, [
        ("工程名称", pn),
        ("会议时间", args.meeting_date),
        ("会议地点", args.meeting_place),
        ("主持人", args.host),
        ("记录人", "【待填：记录人】"),
        ("参会单位", "建设单位、勘察单位、设计单位、施工单位、监理单位、质量监督机构（如有）"),
    ], widths=[3.4, 12.1])
    add_para(doc, "")
    add_h2(doc, "会议议程")
    for i, t in enumerate((
        "主持人宣布会议开始，介绍验收组成员及参会单位；",
        "建设单位介绍工程建设及竣工验收准备情况；",
        "施工单位汇报工程施工情况、自评结论；",
        "监理单位汇报监理情况、质量评估意见；",
        "勘察、设计单位发表工程质量意见；",
        "验收组进行现场实体质量检查、验收资料核查；",
        "各验收组成员发表意见，讨论形成验收意见；",
        "宣布验收结论，签署验收意见书。",
    ), start=1):
        add_para(doc, f"{i}. {t}", size=11, space_after=3)
    add_para(doc, "")
    add_para(doc, "注意事项：与会人员请提前 15 分钟签到；验收组应现场核查实体质量与验收资料；",
             size=10, color=RGBColor(0x59, 0x59, 0x59))
    save(doc, out_dir, "竣工验收会议议程.docx")

    # ---- 2. 验收组组成名单 ----
    doc = Document()
    add_title(doc, "竣工验收组组成名单", size=16)
    make_info_table(doc, [
        ("工程名称", pn),
        ("验收时间", args.meeting_date),
    ], widths=[3.4, 12.1])
    add_para(doc, "")
    make_table(doc,
               ["职务", "姓名", "工作单位", "职务/职称", "专业", "联系电话", "签字"],
               [("组长", "", "", "", "", "", ""),
                ("副组长", "", "", "", "", "", ""),
                ("副组长", "", "", "", "", "", ""),
                ("成员", "", "", "", "", "", ""),
                ("成员", "", "", "", "", "", ""),
                ("成员", "", "", "", "", "", ""),
                ("成员", "", "", "", "", "", "")],
               widths=[1.8, 1.9, 3.4, 2.4, 2.0, 2.0, 2.0])
    add_para(doc, "")
    add_para(doc, "注：验收组由建设单位牵头组织，成员应包括勘察、设计、施工、监理等单位项目负责人及聘请的专家。",
             size=9, color=RGBColor(0x66, 0x66, 0x66))
    save(doc, out_dir, "竣工验收验收组名单.docx")

    # ---- 3. 验收会议签到表 ----
    doc = Document()
    add_title(doc, "竣工验收会议签到表", size=16)
    make_info_table(doc, [
        ("会议名称", f"{pn} 工程竣工验收会议"),
        ("会议时间", args.meeting_date),
        ("会议地点", args.meeting_place),
    ], widths=[3.4, 12.1])
    add_para(doc, "")
    rows = [(i, "", "", "", "", "") for i in range(1, 15)]
    make_table(doc,
               ["序号", "姓名", "单位", "职务", "联系电话", "签名"],
               rows, widths=[1.4, 2.4, 4.0, 2.6, 2.6, 2.5])
    save(doc, out_dir, "竣工验收会议签到表.docx")

    # ---- 4. 验收意见书框架 ----
    doc = Document()
    add_title(doc, "工程竣工验收意见书", size=16)
    add_para(doc, f"工程名称：{pn}", size=12, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    add_h1(doc, "一、工程概况")
    make_info_table(doc, [
        ("工程名称", pn),
        ("工程地点", "【待填：工程地点】"),
        ("建设规模", "【待填：建设规模】"),
        ("建设单位", "【待填：名称】"),
        ("勘察单位", "【待填：名称】"),
        ("设计单位", "【待填：名称】"),
        ("施工单位", "【待填：名称】"),
        ("监理单位", "【待填：名称】"),
    ], widths=[3.4, 12.1])
    add_para(doc, "")
    add_h1(doc, "二、验收组织情况")
    add_para(doc, "验收时间：＿＿＿＿年＿＿月＿＿日；验收地点：＿＿＿＿＿＿＿＿＿＿。", size=11, space_after=4)
    add_para(doc, "验收组组长：＿＿＿＿＿＿；副组长：＿＿＿＿＿＿；成员共＿＿人（名单附后）。", size=11, space_after=8)
    add_h1(doc, "三、验收依据及程序")
    add_para(doc, "依据《建设工程质量管理条例》、建质〔2000〕142号、GB 50300-2013 及施工合同约定，"
                  "按照听取汇报、现场检查、资料核查、讨论评议的程序组织验收。", size=11, space_after=8)
    add_h1(doc, "四、验收结论")
    add_para(doc, "□ 本工程竣工验收合格，同意交付使用。", size=12, bold=True, space_after=4)
    add_para(doc, "□ 本工程存在下列问题，验收不合格，待整改后重新组织验收：", size=12, bold=True, space_after=2)
    add_para(doc, "【待填：存在问题及整改要求】", size=11, space_after=8)
    add_h1(doc, "五、验收组签字")
    make_table(doc,
               ["职务", "姓名", "单位", "签字", "日期"],
               [("组长", "", "", "", ""), ("副组长", "", "", "", ""),
                ("成员", "", "", "", ""), ("成员", "", "", "", ""),
                ("成员", "", "", "", ""), ("成员", "", "", "", "")],
               widths=[2.0, 2.4, 4.2, 3.4, 3.5])
    add_para(doc, "")
    add_para(doc, "（本意见书一式＿份，建设单位、施工单位、监理单位、实施机构/质监机构各执一份）",
             size=9, color=RGBColor(0x66, 0x66, 0x66))
    save(doc, out_dir, "竣工验收意见书框架.docx")

    print(f"[meeting] 已生成 4 个文件到：{out_dir}")


# ---------------------------------------------------------------
# v1.1.0 新增：分部分项划分表（GB 50300-2013 要求，污水厂工程）
# ---------------------------------------------------------------
# 市政污水厂工程分部分项划分（依据 GB 50300-2013 + GB 50268-2008 习惯做法）
DIVISIONS = [
    ("地基与基础分部", ["土方开挖检验批", "土方回填检验批", "混凝土垫层检验批", "钢筋加工/安装检验批", "模板安装/拆除检验批", "混凝土浇筑检验批", "地基处理（换填/强夯）检验批"]),
    ("主体结构分部（构筑物）", ["池体底板混凝土检验批", "池壁混凝土检验批", "池顶板/走道板检验批", "预埋件/预留孔洞检验批", "防水混凝土检验批", "满水试验记录（功能性检验）"]),
    ("主体结构分部（建筑物）", ["综合楼/机修间砌体检验批", "钢筋混凝土框架梁柱检验批", "屋面工程检验批", "装饰装修检验批", "门窗安装检验批"]),
    ("建筑给排水及供暖分部", ["给水管网安装检验批", "排水管道安装检验批", "卫生器具安装检验批", "管道试压/冲洗记录"]),
    ("建筑电气分部", ["电缆桥架/线槽安装检验批", "配管配线检验批", "照明器具安装检验批", "防雷接地检验批", "电气通电试运行记录"]),
    ("工艺设备安装分部", ["粗格栅/细格栅安装检验批", "提升泵/回流泵安装检验批", "鼓风机安装检验批", "刮泥机/吸泥机安装检验批", "加药设备安装检验批", "消毒设备安装检验批", "污泥脱水设备安装检验批", "设备单机试运转记录"]),
    ("工艺管道分部", ["进水管/出水管安装检验批", "工艺连接管道安装检验批", "加药管/污泥管安装检验批", "管道水压/闭水试验记录", "管道冲洗消毒记录"]),
    ("自动化仪表与监控分部", ["仪表安装检验批", "PLC控制柜安装检验批", "监控系统安装检验批", "自控系统联调记录"]),
    ("室外附属分部", ["道路工程检验批", "围墙/大门检验批", "绿化工程检验批", "室外照明检验批"]),
]

def cmd_divisions(args):
    """生成污水厂工程分部分项划分表（Word）"""
    doc = Document()
    add_title(doc, "市政污水处理厂工程 分部分项划分表")
    add_para(doc, f"工程名称：{args.project_name}", size=11, space_after=4)
    add_para(doc, f"依据：《建筑工程施工质量验收统一标准》GB 50300-2013、《给水排水管道工程施工及验收规范》GB 50268-2008", size=10, space_after=8)
    add_h1(doc, "一、划分原则")
    add_para(doc, "1. 单位工程按独立施工条件或独立使用功能划分；分部工程按专业性质、建筑部位划分；分项工程按主要工种、材料、施工工艺、设备类别划分；检验批按工程量、楼层、施工段划分。", size=10.5, space_after=4)
    add_para(doc, "2. 本表为市政污水厂工程典型划分，实际项目应按施工图纸、合同范围及当地质监站要求调整；划分结果须经监理工程师确认。", size=10.5, space_after=8)
    add_h1(doc, "二、分部分项划分明细")
    rows = []
    idx = 1
    for div_name, items in DIVISIONS:
        rows.append((str(idx), div_name, "、".join(items), "", ""))
        idx += 1
    make_table(doc, ["序号", "分部工程", "分项工程（检验批）", "验收批数", "备注"], rows,
               widths=[1.2, 4.0, 8.0, 1.6, 1.6])
    add_para(doc, "")
    add_h1(doc, "三、使用说明")
    add_para(doc, "1. 验收批数由施工单位按实际检验批划分填写，监理复核；", size=10.5, space_after=4)
    add_para(doc, "2. 每个分部工程验收前须形成分项工程质量验收记录、分部工程质量验收记录；", size=10.5, space_after=4)
    add_para(doc, "3. 隐蔽工程（地基、钢筋、预埋件、防水层等）须先办理隐蔽验收记录再进入下道工序；", size=10.5, space_after=4)
    add_para(doc, "4. 满水试验、闭水试验、单机试运转等功能性检验记录作为分部验收的必备附件。", size=10.5, space_after=8)
    out_dir = Path(args.output)
    ensure_dir(out_dir)
    save(doc, out_dir, "污水厂工程分部分项划分表.docx")
    print(f"[divisions] 已生成污水厂分部分项划分表到：{out_dir}")


# ---------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        prog="acceptance_tools",
        description="工程验收全套资料生成工具（依据《建设工程质量管理条例》、建质〔2000〕142号、GB 50300-2013）")
    sub = parser.add_subparsers(dest="command", required=True, help="子命令")

    p = sub.add_parser("checklist", help="生成验收资料核对清单")
    p.add_argument("-o", "--output", default="./output", help="输出目录（默认 ./output）")
    p.add_argument("--project-name", default="【待填：工程名称】", help="工程名称")
    p.set_defaults(func=cmd_checklist)

    p = sub.add_parser("records", help="生成检验批/隐蔽/分项/分部验收记录模板包")
    p.add_argument("-o", "--output", default="./output", help="输出目录（默认 ./output）")
    p.add_argument("--project-name", default="【待填：工程名称】", help="工程名称")
    p.set_defaults(func=cmd_records)

    p = sub.add_parser("report", help="生成竣工验收报告框架")
    p.add_argument("-o", "--output", default="./output", help="输出目录（默认 ./output）")
    p.add_argument("--project-name", default="【待填：工程名称】", help="工程名称")
    p.add_argument("--location", default="【待填：工程地点】", help="工程地点")
    p.add_argument("--cost", default="【待填：工程造价】", help="工程造价")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("meeting", help="生成竣工验收会议全套文件")
    p.add_argument("-o", "--output", default="./output", help="输出目录（默认 ./output）")
    p.add_argument("--project-name", default="【待填：工程名称】", help="工程名称")
    p.add_argument("--meeting-date", default="【待填：年 月 日】", help="会议时间")
    p.add_argument("--meeting-place", default="【待填：会议地点】", help="会议地点")
    p.add_argument("--host", default="【待填：主持人】", help="会议主持人")
    p.set_defaults(func=cmd_meeting)

    p = sub.add_parser("divisions", help="生成污水厂工程分部分项划分表（GB 50300-2013）")
    p.add_argument("-o", "--output", default="./output", help="输出目录（默认 ./output）")
    p.add_argument("--project-name", default="【待填：工程名称】", help="工程名称")
    p.set_defaults(func=cmd_divisions)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
