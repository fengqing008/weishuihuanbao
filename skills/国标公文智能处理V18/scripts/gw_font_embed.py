#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gw_font_embed.py —— GB/T 9704 公函字体嵌入模块（v1.0）

把 TrueType 字体作为 OLE 字体真正嵌入 .docx，使接收方未安装字体也能正确显示。
修复既有 V16/V18 实现的缺陷：仅写了字体文件与 document.xml.rels，
未在 fontTable.xml 声明 <w:embedRegular>、未在 settings.xml 置 embedTrueTypeFonts，
导致嵌入实际不生效。

正确需覆盖四处：
  1) [Content_Types].xml      → Default Extension="ttf"
  2) word/_rels/fontTable.xml.rels → Relationship(type=font, Target=fonts/xxx.ttf)
  3) word/fontTable.xml       → <w:font w:name="X"><w:embedRegular r:id=.. w:fontKey=../></w:font>
  4) word/settings.xml        → <w:embedTrueTypeFonts/><w:saveSubsetFonts/>

用法：
  python3 gw_font_embed.py <docx路径>                      # 默认嵌入 仿宋_GB2312 + 方正小标宋简体
  python3 gw_font_embed.py <docx> --font "黑体=/path/simhei.ttf"
  python3 gw_font_embed.py <docx> --fonts-dir /path/fonts  # 目录内 *.ttf 全部按文件名（去扩展名）作字体名嵌入
  python3 gw_font_embed.py <docx> --check                  # 只校验当前嵌入状态
