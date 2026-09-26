# -*- coding: utf-8 -*-
"""geo_analyze.py — 环境形势分析（堪舆文化视角）

读取地点坐标或地址，检索周边环境要素，按传统四神砂格局与形煞民俗作文化解读。
不涉及吉凶判断，仅供了解传统建筑环境文化。

用法:
  python3 geo_analyze.py --address "某市某区XXX"
  python3 geo_analyze.py --lat 34.37 --lng 109.21
  python3 geo_analyze.py --address "..." --radius 1500 --json
"""
import os
import sys
import math
import json
import time
import argparse
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE, "assets")
KEY = os.environ.get("AMAP_KEY", "")

DIRS = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]

# 关键词 -> 环境类属
KW_GROUPS = [
    ("水体", ["河流", "湖", "水库", "池塘", "公园"]),
    ("道路", ["道路", "路", "高速", "立交"]),
    ("建筑", ["小区", "大厦", "广场", "写字楼"]),
    ("文教", ["学校", "大学", "图书馆"]),
    ("医疗", ["医院", "诊所"]),
    ("宗教", ["寺庙", "道观", "教堂", "墓地", "陵园"]),
]


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(address):
    if not KEY:
        return None
    q = urllib.parse.urlencode({"address": address, "key": KEY})
    d = http_json("https://restapi.amap.com/v3/geocode/geo?" + q)
    if d.get("status") == "1" and d.get("geocodes"):
        g = d["geocodes"][0]
        lng, lat = g["location"].split(",")
        return float(lng), float(lat), g.get("formatted_address", address)
    return None


