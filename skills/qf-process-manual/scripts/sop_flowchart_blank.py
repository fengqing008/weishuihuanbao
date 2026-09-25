#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板风格流程图 · 空白节点模板（骨架）
—— 三列分支 + 阶梯式汇聚 + 单列步骤的通用骨架，节点文字可自定义。

用法：
  python3 sop_flowchart_blank.py --out 骨架.png
  python3 sop_flowchart_blank.py --config my_flow.json --out 我的流程.png

JSON 结构（除 branches 外均可省略）：
{
  "title":"XX项目 · XX业务 SOP", "subtitle":"适用：甲 ／ 乙 ／ 丙",
  "principle":"总原则：……", "branch_question":"……属于哪一类？",
  "branches":[{"tag":"分支一","action":"动作","decision":"判断？","yes":"是→结果","no":"否→处理"}],
  "summary":"汇总说明", "steps":["步骤一","步骤二"], "note":"关键控制点：……"
}
（branches 支持 2–3 条；steps 支持 2–6 条）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flowchart_kit import (init, save, title_block, start_node, end_node,
                           rbox, diamond, note, path, label, line, dot, rrect, poly,
                           RES_F, RES_E, WARN_F, WARN_E, ACT_E, EDGE, DEC_F, DEC_E)

DEFAULT = {
    "title": "XX项目 · XX业务 SOP",
    "subtitle": "适用：建设单位 ／ 监理单位 ／ 施工单位 ／ 审计单位",
    "principle": "总原则：（填写全局规则，作为一切判断的依据）",
    "branch_question": "（填写：按什么条件分流？）",
    "branches": [
        {"tag": "分支一", "action": "动作一\n（填写核对/操作内容）", "decision": "是否\n符合？",
         "yes": "结果一", "no": "处理一"},
        {"tag": "分支二", "action": "动作二\n（填写核对/操作内容）", "decision": "是否\n符合？",
         "yes": "结果二", "no": "处理二"},
        {"tag": "分支三", "action": "动作三\n（填写核对/操作内容）", "decision": "是否\n符合？",
         "yes": "结果三", "no": "处理三"},
    ],
    "summary": "汇总说明 →（填写汇总口径）",
    "steps": ["步骤一（填写）", "步骤二（填写）", "步骤三（填写）", "步骤四（填写）", "步骤五（填写）"],
    "note": "关键控制点：（填写底线规则 / 不可省略的签章或资料要求）",
}

ap = argparse.ArgumentParser(description='模板风格流程图 · 空白节点模板')
ap.add_argument('--config', help='JSON 配置文件路径（省略则用内置占位骨架）')
ap.add_argument('--project', help='覆盖标题前缀（可选）')
ap.add_argument('--out', default='空白模板_流程图.png')
A = ap.parse_args()

cfg = dict(DEFAULT)
if A.config:
    with open(A.config, encoding='utf-8') as f:
        cfg.update(json.load(f))
if A.project:
    cfg['title'] = cfg['title'].replace('XX项目', A.project)

branches = cfg['branches'][:3]
steps = cfg['steps'][:6]
n = len(branches)

init()
title_block(cfg['title'], cfg['subtitle'], fs_title=25)
CX = 11.0
COL = [4.0, 11.0, 18.0] if n == 3 else [6.5, 15.5]

# ===== 起止 + 总原则 =====
start_node(CX, 23.1)
label(CX + 0.62, 23.1, '开始', fs=11, color='#4a5763')
path([(CX, 22.8), (CX, 22.475)])
rbox(CX, 22.0, 14.4, 0.95, cfg['principle'], fs=14, bold=True)
path([(CX, 21.525), (CX, 21.3)])

# ===== 分流判断 =====
diamond(CX, 20.5, 7.4, 1.6, cfg['branch_question'], fs=13)
for b, cx in zip(branches, COL):
    path([(CX, 19.7), (CX, 19.0), (cx, 19.0), (cx, 18.85)])
    if n == 3 and cx == COL[1]:
        label(cx + 1.25, 19.32, b['tag'], fs=12)      # 中列直下 → 标签置右侧
    else:
        label((CX + cx) / 2, 19.32, b['tag'], fs=12)

