#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水污染虚拟治理成本法计算器
依据 GB/T 39793.2-2020《生态环境损害鉴定评估技术指南 基础方法 第2部分：水污染虚拟治理成本法》
公式：D = E × C × γ，γ = α × τ × ω

用法示例：
  python3 virtual_cost_calculator.py --E 142420 --C 0.634 --alpha 1 --kappa 3.27 --omega 1.5
  python3 virtual_cost_calculator.py --E 142420 --C 0.634 --alpha 1 --Z 21.36 --B 5 --omega 1.5
  python3 virtual_cost_calculator.py --E 10000 --C 0.9 --alpha 1.5 --tau 1.5 --omega 2 --json
"""
import argparse
import json
import sys


def tau_from_kappa(kappa):
    """超标系数定档（表3）。kappa<=0 视为未超标，取 1。"""
    if kappa is None:
        return None
    if kappa <= 0:
        return 1.0
    if kappa <= 10:
        return 1.25
    if kappa <= 100:
        return 1.5
    if kappa <= 1000:
        return 1.75
    return 2.0


def kappa_from(Z, B):
    """最大超标倍数 κ = (Z - B) / B"""
    if B in (None, 0):
        raise ValueError("排放标准限值 B 不能为 0")
    return (Z - B) / B


def build_parser():
    p = argparse.ArgumentParser(
        description="水污染虚拟治理成本法计算器（GB/T 39793.2-2020） D = E × C × γ, γ = α × τ × ω")
    p.add_argument("--E", type=float, required=True, help="排放数量（t 或 m3）")
    p.add_argument("--C", type=float, required=True, help="单位治理成本（元/t 或 元/m3）")
    p.add_argument("--alpha", type=float, default=None, help="危害系数 α（表1/表2）")
    p.add_argument("--omega", type=float, default=None, help="环境功能系数 ω（表5）")
    p.add_argument("--kappa", type=float, default=None, help="最大超标倍数 κ")
    p.add_argument("--tau", type=float, default=None, help="超标系数 τ（与 --kappa/--Z 二选一）")
    p.add_argument("--Z", type=float, default=None, help="污染物实测浓度（mg/L，用于计算 κ）")
    p.add_argument("--B", type=float, default=None, help="排放标准限值（mg/L，用于计算 κ）")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.alpha is None:
        print("[错误] 必须提供危害系数 α（--alpha），取值见 GB/T 39793.2-2020 表1/表2。", file=sys.stderr)
        return 2
    if args.omega is None:
        print("[错误] 必须提供环境功能系数 ω（--omega），取值见 GB/T 39793.2-2020 表5。", file=sys.stderr)
        return 2

    # 超标系数：优先显式 --tau；否则由 κ 或 Z/B 推出
    kappa = args.kappa
    if kappa is None and args.Z is not None and args.B is not None:
        kappa = kappa_from(args.Z, args.B)

    if args.tau is not None:
        tau = args.tau
        tau_src = "用户给定"
    elif kappa is not None:
        tau = tau_from_kappa(kappa)
        tau_src = "按最大超标倍数 κ 定档"
    else:
        print("[错误] 需提供 --tau，或 --kappa，或同时提供 --Z 与 --B。", file=sys.stderr)
        return 2

    gamma = args.alpha * tau * args.omega
    D = args.E * args.C * gamma

    if args.json:
        out = {
            "E": args.E, "C": args.C, "alpha": args.alpha, "tau": tau,
            "omega": args.omega, "kappa": kappa, "gamma": gamma, "D": D,
            "D_wan": D / 10000.0,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print("== 水污染虚拟治理成本法计算（GB/T 39793.2-2020） ==")
    print("公式：D = E × C × γ，γ = α × τ × ω")
    print("-" * 44)
    print("E（排放数量）      = %s" % fmt(args.E))
    print("C（单位治理成本）  = %s" % fmt(args.C))
    print("α（危害系数）      = %s" % fmt(args.alpha))
    if kappa is not None:
        print("κ（最大超标倍数）  = %s" % fmt(kappa))
    print("τ（超标系数）      = %s  [%s]" % (fmt(tau), tau_src))
    print("ω（环境功能系数）  = %s" % fmt(args.omega))
    print("γ（调整系数）      = α×τ×ω = %s × %s × %s = %s" % (
        fmt(args.alpha), fmt(tau), fmt(args.omega), fmt(gamma)))
    print("-" * 44)
    print("D（损害数额）      = E × C × γ = %s × %s × %s = %s 元" % (
        fmt(args.E), fmt(args.C), fmt(gamma), fmt(D)))
    print("                   ≈ %s 万元" % fmt(D / 10000.0))
    print("-" * 44)
    print("提示：α、τ、ω 的取值须落在 GB/T 39793.2-2020 表1/表3/表5 范围内，并在报告中写明取值依据。")
    return 0


def fmt(x):
    if x is None:
        return "-"
    if abs(x - round(x)) < 1e-9:
        return "{:,}".format(int(round(x)))
    return "{:,.4f}".format(x).rstrip("0").rstrip(".")


if __name__ == "__main__":
    sys.exit(main())
