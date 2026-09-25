#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板风格流程图 · 工程量核对（主图）
用法：python3 sop_flowchart_total.py --project 示例PPP --out 工程量核对.png
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flowchart_kit import (init, save, title_block, start_node, end_node,
                           rbox, diamond, note, path, label, line, dot, rrect, poly,
                           RES_F, RES_E, WARN_F, WARN_E, ACT_E, EDGE, DEC_F, DEC_E)

ap = argparse.ArgumentParser(description='模板风格流程图 · 工程量核对')
ap.add_argument('--project', default='示例PPP', help='项目名称前缀')
ap.add_argument('--subtitle', default='适用：施工单位 ／ 监理单位 ／ 审计单位 ／ 建设单位')
ap.add_argument('--out', default='工程量核对_流程图.png')
A = ap.parse_args()

init()
title_block(f'{A.project}项目工程结算 · 工程量核对 SOP', A.subtitle, fs_title=25)

CX = 11.0
COL = [4.0, 11.0, 18.0]          # 管网 / 接户管 / 站点

# ===== 起止 + 总原则 =====
start_node(CX, 23.1)
path([(CX, 22.8), (CX, 22.475)])
rbox(CX, 22.0, 12.8, 0.95, '总原则：所有工程量以签字盖章的竣工图为基准', fs=15, bold=True)
path([(CX, 21.525), (CX, 21.3)])

# ===== 部位判断 + 三列分流 =====
diamond(CX, 20.5, 6.6, 1.6, '核对对象属于哪个部位？', fs=13.5)
tags = ['管网部分', '接户管', '站点部分']
for cx in COL:
    path([(CX, 19.7), (CX, 19.0), (cx, 19.0), (cx, 18.85)])
# 分支标签上移，与水平连线留出安全间距；中列（直下）标签置竖线右侧
label((CX + COL[0]) / 2, 19.32, tags[0], fs=12)
label(COL[1] + 1.25, 19.32, tags[1], fs=12)
label((CX + COL[2]) / 2, 19.32, tags[2], fs=12)

# ===== 三列：动作 =====
rbox(COL[0], 18.15, 5.6, 1.3, '按竣工图逐项比对\n管长 · 检查井 · 管径\n基础形式 · 接口做法', fs=12)
rbox(COL[1], 18.15, 5.6, 1.3, '按三方现场复核\n确认文件为准\n（建设＋监理＋施工）', fs=12)
rbox(COL[2], 18.15, 5.6, 1.3, '按竣工图核查完整性\n建构筑物 · 工艺设备\n电气 · 自控 · 给排水', fs=12)
for cx in COL:
    path([(cx, 17.45), (cx, 17.2)])

# ===== 三列：判断 =====
diamond(COL[0], 16.45, 4.6, 1.5, '与竣工图\n是否一致？', fs=12)
diamond(COL[1], 16.45, 4.6, 1.5, '与支管核定\n文件是否一致？', fs=12)
diamond(COL[2], 16.45, 4.6, 1.5, '与竣工图是否一致？\n有无缺失？', fs=11.5)

# ===== 是 / 否（标签置于折线外侧上方，明确避让） =====
YN, DX = 14.35, 1.6
for cx in COL:
    path([(cx, 15.7), (cx, 15.15), (cx - DX, 15.15), (cx - DX, 14.8)])
    path([(cx, 15.7), (cx, 15.15), (cx + DX, 15.15), (cx + DX, 14.8)])
    label(cx - DX / 2, 15.33, '是', fs=11)
    label(cx + DX / 2, 15.33, '否', fs=11)

rbox(COL[0] - DX, YN, 2.2, 0.78, '按图计量', fc=RES_F, ec=RES_E, fs=13.5)
rbox(COL[0] + DX, YN, 2.2, 0.78, '四方签认', fc=WARN_F, ec=WARN_E, fs=13.5)
rbox(COL[1] - DX, YN, 2.2, 0.78, '按量计量', fc=RES_F, ec=RES_E, fs=13.5)
rbox(COL[1] + DX, YN, 2.2, 0.78, '三方复核', fc=WARN_F, ec=WARN_E, fs=13.5)
rbox(COL[2] - DX, YN, 2.2, 0.78, '按图计量', fc=RES_F, ec=RES_E, fs=13.5)
rbox(COL[2] + DX, YN, 2.2, 0.78, '图纸会审', fc=WARN_F, ec=WARN_E, fs=13.5)

# ===== 阶梯式汇聚 =====
Y1, Y2 = 13.72, 13.45
for cx in COL:
    line([(cx - DX, 13.96), (cx - DX, Y1)])
    line([(cx + DX, 13.96), (cx + DX, Y1)])
    line([(cx - DX, Y1), (cx + DX, Y1)])
    dot(cx, Y1, 0.055)
    line([(cx, Y1), (cx, Y2)])
line([(COL[0], Y2), (COL[2], Y2)])
dot(CX, Y2, 0.07)
path([(CX, Y2), (CX, 12.875)])

rbox(CX, 12.4, 13.6, 0.95, '签认结果汇总 → 形成结算工程量计量依据', fs=14, ec=ACT_E, bold=True)

# ===== 后续单列 =====
steps = [
    (11.2, '结算书编制：第一部分（合同内）＋ 第二部分（合同外）'),
    (10.05, '材料调差：合同内主材按基准价 ／ 签证内容按当期价'),
    (8.9, '结算公式：分部分项费 ＋ 措施项目费 ＋ 规费税金'),
    (7.75, '签字盖章齐备 → 四级组卷归档（GB/T 50328）'),
    (6.6, '报送定案：施工单位 → 建设单位 → 审计单位 → 定案表'),
]
path([(CX, 11.925), (CX, 11.65)])
for i, (y, t) in enumerate(steps):
    rbox(CX, y, 14.8, 0.9, t, fs=12.5)
    if i < len(steps) - 1:
        path([(CX, y - 0.45), (CX, steps[i + 1][0] + 0.45)])

# ===== 终止 =====
path([(CX, 6.15), (CX, 6.0)])
end_node(CX, 5.7)

# ===== 关键控制点（折角注释） =====
note(CX, 4.2, 19.6, 1.35,
     '关键控制点：管网差异须《工程量确认表》四方签章；站点差异须《图纸会审记录》四方签字；\n'
     '接户管差异三方现场复核 —— 签章不全者，结算审计不予认定', fs=12)

# ===== 图例 =====
ly = 2.75
start_node(3.4, ly, 0.14)
label(3.8, ly, '起止', fs=11, color='#4a5763')
rrect(5.9, ly - 0.19, 0.9, 0.38, '#ffffff', EDGE)
label(7.05, ly, '活动', fs=11, color='#4a5763')
poly([(9.7, ly + 0.22), (10.15, ly), (9.7, ly - 0.22), (9.25, ly)], DEC_F, DEC_E)
label(10.4, ly, '判断', fs=11, color='#4a5763')
rrect(12.6, ly - 0.19, 0.9, 0.38, RES_F, RES_E)
label(13.75, ly, '计量结果', fs=11, color='#4a5763')
poly([(16.6, ly - 0.2), (17.5, ly - 0.2), (17.5, ly + 0.05), (17.3, ly + 0.2), (16.6, ly + 0.2)],
     WARN_F, WARN_E)
label(17.75, ly, '差异处理', fs=11, color='#4a5763')

save(A.out)
print('OK', A.out)
