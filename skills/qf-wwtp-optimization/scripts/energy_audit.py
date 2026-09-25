#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曝气能耗核算与小工具

用法：
    python3 energy_audit.py --flow 20000 --do 2.0 --cod 350 --cod-out 50 --nh3 30 --nh3-out 5
    python3 energy_audit.py --file 运行数据.txt

计算：去除 COD 需氧、硝化需氧、反硝化产氧抵减、总需氧量 AOR、折算风量、比能耗。
"""
import argparse, sys

def calc(flow, cod_in, cod_out, nh3_in, nh3_out, no3_out=0.0, sote=0.25, depth=5.0, kwh_price=0.7):
    dcod = max(0.0, (cod_in - cod_out)) * flow / 1000.0          # kgCOD/d
    o2_cod = 0.48 * dcod                                          # kgO2/d
    dnh3 = max(0.0, (nh3_in - nh3_out)) * flow / 1000.0           # kgN/d
    o2_nit = 4.57 * dnh3
    o2_denit = 2.86 * (no3_out * flow / 1000.0) * 0.4             # 假设 40% 反硝化
    aor = o2_cod + o2_nit - o2_denit
    # 风量估算：AOR /(SOTE * 23.2% * 1.429 kg/m3 * 曝气效率系数)
    air = aor / max(0.01, (sote * 0.232 * 1.429 * 0.6))            # m3/d
    power = air * depth * 9.81 / 3600.0 / 0.6 * 0.001              # kW 估算（风机效率 60%）
    unit = power * 24.0 / flow if flow else 0.0                    # kWh/m3
    return {"去除COD(kg/d)": round(dcod, 1), "COD需氧(kgO2/d)": round(o2_cod, 1),
            "硝化需氧(kgO2/d)": round(o2_nit, 1), "反硝化抵减(kgO2/d)": round(o2_denit, 1),
            "总需氧量AOR(kgO2/d)": round(aor, 1), "估算风量(m3/d)": round(air),
            "估算曝气功率(kW)": round(power, 1), "吨水曝气电耗(kWh/m3)": round(unit, 3),
            "日电费(元)": round(power * 24 * kwh_price, 0)}

def main():
    ap = argparse.ArgumentParser(description="曝气能耗核算")
    ap.add_argument("--flow", type=float, help="设计水量 m3/d")
    ap.add_argument("--cod", type=float, default=350, help="进水 COD mg/L")
    ap.add_argument("--cod-out", type=float, default=50, help="出水 COD mg/L")
    ap.add_argument("--nh3", type=float, default=30, help="进水氨氮 mg/L")
    ap.add_argument("--nh3-out", type=float, default=5, help="出水氨氮 mg/L")
    ap.add_argument("--do", type=float, default=2.0, help="好氧区溶解氧 mg/L（记录用）")
    ap.add_argument("--sote", type=float, default=0.25, help="标准氧转移效率 0-1")
    ap.add_argument("--depth", type=float, default=5.0, help="曝气水深 m")
    a = ap.parse_args()
    if not a.flow:
        print("请提供 --flow 设计水量"); return 2
    r = calc(a.flow, a.cod, a.cod_out, a.nh3, a.nh3_out, sote=a.sote, depth=a.depth)
    print("=" * 50); print("曝气能耗核算"); print("=" * 50)
    for k, v in r.items():
        print("%-24s : %s" % (k, v))
    print("-" * 50)
    print("提示：AOR 为方案级估算；比能耗高于 0.35 kWh/m3 建议做节能诊断。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
