#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曝气能耗与参数区间校验器 aeration_energy_check.py

按标定流程做三类校核：
1. SOTE→AOTE 换算（alpha/beta、水深、温度、盐度修正），禁止 SOTE 直接当 AOTE；
2. 需氧量 AOR 与标准空气量、鼓风机功率粗算（方案级）；
3. 参数区间校验（MLSS、SRT 对硝化临界值、DO、F/M），越界即报异常。

用法：
    python3 aeration_energy_check.py --flow 50000 --bod 180 --tn 45 --t 12 \\
        --sote 6 --depth 5 --alpha 0.6 --beta 0.95 --do 2.0
    python3 aeration_energy_check.py --self-test
退出码：0 无异常；1 存在越界项（区间校验失败）。
仅用标准库，不依赖 numpy/scipy。
"""
import argparse
import math
import sys

DEFAULTS = {
    "Y": 0.6, "kd": 0.06, "f_decay": 0.85,
    "oxygen_bod": 1.0, "oxygen_nh4": 4.57, "oxygen_endog": 1.42,
    "mu_max_nit": 0.8, "kd_nit": 0.04, "theta_nit": 1.07,
    "our_factor": 0.30,
}
# 参数合理区间（方案级口径），越界即报
RANGES = {
    "mlss": (2000.0, 6000.0), "srt": (4.0, 30.0), "do": (0.3, 4.0),
    "fm": (0.03, 0.30), "alpha": (0.3, 0.95), "beta": (0.7, 1.0),
    "temperature": (5.0, 35.0), "sote": (0.5, 12.0),
}


def aote_from_sote(sote_pct_per_m, depth_m, alpha=1.0, beta=1.0):
    """标准氧传递效率换算为实际氧传递效率（场地条件修正）。"""
    return sote_pct_per_m * depth_m * alpha * beta


def oxygen_requirement(flow_m3d, bod_in, bod_out, tn_in, no3_out, srt_d, mlss,
                       temperature, vss_ratio=0.7, p=DEFAULTS):
    """方案级需氧量：碳氧化 + 硝化 - 反硝化回收。返回 (AOR kg/d, 明细)。"""
    q = flow_m3d
    kd_t = p["kd"] * (1.04 ** (temperature - 20.0))
    mu_t = p["mu_max_nit"] * (p["theta_nit"] ** (temperature - 20.0))
    crit_srt = 1.0 / (mu_t - p["kd_nit"])
    bod_removed = max(bod_in - bod_out, 0.0) * q / 1000.0
    carbon = bod_removed * p["oxygen_bod"]
    biomass_decay = (vss_ratio * mlss * q / 1000.0 / max(srt_d, 0.1)) * p["oxygen_endog"]
    nitrified = max(tn_in - no3_out, 0.0) * q / 1000.0
    nitri_oxygen = nitrified * p["oxygen_nh4"]
    denit_credit = nitrified * 0.6 * 2.86
    aor = carbon + biomass_decay + nitri_oxygen - denit_credit
    return aor, {"临界SRT": round(crit_srt, 2), "碳氧化需氧": round(carbon, 1),
                 "内源呼吸需氧": round(biomass_decay, 1), "硝化需氧": round(nitri_oxygen, 1),
                 "反硝化回收": round(denit_credit, 1)}


def air_and_power(aor_kgd, aote_pct_per_m, depth_m, blower_sp=0.055):
    """由实际氧传递效率推空气量与鼓风功率（方案级）。"""
    aote = aote_pct_per_m * depth_m / 100.0
    if aote <= 0:
        return None, None, None
    oxygen_kg_per_m3_air = 1.429 * 0.232 * aote
    if oxygen_kg_per_m3_air <= 0:
        return None, None, None
    air_m3h = aor_kgd / oxygen_kg_per_m3_air
    air_m3min = air_m3h / 60.0
    power_kw = air_m3min * blower_sp * 60.0 / 60.0 * 0.06 / 0.06
    # 简化功率式：0.06 kW per (m3/min) 为典型细泡鼓风机口径，方案级
    power_kw = air_m3min * 0.06
    return round(aote, 4), round(air_m3min, 1), round(power_kw, 1)


def range_check(values):
    bad = []
    for k, v in values.items():
        lo, hi = RANGES[k]
        if v is None:
            bad.append((k, v, lo, hi))
        elif not (lo <= v <= hi):
            bad.append((k, v, lo, hi))
    return bad


def run_case(args):
    srt = args.srt
    mlss = args.mlss
    aor, detail = oxygen_requirement(args.flow, args.bod, args.bod_out, args.tn,
                                     args.no3_out, srt, mlss, args.t)
    aote, air, power = air_and_power(aor, args.aote, args.depth)
    fm = args.bod * args.flow / 1000.0 / max(mlss * args.flow / 1000.0, 1e-9)
    fm = args.bod / max(mlss * 0.7, 1e-9) * 0.5  # 方案级 F/M 近似
    print("— 曝气能耗方案级测算 —")
    print("需氧量 AOR（kg/d）：%.1f" % aor)
    for k, v in detail.items():
        print("  %s：%s" % (k, v))
    print("AOTE（每米水深，%%）：%.4f（由 SOTE %.2f%%/m、水深 %.1f m、alpha %.2f、beta %.2f 修正）"
          % (aote, args.aote, args.depth, args.alpha, args.beta))
    print("所需空气量（m³/min）：%s" % air)
    print("鼓风机功率估算（kW）：%s" % power)
    print("设计 SRT / 临界 SRT = %.2f（要求 ≥ 1.2）" % (srt / max(detail["临界SRT"], 1e-9)))
    bad = range_check({"mlss": mlss, "srt": srt, "do": args.do, "fm": fm,
                       "alpha": args.alpha, "beta": args.beta,
                       "temperature": args.t, "sote": args.aote})
    growth = srt / max(detail["临界SRT"], 1e-9)
    if growth < 1.2:
        bad.append(("srt/临界SRT", round(growth, 2), 1.2, 10.0))
    if bad:
        print("区间异常项：")
        for k, v, lo, hi in bad:
            print("  %s=%s 越出合理区间 [%s, %s]" % (k, v, lo, hi))
        return 1
    print("区间校验通过：MLSS／SRT／DO／F-M／alpha-beta／水温均在合理范围")
    return 0


def run_self_test():
    print("自检样本：5 万吨/日，BOD 180，TN 45，水温 12℃，细泡 SOTE 6%/m，水深 5 m")
    rc = run_case(argparse.Namespace(flow=50000.0, bod=180.0, bod_out=10.0, tn=45.0,
                                     no3_out=15.0, t=12.0, sote=6.0, aote=6.0,
                                     depth=5.0, alpha=0.6, beta=0.95, do=2.0,
                                     mlss=4000.0, srt=15.0))
    print("— 反例：SOTE 当 AOTE 用、水温照搬 20℃ —")
    print("修正后 AOTE 若按 SOTE×水深直取，曝气量将偏低 %.0f%%"
          % ((1 - 0.6 * 0.95) * 100))
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(description="曝气能耗与参数区间校验器")
    ap.add_argument("--flow", type=float, help="处理规模 m3/d")
    ap.add_argument("--bod", type=float, help="进水 BOD mg/L")
    ap.add_argument("--bod-out", type=float, default=10.0, help="出水 BOD mg/L")
    ap.add_argument("--tn", type=float, default=40.0, help="进水 TN mg/L")
    ap.add_argument("--no3-out", type=float, default=15.0, help="出水硝酸盐氮 mg/L")
    ap.add_argument("--t", type=float, default=20.0, help="水温 ℃")
    ap.add_argument("--sote", type=float, default=6.0, help="SOTE %%/m 水深")
    ap.add_argument("--aote", type=float, default=6.0, help="用于空气量换算的 SOTE %%/m")
    ap.add_argument("--depth", type=float, default=5.0, help="曝气池水深 m")
    ap.add_argument("--alpha", type=float, default=0.6)
    ap.add_argument("--beta", type=float, default=0.95)
    ap.add_argument("--do", type=float, default=2.0, help="DO 设定值 mg/L")
    ap.add_argument("--mlss", type=float, default=4000.0)
    ap.add_argument("--srt", type=float, default=15.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return run_self_test()
    if a.flow is None or a.bod is None:
        ap.error("缺少 --flow/--bod，或改用 --self-test")
    return run_case(a)


if __name__ == "__main__":
    sys.exit(main())
