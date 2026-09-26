#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP Word文档生成器
- 基于GB/T 9704-2012排版
- 12章标准结构
- Word内置Heading 1/2样式（导航窗格可用）
- 四方签字约定嵌入

Usage:
    python3 sop_docx_generator.py --title "XXX项目竣工结算SOP" \\
        --baseline-date "2019年7月" --output "SOP_V1.0.docx"
"""
import argparse
import os
from datetime import date as _today
from pathlib import Path
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ============== 字体常量 ==============
FONT_TITLE = '方正小标宋_GB2312'
FONT_H1 = '黑体'
FONT_H2 = '楷体_GB2312'
FONT_BODY = '仿宋_GB2312'
FONT_EN = 'Times New Roman'
SIZE_TITLE = 22
SIZE_H1 = 16
SIZE_H2 = 16
SIZE_BODY = 16
SIZE_TABLE = 10.5


def set_run(run, cn_font, size, bold=False, color=None):
    run.font.name = FONT_EN
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), cn_font)
    rFonts.set(qn('w:ascii'), FONT_EN)
    rFonts.set(qn('w:hAnsi'), FONT_EN)


def configure_styles(doc):
    """配置Word内置标题样式"""
    styles = doc.styles
    # Normal
    n = styles['Normal']
    n.font.name = FONT_EN
    n.font.size = Pt(SIZE_BODY)
    rPr = n.element.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:eastAsia'), FONT_BODY)
    rFonts.set(qn('w:ascii'), FONT_EN)
    rFonts.set(qn('w:hAnsi'), FONT_EN)
    for old in rPr.findall(qn('w:rFonts')):
        rPr.remove(old)
    rPr.insert(0, rFonts)
    # Heading 1
    h1 = styles['Heading 1']
    h1.font.name = FONT_EN
    h1.font.size = Pt(SIZE_H1)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0, 0, 0)
    rPr = h1.element.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:eastAsia'), FONT_H1)
    rFonts.set(qn('w:ascii'), FONT_EN)
    rFonts.set(qn('w:hAnsi'), FONT_EN)
    for old in rPr.findall(qn('w:rFonts')):
        rPr.remove(old)
    rPr.insert(0, rFonts)
    # Heading 2
    h2 = styles['Heading 2']
    h2.font.name = FONT_EN
    h2.font.size = Pt(SIZE_H2)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0, 0, 0)
    rPr = h2.element.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:eastAsia'), FONT_H2)
    rFonts.set(qn('w:ascii'), FONT_EN)
    rFonts.set(qn('w:hAnsi'), FONT_EN)
    for old in rPr.findall(qn('w:rFonts')):
        rPr.remove(old)
    rPr.insert(0, rFonts)


def setup_margins(section):
    section.top_margin = Mm(37)
    section.bottom_margin = Mm(35)
    section.left_margin = Mm(28)
    section.right_margin = Mm(26)
    section.page_height = Mm(297)
    section.page_width = Mm(210)


def add_h1(doc, text):
    p = doc.add_paragraph(text, style='Heading 1')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def add_h2(doc, text):
    p = doc.add_paragraph(text, style='Heading 2')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def add_body(doc, text):
    return doc.add_paragraph(text)


def add_body_runs(doc, segments):
    p = doc.add_paragraph()
    for text, bold in segments:
        run = p.add_run(text)
        set_run(run, FONT_BODY, SIZE_BODY, bold)
    return p


def build_sop(title, baseline_date, project_name, output_path,
              date_str=None, doc_no='【待核：发文字号】',
              drafting_unit='某环境工程有限公司'):
    if not date_str:
        t = _today.today()
        date_str = f'{t.year}年{t.month}月{t.day}日'
    doc = Document()
    section = doc.sections[0]
    setup_margins(section)
    configure_styles(doc)

    # 标题
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run(title), FONT_TITLE, SIZE_TITLE, True)
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_after = Pt(12)

    # 元数据
    for line in [
        f'文件编号：{doc_no}',
        f'版本：V1.0',
        f'编制单位：{drafting_unit}',
        f'落款单位：{drafting_unit}',
        f'成文日期：{date_str}',
        '施行日期：自发布之日起施行',
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run(p.add_run(line), FONT_H2, 14)
        p.paragraph_format.first_line_indent = Pt(0)

    # 第一章
    add_h1(doc, '一、编制目的与依据')
    add_h2(doc, '（一）目的')
    add_body(doc, f'统一{project_name}竣工结算编制口径与工程量核定流程，规范施工单位结算资料报送标准，保障结算审计有序推进、防止漏报错报、控制审计风险。')
    add_h2(doc, '（二）依据')
    laws = [
        f'1. {project_name}《施工总承包合同》（专用条款第11.1条“价格调整”、第11.4条“材料调差”）。',
        f'2. 某环境工程有限公司2026年7月8日《竣工结算专题会议纪要》（建设单位内部印发）。',
        f'3. 财政部、原建设部《建设工程价款结算暂行办法》（财建〔2004〕369号，本项目合同签订时适用版本）。',
        f'4. 《建设工程工程量清单计价规范》（GB 50500-2013）；《市政工程工程量计算规范》（GB 50857-2013）。',
        f'5. 陕西省住房和城乡建设厅《陕西省建设工程造价管理办法》及{baseline_date}当期《陕西工程造价管理信息》材料信息价。',
        f'6. 现行《建设工程文件归档规范》（GB/T 50328-2019）。',
    ]
    for l in laws:
        add_body(doc, l)

    # 第二章
    add_h1(doc, '二、适用范围与术语')
    add_h2(doc, '（一）适用范围')
    add_body(doc, f'适用于{project_name}竣工结算编制、审核、报送全过程；约束建设单位、监理单位、审计单位、总承包单位统一执行。')
    add_h2(doc, '（二）术语定义')
    for term, defn in [
        ('基准价', f'合同约定的固定一期信息价，本项目统一采用{baseline_date}当期陕西《工程造价管理信息》材料信息价。'),
        ('合同内工程量', '施工总承包合同约定范围内、按图施工、严格对应竣工图纸的工程量。'),
        ('合同外工程量', '合同约定范围外、由设计变更、现场签证、技术核定单、图纸会审记录等过程资料支撑的工程量。'),
        ('主材调差', '合同约定允许调差的主材（钢材、商品混凝土、砂石、水泥、HDPE双壁波纹管、PE管、电缆等大宗材料）。'),
        ('辅材', '除主材以外的零星材料，不参与调差。'),
        ('签证施工内容', '通过设计变更通知单、技术核定单、工程签证单等过程资料确认的施工内容。'),
    ]:
        add_body_runs(doc, [(f'{term}：', True), (defn, False)])

    # 第三章
    add_h1(doc, '三、结算基准')
    add_h2(doc, '（一）基准数据')
    add_body(doc, '所有工程量计算严格以签字盖章的竣工图为基准数据。接户管工程量以建设单位、监理单位、施工单位三方现场复核确认文件为基准（与竣工图同步提交）；站点工程以竣工图为准。')
    add_h2(doc, '（二）基准价')
    add_body(doc, f'材料基准价统一执行{baseline_date}当期陕西《工程造价管理信息》材料信息价（即项目开工当月信息价）。项目所有标段、所有施工单位、所有分部分项工程的相同清单子目，基准价须一致。')
    add_h2(doc, '（三）清单子目单价一致性原则')
    add_body(doc, '相同清单子目在不同标段、不同施工单位的结算书中单价须保持一致；上报结算书中相同清单项单价存在差异的，审计按低价予以认定。')

    # 第四章
    add_h1(doc, '四、结算书结构')
    add_h2(doc, '（一）整体划分')
    add_body_runs(doc, [('结算书整体分为两大部分，顺序固定、不得颠倒：', False)])
    add_body_runs(doc, [('第一部分——合同范围内工程量：', True), ('严格对应竣工图纸，按图计算、按图计量。', False)])
    add_body_runs(doc, [('第二部分——合同范围外工程量：', True), ('涵盖设计变更、现场签证、技术核定单、图纸会审纪要等过程资料支撑的全部内容。', False)])
    add_h2(doc, '（二）单据编号规则')
    add_body(doc, '1. 有正式编号的变更/签证单据，按原编号直接列入第二部分对应分部分项；')
    add_body(doc, '2. 无正式编号的单据，由施工单位自行统一编制编号；')
    add_body(doc, '3. 第二部分严禁漏项。')
    add_h2(doc, '（三）清单项目层级')
    add_body(doc, '结算书层级遵循"单位工程→分部工程→分项工程→清单子目"四级结构。')

    # 第五章
    add_h1(doc, '五、工程量核定流程')
    add_h2(doc, '（一）总体原则')
    add_body(doc, '竣工图与结算书严格对应；结算书编制技术人员与竣工图绘制人员须充分对接沟通。')
    add_h2(doc, '（二）管网工程量核定')
    add_body(doc, '按竣工图逐项比对管段长度、检查井数量、接户管长度、管径规格、基础形式、接口做法。')
    add_h2(doc, '（三）站点工程量核定')
    add_body(doc, '按竣工图核查站点工程量及完整性（建构筑物、工艺设备、电气、自控、给排水等）。')

    # 第六章（核心：四方签字约定）
    add_h1(doc, '六、工程量差异处理')
    add_h2(doc, '（一）管网工程量差异（启动工程量确认表流程）')
    add_body(doc, '触发条件：实际管网工程量与竣工图存在差异。')
    add_body_runs(doc, [('四方签章缺一不可：', True)])
    add_body_runs(doc, [('1. 施工单位填报签字盖章；', False)])
    add_body_runs(doc, [('2. 设计单位专业设计负责人签字盖章；', False)])
    add_body_runs(doc, [('3. 监理单位总监理工程师签字盖章；', False)])
    add_body_runs(doc, [('4. 建设单位项目负责人签字盖章。', False)])
    add_body(doc, '底线规则：任何管网差异量无四方签字盖章齐全的工程量确认表支撑，结算审计不予认定。')

    add_h2(doc, '（二）站点工程量差异（启动图纸会审流程）')
    add_body(doc, '触发条件：站点工程实际施工与竣工图不一致或存在缺漏。')
    add_body_runs(doc, [('四方签字缺一不可：', True)])
    add_body_runs(doc, [('1. 施工单位项目技术负责人签字；', False)])
    add_body_runs(doc, [('2. 设计单位专业设计负责人签字；', False)])
    add_body_runs(doc, [('3. 监理单位项目技术负责人签字；', False)])
    add_body_runs(doc, [('4. 建设单位项目技术负责人签字。', False)])
    add_body(doc, '底线规则：图纸会审记录未签字盖章齐全的，差异量不予认定。')

    add_h2(doc, '（三）签字盖章栏格式')
    add_body(doc, '工程量确认表、图纸会审记录的签字盖章栏按既有模板执行；日期采用阿拉伯数字标全年月日。')

    # 第七章
    add_h1(doc, '七、结算编制公式')
    add_h2(doc, '（一）分部分项工程费')
    add_body_runs(doc, [('分部分项工程费＝∑（工程量×综合单价）', True)])
    add_h2(doc, '（二）措施项目费')
    add_body(doc, '措施项目费按合同约定费率及方式计算。')
    add_h2(doc, '（三）其他项目费')
    add_body(doc, '暂列金额、计日工、总承包服务费按合同约定。')
    add_h2(doc, '（四）规费与税金')
    add_body(doc, '按省级主管部门发布的现行规费费率和国家现行增值税税率计算。')
    add_h2(doc, '（五）主材调差计算')
    add_body_runs(doc, [('主材调差金额＝∑[主材用量Q×（施工当期信息价-基准价）]', True)])
    add_body(doc, '其中：Q = 对应分部分项工程结算量 × 定额消耗量，按现行定额执行。')

    # 第八章
    add_h1(doc, '八、签证与材料调差规则')
    add_h2(doc, '（一）签证施工内容')
    add_body(doc, '签证施工内容不参与基准价与施工当期价的差额调差，结算单价按实际施工当期信息价执行。')
    add_h2(doc, '（二）材料调差')
    add_body(doc, f'基准价：{baseline_date}当期信息价（全项目统一）；按各施工阶段对应信息价与基准价之差执行；主材调差，辅材不调差。')

    # 第九章
    add_h1(doc, '九、必备资料清单')
    add_body(doc, '各施工单位报送结算资料须完整包含以下内容（纸质签章版+电子版，缺一不予受理）：')
    items = [
        '竣工图纸资料', '变更签证资料', '过程资料', '验收文件',
        '结算书', '工程量确认表（四方签字盖章）', '图纸会审记录（四方签字盖章）',
        '接户管现场收方资料', '拆除恢复工程现场收方资料', '垃圾外运运距证明资料',
        '工期延期证明文件', '调差阶段证明资料',
    ]
    for i, it in enumerate(items, 1):
        add_body(doc, f'{i}. {it}')

    # 第十章
    add_h1(doc, '十、报送流程与时点')
    add_h2(doc, '（一）报送原则')
    add_body(doc, '竣工验收完成后1个月内施工单位完成结算资料编制。')
    add_h2(doc, '（二）报送节点')
    add_body(doc, '1. 施工单位向建设单位提交结算资料；2. 建设单位组织资料完整性初核；3. 初核通过后移交审计单位开展审核；4. 审计单位出具审核意见；5. 最终出具定案表。')

    # 第十一章
    add_h1(doc, '十一、签字盖章与归档')
    add_h2(doc, '（一）签字盖章要求')
    add_body(doc, '1. 工程量确认表、图纸会审记录、变更签证单等过程资料须四方签字盖章齐全。')
    add_h2(doc, '（二）档案管理')
    add_body(doc, '纸质件按"建设项目-单项工程-单位工程-分部工程"四级组卷；归档保存期限按GB/T 50328-2019执行。')

    # 第十二章
    add_h1(doc, '十二、附则')
    add_h2(doc, '（一）解释主体')
    add_body(doc, '本规程由某环境工程有限公司工程线（总工办）负责解释。')
    add_h2(doc, '（二）施行日期')
    add_body(doc, '本规程自发布之日起施行；未尽事宜按合同约定、会议纪要及国家现行有关规定执行。')

    # 落款
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run(p.add_run('落款：'), FONT_H2, SIZE_BODY, True)
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(18)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run(p.add_run(drafting_unit), FONT_H2, SIZE_BODY, True)
    p.paragraph_format.first_line_indent = Pt(0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run(p.add_run(date_str), FONT_H2, SIZE_BODY, True)
    p.paragraph_format.first_line_indent = Pt(0)

    doc.save(output_path)
    size = os.path.getsize(output_path)
    return f'✓ 已生成：{output_path}（{size/1024:.1f}KB）'


def main():
    parser = argparse.ArgumentParser(description='SOP Word生成器')
    parser.add_argument('--title', required=True, help='SOP标题')
    parser.add_argument('--project-name', required=True, help='项目名称')
    parser.add_argument('--baseline-date', required=True, help='基准价日期（如"2019年7月"）')
    parser.add_argument('--output', required=True, help='输出docx路径')
    parser.add_argument('--date', default=None, help='成文日期（默认取系统当天，格式如 2026年9月11日）')
    parser.add_argument('--doc-no', default='【待核：发文字号】', help='文件编号')
    parser.add_argument('--drafting-unit', default='某环境工程有限公司', help='编制/落款单位')
    args = parser.parse_args()
    print(build_sop(args.title, args.baseline_date, args.project_name, args.output,
                    date_str=args.date, doc_no=args.doc_no, drafting_unit=args.drafting_unit))


if __name__ == '__main__':
    main()