"""
import os, re, sys, shutil, hashlib, zipfile, argparse

NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS_PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'

DEFAULT_FONTS_DIR = 'assets/fonts'
DEFAULT_FONT_NAMES = ['仿宋_GB2312', '方正小标宋简体']


def _font_key(name: str) -> str:
    """按字体名生成稳定伪 GUID 作 w:fontKey（Word 不强制校验其真实性）"""
    h = hashlib.md5(('gwfont:' + name).encode('utf-8')).hexdigest().upper()
    return '{' + f'{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}' + '}'


def _rel_id(name: str) -> str:
    return 'rIdGWF' + hashlib.md5(name.encode('utf-8')).hexdigest()[:6].upper()


def embed_fonts(docx_path: str, font_map: dict) -> bool:
    """font_map: {字体显示名: ttf绝对路径}。返回是否成功写入。"""
    font_map = {k: v for k, v in font_map.items() if v and os.path.isfile(v)}
    if not font_map or not os.path.isfile(docx_path):
        return False

    tmp = docx_path + '.gwtmp'
    with zipfile.ZipFile(docx_path, 'r') as zin:
        items = {i.filename: zin.read(i.filename) for i in zin.infolist()}

    # 1) [Content_Types].xml
    ct = items['[Content_Types].xml'].decode('utf-8')
    if 'Extension="ttf"' not in ct:
        ct = ct.replace('</Types>', '<Default Extension="ttf" ContentType="application/x-font-ttf"/></Types>')
    items['[Content_Types].xml'] = ct.encode('utf-8')

    # 2) word/_rels/fontTable.xml.rels （关系归属于 fontTable 部件）
    rels_name = 'word/_rels/fontTable.xml.rels'
    if rels_name in items:
        rels = items[rels_name].decode('utf-8')
    else:
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<Relationships xmlns="{NS_PKG}"></Relationships>')
    for name, path in font_map.items():
        tgt = f'fonts/{os.path.basename(path)}'
        rid = _rel_id(name)
        if f'Target="{tgt}"' not in rels:
            rels = rels.replace('</Relationships>',
                                f'<Relationship Id="{rid}" Type="{NS_R}/font" Target="{tgt}"/></Relationships>')
    items[rels_name] = rels.encode('utf-8')

    # 3) word/fontTable.xml
    ft_name = 'word/fontTable.xml'
    if ft_name in items:
        ft = items[ft_name].decode('utf-8')
    else:
        ft = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
              '</w:fonts>')
    for name, path in font_map.items():
        rid = _rel_id(name)
        embed = f'<w:embedRegular r:id="{rid}" w:fontKey="{_font_key(name)}"/>'
        pat = re.compile(r'(<w:font w:name="%s"[^>]*>)(.*?)(</w:font>)' % re.escape(name), re.S)
        m = pat.search(ft)
        if m:
            inner = re.sub(r'<w:embedRegular[^>]*/>', '', m.group(2))
            ft = pat.sub(lambda mm: mm.group(1) + inner + embed + mm.group(3), ft, count=1)
        else:
            node = (f'<w:font w:name="{name}"><w:family w:val="auto"/>'
                    f'<w:pitch w:val="variable"/>{embed}</w:font>')
            ft = ft.replace('</w:fonts>', node + '</w:fonts>')
    items[ft_name] = ft.encode('utf-8')

    # 4) word/settings.xml
    st_name = 'word/settings.xml'
    if st_name in items:
        st = items[st_name].decode('utf-8')
        add = ''
        if 'embedTrueTypeFonts' not in st:
            add += '<w:embedTrueTypeFonts/>'
        if 'saveSubsetFonts' not in st:
            add += '<w:saveSubsetFonts/>'
        if add:
            st = re.sub(r'(<w:settings[^>]*>)', lambda m: m.group(1) + add, st, count=1)
        items[st_name] = st.encode('utf-8')

    # 5) 重打包 + 写入字体
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for name, data in items.items():
            if name.startswith('word/fonts/'):
                continue  # 旧字体条目跳过，由下方统一写入，避免重复
            zout.writestr(name, data)
        for name, path in font_map.items():
            zout.write(path, f'word/fonts/{os.path.basename(path)}')
    shutil.move(tmp, docx_path)
    return True


def check_embed(docx_path: str) -> dict:
    """返回 {嵌入字体文件, fontTable声明, fontTable.rels关系, settings标记}"""
    with zipfile.ZipFile(docx_path) as z:
        names = z.namelist()
        files = [n for n in names if n.startswith('word/fonts/')]
        ft = z.read('word/fontTable.xml').decode('utf-8', 'ignore') if 'word/fontTable.xml' in names else ''
        declares = re.findall(r'<w:font w:name="([^"]+)"[^>]*>(?:(?!</w:font>).)*<w:embedRegular', ft, re.S)
        rels_name = 'word/_rels/fontTable.xml.rels'
        rels = z.read(rels_name).decode('utf-8', 'ignore') if rels_name in names else ''
        st = z.read('word/settings.xml').decode('utf-8', 'ignore') if 'word/settings.xml' in names else ''
        return {
            'font_files': files,
            'fontTable_declared': declares,
            'fontTable_rels': re.findall(r'Target="([^"]+)"', rels),
            'settings_embed': 'embedTrueTypeFonts' in st,
        }


def _resolve_fonts(args):
    fmap = {}
    if args.fonts_dir:
        for fn in os.listdir(args.fonts_dir):
            if fn.lower().endswith(('.ttf', '.otf')):
                fmap[os.path.splitext(fn)[0]] = os.path.join(args.fonts_dir, fn)
    for spec in (args.font or []):
        if '=' in spec:
            n, p = spec.split('=', 1)
            fmap[n.strip()] = p.strip()
    if not fmap:
        for n in DEFAULT_FONT_NAMES:
            p = os.path.join(DEFAULT_FONTS_DIR, n + '.ttf')
            if os.path.isfile(p):
                fmap[n] = p
    return fmap


def main():
    ap = argparse.ArgumentParser(description='GB/T 9704 公函字体嵌入模块')
    ap.add_argument('docx')
    ap.add_argument('--font', action='append', help='字体名=ttf路径，可多次')
    ap.add_argument('--fonts-dir', help='目录内 ttf 全部按文件名作字体名嵌入')
    ap.add_argument('--check', action='store_true', help='仅校验嵌入状态')
    args = ap.parse_args()

    if args.check:
        r = check_embed(args.docx)
        print('字体文件      :', r['font_files'])
        print('fontTable声明 :', r['fontTable_declared'])
        print('fontTable关系 :', r['fontTable_rels'])
        print('settings嵌入  :', r['settings_embed'])
        ok = bool(r['font_files']) and bool(r['fontTable_declared']) and r['settings_embed']
        print('结论          :', '嵌入生效 ✓' if ok else '嵌入不完整 ✗')
        sys.exit(0 if ok else 1)

    fmap = _resolve_fonts(args)
    if not fmap:
        print('未找到可用字体，请用 --font / --fonts-dir 指定', file=sys.stderr)
        sys.exit(2)
    ok = embed_fonts(args.docx, fmap)
    print('已嵌入:', ', '.join(f'{k}' for k in fmap) if ok else '失败')
    r = check_embed(args.docx)
    print('校验  :', r)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
