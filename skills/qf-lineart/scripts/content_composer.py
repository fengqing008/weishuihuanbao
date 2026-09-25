#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qf-lineart · 文意构思器（核心框架 → 画面任务单）

补上「读文 → 出图」之间原先由人工完成的一步，且比"取关键词选题"多走一层：
先提文章的核心内容与核心框架，再据此构思画面，使配图从文章里长出来。

三步链分工：
    text_brief.py       正文 → 素材底稿（物象/场景段/基调）     只提素材，不做构思
    content_composer.py 正文 → 核心框架 + 画面任务单（本脚本） 提框架 + 构思画面
    prompt_builder.py   任务单 → 标准提示词；lineart_cli.py 程序化兜底出图

核心框架（core frame）四件：一句话主旨 / 结构框架 / 分节要点 / 核心意象。
画面任务由框架派生，各司其职：
    论点句 → 主旨      （短、含判断词，如"反对不是目的，把事办对才是"）
    叙事句 → wide 画面 （有场景、有动作、有物件，如"会前做功课、会后提交书面意见"）
    物象句 → inline 图 （可特写的静物，如"一支签字笔"）

输出两件：
    core_frame.md        核心框架卡
    art_brief_auto.json  画面任务单（wide / inline 两条，字段合 references/art-brief-guide.md）

用法：
    python3 content_composer.py --file src_52.md -o brief.json --frame-out core_frame.md
    python3 content_composer.py --manifest book.json --outdir briefs --palette sepia --style pencil
    python3 content_composer.py --text "竣工验收这半年" -o brief.json
