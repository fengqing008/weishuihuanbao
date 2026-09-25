#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板风格流程图 · 工程量差异处理
用法：python3 sop_flowchart_diff.py --project 示例PPP --out 差异处理.png
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flowchart_kit import (init, save, title_block, start_node, end_node,
                           rbox, diamond, note, path, label, line, dot, rrect, poly,
                           RES_F, RES_E, WARN_F, WARN_E, BAD_F, BAD_E, ACT_E,
                           EDGE, DEC_F, DEC_E, NOTE_F, NOTE_E)

ap = argparse.ArgumentParser(description='模板风格流程图 · 工程量差异处理')
ap.add_argument('--project', default='示例PPP', help='项目名称前缀')
ap.add_argument('--subtitle', default='适用：施工单位 ／ 设计单位 ／ 监理单位 ／ 建设单位')
ap.add_argument('--out', default='差异处理_流程图.png')
A = ap.parse_args()

init()
title_block(f'{A.project}项目工程结算 · 工程量差异处理 SOP', A.subtitle, fs_title=25)

CX = 11.0
COL = [4.0, 11.0, 18.0]

# ===== 起止 + 总原则 =====
start_node(CX, 23.1)
path([(CX, 22.8), (CX, 22.475)])
rbox(CX, 22.0, 13.8, 0.95, '总原则：差异工程量须有签章齐全的过程资料支撑，否则不予认定',
     fs=14.5, bold=True)
path([(CX, 21.525), (CX, 21.3)])

# ===== 类型判断 + 三列分流 =====
diamond(CX, 20.5, 7.2, 1.6, '工程量差异属于哪一类？', fs=13.5)
tags = ['管网差异', '接户管差异', '站点差异']
for cx in COL:
    path([(CX, 19.7), (CX, 19.0), (cx, 19.0), (cx, 18.85)])
label((CX + COL[0]) / 2, 19.32, tags[0], fs=12)
label(COL[1] + 1.0, 19.32, tags[1], fs=12)
label((CX + COL[2]) / 2, 19.32, tags[2], fs=12)

# ===== 三列：情形 → 资料 → 签章 =====
rbox(COL[0], 18.2, 5.6, 1.3, '管网工程量\n与竣工图存在差异', fs=12)
rbox(COL[1], 18.2, 5.6, 1.3, '接户管实际收方\n与图纸不符', fs=12)
rbox(COL[2], 18.2, 5.6, 1.3, '站点实际施工\n与竣工图不一致或缺漏', fs=12)
for cx in COL:
    path([(cx, 17.55), (cx, 17.35)])

rbox(COL[0], 16.7, 5.6, 1.3, '编制《工程量确认表》\n（四方确认栏版）', ec=ACT_E, fs=12)
rbox(COL[1], 16.7, 5.6, 1.3, '编制《接户管工程量\n三方确认文件》', ec=ACT_E, fs=12)
rbox(COL[2], 16.7, 5.6, 1.3, '形成《图纸会审记录》\n（表D.5，按专业分列）', ec=ACT_E, fs=12)
for cx in COL:
    path([(cx, 16.05), (cx, 15.85)])

note(COL[0], 15.1, 5.6, 1.5, '①施工 ②设计\n③监理 ④建设\n依次签字盖章', fs=12)
note(COL[1], 15.1, 5.6, 1.5, '建设＋监理＋施工\n三方现场复核\n（设计单位不参与）', fs=12)
note(COL[2], 15.1, 5.6, 1.5, '①施工 ②设计\n③监理 ④建设\n四方签字（表D.5）', fs=12)

# ===== 阶梯式汇聚 =====
Y1, Y2 = 13.65, 13.3
line([(COL[0], 14.35), (COL[0], Y1)])
line([(COL[0], Y1), (CX, Y1)])
line([(CX, 14.35), (CX, Y2)])
line([(COL[2], 14.35), (COL[2], Y1)])
line([(COL[2], Y1), (CX, Y1)])
line([(COL[1], 14.35), (COL[1], Y2)])
dot(CX, Y1, 0.06)
dot(CX, Y2, 0.07)
path([(CX, Y2), (CX, 12.875)])

rbox(CX, 12.4, 13.8, 0.95, '签认结果确认 → 形成差异工程量计量依据', ec=ACT_E, fs=14, bold=True)
path([(CX, 11.925), (CX, 11.9)])

# ===== 签章齐全性判定 =====
diamond(CX, 11.2, 6.8, 1.6, '四方签章是否齐全？', fs=13)
path([(CX, 10.4), (CX, 9.9), (8.2, 9.9), (8.2, 9.75)])
path([(CX, 10.4), (CX, 9.9), (13.8, 9.9), (13.8, 9.75)])
label(9.55, 10.13, '是', fs=11)
label(12.45, 10.13, '否', fs=11)

rbox(8.2, 9.3, 5.8, 0.9, '予以认定，纳入结算工程量', fc=RES_F, ec=RES_E, fs=13, bold=True)
rbox(13.8, 9.3, 5.8, 0.9, '不予认定，退回补正', fc=BAD_F, ec=BAD_E, fs=13, bold=True)

# 是 → 结束；否 → 补正（折角注释）
path([(8.2, 8.85), (8.2, 8.3)])
end_node(8.2, 8.0)
path([(13.8, 8.85), (13.8, 8.65)])
note(13.8, 7.95, 7.0, 1.3,
     '补正签章齐全后重新报审\n（回到本表签章环节重新判定）', fs=12, fc=WARN_F, ec=WARN_E)

# ===== 底线规则（折角注释） =====
note(CX, 5.9, 19.8, 1.35,
     '底线规则：管网差异无《工程量确认表》四方签章、站点差异无《图纸会审记录》四方签字、\n'
     '接户管差异无三方现场复核文件的 —— 该差异量结算审计一律不予认定', fs=12,
     fc=BAD_F, ec=BAD_E)

# ===== 图例 =====
ly = 4.25
start_node(3.0, ly, 0.14)
label(3.4, ly, '起止', fs=11, color='#4a5763')
rrect(5.5, ly - 0.19, 0.9, 0.38, '#ffffff', EDGE)
label(6.65, ly, '活动', fs=11, color='#4a5763')
poly([(9.3, ly + 0.22), (9.75, ly), (9.3, ly - 0.22), (8.85, ly)], DEC_F, DEC_E)
label(10.0, ly, '判断', fs=11, color='#4a5763')
poly([(12.3, ly - 0.2), (13.2, ly - 0.2), (13.2, ly + 0.05), (13.0, ly + 0.2), (12.3, ly + 0.2)],
     NOTE_F, NOTE_E)
label(13.45, ly, '签章要求', fs=11, color='#4a5763')
rrect(16.4, ly - 0.19, 0.9, 0.38, BAD_F, BAD_E)
label(17.55, ly, '不予认定', fs=11, color='#4a5763')

save(A.out)
print('OK', A.out)
