#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环评标准与限值速查

用法：
    python3 standard_lookup.py --list
    python3 standard_lookup.py --search 污水
    python3 standard_lookup.py --code GB18918
"""
import argparse, sys

STANDARDS = [
    ("GB 18918-2002", "城镇污水处理厂污染物排放标准", "排放标准", "城镇污水厂"),
    ("GB 8978-1996", "污水综合排放标准", "排放标准", "工业排水"),
    ("GB 21900-2008", "电镀污染物排放标准", "排放标准", "电镀行业"),
    ("GB 13458-2013", "合成氨工业水污染物排放标准", "排放标准", "合成氨"),
    ("GB 15580-2011", "磷肥工业水污染物排放标准", "排放标准", "磷肥"),
    ("GB 25467-2010", "铜镍钴工业污染物排放标准", "排放标准", "有色金属"),
    ("GB 3838-2002", "地表水环境质量标准", "质量标准", "受纳水体"),
    ("GB/T 14848-2017", "地下水质量标准", "质量标准", "地下水"),
    ("GB 3095-2012", "环境空气质量标准", "质量标准", "大气"),
    ("GB 3096-2008", "声环境质量标准", "质量标准", "噪声"),
    ("GB 36600-2018", "土壤环境质量建设用地土壤污染风险管控标准", "质量标准", "场地"),
    ("GB 15618-2018", "土壤环境质量农用地土壤污染风险管控标准", "质量标准", "农用地"),
    ("HJ 2.1-2016", "建设项目环境影响评价技术导则 总纲", "技术导则", "环评总纲"),
    ("HJ 2.3-2018", "地表水环境影响评价技术导则", "技术导则", "地表水"),
    ("HJ 2.2-2018", "大气环境影响评价技术导则", "技术导则", "大气"),
    ("HJ 2.4-2021", "声环境影响评价技术导则", "技术导则", "噪声"),
    ("HJ 964-2018", "土壤环境影响评价技术导则", "技术导则", "土壤"),
    ("HJ 610-2016", "地下水环境影响评价技术导则", "技术导则", "地下水"),
    ("HJ 19-2022", "环境影响评价技术导则 生态影响", "技术导则", "生态"),
]

def main():
    ap = argparse.ArgumentParser(description="环评标准与限值速查")
    ap.add_argument("--list", action="store_true", help="列出全部标准")
    ap.add_argument("--search", help="按关键词检索")
    ap.add_argument("--code", help="按标准号检索")
    a = ap.parse_args()
    rows = STANDARDS
    if a.code:
        key = a.code.replace(" ", "").upper()
        rows = [r for r in STANDARDS if key in r[0].replace(" ", "").upper()]
    elif a.search:
        rows = [r for r in STANDARDS if a.search in r[1] or a.search in r[3] or a.search in r[2]]
    print("=" * 76)
    print("环评标准速查    共 %d 条" % len(rows))
    print("=" * 76)
    print("%-18s %-40s %-10s %s" % ("标准号", "名称", "类别", "适用"))
    for code, name, cat, use in rows:
        print("%-18s %-40s %-10s %s" % (code, name[:38], cat, use))
    print("-" * 76)
    print("提示：标准存在修订，使用前须核对现行有效版本；地方标准严于国家标准时从其规定。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
