#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
activated_sludge_calculator.py — 活性污泥工艺计算器 v1.0
============================================================
用途：ASM2d 简化动力学的活性污泥工艺设计/校核计算，本地化自
      puran-water/aerobic-design-mcp（已归档）的核心公式。
能力：工艺选型判断 + 物料平衡（污泥产量/氮同化/硝化量）+ SRT 临界值
      + 好氧/缺氧体积 + MBR 膜面积 + 需氧量(AOR)。
用法：
  python3 activated_sludge_calculator.py \
      --Q 20000 --cod_in 500 --cod_eff 50 --tkn_in 45 --nh4_eff 1 \
      --tp_in 7 --tp_eff 0.5 --tss_in 200 --temp 12 --mlss 6000 --srt 15
作者：ima.copilot 小邦 / v1.0 2026-09-05
"""

import argparse
import math
import sys


def temp_factor(theta, temp):
    """温度校正：k_T = k_20 × θ^(T−20)，T_ref=20℃"""
    return theta ** (temp - 20)


def calc_y_obs(Y, b_20, theta_b, temp, srt):
    """观测产率：Y_obs = Y / (1 + b_T·SRT)"""
    b_T = b_20 * temp_factor(theta_b, temp)
    return Y / (1 + b_T * srt)


def calc_mass_balance(Q, cod_in, cod_eff, tkn_in, nh4_eff, tss_in, temp, srt):
    """物料平衡：污泥产量、氮同化、硝化量"""
    # 异养菌参数（design set, 20℃）
    Y_H = 0.625          # gCOD/gCOD
    b_H_20 = 0.12        # d^-1
    theta_b = 1.04
    # 自养菌参数
    Y_A = 0.24
    b_A_20 = 0.05

    cod_removed = max(cod_in - cod_eff, 0) * Q / 1000.0   # kg COD/d

    y_obs_H = calc_y_obs(Y_H, b_H_20, theta_b, temp, srt)
    y_obs_A = calc_y_obs(Y_A, b_A_20, theta_b, temp, srt)

    # 异养污泥产量
    P_XH_COD = cod_removed * y_obs_H          # kg COD/d
    P_XH_VSS = P_XH_COD / 1.48                # kg VSS/d
    P_XH_TSS = P_XH_VSS / 0.85                # kg TSS/d (VSS/TSS=0.85)

    # 自养菌（硝化菌）产量
    i_NBM = 0.10 if srt > 20 else 0.12         # 氮同化系数
    # 先估算氮同化（用异养 TSS 近似，迭代一次）
    N_assim_est = P_XH_TSS * i_NBM / (Q / 1000.0)   # mg/L（近似）
    N_nitrified = max(tkn_in - nh4_eff - N_assim_est, 0)  # mg/L
    P_XA_COD = N_nitrified * Q / 1000.0 * y_obs_A
    P_XA_VSS = P_XA_COD / 1.48
    P_XA_TSS = P_XA_VSS / 0.85

    # 惰性 TSS
    TSS_inert = tss_in * Q / 1000.0 * 0.15    # kg TSS/d

    TSS_biomass = P_XH_TSS + P_XA_TSS
    TSS_total = TSS_biomass + TSS_inert       # kg TSS/d

    # 氮同化（用总 TSS）
    N_assim = TSS_total * i_NBM / (Q / 1000.0)   # mg/L
    N_nitrified = max(tkn_in - nh4_eff - N_assim, 0)  # mg/L

    return {
        "cod_removed_kg_d": cod_removed,
        "y_obs_H": y_obs_H,
        "y_obs_A": y_obs_A,
        "P_XH_TSS": P_XH_TSS,
        "P_XA_TSS": P_XA_TSS,
        "TSS_inert": TSS_inert,
        "TSS_total": TSS_total,
        "N_assim": N_assim,
        "N_nitrified": N_nitrified,
    }


def calc_nitrification_srt_crit(temp, nh4, do):
    """硝化菌临界 SRT（washout）：SRT_crit = 1/(μ_A,eff − b_A,T)"""
    mu_A_20 = 0.90        # d^-1
    theta_mu = 1.09
    b_A_20 = 0.17         # d^-1
    theta_b = 1.029
    K_NH4 = 0.5           # mg/L
    K_DO = 0.5            # mg/L

    mu_A_T = mu_A_20 * temp_factor(theta_mu, temp)
    b_A_T = b_A_20 * temp_factor(theta_b, temp)
    mu_eff = mu_A_T * nh4 / (K_NH4 + nh4) * do / (K_DO + do)

    if mu_eff <= b_A_T:
        return float("inf")   # 无法维持硝化
    return 1.0 / (mu_eff - b_A_T)


def calc_sdnr(rbcod_frac, temp, f_m):
    """SDNR 反硝化速率：SDNR = (b0 + b1·ln(F/M)) × 1.09^(T−20)"""
    table = [
        (0.10, 0.186, 0.078), (0.20, 0.213, 0.118), (0.30, 0.235, 0.141),
        (0.40, 0.242, 0.152), (0.50, 0.250, 0.160),
    ]
    b0, b1 = 0.235, 0.141   # 表外默认
    for frac, _b0, _b1 in table:
        if rbcod_frac <= frac:
            b0, b1 = _b0, _b1
            break
    if f_m <= 0:
        return 0.0
    return (b0 + b1 * math.log(f_m)) * temp_factor(1.09, temp)


def calc_oxygen_demand(cod_removed_kg_d, y_obs_H, n_nitrified_mgL, Q, no3_removed_mgL):
    """需氧量 AOR = O2_COD + O2_nit − O2_credit"""
    O2_COD = cod_removed_kg_d * (1 - 1.42 * y_obs_H)      # kg O2/d
    O2_nit = n_nitrified_mgL * Q / 1000.0 * 4.57          # kg O2/d
    O2_credit = no3_removed_mgL * Q / 1000.0 * 2.86       # kg O2/d
    AOR = O2_COD + O2_nit - O2_credit
    return {"O2_COD": O2_COD, "O2_nit": O2_nit, "O2_credit": O2_credit, "AOR": AOR}


def calc_mbr_area(Q, flux_lmh=18, fouling_factor=1.8):
    """MBR 膜面积：design_flux = flux/fouling，area = Q×1000/(design_flux×24)"""
    design_flux = flux_lmh / fouling_factor
    area = Q * 1000.0 / (design_flux * 24.0)
    return {"design_flux_lmh": design_flux, "membrane_area_m2": area}


def select_flowsheet(tp_target, tn_target):
    """工艺选型判据（简化，按出水目标严格度）"""
    if tp_target < 1.0:
        return "A2O（EBPR）或化学除磷（TP 目标 <1 mg/L 需强化除磷）"
    if tn_target < 10.0:
        return "MLE_POST（后置缺氧）或外加碳源（TN 目标 <10 mg/L 需深度脱氮）"
    return "MLE（最简方案）"


def main():
    ap = argparse.ArgumentParser(description="活性污泥工艺计算器 v1.0")
    ap.add_argument("--Q", type=float, default=20000, help="进水流量 m³/d")
    ap.add_argument("--cod_in", type=float, default=500, help="进水 COD mg/L")
    ap.add_argument("--cod_eff", type=float, default=50, help="出水 COD mg/L")
    ap.add_argument("--tkn_in", type=float, default=45, help="进水 TKN mg/L")
    ap.add_argument("--nh4_eff", type=float, default=1, help="出水 NH4-N mg/L")
    ap.add_argument("--tp_in", type=float, default=7, help="进水 TP mg/L")
    ap.add_argument("--tp_eff", type=float, default=0.5, help="出水 TP mg/L")
    ap.add_argument("--tss_in", type=float, default=200, help="进水 TSS mg/L")
    ap.add_argument("--temp", type=float, default=12, help="水温 ℃")
    ap.add_argument("--mlss", type=float, default=6000, help="MLSS mg/L")
    ap.add_argument("--srt", type=float, default=15, help="设计 SRT d")
    ap.add_argument("--do", type=float, default=2, help="好氧区 DO mg/L")
    ap.add_argument("--tn_target", type=float, default=15, help="出水 TN 目标 mg/L")
    ap.add_argument("--tp_target", type=float, default=0.5, help="出水 TP 目标 mg/L")
    ap.add_argument("--flux_lmh", type=float, default=18, help="MBR 膜通量 LMH")
    ap.add_argument("--fouling_factor", type=float, default=1.8, help="膜污染系数")
    args = ap.parse_args()

    print("=" * 60)
    print(f"活性污泥工艺计算器 v1.0  (T={args.temp}℃, SRT={args.srt}d, MLSS={args.mlss}mg/L)")
    print("=" * 60)

    mb = calc_mass_balance(args.Q, args.cod_in, args.cod_eff, args.tkn_in,
                           args.nh4_eff, args.tss_in, args.temp, args.srt)
    print("\n[1] 物料平衡")
    print(f"  去除 COD = {mb['cod_removed_kg_d']:.1f} kg/d")
    print(f"  观测产率 Y_obs_H = {mb['y_obs_H']:.4f}, Y_obs_A = {mb['y_obs_A']:.4f}")
    print(f"  污泥产量：异养 {mb['P_XH_TSS']:.1f} + 自养 {mb['P_XA_TSS']:.2f} + 惰性 {mb['TSS_inert']:.1f} = {mb['TSS_total']:.1f} kg TSS/d")
    print(f"  氮同化 N_assim = {mb['N_assim']:.2f} mg/L，硝化量 N_nitrified = {mb['N_nitrified']:.2f} mg/L")

    srt_crit = calc_nitrification_srt_crit(args.temp, args.nh4_eff, args.do)
    print("\n[2] 硝化菌临界 SRT")
    if srt_crit == float("inf"):
        print(f"  临界 SRT = ∞（当前温度/DO 下硝化菌无法维持）")
    else:
        print(f"  SRT_crit = {srt_crit:.2f} d（设计 SRT {args.srt}d {'≥' if args.srt >= srt_crit else '<'} 临界，"
              f"{'安全' if args.srt >= srt_crit * 1.2 else '安全系数不足，建议 SRT ≥ ' + format(srt_crit * 1.2, '.1f') + 'd'}）")

    print("\n[3] 反硝化 SDNR（rbCOD=0.3 参考，F/M=0.24 收敛）")
    sdnr = calc_sdnr(0.30, args.temp, 0.24)
    print(f"  SDNR = {sdnr:.3f} kgNO3-N/kgMLVSS/d @ {args.temp}℃")

    # 内回流 NO3（MLE IR=4.0）
    ir = 4.0
    no3_recycled = mb["N_nitrified"] * ir / (1 + ir)
    # 反硝化去除量（简化：假设前置缺氧去除内回流 NO3）
    no3_removed = no3_recycled
    od = calc_oxygen_demand(mb["cod_removed_kg_d"], mb["y_obs_H"],
                            mb["N_nitrified"], args.Q, no3_removed)
    print("\n[4] 需氧量")
    print(f"  O2_COD = {od['O2_COD']:.1f} kg/d, O2_nit = {od['O2_nit']:.1f} kg/d, "
          f"O2_credit = {od['O2_credit']:.1f} kg/d")
    print(f"  AOR = {od['AOR']:.1f} kg O2/d")

    mbr = calc_mbr_area(args.Q, args.flux_lmh, args.fouling_factor)
    print("\n[5] MBR 膜面积")
    print(f"  设计通量 = {args.flux_lmh}/{args.fouling_factor} = {mbr['design_flux_lmh']:.1f} LMH")
    print(f"  膜面积 = {mbr['membrane_area_m2']:.0f} m²")

    flowsheet = select_flowsheet(args.tp_target, args.tn_target)
    print("\n[6] 工艺选型建议")
    print(f"  {flowsheet}")

    print("\n" + "=" * 60)
    print("注：结果为 ASM2d 简化估算，正式设计须结合水质实测与生物相校核。")
    print("=" * 60)


if __name__ == "__main__":
    main()
