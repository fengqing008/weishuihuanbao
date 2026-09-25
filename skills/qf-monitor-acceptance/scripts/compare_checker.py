#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_checker.py — 在线监测设备比对结果判定（HJ 355-2019）

用法:
  python3 compare_checker.py -i 比对数据.csv [-o 判定结果.csv]

输入 CSV 列（首行表头）：
  参数,在线值,实验室值[,限值类型,限值]
  - 限值类型：rel（相对误差，%）/ abs（绝对误差）
  - 缺省限值类型与限值列时，按内置默认表取值
内置默认限值（HJ 355-2019，具体以标准原文与许可量程为准）：
  pH: abs 0.5 ; 流量: rel 10 ; 化学需氧量/COD/氨氮/总磷/总氮: rel 15

输出：判定结果 CSV（参数/在线值/实验室值/误差/限值类型/限值/是否合格/超限幅度），
     并打印总体结论。退出码：0=全部合格，1=存在超限。
"""
import argparse
import csv
import os
import sys

DEFAULTS = {
    "ph": ("abs", 0.5),
    "流量": ("rel", 10.0),
    "化学需氧量": ("rel", 15.0),
    "cod": ("rel", 15.0),
    "codcr": ("rel", 15.0),
    "氨氮": ("rel", 15.0),
    "总磷": ("rel", 15.0),
    "总氮": ("rel", 15.0),
}
ALIAS = {
    "ph值": "ph", "ph": "ph",
    "化学需氧量": "化学需氧量", "cod": "化学需氧量", "codcr": "化学需氧量",
    "氨氮": "氨氮", "nh3-n": "氨氮", "nh₃-n": "氨氮",
    "总磷": "总磷", "tp": "总磷", "总氮": "总氮", "tn": "总氮",
    "流量": "流量",
}


def norm(name):
    return ALIAS.get((name or "").strip().lower(), (name or "").strip())


def lookup_default(name):
    return DEFAULTS.get(norm(name).lower()) or DEFAULTS.get(name.strip().lower())


def calc(kind, online, lab):
    if kind == "abs":
        return abs(online - lab), None
    base = lab if lab != 0 else None
    if base is None:
        return abs(online - lab), None
    return abs(online - lab) / abs(lab) * 100.0, "%"


def main():
    ap = argparse.ArgumentParser(description="在线监测设备比对结果判定（HJ 355-2019）")
    ap.add_argument("-i", "--input", required=True, help="比对数据 CSV")
    ap.add_argument("-o", "--output", default=None, help="判定结果 CSV（可选）")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        sys.exit("输入文件不存在：%s" % args.input)

    rows = []
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    if not rows:
        sys.exit("输入 CSV 无数据行")

    out = []
    all_ok = True
    for r in rows:
        name = r.get("参数") or r.get("parameter") or ""
        try:
            online = float(r.get("在线值") or r.get("online"))
            lab = float(r.get("实验室值") or r.get("lab"))
        except (TypeError, ValueError):
            print("跳过无法解析的行：%r" % r, file=sys.stderr)
            continue
        kind = (r.get("限值类型") or "").strip().lower()
        limit = r.get("限值")
        if not kind or not limit:
            d = lookup_default(name)
            if d:
                kind = kind or d[0]
                limit = limit or d[1]
        if not kind or limit in (None, ""):
            print("警告：参数 %s 无限值，跳过" % name, file=sys.stderr)
            continue
        limit = float(limit)
        err, unit = calc(kind, online, lab)
        ok = err <= limit + 1e-9
        all_ok = all_ok and ok
        over = 0.0 if ok else err - limit
        out.append([name, online, lab, "%.3f" % err + (unit or ""),
                    kind, limit, "合格" if ok else "不合格", "%.3f" % over])

    header = ["参数", "在线值", "实验室值", "误差", "限值类型", "限值", "是否合格", "超限幅度"]
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(out)
        print("判定结果已写入：%s" % args.output)

    print("%-10s %-10s %-10s %-10s %-8s" % ("参数", "误差", "限值", "判定", "超限幅度"))
    for row in out:
        print("%-10s %-10s %-10s %-8s %-8s" % (row[0], row[3], row[5], row[6], row[7]))
    print("总体结论：%s" % ("全部合格" if all_ok else "存在超限，须整改复测"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
