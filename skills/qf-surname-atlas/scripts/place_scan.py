#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""姓氏地名扫描：以"姓氏+村/庄/家/营/寨/屯"等高德 POI 密度，侧面反映宗族聚居。

用法：
  python3 scripts/place_scan.py --surname 王
  python3 scripts/place_scan.py --surname 王 --city 西安
  python3 scripts/place_scan.py --surname 王 --city 西安 --format json

说明：
  地区级姓氏人口无官方逐县统计。大量村落以主姓命名（王村、李庄、张家湾），
  故以姓氏地名密度作为宗族聚居程度的侧面证据，不作人口数字断言。
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
KEY = os.environ.get("AMAP_KEY", "")
SUFFIXES = ["村", "庄", "家", "营", "寨", "屯"]


def amap_text(keywords, city=None, citylimit=True):
    params = {
        "key": KEY,
        "keywords": keywords,
        "offset": 25,
        "page": 1,
        "extensions": "base",
    }
    if city:
        params["city"] = city
        params["citylimit"] = "true" if citylimit else "false"
    url = "https://restapi.amap.com/v3/place/text?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def scan(surname, city=None):
    if not KEY:
        print("【缺少 AMAP_KEY】无法进行地名扫描，请先配置环境变量 AMAP_KEY。", file=sys.stderr)
        sys.exit(3)

    seen = set()
    items = []
    by_kw = {}
    errors = []

    for suf in SUFFIXES:
        kw = surname + suf
        try:
            d = amap_text(kw, city)
        except Exception as e:  # 网络/限流
            errors.append("{}: {}".format(kw, e))
            by_kw[kw] = {"count": 0, "error": str(e)}
            time.sleep(1.0)
            continue

        if str(d.get("status")) != "1":
            errors.append("{}: {}".format(kw, d.get("info")))
            by_kw[kw] = {"count": 0, "error": d.get("info")}
            time.sleep(1.0)
            continue

        pois = d.get("pois") or []
        by_kw[kw] = {"count": len(pois)}
        for p in pois:
            pid = p.get("id")
            if pid in seen:
                continue
            seen.add(pid)
            loc = p.get("location", "") or ""
            lng, _, lat = loc.partition(",")
            items.append({
                "name": p.get("name"),
                "type": p.get("type"),
                "lng": lng,
                "lat": lat,
                "address": p.get("address"),
            })
        time.sleep(0.5)  # 限流保护

    result = {
        "surname": surname,
        "city": city or "全国",
        "total_unique": len(items),
        "by_keyword": by_kw,
        "samples": items[:40],
        "errors": errors,
        "note": "姓氏地名密度为宗族聚居程度的侧面证据，非人口数字。地名为'姓氏+村/庄/家/营/寨/屯'形式。",
    }
    return result


def render_md(r):
    L = ["# {}姓姓氏地名扫描（{}）".format(r["surname"], r["city"]), ""]
    L.append("共检索到不重复的姓氏地名 **{}** 处。".format(r["total_unique"]))
    L.append("")
    L.append("## 按后缀分布")
    for kw, v in r["by_keyword"].items():
        if isinstance(v, dict) and "error" in v:
            L.append("- {}：检索失败（{}）".format(kw, v["error"]))
        else:
            cnt = v["count"] if isinstance(v, dict) else v
            L.append("- {}：{} 处".format(kw, cnt))
    L.append("")
    if r["samples"]:
        L.append("## 部分地名样例")
        for s in r["samples"][:20]:
            L.append("- {}（{}）".format(s["name"], s.get("address") or "地址不详"))
        L.append("")
    L.append("## 说明")
    L.append(r["note"])
    L.append("")
    L.append("> 本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="姓氏地名扫描（高德 POI）")
    ap.add_argument("--surname", required=True, help="姓氏，如 王")
    ap.add_argument("--city", help="城市名，如 西安（不填为全国）")
    ap.add_argument("--format", choices=["md", "json"], default="json")
    args = ap.parse_args()

    r = scan(args.surname, args.city)
    if args.format == "md":
        print(render_md(r))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
