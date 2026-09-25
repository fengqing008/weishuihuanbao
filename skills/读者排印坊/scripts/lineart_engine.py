#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qf-lineart · 手绘线稿插图引擎（内核库 v2.0）

把 Rough.js 的参数化手绘算法（双描线 + 正态抖动 + 贝塞尔平滑 + bowing 弯曲）
与 SVG 手绘滤镜思路（噪声位移 + 复线叠加 + 晕染 + 纸纹颗粒）在 Python/PIL 上复现，
并内置暖色墨体系，产出透明底或暖纸底的手绘线稿插图。

设计口径
--------
- 笔触 5 种：fountain 钢笔 / pencil 铅笔 / brush 毛笔 / marker 马克笔 / charcoal 炭笔
- 配色 7 套：sepia 暖褐 / ochre 赭石 / amber 暖金 / terracotta 陶土 / rosewood 玫瑰木 /
             olive 暖橄榄 / ink 传统墨（兼容旧版）
- 填充 4 种：none / hachure 斜排线 / cross-hatch 交叉排线 / dots 点画
- 母题 32 个：16 个象征母题（叶/月/书/云…）+ 16 个场景母题（三级台阶/工位/会议桌/处理池/图纸/化验台/验收清单/合同/天平/函件/档案柜/健康/一家/启程/交接…）（v2.0 新增场景层）
- 参数：roughness 粗糙度、bowing 弯曲度、grain 颗粒、seed 种子（同种子可复现）

本模块只做库，命令行入口见 lineart_cli.py。
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

# ======================================================================
# 一、配色体系（暖色为主）
# ======================================================================
PALETTES = {
    "sepia":      {"cn": "暖褐",     "ink": (107, 74, 47),   "ink2": (150, 116, 80),  "accent": (169, 118, 74),  "paper": (251, 246, 236)},
    "ochre":      {"cn": "赭石",     "ink": (138, 90, 43),   "ink2": (176, 130, 72),  "accent": (192, 138, 62),  "paper": (252, 247, 238)},
    "amber":      {"cn": "暖金",     "ink": (122, 83, 32),   "ink2": (166, 124, 60),  "accent": (200, 155, 60),  "paper": (253, 249, 238)},
    "terracotta": {"cn": "陶土",     "ink": (140, 74, 52),   "ink2": (178, 112, 86),  "accent": (194, 112, 76),  "paper": (252, 245, 240)},
    "rosewood":   {"cn": "玫瑰木",   "ink": (122, 59, 59),   "ink2": (160, 96, 92),   "accent": (178, 104, 95),  "paper": (252, 245, 244)},
    "olive":      {"cn": "暖橄榄",   "ink": (94, 90, 44),    "ink2": (132, 128, 74),  "accent": (150, 142, 72),  "paper": (250, 249, 238)},
    "ink":        {"cn": "墨黑（传统）", "ink": (43, 43, 43), "ink2": (90, 90, 90),    "accent": (120, 120, 120), "paper": (250, 250, 248)},
}
WARM_PALETTES = [k for k in PALETTES if k != "ink"]

# ======================================================================
# 二、笔触档案（Rough.js 风格参数化）
# ======================================================================
# passes  复笔遍数（2–3 遍模拟 Rough.js 双描线，叠加读作手绘）
# jitter_k 抖动系数（乘在 roughness 基准之上）
# width_k  线宽系数
# alpha    首遍不透明度
# taper    是否变宽（起笔细—行笔粗—收笔细，模拟毛笔/铅笔压感）
# grain    墨色颗粒强度（纸纹/铅笔颗粒耦合）
# blur     收笔后高斯晕染半径（模拟墨水洇纸 / 铅笔柔边）
STROKE_PROFILES = {
    "fountain": {"cn": "钢笔",   "passes": 2, "jitter_k": 1.00, "width_k": 1.10, "alpha": 248, "taper": False, "grain": 0.05, "blur": 0.25},
    "pencil":   {"cn": "铅笔",   "passes": 3, "jitter_k": 1.25, "width_k": 1.05, "alpha": 234, "taper": False, "grain": 0.15, "blur": 0.35},
    "brush":    {"cn": "毛笔",   "passes": 2, "jitter_k": 1.35, "width_k": 1.60, "alpha": 250, "taper": True,  "grain": 0.08, "blur": 0.45},
    "marker":   {"cn": "马克笔", "passes": 1, "jitter_k": 0.55, "width_k": 2.00, "alpha": 255, "taper": False, "grain": 0.03, "blur": 0.18},
    "charcoal": {"cn": "炭笔",   "passes": 3, "jitter_k": 1.90, "width_k": 1.85, "alpha": 216, "taper": False, "grain": 0.28, "blur": 0.65},
}

