#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""水务政策法规速查。

按关键词、层级或发文机关检索内置政策库。
用法：
    python3 policy_lookup.py --q 特许经营
    python3 policy_lookup.py --level 省级
    python3 policy_lookup.py --list
"""
import argparse
import sys

DB = [
    {"name": "省人民政府关于全面推进乡镇生活污水治理工作的意见", "no": "【待核】", "level": "省级", "org": "省政府", "key": "乡镇污水治理总体要求"},
    {"name": "关于推进全省乡镇生活污水治理提质增效行动的通知", "no": "鄂建文〔2023〕4号", "level": "省级", "org": "住建厅", "key": "提质增效行动"},
    {"name": "湖北省人民政府关于进一步推进非经营性政府投资工程项目实施代建制的通知", "no": "【待核】", "level": "省级", "org": "省政府", "key": "代建制实施"},
    {"name": "国有企业参股管理暂行办法", "no": "国资发改革规〔2023〕41号", "level": "国家级", "org": "国资委", "key": "国企参股管理"},
    {"name": "基本建设项目建设成本管理规定", "no": "【待核】", "level": "国家级", "org": "财政部", "key": "建设成本管理"},
    {"name": "省财政厅等八部门关于规范政府和社会资本合作存量项目建设和运营的通知", "no": "鄂财金发〔2026〕6号", "level": "省级", "org": "财政厅", "key": "存量项目规范"},
    {"name": "关于调整我市城区自来水销售价格的通知", "no": "利发改价格〔2024〕2号", "level": "市县级", "org": "发改局", "key": "水价调整"},
    {"name": "基础设施和公用事业特许经营管理办法", "no": "【待核】", "level": "国家级", "org": "发改委等", "key": "特许经营基本制度"},
    {"name": "污水处理费征收使用管理办法", "no": "【待核】", "level": "国家级", "org": "财政部等", "key": "污水处理费征收"},
    {"name": "污泥无害化处理和资源化利用实施方案", "no": "【待核】", "level": "国家级", "org": "发改委等", "key": "污泥处理处置"},
]


def show(it):
    print(f"文件：{it['name']}")
    print(f"  文号：{it['no']}　层级：{it['level']}　发文机关：{it['org']}")
    print(f"  要点：{it['key']}")


def main():
    ap = argparse.ArgumentParser(description="水务政策法规速查")
    ap.add_argument("--q", help="关键词检索")
    ap.add_argument("--level", help="按层级：国家级/省级/市县级")
    ap.add_argument("--list", action="store_true", help="列出全部")
    args = ap.parse_args()

    if args.list:
        for it in DB:
            print(f"{it['level']:<6}{it['no']:<24}{it['name']}")
        return 0

    hits = []
    if args.level:
        hits = [it for it in DB if it["level"] == args.level]
    elif args.q:
        q = args.q.strip()
        hits = [it for it in DB if q in it["name"] or q in it["key"] or q in it["org"] or q in it["no"]]
    else:
        ap.error("请提供 --q / --level / --list")

    if not hits:
        print("未检索到匹配文件，调整关键词后重试。")
        return 1
    for it in hits:
        show(it)
    return 0


if __name__ == "__main__":
    sys.exit(main())
