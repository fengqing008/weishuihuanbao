#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP质量门禁
- 条款编号连续性检查
- 法规/标准名称规范性
- 四方签字约定核验
- 关键词/AI味扫描

Usage:
    python3 sop_quality_check.py --file "SOP.docx"
    python3 sop_quality_check.py --file "SOP.md"
"""
import argparse
import re
from pathlib import Path
from collections import Counter

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def read_text(file_path):
    p = Path(file_path)
    if p.suffix == '.docx':
        if not HAS_DOCX:
            return ''
        doc = Document(file_path)
        return '\n'.join(par.text for par in doc.paragraphs if par.text.strip())
    return p.read_text(encoding='utf-8')


def check_clause_numbering(text):
    """检查条款编号是否连续"""
    matches = re.findall(r'第([一二三四五六七八九十百零]+)条', text, re.M)
    chinese_num = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100,'零':0}

    def parse(s):
        if s == '十': return 10
        if '十' in s:
            parts = s.split('十')
            high = chinese_num.get(parts[0], 1) if parts[0] else 1
            low = chinese_num.get(parts[1], 0) if parts[1] else 0
            return high*10 + low
        return chinese_num.get(s, 0)

    nums = [parse(m) for m in matches]
    if not nums:
        # 回退：兼容"章-节"层级体例（一、二、… + （一）（二）…）
        chapters = re.findall(r'^\s*([一二三四五六七八九十]+)、', text, re.M)
        sections = re.findall(r'^\s*（([一二三四五六七八九十]+)）', text, re.M)
        if not chapters:
            return '⚠ 未发现条款编号'
        expect = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
                  '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']
        if chapters != expect[:len(chapters)]:
            return f'⚠ 章编号不连续：{chapters}'
        extra = f'，节编号 {len(sections)} 个' if sections else ''
        return f'✓ 章编号连续：{len(chapters)}章（一—{chapters[-1]}）{extra}'

    # 查重
    dup = [n for n, c in Counter(nums).items() if c > 1]
    # 查跳号
    sorted_nums = sorted(set(nums))
    gaps = [(sorted_nums[i], sorted_nums[i+1])
            for i in range(len(sorted_nums)-1) if sorted_nums[i+1] - sorted_nums[i] > 1]

    issues = []
    if dup:
        issues.append(f'❌ 重复编号：{dup}')
    if gaps:
        issues.append(f'⚠ 跳号区间：{gaps}')
    if not issues:
        return f'✓ 编号连续：{len(nums)}条（1-{max(nums)}）'
    return '\n  '.join(issues)


def check_law_names(text):
    """核验法规/标准名称规范性"""
    issues = []
    # 法规必须带书名号
    laws = re.findall(r'《([^》]+)》', text)
    # 非法规类书名号（合同/纪要/信息价/记录/清单等）不纳入法规规范检查
    non_law_kw = ['合同', '纪要', '信息', '协议', '方案', '记录', '清单', '报告', '表', '证明', '文件']
    bad_laws = [l for l in laws
                if not re.search(r'[法规定办法规范则条例标准]', l)
                and not any(k in l for k in non_law_kw)]
    if bad_laws:
        issues.append(f'⚠ 法规名疑似不完整（缺"法/规定/办法/规范/则/条例"）：{bad_laws[:5]}')

    # GB标准号格式
    bad_gb = re.findall(r'GB[\s/]?(\d+)', text)
    # 这里不报错，只是列出

    # 常见笔误
    typos = {
        '住房城乡建设部': '住房和城乡建设部',
        '住建部': '住房和城乡建设部（首次出现）',
        '建设部令第': '住房和城乡建设部令第',
    }
    for typo, correct in typos.items():
        if typo in text and correct.split('（')[0] not in text:
            issues.append(f'⚠ 疑似笔误："{typo}" → "{correct}"')

    return '\n  '.join(issues) if issues else '✓ 法规名称规范'


def check_4party_signature(text):
    """核验四方签字约定"""
    issues = []
    # 必须包含"四方"
    if '四方签章' not in text and '四方签字' not in text:
        issues.append('❌ 未提及"四方签章/四方签字"')
    # 4方必须齐全
    required = ['施工', '设计', '监理', '建设']
    for r in required:
        if r not in text:
            issues.append(f'❌ 四方签字缺少{r}')
    if not issues:
        return '✓ 四方签字约定齐全（施工+设计+监理+建设）'
    return '\n  '.join(issues)


def check_ai_smell(text):
    """AI味扫描"""
    bad_words = ['赋能', '抓手', '闭环', '链路', '颗粒度', '底层逻辑', '拉通', '沉淀', '对标对表']
    found = [w for w in bad_words if w in text]
    if found:
        return f'❌ AI味词汇：{found}'
    return '✓ 无AI味词汇'


def check_required_sections(text):
    """核验必含章节"""
    required = ['结算基准', '工程量核定', '四方签章', '材料调差', '报送']
    missing = [r for r in required if r not in text]
    if missing:
        return f'⚠ 缺失关键章节：{missing}'
    return '✓ 关键章节齐全'


def main():
    parser = argparse.ArgumentParser(description='SOP质量门禁')
    parser.add_argument('--file', required=True, help='SOP文件路径（.docx/.md/.txt）')
    args = parser.parse_args()

    text = read_text(args.file)
    if not text:
        print(f'✗ 无法读取文件或文件为空：{args.file}')
        return

    print(f'文件：{args.file}')
    print(f'字符数：{len(text)}')
    print('=' * 60)
    print('【1. 条款编号连续性】')
    print(f'  {check_clause_numbering(text)}')
    print('\n【2. 法规/标准名称规范】')
    print(f'  {check_law_names(text)}')
    print('\n【3. 四方签字约定】')
    print(f'  {check_4party_signature(text)}')
    print('\n【4. 关键章节完整性】')
    print(f'  {check_required_sections(text)}')
    print('\n【5. AI味扫描】')
    print(f'  {check_ai_smell(text)}')
    print('=' * 60)


if __name__ == '__main__':
    main()
