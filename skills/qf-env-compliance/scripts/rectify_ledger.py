#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rectify_ledger.py — 环保督察整改台账与销号清单生成器（纯标准库）

功能：
  1. 读取问题清单 CSV（或内置示例），按问题等级推算整改时限与到期日；
  2. 计算剩余天数并标注逾期/临期/正常三档；
  3. 输出整改台账 CSV（含销号状态列）与 Markdown 销号清单；
  4. 支持按责任部门汇总统计；
  5. 支持批量更新销号状态（closed / verifying / open）。

输入 CSV 表头（顺序不限，须含前两列）：
    序号,问题描述,涉及点位,依据条款,问题等级,责任部门,责任岗位,发现日期
  问题等级取值：立行立改 / 限期整改 / 专项整治 / 系统治理
  发现日期格式：YYYY-MM-DD

用法示例：
    python3 rectify_ledger.py --in 问题清单.csv --out 整改台账.csv --md 销号清单.md
    python3 rectify_ledger.py --in 问题清单.csv --today 2026-09-20 --out 整改台账.csv
    python3 rectify_ledger.py --in 整改台账.csv --out 整改台账_更新.csv --set "1=closed,3=verifying"
    python3 rectify_ledger.py --demo --out 示例台账.csv --md 示例销号清单.md