# ======================================================================
# 三、母题库
# ======================================================================
MOTIF_META = {
    # —— 12 个基础母题（与《读者》版式一脉相承）——
    "leaf":     {"cn": "一叶",   "kw": ["叶", "树", "枝", "花", "草", "生长", "林", "森", "春", "绿"], "desc": "叶片与枝脉，喻成长与自然"},
    "sprout":   {"cn": "新芽",   "kw": ["种", "芽", "新生", "希望", "开始", "幼", "萌", "育"],        "desc": "破土新芽，喻起点与希望"},
    "mountain": {"cn": "远山",   "kw": ["山", "峰", "远方", "路", "跋涉", "岭", "高", "登"],          "desc": "层山与日轮，喻志向与远征"},
    "window":   {"cn": "窗",     "kw": ["窗", "家", "屋", "巷", "门", "邻", "房", "院"],              "desc": "窗棂与窗台，喻日常与家园"},
    "lamp":     {"cn": "灯",     "kw": ["灯", "光", "夜", "照", "明", "亮", "火", "暖"],              "desc": "桌灯与光晕，喻温暖与守候"},
    "book":     {"cn": "书",     "kw": ["书", "读", "字", "页", "翻", "写", "纸", "文"],              "desc": "摊开的书，喻阅读与文思"},
    "bird":     {"cn": "飞鸟",   "kw": ["鸟", "飞", "天空", "自由", "翅", "翔"],                      "desc": "掠空飞鸟，喻自由与远方"},
    "cloud":    {"cn": "云",     "kw": ["云", "天", "风", "雨", "飘", "空"],                          "desc": "叠云与风，喻闲适与变幻"},
    "moon":     {"cn": "月",     "kw": ["月", "星", "梦", "静", "夜", "黑"],                          "desc": "弦月与疏星，喻静思与梦境"},
    "ripple":   {"cn": "水波",   "kw": ["水", "河", "海", "波", "流", "湖", "雨"],                    "desc": "层层水波，喻时间与流动"},
    "boat":     {"cn": "舟",     "kw": ["船", "舟", "渡", "帆", "远航"],                              "desc": "一叶轻舟，喻渡越与前行"},
    "pattern":  {"cn": "纹样",   "kw": ["时间", "生命", "人生", "世界", "岁月"],                      "desc": "几何纹样，喻秩序与哲思"},
    # —— 4 个扩展母题（独立技能通用场景）——
    "tea":      {"cn": "一盏茶", "kw": ["茶", "咖啡", "饮", "香", "煮", "杯", "闲"],                  "desc": "杯盏与热气，喻慢与从容"},
    "bridge":   {"cn": "桥",     "kw": ["桥", "连接", "跨越", "两岸", "通", "渡口"],                  "desc": "拱桥与水，喻连接与过渡"},
    "star":     {"cn": "星",     "kw": ["星", "愿", "梦", "闪耀", "期", "盼"],                        "desc": "星芒与散星，喻愿望与指引"},
    "home":     {"cn": "小屋",   "kw": ["家", "房子", "屋", "居", "团圆", "归"],                      "desc": "屋顶与烟囱，喻归处与团圆"},
}
SCENE_META = {
    # —— 职场域 ——
    "steps3":    {"cn": "三级台阶", "kw": ["路径", "职业", "成长", "阶段", "晋升", "三段", "打底", "转型", "年轮", "规划"],
                  "desc": "三级台阶上三个前行人影，喻职业的三段路"},
    "desk":      {"cn": "工位",     "kw": ["一天", "日常", "工作", "工位", "办公室", "时间管理", "习惯", "节奏", "加班"],
                  "desc": "工位一角：屏、键、笔记与灯光，喻日复一日"},
    "meeting":   {"cn": "会议桌",   "kw": ["开会", "会议", "沟通", "协调", "跨部门", "讨论", "沟通会", "当面", "汇报", "碰头", "商量", "参会"],
                  "desc": "长桌与椅子围坐，喻商议与协调"},
    "interview": {"cn": "对坐",     "kw": ["面试", "招聘", "被面试", "面试别人", "谈", "对谈"],
                  "desc": "两人隔桌对坐，喻交谈与互选"},
    # —— 工程域 ——
    "plant":     {"cn": "处理池",   "kw": ["厂", "污水", "池", "运行", "运营", "养厂", "曝气", "工艺", "膜", "达标", "水厂"],
                  "desc": "池体剖面与管线阀门，喻运行与工艺"},
    "blueprint": {"cn": "图纸",     "kw": ["图纸", "竣工图", "设计", "方案", "考证", "双证", "参数", "画图", "尺寸"],
                  "desc": "展开的图纸与尺笔，喻设计与依据"},
    "lab":       {"cn": "化验台",   "kw": ["化验", "检测", "水质", "较真", "数据", "取样", "指标", "量"],
                  "desc": "锥形瓶、试管与天平，喻检测与较真"},
    "checklist": {"cn": "验收清单", "kw": ["验收", "清单", "检查", "竣工", "移交", "销项", "整改", "交验", "手续"],
                  "desc": "夹板上逐条勾选，喻核验与交付"},
    # —— 治理域 ——
    "contract":  {"cn": "合同",     "kw": ["合同", "签约", "条款", "救回", "发票", "付款", "协议", "约定", "关联交易"],
                  "desc": "文书、签字笔与印章，喻约定与凭据"},
    "scales":    {"cn": "天平",     "kw": ["诉讼", "争议", "权衡", "公平", "审计", "背锅", "责任", "是非", "质证", "答辩", "官司"],
                  "desc": "天平两端，喻权衡与是非"},
    "letter":    {"cn": "函件",     "kw": ["公函", "请示", "复函", "异议函", "书面意见", "致函", "来函", "回函", "此函"],
                  "desc": "信封与信笺，喻正式沟通与留痕"},
    "archive":   {"cn": "档案柜",   "kw": ["档案", "归档", "结算", "台账", "备案", "底稿", "错题本", "留痕", "归档资料"],
                  "desc": "档案柜与档案盒，喻积累与存档"},
    # —— 生活域 ——
    "health":    {"cn": "健康",     "kw": ["健康", "身体", "运动", "体检", "养生", "锻炼", "心率", "作息"],
                  "desc": "心率曲线与苹果，喻身体这本账"},
    "family":    {"cn": "一家",     "kw": ["家", "家庭", "孩子", "亲子", "孝顺", "养老", "团圆", "家人", "课"],
                  "desc": "屋檐下三口人手拉手，喻归处与牵挂"},
    "move":      {"cn": "启程",     "kw": ["换城", "搬家", "跳槽", "离开", "新环境", "行李", "远行", "换一座城", "留守"],
                  "desc": "行李箱与远城，喻迁徙与启程"},
    "handover":  {"cn": "交接",     "kw": ["移交", "交接", "过渡", "接棒", "交替", "交出去", "托付"],
                  "desc": "两人之间递出的文书，喻接棒与托付"},
}
MOTIF_META.update(SCENE_META)
MOTIFS = list(MOTIF_META)
SCENES = list(SCENE_META)


# ======================================================================
# 四、几何与纹理工具
# ======================================================================
def bez(p0, p1, p2, p3, n=40):
    """三次贝塞尔采样（曲线平滑，等价 Rough.js 的曲线拟合）"""
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def ellipse_pts(cx, cy, rx, ry, n=60, start=0.0, end=2 * math.pi):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a))
            for a in [start + (end - start) * i / n for i in range(n + 1)]]