# ===== 三列：动作 → 判断 → 是/否 =====
for b, cx in zip(branches, COL):
    rbox(cx, 18.15, 5.6, 1.3, b['action'], fs=12)
    path([(cx, 17.45), (cx, 17.2)])
    diamond(cx, 16.45, 4.8, 1.5, b['decision'], fs=12)

YN, DX = 14.35, 1.6
for b, cx in zip(branches, COL):
    path([(cx, 15.7), (cx, 15.15), (cx - DX, 15.15), (cx - DX, 14.8)])
    path([(cx, 15.7), (cx, 15.15), (cx + DX, 15.15), (cx + DX, 14.8)])
    label(cx - DX / 2, 15.33, '是', fs=11)
    label(cx + DX / 2, 15.33, '否', fs=11)
    rbox(cx - DX, YN, 2.4, 0.78, b['yes'], fc=RES_F, ec=RES_E, fs=13)
    rbox(cx + DX, YN, 2.4, 0.78, b['no'], fc=WARN_F, ec=WARN_E, fs=13)

# ===== 阶梯式汇聚 =====
Y1, Y2 = 13.65, 13.3
if n == 3:
    for cx in COL:
        line([(cx - DX, 13.96), (cx - DX, Y1)])
        line([(cx + DX, 13.96), (cx + DX, Y1)])
        line([(cx - DX, Y1), (cx + DX, Y1)])
        dot(cx, Y1, 0.055)
        line([(cx, Y1), (cx, Y2)])
    line([(COL[0], Y2), (COL[2], Y2)])
else:
    for cx in COL:
        line([(cx - DX, 13.96), (cx - DX, Y2)])
        line([(cx + DX, 13.96), (cx + DX, Y2)])
    line([(COL[0] - DX, Y2), (COL[1] + DX, Y2)])
dot(CX, Y2, 0.07)
path([(CX, Y2), (CX, 12.875)])
rbox(CX, 12.4, 14.4, 0.95, cfg['summary'], fs=14, ec=ACT_E, bold=True)

# ===== 单列步骤（自适应条数） =====
top, gap = 11.2, 1.15
ys = [top - i * gap for i in range(len(steps))]
path([(CX, 11.925), (CX, ys[0] + 0.45)])
for i, (y, t) in enumerate(zip(ys, steps)):
    rbox(CX, y, 14.8, 0.9, t, fs=12.5)
    if i < len(steps) - 1:
        path([(CX, y - 0.45), (CX, ys[i + 1] + 0.45)])

# ===== 终止 =====
last = ys[-1]
end_y = last - 0.9
path([(CX, last - 0.45), (CX, end_y + 0.3)])
end_node(CX, end_y)
label(CX + 0.62, end_y, '结束', fs=11, color='#4a5763')

# ===== 关键控制点 =====
note(CX, end_y - 1.5, 19.6, 1.35, cfg['note'], fs=12)
ly = end_y - 2.95

# ===== 图例 =====
start_node(3.4, ly, 0.14)
label(3.8, ly, '起止', fs=11, color='#4a5763')
rrect(5.9, ly - 0.19, 0.9, 0.38, '#ffffff', EDGE)
label(7.05, ly, '活动', fs=11, color='#4a5763')
poly([(9.7, ly + 0.22), (10.15, ly), (9.7, ly - 0.22), (9.25, ly)], DEC_F, DEC_E)
label(10.4, ly, '判断', fs=11, color='#4a5763')
rrect(12.6, ly - 0.19, 0.9, 0.38, RES_F, RES_E)
label(13.75, ly, '是→结果', fs=11, color='#4a5763')
poly([(16.6, ly - 0.2), (17.5, ly - 0.2), (17.5, ly + 0.05), (17.3, ly + 0.2), (16.6, ly + 0.2)],
     WARN_F, WARN_E)
label(17.75, ly, '否→处理', fs=11, color='#4a5763')

save(A.out)
print('OK', A.out)