退出码：0 正常；1 输入错误（缺列/日期非法）；2 参数错误（argparse）。
"""
import argparse
import csv
import sys
from datetime import date, datetime, timedelta

LEVEL_DAYS = {
    "立行立改": 3,
    "限期整改": 15,
    "专项整治": 30,
    "系统治理": 60,
}
STATUS_TEXT = {
    "open": "整改中",
    "verifying": "验收中",
    "closed": "已销号",
}
REQUIRED = ["序号", "问题描述", "问题等级", "责任部门", "发现日期"]

DEMO_ROWS = [
    {"序号": "1", "问题描述": "药剂与在线监测设备混堆，储存不规范", "涉及点位": "沙溪乡污水处理厂加药间",
     "依据条款": "《危险化学品安全管理条例》", "问题等级": "专项整治", "责任部门": "生产运行部",
     "责任岗位": "设备主管", "发现日期": "2026-09-01"},
    {"序号": "2", "问题描述": "总氮在线监测备机未经验收即使用", "涉及点位": "城区污水处理厂出水口",
     "依据条款": "HJ 355、HJ 212", "问题等级": "限期整改", "责任部门": "生产运行部",
     "责任岗位": "仪表工程师", "发现日期": "2026-09-05"},
    {"序号": "3", "问题描述": "危险废物暂存无专用贮存间", "涉及点位": "厂区东北角露天区",
     "依据条款": "GB 18597", "问题等级": "专项整治", "责任部门": "安全环保部",
     "责任岗位": "环保员", "发现日期": "2026-09-10"},
    {"序号": "4", "问题描述": "第三级管网未接入，存在应接未接", "涉及点位": "苏马荡片区",
     "依据条款": "长江经济带警示片整改要求", "问题等级": "系统治理", "责任部门": "工程管理部",
     "责任岗位": "项目经理", "发现日期": "2026-09-12"},
    {"序号": "5", "问题描述": "台账记录不规范，划改未签名", "涉及点位": "危废贮存间",
     "依据条款": "《固废法》", "问题等级": "立行立改", "责任部门": "安全环保部",
     "责任岗位": "环保员", "发现日期": "2026-09-18"},
]


def parse_date(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def read_input(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV 为空或无表头")
        headers = [h.strip() for h in reader.fieldnames]
        missing = [c for c in REQUIRED if c not in headers]
        if missing and "整改期限" not in headers:
            raise ValueError("缺少必需列：%s" % "、".join(missing))
        for raw in reader:
            rows.append({(k or "").strip(): (v or "").strip() for k, v in raw.items()})
    return rows


def build_ledger(rows, today):
    """为每行补充整改期限、到期日、剩余天数、预警、销号状态。"""
    out = []
    for r in rows:
        level = r.get("问题等级", "")
        days = LEVEL_DAYS.get(level)
        if days is None:
            raise ValueError("序号 %s 的问题等级非法：%s（应为 %s）"
                             % (r.get("序号", "?"), level, "/".join(LEVEL_DAYS)))
        try:
            d0 = parse_date(r["发现日期"])
        except (KeyError, ValueError):
            raise ValueError("序号 %s 的发现日期非法：%s（应为 YYYY-MM-DD）"
                             % (r.get("序号", "?"), r.get("发现日期", "")))
        due = d0 + timedelta(days=days)
        remain = (due - today).days
        if remain < 0:
            warn = "逾期 %d 天" % (-remain)
        elif remain <= 3:
            warn = "临期 %d 天" % remain
        else:
            warn = "正常"
        status = r.get("销号状态") or "open"
        item = dict(r)
        item["整改期限"] = "%d 日" % days
        item["到期日"] = due.isoformat()
        item["剩余天数"] = str(remain)
        item["预警"] = warn
        item["销号状态"] = STATUS_TEXT.get(status, status)
        item["_status_code"] = status
        out.append(item)
    return out


def write_csv(rows, path, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_md(rows, path):
    lines = ["# 环保督察整改销号清单", "", "| 序号 | 问题描述 | 等级 | 责任部门 | 到期日 | 预警 | 状态 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r.get("序号", ""), r.get("问题描述", ""), r.get("问题等级", ""),
            r.get("责任部门", ""), r.get("到期日", ""), r.get("预警", ""), r.get("销号状态", "")))
    over = [r for r in rows if str(r.get("预警", "")).startswith("逾期")]
    soon = [r for r in rows if str(r.get("预警", "")).startswith("临期")]
    lines += ["", "## 汇总", "",
              "- 条目总数：%d" % len(rows),
              "- 逾期：%d" % len(over),
              "- 临期：%d" % len(soon),
              "- 已销号：%d" % sum(1 for r in rows if r.get("销号状态") == STATUS_TEXT["closed"])]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def apply_status(rows, spec):
    """解析 '1=closed,3=verifying' 形式的批量状态更新。"""
    idx = {}
    for kv in spec.split(","):
        kv = kv.strip()
        if not kv:
            continue
        if "=" not in kv:
            raise ValueError("状态更新格式应为 序号=状态，收到：%s" % kv)
        k, v = kv.split("=", 1)
        if v not in STATUS_TEXT:
            raise ValueError("状态非法：%s（应为 %s）" % (v, "/".join(STATUS_TEXT)))
        idx[k.strip()] = v
    for r in rows:
        if r.get("序号", "").strip() in idx:
            r["销号状态"] = STATUS_TEXT[idx[r["序号"].strip()]]
            r["_status_code"] = idx[r["序号"].strip()]
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="环保督察整改台账与销号清单生成器")
    ap.add_argument("--in", dest="inp", help="问题清单 CSV 路径")
    ap.add_argument("--out", dest="out", required=True, help="台账 CSV 输出路径")
    ap.add_argument("--md", dest="md", help="销号清单 Markdown 输出路径")
    ap.add_argument("--today", dest="today", help="基准日期 YYYY-MM-DD，默认系统当日")
    ap.add_argument("--set", dest="set", help="批量更新销号状态，如 1=closed,3=verifying")
    ap.add_argument("--demo", action="store_true", help="使用内置示例数据（无需 --in）")
    args = ap.parse_args(argv)

    today = parse_date(args.today) if args.today else date.today()
    try:
        rows = DEMO_ROWS if args.demo else read_input(args.inp)
        ledger = build_ledger(rows, today)
        if args.set:
            ledger = apply_status(ledger, args.set)
    except ValueError as e:
        print("[ERROR] %s" % e, file=sys.stderr)
        return 1

    fields = ["序号", "问题描述", "涉及点位", "依据条款", "问题等级", "责任部门",
              "责任岗位", "发现日期", "整改期限", "到期日", "剩余天数", "预警", "销号状态"]
    write_csv(ledger, args.out, fields)
    if args.md:
        write_md(ledger, args.md)

    print("已生成台账：%s（%d 条）" % (args.out, len(ledger)))
    for r in ledger:
        print("  #%s %s | 到期 %s | %s | %s" % (
            r.get("序号"), r.get("问题等级"), r.get("到期日"), r.get("预警"), r.get("销号状态")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