def _value_noise(w, h, cell, seed):
    """值噪声：低分辨率随机点阵 + 双线性放大（SVG feTurbulence 的轻量等价物）"""
    gw, gh = max(2, w // cell), max(2, h // cell)
    rng = random.Random(seed)
    small = Image.new("L", (gw, gh))
    small.putdata([rng.randint(0, 255) for _ in range(gw * gh)])
    return small.resize((w, h), Image.BILINEAR)


def apply_grain(img, strength=0.18, cell=26, seed=1):
    """纸纹颗粒：局部削弱 alpha，让通体墨色有浓淡，模拟铅笔/炭笔的纸面摩擦"""
    if strength <= 0:
        return img
    w, h = img.size
    grain = _value_noise(w, h, cell, seed)
    grain = grain.point(lambda v: 255 - int((255 - v) * strength))
    alpha = ImageChops.multiply(img.getchannel("A"), grain)
    img.putalpha(alpha)
    return img


def apply_paper(img, paper=(251, 246, 236), grain=0.10, seed=1):
    """铺暖纸底：把透明底替换为暖纸色（带极轻纸纹），用于直接贴进页面"""
    w, h = img.size
    bg = Image.new("RGB", (w, h), paper)
    if grain > 0:
        n = _value_noise(w, h, 20, seed + 7).point(lambda v: 255 - int((255 - v) * grain * 0.5))
        bg = Image.composite(Image.new("RGB", (w, h), tuple(max(0, c - 6) for c in paper)), bg,
                             n.point(lambda v: 255 if v < 248 else 0).convert("L"))
    out = bg.convert("RGBA")
    out.alpha_composite(img)
    return out


def hachure_mask(size, shape_pts, angle=45, gap=14, jitter=1.6, color=(0, 0, 0), alpha=130,
                 passes=1, rng=None):
    """排线填充：在包围盒内铺等距平行线，再用形状 mask 裁剪（Rough.js hachure 的等价实现）
    shape_pts: 轮廓点列表；cross=True 时由调用方再叠一层反向排线。
    """
    w, h = size
    rng = rng or random.Random(7)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer, "RGBA")
    xs = [p[0] for p in shape_pts]
    ys = [p[1] for p in shape_pts]
    dx, dy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    px, py = -dy, dx                                   # 垂直于排线方向
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / 2 + gap
    k = int(span / gap) + 1
    for i in range(-k, k + 1):
        bx, by = cx + px * i * gap, cy + py * i * gap
        for p in range(max(1, passes)):
            jj = jitter * (1 + p * 0.7)
            p0 = (bx - dx * span + rng.uniform(-jj, jj), by - dy * span + rng.uniform(-jj, jj))
            p1 = (bx + dx * span + rng.uniform(-jj, jj), by + dy * span + rng.uniform(-jj, jj))
            ld.line([p0, p1], fill=(*color, alpha if p == 0 else max(40, alpha - 60)), width=2)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(shape_pts, fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    return layer


# ======================================================================
# 五、手绘笔（Rough.js 参数化：双描线 / bowing / 复笔 / 变宽）
# ======================================================================
class Pen:
    """手绘笔。所有几何图元统一走 line()，改一处即改全局笔感。"""

    def __init__(self, seed=0, scale=1.0, roughness=1.0, bowing=1.0,
                 style="fountain", palette="sepia", grain_scale=1.0):
        self.rng = random.Random(seed)
        self.seed = seed
        self.scale = scale
        self.roughness = roughness
        self.bowing = bowing
        self.style = style
        self.prof = STROKE_PROFILES.get(style, STROKE_PROFILES["fountain"])
        self.pal = PALETTES.get(palette, PALETTES["sepia"])
        self.grain_scale = grain_scale

    # ---------- 核心：一条手绘线 ----------
    def line(self, d, pts, color, w=3.0, jitter=None, passes=None, alpha=None, taper=None):
        prof = self.prof
        base_j = 1.7 * self.roughness * prof["jitter_k"]
        jj0 = base_j if jitter is None else jitter * prof["jitter_k"]
        n_pass = prof["passes"] if passes is None else passes
        a0 = prof["alpha"] if alpha is None else alpha
        use_taper = prof["taper"] if taper is None else taper
        w0 = max(1, int(round(w * self.scale * prof["width_k"])))

        # 短元素（星点/书页线/小图元）自动收敛抖动，避免细节被抖散
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        if span < 40:
            jj0 *= 0.45

        for p in range(n_pass):
            jj = jj0 * (1 + p * 0.35)
            # 两层抖动：整条线一次性偏移（保形状）+ 逐点微扰（出手绘毛边）
            oj = jj * 0.7
            ox, oy = self.rng.uniform(-oj, oj), self.rng.uniform(-oj, oj)
            jw = jj * 0.45
            jpts = [(x + ox + self.rng.uniform(-jw, jw), y + oy + self.rng.uniform(-jw, jw))
                    for x, y in pts]
            if self.bowing > 0 and len(jpts) == 2:          # 直线加一点弓形弯曲
                (x0, y0), (x1, y1) = jpts
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                nx, ny = -(y1 - y0), (x1 - x0)
                nl = math.hypot(nx, ny) or 1
                b = self.rng.uniform(-1, 1) * self.bowing * 3.2 * self.scale
                jpts = [jpts[0], (mx + nx / nl * b, my + ny / nl * b), jpts[1]]
            aa = a0 if p == 0 else max(48, a0 - 95)
            ww = max(1, int(round(w0 * (1.0 if p == 0 else 0.62))))
            if use_taper:
                self._taper(d, jpts, color, ww, aa)
            else:
                d.line(jpts, fill=(*color, aa), width=ww, joint="curve")

    def _taper(self, d, pts, color, wmax, alpha):
        """变宽笔触：起笔细—行笔粗—收笔细，模拟毛笔/铅笔压感"""
        n = len(pts)
        if n < 2:
            return
        for i in range(n - 1):
            t = i / (n - 1)
            k = 0.35 + 0.65 * math.sin(math.pi * t)      # 两端 0.35 倍，中段 1.0 倍
            w = max(1, int(round(wmax * k)))
            d.line([pts[i], pts[i + 1]], fill=(*color, alpha), width=w)

    # ---------- 图元 ----------
    def curve(self, d, p0, p1, p2, p3, color, w=3.0, **kw):
        self.line(d, bez(p0, p1, p2, p3), color, w, **kw)

    def circle(self, d, cx, cy, r, color, w=3.0, **kw):
        """圆：低频柔波（而非逐点随机），保证"圆仍是圆"，只有手绘的呼吸感"""
        ph = self.rng.uniform(0, 2 * math.pi)
        amp = 0.014 * self.roughness
        n = 52
        rr = []
        for i in range(n + 1):
            a = i * 2 * math.pi / n
            k = 1 + amp * math.sin(3 * a + ph) + amp * 0.5 * math.sin(7 * a + ph * 1.7)
            rr.append((cx + r * k * math.cos(a), cy + r * k * math.sin(a)))
        self.line(d, rr, color, w, **kw)

    def dot(self, d, x, y, r, color, alpha=215):
        d.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))

    # ---------- 排线填充 ----------
    def fill_hachure(self, img, shape_pts, angle=45, gap=14, color=None, alpha=125,
                     cross=False, dots=False):
        color = color or self.pal["accent"]
        if dots:
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer, "RGBA")
            xs = [p[0] for p in shape_pts]
            ys = [p[1] for p in shape_pts]
            step = gap * 1.7
            y = min(ys)
            while y < max(ys):
                x = min(xs)
                while x < max(xs):
                    ld.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(*color, alpha))
                    x += step
                y += step
            mask = Image.new("L", img.size, 0)
            ImageDraw.Draw(mask).polygon(shape_pts, fill=255)
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
            img.alpha_composite(layer)
            return
        img.alpha_composite(hachure_mask(img.size, shape_pts, angle, gap, 1.6, color, alpha, 1, self.rng))
        if cross:
            img.alpha_composite(hachure_mask(img.size, shape_pts, angle + 90, gap, 1.6, color,
                                             int(alpha * 0.75), 1, self.rng))


# ======================================================================
# 六、母题绘制（每个函数：d 画布 / W H 尺寸 / pen 手绘笔 / ink 主墨色）
# ======================================================================
def m_leaf(d, W, H, pen, ink):
    cx = W * 0.5
    pen.curve(d, (cx, H * 0.92), (cx - 40, H * 0.60), (cx + 40, H * 0.36), (cx, H * 0.12), ink, 3)
    for i, (t, side) in enumerate([(0.30, -1), (0.48, 1), (0.62, -1), (0.78, 1)]):
        y = H * (0.92 - t * 0.75)
        L = W * (0.22 - i * 0.02)
        tipx, tipy = cx + side * L, y - H * 0.10
        pen.curve(d, (cx, y), (cx + side * L * 0.4, y - H * 0.03), (cx + side * L * 0.8, y - H * 0.06), (tipx, tipy), ink, 2)
        pen.curve(d, (cx, y), (cx + side * L * 0.4, y + H * 0.03), (cx + side * L * 0.8, y - H * 0.02), (tipx, tipy), ink, 2)


def m_sprout(d, W, H, pen, ink):
    base = H * 0.80
    pen.line(d, [(W * 0.14, base), (W * 0.86, base)], ink, 2)
    cx = W * 0.5
    pen.curve(d, (cx, base), (cx - 16, base - H * 0.22), (cx + 14, base - H * 0.40), (cx, base - H * 0.56), ink, 3)
    for side in (-1, 1):
        pen.curve(d, (cx, base - H * 0.34), (cx + side * W * 0.12, base - H * 0.44),
                  (cx + side * W * 0.22, base - H * 0.40), (cx + side * W * 0.26, base - H * 0.30), ink, 2)
    pen.dot(d, cx, base - H * 0.60, 5, ink)


def m_mountain(d, W, H, pen, ink):
    base = H * 0.74
    for sx, ex, hgt in [(0.06, 0.52, 0.40), (0.40, 0.92, 0.30)]:
        top = base - H * hgt
        pen.line(d, [(W * sx, base), (W * (sx + ex) / 2 * 0.98, top), (W * ex, base)], ink, 3)
        pen.line(d, [(W * (sx + ex) / 2 * 0.9, top + H * 0.06), (W * (sx + ex) / 2 * 1.08, top + H * 0.11)], ink, 2)
    pen.line(d, [(W * 0.04, base), (W * 0.96, base)], ink, 2)
    for cx, cy, r in [(0.70, 0.20, 0.05), (0.79, 0.24, 0.035)]:
        pen.curve(d, (W * cx - W * r, H * cy), (W * cx - W * r * 0.4, H * cy - H * r),
                  (W * cx + W * r * 0.4, H * cy - H * r), (W * cx + W * r, H * cy), ink, 2)
        pen.line(d, [(W * cx - W * r, H * cy), (W * cx + W * r, H * cy)], ink, 2)


def m_window(d, W, H, pen, ink):
    x0, y0, x1, y1 = W * 0.26, H * 0.16, W * 0.74, H * 0.72
    for pts in [[(x0, y0), (x1, y0)], [(x0, y1), (x1, y1)], [(x0, y0), (x0, y1)], [(x1, y0), (x1, y1)]]:
        pen.line(d, pts, ink, 3)
    pen.line(d, [(W * 0.5, y0), (W * 0.5, y1)], ink, 2)
    pen.line(d, [(x0, H * 0.44), (x1, H * 0.44)], ink, 2)
    pen.line(d, [(x0 - W * 0.05, y1), (x1 + W * 0.05, y1)], ink, 3)


