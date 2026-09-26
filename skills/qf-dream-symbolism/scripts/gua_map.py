# -*- coding: utf-8 -*-
"""gua_map.py — 易经卦象查询与起卦（文化解读视角）

支持：时间起卦（梅花易数法）、数字起卦、卦名直查、全卦列表。
用法:
  python3 gua_map.py --time "2026-09-26 12:30"
  python3 gua_map.py --num 7 5
  python3 gua_map.py --name 泰
  python3 gua_map.py --list
"""
import os
import sys
import json
import argparse
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "assets", "gua_map.json")

NUM2GUA = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}
GUA2NUM = {v: k for k, v in NUM2GUA.items()}

# (上卦, 下卦) -> 卦名
TABLE = {
    ("乾", "乾"): "乾", ("乾", "兑"): "履", ("乾", "离"): "同人", ("乾", "震"): "无妄",
    ("乾", "巽"): "姤", ("乾", "坎"): "讼", ("乾", "艮"): "遁", ("乾", "坤"): "否",
    ("兑", "乾"): "夬", ("兑", "兑"): "兑", ("兑", "离"): "革", ("兑", "震"): "随",
    ("兑", "巽"): "大过", ("兑", "坎"): "困", ("兑", "艮"): "咸", ("兑", "坤"): "萃",
    ("离", "乾"): "大有", ("离", "兑"): "睽", ("离", "离"): "离", ("离", "震"): "噬嗑",
    ("离", "巽"): "鼎", ("离", "坎"): "未济", ("离", "艮"): "旅", ("离", "坤"): "晋",
    ("震", "乾"): "大壮", ("震", "兑"): "归妹", ("震", "离"): "丰", ("震", "震"): "震",
    ("震", "巽"): "恒", ("震", "坎"): "解", ("震", "艮"): "小过", ("震", "坤"): "豫",
    ("巽", "乾"): "小畜", ("巽", "兑"): "中孚", ("巽", "离"): "家人", ("巽", "震"): "益",
    ("巽", "巽"): "巽", ("巽", "坎"): "涣", ("巽", "艮"): "渐", ("巽", "坤"): "观",
    ("坎", "乾"): "需", ("坎", "兑"): "节", ("坎", "离"): "既济", ("坎", "震"): "屯",
    ("坎", "巽"): "井", ("坎", "坎"): "坎", ("坎", "艮"): "蹇", ("坎", "坤"): "比",
    ("艮", "乾"): "大畜", ("艮", "兑"): "损", ("艮", "离"): "贲", ("艮", "震"): "颐",
    ("艮", "巽"): "蛊", ("艮", "坎"): "蒙", ("艮", "艮"): "艮", ("艮", "坤"): "剥",
    ("坤", "乾"): "泰", ("坤", "兑"): "临", ("坤", "离"): "明夷", ("坤", "震"): "复",
    ("坤", "巽"): "升", ("坤", "坎"): "师", ("坤", "艮"): "谦", ("坤", "坤"): "坤",
}


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def by_name(data, name):
    name = name.replace("卦", "")
    for g in data["guas"]:
        if g["name"] == name:
            return g
    return None


def cast_from_time(dt):
    """梅花易数时间起卦：上卦=(年+月+日)%8，下卦=(年+月+日+时)%8，动爻=(年+月+日+时)%6"""
    y, m, d, h = dt.year, dt.month, dt.day, dt.hour
    up = (y + m + d) % 8 or 8
    low = (y + m + d + h) % 8 or 8
    move = (y + m + d + h) % 6 or 6
    return NUM2GUA[up], NUM2GUA[low], move


def cast_from_num(a, b, c=None):
    up = a % 8 or 8
    low = b % 8 or 8
    move = ((c if c is not None else a + b) % 6) or 6
    return NUM2GUA[up], NUM2GUA[low], move


def show(data, gua, extra=""):
    print("【%s】%s" % (gua["name"], gua["xiang"]))
    print("  卦辞：%s" % gua["ci"])
    print("  象义：%s" % gua["symbol"])
    if extra:
        print("  " + extra)
    print()


def main():
    ap = argparse.ArgumentParser(description="易经卦象查询与起卦（文化解读视角）")
    ap.add_argument("--time", default="", help="时间起卦，如 '2026-09-26 12:30'")
    ap.add_argument("--num", nargs="+", type=int, help="数字起卦，1-3 个数")
    ap.add_argument("--name", default="", help="按卦名查询")
    ap.add_argument("--list", action="store_true", help="列出六十四卦")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    data = load()

    if a.list:
        for g in data["guas"]:
            print("%2d. %-3s %-10s %s" % (g["no"], g["name"], g["xiang"], g["symbol"]))
        print("\n共 %d 卦（《周易》六十四卦）" % data["count"])
        return

    if a.name:
        g = by_name(data, a.name)
        if not g:
            print("未找到卦：%s" % a.name, file=sys.stderr)
            sys.exit(1)
        if a.json:
            print(json.dumps(g, ensure_ascii=False, indent=1))
        else:
            show(data, g)
        return

    if a.time:
        try:
            dt = datetime.strptime(a.time.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            dt = datetime.strptime(a.time.strip()[:10], "%Y-%m-%d")
        up, low, move = cast_from_time(dt)
    elif a.num:
        nums = a.num
        up, low, move = cast_from_num(nums[0], nums[1] if len(nums) > 1 else nums[0],
                                      nums[2] if len(nums) > 2 else None)
    else:
        ap.error("请用 --time / --num / --name / --list 之一")

    gname = TABLE.get((up, low))
    if not gname:
        print("组合无法识别：%s上%s下" % (up, low), file=sys.stderr)
        sys.exit(1)
    g = by_name(data, gname)
    if a.json:
        print(json.dumps({"up": up, "low": low, "move": move, "gua": g},
                         ensure_ascii=False, indent=1))
        return
    print("起卦：%s上 %s下 → 第%d爻动" % (up, low, move))
    print()
    show(data, g, extra="提示：第 %d 爻为动爻，可参看该爻位所主之事。" % move)
    print("说明：本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据。")


if __name__ == "__main__":
    main()
