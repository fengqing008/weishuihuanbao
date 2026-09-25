#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境风险等级矩阵查询。

按"可能性 × 后果"查询风险等级，或按等级列出内置风险源清单。
用法：
    python3 risk_matrix.py --demo
    python3 risk_matrix.py --level 重大
    python3 risk_matrix.py --p 高 --c 较大
"""
import argparse
import sys

LEVELS = ["低", "中", "较大", "重大"]
CONSEQ = ["轻微", "一般", "较大", "严重"]
PROB = ["低", "中", "高"]

MATRIX = {
    ("高", "轻微"): "中", ("高", "一般"): "较大", ("高", "较大"): "重大", ("高", "严重"): "重大",
    ("中", "轻微"): "低", ("中", "一般"): "中", ("中", "较大"): "较大", ("中", "严重"): "重大",
    ("低", "轻微"): "低", ("低", "一般"): "低", ("低", "较大"): "中", ("低", "严重"): "较大",
}

RISK_LIST = [
    ("药剂（次氯酸钠、酸碱）", "泄漏、中毒、腐蚀", "较大"),
    ("污泥", "异常外溢、含水率超标", "中"),
    ("污水", "超标排放、管网溢流", "较大"),
    ("危险废物", "泄漏、混存、非法转移", "较大"),
    ("有限空间", "中毒、窒息", "较大"),
    ("电气设备", "火灾、触电", "中"),
]


def query(p, c):
    if p not in PROB or c not in CONSEQ:
        return None
    return MATRIX[(p, c)]


def main():
    ap = argparse.ArgumentParser(description="环境风险等级矩阵查询")
    ap.add_argument("--p", help="可能性：低/中/高")
    ap.add_argument("--c", help="后果：轻微/一般/较大/严重")
    ap.add_argument("--level", help="按等级列出风险源")
    ap.add_argument("--demo", action="store_true", help="打印矩阵与风险源清单")
    args = ap.parse_args()

    if args.p and args.c:
        r = query(args.p, args.c)
        if r is None:
            print("参数不合法，可能性取 低/中/高，后果取 轻微/一般/较大/严重")
            return 1
        print(f"可能性={args.p}，后果={args.c} → 风险等级：{r}")
        return 0

    if args.level:
        hits = [x for x in RISK_LIST if x[2] == args.level]
        if not hits:
            print(f"无等级为「{args.level}」的风险源；可选：低/中/较大/重大")
            return 1
        for name, ev, lv in hits:
            print(f"[{lv}] {name}：{ev}")
        return 0

    print("可能性 × 后果 矩阵（行=可能性，列=后果）：")
    print("        " + "".join(f"{c:<8}" for c in CONSEQ))
    for p in PROB[::-1]:
        print(f"{p:<8}" + "".join(f"{MATRIX[(p, c)]:<8}" for c in CONSEQ))
    print("\n内置风险源清单：")
    for name, ev, lv in RISK_LIST:
        print(f"[{lv}] {name}：{ev}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
