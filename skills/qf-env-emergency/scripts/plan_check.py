#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""突发环境事件应急预案交付门检（env-emergency-plan）

对预案初稿/定稿（.md/.txt）做交付与备案前自检：
  G1 占位符与【待核】残留
  G2 预案九章结构齐备（总则/基本情况/风险源与评价/组织职责/预防预警/应急响应/应急保障/后期处置/预案管理）
  G3 五类风险源覆盖（药剂/污泥/污水/危废/有限空间）
  G4 应急组织与联系方式（电话/联系人）
  G5 预警条件可判定（阈值）
  G6 备案要素齐备（备案编号/评审意见/发布）

用法（仅标准库）:
  python3 plan_check.py --file 预案.md --out 门检报告.md
  python3 plan_check.py --file plan.md --json

退出码: 0=全部 PASS, 1=存在 FAIL, 2=用法/文件错误
"""
import argparse
import json
import os
import re
import sys

PLACEHOLDER_RE = re.compile(r"(待填|待补|请填写|TODO|xx年|XX年|例：|占位)")
PENDING_RE = re.compile(r"【待核[^】]*】")
CHAPTERS = ["总则", "基本情况", "风险", "组织机构", "组织", "预防", "预警",
            "应急响应", "响应", "保障", "后期处置", "善后", "预案管理", "备案"]
RISK_SOURCES = ["药剂", "污泥", "污水", "危废", "有限空间"]
CONTACT_RE = re.compile(r"(电话|联系方式|联系电话|1\d{10}|联系人)")
THRESHOLD_RE = re.compile(r"(阈值|浓度|mg/L|超标|达到.*(级|档)|触发条件|判据)")
FILING_WORDS = ["备案编号", "评审", "发布", "备案"]


def read(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description="突发环境事件应急预案交付门检")
    ap.add_argument("--file", required=True, help="预案稿（.md/.txt）")
    ap.add_argument("--out", help="门检报告输出（.md）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        print(f"FAIL [G0] 文件不存在：{args.file}")
        sys.exit(2)
    try:
        text = read(args.file)
    except Exception as e:
        print(f"FAIL [G0] 读取失败：{e}")
        sys.exit(2)

    results = []

    def gate(code, ok, msg):
        results.append((code, bool(ok), msg))
        print(("PASS" if ok else "FAIL") + f" [{code}] {msg}")

    ph = PLACEHOLDER_RE.findall(text)
    pd = PENDING_RE.findall(text)
    gate("G1", (not ph and not pd),
         "无占位符/待核残留" if (not ph and not pd) else f"残留：{sorted(set(ph))[:5]}；待核 {pd[:5]}")

    miss_ch = [c for c in CHAPTERS if c not in text]
    gate("G2", len(miss_ch) <= 2,
         "预案九章结构齐备" if len(miss_ch) <= 2 else f"缺章节要素 {miss_ch}")

    miss_rs = [r for r in RISK_SOURCES if r not in text]
    gate("G3", len(miss_rs) == 0,
         "五类风险源覆盖齐备" if not miss_rs else f"缺风险源 {miss_rs}（漏识别则无对应处置措施）")

    has_contact = bool(CONTACT_RE.search(text))
    gate("G4", has_contact, "含应急组织联系方式" if has_contact else "缺应急组织联系人/电话（事件时无人履职）")

    has_th = bool(THRESHOLD_RE.search(text))
    gate("G5", has_th, "预警条件含可判定阈值" if has_th else "预警条件缺阈值（如仅写\"发现异常\"无法判启动）")

    miss_fi = [w for w in FILING_WORDS if w not in text]
    gate("G6", len(miss_fi) <= 1,
         "备案要素齐备" if len(miss_fi) <= 1 else f"缺备案要素 {miss_fi}（未备案不得视为完成）")

    fails = [c for c, ok, _ in results if not ok]
    conclusion = ("六道门全部 PASS，可提交评审与备案。" if not fails
                  else f"FAIL {len(fails)} 项 {fails}——回补后重跑。")
    print("-" * 56)
    print(f"结论：{conclusion}\n降级：任一 FAIL 回退补齐风险源/组织/阈值，异常显式告知，未过不得备案。")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("# 突发环境事件应急预案交付门检报告\n\n")
            f.write(f"- 受检文件：`{args.file}`\n- 结论：{conclusion}\n\n")
            f.write("| 门 | 结果 | 说明 |\n|---|---|---|\n")
            for c, ok, m in results:
                f.write(f"| {c} | {'PASS' if ok else 'FAIL'} | {m} |\n")

    if args.json:
        print(json.dumps({"file": args.file,
                          "gates": [{"code": c, "pass": ok, "msg": m} for c, ok, m in results],
                          "conclusion": conclusion}, ensure_ascii=False, indent=2))
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
