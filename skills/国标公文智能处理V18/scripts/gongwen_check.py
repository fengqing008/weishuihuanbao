#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
国标公文智能处理 - 格式校验工具 v2
新增：中文标点符号校验、页码格式校验、字体嵌入校验
"""
import sys
import io
import os
import argparse
import zipfile
from datetime import datetime as dt

if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn

# ============ 标准值 ============
STANDARD = {
    'top_margin': Cm(3.7),
    'bottom_margin': Cm(3.5),
    'left_margin': Cm(2.8),
    'right_margin': Cm(2.6),
    'margin_tol': Cm(0.1),
    'line_spacing': Pt(28),
    'line_spacing_tol': Pt(1),
    'first_indent': Pt(32),
    'first_indent_tol': Pt(2),
    'body_fonts': ['仿宋_GB2312', '仿宋', 'FangSong'],
    'title_fonts': ['方正小标宋简体', '黑体'],
    'heading1_fonts': ['黑体'],
    'page_num_font': '宋体',
}

# 中文标点字符集
CN_PUNCT = set('\u3002\uff0c\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09\u300a\u300b\u3010\u3011\u3001\u2014\uff5e\u3014\u3015\u3008\u3009')
# 禁止在中文公文中出现的英文标点
EN_PUNCT_FORBIDDEN = {',', ';', ':', '(', ')', '"', "'"}


def _pt_str(val):
    if val is None:
        return "None"
    try:
        return f"{val / 12700:.1f}pt"
    except Exception:
        return str(val)


def _cm_str(val):
    if val is None:
        return "None"
    try:
        return f"{val / 360000:.2f}cm"
    except Exception:
        return str(val)


def check_page_setup(doc):
    """页面设置检查"""
    issues = []
    for section in doc.sections:
        for attr, std_val, label in [
            ('top_margin', STANDARD['top_margin'], '上'),
            ('bottom_margin', STANDARD['bottom_margin'], '下'),
            ('left_margin', STANDARD['left_margin'], '左'),
            ('right_margin', STANDARD['right_margin'], '右'),
        ]:
            val = getattr(section, attr)
            if val is not None and abs(val - std_val) > STANDARD['margin_tol']:
                issues.append(f"页边距-{label}: 期望 {_cm_str(std_val)}, 实际 {_cm_str(val)}")
    return issues


def check_punctuation(text: str, para_idx: int) -> list:
    """检查段落文本中的英文标点"""
    issues = []
    for i, ch in enumerate(text):
        if ch in EN_PUNCT_FORBIDDEN:
            context = text[max(0, i-3):i+4]
            issues.append(f"英文标点(段落{para_idx}): 发现 '{ch}' 在 \"...{context}...\"")
    return issues


def check_paragraphs(doc):
    """段落格式和标点检查"""
    issues = []
    stats = {'total': 0, 'indent_ok': 0, 'spacing_ok': 0, 'font_ok': 0, 'punct_ok': 0}

    for idx, para in enumerate(doc.paragraphs, 1):
        text = para.text.strip()
        if not text:
            continue
        pf = para.paragraph_format
        stats['total'] += 1

        # 行距检查
        if pf.line_spacing is not None:
            try:
                if abs(pf.line_spacing - STANDARD['line_spacing']) <= STANDARD['line_spacing_tol']:
                    stats['spacing_ok'] += 1
                elif stats['total'] <= 5:
                    issues.append(f"行距(段落{idx}): 期望28pt, 实际{_pt_str(pf.line_spacing)}")
            except Exception:
                pass

        # 段间距检查
        if pf.space_before is not None and pf.space_before > Pt(3) and stats['total'] <= 5:
            issues.append(f"段前间距(段落{idx}): {_pt_str(pf.space_before)}")
        if pf.space_after is not None and pf.space_after > Pt(3) and stats['total'] <= 5:
            issues.append(f"段后间距(段落{idx}): {_pt_str(pf.space_after)}")

        # 首行缩进检查
        if pf.first_line_indent is not None:
            if abs(pf.first_line_indent - STANDARD['first_indent']) <= STANDARD['first_indent_tol']:
                stats['indent_ok'] += 1

        # 字体检查
        font_match = False
        for run in para.runs:
            if run.font.name in STANDARD['body_fonts']:
                font_match = True
                break
        if font_match:
            stats['font_ok'] += 1

        # 【新增】标点符号检查
        punct_issues = check_punctuation(text, idx)
        if punct_issues:
            issues.extend(punct_issues)
        else:
            stats['punct_ok'] += 1

    return issues, stats


def check_page_number(doc):
    """【新增】页码格式检查：双面打印、奇偶页对齐"""
    issues = []
    for si, section in enumerate(doc.sections, 1):
        sectPr = section._sectPr
        evenAndOdd = sectPr.find(qn('w:evenAndOddHeaders'))
        if evenAndOdd is None:
            issues.append(f"页码(第{si}节): 未启用奇偶页不同 (w:evenAndOddHeaders)")

        # 检查奇数页页脚
        footer = section.footer
        if footer.is_linked_to_previous:
            issues.append(f"页码(第{si}节): 奇数页页脚链接到上一节，可能被覆盖")

        # 检查偶数页页脚
        even_footer = section.even_page_footer
        if even_footer.is_linked_to_previous:
            issues.append(f"页码(第{si}节): 偶数页页脚链接到上一节，可能被覆盖")
    return issues


def check_fonts_embedded(filepath):
    """【新增】检查字体是否嵌入文档"""
    issues = []
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            font_files = [f for f in z.namelist() if f.startswith('word/fonts/') and f.endswith('.ttf')]
            if not font_files:
                # 检查 [Content_Types].xml 中是否有字体声明
                ct = z.read('[Content_Types].xml').decode('utf-8')
                if 'application/x-font-ttf' in ct:
                    issues.append("字体嵌入: Content_Types 已声明但未找到实际字体文件")
                else:
                    issues.append("字体嵌入: 未嵌入任何字体文件（建议嵌入仿宋_GB2312和方正小标宋简体）")
            else:
                for ff in font_files:
                    basename = os.path.basename(ff)
                    issues.append(f"字体嵌入: 已嵌入 {basename} (OK)")
    except Exception as e:
        issues.append(f"字体嵌入检查失败: {e}")
    return issues


def check_document(filepath):
    """综合校验"""
    doc = Document(filepath)
    all_issues = []
    all_stats = {}

    # 页面设置
    page_issues = check_page_setup(doc)
    all_issues.extend([f"[页面] {i}" for i in page_issues])

    # 段落格式 + 标点
    para_issues, stats = check_paragraphs(doc)
    all_issues.extend([f"[段落] {i}" for i in para_issues])
    all_stats = stats

    # 页码
    pn_issues = check_page_number(doc)
    all_issues.extend([f"[页码] {i}" for i in pn_issues])

    # 字体嵌入
    fi_issues = check_fonts_embedded(filepath)
    all_issues.extend([f"[字体嵌入] {i}" for i in fi_issues])

    # 输出报告
    print("=" * 60)
    print("公文格式校验报告 v2")
    print(f"文件: {filepath}")
    print(f"日期: {dt.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print(f"\n[统计]")
    print(f"  段落总数: {all_stats.get('total', 0)}")
    print(f"  行距合规: {all_stats.get('spacing_ok', 0)}/{all_stats.get('total', 1)}")
    print(f"  缩进合规: {all_stats.get('indent_ok', 0)}/{all_stats.get('total', 1)}")
    print(f"  字体合规: {all_stats.get('font_ok', 0)}/{all_stats.get('total', 1)}")
    print(f"  标点合规: {all_stats.get('punct_ok', 0)}/{all_stats.get('total', 1)}")

    critical = [i for i in all_issues if '[字体嵌入]' not in i or 'OK' not in i.split('(OK)')[0] if '(OK)' not in i]
    font_ok_msgs = [i for i in all_issues if '(OK)' in i]

    if critical:
        print(f"\n[!] 发现 {len(critical)} 个问题:")
        for i, issue in enumerate(critical, 1):
            print(f"  {i}. {issue}")
    else:
        print(f"\n[PASS] 核心格式校验通过。")

    if font_ok_msgs:
        print(f"\n[字体嵌入]")
        for msg in font_ok_msgs:
            print(f"  {msg}")

    return all_issues


def main():
    parser = argparse.ArgumentParser(description="gongwen check v2")
    parser.add_argument("--file", "-f", type=str, required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"[ERROR] file not found: {args.file}")
        sys.exit(1)

    issues = check_document(args.file)
    critical = [i for i in issues if '(OK)' not in i]
    sys.exit(0 if not critical else 1)


if __name__ == "__main__":
    main()
