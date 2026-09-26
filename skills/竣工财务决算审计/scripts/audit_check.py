#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_check.py — 竣工财务决算审计数据校验器

对竣工财务决算的关键审计口径逐条判定：报表勾稽、四类投资归集、资产贯通、
核减率、超概算、尾工工程5%上限、建设管理费控制额、结余缺口。
金额单位统一为「万元」，输入文件中的数值须为万元。

用法:
  python3 scripts/audit_check.py --demo
  python3 scripts/audit_check.py --input 审计数据.json
  python3 scripts/audit_check.py --input 审计数据.json --json 校验报告.json
  python3 scripts/audit_check.py --input 审计数据.json --tolerance 0.01

退出码:
  0 = 全部通过
  1 = 存在须复核项
  2 = 输入文件不存在或格式错误
"""
import argparse
import json
import sys

TAIL_WORK_LIMIT = 0.05  # 尾工工程不超过批准概（预）算总投资的 5%


def demo_data():
    """内置某县市某乡、某镇污水厂改造工程公开口径（单位：万元）。"""
    return {
        "project": "某县市某乡、某镇污水厂改造工程（样例）",
        "overview": {"approve_amount": 1591.75, "actual_amount": 894.114112},
        "settlement": {
            "send_amount": 940.083367,
            "audited_amount": 894.114112,
            "items": [
                {"name": "建筑安装工程投资", "send": 667.863311, "audited": 628.614321},
                {"name": "设备、工器具", "send": 167.6796, "audited": 167.6796},
                {"name": "待摊投资", "send": 104.540456, "audited": 97.820191},
            ],
        },
        "table2": {
            "source_total": 894.128263,
            "use_total": 894.128263,
            "capital_construction_expenditure": 894.114112,
            "delivered_assets": 894.114112,
        },
        "expenditure": {
            "construction": 628.614321,
            "equipment": 167.6796,
            "overhead": 97.820191,
            "other": 0.0,
        },
        "table3": {"total": 894.114112},
        "tail_work": {"amount": 0.0},
        "mgmt_fee": {"base": 894.114112, "claimed": 18.433007, "standard": 17.882283},
        "funds": {"allocated": 711.680246, "gap": 182.433866, "gap_source": "项目公司自筹"},
    }


def g(d, *keys, default=0.0):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    return cur if isinstance(cur, (int, float)) else default


def build_checks(d, tol):
    t2 = d.get("table2", {})
    ex = d.get("expenditure", {})
    st = d.get("settlement", {})
    ov = d.get("overview", {})

    sum_ex = g(ex, "construction") + g(ex, "equipment") + g(ex, "overhead") + g(ex, "other")
    send = g(st, "send_amount")
    audited = g(st, "audited_amount")
    approve = g(ov, "approve_amount")
    actual = g(ov, "actual_amount")
    tail = g(d, "tail_work", "amount")
    mgmt_claimed = g(d, "mgmt_fee", "claimed")
    mgmt_std = g(d, "mgmt_fee", "standard")
    gap = g(d, "funds", "gap")
    gap_src = d.get("funds", {}).get("gap_source", "")

    checks = []  # (名称, 左值, 右值, 是否关键)

    # R1 表二表内平衡
    checks.append(("R1 决算表平衡：资金来源合计 = 资金占用合计",
                   g(t2, "source_total"), g(t2, "use_total"), True))
    # R2 概算对照
    checks.append(("R2 概算对照：概况表实际完成投资 = 决算表基本建设支出",
                   actual, g(t2, "capital_construction_expenditure"), True))
    # R3 四类投资归集
    checks.append(("R3 四类投资归集：建安+设备+待摊+其他 = 基本建设支出",
                   sum_ex, g(t2, "capital_construction_expenditure"), True))
    # R4 资产贯通
    checks.append(("R4 资产贯通：交付使用资产总表合计 = 决算表交付使用资产",
                   g(d, "table3", "total"), g(t2, "delivered_assets"), True))
    # R5 送审-审定核减
    checks.append(("R5 送审核定核对：审定投资 = 各分类审定之和",
                   audited,
                   sum(float(i.get("audited", 0)) for i in st.get("items", [])), True))

    results = []
    for name, a, b, key in checks:
        diff = round(a - b, 6)
        ok = abs(diff) <= tol
        results.append({"name": name, "left": round(a, 6), "right": round(b, 6),
                        "diff": diff, "ok": ok, "key": key})

    # R6 核减率
    reduce_rate = ((send - audited) / send * 100) if send else 0.0
    over_rate = ((actual - approve) / approve * 100) if approve else 0.0
    # R7 尾工5%上限
    tail_limit = approve * TAIL_WORK_LIMIT
    tail_ok = tail <= tail_limit + tol
    # R8 管理费控制额
    mgmt_ok = mgmt_claimed <= mgmt_std + tol
    # R9 缺口来源
    gap_ok = (abs(gap) <= tol) or bool(gap_src and gap_src.strip())

    metrics = {
        "reduce_rate": round(reduce_rate, 4),
        "over_approve_rate": round(over_rate, 4),
        "tail_work_amount": round(tail, 6),
        "tail_work_limit": round(tail_limit, 6),
        "tail_work_ok": tail_ok,
        "mgmt_fee_claimed": round(mgmt_claimed, 6),
        "mgmt_fee_standard": round(mgmt_std, 6),
        "mgmt_fee_ok": mgmt_ok,
        "gap": round(gap, 6),
        "gap_source": gap_src,
        "gap_ok": gap_ok,
    }
    return results, metrics


def run(d, tol):
    results, metrics = build_checks(d, tol)
    fails = [r for r in results if not r["ok"]]
    extra_fails = []
    if not metrics["tail_work_ok"]:
        extra_fails.append("R6 尾工工程超批准概算总投资5%上限")
    if not metrics["mgmt_fee_ok"]:
        extra_fails.append("R7 建设管理费超控制额")
    if not metrics["gap_ok"]:
        extra_fails.append("R8 资金缺口未写明填补来源")

    print("=" * 64)
    print(f"审计数据校验：{d.get('project', '(未命名项目)')}")
    print("=" * 64)
    for r in results:
        flag = "通过" if r["ok"] else "差额"
        print(f"[{flag}] {r['name']}")
        print(f"        左={r['left']:.6f}  右={r['right']:.6f}  差={r['diff']:.6f}")
    print("-" * 64)
    print(f"核减率           : {metrics['reduce_rate']:.4f}%")
    print(f"超概算率         : {metrics['over_approve_rate']:.4f}%")
    print(f"尾工工程         : {metrics['tail_work_amount']:.6f} 万 / 上限 {metrics['tail_work_limit']:.6f} 万  "
          f"{'通过' if metrics['tail_work_ok'] else '超限'}")
    print(f"建设管理费       : 申报 {metrics['mgmt_fee_claimed']:.6f} / 控制额 {metrics['mgmt_fee_standard']:.6f}  "
          f"{'通过' if metrics['mgmt_fee_ok'] else '超标准'}")
    print(f"结余/缺口        : {metrics['gap']:.6f} 万  来源：{metrics['gap_source'] or '未写明'}  "
          f"{'通过' if metrics['gap_ok'] else '未落实'}")
    print("-" * 64)
    total_fail = len(fails) + len(extra_fails)
    if total_fail == 0:
        print("结论：全部校验通过。")
    else:
        print(f"结论：{total_fail} 项须复核。")
        for e in extra_fails:
            print(f"  - {e}")
    return results, metrics, total_fail


def main():
    ap = argparse.ArgumentParser(description="竣工财务决算审计数据校验器")
    ap.add_argument("--input", help="审计数据 JSON 路径")
    ap.add_argument("--demo", action="store_true", help="使用内置样例数据")
    ap.add_argument("--json", help="校验报告 JSON 输出路径")
    ap.add_argument("--tolerance", type=float, default=0.01, help="勾稽容差，默认0.01")
    args = ap.parse_args()

    if args.demo:
        d = demo_data()
    elif args.input:
        try:
            with open(args.input, encoding="utf-8") as f:
                d = json.load(f)
        except FileNotFoundError:
            print(f"错误：输入文件不存在：{args.input}", file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError as e:
            print(f"错误：JSON 解析失败：{e}", file=sys.stderr)
            sys.exit(2)
    else:
        ap.error("须指定 --input 或 --demo")

    results, metrics, total_fail = run(d, args.tolerance)

    if args.json:
        payload = {"project": d.get("project", ""), "checks": results,
                   "metrics": metrics, "fail_count": total_fail}
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n校验报告已写出：{args.json}")

    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()
