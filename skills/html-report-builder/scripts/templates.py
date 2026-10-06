#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""templates.py —— 81 套模板参考库检索工具（v7.1.0 · 目录/zip 双模式）

来源：nexu-io/html-anything（Apache-2.0）。
模板库优先读 templates/ 目录；目录不存在时回退读取 templates.zip
（SkillHub 付费技能包单包文件数上限 200，模板库以 zip 形式随包分发，内容无损）。

用法：
  python3 templates.py list                   全部模板
  python3 templates.py list --cat slides      按分类
  python3 templates.py search 仪表盘           关键词检索（支持中文分类别名）
  python3 templates.py show data-report       读某套的设计指令与示例路径
  python3 templates.py cats                   分类统计
  python3 templates.py source                 当前数据来源（目录 / zip）
"""
import argparse
import io
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(HERE)
TPL_DIR = os.path.join(_ROOT, 'templates')
TPL_ZIP = os.path.join(_ROOT, 'templates.zip')

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


def _source():
    if os.path.isdir(TPL_DIR):
        return '目录 templates/'
    if os.path.isfile(TPL_ZIP):
        return '压缩包 templates.zip'
    return '缺失'


def _names():
    """模板目录名列表。"""
    if os.path.isdir(TPL_DIR):
        return sorted(n for n in os.listdir(TPL_DIR)
                      if os.path.isdir(os.path.join(TPL_DIR, n)))
    if os.path.isfile(TPL_ZIP):
        out = set()
        with zipfile.ZipFile(TPL_ZIP) as z:
            for n in z.namelist():
                parts = n.split('/')
                if len(parts) >= 2 and parts[0]:
                    out.add(parts[0])
        return sorted(out)
    return []


def _read(rel):
    """读模板内文件；rel 形如 'data-report/SKILL.md'。"""
    p = os.path.join(TPL_DIR, rel)
    if os.path.isfile(p):
        return io.open(p, encoding='utf-8').read()
    if os.path.isfile(TPL_ZIP):
        with zipfile.ZipFile(TPL_ZIP) as z:
            try:
                return z.read(rel).decode('utf-8')
            except KeyError:
                return None
    return None


def _exists(rel):
    if os.path.isfile(os.path.join(TPL_DIR, rel)):
        return True
    if os.path.isfile(TPL_ZIP):
        with zipfile.ZipFile(TPL_ZIP) as z:
            return rel in z.namelist()
    return False


def _meta(name):
    t = _read(name + '/SKILL.md')
    if t is None:
        return None

    def g(k):
        m = re.search(r'^' + k + r':\s*(.+)$', t, re.M)
        return m.group(1).strip().strip('"').strip("'") if m else ''

    ex_rel = name + '/example.html'
    if _exists(ex_rel):
        ex = (os.path.join(TPL_DIR, ex_rel) if os.path.isdir(TPL_DIR)
              else 'templates.zip::' + ex_rel)
    else:
        ex = ''
    return {
        'name': name,
        'zh': g('zh_name'),
        'desc': g('description'),
        'cat': g('category'),
        'aspect': g('aspect_hint'),
        'feat': int(g('featured') or 0),
        'example': ex,
        'path': (os.path.join(TPL_DIR, name, 'SKILL.md') if os.path.isdir(TPL_DIR)
                 else 'templates.zip::' + name + '/SKILL.md'),
    }


def _all():
    return [m for m in (_meta(n) for n in _names()) if m]


def cmd_list(a):
    items = _all()
    if a.cat:
        items = [x for x in items if x['cat'] == a.cat]
    print('共 %d 套模板（来源：%s）：' % (len(items), _source()))
    for x in sorted(items, key=lambda z: (z['cat'], -z['feat'])):
        print('  %-28s [%-10s] %-16s %s' % (x['name'], x['cat'], x['zh'], x['desc']))
    return 0


def cmd_cats(a):
    items = _all()
    d = {}
    for x in items:
        d.setdefault(x['cat'], 0)
        d[x['cat']] += 1
    print('共 %d 套 / %d 类（来源：%s）：' % (len(items), len(d), _source()))
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
    print('命中 %d 套（来源：%s）：' % (len(hits), _source()))
    for x in hits:
        print('  %-28s [%-10s] %-16s %s' % (x['name'], x['cat'], x['zh'], x['desc']))
    return 0


def cmd_show(a):
    m = _meta(a.name)
    if not m:
        print('未找到模板：%s（来源：%s）' % (a.name, _source()))
        return 1
    print('=' * 64)
    print('模板 %s ｜ %s ｜ 分类 %s ｜ 画幅 %s' % (m['name'], m['zh'], m['cat'], m['aspect']))
    print('设计指令：%s' % m['path'])
    print('参考实现：%s' % (m['example'] or '（无 example.html）'))
    print('=' * 64)
    print(_read(a.name + '/SKILL.md'))
    return 0


def cmd_source(a):
    print('模板库来源：%s' % _source())
    print('模板套数：%d' % len(_all()))
    return 0


def main():
    ap = argparse.ArgumentParser(description='81 套模板参考库检索（目录/zip 双模式）')
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

    p5 = sub.add_parser('source')
    p5.set_defaults(fn=cmd_source)

    a = ap.parse_args()
    if not getattr(a, 'fn', None):
        ap.print_help()
        return 0
    return a.fn(a)


if __name__ == '__main__':
    raise SystemExit(main())