def m_lamp(d, W, H, pen, ink):
    cx, top = W * 0.5, H * 0.10
    pen.line(d, [(cx, top), (cx, H * 0.30)], ink, 2)
    pen.line(d, [(W * 0.36, H * 0.30), (W * 0.64, H * 0.30)], ink, 3)
    pen.line(d, [(W * 0.36, H * 0.30), (W * 0.42, H * 0.52), (W * 0.58, H * 0.52), (W * 0.64, H * 0.30)], ink, 3)
    pen.curve(d, (W * 0.42, H * 0.52), (W * 0.46, H * 0.62), (W * 0.54, H * 0.62), (W * 0.58, H * 0.52), ink, 2)
    pen.circle(d, cx, H * 0.44, H * 0.19, ink, 1, passes=1, alpha=80)              # 柔光晕
    pen.line(d, [(W * 0.40, H * 0.68), (W * 0.60, H * 0.68)], ink, 1, alpha=140)  # 桌沿线


def m_book(d, W, H, pen, ink):
    cx, cy = W * 0.5, H * 0.56
    pen.line(d, [(W * 0.16, cy), (W * 0.16, H * 0.80)], ink, 3)
    pen.line(d, [(W * 0.84, cy), (W * 0.84, H * 0.80)], ink, 3)
    pen.curve(d, (W * 0.16, cy), (W * 0.34, cy - H * 0.10), (W * 0.46, cy - H * 0.06), (cx, cy), ink, 3)
    pen.curve(d, (cx, cy), (W * 0.54, cy - H * 0.06), (W * 0.66, cy - H * 0.10), (W * 0.84, cy), ink, 3)
    pen.line(d, [(cx, cy), (cx, H * 0.82)], ink, 2)
    for k in range(4):
        y = cy + H * 0.05 + k * H * 0.045
        pen.line(d, [(W * 0.22, y), (W * 0.44, y)], ink, 1, alpha=150)
        pen.line(d, [(W * 0.56, y), (W * 0.78, y)], ink, 1, alpha=150)


def m_bird(d, W, H, pen, ink):
    for cx, cy, s in [(0.36, 0.40, 1.0), (0.58, 0.30, 0.7), (0.68, 0.52, 0.55)]:
        w = W * 0.10 * s
        pen.curve(d, (W * cx - w, H * cy), (W * cx - w * 0.4, H * cy - H * 0.06 * s),
                  (W * cx + w * 0.4, H * cy - H * 0.06 * s), (W * cx + w, H * cy), ink, 2)
        pen.curve(d, (W * cx + w, H * cy), (W * cx + w * 1.6, H * cy - H * 0.05 * s),
                  (W * cx + w * 2.2, H * cy - H * 0.03 * s), (W * cx + w * 2.6, H * cy), ink, 2)


def m_cloud(d, W, H, pen, ink):
    cy = H * 0.42
    pen.curve(d, (W * 0.20, cy), (W * 0.24, cy - H * 0.14), (W * 0.36, cy - H * 0.16), (W * 0.42, cy), ink, 3)
    pen.curve(d, (W * 0.36, cy), (W * 0.40, cy - H * 0.20), (W * 0.56, cy - H * 0.18), (W * 0.58, cy), ink, 3)
    pen.curve(d, (W * 0.52, cy), (W * 0.58, cy - H * 0.12), (W * 0.70, cy - H * 0.10), (W * 0.74, cy), ink, 3)
    pen.line(d, [(W * 0.20, cy), (W * 0.74, cy)], ink, 3)


def m_moon(d, W, H, pen, ink):
    """真月牙：外弧（经左侧的 280° 弧）+ 内弧（右凸的凹弧），两侧共用端点闭合"""
    cx, cy, r = W * 0.40, H * 0.46, H * 0.26
    a = math.radians(66)
    pen.line(d, ellipse_pts(cx, cy, r, r, 64, start=a, end=2 * math.pi - a), ink, 3)  # 外弧（左侧 228°）
    k = -1.5                                             # 内弧圆心左偏，深度决定月牙厚薄（-1.5→厚约 0.39r）
    icx = cx + k * r
    ir = math.hypot(r * math.cos(a) - k * r, r * math.sin(a))
    ang = math.atan2(r * math.sin(a), r * math.cos(a) - k * r)   # 端点相对内圆心的张角
    pen.line(d, ellipse_pts(icx, cy, ir, ir, 56, start=ang, end=-ang), ink, 3)  # 内凹弧（右凸浅凹）
    for sx, sy, s in [(0.74, 0.22, 7), (0.84, 0.40, 5), (0.68, 0.60, 4)]:
        pen.line(d, [(W * sx - s, H * sy), (W * sx + s, H * sy)], ink, 2)
        pen.line(d, [(W * sx, H * sy - s), (W * sx, H * sy + s)], ink, 2)


def m_ripple(d, W, H, pen, ink):
    cx, cy = W * 0.5, H * 0.52
    for i in range(5):
        rx, ry = W * (0.12 + i * 0.075), H * (0.05 + i * 0.032)
        pts = [p for p in ellipse_pts(cx, cy, rx, ry, 60) if p[1] >= cy - ry * 1.2]
        pen.line(d, pts, ink, 2, alpha=180 - i * 22, jitter=1.4)


def m_boat(d, W, H, pen, ink):
    cy = H * 0.62
    pen.curve(d, (W * 0.28, cy), (W * 0.38, cy + H * 0.10), (W * 0.62, cy + H * 0.10), (W * 0.72, cy), ink, 3)
    pen.line(d, [(W * 0.28, cy), (W * 0.72, cy)], ink, 3)
    pen.line(d, [(W * 0.50, cy), (W * 0.50, H * 0.26)], ink, 3)
    pen.line(d, [(W * 0.50, H * 0.28), (W * 0.68, cy - H * 0.02)], ink, 2)
    pen.line(d, [(W * 0.50, H * 0.30), (W * 0.36, cy - H * 0.02)], ink, 2)
    for k in range(3):
        y = cy + H * 0.16 + k * H * 0.05
        pen.line(d, [(W * 0.30 + k * W * 0.02, y), (W * 0.70 - k * W * 0.02, y)], ink, 2, alpha=150 - k * 30)


def m_pattern(d, W, H, pen, ink):
    pen.circle(d, W * 0.5, H * 0.5, H * 0.26, ink, 3, jitter=2.2)
    pen.circle(d, W * 0.5, H * 0.5, H * 0.16, ink, 2, jitter=2.0)
    for k in range(8):
        a = k * math.pi / 4
        pen.line(d, [(W * 0.5 + math.cos(a) * H * 0.18, H * 0.5 + math.sin(a) * H * 0.18),
                     (W * 0.5 + math.cos(a) * H * 0.30, H * 0.5 + math.sin(a) * H * 0.30)], ink, 2, alpha=170)
    pen.dot(d, W * 0.5, H * 0.5, 6, ink)


def m_tea(d, W, H, pen, ink):
    cy = H * 0.62
    pen.line(d, [(W * 0.30, cy), (W * 0.36, cy + H * 0.22), (W * 0.64, cy + H * 0.22), (W * 0.70, cy)], ink, 3)
    pen.line(d, [(W * 0.30, cy), (W * 0.70, cy)], ink, 3)
    pen.line(d, [(W * 0.22, cy + H * 0.26), (W * 0.78, cy + H * 0.26)], ink, 3)
    pen.curve(d, (W * 0.70, cy + H * 0.06), (W * 0.80, cy + H * 0.02), (W * 0.82, cy + H * 0.14), (W * 0.72, cy + H * 0.14), ink, 2)
    for i, x in enumerate([0.42, 0.50, 0.58]):
        pen.curve(d, (W * x, cy - H * 0.06), (W * x - 10, cy - H * 0.18), (W * x + 10, cy - H * 0.24), (W * x, cy - H * 0.34), ink, 1, alpha=150)


