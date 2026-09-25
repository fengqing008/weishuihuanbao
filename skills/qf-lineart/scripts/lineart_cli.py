#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qf-lineart · 手绘线稿插图引擎（命令行入口）

用法示例
--------
  # 看清单
  python lineart_cli.py --list-motifs
  python lineart_cli.py --list-styles
  python lineart_cli.py --list-palettes

  # 单张（暖褐墨 + 钢笔）
  python lineart_cli.py --motif lamp --palette sepia --style fountain -o lamp.png

  # 一次比较 5 种笔触
  python lineart_cli.py --motif cloud --compare-styles -o sheet.png

  # 母题总览图（16 母题拼版，暖色）
  python lineart_cli.py --sheet sheet.png --palette ochre

  # 按文章批量配图（关键词选题 + 落位规划）
  python lineart_cli.py --manifest book.json --per-article 3 \
      --outdir images/auto --palette sepia -o auto_images.json
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import lineart_engine as E


_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
]


def _load_font(size=20):
    from PIL import ImageFont
    for p in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _label(img, text, color=(120, 90, 60), font=None):
    """角标：优先中文字体，缺失则退化为 ASCII"""
    d = ImageDraw.Draw(img, "RGBA")
    f = font or _load_font()
    try:
        d.text((14, 12), text, fill=(*color, 235), font=f)
    except Exception:
        d.text((14, 12), text.encode("ascii", "ignore").decode(), fill=(*color, 235))
    return img


def _sheet(names, palette, style, size, cols, out, label=True, shade=True):
    W, H = size
    rows = (len(names) + cols - 1) // cols
    pad = 18
    canvas = Image.new("RGBA", (cols * W + (cols + 1) * pad, rows * H + (rows + 1) * pad),
                       (*E.PALETTES[palette]["paper"], 255))
    for i, m in enumerate(names):
        r, c = divmod(i, cols)
        im = E.render(m, size=(W, H), style=style, palette=palette, seed=1000 + i, paper=True, shade=shade)
        if label:
            _label(im, f"{m} / {E.MOTIF_META[m]['cn']}")
        canvas.alpha_composite(im, (pad + c * (W + pad), pad + r * (H + pad)))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out, quality=95)
    return out


