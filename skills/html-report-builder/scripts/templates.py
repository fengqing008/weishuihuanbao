#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""templates.py —— 81 套模板参考库检索工具（v7.0.0）

来源：nexu-io/html-anything（Apache-2.0），全量嵌入 templates/。
模板库为可选参考，不替换本技能既有渲染路径。

用法：
  python3 templates.py list                   全部模板
  python3 templates.py list --cat slides      按分类
  python3 templates.py search 仪表盘           关键词检索（支持中文分类别名）
  python3 templates.py show data-report       读某套的设计指令与示例路径
  python3 templates.py cats                   分类统计
"""
import argparse
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(os.path.dirname(HERE), 'templates')

ALIAS = {
    '幻灯片': 'slides', '演示': 'slides', 'PPT': 'slides', 'ppt': 'slides',
    '文档': 'doc', '报告': 'doc', '简报': 'doc',
    '仪表盘': 'dashboard', '看板': 'dashboard', '数据看板': 'dashboard',
    '海报': 'poster', '卡片': 'card', '图文': 'card',
    '原型': 'prototype', '落地页': 'prototype', '网页': 'prototype',
    '视频': 'video', '动效': 'video',
    '文章': 'article', '长文': 'article', '博客': 'article',
    '数据': 'data', '移动': 'mobile', '财务': 'finance',
    '邮件': 'email', '简历': 'resume',
}


def _meta(name):
    p = os.path.join(TPL, name, 'SKILL.md')
    if not os.path.exists(p):
        return None
    t = io.open(p, encoding='utf-8').read()

    def g(k):
        m = re.search(r'^' + k + r':\s*(.+)$', t, re.M)
        return m.group(1).strip().strip('"').strip("'") if m else ''

    ex = os.path.join(TPL, name, 'example.html')
    return {
        'name': name,
        'zh': g('zh_name'),
        'desc': g('description'),
        'cat': g('category'),
        'aspect': g('aspect_hint'),
        'feat': int(g('featured') or 0),
        'example': ex if os.path.exists(ex) else '',
        'path': p,
    }


def _all():
    if not os.path.isdir(TPL):
        return []
    out = []
    for n in sorted(os.listdir(TPL)):
        m = _meta(n)
        if m:
            out.append(m)
    return out


def cmd_list(a):
    items = _all()
    if a.cat:
        items = [x for x in items if x['cat'] == a.cat]
    print('共 %d 套模板：' % len(items))
    for x in sorted(items, key=lambda z: (z['cat'], -z['feat'])):
        print('  %-28s [%-10s] %-16s %s' % (x['name'], x['cat'], x['zh'], x['desc']))
    return 0


def cmd_cats(a):
    items = _all()
    d = {}
    for x in items:
        d.setdefault(x['cat'], 0)
        d[x['cat']] += 1
    print('共 %d 套 / %d 类：' % (len(items), len(d)))
    for k in sorted(d):
        print('  %-12s %d' % (k, d[k]))
    return 0


def cmd_search(a):
    kw = a.keyword.lower()
    cat = ALIAS.get(a.keyword, '')
    hits = []
    for x in _all():
        text = (x['name'] + x['zh'] + x['desc'] + x['cat']).lower()
        if kw in text or (cat and x['cat'] == cat):
            hits.append(x)
    print('命中 %d 套：' % len(hits))
    for x in hits:
        print('  %-28s [%-10s] %-16s %s' % (x['name'], x['cat'], x['zh'], x['desc']))
    return 0


def cmd_show(a):
    m = _meta(a.name)
    if not m:
        print('未找到模板：%s' % a.name)
        return 1
    print('=' * 64)
    print('模板 %s ｜ %s ｜ 分类 %s ｜ 画幅 %s' % (m['name'], m['zh'], m['cat'], m['aspect']))
    print('设计指令：%s' % m['path'])
    print('参考实现：%s' % (m['example'] or '（无 example.html）'))
    print('=' * 64)
    print(io.open(m['path'], encoding='utf-8').read())
    return 0


def main():
    ap = argparse.ArgumentParser(description='81 套模板参考库检索')
    sub = ap.add_subparsers(dest='cmd')

    p1 = sub.add_parser('list')
    p1.add_argument('--cat', default='')
    p1.set_defaults(fn=cmd_list)

    p2 = sub.add_parser('cats')
    p2.set_defaults(fn=cmd_cats)

    p3 = sub.add_parser('search')
    p3.add_argument('keyword')
    p3.set_defaults(fn=cmd_search)

    p4 = sub.add_parser('show')
    p4.add_argument('name')
    p4.set_defaults(fn=cmd_show)

    a = ap.parse_args()
    if not getattr(a, 'fn', None):
        ap.print_help()
        return 0
    return a.fn(a)


if __name__ == '__main__':
    raise SystemExit(main())
