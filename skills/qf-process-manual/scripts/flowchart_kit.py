# -*- coding: utf-8 -*-
"""
流程图绘制公共库 —— 模板风格
UML 活动图符号 · 低饱和商务配色 · 真粗体（NotoSansCJK-Bold）· 零字符符号
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, Polygon, Circle

# ---- 字体（Regular + Bold 双字体，避免合成假粗体） ----
FONT_R = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONT_B = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
for _f in (FONT_R, FONT_B):
    try:
        fm.fontManager.addfont(_f)
    except Exception:
        pass
FP = fm.FontProperties(fname=FONT_R)
try:
    FPB = fm.FontProperties(fname=FONT_B)
except Exception:
    FPB = FP

# ---- 配色（低饱和商务） ----
EDGE = '#5a6c7d'
DEC_F, DEC_E = '#fff3cd', '#d99b1a'
NOTE_F, NOTE_E = '#f7f8e6', '#a9ab63'
RES_F, RES_E = '#e6f2e2', '#6da33f'
WARN_F, WARN_E = '#fbeee0', '#c0773f'
BAD_F, BAD_E = '#fbe0e0', '#c0392b'
ACT_E = '#2f7f96'
TXT = '#1b1b1b'
LW = 1.3

AX = None


def init(figsize=(16.2, 15.8), xlim=(0, 22), ylim=(2.0, 25.8), dpi=170):
    global AX
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    AX = ax
    return fig, ax


def rbox(cx, cy, w, h, text, fc='#ffffff', ec=EDGE, fs=12, lw=LW, rs=0.22, tc=TXT, bold=False):
    AX.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                 boxstyle="round,pad=0,rounding_size=%.3f" % rs,
                 fc=fc, ec=ec, lw=lw, zorder=3))
    AX.text(cx, cy, text, ha='center', va='center',
            fontproperties=(FPB if bold else FP),
            fontsize=fs, color=tc, zorder=4, linespacing=1.55)


def diamond(cx, cy, w, h, text, fc=DEC_F, ec=DEC_E, fs=11.5, lw=LW):
    AX.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
                 closed=True, fc=fc, ec=ec, lw=lw, zorder=3))
    AX.text(cx, cy, text, ha='center', va='center', fontproperties=FP,
            fontsize=fs, color=TXT, zorder=4, linespacing=1.5)


def note(cx, cy, w, h, text, fold=0.4, fc=NOTE_F, ec=NOTE_E, fs=11.5, lw=LW):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    AX.add_patch(Polygon([(x0, y0), (x1, y0), (x1, y1 - fold), (x1 - fold, y1), (x0, y1)],
                 closed=True, fc=fc, ec=ec, lw=lw, zorder=3))
    AX.plot([x1 - fold, x1 - fold, x1], [y1, y1 - fold, y1 - fold],
            color=ec, lw=lw * 0.85, zorder=4)
    AX.text(cx, cy, text, ha='center', va='center', fontproperties=FP,
            fontsize=fs, color=TXT, zorder=4, linespacing=1.7)


def arrow(p1, p2, color=EDGE, lw=LW, ms=13):
    AX.annotate('', xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                shrinkA=0, shrinkB=0, mutation_scale=ms), zorder=2)


def path(pts, color=EDGE, lw=LW):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    if len(pts) > 2:
        AX.plot(xs[:-1], ys[:-1], color=color, lw=lw, solid_capstyle='round', zorder=1)
    arrow(pts[-2], pts[-1], color, lw)


def label(x, y, t, fs=10.5, color='#5f6d79', bg=False):
    AX.text(x, y, t, ha='center', va='center', fontproperties=FP, fontsize=fs, color=color,
            zorder=6, bbox=(dict(fc='white', ec='none', pad=1.0) if bg else None))


def start_node(cx, cy, r=0.3):
    AX.add_patch(Circle((cx, cy), r, fc='#1b1b1b', ec='#1b1b1b', zorder=3))


def end_node(cx, cy, r=0.3):
    AX.add_patch(Circle((cx, cy), r, fc='white', ec='#1b1b1b', lw=1.5, zorder=3))
    AX.add_patch(Circle((cx, cy), r * 0.4, fc='#1b1b1b', ec='none', zorder=4))


def title_block(title, subtitle, y_title=25.05, y_sub=24.35, y_line=23.85,
                xspan=(3.0, 19.0), fs_title=24, fs_sub=13.5):
    cx = (xspan[0] + xspan[1]) / 2
    AX.text(cx, y_title, title, ha='center', va='center', fontproperties=FPB,
            fontsize=fs_title, color='#22303d', zorder=5)
    AX.text(cx, y_sub, subtitle, ha='center', va='center', fontproperties=FP,
            fontsize=fs_sub, color='#5a6c7d')
    AX.plot(list(xspan), [y_line, y_line], color=EDGE, lw=1.1, zorder=1)


def save(png):
    AX.figure.savefig(png, bbox_inches='tight', facecolor='white')


def line(pts, color=EDGE, lw=LW, ls='-'):
    """无箭头折线（用于汇聚总线等）"""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    AX.plot(xs, ys, color=color, lw=lw, solid_capstyle='round', zorder=1, linestyle=ls)


def poly(points, fc, ec, lw=LW):
    """多边形（图例菱形/折角等）"""
    AX.add_patch(Polygon(points, closed=True, fc=fc, ec=ec, lw=lw, zorder=3))


def rrect(x0, y0, w, h, fc, ec, lw=LW, rs=0.1):
    """圆角矩形（图例用，左下角定位）"""
    AX.add_patch(FancyBboxPatch((x0, y0), w, h,
                 boxstyle="round,pad=0,rounding_size=%.3f" % rs,
                 fc=fc, ec=ec, lw=lw, zorder=3))


def dot(cx, cy, r=0.07, fc=EDGE):
    AX.add_patch(Circle((cx, cy), r, fc=fc, ec=fc, zorder=3))
