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
DEMO = os.path.join(ROOT, "assets", "demo_result.json")

THEME = "sunset"


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
    L.append("三停之说|《麻衣神相·十观》：上停长，中停长，下停长，三停俱得，富贵荣昌（此系古籍原文之文化表述，非本报告之判断）")
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
             "不构成任何判断、预测、评价或决策依据。**不作运势、命运、吉凶等任何形式的推断**。"
             "请勿据此对任何人作出评价或决定。")
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
    ap.add_argument("--md-only", action="store_true", help="仅生成 Markdown")
    ap.add_argument("--demo", action="store_true", help="使用内置样例数据")
    ap.add_argument("--no-images", action="store_true", help="不生成配图")
    a = ap.parse_args()

    if a.demo:
        with open(DEMO, encoding="utf-8") as f:
            r = json.load(f)
    elif a.input:
        with open(a.input, encoding="utf-8") as f:
            r = json.load(f)
    else:
        ap.print_help()
        return 2

    md = build_md(r)
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
