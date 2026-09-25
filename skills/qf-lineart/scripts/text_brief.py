#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qf-lineart · 文意提取器（读文 → 素材底稿）

为「文意提取」通道做第一步：把一篇正文拆成可用的画面素材底稿，
供人（或模型）在其中挑选插画中心点。本脚本只做提取，不做构思。

输出（brief_materials.json）每篇含：
    order/title/column  文章标识
    paragraphs          段落清单（已清 markdown 标记）
    scene_candidates    可视性最强的段落（含物件+动作/场景词）
    object_candidates   文中出现的可特写物象
    action_candidates   文中出现的可画动作
    mood_hint           基调提示词
    anchor_candidates   落位锚点候选（kn:关键词）

用法：
    python3 text_brief.py --src ./src --out brief_materials.json
    python3 text_brief.py --manifest manifest.json --out brief_materials.json
    python3 text_brief.py --file src_28-竣工验收这半年.md
"""
import argparse
import json
import re
import sys
from pathlib import Path

# —— 物象词表（可特写的实体，按场景域归类）——
OBJECTS = [
    # 办公 / 文书
    "台账", "清单", "图纸", "合同", "章程", "章程文书", "文书", "信纸", "信封", "印章", "签章",
    "笔", "签字笔", "铅笔", "卷尺", "直尺", "笔记本", "台账本", "文件夹", "档案盒", "档案柜",
    "电脑", "显示器", "键盘", "台灯", "茶杯", "保温杯", "纸杯", "会议桌", "白板", "投影",
    "台账表", "复写纸", "便签", "印章盒", "回形针", "订书机", "公文包", "资料袋", "U盘",
    # 工程 / 现场
    "安全帽", "反光背心", "工装", "手套", "扳手", "管钳", "阀门", "管道", "螺栓", "梯子",
    "脚手架", "塔吊", "搅拌车", "焊枪", "全站仪", "水准仪", "试块", "钢筋", "模板", "混凝土",
    "围挡", "警示锥", "电缆", "配电箱", "水泵", "风机", "格栅", "沉砂池", "沉淀池", "曝气池",
    "池面", "水面", "堰", "水管", "压力表", "流量计", "化验台", "锥形瓶", "试管", "滴管",
    "天平", "量筒", "试剂瓶", "显微镜", "污泥", "滤纸", "培养皿", "试纸", "比色管",
    # 生活 / 环境
    "台灯", "书", "窗", "窗台", "巷口", "小路", "路灯", "台阶", "门槛", "院落", "烟囱",
    "厂区", "车间", "食堂", "宿舍", "站台", "车轮", "方向盘", "行李", "饭盒", "碗", "锅",
    "雨伞", "外套", "篮球", "象棋", "扑克", "花盆", "菜市场", "快递盒",
]

# —— 动作词表（可入画的动作）——
ACTIONS = [
    "打勾", "签字", "盖章", "翻阅", "摊开", "合上", "搁下", "放下", "递", "接过", "点头",
    "摇头", "起身", "落座", "走向", "走进", "走出", "站着", "蹲", "蹲下", "抬头", "低头",
    "盯", "看", "望向", "皱眉", "笑", "沉默", "争", "吵", "握手", "拍肩", "挥手", "拧开",
    "拧紧", "搬", "抬", "扛", "拉", "推", "拧", "敲", "敲击", "测量", "记", "抄", "算",
    "划", "圈", "勾", "标", "擦拭", "清洗", "值守", "巡检", "赶", "等", "坐着", "靠着",
]

# —— 场景词表（场所与时间，能定氛围）——
SCENES = [
    "会议室", "办公室", "工位", "工地", "厂区", "车间", "池边", "泵房", "化验室", "走廊",
    "楼道", "电梯", "食堂", "宿舍", "车里", "车上", "路上", "门口", "窗边", "灯下", "台灯下",
    "深夜", "凌晨", "清晨", "黄昏", "傍晚", "雨里", "雪里", "风里", "夏天", "冬天", "会场",
    "评审会", "验收会", "股东会", "庭审", "庭上", "约谈", "现场", "一线", "值班室", "中控室",
]

# —— 基调词 ——
MOODS = {
    "沉静": ["沉默", "静", "安静", "独自", "慢慢", "深夜", "灯下"],
    "笃定": ["坚持", "守住", "扎", "稳", "踏实", "底", "扎实"],
    "克制": ["分寸", "边界", "克制", "慎重", "衡量", "拿捏"],
    "紧迫": ["赶", "催", "急", "deadline", "时间紧", "节点"],
    "温润": ["家", "孩子", "妻", "父母", "老", "回忆", "少年", "当年"],
    "未定": ["迷茫", "选", "岔路", "不知道", "两难", "犹豫"],
}

SENT_SPLIT = re.compile(r"(?<=[。！？；])")
MD_CLEAN = re.compile(r"^\s{0,3}#{1,6}\s*|^\s*[-*+]\s+|^\s*\d+\.\s+|[*`>\[\]()]|（江江手记[^）]*）")


def clean_md(t: str) -> str:
    t = MD_CLEAN.sub("", t)
    return t.strip()


def paragraphs(path: Path):
    out = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").split("\n"):
        s = clean_md(raw)
        if len(s) >= 12 and not s.startswith("##"):
            out.append(s)
    return out


def score_para(p: str):
    objs = [o for o in OBJECTS if o in p]
    acts = [a for a in ACTIONS if a in p]
    scns = [s for s in SCENES if s in p]
    return len(objs) * 2 + len(acts) + len(scns), objs, acts, scns


def brief_of(order, title, column, file, paras):
    scored = []
    objs_all, acts_all = set(), set()
    for i, p in enumerate(paras, 1):
        s, objs, acts, scns = score_para(p)
        objs_all.update(objs)
        acts_all.update(acts)
        if s > 0:
            scored.append({"p": i, "score": s, "text": p})
    scored.sort(key=lambda x: -x["score"])
    moods = [m for m, kws in MOODS.items() if any(k in "\n".join(paras) for k in kws)]
    return {
        "order": order,
        "title": title,
        "column": column,
        "file": str(file),
        "paragraphs": paras,
        "scene_candidates": scored[:8],
        "object_candidates": sorted(objs_all)[:18],
        "action_candidates": sorted(acts_all)[:12],
        "mood_hint": moods[:3],
        "anchor_candidates": [f"kn:{o}" for o in sorted(objs_all)[:5]],
    }


def from_manifest(mf: Path):
    m = json.loads(mf.read_text(encoding="utf-8"))
    base = mf.parent
    out = []
    for a in m.get("articles", []):
        f = base / a["body"]
        if f.exists():
            out.append(brief_of(a.get("order"), a.get("title"), a.get("column"), f, paragraphs(f)))
    return out


def from_src(d: Path):
    out = []
    for f in sorted(d.glob("src_*.md")):
        n = re.match(r"src_(\d+)", f.name)
        title = re.sub(r"^src_\d+-|\.md$", "", f.name)
        out.append(brief_of(int(n.group(1)) if n else 0, title, "", f, paragraphs(f)))
    return out


def main():
    ap = argparse.ArgumentParser(description="文意提取器：正文 → 画面素材底稿")
    ap.add_argument("--src", help="正文目录（src_*.md）")
    ap.add_argument("--manifest", help="书目 manifest.json")
    ap.add_argument("--file", help="单篇正文")
    ap.add_argument("--out", default="brief_materials.json", help="输出 JSON")
    a = ap.parse_args()

    if a.manifest:
        data = from_manifest(Path(a.manifest))
    elif a.src:
        data = from_src(Path(a.src))
    elif a.file:
        f = Path(a.file); paras = paragraphs(f)
        data = [brief_of(0, f.stem, "", f, paras)]
    else:
        ap.print_help(); sys.exit(2)

    Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {a.out}  篇数={len(data)}")
    for d in data:
        print(f"  {d['order']:>3} {d['title'][:22]:22s} 候选段={len(d['scene_candidates'])} 物象={len(d['object_candidates'])} 基调={','.join(d['mood_hint'])}")


if __name__ == "__main__":
    main()
