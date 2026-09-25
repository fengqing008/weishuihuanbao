#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身价罗盘（Net Worth Compass）· 核心计算引擎
================================================
读取资产清单 → 分类归集 → 计算净资产 → 全国/省/市/县区四级分位定位
输出结构化 JSON，供 nwc_html.py 渲染 HTML 报告。

用法：
  python3 nwc_calc.py --input assets.json --out result.json
  python3 nwc_calc.py --demo --out result.json -o-owner "测试账号"

输入 JSON 格式：
{
  "owner": "王京图",
  "region_code": "610115",
  "scope": "家庭",           // 个人 / 家庭
  "assets": [
     {"name": "万科金域东郡房产", "value": 1096100},
     {"name": "汽车", "value": 50000, "category": "车辆"}
  ],
  "liabilities": [
     {"name": "房贷", "value": 0}
  ]
}
"""
import json
import math
import os
import sys
import argparse
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_PATH = os.path.join(BASE_DIR, "assets", "baseline.json")

# 标准资产大类（顺序即报告展示顺序）
CATS = ["房产", "车辆", "现金存款", "理财投资", "公积金", "股权出资", "应收借出", "其他资产"]

# 分类关键词（按优先级自上而下匹配，命中即归类）
CAT_RULES = [
    ("公积金",   ["公积金"]),
    ("房产",     ["房", "宅", "别墅", "公寓", "商铺", "写字楼", "不动产", "车位"]),
    ("车辆",     ["汽车", "轿车", "车", "摩托"]),
    ("股权出资", ["股权", "股份", "出资", "注册资本", "股份公司"]),
    ("应收借出", ["应收", "借出", "欠款", "债权", "押金"]),
    ("理财投资", ["理财", "基金", "股票", "债券", "证券", "信托", "保险", "黄金",
                  "贵金属", "投资", "国债", "外币"]),
    ("现金存款", ["存款", "活期", "定期", "现金", "银行", "储蓄", "支付宝", "微信",
                  "余额", "招行", "工行", "建行", "农行", "中行", "邮储", "零钱"]),
]


def norm_cdf(x):
    """标准正态分布 CDF"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p):
    """标准正态分布逆函数（Acklam 近似，精度 1e-9）"""
    if p <= 0 or p >= 1:
        raise ValueError("p must be in (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def classify(name, explicit=None):
    """把一项资产归入标准大类"""
    if explicit:
        for c in CATS:
            if explicit == c:
                return c
        # 兼容输入里的近义大类
        for c in CATS:
            if explicit in c or c in explicit:
                return c
    n = str(name or "")
    for cat, kws in CAT_RULES:
        for kw in kws:
            if kw in n:
                return cat
    return "其他资产"


def load_baseline():
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fit_sigma(median, anchor_threshold, anchor_top_pct):
    """用中位数 + 一个高端锚点 标定对数正态分布的 sigma"""
    z = norm_ppf(1 - anchor_top_pct / 100.0)
    return (math.log(anchor_threshold) - math.log(median)) / z


def percentile_national(nv, median, sigma, anchors):
    """
    返回全国口径下 ‘净资产 >= nv 的家庭占比(%)’，即前 N%。
    低段（<600万）用对数正态；高段（>=600万）用胡润锚点对数插值。
    """
    if nv <= 0:
        return 99.0
    a_sorted = sorted(anchors, key=lambda x: x["threshold"])
    top_anchor = a_sorted[0]  # 最小门槛=600万
    if nv < top_anchor["threshold"]:
        mu = math.log(median)
        z = (math.log(nv) - mu) / sigma
        return max(0.0001, min(99.99, 100.0 * (1.0 - norm_cdf(z))))
    # 高段：对数-对数插值
    pts = sorted([(math.log(a["threshold"]), math.log(a["top_pct"])) for a in anchors])
    lx = math.log(nv)
    if lx >= pts[-1][0]:  # 超过最高锚点（1亿）→ 幂律外推
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        k = (y1 - y0) / (x1 - x0)
        return math.exp(y1 + k * (lx - x1))
    for i in range(len(pts) - 1):
        if pts[i][0] <= lx <= pts[i + 1][0]:
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            t = (lx - x0) / (x1 - x0)
            return math.exp(y0 + t * (y1 - y0))
    return math.exp(pts[0][1])


def label_for(top_pct):
    if top_pct <= 0.05:
        return "全国顶尖 · 前 0.05%"
    if top_pct <= 0.1:
        return "前 0.1% · 超高净值"
    if top_pct <= 0.5:
        return "前 0.5%"
    if top_pct <= 1:
        return "前 1% · 富裕家庭"
    if top_pct <= 5:
        return "前 5% · 高收入"
    if top_pct <= 10:
        return "前 10% · 中上"
    if top_pct <= 25:
        return "前 25% · 中上"
    if top_pct <= 50:
        return "前 50% · 中位以上"
    return "后 50%"


def build_summary(assets, liabilities):
    by_cat = {c: 0.0 for c in CATS}
    detail = {c: [] for c in CATS}
    total_assets = 0.0
    for a in assets:
        cat = classify(a.get("name"), a.get("category"))
        v = float(a.get("value", 0) or 0)
        by_cat[cat] += v
        detail[cat].append({"name": a.get("name", ""), "value": v})
        total_assets += v
    total_liab = sum(float(x.get("value", 0) or 0) for x in (liabilities or []))
    nv = total_assets - total_liab
    return {
        "total_assets": total_assets,
        "total_liabilities": total_liab,
        "net_worth": nv,
        "by_category": {k: v for k, v in by_cat.items() if v > 0},
        "detail": {k: v for k, v in detail.items() if v},
    }


def compute(data):
    bl = load_baseline()
    nat = bl["national"]
    median = nat["median_net_worth"]
    anchors = nat["anchors"]
    top_anchor = sorted(anchors, key=lambda x: x["threshold"])[0]
    sigma = fit_sigma(median, top_anchor["threshold"], top_anchor["top_pct"])

    s = build_summary(data.get("assets", []), data.get("liabilities", []))
    nv = s["net_worth"]

    positions = []
    # 全国
    p_nat = percentile_national(nv, median, sigma, anchors)
    positions.append({
        "level": "全国", "region": "中国",
        "households": nat["households"],
        "top_pct": p_nat,
        "rank_households": round(p_nat / 100.0 * nat["households"]),
        "median": median,
        "label": label_for(p_nat),
    })
    # 省 / 市 / 县区
    region_chain = []
    rc = str(data.get("region_code", "")).strip()
    if rc:
        # 构造 省(前2位+0000) → 市(前4位+00) → 区县
        prov = rc[:2] + "0000"
        city = rc[:4] + "00"
        for code in [prov, city, rc]:
            if code in bl["regions"] and code not in [x[0] for x in region_chain]:
                region_chain.append((code, bl["regions"][code]))
    for code, r in region_chain:
        mu_r = math.log(median) + math.log(r["coef"])
        z = (math.log(nv) - mu_r) / sigma if nv > 0 else 99
        p = max(0.0001, min(99.99, 100.0 * (1.0 - norm_cdf(z))))
        positions.append({
            "level": "省" if code.endswith("0000") else ("市" if code.endswith("00") else "县区"),
            "region": r["name"], "code": code,
            "households": r["households"],
            "top_pct": p,
            "rank_households": round(p / 100.0 * r["households"]),
            "median": median * r["coef"],
            "label": label_for(p),
            "coef": r["coef"],
            "coef_source": r.get("coef_source", ""),
            "income": r.get("per_capita_income"),
        })

    result = {
        "meta": {
            "owner": data.get("owner", "未署名"),
            "scope": data.get("scope", "家庭"),
            "region_code": rc,
            "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "engine": "net-worth-compass v1.0",
            "as_of": bl["as_of"],
        },
        "summary": s,
        "positions": positions,
        "model": {
            "median_national": median,
            "sigma": round(sigma, 4),
            "anchor_threshold": top_anchor["threshold"],
            "anchor_top_pct": top_anchor["top_pct"],
        },
        "sources": [nat["households_source"], nat["median_source"]] +
                   [a["source"] for a in anchors] +
                   [r.get("coef_source", "") for _, r in region_chain if r.get("coef_source")],
        "disclaimer": bl["disclaimer"],
    }
    return result


DEMO = {
    "owner": "王京图（测试）",
    "region_code": "610115",
    "scope": "家庭",
    "assets": [
        {"name": "万科东望", "value": 1096100, "category": "房产"},
        {"name": "公积金", "value": 302000},
        {"name": "现金存款", "value": 331011, "category": "现金存款"},
        {"name": "汽车", "value": 50000},
        {"name": "支付宝", "value": 15000},
        {"name": "微信", "value": 5000},
        {"name": "股票", "value": 30000},
        {"name": "基金", "value": 20000},
    ],
    "liabilities": [],
}


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def validate_input(data):
    """输入校验：返回错误清单（空=通过）。防止字段不符被静默按 0 计算。"""
    errs = []
    if not isinstance(data, dict):
        return ["输入根节点必须是 JSON 对象"]
    assets = data.get("assets", [])
    if not isinstance(assets, list):
        errs.append("assets 必须是数组")
        assets = []
    for i, a in enumerate(assets):
        if not isinstance(a, dict):
            errs.append("assets[%d] 不是对象" % i)
            continue
        if not str(a.get("name", "")).strip():
            errs.append("assets[%d] 缺少 name（资产名称）" % i)
        if _num(a.get("value")) is None:
            errs.append("assets[%d]（%s）的 value 缺失或非数值" % (i, a.get("name", "?")))
    liabs = data.get("liabilities", []) or []
    if not isinstance(liabs, list):
        errs.append("liabilities 必须是数组")
        liabs = []
    for i, a in enumerate(liabs):
        if isinstance(a, dict) and _num(a.get("value")) is None:
            errs.append("liabilities[%d] 的 value 缺失或非数值" % i)
    if not assets and not liabs:
        errs.append("assets 与 liabilities 均为空，无可计算数据")
    return errs


def main():
    ap = argparse.ArgumentParser(description="身价罗盘 · 核心计算引擎")
    ap.add_argument("--input", help="资产清单 JSON 路径")
    ap.add_argument("--demo", action="store_true", help="使用内置测试数据")
    ap.add_argument("--out", default="nwc_result.json", help="输出 JSON 路径")
    ap.add_argument("--region", help="覆盖地区代码，如 610115")
    ap.add_argument("--owner", help="覆盖署名")
    args = ap.parse_args()

    if args.demo or not args.input:
        data = dict(DEMO)
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    if args.region:
        data["region_code"] = args.region
    if args.owner:
        data["owner"] = args.owner

    errs = validate_input(data)
    if errs:
        print("身价罗盘：输入校验未通过，已中止（避免生成无效分位结论）：", file=sys.stderr)
        for e in errs[:20]:
            print("  - " + e, file=sys.stderr)
        print("请修正 JSON 后重试（字段说明见 SKILL.md）。", file=sys.stderr)
        sys.exit(2)

    result = compute(data)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    s = result["summary"]
    print("== 身价罗盘计算结果 ==")
    print(f"署名: {result['meta']['owner']}  口径: {result['meta']['scope']}")
    print(f"总资产: {s['total_assets']:,.2f} 元")
    print(f"总负债: {s['total_liabilities']:,.2f} 元")
    print(f"净资产: {s['net_worth']:,.2f} 元")
    for p in result["positions"]:
        print(f"  [{p['level']}] {p['region']}: 约前 {p['top_pct']:.2f}%  "
              f"（约 {p['rank_households']:,} 户）  {p['label']}")
    print(f"输出: {args.out}")


if __name__ == "__main__":
    main()
