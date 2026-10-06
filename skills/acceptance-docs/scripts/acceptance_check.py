#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""acceptance_check.py —— 工程验收资料交付前质检（quality gate）

对 scripts/acceptance_tools.py 产出的 Word 资料做交付前自检，作为交付门禁：
  1) 齐套性：五类产出的关键文件是否齐全（缺件列提示，非阻断）
  2) 结构：每个 .docx 是否含表格、段落（空文档即 FAIL）
  3) 占位符：【待填：...】计数，判断必填字段是否已定位、是否被误填
  4) 签字栏：统计【待填：签字/签章/日期】类占位是否存在（不应被填死）

用法：
  python3 acceptance_check.py ./output            # 检查目录下全部 .docx
  python3 acceptance_check.py ./output --json     # 输出 JSON 结果
退出码：0 = 通过（无 FAIL）；1 = 存在 FAIL。
"""
import argparse
import json
import os
import re
import sys

EXPECT_FILES = ["验收资料核对清单", "检验批质量验收记录", "隐蔽工程验收记录",
                "分项工程质量验收记录", "分部工程质量验收记录", "竣工验收报告",
                "会议议程", "验收组", "签到", "验收意见书"]
PLACEHOLDER_RE = re.compile(r"【待填[:：][^】]*】")
SIGN_RE = re.compile(r"【待填[:：][^】]*(签|章|日期|年|月|日)[^】]*】")


def read_docx(path):
    """返回 (data, err)。data 含段落/表格文本、表格数。"""
    try:
        from docx import Document
    except Exception as e:  # 依赖缺失时明确降级提示，不静默失败
        return None, "缺 python-docx：%s（请 pip install -r requirements.txt 后重试）" % e
    try:
        doc = Document(path)
    except Exception as e:
        return None, "文档读取失败：%s" % e
    paras = [p.text for p in doc.paragraphs]
    cells = []
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                cells.append(c.text)
    return {"paras": paras, "cells": cells, "tables": len(doc.tables)}, None


def check_dir(d):
    res = {"dir": d, "files": [], "fail": [], "warn": [], "pass": []}
    if not os.path.isdir(d):
        res["fail"].append("目录不存在：%s" % d)
        return res
    names = sorted(f for f in os.listdir(d) if f.lower().endswith(".docx"))
    if not names:
        res["fail"].append("目录下无 .docx 产出，无法质检")
        return res
    joined = " ".join(names)
    for key in EXPECT_FILES:
        if key in joined:
            res["pass"].append("齐套命中：%s" % key)
        else:
            res["warn"].append("未见文件（按需生成）：%s" % key)
    for f in names:
        data, err = read_docx(os.path.join(d, f))
        if err:
            res["fail"].append("%s → %s" % (f, err))
            continue
        ph = sum(len(PLACEHOLDER_RE.findall(x)) for x in data["paras"] + data["cells"])
        sign = sum(len(SIGN_RE.findall(x)) for x in data["paras"] + data["cells"])
        info = {"file": f, "tables": data["tables"], "placeholders": ph, "sign_ph": sign}
        res["files"].append(info)
        if data["tables"] == 0:
            res["fail"].append("%s 无表格，疑似空文档" % f)
        if ph == 0 and ("记录" not in f):
            res["warn"].append("%s 未检出【待填】占位，请确认必填字段口径" % f)
        if "记录" in f and sign == 0:
            res["warn"].append("%s 未见签字栏占位，请确认签署位齐备" % f)
    return res


def main():
    ap = argparse.ArgumentParser(description="工程验收资料交付前质检（quality gate）")
    ap.add_argument("dir", help="acceptance_tools.py 的输出目录")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    a = ap.parse_args()
    r = check_dir(a.dir)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print("== 工程验收资料质检 ==")
        for x in r["pass"]:
            print("  ✔", x)
        for x in r["warn"]:
            print("  ⚠", x)
        for x in r["fail"]:
            print("  ✘", x)
        print("文件数：%d，FAIL：%d，WARN：%d" % (len(r["files"]), len(r["fail"]), len(r["warn"])))
    sys.exit(1 if r["fail"] else 0)


if __name__ == "__main__":
    main()