"""
import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import lineart_engine as E
except Exception:
    E = None

NEGATIVE = "不得出现任何文字、字母、数字、logo、水印。"

# —— 2–4 字 n-gram 停用片段（虚词组合，不作关键词）——
STOP_GRAMS = {
    "的时", "时候", "了的", "是一", "在这", "这个", "那个", "我们", "你们", "他们", "她们",
    "什么", "怎么", "如果", "但是", "所以", "因为", "而且", "就是", "还是", "这样", "那样",
    "这种", "那种", "一个", "一种", "一段", "一些", "可以", "不能", "没有", "已经", "自己",
    "这些", "那些", "不是", "不会", "其实", "只是", "而是", "或者", "以及", "对于", "关于",
    "通过", "进行", "很多", "以后", "之前", "之后", "在于", "一样", "事情", "东西", "地方",
    "情况", "方面", "有点", "一点", "一直", "一定", "为了", "来说", "来看", "起来", "出来",
    "过来", "下去", "上来", "的话", "想清", "选对", "越大", "件事", "那些", "这年",
}
FUNC_CHARS = set("的是在我也你他她它的了和与及或就都还而但等对从到把被为以后前中上下这那一不没会有能可要很才又多")

# —— 结构框架识别规则（关键词命中数 × 权重决胜）——
FRAME_RULES = [
    ("问题—对策型", ["为什么", "怎么办", "如何", "怎么", "坑", "误区", "大忌", "忌讳", "别把"], 1.0),
    ("并列要点型", ["一是", "二是", "三是", "四是", "其一", "其二", "第一", "第二", "第三"], 1.1),
    ("递进论证型", ["因为", "由于", "所以", "因此", "据此", "因而", "既然", "可见"], 1.0),
    ("叙事时间线", ["有一次", "那次", "那天", "后来", "当年", "当时", "那年"], 1.2),
]

# —— 叙事片段标记（最可入画的句子常出自这些）——
NARRATIVE_MARKS = [
    "有一次", "那次", "那天", "后来", "当场", "会上", "会前", "会后", "当时", "那年",
    "第一次", "记得", "站上", "走进", "坐在", "盯着", "翻出", "摊开", "递", "签", "整理成", "提交",
]

# —— 论点句标记（用作主旨）——
THESIS_MARKS = ["不是", "才是", "要", "应", "在于", "重在", "关键", "底线", "原则", "说到底"]

# —— 图解式词（红线2：不得把主题直译成符号）——
DIAGRAM_WORDS = ["箭头", "台阶", "天平", "齿轮", "象征", "寓意", "代表", "意味着"]

# —— 事务词（抽象，用于 wide 主体与关键词，不作特写）——
ABSTRACT = [
    "书面意见", "异议函", "关联交易", "合规风险", "定价依据", "留痕",
    "台账", "清单", "图纸", "意见", "记录", "数据", "材料", "方案", "文件", "政策",
]

# —— 静物表（可特写的实体，长词优先命中；inline 只用本表）——
PHYSICAL = [
    "合同", "章程", "文书", "信纸", "信封", "印章", "签章",
    "签字笔", "铅笔", "笔", "文件夹", "档案盒", "档案柜", "笔记本", "卷尺", "直尺",
    "电脑", "显示器", "键盘", "台灯", "茶杯", "保温杯", "会议桌", "白板", "投影",
    "安全帽", "反光背心", "手套", "扳手", "阀门", "管道", "螺栓", "梯子",
    "池面", "水面", "水管", "压力表", "流量计", "化验台", "锥形瓶", "试管", "滴管",
    "天平", "量筒", "试剂瓶", "污泥", "滤纸", "试纸",
    "书", "窗", "窗台", "小路", "路灯", "台阶", "门槛", "院落", "饭盒", "碗",
]
OBJECTS = ABSTRACT + PHYSICAL

# —— 时间词（不作主体前缀，只入氛围）——
TIME_WORDS = {"会前", "会上", "会后", "深夜", "凌晨", "清晨", "黄昏", "傍晚"}

# —— 动作表（可入画）——
ACTIONS = [
    "打勾", "签字", "盖章", "翻阅", "摊开", "合上", "搁下", "递", "接过", "点头",
    "起身", "落座", "走向", "站着", "蹲下", "抬头", "低头", "看", "望向", "皱眉",
    "握手", "挥手", "拧开", "拧紧", "搬", "抬", "拉", "推", "敲", "测量", "记",
    "抄", "算", "划", "圈", "勾", "标", "清洗", "值守", "巡检", "等", "整理成", "提交",
]

# —— 场景表（能定氛围的场所与时间）——
SCENES = [
    "会议室", "办公室", "工位", "工地", "厂区", "车间", "池边", "泵房", "化验室", "走廊",
    "食堂", "宿舍", "车里", "路上", "门口", "窗边", "灯下", "深夜", "凌晨", "清晨",
    "黄昏", "傍晚", "会场", "评审会", "验收会", "股东会", "庭审", "现场", "值班室", "中控室", "会前", "会上",
]

MOODS = {
    "沉静": ["沉默", "静", "安静", "独自", "慢慢", "深夜", "灯下"],
    "笃定": ["坚持", "守住", "扎", "稳", "踏实", "底线", "扎实", "始终", "分寸"],
    "克制": ["分寸", "边界", "克制", "慎重", "衡量", "拿捏", "对事不对人", "对事"],
    "紧迫": ["赶", "催", "急", "时间紧", "节点"],
    "温润": ["家", "孩子", "妻", "父母", "老", "回忆", "少年", "当年"],
    "未定": ["迷茫", "选", "岔路", "不知道", "两难", "犹豫"],
    "郑重": ["正式", "书面", "提交", "留痕", "托付", "职责"],
}

# —— 动作 → 画面语言（只转写文中已出现的动作，不引入文中没有的元素）——
ACTION_RENDER = {
    "整理成": "在灯下把散开的纸页理齐、叠成一沓",
    "提交": "双手将一沓文书向前递出",
    "打勾": "捏笔在清单某一行落下一勾",
    "签字": "握笔在纸面落款处写下名字",
    "盖章": "抬手把印章压向纸面",
    "翻阅": "翻开一沓资料逐页查看",
    "摊开": "把一份文书在桌面上摊平",
    "接过": "抬手接住递来的一份文书",
    "测量": "俯身在设备前读取仪表数值",
    "记录": "低头在记录本上落字",
    "记": "低头在记录本上落字",
    "算": "在纸面一列数字间比划核对",
    "标注": "在纸面一列数字间比划核对",
    "勾": "捏笔在清单某一行落下一勾",
    "看": "侧过身看向桌面的一叠材料",
    "等": "站在门口，手里攥着一份材料",
}

# —— 基调 → 光与留白（氛围层，不涉具体元素）——
MOOD_LIGHT = {
    "沉静": "灯下寂静，桌面干净，窗外一抹夜色",
    "笃定": "光线平稳，物件各安其位，纸页压得平实",
    "克制": "桌面留白很多，物件少而齐整，一道安静的侧光",
    "郑重": "一道侧光落在纸面，边角干净",
    "温润": "暖光落在桌角，空气里有一点松弛",
    "紧迫": "灯光偏冷，纸页翻得起了角",
    "未定": "光色偏淡，桌面物件疏落",
}

# —— 时间词 → 画面短语 ——
TIME_PHRASE = {
    "会前": "这时会议尚未开始", "会上": "会场上人已坐定", "会后": "散会之后",
    "深夜": "夜深", "凌晨": "天色未亮", "清晨": "天刚亮",
    "黄昏": "日头偏西", "傍晚": "天将暗",
}

LEN_BONUS = {2: 1.0, 3: 1.25, 4: 1.35}
SENT_SPLIT = re.compile(r"(?<=[。！？；!?;])")
CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
MD_MARK = re.compile(r"^\s{0,3}#{1,6}\s*|^\s*[-*+]\s+|^\s*\d+[.、]\s+|[`*>\[\]*#]")
HEAD_NUM = re.compile(r"^\s*(第?[一二三四五六七八九十]+[、.)）]|[（(][一二三四五六七八九十1-9][）)]|\d+[.、])\s*")


# ======================================================================
# 一、文本清洗与切分
# ======================================================================
def clean_line(t: str) -> str:
    t = re.sub(r"（江江手记[^）]*）", "", t)
    return MD_MARK.sub("", t).strip()


def guess_title(name: str) -> str:
    s = re.sub(r"\.\w+$", "", name)
    s = re.sub(r"^src_\d+[-_]\s*", "", s)
    s = re.sub(r"^\d+[-–、]\s*", "", s)
    return s.strip()


def doc_title_of(text: str, fallback: str) -> str:
    for raw in text.split("\n"):
        if raw.lstrip().startswith("# "):
            t = clean_line(raw)
            if t:
                return t
    return fallback


def paragraphs(text: str):
    out = []
    for raw in text.split("\n"):
        s = clean_line(raw)
        if len(s) < 6:
            continue
        out.append({"idx": len(out) + 1, "heading": raw.lstrip().startswith("#"),
                    "num_head": bool(HEAD_NUM.match(s)), "text": s})
    return out


def sentences_of(paras):
    out = []
    for p in paras:
        for s in SENT_SPLIT.split(p["text"]):
            s = s.strip()
            if len(s) >= 8:
                out.append({"para": p["idx"], "heading": p["heading"], "text": s})
    return out


def ngrams(run: str, lo=2, hi=4):
    L = len(run)
    for n in range(lo, hi + 1):
        if L < n:
            continue
        for i in range(L - n + 1):
            yield run[i:i + n]


def is_noise(g: str) -> bool:
    if g in STOP_GRAMS:
        return True
    if any(c in "这那其此该哪" for c in g):
        return True
    if re.search(r"(.)\1", g):
        return True
    return sum(1 for c in g if c in FUNC_CHARS) / len(g) >= 0.5


def overlap(a: str, b: str) -> int:
    """最长公共连续子串长度（用于淘汰滑窗产生的近重复词）。"""
    best = 0
    for i in range(len(a)):
        for j in range(1, len(a) - i + 1):
            if a[i:i + j] in b:
                best = max(best, j)
    return best


# ======================================================================
# 二、核心框架提取
# ======================================================================
def extract_keywords(sents, title, top=12, min_freq=2):
    freq = Counter()
    for s in sents:
        seen = set()
        for run in CJK_RUN.findall(s["text"]):
            for g in ngrams(run):
                if g in seen or is_noise(g):
                    continue
                freq[g] += 1
                seen.add(g)
    for run in CJK_RUN.findall(title):
        for g in ngrams(run):
            if not is_noise(g):
                freq[g] += 1
    scored = {g: c * LEN_BONUS[len(g)] for g, c in freq.items() if c >= min_freq}
    if not scored:
        scored = {g: c * LEN_BONUS[len(g)] for g, c in freq.items()}
    items = sorted(scored.items(), key=lambda x: -x[1])
    picked = []
    for g, sc in items:
        if any(g in o or overlap(g, o) >= 3 for o in picked):
            continue
        picked.append(g)
        if len(picked) >= top:
            break
    return picked, scored


def score_sent(s, kw_w):
    return sum(w for k, w in kw_w.items() if k in s["text"][:90])


def pick_thesis(core, text):
    """主旨句：短、含判断词、权重高。"""
    cands = [s for s in core if len(s["text"]) <= 46 and any(m in s["text"] for m in THESIS_MARKS)]
    if cands:
        cands.sort(key=lambda s: (-score_sent(s, _W[0]), len(s["text"])))
        return cands[0]["text"]
    if core:
        return min(core, key=lambda s: len(s["text"]))["text"]
    return text.strip()[:60]


_W = [{}]  # 承载当前 kw 权重（供 pick_thesis 复用，避免多层传参）


def section_gists(paras, kw_w, doc_title):
    secs, cur = [], None
    for p in paras:
        if p["heading"] and not (p is paras[0] and not p["num_head"]):
            cur = {"heading": HEAD_NUM.sub("", p["text"]).strip(), "paras": []}
            secs.append(cur)
        elif cur is not None:
            cur["paras"].append(p)
    for s in secs:
        best, bsc = "", -1.0
        for p in s["paras"]:
            for sent in SENT_SPLIT.split(p["text"]):
                sent = sent.strip()
                if len(sent) < 8:
                    continue
                sc = sum(w for k, w in kw_w.items() if k in sent)
                if sc > bsc:
                    best, bsc = sent, sc
        s["gist"] = best
    if not secs:
        return [{"heading": doc_title, "gist": "", "paras": []}]
    return secs


def detect_frame(paras, text):
    corpus = "\n".join(p["text"] for p in paras)
    score = {n: sum(corpus.count(k) for k in kws) * w for n, kws, w in FRAME_RULES}
    best = max(score, key=score.get) if score else ""
    if not best or score.get(best, 0) == 0:
        best = "总述展开型"
    return best, score


def build_frame(title, text):
    paras = paragraphs(text)
    sents = sentences_of(paras)
    kws, kw_w = extract_keywords(sents, title)
    core = sorted([s for s in sents if not s["heading"]], key=lambda s: -score_sent(s, kw_w))[:8]
    _W[0] = kw_w
    frame_type, frame_score = detect_frame(paras, text)
    doc_title = title or (paras[0]["text"] if paras else "")
    secs = section_gists(paras, kw_w, doc_title)
    points = [s["heading"] for s in secs if s["heading"]][:6] or [c["text"] for c in core[:5]]
    moods = [m for m, ws in MOODS.items() if any(k in text for k in ws)]
    return {
        "title": doc_title,
        "frame_type": frame_type,
        "frame_score": frame_score,
        "thesis": pick_thesis(core, text),
        "points": points,
        "sections": secs,
        "keywords": kws[:10],
        "moods": moods[:3],
        "paragraphs": paras,
        "sentences": sents,
        "core_sentences": core,
        "kw_weights": kw_w,
    }


# ======================================================================
# 三、画面构思（核心框架 → 两条任务）
# ======================================================================
def hits(s, table):
    return [x for x in table if x in s]


def best_hit(s, table):
    hs = hits(s, table)
    if not hs:
        return ""
    return sorted(hs, key=lambda x: (-len(x), -s.count(x)))[0]


def dedup(xs):
    out = []
    for x in sorted(xs, key=lambda s: -len(s)):
        if not any(x in o for o in out):
            out.append(x)
    return out


def render_scene(obj, act, scn, mood):
    """把文中已有的动作与物象转成可画的画面语言；氛围按基调补光，不引入文中没有的元素。"""
    seg = []
    if act:
        seg.append("一个人影" + ACTION_RENDER.get(act, act))
    elif obj:
        seg.append("画面上是一份" + obj)
    if scn:
        seg.append(TIME_PHRASE.get(scn, f"场景在{scn}"))
    seg.append(MOOD_LIGHT.get(mood.split("、")[0], "一道安静的侧光"))
    return "，".join(seg) + "。"


def narrative_score(s: str):
    return sum(1 for m in NARRATIVE_MARKS if m in s) * 3 + len(hits(s, OBJECTS)) * 2 + len(hits(s, ACTIONS))


def compose_wide(frame):
    kw_w = frame["kw_weights"]
    cands = [s for s in frame["sentences"] if not s["heading"]]
    best, best_sc = None, -1.0
    for s in cands:
        sc = narrative_score(s["text"]) * 1.5 + sum(w for k, w in kw_w.items() if k in s["text"][:60]) / 8.0
        if sc > best_sc:
            best, best_sc = s, sc
    if best is None:
        best = {"text": frame["thesis"], "para": 1}
    t = best["text"]
    obj = best_hit(t, OBJECTS)
    act = best_hit(t, ACTIONS)
    scn = best_hit(t, SCENES)
    place = "" if scn in TIME_WORDS else scn
    subject = f"{place}上的{obj}" if (place and obj) else (obj or scn or "一处现场")
    mood = "、".join(frame["moods"][:2]) or "克制"
    scene = render_scene(obj, act, scn, mood)
    return {
        "subject": subject,
        "scene": scene[:120],
        "composition": "横版 16:9，主体偏左，右侧大面积留白",
        "mood": mood,
        "elements": {"objects": dedup(hits(t, OBJECTS)), "actions": hits(t, ACTIONS), "scenes": hits(t, SCENES)},
        "evidence": f"p:{best['para']}｜{t[:44]}",
    }


def compose_inline(frame, wide):
    used = set(hits(wide["scene"], OBJECTS)) | {wide["subject"]}
    pool = [s for s in frame["core_sentences"] if s["text"][:14] not in wide["evidence"]]
    pool += [s for s in frame["sentences"] if s not in pool and not s["heading"]]
    best, best_obj, best_sc = None, "", -1.0
    for s in pool:
        objs = [o for o in hits(s["text"], PHYSICAL) if o not in used]
        if not objs:
            continue
        obj = sorted(objs, key=lambda x: -len(x))[0]
        sc = len(obj) + (2 if s["para"] != 1 else 0)
        if sc > best_sc:
            best, best_obj, best_sc = s, obj, sc
    if best is None:
        best, best_obj = {"text": frame["thesis"], "para": 1}, "信纸"
    return {
        "subject": f"{best_obj}（特写）",
        "scene": f"{best_obj}置于纸面横线之上，一角压住另一页，边缘留出大片空白，纸纹清晰",
        "composition": "竖版 3:4，主体偏下，上方留白",
        "mood": "郑重",
        "elements": {"objects": [best_obj], "actions": [], "scenes": []},
        "evidence": f"p:{best['para']}｜{best['text'][:44]}",
    }


def motif_for(text):
    """母题兜底：按 subject 与核心意象命中，单字词降权（避免"书"被"书面"误抬）。"""
    if E is None:
        return ""
    best, bs = "", 0.0
    for m in E.MOTIFS:
        w = 1.5 if m in E.SCENES else 1.0
        s = 0.0
        for k in E.MOTIF_META[m]["kw"]:
            c = text.count(k)
            if c:
                s += c * w * (1.0 if len(k) >= 2 else 0.45)
        if s > bs:
            best, bs = m, s
    return best


def self_check(wide, inline):
    blob = wide["scene"] + inline["scene"] + wide["subject"] + inline["subject"]
    return {
        "有出处": bool(wide["evidence"] and inline["evidence"]),
        "非图解": not any(w in blob for w in DIAGRAM_WORDS),
        "两图不重": wide["subject"] != inline["subject"],
        "可入画": bool(wide["subject"] and wide["elements"]["objects"]),
        "无字": True,
        "克制": "人工复核",
    }


def compose(text, title="", palette="sepia", style="pencil", order=None, column=""):
    frame = build_frame(title, text)
    wide = compose_wide(frame)
    inline = compose_inline(frame, wide)
    wide["motif"] = motif_for(" ".join([wide["subject"]] + frame["keywords"]))
    inline["motif"] = motif_for(" ".join([inline["subject"]] + frame["keywords"]))
    brief = {
        "order": order, "title": frame["title"], "column": column,
        "wide": wide, "inline": inline, "palette": palette, "style": style,
        "anchor": "kn:" + (frame["keywords"][0] if frame["keywords"] else "正文"),
        "core": {"frame_type": frame["frame_type"], "thesis": frame["thesis"],
                 "points": frame["points"], "keywords": frame["keywords"]},
        "checks": self_check(wide, inline),
    }
    return frame, brief


# ======================================================================
# 四、输出
# ======================================================================
def frame_md(frame, brief):
    L = [f"# 核心框架卡 · {frame['title']}", "",
         f"**结构框架**：{frame['frame_type']}", "",
         f"**一句话主旨**：{frame['thesis']}", "", "**结构骨架**："]
    secs = [s for s in frame.get("sections", []) if s.get("heading")]
    if secs:
        for i, s in enumerate(secs, 1):
            gist = f"　—　{s['gist'][:40]}" if s.get("gist") else ""
            L.append(f"{i}. {s['heading']}{gist}")
    else:
        for i, p in enumerate(frame["points"], 1):
            L.append(f"{i}. {p}")
    L += ["", "**核心意象**：" + "、".join(frame["keywords"]), "", "**画面落点**：",
          f"- wide：{brief['wide']['subject']} —— {brief['wide']['scene']}",
          f"  （出处 {brief['wide']['evidence']}；母题兜底 {brief['wide'].get('motif') or '—'}）",
          f"- inline：{brief['inline']['subject']} —— {brief['inline']['scene']}",
          f"  （出处 {brief['inline']['evidence']}；母题兜底 {brief['inline'].get('motif') or '—'}）",
          "", "**红线自检**：" + "  ".join(f"{k}={'✓' if v is True else v}" for k, v in brief["checks"].items()), ""]
    return "\n".join(L)


def one(text, title, args, outdir=None, order=None, column=""):
    frame, brief = compose(text, title=title, palette=args.palette, style=args.style,
                           order=order, column=column)
    stem = f"art{order}" if order is not None else (re.sub(r"[^\w\u4e00-\u9fff]", "", title)[:16] or "draft")
    base = Path(outdir) if outdir else Path(".")
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{stem}_brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    (base / f"{stem}_frame.md").write_text(frame_md(frame, brief), encoding="utf-8")
    return frame, brief, stem, base


def main():
    ap = argparse.ArgumentParser(description="qf-lineart · 文意构思器（核心框架 → 画面任务单）")
    ap.add_argument("--file", help="单篇正文 md/txt")
    ap.add_argument("--text", help="直接给标题或短文本")
    ap.add_argument("--manifest", help="稿件清单 JSON（含 articles[]）")
    ap.add_argument("--outdir", help="批量输出目录")
    ap.add_argument("--palette", default="sepia")
    ap.add_argument("--style", default="pencil")
    ap.add_argument("-o", "--out", help="单篇任务单输出路径")
    ap.add_argument("--frame-out", help="单篇核心框架卡输出路径")
    a = ap.parse_args()

    if a.manifest:
        mf = Path(a.manifest)
        m = json.loads(mf.read_text(encoding="utf-8"))
        briefs = []
        for art in m.get("articles", []):
            f = mf.parent / art["body"]
            if not f.exists():
                continue
            frame, brief, _, _ = one(f.read_text(encoding="utf-8"), art.get("title", ""), a,
                                     outdir=a.outdir or "briefs", order=art.get("order"),
                                     column=art.get("column", ""))
            briefs.append(brief)
            print(f"OK #{art.get('order')} {art.get('title')} [{frame['frame_type']}]")
        out = Path(a.outdir or "briefs") / "art_brief_auto.json"
        out.write_text(json.dumps({"briefs": briefs}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"任务单 {out}  共 {len(briefs)} 篇")
        return 0

    if a.file:
        text = Path(a.file).read_text(encoding="utf-8", errors="ignore")
        title = doc_title_of(text, guess_title(Path(a.file).name))
        frame, brief, stem, base = one(text, title, a)
        if a.out:
            Path(a.out).write_text(json.dumps({"briefs": [brief]}, ensure_ascii=False, indent=2), encoding="utf-8")
        if a.frame_out:
            Path(a.frame_out).write_text(frame_md(frame, brief), encoding="utf-8")
        print(f"OK {stem}  框架={frame['frame_type']}")
        print(f"   主旨：{frame['thesis']}")
        print(f"   wide  ：{brief['wide']['subject']} | {brief['wide']['motif']}")
        print(f"   inline：{brief['inline']['subject']} | {brief['inline']['motif']}")
        return 0

    if a.text:
        frame, brief = compose(f"# {a.text}\n\n{a.text}", title=a.text, palette=a.palette, style=a.style)
        print(frame_md(frame, brief))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