def main():
    ap = argparse.ArgumentParser(description="qf-lineart · 手绘线稿插图引擎")
    ap.add_argument("--list-motifs", action="store_true")
    ap.add_argument("--list-styles", action="store_true")
    ap.add_argument("--list-palettes", action="store_true")

    ap.add_argument("--motif", help="单张母题名")
    ap.add_argument("--style", default="fountain", help="笔触：fountain/pencil/brush/marker/charcoal")
    ap.add_argument("--palette", default="sepia", help="配色：sepia/ochre/amber/terracotta/rosewood/olive/ink")
    ap.add_argument("--size", default="1500x820", help="尺寸 WxH（跨栏 1500x820 / 栏内 760x980）")
    ap.add_argument("--roughness", type=float, default=1.0, help="粗糙度 0–3")
    ap.add_argument("--bowing", type=float, default=1.0, help="弯曲度 0–3")
    ap.add_argument("--grain", type=float, default=None, help="颗粒强度 0–0.5（默认按笔触）")
    ap.add_argument("--transparent", action="store_true", help="输出透明底（默认铺暖纸实底；透明底在深色界面会呈黑底，不推荐）")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--no-shade", action="store_true", help="关闭体量排线（v2.4.0，默认开启）")

    ap.add_argument("--compare-styles", action="store_true", help="一次输出 5 种笔触对比图")
    ap.add_argument("--sheet", metavar="OUT", help="母题总览拼版输出路径")
    ap.add_argument("--cols", type=int, default=4)

    ap.add_argument("--manifest", help="稿件清单 JSON（批量配图）")
    ap.add_argument("--per-article", type=int, default=3, help="每篇配图数 2–3")
    ap.add_argument("--outdir", default="images/auto", help="批量输出目录（相对清单所在目录）")
    ap.add_argument("-o", "--out", help="输出路径（单张）/ 配图清单输出（批量）")

    a = ap.parse_args()

    if a.list_motifs:
        for i, m in enumerate(E.MOTIFS):
            print(f"{m:10s} {E.MOTIF_META[m]['cn']:6s} {E.MOTIF_META[m]['desc']}")
        return 0
    if a.list_styles:
        for k, v in E.STROKE_PROFILES.items():
            print(f"{k:10s} {v['cn']:4s} 复笔{v['passes']}遍 抖动×{v['jitter_k']} 线宽×{v['width_k']} 颗粒{v['grain']}")
        return 0
    if a.list_palettes:
        for k, v in E.PALETTES.items():
            print(f"{k:12s} {v['cn']:6s} ink={v['ink']} accent={v['accent']} paper={v['paper']}")
        return 0

    if a.compare_styles:
        out = a.out or "style_compare.png"
        names = list(E.STROKE_PROFILES)
        w, h = 760, 420
        pad = 16
        canvas = Image.new("RGB", (w * len(names) + pad * (len(names) + 1), h + pad * 2),
                           E.PALETTES[a.palette]["paper"])
        for i, st in enumerate(names):
            im = E.render(a.motif or "cloud", size=(w, h), style=st, palette=a.palette, seed=a.seed, paper=True, shade=not a.no_shade)
            _label(im, f"{st} / {E.STROKE_PROFILES[st]['cn']}")
            canvas.paste(im.convert("RGB"), (pad + i * (w + pad), pad))
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out)
        print(f"OK {out}  5 笔触对比")
        return 0

    if a.sheet:
        _sheet(E.MOTIFS, a.palette, a.style, (560, 320), a.cols, a.sheet, shade=not a.no_shade)
        print(f"OK {a.sheet}  {len(E.MOTIFS)} 母题总览（{a.palette}/{a.style}）")
        return 0

    if a.motif:
        W, H = (int(x) for x in a.size.lower().split("x"))
        out = a.out or f"{a.motif}.png"
        E.render(a.motif, out=out, size=(W, H), style=a.style, palette=a.palette,
                 seed=a.seed, roughness=a.roughness, bowing=a.bowing, grain=a.grain,
                 paper=not a.transparent, shade=not a.no_shade)
        print(f"OK {out}  motif={a.motif} style={a.style} palette={a.palette}")
        return 0

    if not a.manifest:
        ap.error("需 --motif / --sheet / --compare-styles / --manifest 之一")

    mp = Path(a.manifest).resolve()
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    outdir = mp.parent / a.outdir
    n_per = max(1, min(3, a.per_article))
    mapping = {}
    for idx, art in enumerate(manifest.get("articles", [])):
        bp = (mp.parent / art["body"]).resolve()
        text = art.get("title", "") + (bp.read_text(encoding="utf-8") if bp.exists() else "")
        motifs = E.pick_motifs(text, n_per, seed=a.seed + idx)
        roles = E.plan_roles(n_per)
        items = []
        for mi, (motif, role) in enumerate(zip(motifs, roles)):
            fn = outdir / f"art{art.get('order')}_{mi+1}_{motif}.png"
            E.render(motif, out=str(fn), size=E.size_for_role(role), style=a.style,
                     palette=a.palette, seed=a.seed + idx * 10 + mi, shade=not a.no_shade)
            items.append({"file": str(fn), "motif": motif, "role": role})
        mapping[str(art.get("order"))] = items
        print(f"art{art.get('order')} [{art.get('column')}] {art.get('title')} -> {[i['motif'] for i in items]}")
    if a.out:
        Path(a.out).write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"OK 配图清单 -> {a.out}  共 {sum(len(v) for v in mapping.values())} 张")
    return 0


if __name__ == "__main__":
    sys.exit(main())
