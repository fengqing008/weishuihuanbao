#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""民法典 条文检索工具（离线，纯标准库）。

用法：
  python3 scripts/mfd.py article 188               # 民法典单条
  python3 scripts/mfd.py article 143-157           # 民法典条号区间
  python3 scripts/mfd.py search 定金                # 民法典关键词检索
  python3 scripts/mfd.py chapter 借款              # 民法典按章定位
  python3 scripts/mfd.py structure                 # 民法典编章索引
  python3 scripts/mfd.py stat                      # 民法典统计

说明：生态环境法典及其配套生态环境法律条文的检索，已迁至
「生态环境法律工具箱」(qf-eco-code) 技能，本技能专注民法典与常用法律。
常用法律（刑法/民诉法等 15 部）检索见同目录 scripts/law_search.py。
"""
import os
import re
import json
import argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(BASE, 'references')

CIVIL_FILES = ['01-总则编', '02-物权编', '03-合同编', '04-人格权编',
               '05-婚姻家庭编', '06-继承编', '07-侵权责任编', '08-附则']
LAW = {
    'civil': {'name': '民法典', 'files': CIVIL_FILES,
              'index': '09-编章体系与条号索引.md',
              'bounds': [('总则', 1, 204), ('物权', 205, 462), ('合同', 463, 988),
                         ('人格权', 989, 1039), ('婚姻家庭', 1040, 1118),
                         ('继承', 1119, 1163), ('侵权责任', 1164, 1258), ('附则', 1259, 1260)]},
}


def load_articles(law):
    arts = {}
    for f in LAW[law]['files']:
        p = os.path.join(REF, f + '.md')
        if not os.path.exists(p):
            continue
        t = open(p, encoding='utf-8').read()
        parts = re.split(r'^## 第(\d+)条\n', t, flags=re.M)
        for i in range(1, len(parts), 2):
            arts[int(parts[i])] = parts[i + 1].strip()
    return arts


def flat(s):
    return re.sub(r'\s+', ' ', s).strip()


def cmd_article(a):
    arts = load_articles(a.law)
    rng = a.range.strip()
    nums = list(range(int(rng.split('-')[0]), int(rng.split('-')[1]) + 1)) if '-' in rng else [int(rng)]
    for n in nums:
        if n in arts:
            print(arts[n]); print()
        else:
            print('%s第%d条：未找到（本库共 %d 条）' % (LAW[a.law]['name'], n, len(arts)))


def cmd_search(a):
    arts = load_articles(a.law)
    kw = a.keyword
    hits = [(n, arts[n].count(kw), arts[n]) for n in sorted(arts) if kw in arts[n]]
    if a.json:
        print(json.dumps([{'article': n, 'hits': c, 'text': flat(t)} for n, c, t in hits],
                         ensure_ascii=False, indent=1))
        return
    print('%s：关键词「%s」命中 %d 条' % (LAW[a.law]['name'], kw, len(hits)))
    for n, c, t in hits:
        s = flat(t)
        i = s.find(kw)
        seg = s[max(0, i - 28):i + len(kw) + 40]
        print('  第%d条 ×%d：…%s…' % (n, c, seg))


def cmd_chapter(a):
    p = os.path.join(REF, LAW[a.law]['index'])
    hit = False
    for ln in open(p, encoding='utf-8'):
        if a.name in ln and '—' in ln and '第' in ln:
            print(ln.replace('    ', '  ').rstrip())
            hit = True
    if not hit:
        print('未在索引中定位到「%s」，可用 `structure` 查看完整索引。' % a.name)


def cmd_structure(a):
    print(open(os.path.join(REF, LAW[a.law]['index']), encoding='utf-8').read())


def cmd_stat(a):
    arts = load_articles(a.law)
    print('法源：%s' % LAW[a.law]['name'])
    print('条文总数：%d 条' % len(arts))
    print('条号范围：第%d条 — 第%d条' % (min(arts), max(arts)))
    print('编别分布：')
    for name, x, y in LAW[a.law]['bounds']:
        cnt = sum(1 for n in arts if x <= n <= y)
        print('  %-8s 第%d—%d条  共%d条' % (name, x, y, cnt))


def main():
    ap = argparse.ArgumentParser(description='民法典 条文检索（离线）')
    sub = ap.add_subparsers(dest='cmd')
    for p in (sub.add_parser('article', help='按条号查条文，支持区间'),
              sub.add_parser('search', help='全库关键词检索'),
              sub.add_parser('chapter', help='按章/节名称定位条号范围'),
              sub.add_parser('structure', help='打印编章条号索引'),
              sub.add_parser('stat', help='统计信息')):
        p.add_argument('--law', choices=['civil'], default='civil',
                       help='法源：civil=民法典（默认）')
    for p in sub.choices.values():
        if p.prog.endswith('article'):
            p.add_argument('range', help='条号或条号区间')
        elif p.prog.endswith('search'):
            p.add_argument('keyword', help='关键词')
            p.add_argument('--json', action='store_true', help='输出 JSON')
        elif p.prog.endswith('chapter'):
            p.add_argument('name', help='章或节名称关键词')
    args = ap.parse_args()
    {'article': cmd_article, 'search': cmd_search, 'chapter': cmd_chapter,
     'structure': cmd_structure, 'stat': cmd_stat}.get(args.cmd, lambda x: ap.print_help())(args)


if __name__ == '__main__':
    main()
