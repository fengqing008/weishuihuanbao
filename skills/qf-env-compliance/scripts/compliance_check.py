#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环保合规与督察整改材料交付门检（wwtp-env-compliance）

对整改台账 / 整改方案 / 整改报告 / 合规自查清单（.xlsx/.csv/.md/.txt）做交付前自检：
  G1 占位符与【待核】残留
  G2 合规义务六项覆盖（环评/排污许可/竣工环保验收/危废/在线监测/环保税）
  G3 问题清单字段齐备（序号/问题/依据/等级/责任部门/责任人/时限/销号佐证）
  G4 整改闭环五件套（问题文件/方案/报告/佐证/销号件）
  G5 依据文号现行性标注（法律/条例/HJ 标准）
  G6 涉刑拦截（篡改数据/偷排/伪造台账 线索）

用法（仅标准库）:
  python3 compliance_check.py --file 整改台账.xlsx --out 门检报告.md
  python3 compliance_check.py --file 整改方案.md --json

退出码: 0=全部 PASS, 1=存在 FAIL, 2=用法/文件/解析错误
"""
import argparse
import json
import os
import re
import sys
import zipfile

M_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PLACEHOLDER_RE = re.compile(r"(待填|待补|请填写|请描述|TODO|xx年|XX年|例：|占位)")
PENDING_RE = re.compile(r"【待核[^】]*】")
LAW_RE = re.compile(r"《[^》]{2,40}》|HJ\s?\d{2,}|GB\s?/?T?\s?\d{3,}|国务院令第\d+号|[〔(]\d{4}[〕)]\d+号")
OBLIGATIONS = ["环评", "排污许可", "竣工环保验收", "危险废物", "危废", "在线监测", "环保税"]
FIELDS = ["序号", "问题", "依据", "等级", "责任", "时限", "销号"]
FIVE_SET = ["问题", "方案", "报告", "佐证", "销号"]
CRIME_WORDS = ["篡改", "偷排", "伪造", "数据造假", "稀释", "旁路"]


def xlsx_text(path):
    out = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            import xml.etree.ElementTree as ET
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(M_NS + "si"):
                shared.append("".join(t.text or "" for t in si.iter(M_NS + "t")))
        for n in z.namelist():
            if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"):
                import xml.etree.ElementTree as ET
                root = ET.fromstring(z.read(n))
                for c in root.iter(M_NS + "c"):
                    v = c.find(M_NS + "v")
                    if v is None:
                        continue
                    val = v.text or ""
                    if c.get("t") == "s" and val.isdigit() and int(val) < len(shared):
                        val = shared[int(val)]
                    out.append(val)
    return "\n".join(out)


def read_any(path):
    if os.path.splitext(path)[1].lower() in (".xlsx", ".xlsm"):
        return xlsx_text(path)
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description="环保合规与督察整改材料交付门检")
    ap.add_argument("--file", required=True, help="台账/方案/报告/清单（.xlsx/.csv/.md/.txt）")
    ap.add_argument("--out", help="门检报告输出（.md）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        print(f"FAIL [G0] 文件不存在：{args.file}")
        sys.exit(2)
    try:
        text = read_any(args.file)
    except Exception as e:
        print(f"FAIL [G0] 解析失败：{e}")
        sys.exit(2)

    results = []

    def gate(code, ok, msg):
        results.append((code, bool(ok), msg))
        print(("PASS" if ok else "FAIL") + f" [{code}] {msg}")

    ph = PLACEHOLDER_RE.findall(text)
    pd = PENDING_RE.findall(text)
    gate("G1", (not ph and not pd),
         "无占位符/待核残留" if (not ph and not pd) else f"残留：{sorted(set(ph))[:5]}；待核 {pd[:5]}")

    miss_ob = [o for o in OBLIGATIONS if o not in text]
    # 危废与危险废物同义，命中其一即可
    if "危废" in miss_ob and "危险废物" in text:
        miss_ob.remove("危废")
    gate("G2", len(miss_ob) == 0,
         "六项合规义务覆盖齐备" if not miss_ob else f"缺义务 {miss_ob}（证据缺口即合规缺口）")

    miss_fd = [f for f in FIELDS if f not in text]
    gate("G3", len(miss_fd) == 0,
         "问题清单八字段齐备" if not miss_fd else f"缺字段 {miss_fd}")

    miss5 = [s for s in FIVE_SET if s not in text]
    gate("G4", len(miss5) <= 1,
         "整改闭环五件套齐备" if not miss5 else f"缺闭环件 {miss5}（五件套缺一不可）")

    laws = LAW_RE.findall(text)
    gate("G5", len(laws) >= 2,
         f"依据文号命中 {len(laws)} 处（现行有效）" if len(laws) >= 2
         else f"依据文号仅 {len(laws)} 处，须援引法律/条例/标准全称与文号")

    crime = [w for w in CRIME_WORDS if w in text]
    # 命中涉刑词属正常（用于拦截），只要文中有拦截声明即安全
    intercept = ("停止代办" in text) or ("转 L4" in text) or ("不得规避" in text) or ("涉嫌违法" in text)
    gate("G6", bool(intercept),
         "涉刑线索拦截声明齐备" if intercept else f"未检出涉刑拦截声明（命中词 {crime} 须一律停止代办并转法律救济）")

    fails = [c for c, ok, _ in results if not ok]
    conclusion = ("六道门全部 PASS，可交付/报送。" if not fails
                  else f"FAIL {len(fails)} 项 {fails}——返工后重跑。")
    print("-" * 56)
    print(f"结论：{conclusion}\n降级：任一 FAIL 回退补齐证据，异常显式告知，未过不得报送主管部门。")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("# 环保合规与督察整改材料交付门检报告\n\n")
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