def around(lng, lat, keywords, radius):
    if not KEY:
        return []
    out = []
    for kw in keywords:
        q = urllib.parse.urlencode({"location": "%f,%f" % (lng, lat), "keywords": kw,
                                    "radius": radius, "offset": 20, "key": KEY})
        try:
            d = http_json("https://restapi.amap.com/v3/place/around?" + q)
        except Exception:
            time.sleep(0.5)
            continue
        for p in (d.get("pois") or []):
            loc = p.get("location") or ""
            if "," not in loc:
                continue
            plng, plat = [float(x) for x in loc.split(",")]
            dx = (plng - lng) * 111000 * math.cos(math.radians(lat))
            dy = (plat - lat) * 111000
            dist = math.hypot(dx, dy)
            if dist > radius * 1.5:
                continue
            brg = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            d8 = DIRS[int((brg + 22.5) % 360 // 45)]
            out.append({"name": p.get("name"), "kw": kw, "dist": round(dist),
                        "dir": d8, "brg": round(brg, 1)})
        time.sleep(0.35)
    return out


def classify(pois):
    """把周边 POI 归入环境类属。"""
    res = {}
    for grp, kws in KW_GROUPS:
        hits = [p for p in pois if p["kw"] in kws]
        if hits:
            res[grp] = sorted(hits, key=lambda x: x["dist"])[:6]
    return res


def sixiang_view(groups):
    """按方位给出四神砂参照（文化描述）。"""
    lines = []
    idx = {"北": "玄武", "南": "朱雀", "东": "青龙", "西": "白虎"}
    for d, name in idx.items():
        hits = [p for p in sum(groups.values(), []) if p["dir"] == d]
        if hits:
            near = sorted(hits, key=lambda x: x["dist"])[0]
            lines.append((name, d, "近旁有「%s」（约 %d 米）" % (near["name"], near["dist"])))
        else:
            lines.append((name, d, "此方位近旁未见明显要素"))
    return lines


def shas_hint(groups):
    """按环境类属给出传统形煞提示（文化描述）。"""
    tips = []
    if "道路" in groups:
        for p in groups["道路"]:
            if p["dist"] < 200:
                tips.append(("路冲煞 / 反弓煞", "近旁有道路「%s」，距约 %d 米" % (p["name"], p["dist"]),
                             "传统以直冲、反弓为忌，讲求屈曲环抱；可与噪声、车流与安全视线一并考量。"))
                break
    if "水体" in groups:
        for p in groups["水体"]:
            if p["dist"] < 150:
                tips.append(("割脚水", "近旁水体「%s」距约 %d 米，贴邻而行" % (p["name"], p["dist"]),
                             "古人以水离宅过近为忌，所虑在地基与水患；现代对应低洼处防洪排涝问题。"))
                break
    if "宗教" in groups:
        for p in groups["宗教"]:
            tips.append(("独阴煞", "近旁有「%s」（%s），距约 %d 米" % (p["name"], p["kw"], p["dist"]),
                         "传统对此类场所取疏远之意，多与心理感受和生活习惯相关，非吉凶之断。"))
            break
    if "建筑" in groups:
        near = sorted(groups["建筑"], key=lambda x: x["dist"])[:2]
        if near:
            tips.append(("高耸逼压", "近旁有「%s」等建筑，距约 %d 米" % ("」「".join(x["name"] for x in near), near[0]["dist"]),
                         "古人讲求前后左右高低相宜，本质是一种对空间尺度与平衡的审美取向。"))
    if "医疗" in groups:
        for p in groups["医疗"]:
            tips.append(("味煞 / 独阴", "近旁有医疗场所「%s」，距约 %d 米" % (p["name"], p["dist"]),
                         "古人重「气」之清浊，与传统环境卫生观一脉相承。"))
            break
    return tips


def main():
    ap = argparse.ArgumentParser(description="环境形势分析（堪舆文化视角）")
    ap.add_argument("--address", default="", help="地址（需高德地理编码）")
    ap.add_argument("--lat", type=float, help="纬度")
    ap.add_argument("--lng", type=float, help="经度")
    ap.add_argument("--radius", type=int, default=1000, help="检索半径（米）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--offline-demo", action="store_true", help="离线演示（不联网）")
    a = ap.parse_args()

    if a.offline_demo:
        lng, lat, addr = 109.214, 34.372, "离线演示点位"
    elif a.lat is not None and a.lng is not None:
        lng, lat, addr = a.lng, a.lat, "坐标点位（%.4f, %.4f）" % (a.lat, a.lng)
    elif a.address:
        g = geocode(a.address)
        if not g:
            print("地理编码失败（请检查 AMAP_KEY 或地址）。可改用 --lat/--lng，或加 --offline-demo。", file=sys.stderr)
            sys.exit(1)
        lng, lat, addr = g
    else:
        ap.error("请用 --address 或 --lat/--lng 指定地点")

    if a.offline_demo:
        pois = []
    else:
        kws = [k for _, ks in KW_GROUPS for k in ks]
        pois = around(lng, lat, kws, a.radius)

    groups = classify(pois)
    six = sixiang_view(groups)
    tips = shas_hint(groups)

    if a.json:
        print(json.dumps({"center": {"lng": lng, "lat": lat, "addr": addr},
                          "radius": a.radius, "pois": pois, "groups": groups,
                          "sixiang": six, "shas": tips}, ensure_ascii=False, indent=1))
        return

    print("点位：%s（%.5f, %.5f）　检索半径 %d 米" % (addr, lng, lat, a.radius))
    print("周边要素命中 %d 处。" % len(pois))
    print()
    print("一、周边环境要素（按类属）")
    if not groups:
        print("  （未检索到要素，可增大半径或改用地标名称）")
    for grp, hits in groups.items():
        print("  【%s】" % grp)
        for p in hits:
            print("    - %s（%s，约 %d 米）" % (p["name"], p["dir"], p["dist"]))
    print()
    print("二、四神砂格局参照（传统描述）")
    for name, d, desc in six:
        print("  %s（%s）：%s" % (name, d, desc))
    print()
    print("三、传统形煞提示（文化描述）")
    if not tips:
        print("  （未触及相关民俗提示）")
    for name, ev, cu in tips:
        print("  【%s】%s" % (name, ev))
        print("      %s" % cu)
    print()
    print("说明：本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")


if __name__ == "__main__":
    main()