def m_bridge(d, W, H, pen, ink):
    base = H * 0.60
    pen.curve(d, (W * 0.16, base), (W * 0.32, base - H * 0.30), (W * 0.68, base - H * 0.30), (W * 0.84, base), ink, 3)
    pen.line(d, [(W * 0.16, base), (W * 0.84, base)], ink, 2)
    pen.line(d, [(W * 0.16, base), (W * 0.16, H * 0.74)], ink, 2)
    pen.line(d, [(W * 0.84, base), (W * 0.84, H * 0.74)], ink, 2)
    for k in range(4):
        x = W * (0.28 + k * 0.147)
        pen.line(d, [(x, base - H * 0.16 + abs(k - 1.5) * H * 0.05), (x, base)], ink, 1, alpha=170)
    for k in range(3):
        y = H * (0.80 + k * 0.05)
        pen.line(d, [(W * (0.22 + k * 0.03), y), (W * (0.78 - k * 0.03), y)], ink, 1, alpha=150 - k * 30)


def m_star(d, W, H, pen, ink):
    cx, cy, R = W * 0.44, H * 0.42, H * 0.26
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = R if k % 2 == 0 else R * 0.42
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pen.line(d, pts + [pts[0]], ink, 3)
    for sx, sy, s in [(0.76, 0.22, 4), (0.85, 0.42, 3), (0.72, 0.62, 3)]:
        pen.dot(d, W * sx, H * sy, s, ink, alpha=170)


def m_home(d, W, H, pen, ink):
    x0, x1 = W * 0.24, W * 0.76
    yb, yr = H * 0.74, H * 0.46
    pen.line(d, [(x0, yr), (W * 0.5, H * 0.20), (x1, yr)], ink, 3)
    pen.line(d, [(x0, yr), (x0, yb), (x1, yb), (x1, yr)], ink, 3)
    pen.line(d, [(W * 0.60, H * 0.26), (W * 0.60, H * 0.16), (W * 0.68, H * 0.16)], ink, 2)
    pen.line(d, [(W * 0.36, H * 0.62), (W * 0.46, H * 0.62), (W * 0.46, yb)], ink, 2)
    pen.line(d, [(W * 0.58, H * 0.58), (W * 0.70, H * 0.58), (W * 0.70, H * 0.66), (W * 0.58, H * 0.66), (W * 0.58, H * 0.58)], ink, 2)
    pen.line(d, [(W * 0.64, H * 0.58), (W * 0.64, H * 0.66)], ink, 1, alpha=160)
    pen.line(d, [(W * 0.58, H * 0.62), (W * 0.70, H * 0.62)], ink, 1, alpha=160)




# ======================================================================
# 六之二、场景母题（v2.0：具体物件与人物，贴合文章内容）
# ======================================================================
def person(d, pen, x, y, h=1.0, ink=(0, 0, 0), pose="stand"):
    """简笔人影：y 为脚底。头 + 躯干 + 双腿 + 双臂（姿势可选）"""
    pen.circle(d, x, y - 46 * h, 13 * h, ink, 2)
    pen.line(d, [(x, y - 33 * h), (x, y - 8 * h)], ink, 3)
    if pose == "sit":
        pen.line(d, [(x, y - 8 * h), (x + 15 * h, y - 8 * h)], ink, 3)
        pen.line(d, [(x + 15 * h, y - 8 * h), (x + 17 * h, y + 12 * h)], ink, 3)
        pen.line(d, [(x, y - 8 * h), (x - 3 * h, y + 12 * h)], ink, 3)
        pen.line(d, [(x, y - 28 * h), (x + 11 * h, y - 16 * h)], ink, 2)
    else:
        pen.line(d, [(x, y - 8 * h), (x - 8 * h, y + 14 * h)], ink, 3)
        pen.line(d, [(x, y - 8 * h), (x + 8 * h, y + 14 * h)], ink, 3)
        if pose == "raise":
            pen.line(d, [(x, y - 28 * h), (x + 13 * h, y - 42 * h)], ink, 2)
            pen.line(d, [(x, y - 28 * h), (x - 12 * h, y - 38 * h)], ink, 2)
        elif pose == "point":
            pen.line(d, [(x, y - 28 * h), (x + 16 * h, y - 30 * h)], ink, 2)
            pen.line(d, [(x, y - 28 * h), (x - 9 * h, y - 14 * h)], ink, 2)
        else:
            pen.line(d, [(x, y - 28 * h), (x + 10 * h, y - 12 * h)], ink, 2)
            pen.line(d, [(x, y - 28 * h), (x - 10 * h, y - 12 * h)], ink, 2)


def s_steps3(d, W, H, pen, ink):
    """三级台阶 + 三个前行人影：喻职业路径的三段"""
    base = H * 0.80
    x0, sw, sh = W * 0.20, W * 0.19, H * 0.10
    for i in range(3):
        x, y = x0 + i * sw, base - (i + 1) * sh
        pen.line(d, [(x, y), (x + sw, y)], ink, 3)
        pen.line(d, [(x + sw, y), (x + sw, base)], ink, 2)
        person(d, pen, x + sw * 0.48, y - 4, h=0.52 + i * 0.09, ink=ink, pose="stand")
    pen.line(d, [(x0 - W * 0.04, base), (W * 0.93, base)], ink, 2)
    pen.curve(d, (W * 0.86, H * 0.34), (W * 0.90, H * 0.24), (W * 0.94, H * 0.22), (W * 0.96, H * 0.14), ink, 2)
    pen.line(d, [(W * 0.96, H * 0.14), (W * 0.93, H * 0.19)], ink, 2)
    pen.line(d, [(W * 0.96, H * 0.14), (W * 0.91, H * 0.15)], ink, 2)


def s_desk(d, W, H, pen, ink):
    """工位一角：显示器、键盘、笔记、台灯、咖啡"""
    ty = H * 0.72
    pen.line(d, [(W * 0.10, ty), (W * 0.90, ty)], ink, 3)
    pen.line(d, [(W * 0.14, ty), (W * 0.14, H * 0.92)], ink, 2)
    pen.line(d, [(W * 0.86, ty), (W * 0.86, H * 0.92)], ink, 2)
    pen.line(d, [(W * 0.30, ty), (W * 0.30, H * 0.50), (W * 0.62, H * 0.50), (W * 0.62, ty)], ink, 3)   # 屏
    pen.line(d, [(W * 0.28, H * 0.50), (W * 0.64, H * 0.50)], ink, 3)
    for k in range(3):
        y = H * 0.55 + k * H * 0.045
        pen.line(d, [(W * 0.34, y), (W * 0.58, y)], ink, 1, alpha=150)
    pen.line(d, [(W * 0.22, ty - H * 0.03), (W * 0.46, ty - H * 0.03)], ink, 2)          # 键盘
    pen.line(d, [(W * 0.68, ty - H * 0.02), (W * 0.82, ty - H * 0.02)], ink, 2)          # 笔记
    pen.line(d, [(W * 0.70, ty - H * 0.05), (W * 0.80, ty - H * 0.05)], ink, 1, alpha=160)
    pen.curve(d, (W * 0.20, ty - H * 0.08), (W * 0.22, ty - H * 0.20), (W * 0.30, ty - H * 0.20), (W * 0.30, ty - H * 0.13), ink, 2)
    pen.line(d, [(W * 0.20, ty - H * 0.08), (W * 0.20, ty - H * 0.26), (W * 0.26, ty - H * 0.26)], ink, 2)


