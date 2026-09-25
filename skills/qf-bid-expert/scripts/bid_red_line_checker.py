#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""废标红线扫描器 v1.2 —— 条款分块 + 同义词扩展 + 多格式输出（md/csv/xlsx）。

用法:
    python3 bid_red_line_checker.py --file 招标文件.md --out 废标核查表.md
    python3 bid_red_line_checker.py --file 招标文件.md --out 废标核查表.xlsx
"""
import argparse
import csv
import os
import re
import sys

# 每类：主关键词 + 同义/变体写法（覆盖换行、标点差异与常见近义表述）
CATEGORIES = {
    "报价类": ["最高限价", "招标控制价", "最高投标限价", "报价上限", "不得超过最高", "报价超过",
               "超过最高限价", "报价等于", "等于或超过", "只允许提交一个", "唯一报价", "一个有效报价",
               "报价唯一", "低于成本", "低于其他供应商平均报价", "低于平均报价", "固定不变",
               "不得调整", "价格调整", "报价不予调整"],
    "资格符合性类": ["资格审查", "资格要求", "资格条件", "资格证明", "营业执照", "经营范围",
                     "投标有效期", "虚假信息", "虚假材料", "信用中国", "信用记录", "失信被执行人",
                     "重大税收违法", "政府采购严重违法失信", "行贿犯罪", "无重大违法记录"],
    "技术评议类": ["虚假响应", "响应与事实不符", "不能证明", "原文复制", "照抄", "不能接受的条件",
                   "实质性响应", "负偏离", "技术偏离"],
    "形式密封签署类": ["密封", "加写标记", "不予受理", "逾期送达", "授权委托书", "字迹模糊",
                       "正副本", "大写金额", "身份核验", "参加开标", "法定代表人签字", "加盖公章",
                       "逐页", "骑缝章", "装订"],
    "串通弄虚作假类": ["串通", "行贿", "同一单位", "同一人", "异常一致", "规律性差异",
                       "相互混装", "以他人名义", "提供虚假"],
    "招标人否决权类": ["否决", "无效标", "无效投标", "废标", "不予接受", "虚假陈述",
                       "本质性差别", "未按投标人须知", "未按招标文件要求"],
    "保证金没收类": ["投标保证金", "没收", "不予返还", "撤回投标", "拒签协议", "履约担保",
                     "附加条件", "履约保证金"],
    "重新招标类": ["重新招标", "招标失败", "少于3个", "少于三个", "少于三家", "否决所有投标",
                   "缺乏有效竞争", "不足三家"],
}

CHECKLIST = [
    ("报价类", "报价不超最高限价或招标控制价"),
    ("报价类", "只有一个有效报价"),
    ("报价类", "不低于成本价并有说明"),
    ("资格符合性类", "全部资格要求逐条满足"),
    ("资格符合性类", "资格证明文件齐全且有效"),
    ("资格符合性类", "信用截图在公告发布日之后并盖鲜章"),
    ("技术评议类", "未整段照抄招标技术要求"),
    ("技术评议类", "证明文件能证实响应内容"),
    ("形式密封签署类", "密封与标记符合要求"),
    ("形式密封签署类", "正副本加盖公章与签名"),
    ("形式密封签署类", "有法定代表人授权委托书"),
    ("形式密封签署类", "大写金额无歧义"),
    ("形式密封签署类", "装订方式符合要求"),
    ("串通弄虚作假类", "非同一单位或个人编制"),
    ("串通弄虚作假类", "项目成员与联系人非同一人"),
    ("招标人否决权类", "无故意的虚假陈述"),
    ("招标人否决权类", "信息与资格文件无本质性差别"),
    ("保证金没收类", "已按规定提交保证金或保函"),
    ("保证金没收类", "保证金形式与有效期符合要求"),
    ("重新招标类", "投标人不少于三家"),
]


def into_blocks(path):
    """按行读取并合并为条款块，返回 [(块文本, 起始行号)]（处理换行的长条款）。"""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    buf, start, out = [], 0, []
    for no, ln in enumerate(lines, 1):
        t = ln.strip()
        if not t:
            if buf:
                out.append((" ".join(buf), start)); buf = []
            continue
        if not buf:
            start = no
        buf.append(t)
        joined = " ".join(buf)
        if t.endswith(("。", "；", ";", "：", ":", "）", ")")) or len(joined) > 200:
            out.append((joined, start)); buf = []
    if buf:
        out.append((" ".join(buf), start))
    return out


def scan(path):
    hits = {k: [] for k in CATEGORIES}
    for i, (blk, ln) in enumerate(into_blocks(path), 1):
        for cat, kws in CATEGORIES.items():
            for kw in kws:
                if kw in blk:
                    hits[cat].append((f"{i}(L{ln})", kw, blk[:200]))
                    break
    return hits


def build_rows(hits):
    rows = [["类别", "核查项", "是否满足", "证据位置"]]
    for cat, item in CHECKLIST:
        rows.append([cat, item, "□", ""])
    return rows


def write_md(hits, out):
    total = sum(len(v) for v in hits.values())
    L = ["# 废标红线核查表", "", f"> 命中条款块：{total} 处", "",
         "## 一、红线条款命中片段", ""]
    for cat, items in hits.items():
        L.append(f"### {cat}（{len(items)} 处）")
        L.append("")
        if not items:
            L.append("- 未命中")
            L.append("")
            continue
        for bid, kw, text in items:
            L.append(f"- 块{bid} [{kw}] {text}")
        L.append("")
    L += ["## 二、逐条核查清单", "", "| 类别 | 核查项 | 是否满足 | 证据位置 |", "|---|---|---|---|"]
    for cat, item in CHECKLIST:
        L.append(f"| {cat} | {item} | □ | |")
    L.append("")
    L.append("> 任一核查项不满足或证据缺失，标书不得递交。")
    open(out, "w", encoding="utf-8").write("\n".join(L))


def write_csv(hits, out):
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["类别", "命中关键词", "条款块号", "原文片段"])
        for cat, items in hits.items():
            for bid, kw, text in items:
                w.writerow([cat, kw, bid, text])
        w.writerow([])
        w.writerows(build_rows(hits))


def write_xlsx(hits, out):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        print("导出 .xlsx 需要 openpyxl，请先安装：pip install openpyxl", file=sys.stderr)
        sys.exit(3)
    wb = Workbook()
    ws = wb.active
    ws.title = "红线核查"
    ws.append(["类别", "核查项", "是否满足", "证据位置"])
    for cat, item in CHECKLIST:
        ws.append([cat, item, "", ""])
    ws2 = wb.create_sheet("命中片段")
    ws2.append(["类别", "命中关键词", "条款块号", "原文片段"])
    for cat, items in hits.items():
        for bid, kw, text in items:
            ws2.append([cat, kw, bid, text])
    fill = PatternFill("solid", fgColor="CCCCCC")
    for sh in (ws, ws2):
        for c in sh[1]:
            c.font = Font(bold=True)
            c.fill = fill
        for col, w in zip("ABCD", [16, 34, 12, 80]):
            sh.column_dimensions[col].width = w
    wb.save(out)


def main():
    ap = argparse.ArgumentParser(description="废标红线扫描器 v1.2")
    ap.add_argument("--file", required=True, help="招标文件文本（txt/md）")
    ap.add_argument("--out", required=True, help="输出（.md / .csv / .xlsx）")
    args = ap.parse_args()

    hits = scan(args.file)
    total = sum(len(v) for v in hits.values())
    low = args.out.lower()
    if low.endswith(".xlsx"):
        write_xlsx(hits, args.out)
    elif low.endswith(".csv"):
        write_csv(hits, args.out)
    else:
        write_md(hits, args.out)
    print(f"OK 命中 {total} 处条款块，核查表已写入 {args.out}")
    print("提示：关键词扫描为初筛，逐条核查清单须人工勾选证据位置。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
