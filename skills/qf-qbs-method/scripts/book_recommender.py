#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QBS 法 · 荐书评分表生成器（零第三方依赖）

读取候选书 CSV，按「经典书四维标准」计算加权分并排序，输出 Markdown 评分表。
CSV 表头：title,author,first_pub_year,authority,crossgen,match,note
  - first_pub_year：首版年份（整数）
  - authority：权威性 0-10（作者与出版社的学界/业界地位）
  - crossgen：跨代验证 0-10（被多代读者与后续著作反复引用）
  - match：问题匹配度 0-10（与本次问题的贴合程度）
"""
import argparse
import csv
import sys
from datetime import datetime

WEIGHTS = {"time": 0.30, "authority": 0.25, "crossgen": 0.20, "match": 0.25}
FIELDS = ["title", "author", "first_pub_year", "authority", "crossgen", "match", "note"]


def time_score(year, now_year):
    if not year or year <= 0:
        return 1.0, "年份缺失"
    age = now_year - year
    if age >= 30:
        return 10.0, "距今%d年（≥30，通过时间检验）" % age
    if age >= 20:
        return 7.0, "距今%d年（20—30，时间检验不足）" % age
    if age >= 10:
        return 4.0, "距今%d年（10—20，未过经典线）" % age
    return 1.0, "距今%d年（<10，属新书）" % age


def to_num(v, default=0.0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(10.0, x))


def main():
    ap = argparse.ArgumentParser(description="QBS 荐书评分表生成器：按经典书四维标准加权排序")
    ap.add_argument("--problem", default="", help="待解决的问题陈述")
    ap.add_argument("--candidates", default="",
                    help="候选书 CSV（表头：title,author,first_pub_year,authority,crossgen,match,note）")
    ap.add_argument("--out", default="recommend.md", help="输出 Markdown 路径（默认 recommend.md）")
    ap.add_argument("--now-year", type=int, default=datetime.now().year, help="基准年份（默认当前年）")
    ap.add_argument("--template", action="store_true", help="仅输出候选 CSV 模板后退出")
    args = ap.parse_args()

    if args.template:
        with open("candidates_template.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)
            w.writerow(["卓有成效的管理者", "彼得·德鲁克", "1966", "10", "10", "9", "管理学经典"])
        print("已写出 candidates_template.csv")
        return 0

    if not args.candidates:
        print("错误：须提供 --candidates（或加 --template 生成 CSV 模板）", file=sys.stderr)
        return 2

    try:
        with open(args.candidates, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print("错误：候选文件不存在：%s" % args.candidates, file=sys.stderr)
        return 2

    if not rows:
        print("错误：候选文件为空", file=sys.stderr)
        return 2

    scored = []
    for r in rows:
        title = (r.get("title") or "").strip()
        try:
            year = int(float(r.get("first_pub_year") or 0))
        except ValueError:
            year = 0
        ts, tnote = time_score(year, args.now_year)
        au = to_num(r.get("authority"))
        cg = to_num(r.get("crossgen"))
        mt = to_num(r.get("match"))
        total = ts * WEIGHTS["time"] + au * WEIGHTS["authority"] + cg * WEIGHTS["crossgen"] + mt * WEIGHTS["match"]
        scored.append({
            "title": title, "author": (r.get("author") or "").strip(),
            "year": year, "ts": ts, "au": au, "cg": cg, "mt": mt,
            "total": total, "tnote": tnote, "note": (r.get("note") or "").strip(),
        })

    scored.sort(key=lambda x: x["total"], reverse=True)

    lines = []
    lines.append("# QBS 荐书评分表\n")
    lines.append("**问题**：%s\n" % args.problem)
    lines.append("基准年份：%d｜加权口径：时间检验 %.2f + 权威性 %.2f + 跨代验证 %.2f + 问题匹配度 %.2f\n" %
                 (args.now_year, WEIGHTS["time"], WEIGHTS["authority"], WEIGHTS["crossgen"], WEIGHTS["match"]))
    lines.append("| 排名 | 书名 | 作者 | 首版年 | 时间检验 | 权威性 | 跨代验证 | 匹配度 | 加权总分 | 备注 |")
    lines.append("|:--:|:--|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--|")
    for i, s in enumerate(scored, 1):
        lines.append("| %d | %s | %s | %s | %.1f | %.1f | %.1f | %.1f | **%.2f** | %s |" % (
            i, s["title"], s["author"], s["year"] or "—", s["ts"], s["au"], s["cg"], s["mt"], s["total"], s["note"]))
    lines.append("")
    lines.append("## 时间检验校验\n")
    for s in scored:
        flag = "✅" if s["year"] and (args.now_year - s["year"]) >= 30 else "⚠️"
        lines.append("- %s %s：%s" % (flag, s["title"], s["tnote"]))
    lines.append("")
    lines.append("> 入选建议：加权总分前列且时间检验通过（≥30 年）者优先；未过经典线的新书须标注取舍理由。\n")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("已生成荐书评分表：%s（候选 %d 本，榜首：%s，%.2f 分）" %
          (args.out, len(scored), scored[0]["title"], scored[0]["total"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
