#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""读取docx → Markdown（段落+表格），v18.3"""
import sys, os, re

def _is_table_caption(text):
    return text if re.match(r'^表\s*\d+', text) else None

def read_docx(path):
    from docx import Document
    from docx.oxml.ns import qn

    doc = Document(path)
    lines = []; last_para = None
    body = doc.element.body
    pt, tt = qn('w:p'), qn('w:tbl')

    for child in body:
        if child.tag == pt:
            text = ''.join(t.text or '' for t in child.iter(qn('w:t'))).strip()
            if text: last_para = text; lines.append(text)
            else: last_para = None
        elif child.tag == tt:
            rows = child.findall(qn('w:tr'))
            if not rows: continue
            all_rows = []
            for row in rows:
                cells = []
                for tc in row.findall(qn('w:tc')):
                    ct = ''
                    for p in tc.findall(qn('w:p')):
                        for t in p.iter(qn('w:t')):
                            if t.text: ct += t.text
                        ct += '\n'
                    cells.append(ct.strip().replace('\n',' / '))
                all_rows.append(cells)
            if not all_rows: continue
            ncols = max(len(r) for r in all_rows)
            for r in all_rows:
                while len(r) < ncols: r.append('')
            if lines and lines[-1] != '': lines.append('')
            header = all_rows[0]; data_rows = all_rows[1:] if len(all_rows)>1 else []
            lines.append('| '+' | '.join(header)+' |')
            lines.append('|'+'|'.join(['------']*ncols)+'|')
            for dr in data_rows: lines.append('| '+' | '.join(dr)+' |')
            lines.append(''); last_para = None
    return '\n'.join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python read_docx.py <文件路径>", file=sys.stderr); sys.exit(1)
    fp = sys.argv[1]
    if not os.path.isfile(fp):
        d, bn = os.path.dirname(fp) or ".", os.path.basename(fp)
        for f in os.listdir(d):
            if bn in f and f.endswith('.docx') and not f.startswith('~'):
                fp = os.path.join(d, f); break
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        print(read_docx(fp))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr); sys.exit(1)
