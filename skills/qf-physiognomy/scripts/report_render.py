#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_render.py —— 生成相学文化解读报告（Markdown 底稿 + HTML）

用法：
  python3 scripts/report_render.py --input result.json --out 相学文化解读.html
  python3 scripts/report_render.py --input result.json --md-only --out report.md
  python3 scripts/report_render.py --demo --out 示例.html        # 用内置样例
"""
import os
import sys
import json
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
DEMO = os.path.join(ASSETS, "demo_result.json")

THEME = "sunset"


def _load(name):
    p = os.path.join(ASSETS, name)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def build_md_knowledge():
    """相学文化知识全集报告（去个人化，全部为知识史陈述）。"""
    palaces = _load("palaces_full.json").get("palaces", [])
    organs = _load("wuguan.json").get("organs", [])
    themes = _load("themes.json").get("themes", [])
    schools = _load("schools.json").get("schools", [])
    timeline = _load("schools.json").get("timeline", [])
    tuoming = _load("schools.json").get("托名说明", "")
    qise = _load("qise.json")
    shengu = _load("shengu.json")
    classics = _load("classics.json").get("items", [])

    L = []
    L.append("# 相学文化知识全集")
    L.append("")
    L.append("> 依据《麻衣神相》《神相全编》《冰鉴》等公有领域相学文献的纲要性整理，")
    L.append("> 系统呈现十二宫、五官、三停、五行形相、气色、神骨及传统相学的**议题史**。")
    L.append("> 全文为**知识史陈述**——讲古人如何立说、如何命名，不针对任何个人作判断。")
    L.append("")

    # 一、概览
    L.append("## 一、报告概览")
    L.append("")
    L.append(":::kpi")
    L.append("十二宫|%d|逐宫通论" % len(palaces))
    L.append("五官|%d|逐官详论" % len(organs))
    L.append("议题史|%d|命题+现代审视" % len(themes))
    L.append("流派|%d|源流与方法" % len(schools))
    L.append("典籍|%d|部（公有领域）" % len(classics))
    L.append(":::")
    L.append("")
    L.append("本报告由「相学文化」技能生成，把相学文献中散见的名目与论述整理为可检索的知识件：")
    L.append("先分部位（十二宫、五官、三停），再辨形态与名目，后系之以典籍出处；")
    L.append("第六节另立**议题史**，陈述古人就寿夭、禄命、性情、才具、气色、形神等命题如何立说，")
    L.append("并逐条附**现代审视**。全文不作任何个人判断。")
    L.append("")
    L.append("![五行形相示意](images/wuxing5.svg){wide}")
    L.append("")
    L.append("*图 1　五行形相示意　·　依《神相全编·五行形相》程序化绘制，为比类方法的图解*")
    L.append("")

    # 二、十二宫
    L.append("## 二、十二宫逐宫通论")
    L.append("")
    L.append("相学以面部十二处部位为「十二宫」，分论各处形态，见《麻衣神相》卷三「十二宫论」。")
    L.append("以下逐宫列出位置、传统所主、典籍原文、形态名目与文化说明。")
    L.append("")
    L.append("![面部十二宫分布示意](images/face_palace12.svg){wide}")
    L.append("")
    L.append("*图 2　面部十二宫分布示意　·　依《麻衣神相》卷三所载宫位程序化绘制*")
    L.append("")
    for p in palaces:
        L.append("### %s：%s" % (p["name"], p["pos"]))
        L.append("")
        L.append("- **传统所主**：%s" % p["sizhu"])
        L.append("- **典籍原文**：%s" % p["classic"])
        L.append("- **出处**：%s" % p["source"])
        L.append("- **形态名目**：%s" % "、".join(p["morphology"]))
        L.append("- **各派差异**：%s" % p["schools"])
        L.append("- **文化说明**：%s" % p["culture"])
        L.append("")

    # 三、五官
    L.append("## 三、五官详论")
    L.append("")
    L.append("相学以眉、目、鼻、口、耳为五官，各配一名目。以下逐官列出别称、所配五行、论说要点与形态名目。")
    L.append("")
    L.append(":::bento")
    for o in organs:
        L.append("%s|%s|%s" % (o["name"], o["guan"], o["wuxing"]))
    L.append(":::")
    L.append("")
    for o in organs:
        L.append("### %s（%s）" % (o["name"], o["guan"]))
        L.append("")
        L.append("- **所配五行**：%s" % o["wuxing"])
        L.append("- **论说要点**：%s" % o["function"])
        L.append("- **形态名目**：%s" % "、".join(o["morphology"]))
        L.append("- **典籍原文**：%s" % o["classic"])
        L.append("- **出处**：%s" % o["source"])
        L.append("- **文化说明**：%s" % o["culture"])
        L.append("")

    # 四、三停/五行/气色
    L.append("## 四、三停、五行形相与气色")
    L.append("")
    L.append("相学以发际至眉为上停、眉至准头为中停、准头至地阁为下停，合称「三停」，见《麻衣神相·十观》。")
    L.append("")
    L.append(":::timeline")
    L.append("上停|额部一段|自发际至眉，古称「初主」")
    L.append("中停|鼻颧一段|自眉至准头，古称「中主」")
    L.append("下停|口颐一段|自准头至地阁，古称「末主」")
    L.append(":::")
    L.append("")
    L.append("《神相全编·五行形相》以五行比类脸形：金形面方而正、木形面长而瘦、")
    L.append("水形面圆而润、火形面上尖下阔、土形面圆而厚；古籍另载五行相兼之说。")
    L.append("")
    L.append("**气色论**：相书以面部气色（明润枯暗）盛衰论人顺逆，立五色配五行之说——")
    wuse = "；".join("%s属%s" % (w["color"], w["element"]) for w in qise.get("wuse", []))
    L.append(wuse + "。此说与中医望色语汇同源，然取以论人事，旨趣不同。")
    L.append("")
    L.append(":::law")
    L.append("现代审视|气色由睡眠、饮食、疾患、情绪、光线、妆造、影像条件共同决定，随境而变，不能稳定对应人事际遇；以气色断顺逆缺乏可证伪性（此系本报告之审视，非古籍原文）")
    L.append(":::")
    L.append("")

    # 五、神骨
    L.append("## 五、神骨论（《冰鉴》一派）")
    L.append("")
    L.append("旧题清·曾国藩《冰鉴》以「神、骨、气、态」为纲，主张形态之上别有神采与骨力。")
    L.append("")
    for it in shengu.get("items", []):
        L.append("### %s" % it["name"])
        L.append("")
        L.append("- **论述**：%s" % it["content"])
        L.append("- **出处**：%s" % it["source"])
        L.append("- **按语**：%s" % it["note"])
        L.append("")
    L.append(":::law")
    L.append("现代审视|%s（此系本报告之审视，非古籍原文）" % shengu.get("critique", ""))
    L.append(":::")
    L.append("")

    # 六、议题史（核心）
    L.append("## 六、传统相学议题史")
    L.append("")
    L.append("本节逐一陈述「古人就某一命题如何立说」，命题述为「传统/古籍以……为说」，")
    L.append("并逐条附**现代审视**。此为**文化史陈述**，古人持此说，今人不必信从；")
    L.append("本技能不对任何个人作判断。")
    L.append("")
    for t in themes:
        L.append("### %s" % t["name"])
        L.append("")
        L.append("- **命题概要**：%s" % t["summary"])
        L.append("- **古人论说**：")
        for v in t["classic_views"]:
            L.append("    - %s —— %s" % (v["text"], v["source"]))
        L.append("- **流变**：%s" % t["history"])
        L.append("- **现代审视**：%s" % t["critique"])
        L.append("- **结语**：%s" % t["status"])
        L.append("")

    # 七、流派与典籍
    L.append("## 七、流派源流与典籍年表")
    L.append("")
    L.append(":::bento")
    for s in schools:
        L.append("%s|%s|%s" % (s["name"], s["period"], s["method"][:18]))
    L.append(":::")
    L.append("")
    for s in schools:
        L.append("**%s**（%s）　代表：%s。%s" % (s["name"], s["period"], "、".join(s["representatives"]), s["note"]))
        L.append("")
    L.append("**典籍年表**：")
    L.append("")
    for t in timeline:
        L.append("- **%s**　%s　—— %s" % (t["era"], t["work"], t["note"]))
    L.append("")
    if tuoming:
        L.append("> 托名说明：%s" % tuoming)
        L.append("")

    # 八、典籍
    L.append("## 八、所引典籍")
    L.append("")
    L.append("本技能所引相学古籍均为公有领域著作，条目为纲要性摘录，不作逐字校勘。")
    L.append("")
    L.append(":::matrix")
    L.append("典籍|托名/作者|年代|内容概要")
    for x in classics:
        L.append("%s|%s|%s|%s" % (x["name"], x["attr"], x["era"], x["desc"]))
    L.append(":::")
    L.append("")

    # 九、文化说明与免责
    L.append("## 九、文化说明与免责声明")
    L.append("")
    L.append("相学以五行比类脸形、以十二宫划分面部、以五官分论形态、以气色与神骨论人，")
    L.append("是传统时代观察与记录相貌的一套话语体系，也是一份值得了解的文化史料。")
    L.append("本报告整理其名目与论述，供文化了解与文献参考。")
    L.append("")
    L.append("**识别误差声明**：相学文献条目互异、出处复杂，古籍托名现象普遍，")
    L.append("此处标注以通行说法为准，供文化了解，不构成任何判断依据。")
    L.append("")
    L.append("**免责声明**：本报告为中国传统相学文化的知识介绍与文化史陈述，")
    L.append("所引内容均取自公有领域典籍，不构成任何判断、预测、评价或决策依据，")
    L.append("不对任何现实结果作推断或预言。请勿据此对任何人作出评价或决定。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("*本报告由中国传统文化技能「相学文化」（qf-physiognomy）生成　·　作者：清风明月*")
    L.append("")
    return "\n".join(L)


def _v(x):
    return x if x else "—"


def build_md(r):
    L = []
    fs = r.get("face_shape") or "—"
    parts = r.get("parts", [])
    hit = len(parts)

    L.append("# 相学文化解读报告")
    L.append("")
    L.append("> 依据《麻衣神相》十二宫论与五官论，对面容形态作描述性文化解读。")
    L.append("")
    L.append("## 一、报告概览")
    L.append("")
    L.append(":::kpi")
    L.append("脸型归类|%s|五行比类" % fs)
    L.append("命中部位|%d|处" % hit)
    L.append("引据典籍|6|部（公有领域）")
    L.append(":::")
    L.append("")
    L.append("本报告由「相学文化」技能生成：先把面容形态观察规范为词库内的描述词，"
             "再逐条匹配相学典籍中的论述，并标注出处。全文只作**形态描述**与**传统论述引用**，"
             "不作任何判断或预测。")
    L.append("")
    L.append("![五行形相示意](images/wuxing5.svg){wide}")
    L.append("")
    L.append("*图 1　五行形相示意　·　依《神相全编·五行形相》程序化绘制，为比类方法的图解，非照片模拟*")
    L.append("")

    # 二、三停
    L.append("## 二、三停与面容分段")
    L.append("")
    st = r.get("santing") or {}
    L.append("相学以发际至眉为上停、眉至准头为中停、准头至地阁为下停，合称「三停」。"
             "此说见《麻衣神相》卷一「十观」篇，属传统的面部三段划分方式。")
    L.append("")
    L.append(":::timeline")
    L.append("上停|额部一段|自发际至眉，古称「初主」")
    L.append("中停|鼻颧一段|自眉至准头，古称「中主」")
    L.append("下停|口颐一段|自准头至地阁，古称「末主」")
    L.append(":::")
    L.append("")
    L.append("本次观察记录：上停 %s；中停 %s；下停 %s。"
             % (_v(st.get("upper")), _v(st.get("middle")), _v(st.get("lower"))))
    L.append("")
    L.append(":::law")
    L.append("三停之说|《麻衣神相·十观》：三停匀称之说，古籍以三段相称为论（此系古籍纲要性表述，非本报告之判断）")
    L.append(":::")
    L.append("")

    # 三、五官分论
    L.append("## 三、五官与额颏分论")
    L.append("")
    L.append("以下按部位逐项列出可观察的形态与相学典籍中的相关论述。每条均标注出处，"
             "引文属古籍原文之文化表述，不代表本报告观点。")
    L.append("")
    if not parts:
        L.append(":::gap")
        L.append("本次未录入有效特征，无分论内容。请用 face_analyze.py --template 录入后重跑。")
        L.append(":::")
        L.append("")
    else:
        L.append(":::bento")
        for p in parts:
            m = p["matched"][0]
            L.append("%s|%s|%s" % (p["part_cn"], m["feature"], m["desc"]))
        L.append(":::")
        L.append("")
        for p in parts:
            m = p["matched"][0]
            L.append("### %s：%s" % (p["part_cn"], m["feature"]))
            L.append("")
            L.append("- **形态描述**：%s" % m["desc"])
            L.append("- **所属宫位**：%s" % (m["palace"] or "—"))
            L.append("- **相学论述**：%s" % m["reading"])
            L.append("- **出处**：%s" % (m["source"] or "—"))
            L.append("")
            if m.get("classic"):
                L.append("> %s" % m["classic"])
                L.append("")

    # 四、十二宫
    L.append("## 四、面部十二宫概说")
    L.append("")
    p12 = r.get("palace12") or {}
    L.append(p12.get("说明", ""))
    L.append("")
    L.append("![面部十二宫分布示意](images/face_palace12.svg){wide}")
    L.append("")
    L.append("*图 2　面部十二宫分布示意　·　依《麻衣神相》卷三所载宫位程序化绘制，"
             "为文化知识图解，非对面容之判断*")
    L.append("")
    L.append(":::faq")
    for x in p12.get("palaces", []):
        L.append("%s在哪里？|%s，在%s。%s（%s）" % (x["name"], x["desc"], x["pos"], x["classic"], x["source"]))
    L.append(":::")
    L.append("")

    # 五、典籍索引
    L.append("## 五、所引典籍")
    L.append("")
    cl = r.get("classics") or {}
    L.append(cl.get("说明", ""))
    L.append("")
    L.append(":::matrix")
    L.append("典籍|托名/作者|年代|内容概要")
    for x in cl.get("items", []):
        L.append("%s|%s|%s|%s" % (x["name"], x["attr"], x["era"], x["desc"]))
    L.append(":::")
    L.append("")

    # 六、小结与声明
    L.append("## 六、文化小结与识别误差声明")
    L.append("")
    L.append("本次解读共命中 %d 处部位，脸型归类为「%s」。相学以五行比类脸形、"
             "以十二宫划分面部、以五官分论形态，是传统时代以最直观方式观察与记录人的相貌"
             "的一套话语体系，今人可将其作为民俗文化知识来了解。" % (hit, fs))
    L.append("")
    L.append("**识别误差声明**：面部形态的观察由读图完成，受光线、角度、妆造、表情与"
             "模糊度影响，所述形态与实际存在偏差；不同观察者对同一面容的描述亦可能不同。"
             "结果仅供文化了解，不构成任何判断依据。")
    L.append("")
    if r.get("skipped"):
        L.append("> 本次有 %d 项特征未匹配到词库条文：%s。"
                 % (len(r["skipped"]), "、".join(r["skipped"])))
        L.append("")

    L.append("## 七、免责声明")
    L.append("")
    L.append("本报告为中国传统相学文化的知识介绍与形态描述整理，所引内容均取自公有领域典籍，"
             "不构成任何判断、预测、评价或决策依据。**不对任何现实结果作推断或预言**。"
             "请勿据此对任何人作出评价或决定。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("*本报告由中国传统文化技能「相学文化」（qf-physiognomy）生成　·　作者：清风明月*")
    L.append("")
    return "\n".join(L)


def build_md_combined(r, feats):
    """融合模式：相学知识 + 本次面容形态记录（形态记录仅陈述，不作判断）。"""
    palaces = _load("palaces_full.json").get("palaces", [])
    themes = _load("themes.json").get("themes", [])
    classics = _load("classics.json").get("items", [])
    qise = _load("qise.json")
    shengu = _load("shengu.json")

    fs = r.get("face_shape") or "—"
    parts = r.get("parts", [])
    st = r.get("santing") or {}
    ffeat = (feats.get("features") or {}) if isinstance(feats, dict) else {}

    L = []
    L.append("# 相学文化解读报告（照片 × 知识版）")
    L.append("")
    L.append("> 前半讲相学知识（十二宫、五官、气色、神骨、议题史），")
    L.append("> 后半为**本次照片的形态记录**。全文只作形态描述与知识史陈述，**不对照片中的人作任何判断**。")
    L.append("")

    # 一、概览
    L.append("## 一、报告概览")
    L.append("")
    L.append(":::kpi")
    L.append("脸型归类|%s|五行比类" % fs)
    L.append("命中部位|%d|处" % len(parts))
    L.append("知识件|4|十二宫/五官/气色神骨/议题史")
    L.append("引据典籍|%d|部（公有领域）" % len(classics))
    L.append(":::")
    L.append("")
    L.append("本报告由「相学文化」技能生成：先以相学知识为底，再落回本次照片的可观察形态。")
    L.append("**形态记录不等于判断**——记录的是「眉长过目」「准头饱满」这类形体，而非对人的评价。")
    L.append("")
    L.append("![五行形相示意](images/wuxing5.svg){wide}")
    L.append("")
    L.append("*图 1　五行形相示意　·　依《神相全编·五行形相》程序化绘制*")
    L.append("")

    # 二、本次面容形态记录
    L.append("## 二、本次面容形态记录")
    L.append("")
    L.append("三停分段：上停 %s；中停 %s；下停 %s。" % (_v(st.get("upper")), _v(st.get("middle")), _v(st.get("lower"))))
    L.append("")
    L.append(":::bento")
    for p in parts:
        m = p["matched"][0]
        L.append("%s|%s|%s" % (p["part_cn"], m["feature"], m["palace"] or "—"))
    L.append(":::")
    L.append("")

    # 三、五官与额颏分论 × 本次记录
    L.append("## 三、五官与额颏分论 × 本次记录")
    L.append("")
    L.append("每条先列本次照片的形态记录，再列相学典籍中的相关论述与出处。主语均为「古籍/传统相学」。")
    L.append("")
    for p in parts:
        m = p["matched"][0]
        note = ""
        raw = ffeat.get(p["part"])
        if isinstance(raw, dict):
            note = raw.get("note", "")
        L.append("### %s：%s" % (p["part_cn"], m["feature"]))
        L.append("")
        if note:
            L.append("- **本次记录**：%s" % note)
        L.append("- **形态描述**：%s" % m["desc"])
        L.append("- **所属宫位**：%s" % (m["palace"] or "—"))
        L.append("- **相学论述**：%s" % m["reading"])
        L.append("- **出处**：%s" % (m["source"] or "—"))
        L.append("")

    # 四、十二宫通论
    L.append("## 四、十二宫逐宫通论")
    L.append("")
    L.append("相学以面部十二处部位为「十二宫」，见《麻衣神相》卷三「十二宫论」。以下为知识陈述，非对本人的判断。")
    L.append("")
    L.append("![面部十二宫分布示意](images/face_palace12.svg){wide}")
    L.append("")
    L.append("*图 2　面部十二宫分布示意　·　依《麻衣神相》卷三所载宫位程序化绘制*")
    L.append("")
    for p in palaces:
        L.append("### %s：%s" % (p["name"], p["pos"]))
        L.append("")
        L.append("- **传统所主**：%s" % p["sizhu"])
        L.append("- **典籍原文**：%s（%s）" % (p["classic"], p["source"]))
        L.append("- **形态名目**：%s" % "、".join(p["morphology"]))
        L.append("- **文化说明**：%s" % p["culture"])
        L.append("")

    # 五、气色与神骨
    L.append("## 五、气色论与神骨论")
    L.append("")
    L.append("**气色论**：相书以面部气色（明润枯暗）盛衰论人顺逆，立五色配五行之说——")
    L.append("青属木、赤属火、黄属土、白属金、黑属水。此说与中医望色语汇同源，然取以论人事，旨趣不同。")
    L.append("")
    L.append(":::law")
    L.append("本次说明|照片中的气色受光线、妆容与影像条件影响，不能作为形态记录的依据；故本节只述气色论之名目，不对本照片作气色判读（此系本报告之说明，非古籍原文）")
    L.append(":::")
    L.append("")
    L.append("**神骨论**（旧题清·曾国藩《冰鉴》一派）：以「神、骨、气、态」为纲——")
    for it in shengu.get("items", []):
        L.append("- **%s**：%s（%s）" % (it["name"], it["content"], it["source"]))
    L.append("")
    L.append(":::law")
    L.append("现代审视|神、骨、气、态抽象而难定义，缺乏可操作标准与可证伪性，其价值在文献与文辞，不在判断效力（此系本报告之审视，非古籍原文）")
    L.append(":::")
    L.append("")

    # 六、议题史要略
    L.append("## 六、传统相学议题史（要略）")
    L.append("")
    L.append("古人就下列命题如何立说，属**文化史陈述**；古人持此说，今人不必信从，")
    L.append("本技能**不对照片中的人作任何判断**。")
    L.append("")
    for t in themes:
        L.append("- **%s**：%s。结语：%s" % (t["name"], t["summary"], t["status"]))
    L.append("")

    # 七、典籍
    L.append("## 七、所引典籍")
    L.append("")
    L.append(":::matrix")
    L.append("典籍|托名/作者|年代|内容概要")
    for x in classics:
        L.append("%s|%s|%s|%s" % (x["name"], x["attr"], x["era"], x["desc"]))
    L.append(":::")
    L.append("")

    # 八、声明
    L.append("## 八、文化说明与免责声明")
    L.append("")
    L.append("**识别误差声明**：本次形态记录由读图完成，受光线、角度、妆造、表情与模糊度影响，")
    L.append("所述形态与实际存在偏差；不同观察者对同一面容的描述亦可能不同。知识条目为纲要性摘录，不逐字校勘。")
    L.append("")
    L.append("**免责声明**：本报告为中国传统相学文化的知识介绍与形态描述整理，")
    L.append("所引内容均取自公有领域典籍，不构成任何判断、预测、评价或决策依据，")
    L.append("不对任何现实结果作推断或预言。请勿据此对任何人作出评价或决定。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("*本报告由中国传统文化技能「相学文化」（qf-physiognomy）生成　·　作者：清风明月*")
    L.append("")
    return "\n".join(L)


def render_html(md_path, out, title):
    md2 = os.path.join(HERE, "htmlbase", "md2report.py")
    if not os.path.exists(md2):
        print("[WARN] 未找到 HTML 基座：%s，仅输出 Markdown" % md2)
        return False
    cmd = [sys.executable, md2, md_path, "-o", out, "--theme", THEME,
           "--motif", "editorial", "--check"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="相学文化解读报告生成")
    ap.add_argument("--input", help="result.json（rule_engine.py 输出）")
    ap.add_argument("--out", default="相学文化解读.html")
    ap.add_argument("--mode", choices=("physiognomy", "knowledge", "combined"), default="physiognomy",
                    help="physiognomy=个人特征解读；knowledge=知识全集；combined=照片×知识融合")
    ap.add_argument("--features", help="features.json（combined 模式用于补充本次记录）")
    ap.add_argument("--md-only", action="store_true", help="仅生成 Markdown")
    ap.add_argument("--demo", action="store_true", help="使用内置样例数据")
    ap.add_argument("--no-images", action="store_true", help="不生成配图")
    a = ap.parse_args()

    if a.mode == "knowledge":
        md = build_md_knowledge()
    elif a.mode == "combined":
        with open(a.input, encoding="utf-8") as f:
            r = json.load(f)
        feats = {}
        fpath = a.features
        if not fpath:
            cand = os.path.join(os.path.dirname(os.path.abspath(a.input)), "features.json")
            if os.path.exists(cand):
                fpath = cand
        if fpath and os.path.exists(fpath):
            with open(fpath, encoding="utf-8") as f:
                feats = json.load(f)
        md = build_md_combined(r, feats)
    elif a.demo:
        with open(DEMO, encoding="utf-8") as f:
            r = json.load(f)
        md = build_md(r)
    elif a.input:
        with open(a.input, encoding="utf-8") as f:
            r = json.load(f)
        md = build_md(r)
    else:
        ap.print_help()
        return 2
    md_path = os.path.splitext(a.out)[0] + ".md"
    os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    # 默认生成配图（示意图程序化绘制，落在 md 同目录的 images/）
    img_dir = os.path.join(os.path.dirname(os.path.abspath(md_path)), "images")
    dg = os.path.join(HERE, "diagram.py")
    if os.path.exists(dg) and not a.no_images:
        subprocess.run([sys.executable, dg, "--outdir", img_dir],
                       capture_output=True, text=True)
        n = len([x for x in os.listdir(img_dir) if x.endswith(".svg")]) if os.path.isdir(img_dir) else 0
        print("[OK] 配图 %d 张已生成到 %s" % (n, img_dir))
    print("[OK] Markdown 底稿已写入 %s（%d 字）" % (md_path, len(md)))

    if a.md_only:
        return 0
    if render_html(md_path, a.out, "相学文化解读报告"):
        print("[OK] HTML 报告已写入 %s" % a.out)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
