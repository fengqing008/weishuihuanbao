#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装配姓氏溯源底稿并渲染 HTML 报告（HTML 基座 v9）。

用法：
  python3 scripts/report_render.py --surname 王 --out 王姓溯源.html
  python3 scripts/report_render.py --surname 王 --province 陕西 --city 西安 --out out.html
  python3 scripts/report_render.py --surname 王 --out out.html --no-base   # 强制简易模板

依赖：同技能 scripts/htmlbase/md2report.py（HTML 基座副本）。
"""
import argparse
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(BASE), "assets")
HTMLBASE = os.path.join(BASE, "htmlbase", "md2report.py")
sys.path.insert(0, BASE)

import surname_query  # noqa: E402
import pop_calc  # noqa: E402


def _fmt_pop(pop_wan):
    if not pop_wan:
        return None, None
    if pop_wan >= 10000:
        return "{:.2f}".format(pop_wan / 10000.0), "亿人"
    return "{:,.0f}".format(pop_wan), "万人"


def _origin_paragraph(surname, detail):
    if detail and detail.get("origins"):
        return ""
    types = [
        "以国为氏（以祖先受封的诸侯国名为姓）",
        "以邑为氏（以祖先受封的采邑、食邑为姓）",
        "以官为氏（以祖先所任官职为姓）",
        "以职业为氏（以祖先从事的职业或技艺为姓）",
        "以王父字或名为氏（以祖父的字、名为姓）",
        "赐姓与改姓（帝王赐姓、避讳避祸改姓、少数民族汉化改姓）",
    ]
    return (
        "中国姓氏的形成，大体可归为六类源流：{}。"
        "「{}」姓之具体归属，因支系众多、迁徙频繁，往往一姓多源，"
        "须以《中国姓氏大辞典》等权威辞书及各地族谱为准，不可仅凭单一说法。"
        "姓氏既是血缘的标记，也是历史上族群迁徙与融合的活化石；"
        "今日同一姓氏者，其远祖未必同源，天南地北的同姓人，根脉也可能各异。"
        "正因如此，寻根问祖须以严谨考据为据，避免张冠李戴、乱认祖宗。"
    ).format("；".join(types), surname)


def build_md(surname, province=None, city=None, scan_data=None):
    q = surname_query.query(surname)
    if q is None:
        print("【暂未收录】'{}'".format(surname), file=sys.stderr)
        sys.exit(2)

    pop = pop_calc.calc(surname, province)
    n = pop["national"]
    v_pop, u_pop = _fmt_pop(n.get("pop_wan"))

    L = []
    L.append("# {}姓溯源与人口分布".format(surname))
    L.append("")
    L.append(
        "本报告围绕「{}」姓，从全国排名与人口、源流考据、郡望堂号、迁徙分布四个层面展开，"
        "并结合省级归属与姓氏地名密度，呈现该姓在中华版图上的分布脉络。"
        "所引数据均注明来源，估算项予以标注，供文化了解与民俗参考。".format(surname)
    )
    L.append("")

    # ── 一、全国排名与人口 ─────────────────────────────
    L.append("## 一、全国排名与人口")
    poptxt = "约{:,}万人".format(n["pop_wan"]) if n.get("pop_wan") else "官方未公布逐姓人口"
    sharetxt = "，约占全国户籍人口{}".format(n["share"]) if n.get("share") else ""
    L.append(
        "据{}，按户籍人口数量排名，「{}」姓位居全国第{}位，{}{}。".format(
            n["source"], surname, n["rank"], poptxt, sharetxt
        )
    )
    L.append(
        "全国前100大姓合计约占户籍人口的85.9%，是名副其实的「百家姓」；"
        "而前十大姓即已占到全国人口的三成以上。这种高度集中的分布格局，"
        "是历史上大姓宗族在政治、经济与文化上长期积累的结果——"
        "望族累世为官、开枝散叶，小姓则在历次战乱与迁徙中被逐渐稀释。此外，赐姓、改姓与少数民族汉化，也不断为各大姓注入新的支流，使其血脉更为多元交融。"
    )
    L.append(
        "姓氏人口的多少，并不代表地位的高低。现代社会中，姓氏已回归为纯粹的血缘标识，"
        "所谓「赵钱孙李」的排序，只是统计意义上的先后，并无贵贱之别。了解姓氏人口规模，既能帮助理解大姓小姓的历史成因，也有助于体会中华姓氏「大分散、小聚居」的空间特征，进而感知人口与地域的深层关联，理解「一方水土养一方人」的人口学底蕴。"
    )
    L.append("")
    L.append(":::kpi")
    L.append("全国排名|{}|位|综合排名".format(n["rank"]))
    if v_pop:
        L.append("人口规模|{}|{}|官方约数".format(v_pop, u_pop))
    L.append("全国占比|{}|%|户籍人口".format((n.get("share") or "—").rstrip("%")))
    L.append(":::")
    L.append("")
    L.append("![姓氏人口排名示意](images/surname_rank.svg){wide}")
    L.append("")
    L.append("*图 1　全国前十姓人口与本姓排名　·　依公安部《全国姓名报告》与第七次全国人口普查数据程序化绘制，数字为约数*")
    L.append("")

    # ── 二、源流考据 ─────────────────────────────
    L.append("## 二、源流考据")
    if q.get("origin_summary"):
        L.append("**源流概述**：{}".format(q["origin_summary"]))
        L.append("")
        for o in q.get("origins", []):
            L.append("- {}".format(o))
        L.append("")
        L.append(
            "需要说明的是，姓氏源流在历史流传中往往一姓多源：既有主支的清晰脉络，"
            "也有旁支的融合与改造。上述源流为传统姓氏学的主流说法，"
            "不同族谱与地方志或有出入，宜相互参证。考据姓氏源流，须综合姓氏典籍、地方志、族谱与历史地理等多重证据，单一史料往往难以定论，这也是「同姓不同源」现象普遍的原因。姓氏之源，既是血缘之始，也是文化之根；了解源流，方能在浩如烟海的族谱与传说中，辨明主次、去伪存真，不被附会之说所惑。"
            "古人所谓「姓别婚姻、氏明贵贱」，先秦时姓与氏分而为二，"
            "秦汉以后姓氏合一，才逐步演化为今日之姓氏形态。"
        )
    else:
        L.append(_origin_paragraph(surname, None))
    L.append("")

    # ── 三、郡望与堂号 ─────────────────────────────
    L.append("## 三、郡望与堂号")
    if q.get("junwang"):
        L.append("**郡望**：{}。".format("、".join(q["junwang"])))
        L.append(
            "郡望指魏晋至隋唐时期该姓望族聚居之地，是门第的象征。"
            "魏晋实行九品中正制，门阀士族累世高官、垄断仕途，"
            "「郡望」遂成为标榜出身、区别高下的重要标识，"
            "如太原王氏、陇西李氏、清河张氏，皆为一世之望。"
        )
        L.append(
            "堂号则是宗族祠堂的名号，多取自先贤德业或发祥之地，"
            "用以昭示家风、凝聚宗亲，至今仍见于各地宗祠匾额与族谱卷首。"
            "郡望与堂号共同构成了中国传统宗族文化的重要标识。时至今日，海内外宗亲会多以郡望堂号为纽带，续修族谱、联络宗谊，成为中华文化凝聚力的生动体现；堂号之中，往往藏着一族的家训与荣光。"
        )
        L.append("")
        if q.get("tanghao"):
            for t in q["tanghao"]:
                L.append("- **{}**：{}".format(t["name"], t["story"]))
        L.append("")
        L.append(":::tags")
        L.append("、".join(q["junwang"]))
        L.append(":::")
    else:
        L.append(
            "郡望指魏晋至隋唐时期某姓望族聚居之地，是门第的象征；"
            "堂号则是宗族祠堂的名号，多取自先贤德业或发祥之地。"
            "魏晋南北朝时期，门阀士族以郡望相标榜，"
            "郡望与堂号共同构成了中国传统宗族文化的重要标识，"
            "至今仍见于各地宗祠匾额与族谱卷首。该姓具体郡望、堂号请以族谱为准。"
        )
    L.append("")

    # ── 四、迁徙与分布 ─────────────────────────────
    L.append("## 四、迁徙与分布")
    if q.get("migration"):
        L.append(q["migration"])
    else:
        L.append(
            "中国姓氏的分布格局，是数千年间多次大规模人口迁徙的结果。"
            "自西晋永嘉南渡、唐末黄巢之乱、两宋之际靖康南迁，到明清的「江西填湖广」「湖广填四川」，"
            "每一次迁徙都重塑了姓氏的地理版图。总体而言，北方多王、李、张、刘，"
            "南方多陈、黄、吴、林，长江流域则诸姓杂处。"
            "近代以来，随着工业化与城镇化推进，人口跨区域流动加剧，"
            "姓氏原有的地域标签正在弱化，大姓在全国范围内更加均衡。梳理一姓的分布，既能还原家族的迁徙轨迹，也能折射出区域开发、移民政策与人口流动的宏观历史。"
        )
    L.append("")
    L.append(
        "就研究方法而言，姓氏分布的还原依赖三类材料：一是正史与地方志中的移民记载，"
        "二是族谱所记的始迁祖与落籍地，三是当代户籍统计与人口普查数据。"
        "三者各有长短——文献长于叙述源流而疏于量化，谱牒详于一族而难以通观全局，"
        "统计数据精确却只有断面。把三者叠合起来看，才能对一姓的迁徙形成较为完整的认识。"
        "这也正是姓氏研究在历史学、人口学与社会学之间占据独特位置的原因。"
    )
    L.append("")

    # ── 五、本省与本地 ─────────────────────────────
    L.append("## 五、本省与本地分布")
    if pop.get("province"):
        p = pop["province"]
        if p.get("is_first_surname"):
            L.append("在**{}**，该姓为本省**第一大姓**（官方统计）。".format(p["name"]))
        else:
            L.append(
                "在**{}**，该姓非本省第一大姓，按全国占比估算约{:,}万人【估算值】。".format(
                    p["name"], p.get("est_pop_wan", 0)
                )
            )
        L.append(
            "省级分布反映了历史移民路线与现实人口流动的叠加："
            "北方省份多以大姓为第一大姓，南方省份则因历代南迁，"
            "形成了陈、黄、吴、林等姓的集中分布。这些格局的形成，与历史上的移民路线、开发次序密切相关。"
        )
    else:
        L.append("未指定省份；如需省级视角，请追加 --province 参数。")
    L.append("")
    if scan_data:
        L.append(
            "在**{}**范围内，共检索到以该姓命名的地名 **{}** 处。".format(
                scan_data.get("city", "本地"), scan_data.get("total_unique", 0)
            )
        )
        L.append(
            "中国传统村落常以主姓命名（如王村、李庄、张家湾），"
            "故姓氏地名密度可作为宗族聚居程度的侧面证据。以下为部分样例："
        )
        L.append("")
        for s in (scan_data.get("samples") or [])[:10]:
            L.append("- {}".format(s.get("name")))
    else:
        L.append(
            "地区级姓氏人口无官方逐县统计。可运行 scripts/place_scan.py，"
            "以「姓氏地名密度」（王村、李庄等）侧面反映本地宗族聚居程度；"
            "该项为侧面证据，不作人口数字断言。省级与地区级的分布差异，正是历史移民与现实流动共同作用的结果，值得细加体察与回味。"
        )
    L.append("")
    L.append(
        "需要说明的是，地区一级目前没有逐县逐姓的官方人口统计，任何精确到县区的姓氏人口数字都缺乏权威来源。"
        "本报告在这一层级采用姓氏地名密度作为侧面参照：以姓氏命名的自然村、行政村越多，"
        "通常说明该姓在当地聚居越早、越集中。这一方法有其限度——地名会因行政区划调整、"
        "村落合并或改名而变动，也可能出现同名不同源的情形，故只作趋势参考，不与人口数字混用。"
        "若需更细的本地情况，可结合地方志与族谱另行查考。"
    )
    L.append("")

    # ── 六、结语 ─────────────────────────────
    L.append("## 六、结语")
    L.append(
        "姓氏是一把打开家族记忆的钥匙。从「{}」姓的源流、郡望与分布中，"
        "我们读到的不只是一个符号，更是一部浓缩的迁徙史与融合史。"
        "中华姓氏源远流长，字字皆有来历，处处可溯根源。".format(surname)
    )
    L.append(
        "当代社会人口流动加剧，姓氏的地域标签正在弱化，"
        "但慎终追远、敬宗收族的文化传统，仍在一代代人的寻根问祖中延续。"
        "了解自己的姓氏，既是认识家族来路的途径，也是触摸中华文明脉络的窗口。愿每一位寻根者，都能在姓氏的脉络中，找到属于自己的文化坐标；姓氏文化，是中华文明绵延不绝的生动见证，值得每一代人珍视与传承。"
    )
    L.append("")
    L.append("> 本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")

    return "\n".join(L)


def base_available():
    return os.path.exists(HTMLBASE)


def render_with_base(md_text, out_path, theme, motif):
    tmp = out_path + ".src.md"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(md_text)
    cmd = [sys.executable, HTMLBASE, tmp, "-o", out_path,
           "--theme", theme, "--motif", motif, "--check"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp)
    if r.returncode != 0:
        print("[基座渲染警告] rc={}".format(r.returncode), file=sys.stderr)
        tail = (r.stdout or "")[-1200:]
        print(tail, file=sys.stderr)
    return r.returncode == 0


def render_fallback(md_text, out_path):
    import html as _h
    body = _h.escape(md_text)
    doc = (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>姓氏溯源</title><style>body{max-width:820px;margin:2rem auto;"
        "padding:0 1rem;font:16px/1.9 system-ui,'Noto Sans SC',sans-serif;color:#222}"
        "pre{white-space:pre-wrap}</style></head><body><pre>" + body + "</pre></body></html>"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


def main():
    ap = argparse.ArgumentParser(description="姓氏溯源 HTML 报告生成")
    ap.add_argument("--surname", required=True)
    ap.add_argument("--province")
    ap.add_argument("--city")
    ap.add_argument("--scan-json", help="place_scan.py 输出的 JSON 文件")
    ap.add_argument("--out", required=True, help="输出 HTML 路径")
    ap.add_argument("--theme", default="golden")
    ap.add_argument("--motif", default="editorial")
    ap.add_argument("--no-base", action="store_true", help="强制使用简易兜底模板")
    ap.add_argument("--no-images", action="store_true", help="不生成配图")
    args = ap.parse_args()

    scan_data = None
    if args.scan_json and os.path.exists(args.scan_json):
        with open(args.scan_json, encoding="utf-8") as f:
            scan_data = json.load(f)

    md_text = build_md(args.surname, args.province, args.city, scan_data)

    # 默认生成配图（示意图程序化绘制，落在输出同目录的 images/）
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    img_dir = os.path.join(out_dir, "images")
    dg = os.path.join(BASE, "diagram.py")
    if os.path.exists(dg) and not args.no_images:
        subprocess.run([sys.executable, dg, "--outdir", img_dir, "--surname", args.surname],
                       capture_output=True, text=True)
        n = len(os.listdir(img_dir)) if os.path.isdir(img_dir) else 0
        print("配图 {} 张已生成到 {}".format(n, img_dir))

    use_base = base_available() and not args.no_base
    if use_base:
        ok = render_with_base(md_text, args.out, args.theme, args.motif)
        engine = "HTML基座v9" if ok else "HTML基座v9(渲染有警告)"
    else:
        render_fallback(md_text, args.out)
        engine = "简易兜底模板"

    size = os.path.getsize(args.out) if os.path.exists(args.out) else 0
    print("OK engine={} out={} bytes={}".format(engine, args.out, size))


if __name__ == "__main__":
    main()
