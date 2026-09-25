#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""case_extract.py — 水务工程诉讼案件要素抽取器（纯标准库）

从判决书 / 民事起诉状 / 答辩状 / 应诉通知书的纯文本中抽取结构化要素：
  案号、审理法院、案由、当事人及诉讼地位、诉讼请求、判决主文、
  金额（千分位规范化）、缺失字段（标【待核】）。

用法示例：
  python3 case_extract.py --file ./某案民事判决书.txt
  python3 case_extract.py --file ./某案民事起诉状.md --json --out ./case.json
  python3 case_extract.py --text "原告某某公司诉被告某某公司建设工程施工合同纠纷一案，诉讼请求如下：……"

设计约束：
  - 只做抽取与规范化，不做法律判断；
  - 抽不到的字段一律进入 missing 列表，禁止凭上下文推断填充；
  - 输出中不含当事人身份证号、银行账号等身份信息（正则主动剔除）。

退出码：0 = 正常；1 = 输入为空或文件不可读；2 = 参数错误。
"""
import argparse
import json
import re
import sys

# 案由关键词（按命中长度优先匹配）
CAUSE_KEYS = [
    "建设工程施工合同纠纷", "建设工程分包合同纠纷", "确认合同无效纠纷",
    "劳务合同纠纷", "追索劳动报酬纠纷", "买卖合同纠纷", "建设工程价款优先受偿权纠纷",
    "执行异议之诉", "不当得利纠纷", "财产保全损害责任纠纷",
]
PARTY_ROLES = ["原告", "被告", "上诉人", "被上诉人", "申请人", "被申请人",
               "第三人", "再审申请人", "被申请人", "反诉原告", "反诉被告"]
AMOUNT_RE = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?\s*(万|亿)?\s*元")
CASE_NO_RE = re.compile(r"[（(]\s*(\d{4})\s*[）)]\s*([\u4e00-\u9fa5]{0,4}\d{0,4})?\s*[\u4e00-\u9fa5]{0,3}\s*(\d+)\s*号")
COURT_RE = re.compile(r"([\u4e00-\u9fa5]{2,20}人民法院)")
# 敏感信息正则：命中即剔除，不进入输出
SENSITIVE_RES = [
    re.compile(r"\d{17}[\dXx]"),                       # 身份证号
    re.compile(r"9[1-9]\d{4}[0-9A-Z]{10}[0-9A-Z]"),   # 统一社会信用代码
    re.compile(r"\b\d{16,19}\b"),                      # 银行账号
    re.compile(r"1[3-9]\d{9}"),                        # 手机号
]


def sanitize(text: str) -> str:
    """剔除身份证号、统一社会信用代码、银行账号、手机号。"""
    out = text
    for pat in SENSITIVE_RES:
        out = pat.sub("[已脱敏]", out)
    return out


def section(text: str, start_keys, stop_keys, limit=1200) -> str:
    """截取从 start_keys 任一命中处到 stop_keys 任一命中处的片段。"""
    pos = -1
    for k in start_keys:
        i = text.find(k)
        if i != -1 and (pos == -1 or i < pos):
            pos = i
    if pos == -1:
        return ""
    seg = text[pos:pos + limit]
    end = len(seg)
    for k in stop_keys:
        j = seg.find(k, 8)
        if j != -1:
            end = min(end, j)
    return seg[:end].strip()


def extract_parties(text: str):
    """抽取当事人及其诉讼地位：返回 [{role, name}]。"""
    found, seen = [], set()
    for m in re.finditer(r"(原告|被告|上诉人|被上诉人|申请人|被申请人|第三人)\s*[：:]\s*([^\n，,。；;]{2,40})", text):
        role, name = m.group(1), m.group(2).strip()
        name = re.split(r"[，,（(]", name)[0].strip()
        key = (role, name)
        if key in seen or len(name) < 2:
            continue
        seen.add(key)
        found.append({"role": role, "name": name})
    return found


def normalize_amounts(text: str):
    """抽取金额并规范为千分位；支持 元 / 万元 / 亿元 三种量纲。"""
    out, seen = [], set()
    scale = {"": 1.0, "万": 10000.0, "亿": 100000000.0}
    for m in AMOUNT_RE.finditer(text):
        raw = m.group(0).replace(" ", "")
        digits = raw.replace("万元", "").replace("亿元", "").replace("元", "").replace(",", "")
        try:
            val = float(digits) * scale.get(m.group(3) or "", 1.0)
        except ValueError:
            continue
        if m.group(3):
            s = f"{int(round(val)):,}"
        elif "." in digits:
            s = f"{val:,.2f}".rstrip("0").rstrip(".")
        else:
            s = f"{int(val):,}"
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def extract(text: str) -> dict:
    """主抽取函数：返回结构化字典。"""
    body = sanitize(text)
    res = {}

    m = CASE_NO_RE.search(body)
    res["case_no"] = m.group(0).strip() if m else ""

    m = COURT_RE.search(body)
    res["court"] = m.group(1) if m else ""

    cause = ""
    for k in sorted(CAUSE_KEYS, key=len, reverse=True):
        if k in body:
            cause = k
            break
    res["cause"] = cause

    res["parties"] = extract_parties(body)
    res["claims"] = section(body, ["诉讼请求", "诉请事项", "请求事项"],
                            ["事实和理由", "事实与理由", "此致", "事实及理由"])
    if "判决如下" in body or "裁定如下" in body:
        res["judgment"] = section(body, ["判决如下", "裁定如下"],
                                  ["案件受理费", "如不服本判决", "本判决为终审判决", "审判长", "本裁定为终审裁定"])
    else:
        res["judgment"] = section(body, ["判令"], ["案件受理费", "如不服本判决", "审判长"])
    res["amounts"] = normalize_amounts(body)

    missing = [k for k in ("case_no", "court", "cause", "parties", "claims", "judgment")
               if not res.get(k)]
    res["missing"] = [f"{k}【待核：文本未抽取到，须核对原件】" for k in missing]
    return res


def render(res: dict) -> str:
    """文本渲染。"""
    lines = ["# 案件要素抽取结果", ""]
    lines.append(f"- 案号：{res['case_no'] or '【待核：未抽取到】'}")
    lines.append(f"- 法院：{res['court'] or '【待核：未抽取到】'}")
    lines.append(f"- 案由：{res['cause'] or '【待核：未抽取到】'}")
    if res["parties"]:
        lines.append("- 当事人：")
        for p in res["parties"]:
            lines.append(f"  - {p['role']}：{p['name']}")
    else:
        lines.append("- 当事人：【待核：未抽取到】")
    lines.append(f"- 金额（千分位）：{'、'.join(res['amounts']) if res['amounts'] else '【待核：未抽取到】'}")
    lines.append("")
    lines.append("## 诉讼请求")
    lines.append(res["claims"] or "【待核：未抽取到】")
    lines.append("")
    lines.append("## 判决主文")
    lines.append(res["judgment"] or "【待核：未抽取到】")
    if res["missing"]:
        lines.append("")
        lines.append("## 缺失字段")
        for x in res["missing"]:
            lines.append(f"- {x}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="水务工程诉讼案件要素抽取器（案号/法院/案由/当事人/诉请/判项/金额）")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="判决书/起诉状/答辩状文本文件路径（UTF-8）")
    src.add_argument("--text", help="直接传入的文书文本")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--out", help="结果写入文件路径")
    args = ap.parse_args(argv)

    if args.file:
        try:
            text = open(args.file, encoding="utf-8", errors="replace").read()
        except OSError as e:
            print(f"读取失败：{e}", file=sys.stderr)
            return 1
    else:
        text = args.text or ""
    if not text.strip():
        print("输入为空", file=sys.stderr)
        return 1

    res = extract(text)
    payload = json.dumps(res, ensure_ascii=False, indent=2) if args.json else render(res)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"已写入：{args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
