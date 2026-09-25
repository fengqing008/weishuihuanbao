#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""政策沿革时间线。

按施行年份排序输出政策文件，识别同一事项的政策演进。
用法：
    python3 policy_timeline.py --demo
    python3 policy_timeline.py --input policies.csv
CSV 表头：文件名称,文号,施行日期,要点
"""
import argparse
import csv
import sys

DEMO = [
    ["污水处理费征收使用管理办法", "【待核】", "2015-03-01", "污水处理费征收使用"],
    ["省人民政府关于全面推进乡镇生活污水治理工作的意见", "【待核】", "2016-06-01", "乡镇污水治理总体要求"],
    ["关于推进全省乡镇生活污水治理提质增效行动的通知", "鄂建文〔2023〕4号", "2023-02-01", "提质增效行动"],
    ["关于调整我市城区自来水销售价格的通知", "利发改价格〔2024〕2号", "2024-05-01", "水价调整"],
    ["省财政厅等八部门关于规范政府和社会资本合作存量项目建设和运营的通知", "鄂财金发〔2026〕6号", "2026-02-01", "存量项目规范"],
]


def main():
    ap = argparse.ArgumentParser(description="政策沿革时间线")
    ap.add_argument("--input", help="政策 CSV 路径")
    ap.add_argument("--demo", action="store_true", help="使用内置示例")
    args = ap.parse_args()

    rows = DEMO if args.demo else None
    if rows is None:
        if not args.input:
            ap.error("请提供 --input 或 --demo")
        with open(args.input, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
            if rows and "文件名称" in rows[0][0]:
                rows = rows[1:]

    def year(r):
        d = (r[2] if len(r) > 2 else "")
        return d[:4] if d else "0000"

    rows = sorted(rows, key=year)
    print("政策沿革时间线（按施行年份排序）\n")
    for r in rows:
        name, no, date, key = (r + [""] * 4)[:4]
        print(f"{date:<12}{name}")
        print(f"            文号：{no}　要点：{key}")
    print("\n提示：同一事项多份文件并存时，按上位法优于下位法、新法优于旧法判断适用版本。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
