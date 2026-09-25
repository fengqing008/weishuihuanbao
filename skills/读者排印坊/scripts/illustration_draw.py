#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读者排印坊 · 手绘线稿配图（对接 qf-lineart 手绘线稿插图引擎）

引擎解析顺序：
  1) 本技能 scripts/ 下的 lineart_engine.py（随包副本，单技能可独立运行）
  2) 已安装的 qf-lineart 技能引擎（qf-lineart/scripts）
  3) 工作区软链副本（skills/qf-lineart/scripts）

版面口径：跨栏 wide 1500×820；栏内 inline / inline-end 760×980。
默认暖色配置：--palette sepia --style pencil（与《读者》淡黄内页同族）。

子命令：
  --list-motifs / --list-styles / --list-palettes
  --motif lamp --out a.png
  --manifest book.json --per-article 3 --outdir images/auto --out auto_images.json
"""
import argparse
import json
import sys
from pathlib import Path

# ---------------- 引擎解析 ----------------
_ENGINE_DIRS = [
    Path(__file__).resolve().parent,                        # 随包副本优先
    Path("qf-lineart/scripts"),
    Path("skills/qf-lineart/scripts"),
]


def load_engine():
    for p in _ENGINE_DIRS:
        if (p / "lineart_engine.py").exists():
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
            import lineart_engine
            return lineart_engine
    raise SystemExit("未找到 lineart_engine.py：请安装 qf-lineart 技能或把引擎副本放入本技能 scripts/")


E = load_engine()

# 版面尺寸口径（与《读者》版式一致）
SIZE_WIDE = (1500, 820)
SIZE_INLINE = (760, 980)


def size_for_role(role: str):
    return SIZE_WIDE if role == "wide" else SIZE_INLINE


def main() -> int:
    ap = argparse.ArgumentParser(description="读者排印坊·手绘线稿配图（qf-lineart 引擎）")
    ap.add_argument("--list-motifs", action="store_true")
    ap.add_argument("--list-styles", action="store_true")
    ap.add_argument("--list-palettes", action="store_true")

    ap.add_argument("--motif", help="单张绘制母题")
    ap.add_argument("--out", help="单张输出路径 / 批量清单输出")
    ap.add_argument("--manifest", help="稿件清单（批量配图）")
    ap.add_argument("--per-article", type=int, default=3, help="每篇配图数（2–3）")
    ap.add_argument("--outdir", default="images/auto", help="批量输出目录（相对清单所在目录）")
    ap.add_argument("--seed", type=int, default=2026)

    ap.add_argument("--style", default="pencil",
                    help="笔触：fountain/pencil/brush/marker/charcoal（默认 pencil）")
    ap.add_argument("--palette", default="sepia",
                    help="配色：sepia/ochre/amber/terracotta/rosewood/olive/ink（默认暖褐 sepia）")
    ap.add_argument("--size", default="1500x820", help="单张尺寸 WxH")
    ap.add_argument("--transparent", action="store_true", help="输出透明底（默认铺暖纸实底；透明底在深色界面会呈黑底，不推荐）")
    ap.add_argument("--roughness", type=float, default=1.0)
    a = ap.parse_args()

    if a.list_motifs:
        for m in E.MOTIFS:
            print(f"{m:10s} {E.MOTIF_META[m]['cn']:6s} {E.MOTIF_META[m]['desc']}")
        return 0
    if a.list_styles:
        for k, v in E.STROKE_PROFILES.items():
            print(f"{k:10s} {v['cn']:4s} 复笔{v['passes']}遍 抖动×{v['jitter_k']} 线宽×{v['width_k']} 颗粒{v['grain']}")
        return 0
    if a.list_palettes:
        for k, v in E.PALETTES.items():
            print(f"{k:12s} {v['cn']:6s} ink={v['ink']} paper={v['paper']}")
        return 0

    if a.motif:
        W, H = (int(x) for x in a.size.lower().split("x"))
        out = a.out or f"{a.motif}.png"
        E.render(a.motif, out=out, size=(W, H), style=a.style, palette=a.palette,
                 seed=a.seed, roughness=a.roughness, paper=not a.transparent)
        print(f"OK {out}  motif={a.motif} style={a.style} palette={a.palette}")
        return 0

    if not a.manifest:
        ap.error("需 --motif 或 --manifest")

    mp = Path(a.manifest).resolve()
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    # 清单级风格可覆盖命令行默认（保持全册一致）
    style = manifest.get("illustration", {}).get("style", a.style)
    palette = manifest.get("illustration", {}).get("palette", a.palette)
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
            E.render(motif, out=str(fn), size=size_for_role(role), style=style,
                     palette=palette, seed=a.seed + idx * 10 + mi)
            items.append({"file": str(fn), "motif": motif, "role": role})
        mapping[str(art.get("order"))] = items
        print(f"art{art.get('order')} [{art.get('column')}] {art.get('title')} -> {[i['motif'] for i in items]}")
    if a.out:
        Path(a.out).write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"OK 配图清单 -> {a.out}  共 {sum(len(v) for v in mapping.values())} 张（{palette}/{style}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