def s_meeting(d, W, H, pen, ink):
    """会议：长桌、围坐、白板"""
    ty = H * 0.70
    pen.line(d, [(W * 0.16, ty), (W * 0.84, ty)], ink, 3)
    pen.line(d, [(W * 0.16, ty + H * 0.05), (W * 0.84, ty + H * 0.05)], ink, 3)
    pen.line(d, [(W * 0.16, ty), (W * 0.16, ty + H * 0.05)], ink, 2)
    pen.line(d, [(W * 0.84, ty), (W * 0.84, ty + H * 0.05)], ink, 2)
    for i in range(4):
        person(d, pen, W * (0.26 + i * 0.16), ty - 6, h=0.46, ink=ink, pose="sit")
    pen.line(d, [(W * 0.62, H * 0.54), (W * 0.90, H * 0.54), (W * 0.90, H * 0.16), (W * 0.62, H * 0.16), (W * 0.62, H * 0.54)], ink, 3)
    for k in range(3):
        y = H * 0.24 + k * H * 0.07
        pen.line(d, [(W * 0.66, y), (W * (0.80 - k * 0.03), y)], ink, 1, alpha=160)
    person(d, pen, W * 0.53, H * 0.30, h=0.52, ink=ink, pose="point")


def s_interview(d, W, H, pen, ink):
    """对坐：两人隔桌交谈，上方一对对话气泡"""
    ty = H * 0.66
    pen.line(d, [(W * 0.28, ty), (W * 0.72, ty)], ink, 3)
    pen.line(d, [(W * 0.32, ty), (W * 0.32, H * 0.82)], ink, 2)
    pen.line(d, [(W * 0.68, ty), (W * 0.68, H * 0.82)], ink, 2)
    pen.line(d, [(W * 0.40, ty - H * 0.02), (W * 0.54, ty - H * 0.02)], ink, 2)
    pen.line(d, [(W * 0.42, ty - H * 0.05), (W * 0.52, ty - H * 0.05)], ink, 1, alpha=160)
    person(d, pen, W * 0.20, ty + H * 0.07, h=0.68, ink=ink, pose="sit")
    person(d, pen, W * 0.80, ty + H * 0.07, h=0.64, ink=ink, pose="sit")
    pen.line(d, ellipse_pts(W * 0.34, H * 0.26, W * 0.105, H * 0.075, 40), ink, 2)
    pen.line(d, [(W * 0.28, H * 0.32), (W * 0.25, H * 0.40), (W * 0.33, H * 0.33)], ink, 2)
    pen.line(d, ellipse_pts(W * 0.66, H * 0.20, W * 0.085, H * 0.062, 40), ink, 2)
    pen.line(d, [(W * 0.71, H * 0.25), (W * 0.74, H * 0.32), (W * 0.66, H * 0.26)], ink, 2)
def s_plant(d, W, H, pen, ink):
    """处理池剖面：池体、水面、进水管、阀门、气泡"""
    x0, y0, x1, y1 = W * 0.16, H * 0.34, W * 0.84, H * 0.78
    pen.line(d, [(x0, y0), (x0, y1), (x1, y1), (x1, y0)], ink, 3)
    pen.line(d, [(x0, y0), (x1, y0)], ink, 2)
    wy = y0 + H * 0.16
    pen.line(d, [(x0, wy), (x1, wy)], ink, 2)
    for i in range(6):
        cx = x0 + W * 0.06 + i * W * 0.11
        pen.line(d, [(cx - W * 0.035, wy), (cx, wy - H * 0.025), (cx + W * 0.035, wy)], ink, 1, alpha=170)
    for i in range(5):
        cx = x0 + W * (0.10 + i * 0.16)
        r = 4 + (i % 3) * 3
        pen.circle(d, cx, y1 - H * 0.06 - (i % 3) * H * 0.03, r, ink, 1, passes=1, alpha=110)
    pen.line(d, [(x0 - W * 0.10, y0 - H * 0.06), (x0, y0 - H * 0.06), (x0, y0 + H * 0.06)], ink, 3)   # 进水管
    pen.circle(d, x0 - W * 0.05, y0 - H * 0.06, H * 0.028, ink, 2, passes=1)                          # 阀门
    pen.line(d, [(x1, y1), (x1 + W * 0.10, y1)], ink, 3)                                              # 出水管


def s_blueprint(d, W, H, pen, ink):
    """图纸：展开的图纸、直尺、铅笔、尺寸线"""
    x0, y0, x1, y1 = W * 0.18, H * 0.22, W * 0.78, H * 0.70
    pen.line(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], ink, 3)
    pen.line(d, [(x0 + W * 0.06, y1), (x0 + W * 0.06, y0 + H * 0.08), (x1 - W * 0.08, y0 + H * 0.08)], ink, 2)
    pen.circle(d, W * 0.36, H * 0.50, H * 0.09, ink, 2, passes=1)
    pen.line(d, [(W * 0.52, y0 + H * 0.10), (W * 0.72, y0 + H * 0.10)], ink, 1, alpha=160)
    pen.line(d, [(W * 0.52, y0 + H * 0.18), (W * 0.68, y0 + H * 0.18)], ink, 1, alpha=160)
    pen.line(d, [(W * 0.52, y0 + H * 0.26), (W * 0.70, y0 + H * 0.26)], ink, 1, alpha=160)
    pen.line(d, [(x0, y1 + H * 0.10), (x1 - W * 0.10, y1 + H * 0.10)], ink, 2)          # 尺寸线
    for xx in (x0, x1 - W * 0.10):
        pen.line(d, [(xx, y1 + H * 0.07), (xx, y1 + H * 0.13)], ink, 2)
    pen.line(d, [(W * 0.80, H * 0.80), (W * 0.94, H * 0.62)], ink, 3)                   # 铅笔
    pen.line(d, [(W * 0.94, H * 0.62), (W * 0.97, H * 0.58)], ink, 2)


def s_lab(d, W, H, pen, ink):
    """化验台：锥形瓶、试管架、滴管、天平"""
    ty = H * 0.74
    pen.line(d, [(W * 0.10, ty), (W * 0.90, ty)], ink, 3)
    pen.line(d, [(W * 0.16, ty), (W * 0.16, H * 0.86)], ink, 2)
    pen.line(d, [(W * 0.84, ty), (W * 0.84, H * 0.86)], ink, 2)
    pen.line(d, [(W * 0.28, H * 0.46), (W * 0.36, ty)], ink, 2)                          # 锥形瓶
    pen.line(d, [(W * 0.40, H * 0.46), (W * 0.32, ty)], ink, 2)
    pen.line(d, [(W * 0.28, H * 0.46), (W * 0.40, H * 0.46)], ink, 2)
    pen.curve(d, (W * 0.30, H * 0.52), (W * 0.33, H * 0.56), (W * 0.37, H * 0.56), (W * 0.395, H * 0.52), ink, 1, alpha=150)
    pen.line(d, [(W * 0.50, ty), (W * 0.50, H * 0.42)], ink, 2)                          # 试管架
    pen.line(d, [(W * 0.66, ty), (W * 0.66, H * 0.42)], ink, 2)
    pen.line(d, [(W * 0.46, ty), (W * 0.70, ty)], ink, 2)
    for i, xx in enumerate([0.50, 0.58, 0.66]):
        pen.line(d, [(W * xx, H * 0.30), (W * xx, H * 0.42)], ink, 2)
        pen.curve(d, (W * xx - W * 0.015, H * 0.30), (W * xx - W * 0.012, H * 0.27), (W * xx + W * 0.012, H * 0.27), (W * xx + W * 0.015, H * 0.30), ink, 2)
    pen.line(d, [(W * 0.76, H * 0.40), (W * 0.76, ty)], ink, 2)                          # 支架
    pen.line(d, [(W * 0.72, ty), (W * 0.80, ty)], ink, 2)


