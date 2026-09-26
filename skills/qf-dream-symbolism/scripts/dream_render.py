# -*- coding: utf-8 -*-
"""dream_render.py — 梦象解读报告生成（Markdown 底稿 + HTML 基座渲染）

用法:
  python3 dream_render.py --text "梦见大蛇入怀，随后飞翔" --out 梦象报告.html
  python3 dream_render.py --file dream.txt --time "2026-09-26 12:30" --out r.html
  python3 dream_render.py --text "..." --no-base        # 仅出 Markdown 底稿
"""
import os
import sys
import json
import argparse
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
import dream_parse as dp  # noqa: E402
import gua_map as gm  # noqa: E402

NOTICE = "本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。"


def build_md(dream, items, gua=None):
    syms = dp.load()
    cats = sorted(set(i["symbol"]["category"] for i in items))
    L = []
    L.append("# 梦象解读报告")
    L.append("")
    L.append("> 梦境要点：%s" % "、".join(i["symbol"]["name"] for i in items))
    L.append("")

    # 一、概览
    L.append("## 一、梦境与意象概览")
    L.append("")
    L.append(":::kpi")
    L.append("识别意象|%d|项|按触发词最长优先匹配" % len(items))
    L.append("涉及类别|%d|类|传统解梦按物象归类" % len(cats))
    L.append("意象总库|%d|条|本技能收录的传统意象条目" % syms["count"])
    L.append("典籍依据|%d|部|公有领域梦文化典籍" % len(json.load(open(os.path.join(BASE, "assets", "classics.json"), encoding="utf-8"))["classics"]))
    L.append(":::")
    L.append("")
    L.append("中国传统的梦象解读，讲究「以象取意」——《梦林玄解》所谓「象者，像也，像其形，通其意，而吉凶可知矣」。"
             "本报告不做预言，而是把梦境拆解为可辨识的传统意象，逐一给出典籍出处、民俗解读与心理象征三层内容，"
             "供了解中国传统梦文化之用。识别到的意象共 %d 项，归入 %s 等类别。" % (len(items), "、".join(cats)))
    L.append("")
    L.append("![意象类别分布](images/symbol_cats.svg){wide}")
    L.append("")
    L.append("*图 1　意象类别分布　·　按本技能收录意象的分类统计程序化绘制，供了解传统意象的取材范围*")
    L.append("")

    # 二、逐意象
    L.append("## 二、逐意象详解")
    L.append("")
    for idx, it in enumerate(items, 1):
        s = it["symbol"]
        L.append("### （%d）%s" % (idx, s["name"]))
        L.append("")
        L.append("**类别**：%s　**识别依据**：文中出现「%s」" % (s["category"], it["matched"]))
        L.append("")
        L.append("**典籍与民俗**：")
        for c in s["classics"]:
            L.append("- %s" % c)
        L.append("")
        L.append("**传统解读**：%s" % s["meaning"])
        L.append("")
        L.append("**心理象征**：%s" % s["psych"])
        L.append("")
    L.append("传统解梦并非一象一断，同一物象在不同典籍与情境中可有相反之解。例如「血」在民间多取财禄之象，「棺」取「官财」谐音，"
             "「哭」与「病」常作反兆之解，而「蛇」「水」则须视其状态与人之境遇而定。因此本报告并列呈现典籍原文与民俗解读，"
             "不作单一吉凶断言，读者可结合自身处境体会其中的文化意涵。")
    L.append("")

    # 三、心理象征
    L.append("## 三、意象的心理象征层")
    L.append("")
    L.append("除去民俗占断，传统意象在今日更宜作心理象征来读。水往往对应情绪与潜意识之流；坠落与奔跑多与失控、回避相关；"
             "考试与爬山反映被评价的压力与向上之志；房屋象征自我与安全感；棺材与死亡则常指向一个阶段的终结与转化。"
             "本次识别的意象中，其心理象征可归纳如下：")
    L.append("")
    for it in items:
        L.append("- **%s**：%s" % (it["symbol"]["name"], it["symbol"]["psych"]))
    L.append("")
    L.append("这一层读法源自《黄帝内经·灵枢》「淫邪发梦」的「梦为身之讯」传统，以及《列子》「昼想夜梦，神形所遇」之论，"
             "即梦是身心状态的映照，而非外来的吉凶符咒。把梦当镜子看，比把梦当签诗看，更接近古人论梦的理性一脉"
             "——东汉王充在《论衡》中即明言「人梦不能自知，觉悟乃知」，主张梦是自然现象。")
    L.append("")

    # 四、典籍
    L.append("## 四、典籍出处与文化背景")
    L.append("")
    L.append("![周礼六梦结构示意](images/sixdream.svg){wide}")
    L.append("")
    L.append("*图 2　《周礼》六梦结构示意　·　依《周礼·春官·占梦》所载六类分梦方式程序化绘制*")
    L.append("")
    cls = json.load(open(os.path.join(BASE, "assets", "classics.json"), encoding="utf-8"))["classics"]
    L.append("中国传统梦文化有清晰的知识谱系：《周礼·春官》设「占梦」之官，以六梦（正、噩、思、寤、喜、惧）分梦之吉凶，"
             "这是中国最早的梦的分类学；《庄子·齐物论》以「庄周梦蝶」质疑现实与自我的边界；《列子·周穆王》提出「昼想夜梦」；"
             "《黄帝内经》则从脏腑阴阳论梦的生理成因。其后，《敦煌梦书》代表唐代民间占梦的实态，《周公解梦》民间流传本成为最通俗的条目式文本，"
             "明代《梦林玄解》《占梦逸旨》则对梦的成因与方法做了系统总结。相关典籍条目示例：")
    L.append("")
    for c in cls[:10]:
        L.append("- **%s**（%s）：%s —— %s" % (c["book"], c["entry"], c["text"], c["note"]))
    L.append("")
    L.append("需要说明的是，《周公解梦》系托名之作，版本繁杂，本技能所采为其民间流传条目的公有领域内容，并辅以敦煌梦书等出土文献，"
             "力求还原民间梦文化的实际面貌，而非提供某种「标准答案」。")
    L.append("")

    # 五、卦象（可选）
    if gua:
        L.append("## 五、易经卦象参照")
        L.append("")
        L.append("作为传统文化中另一条解读脉络，易经六十四卦亦可作为观照梦境的参照系。此处按时间起卦（梅花易数法）所得：")
        L.append("")
        L.append(":::kpi")
        L.append("上卦|%s|—|起卦所得" % gua["up"])
        L.append("下卦|%s|—|起卦所得" % gua["low"])
        L.append("动爻|第%d爻|—|以时数推得" % gua["move"])
        L.append("本卦|%s|—|%s" % (gua["gua"]["name"], gua["gua"]["xiang"]))
        L.append(":::")
        L.append("")
        L.append("**卦辞**：%s" % gua["gua"]["ci"])
        L.append("")
        L.append("**象义**：%s" % gua["gua"]["symbol"])
        L.append("")
        L.append("按起卦之法，上卦以年月日之数取，下卦并时辰之数取，动爻以总数为六所除之余定。所得本卦为「%s」，"
                 "第 %d 爻为动爻。传统上，本卦示当下之势，动爻指所主之位，参看动爻可以体会变动所在。"
                 "此处仅作文化参照，与梦境意象互为印证，不作占断依据。" % (gua["gua"]["name"], gua["move"]))
        L.append("")

    # 六、综合
    L.append("## 六、综合文化解读")
    L.append("")
    L.append("把上述意象连起来看，本次梦境的主线可概括为：%s。" % " → ".join(i["symbol"]["name"] for i in items))
    L.append("")
    L.append("在传统梦文化的语境里，梦是「神魂预吉凶」的民俗想象，也是「昼想夜梦」的身心映照。两种理解并行不悖："
             "前者让我们看到古人对命运的关切与想象，后者让我们看到梦境与日常心绪的真实联结。"
             "解读梦象的价值，不在于预知祸福，而在于借由这些流传千年的意象，观照自身当下的处境与心境——"
             "这正是中国传统梦文化最值得了解的部分。")
    L.append("")
    L.append("若希望对某一意象或某一卦作更细的了解，可分别检索意象库与六十四卦库；"
             "也可记录梦境，观察同类意象在一段时间内的重复出现，这本身就是一种有趣的文化与自我观察实践。")
    L.append("")

    # 七、说明
    L.append("## 七、说明与免责")
    L.append("")
    L.append("1. 本报告的全部内容属中国传统文化研究范畴，整理自公有领域的梦文化典籍与民俗资料，供文化了解与民俗参考。")
    L.append("2. 报告不构成任何决策依据，不涉及医疗、心理诊断、投资、婚恋或法律判断；如有相关需要，请咨询对应专业人士。")
    L.append("3. 传统解梦存在多解与反兆（如「梦哭主喜」「见棺主官财」），本报告并列呈现，不作单一断言。")
    L.append("4. 引用典籍原文时保留原貌，其观点属古人认识，不代表本报告的立场。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("> %s" % NOTICE)
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="梦象解读报告生成")
    ap.add_argument("--text", default="", help="梦境描述")
    ap.add_argument("--file", default="", help="梦境描述文件")
    ap.add_argument("--time", default="", help="时间起卦，如 '2026-09-26 12:30'")
    ap.add_argument("--out", default="梦象解读报告.html", help="输出 HTML")
    ap.add_argument("--md", default="", help="同时保存 Markdown 底稿")
    ap.add_argument("--theme", default="galaxy", help="基座主题")
    ap.add_argument("--motif", default="editorial", help="基座版式母题")
    ap.add_argument("--no-base", action="store_true", help="仅出 Markdown 底稿")
    ap.add_argument("--no-images", action="store_true", help="不生成配图")
    a = ap.parse_args()

    dream = a.text
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            dream = f.read()
    if not dream.strip():
        ap.error("请用 --text 或 --file 提供梦境描述")

    syms = dp.load()
    items = dp.match(dream, syms)
    if not items:
        print("未从描述中识别到传统意象，请提供更具体的物象（如 蛇、水、飞、牙、考试 等）。", file=sys.stderr)
        sys.exit(1)

    gua = None
    if a.time:
        from datetime import datetime
        dt = datetime.strptime(a.time.strip(), "%Y-%m-%d %H:%M")
        up, low, move = gm.cast_from_time(dt)
        gname = gm.TABLE[(up, low)]
        g = gm.by_name(gm.load(), gname)
        gua = {"up": up, "low": low, "move": move, "gua": g}

    md = build_md(dream, items, gua)

    mdpath = a.md or (os.path.splitext(a.out)[0] + ".md")
    os.makedirs(os.path.dirname(os.path.abspath(mdpath)), exist_ok=True)
    with open(mdpath, "w", encoding="utf-8") as f:
        f.write(md)
    print("Markdown 底稿：%s" % mdpath)

    # 默认生成配图（示意图程序化绘制，落在 md 同目录的 images/）
    img_dir = os.path.join(os.path.dirname(os.path.abspath(mdpath)), "images")
    dg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagram.py")
    if os.path.exists(dg) and not a.no_images:
        subprocess.run([sys.executable, dg, "--outdir", img_dir], capture_output=True, text=True)
        n = len(os.listdir(img_dir)) if os.path.isdir(img_dir) else 0
        print("配图 %d 张已生成到 %s" % (n, img_dir))

    if a.no_base:
        print("已跳过基座渲染（--no-base）")
        return

    renderer = os.path.join(SCRIPTS, "htmlbase", "md2report.py")
    if not os.path.exists(renderer):
        print("基座渲染器缺失：%s（可加 --no-base 仅出底稿）" % renderer, file=sys.stderr)
        sys.exit(2)
    cmd = [sys.executable, renderer, mdpath, "-o", a.out, "--theme", a.theme, "--motif", a.motif, "--check"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode == 0:
        print("HTML 已生成：%s" % a.out)
    else:
        print("基座渲染失败（退出码 %d）" % r.returncode, file=sys.stderr)
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
