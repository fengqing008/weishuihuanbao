#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""常用法律跨法检索器（15 部法律全文本地库）

用法示例：
  python3 law_search.py --list
  python3 law_search.py --law 刑法 --no 338
  python3 law_search.py --law 刑法 --kw 污染环境
  python3 law_search.py --law 民法典 --range 577-580
  python3 law_search.py --all --kw 串通投标
  python3 law_search.py --struct 刑法
  python3 law_search.py --all --kw 竣工验收 --json
数据源：../assets/laws/laws_index.json
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(os.path.dirname(HERE), 'assets', 'laws', 'laws_index.json')
DATA = os.environ.get('LAW_INDEX', DEFAULT_DATA)


def load(path):
    if not os.path.exists(path):
        sys.stderr.write(f'[ERROR] 法律库文件不存在：{path}\n')
        sys.exit(2)
    with open(path, encoding='utf-8') as f:
        return json.load(f)['laws']


def score(text, q):
    if not q:
        return 0.0
    if q in text:
        return 1.0
    grams = [q[i:i + 2] for i in range(len(q) - 1)]
    if not grams:
        return 0.0
    return sum(1 for g in grams if g in text) / len(grams)


def resolve(laws, key):
    if not key:
        return list(laws.keys())
    if key in laws:
        return [key]
    hits = [k for k, v in laws.items() if key in v['short'] or key in v['name'] or key == v['law_id']]
    return hits


def main():
    ap = argparse.ArgumentParser(description='常用法律跨法检索器（15 部法律全文）')
    ap.add_argument('--list', action='store_true', help='列出库内全部法律')
    ap.add_argument('--law', help='限定法律，如 刑法 / 民法典 / criminal_law')
    ap.add_argument('--all', action='store_true', help='跨全部法律检索')
    ap.add_argument('--no', type=int, help='按条号检索')
    ap.add_argument('--range', help='按条号区间检索，如 338-346')
    ap.add_argument('--kw', help='按关键词检索条文')
    ap.add_argument('--fuzzy', action='store_true', help='关键词模糊匹配（2-gram 覆盖率）')
    ap.add_argument('--struct', help='输出指定法律的结构（编/章/节）')
    ap.add_argument('--limit', type=int, default=20, help='每部法最多返回条数（默认20）')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--data')
    args = ap.parse_args()

    laws = load(args.data or DATA)

    if args.list:
        if args.json:
            print(json.dumps([{k: {kk: vv for kk, vv in v.items() if kk not in ('articles', 'sections')}}
                              for k, v in laws.items()], ensure_ascii=False, indent=1))
        else:
            print(f"{'law_id':22s}{'名称':34s}{'条数':>5s}  版本")
            for k, v in laws.items():
                print(f"{k:22s}{v['name']:34s}{v['count']:5d}  {v['version']}")
        return

    if args.struct:
        for lid in resolve(laws, args.struct):
            v = laws[lid]
            print(f"# {v['name']}（{v['count']} 条，{v['version']}）\n")
            for s in v['sections']:
                print('  ' + s)
        return

    targets = list(laws.keys()) if args.all else resolve(laws, args.law)
    if not targets:
        sys.stderr.write(f'[ERROR] 未匹配到法律：{args.law}\n'); sys.exit(2)

    out = {}
    for lid in targets:
        v = laws[lid]
        arts = v['articles']
        if args.no:
            arts = [a for a in arts if a['no'] == args.no]
        if args.range:
            a, b = re.split(r'[-~—]', args.range)
            arts = [x for x in arts if int(a) <= x['no'] <= int(b)]
        if args.kw:
            if args.fuzzy:
                sc = [(score(x['text'], args.kw), x) for x in arts]
                arts = [x for s, x in sorted(sc, key=lambda t: -t[0]) if s >= 0.6]
            else:
                arts = [x for x in arts if args.kw in x['text']]
        if arts:
            out[lid] = {'name': v['name'], 'version': v['version'], 'total': len(arts), 'items': arts[:args.limit]}

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    if not out:
        print('# 未命中')
        return
    for lid, v in out.items():
        print(f"## {v['name']}（命中 {v['total']} 条，展示 {len(v['items'])} 条）\n")
        for a in v['items']:
            loc = f"　[{a['path']}]" if a.get('path') else ''
            print(f"**{a['label']}**{loc}\n{a['text']}\n")


if __name__ == '__main__':
    main()