def s_checklist(d, W, H, pen, ink):
    """验收清单：夹板、逐条勾选、笔与印章"""
    x0, y0, x1, y1 = W * 0.24, H * 0.14, W * 0.66, H * 0.84
    pen.line(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], ink, 3)
    pen.line(d, [(x0 + W * 0.08, y0 - H * 0.04), (x1 - W * 0.08, y0 - H * 0.04)], ink, 3)   # 夹板
    for k in range(4):
        y = y0 + H * 0.14 + k * H * 0.16
        bx = x0 + W * 0.06
        pen.line(d, [(bx, y), (bx + W * 0.055, y), (bx + W * 0.055, y + H * 0.065), (bx, y + H * 0.065), (bx, y)], ink, 2)
        if k < 3:
            pen.line(d, [(bx + W * 0.012, y + H * 0.038), (bx + W * 0.024, y + H * 0.052), (bx + W * 0.046, y + H * 0.012)], ink, 2)
        pen.line(d, [(bx + W * 0.09, y + H * 0.032), (x1 - W * 0.05, y + H * 0.032)], ink, 1, alpha=160)
    pen.line(d, [(W * 0.72, H * 0.76), (W * 0.88, H * 0.56)], ink, 3)                       # 笔
    pen.line(d, [(W * 0.88, H * 0.56), (W * 0.91, H * 0.52)], ink, 2)
    pen.circle(d, W * 0.76, H * 0.30, H * 0.055, ink, 2, passes=1)                          # 印章
    pen.circle(d, W * 0.76, H * 0.30, H * 0.032, ink, 1, passes=1, alpha=150)


def s_contract(d, W, H, pen, ink):
    """合同：文书、签字笔、印章"""
    pen.line(d, [(W * 0.20, H * 0.26), (W * 0.66, H * 0.26), (W * 0.66, H * 0.78), (W * 0.20, H * 0.78), (W * 0.20, H * 0.26)], ink, 3)
    pen.line(d, [(W * 0.26, H * 0.76), (W * 0.60, H * 0.76), (W * 0.60, H * 0.30), (W * 0.26, H * 0.30), (W * 0.26, H * 0.76)], ink, 2)
    for k in range(5):
        y = H * 0.36 + k * H * 0.075
        pen.line(d, [(W * 0.30, y), (W * (0.52 - k * 0.02), y)], ink, 1, alpha=160)
    pen.line(d, [(W * 0.62, H * 0.72), (W * 0.78, H * 0.48)], ink, 3)                        # 签字笔
    pen.line(d, [(W * 0.78, H * 0.48), (W * 0.81, H * 0.44)], ink, 2)
    pen.circle(d, W * 0.70, H * 0.62, H * 0.065, ink, 2, passes=1)                            # 印章
    pen.circle(d, W * 0.70, H * 0.62, H * 0.036, ink, 1, passes=1, alpha=150)
    pen.line(d, [(W * 0.36, H * 0.86), (W * 0.72, H * 0.86)], ink, 2)


def s_scales(d, W, H, pen, ink):
    """天平：立柱、横梁、两托盘"""
    cx, ty = W * 0.50, H * 0.34
    pen.line(d, [(cx, ty), (cx, H * 0.80)], ink, 3)
    pen.line(d, [(cx - W * 0.12, H * 0.80), (cx + W * 0.12, H * 0.80)], ink, 3)
    pen.line(d, [(cx - W * 0.22, ty), (cx + W * 0.22, ty)], ink, 3)
    pen.circle(d, cx, ty, H * 0.035, ink, 2, passes=1)
    for side in (-1, 1):
        px = cx + side * W * 0.22
        pen.line(d, [(px, ty), (px, ty + H * 0.14)], ink, 2)
        pen.curve(d, (px - W * 0.075, ty + H * 0.14), (px - W * 0.05, ty + H * 0.21), (px + W * 0.05, ty + H * 0.21), (px + W * 0.075, ty + H * 0.14), ink, 2)
        pen.line(d, [(px - W * 0.075, ty + H * 0.14), (px + W * 0.075, ty + H * 0.14)], ink, 2)
    pen.line(d, [(cx - W * 0.27, ty + H * 0.08), (cx - W * 0.17, ty + H * 0.08), (cx - W * 0.17, ty + H * 0.14), (cx - W * 0.27, ty + H * 0.14), (cx - W * 0.27, ty + H * 0.08)], ink, 2)
    pen.line(d, [(cx + W * 0.18, ty + H * 0.12), (cx + W * 0.26, ty + H * 0.12)], ink, 2)


def s_letter(d, W, H, pen, ink):
    """函件：信封、信笺、邮戳"""
    x0, y0, x1, y1 = W * 0.22, H * 0.34, W * 0.72, H * 0.72
    pen.line(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], ink, 3)
    pen.line(d, [(x0, y0), (W * 0.47, H * 0.55), (x1, y0)], ink, 2)
    pen.circle(d, W * 0.76, H * 0.28, H * 0.07, ink, 2, passes=1)
    pen.circle(d, W * 0.76, H * 0.28, H * 0.045, ink, 1, passes=1, alpha=150)
    for k in range(2):
        y = H * 0.24 + k * H * 0.07
        pen.line(d, [(W * 0.71, y), (W * 0.81, y)], ink, 1, alpha=140)
    pen.line(d, [(W * 0.14, H * 0.82), (W * 0.80, H * 0.82)], ink, 2)
    pen.line(d, [(W * 0.14, H * 0.86), (W * 0.62, H * 0.86)], ink, 1, alpha=150)


def s_archive(d, W, H, pen, ink):
    """档案柜：抽屉柜与档案盒"""
    x0, x1 = W * 0.18, W * 0.60
    pen.line(d, [(x0, H * 0.24), (x1, H * 0.24), (x1, H * 0.80), (x0, H * 0.80), (x0, H * 0.24)], ink, 3)
    for k in range(3):
        y = H * 0.24 + (k + 1) * H * 0.186
        pen.line(d, [(x0, y), (x1, y)], ink, 2)
        pen.line(d, [(W * 0.37, y - H * 0.09), (W * 0.42, y - H * 0.09)], ink, 2)
    for k in range(3):
        bx = W * (0.66 + k * 0.10)
        by = H * (0.80 - k * H * 0.01)
        pen.line(d, [(bx, by - H * 0.30), (bx + W * 0.075, by - H * 0.30), (bx + W * 0.075, by), (bx, by), (bx, by - H * 0.30)], ink, 2)
        pen.line(d, [(bx + W * 0.012, by - H * 0.25), (bx + W * 0.063, by - H * 0.25)], ink, 1, alpha=170)
    pen.line(d, [(W * 0.10, H * 0.80), (W * 0.92, H * 0.80)], ink, 2)


def s_health(d, W, H, pen, ink):
    """健康：心率曲线、苹果、哑铃"""
    pen.line(d, [(W * 0.12, H * 0.34), (W * 0.30, H * 0.34), (W * 0.36, H * 0.18),
                 (W * 0.42, H * 0.50), (W * 0.48, H * 0.34), (W * 0.88, H * 0.34)], ink, 3)
    pen.line(d, ellipse_pts(W * 0.27, H * 0.68, H * 0.085, H * 0.085, 44), ink, 2)
    pen.line(d, [(W * 0.27, H * 0.595), (W * 0.27, H * 0.555)], ink, 2)
    pen.curve(d, (W * 0.285, H * 0.60), (W * 0.30, H * 0.57), (W * 0.325, H * 0.57), (W * 0.34, H * 0.60), ink, 2)
    cx, cy = W * 0.68, H * 0.70
    pen.line(d, [(cx - W * 0.095, cy), (cx + W * 0.095, cy)], ink, 3)
    for sx in (-1, 1):
        pen.line(d, [(cx + sx * W * 0.095, cy - H * 0.055), (cx + sx * W * 0.095, cy + H * 0.055)], ink, 4)
        pen.line(d, [(cx + sx * W * 0.125, cy - H * 0.042), (cx + sx * W * 0.125, cy + H * 0.042)], ink, 3)
def s_family(d, W, H, pen, ink):
    """一家：屋檐下三人牵手"""
    pen.line(d, [(W * 0.16, H * 0.42), (W * 0.50, H * 0.18), (W * 0.84, H * 0.42)], ink, 3)
    pen.line(d, [(W * 0.20, H * 0.42), (W * 0.20, H * 0.78), (W * 0.80, H * 0.78), (W * 0.80, H * 0.42)], ink, 3)
    person(d, pen, W * 0.36, H * 0.78, h=0.62, ink=ink)
    person(d, pen, W * 0.50, H * 0.78, h=0.50, ink=ink)
    person(d, pen, W * 0.63, H * 0.78, h=0.40, ink=ink)
    pen.line(d, [(W * 0.40, H * 0.60), (W * 0.46, H * 0.63)], ink, 2)
    pen.line(d, [(W * 0.54, H * 0.64), (W * 0.60, H * 0.66)], ink, 2)


