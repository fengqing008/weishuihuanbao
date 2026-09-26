# -*- coding: utf-8 -*-
"""report_render.py — 堪舆文化解读报告（Markdown 底稿 + HTML 基座渲染）

用法:
  python3 report_render.py --address "某市某区XX" --out 报告.html
  python3 report_render.py --lat 34.37 --lng 109.21 --deg 120 --out r.html
  python3 report_render.py --address "..." --offline-demo --no-base
"""
import os
import sys
import json
import argparse
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
ASSETS = os.path.join(BASE, "assets")
sys.path.insert(0, SCRIPTS)
import luopan as lp  # noqa: E402
import geo_analyze as ga  # noqa: E402

NOTICE = "本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。"


def load(fn):
    with open(os.path.join(ASSETS, fn), encoding="utf-8") as f:
        return json.load(f)


def build_md(center, radius, groups, six, tips, shan=None, bagua=None):
    shan_d = load("24shan.json")
    sixi = load("sixiang.json")
    shas = load("shas.json")
    cls = load("classics.json")
    L = []
    L.append("# 堪舆文化解读报告")
    L.append("")
    L.append("> 点位：%s　检索半径：%d 米" % (center["addr"], radius))
    L.append("")

    # 一
    L.append("## 一、点位与环境概览")
    L.append("")
    L.append(":::kpi")
    L.append("命中要素|%d|处|半径 %d 米内" % (sum(len(v) for v in groups.values()), radius))
    L.append("要素类属|%d|类|水体/道路/建筑/文教/医疗/宗教" % len(groups))
    L.append("四神方位|4|方|玄武/朱雀/青龙/白虎")
    L.append("民俗提示|%d|条|传统形煞条目" % len(tips))
    L.append(":::")
    L.append("")
    L.append("堪舆（风水）是中国传统建筑环境文化的重要组成部分，其核心命题见于《葬书》——「葬者，乘生气也。气乘风则散，界水则止」，"
             "讲究「藏风得水」。它并非单纯的吉凶之术，而是一套古人对地形、水流、方位与居住关系的系统观察与经验表达。"
             "本报告把所查点位的周边环境要素，按传统四神砂格局与形煞民俗逐一对应呈现，供了解这套文化的实际样貌，不作吉凶判断。"
             "报告所依据的四神砂、形煞与二十四山等名目，均出自公有领域典籍与民俗整理；所引典籍原文一律保留原貌，其观点属古人认识，"
             "不代表本报告的立场。读者可视其为一份传统环境观的对照材料。")
    L.append("")

    # 二
    L.append("## 二、周边环境要素")
    L.append("")
    if not groups:
        L.append("本点位周边在给定半径内未检索到明显要素。可增大检索半径，或以更具体的地标名称重新查询。"
                 "环境要素是形势派堪舆的观察起点，古人所谓「山外拱而内逼者，穴必尊；水口低而山高者，地必贵」，"
                 "正是从山水形势的实际观察出发的。")
        L.append("")
    for grp, hits in groups.items():
        L.append("### （%s）" % grp)
        L.append("")
        for p in hits:
            L.append("- **%s**（方位 %s，约 %d 米）" % (p["name"], p["dir"], p["dist"]))
        L.append("")
    if groups:
        L.append("古人观察环境，首重「龙、穴、砂、水、向」五要——《地理五诀》概括为「龙要生旺，穴要的实，砂要环抱，水要朝聚，向要迎纳」。"
                 "其中「砂」指周边山体与建筑，「水」指河流湖泊与道路（道路在古代堪舆中亦作「水」看）。"
                 "上表所列要素，正是现代环境中可与「砂」「水」相对应者。")
        L.append("")

    # 三
    L.append("## 三、四神砂格局参照")
    L.append("")
    L.append("![四神砂方位示意](images/sixiang.svg){wide}")
    L.append("")
    L.append("*图 1　四神砂方位示意　·　依《葬书》四神砂之说程序化绘制，为方位关系的文化图解*")
    L.append("")
    L.append("四神砂出自《葬书》「玄武垂头，朱雀翔舞，青龙蜿蜒，白虎驯俯」，是堪舆对理想环境四面形势的经典描述：")
    L.append("")
    for s in sixi["sixiang"]:
        L.append("- **%s**（%s·%s）：%s" % (s["name"], s["position"], s["role"], s["classic"]))
    L.append("")
    L.append("对照本次点位：")
    L.append("")
    for name, d, desc in six:
        L.append("- **%s**（%s）：%s" % (name, d, desc))
    L.append("")
    L.append("需要说明的是，四神砂描述的是一种理想化的空间意象——后有靠、前开阔、左右环抱。"
             "落到现代城市环境中，楼宇、道路与绿地取代了山体与河流，其精神仍是对空间层次与围合感的要求，"
             "属于古人的环境审美经验，而非可预测吉凶的公式。")
    L.append("")

    # 四
    L.append("## 四、传统形煞文化解读")
    L.append("")
    if not tips:
        L.append("本次点位未触发传统形煞条目。传统形煞名目繁多，其共同点是把某些空间形态（直冲、反弓、尖射、逼压）形象化为「煞」，"
                 "并借形取象地赋予其含义。了解这些名目，有助于读懂古人的环境感知方式。")
        L.append("")
    for name, ev, cu in tips:
        L.append("### （%s）" % name)
        L.append("")
        L.append("**观察**：%s" % ev)
        L.append("")
        L.append("**文化解读**：%s" % cu)
        L.append("")
    if tips:
        L.append("形煞之说贵在「见形取义」。古人把空间的直与曲、高与低、远与近，转译为生活的安稳与不安，"
                 "其中不少关切（如临水的地基、临路的噪声、头顶的压迫感）在今天仍有其朴素的合理内核。"
                 "把它当作古人环境经验的记录来读，比当作吉凶判决来用更有价值。")
        L.append("")

    # 五
    L.append("## 五、二十四山与坐向参考")
    L.append("")
    L.append("![二十四山罗盘示意](images/luopan24.svg){wide}")
    L.append("")
    L.append("*图 2　二十四山罗盘示意　·　依传统罗盘二十四山与后天八卦方位程序化绘制，含四正即子午卯酉*")
    L.append("")
    if shan and bagua:
        L.append("按给定度数 %g° 定位，属 **%s** 山（%s 宫，五行 %s）。二十四山由八天干、十二地支与四维组成，"
                 "每山占 15°，是传统罗盘定位的基本刻度。" % (shan["center"], shan["name"], shan["bagua"], shan["wuxing"]))
        L.append("")
        L.append(":::kpi")
        L.append("坐山|%s|—|%s宫" % (shan["name"], shan["bagua"]))
        L.append("中心度数|%d|°|辖 %.1f°—%.1f°" % (shan["center"], (shan["center"] - 7.5) % 360, (shan["center"] + 7.5) % 360))
        L.append("五行|%s|—|%s" % (shan["wuxing"], shan["type"]))
        L.append("所属卦|%s|—|%s" % (bagua["name"], bagua["direction"]))
        L.append(":::")
        L.append("")
        L.append("**说明**：%s" % shan["note"])
        L.append("")
    else:
        L.append("二十四山是传统罗盘的基本刻度，由八天干（甲乙丙丁庚辛壬癸）、十二地支（子丑寅卯辰巳午未申酉戌亥）"
                 "与四维（乾坤艮巽）组成，共二十四山，每山占 15°。其中子为正北、午为正南、卯为正东、酉为正西。"
                 "八宫各辖三山，如坎宫辖壬子癸、巽宫辖辰巽巳。")
        L.append("")
        L.append("用脚本可按度数定山：`python3 scripts/luopan.py --deg 120`。本次未给定度数，故不作定位。"
                 "若要定位坐向，可量取宅门或主窗的朝向度数（正北为 0°，顺时针递增），再按山定宫查阅。")
        L.append("")

    # 六
    L.append("## 六、堪舆典籍与文化背景")
    L.append("")
    L.append("堪舆学有清晰的知识谱系。形法一脉以《葬书》为祖，提出「藏风得水」与四神砂；唐代杨筠松《撼龙经》《疑龙经》专论龙脉，"
             "专看山水形势；宋代卜应天《雪心赋》系统总结形势观察；清代赵九峰《地理五诀》归为「龙穴砂水向」五要，"
             "《阳宅三要》则把住宅堪舆聚焦于「门、主、灶」。理气一脉则有《青囊经》等论阴阳方位配合。相关典籍条目示例：")
    L.append("")
    for c in cls["classics"][:10]:
        L.append("- **%s**（%s）：%s —— %s" % (c["book"], c["entry"], c["text"], c["note"]))
    L.append("")
    L.append("从这些典籍可以看出，堪舆学在历史上的展开有其内在脉络：从《葬书》提出纲领，到唐宋形势派专精于山水观察，"
             "再到明清把经验归纳为可操作的条目，它始终围绕着人与环境的相处方式。其中关于择高避湿、背风向阳、近水利而不受水患的经验，"
             "与今日的选址常识多有相通之处；而附会于其上的吉凶之说，则属特定时代的观念产物，宜分别看待。")

    # 七
    L.append("## 七、说明与免责")
    L.append("")
    L.append("1. 本报告的全部内容属中国传统文化研究范畴，整理自公有领域的堪舆典籍与民俗资料，供文化了解与民俗参考。")
    L.append("2. 报告不构成任何决策依据，不涉及购房、选址、投资、医疗或法律判断；相关需要请咨询对应专业人士。")
    L.append("3. 传统堪舆存在多种流派与相异说法，本报告取主流的形势派视角，并明示其属古人认识。")
    L.append("4. 形煞与四神砂条目均作文化描述，不作吉凶断言，读者可视为了解传统环境观的一个窗口。")
    L.append("5. 报告中涉及位置信息仅用于环境要素的方位比对与传统文化对照，不用于其他用途。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("> %s" % NOTICE)
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="堪舆文化解读报告生成")
    ap.add_argument("--address", default="")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lng", type=float)
    ap.add_argument("--deg", type=float, help="坐向度数（可选）")
    ap.add_argument("--radius", type=int, default=1000)
    ap.add_argument("--out", default="堪舆文化解读报告.html")
    ap.add_argument("--md", default="")
    ap.add_argument("--theme", default="forest")
    ap.add_argument("--motif", default="editorial")
    ap.add_argument("--offline-demo", action="store_true")
    ap.add_argument("--no-base", action="store_true")
    ap.add_argument("--no-images", action="store_true", help="不生成配图")
    a = ap.parse_args()

    if a.offline_demo:
        center = {"lng": 109.214, "lat": 34.372, "addr": "离线演示点位"}
        pois = []
    elif a.lat is not None and a.lng is not None:
        center = {"lng": a.lng, "lat": a.lat, "addr": "坐标点位（%.4f, %.4f）" % (a.lat, a.lng)}
        pois = ga.around(a.lng, a.lat, [k for _, ks in ga.KW_GROUPS for k in ks], a.radius)
    elif a.address:
        g = ga.geocode(a.address)
        if not g:
            print("地理编码失败（检查 AMAP_KEY 或地址）。", file=sys.stderr)
            sys.exit(1)
        center = {"lng": g[0], "lat": g[1], "addr": g[2]}
        pois = ga.around(g[0], g[1], [k for _, ks in ga.KW_GROUPS for k in ks], a.radius)
    else:
        ap.error("请用 --address 或 --lat/--lng 指定地点")

    groups = ga.classify(pois)
    six = ga.sixiang_view(groups)
    tips = ga.shas_hint(groups)

    shan = bagua = None
    if a.deg is not None:
        sd = lp.load("24shan.json")
        shan = lp.shan_of_deg(sd["shan"], a.deg)
        bd = lp.load("bagua.json")
        bagua = [b for b in bd["bagua"] if b["name"] == shan["bagua"]][0]

    md = build_md(center, a.radius, groups, six, tips, shan, bagua)
    mdpath = a.md or (os.path.splitext(a.out)[0] + ".md")
    os.makedirs(os.path.dirname(os.path.abspath(mdpath)), exist_ok=True)
    with open(mdpath, "w", encoding="utf-8") as f:
        f.write(md)
    print("Markdown 底稿：%s" % mdpath)

    # 默认生成配图（示意图程序化绘制，落在 md 同目录的 images/）
    img_dir = os.path.join(os.path.dirname(os.path.abspath(mdpath)), "images")
    dg = os.path.join(SCRIPTS, "diagram.py")
    if os.path.exists(dg) and not a.no_images:
        subprocess.run([sys.executable, dg, "--outdir", img_dir], capture_output=True, text=True)
        n = len(os.listdir(img_dir)) if os.path.isdir(img_dir) else 0
        print("配图 %d 张已生成到 %s" % (n, img_dir))

    if a.no_base:
        print("已跳过基座渲染（--no-base）")
        return

    renderer = os.path.join(SCRIPTS, "htmlbase", "md2report.py")
    if not os.path.exists(renderer):
        print("基座渲染器缺失：%s" % renderer, file=sys.stderr)
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