def s_move(d, W, H, pen, ink):
    """启程：行李箱、远城、路标"""
    bx, by = W * 0.20, H * 0.80
    pen.line(d, [(bx, by), (W * 0.40, by), (W * 0.40, H * 0.50), (bx, H * 0.50), (bx, by)], ink, 3)
    pen.line(d, [(bx + W * 0.035, H * 0.50), (bx + W * 0.035, H * 0.44), (W * 0.365, H * 0.44), (W * 0.365, H * 0.50)], ink, 2)
    pen.line(d, [(bx, H * 0.62), (W * 0.40, H * 0.62)], ink, 2)
    pen.line(d, [(bx + W * 0.02, by + H * 0.03), (bx + W * 0.04, by - H * 0.02)], ink, 2)
    for i, (fx, fw, fh) in enumerate([(0.54, 0.10, 0.30), (0.66, 0.13, 0.44), (0.81, 0.09, 0.24)]):
        pen.line(d, [(W * fx, H * 0.80), (W * fx, H * (0.80 - fh)), (W * (fx + fw), H * (0.80 - fh)), (W * (fx + fw), H * 0.80)], ink, 2)
        for k in range(3):
            yy = H * (0.80 - fh) + (k + 1) * H * (fh / 4)
            pen.line(d, [(W * (fx + fw * 0.25), yy), (W * (fx + fw * 0.75), yy)], ink, 1, alpha=150)
    pen.line(d, [(W * 0.14, H * 0.86), (W * 0.90, H * 0.86)], ink, 2)


def s_handover(d, W, H, pen, ink):
    """交接：两人之间递出的文书，上方弧线箭头"""
    mx, my = W * 0.50, H * 0.54
    pen.line(d, [(mx - W * 0.10, my - H * 0.085), (mx + W * 0.10, my - H * 0.085),
                 (mx + W * 0.10, my + H * 0.085), (mx - W * 0.10, my + H * 0.085),
                 (mx - W * 0.10, my - H * 0.085)], ink, 3)
    for k in range(2):
        y = my - H * 0.03 + k * H * 0.05
        pen.line(d, [(mx - W * 0.065, y), (mx + W * 0.065, y)], ink, 1, alpha=160)
    person(d, pen, W * 0.22, H * 0.78, h=0.72, ink=ink, pose="point")
    person(d, pen, W * 0.78, H * 0.78, h=0.68, ink=ink, pose="point")
    pen.line(d, [(W * 0.30, H * 0.60), (mx - W * 0.11, H * 0.62)], ink, 2)
    pen.line(d, [(W * 0.70, H * 0.60), (mx + W * 0.11, H * 0.62)], ink, 2)
    pen.curve(d, (W * 0.36, H * 0.30), (W * 0.44, H * 0.20), (W * 0.56, H * 0.20), (W * 0.64, H * 0.30), ink, 2)
    pen.line(d, [(W * 0.64, H * 0.30), (W * 0.595, H * 0.265)], ink, 2)
    pen.line(d, [(W * 0.64, H * 0.30), (W * 0.615, H * 0.345)], ink, 2)
    pen.line(d, [(W * 0.12, H * 0.84), (W * 0.88, H * 0.84)], ink, 2)
DRAW = {
    "leaf": m_leaf, "sprout": m_sprout, "mountain": m_mountain, "window": m_window,
    "lamp": m_lamp, "book": m_book, "bird": m_bird, "cloud": m_cloud,
    "moon": m_moon, "ripple": m_ripple, "boat": m_boat, "pattern": m_pattern,
    "tea": m_tea, "bridge": m_bridge, "star": m_star, "home": m_home,
    # v2.0 场景母题
    "steps3": s_steps3, "desk": s_desk, "meeting": s_meeting, "interview": s_interview,
    "plant": s_plant, "blueprint": s_blueprint, "lab": s_lab, "checklist": s_checklist,
    "contract": s_contract, "scales": s_scales, "letter": s_letter, "archive": s_archive,
    "health": s_health, "family": s_family, "move": s_move, "handover": s_handover,
}


# ======================================================================
# 七、渲染出口
# ======================================================================
def render(motif, out=None, size=(1500, 820), style="fountain", palette="sepia",
           seed=None, roughness=1.0, bowing=1.0, grain=None, paper=True, blur=None,
           accent_pop=False):
    """渲染单个母题为 PIL Image。

    style    笔触（fountain/pencil/brush/marker/charcoal）
    palette  暖色墨（sepia/ochre/amber/terracotta/rosewood/olive/ink）
    seed     随机种子（同种子可复现）
    grain    纸纹颗粒强度（None=按笔触档案）
    paper    True=铺暖纸底（不透明），False=透明底
    """
    if motif not in DRAW:
        raise KeyError(f"未知母题 {motif}，可选：{', '.join(MOTIFS)}")
    if seed is None:
        seed = random.randint(1, 99999)
    W, H = size
    prof = STROKE_PROFILES.get(style, STROKE_PROFILES["fountain"])
    pal = PALETTES.get(palette, PALETTES["sepia"])
    ink = pal["ink"]
    g = prof["grain"] if grain is None else grain
    bl = prof["blur"] if blur is None else blur

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    pen = Pen(seed, scale=1.35 if W >= 1200 else 1.7, roughness=roughness, bowing=bowing,
              style=style, palette=palette)

    # 母题自带强调笔（副色）：让画面有主墨 + 一点暖强调
    DRAW[motif](d, W, H, pen, ink)
    if accent_pop and motif in ("moon", "star"):
        pen.circle(d, W * 0.5, H * 0.5, min(W, H) * 0.36, pal["accent"], 1, passes=1, alpha=36)

    img = apply_grain(img, g, seed=seed)
    if bl > 0:
        img = img.filter(ImageFilter.GaussianBlur(bl))
    if paper:
        img = apply_paper(img, pal["paper"], grain=0.06, seed=seed)
    if out:
        from pathlib import Path
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        img.save(out)
    return img


# ======================================================================
# 八、关键词选题与落位
# ======================================================================
def pick_motifs(text, n=3, seed=None, pool=None):
    """按关键词命中选题；场景母题权重 1.5（贴合内容的具象场景优先于抽象符号）"""
    rng = random.Random(seed)
    pool = pool or MOTIFS
    score = {m: 0.0 for m in pool}
    for m in pool:
        w = 1.5 if m in SCENES else 1.0
        for k in MOTIF_META[m]["kw"]:
            score[m] += text.count(k) * w
    ranked = sorted(pool, key=lambda m: (-score[m], rng.random()))
    picked = [m for m in ranked if score[m] > 0][:n]
    fallback = ["steps3", "desk", "plant", "checklist", "leaf", "book"]
    while len(picked) < n:
        for m in fallback:
            if m not in picked and m in pool:
                picked.append(m)
                break
    return picked[:n]


def plan_roles(n):
    """落位规划：wide=跨栏大图 / inline=栏内浮图 / inline-end=靠后浮图"""
    if n <= 1:
        return ["wide"]
    if n == 2:
        return ["wide", "inline"]
    return ["wide", "inline", "inline-end"]


def size_for_role(role):
    return (1500, 820) if role == "wide" else (760, 980)


if __name__ == "__main__":
    print("qf-lineart 引擎库。母题：", ", ".join(MOTIFS))
    print("笔触：", ", ".join(f"{k}({v['cn']})" for k, v in STROKE_PROFILES.items()))
    print("配色：", ", ".join(f"{k}({v['cn']})" for k, v in PALETTES.items()))
    print("命令行入口：python lineart_cli.py --help")
