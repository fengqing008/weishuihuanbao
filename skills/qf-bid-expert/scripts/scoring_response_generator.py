#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评分响应表生成器 v5 —— 分档解析 + 原文出处 + 报价行自动合并 + 逐行覆盖度校验。

用法:
    python3 scoring_response_generator.py --file 招标文件.md --out 响应表.xlsx
    python3 scoring_response_generator.py --merge --response 响应表.xlsx --price-rows 报价核对表.xlsx --out 响应表_含报价.xlsx
    python3 scoring_response_generator.py --coverage --file 招标文件.md --response 响应表_含报价.xlsx

填写约定：响应情况或响应位置列须写明对应评审因素名称（如「完全响应：运行维护整体方案，见第二章 2.1 节」）；
校验按行比对——先定位该评审因素所在行，再核该行响应列是否含因素名称（含即通过），否则按分词相似度 0.60 判定；
两列均为空或仅有未填占位（__ / 待填 / 待核）时判 FAIL。报价行须已并入并填写，否则判 FAIL。
"""
import argparse
import csv
import difflib
import re
import sys

HEADER = ["序号", "评审因素(含分值)", "评分标准(分档原文)", "响应情况", "响应位置", "原文出处(行号)"]

FACTOR_RE = re.compile(
    r"^\s*(?:\d+[\.、]|[（(]\s*\d+\s*[)）]|[一二三四五六七八九十]+\s*[、\.])\s*"
    r"(?P<name>[^（(]{2,40}?)[（(]\s*(?P<score>\d{1,3}(?:\.\d)?)\s*分\s*[)）]")
BAND_RE = re.compile(r"得\s*(?P<band>\d{1,3}(?:\.\d)?\s*[—\-~～至]\s*\d{1,3}(?:\.\d)?|\d{1,3}(?:\.\d)?)\s*分")
STOP_NAME = ("第", "共", "合计", "小计", "总")
SKIP_NAMES = ("技术分", "商务分", "财务分", "法律分", "经济分", "资信分", "综合分")
UNFILLED = ("__", "待填", "待核", "待补")
COL_RESP = ("响应情况", "响应位置")
PRICE_KW = ("报价", "价格")
MERGE_CMD = ("python3 scripts/scoring_response_generator.py --merge --response 响应表.xlsx "
             "--price-rows 报价核对表.xlsx --out 响应表_含报价.xlsx")


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().replace("\r\n", "\n").split("\n")


def cell_val(c):
    m = re.fullmatch(r"(\d{1,3}(?:\.\d{1,2})?)\s*分?", c or "")
    return m.group(1) if m else None


def is_price(name):
    return any(k in name for k in PRICE_KW)


def parse_table_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 3 or all(set(c) <= set("-: ") for c in cells):
        return None
    nums = [c for c in cells if cell_val(c) is not None]
    if not nums:
        return None
    if len(nums) < 2 and "分" not in line:
        return None
    cand = nums[1:] if len(nums) > 1 else nums
    score = cand[0]
    texts = [c for c in cells if c and cell_val(c) is None]
    if not texts:
        return None
    texts = [t for t in texts if "分" not in t] + [t for t in texts if "分" in t]
    name = texts[0][:40]
    if len(name) < 2:
        return None
    best_band = None
    for c in cells:
        if "分" in c and (best_band is None or len(c) > len(best_band)):
            best_band = c
    return name, score, (best_band or max(cells, key=len))


def parse(path):
    """解析为 [(因素名, 分值, [分档原文…], 行号, 是否报价类)]，行式（含中文序号）与表格式双通道。"""
    factors, cur = [], None
    for i, raw in enumerate(read_lines(path), 1):
        s = raw.strip()
        if not s:
            continue
        if s.startswith("|"):
            t = parse_table_row(s)
            if t and t[0] not in SKIP_NAMES:
                cur = {"name": t[0], "score": t[1], "bands": [t[2]], "line": i, "price": is_price(t[0])}
                factors.append(cur)
            continue
        m = FACTOR_RE.match(s)
        if m:
            name = m.group("name").strip(" 　·、,，.。：:|｜-—")
            if len(name) >= 2 and not name.startswith(STOP_NAME) and name not in SKIP_NAMES:
                cur = {"name": name, "score": m.group("score"), "bands": [], "line": i,
                       "price": is_price(name)}
                factors.append(cur)
            continue
        if cur is not None and BAND_RE.search(s):
            cur["bands"].append(s)
    seen, out = set(), []
    for f in factors:
        key = (f["name"], f["score"])
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def build_rows(factors):
    rows = [HEADER]
    for idx, f in enumerate(factors, 1):
        bands = "；".join(f["bands"]) if f["bands"] else "【待核：分档原文】"
        tag = "【报价行】" if f["price"] else ""
        rows.append([idx, f"{f['name']}（{f['score']}分·待核）{tag}", bands, "", "", f"L{f['line']}"])
    return rows


def load_table(path):
    """读取 xlsx / csv / md 为二维表；xlsx 优先取「响应条目」表，md 依次尝试节内表与首个表格。"""
    low = path.lower()
    if low.endswith(".xlsx"):
        try:
            from openpyxl import load_workbook
        except ImportError:
            print("读取 .xlsx 需 openpyxl", file=sys.stderr)
            sys.exit(3)
        wb = load_workbook(path)
        ws = wb["响应条目"] if "响应条目" in wb.sheetnames else wb.active
        return [["" if c is None else str(c) for c in r] for r in ws.iter_rows(values_only=True)]
    if low.endswith(".csv"):
        with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
            return list(csv.reader(f))

    def collect(lines, inside=False):
        rows, sec = [], inside
        for ln in lines:
            s = ln.strip()
            if s.startswith("##"):
                sec = ("响应条目" in s) or ("响应表" in s) or ("评价" in s)
                continue
            if s.startswith("|") and sec:
                cells = [c.strip() for c in s.strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):
                    continue
                rows.append(cells)
        return rows

    lines = read_lines(path)
    rows = collect(lines, inside=True)
    return rows if rows else collect(lines, inside=False)


def merge_price(resp_path, price_path, out):
    """把报价条目并入响应表：已有报价行则填充，无则在末尾追加并续编号。"""
    resp = load_table(resp_path)
    hdr_i = -1
    for i, r in enumerate(resp[:3]):
        if any("评审因素" in (c or "") for c in r):
            hdr_i = i
            break
    if hdr_i < 0:
        print("未识别到响应表表头（须含【评审因素】列），请使用本脚本生成的响应表。", file=sys.stderr)
        return 2
    hdr = resp[hdr_i]
    idxs = [j for j, c in enumerate(hdr) if any(k in (c or "") for k in COL_RESP)]
    if len(idxs) < 2:
        print("响应表缺少【响应情况】或【响应位置】列。", file=sys.stderr)
        return 2

    pr = load_table(price_path)
    prow = None
    for r in pr:
        if len(r) >= 3 and any(k in (r[0] + r[1]) for k in PRICE_KW):
            prow = r
            break
    if prow is None:
        print("报价核对表中未找到报价条目（xlsx 需含「响应条目」表，md 需含「报价响应条目」节）。",
              file=sys.stderr)
        return 2
    p_name = (prow[1] if len(prow) > 1 else "投标报价").strip()
    p_band = (prow[2] if len(prow) > 2 else "见报价评分办法摘要").strip()
    p_resp = (prow[3] if len(prow) > 3 else "").strip()
    p_pos = (prow[4] if len(prow) > 4 else "").strip()

    hit = -1
    for i, r in enumerate(resp):
        if i <= hdr_i:
            continue
        if any(k in (r[1] if len(r) > 1 else "") for k in PRICE_KW):
            hit = i
            break
    if hit > 0:
        while len(resp[hit]) < max(len(hdr), 6):
            resp[hit].append("")
        cur_band = (resp[hit][2] or "").strip()
        if p_band and (not cur_band or any(u in cur_band for u in UNFILLED)):
            resp[hit][2] = p_band
        for j, val in zip(idxs, (p_resp, p_pos)):
            resp[hit][j] = val
        action = f"已填充既有报价行（第 {hit + 1} 行），并同步分档原文"
    else:
        seq = 0
        for r in resp[hdr_i + 1:]:
            if r and str(r[0]).strip().isdigit():
                seq = max(seq, int(r[0]))
        newrow = [""] * len(hdr)
        newrow[0] = seq + 1
        newrow[1] = f"{p_name}（分值待核）【报价行】"
        newrow[2] = p_band
        for j, val in zip(idxs, (p_resp, p_pos)):
            newrow[j] = val
        if len(newrow) > 5 and not newrow[5]:
            newrow[5] = "报价核对表"
        resp.append(newrow)
        action = f"已追加报价行（序号 {seq + 1}）"

    if out.lower().endswith(".xlsx"):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            print("导出 .xlsx 需 openpyxl", file=sys.stderr)
            return 3
        wb = Workbook(); ws = wb.active; ws.title = "评分响应表"
        for r in resp:
            ws.append(r)
        for c in ws[1]:
            c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="CCCCCC")
        wb.save(out)
    elif out.lower().endswith(".csv"):
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerows(resp)
    else:
        L = ["# 评分响应表（含报价行）", "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
        L += ["| " + " | ".join(str(c) for c in r) + " |" for r in resp[hdr_i + 1:]]
        open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"OK {action}：{out}")
    print("提示：其余评审因素仍需逐条填写响应情况与响应位置，再跑 --coverage 校验。")
    return 0


def coverage(factors, response_path, price_hint=False):
    """逐行校验：先定位评审因素所在行，再核该行响应列；另校验报价行是否并入并填写。"""
    rows = load_table(response_path)
    print("== 覆盖度校验（逐行判定；含名称即通过，否则相似度 0.60）==")
    hdr_i = -1
    for i, r in enumerate(rows[:3]):
        if any("评审因素" in (c or "") for c in r):
            hdr_i = i
            break
    if hdr_i < 0:
        print("未识别到响应表表头（须含【评审因素】列）。请使用本脚本生成的响应表模板。")
        print("结论: FAIL")
        return 1
    hdr = rows[hdr_i]
    idxs = [j for j, c in enumerate(hdr) if any(k in (c or "") for k in COL_RESP)]
    if not idxs:
        print("响应表缺少【响应情况】或【响应位置】列，无法校验。请补齐该两列后重试。")
        print("结论: FAIL")
        return 1
    nm_idx = 1 if len(hdr) > 1 else 0

    body = rows[hdr_i + 1:]
    price_factors = [f for f in factors if f["price"]]
    need_price = bool(price_factors) or price_hint
    fail, price_ok = False, False
    if need_price:
        p_rows = [r for r in body if any(k in (r[1] if len(r) > 1 else "") for k in PRICE_KW)]
        if not p_rows:
            print("报价行校验: FAIL —— 招标文件含报价分，但响应表无报价行。")
            print(f"  处置：先跑 --merge 并入报价条目（{MERGE_CMD}）")
            fail = True
        else:
            unfilled = [r for r in p_rows
                        if not any((r[j] if j < len(r) else "").strip() and
                                   not any(u in r[j] for u in UNFILLED) for j in idxs)]
            print(f"报价行校验: {'FAIL' if unfilled else 'PASS'} —— 报价行 {len(p_rows)} 行"
                  f"{'' if not unfilled else '，其中响应情况/响应位置未填'}")
            price_ok = not unfilled
            fail = fail or bool(unfilled)

    all_cells = [(r[j] if j < len(r) else "").strip() for r in body for j in idxs]
    if not [c for c in all_cells if c and not any(u in c for u in UNFILLED)]:
        print("响应表的【响应情况／响应位置】两列尚为空或仅有未填占位（__／待填／待核）。")
        print("填写约定：逐条写明对应评审因素名称与响应结论，如【完全响应：运行维护整体方案，见第二章 2.1 节】。")
        print("结论: FAIL（空表不合格，填毕后再校验）")
        return 1

    missing = []
    for f in factors:
        if f["price"] and price_ok:
            continue
        own = [r for r in body
               if (lambda nm: bool(nm) and (norm(f["name"]) in norm(nm) or sim(f["name"], nm) >= 0.6))
               ((r[nm_idx] if len(r) > nm_idx else ""))]
        if not own:
            missing.append((f["name"], f["score"], "表内无对应行"))
            continue
        best = 0.0
        for r in own:
            for j in idxs:
                v = (r[j] if j < len(r) else "").strip()
                if v and not any(u in v for u in UNFILLED):
                    best = max(best, sim(f["name"], v))
        if best < 0.6:
            missing.append((f["name"], f["score"], round(best, 2)))
    print(f"招标文件评审因素: {len(factors)} 项（其中报价类 {len(price_factors)} 项）")
    print(f"已覆盖: {len(factors) - len(missing)} 项 | 未覆盖: {len(missing)} 项")
    for name, score, b in missing:
        print(f"  - 缺: {name}（{score}分，{b}）→ 请在该行响应情况中写明该评审因素名称")
    ok = (not missing) and not fail
    print("结论:", "PASS" if ok else "FAIL（补齐缺失项与报价行后再交付）")
    return 0 if ok else 1


def norm(s):
    s = re.sub(r"[（(].*?[)）]", "", s or "")
    return re.sub(r"[\s·、,，.。：:|｜\-—【】]", "", s)


def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if len(a) >= 3 and a in b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def write_out(rows, out):
    if out.lower().endswith(".xlsx"):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            print("导出 .xlsx 需 openpyxl：pip install openpyxl", file=sys.stderr)
            sys.exit(3)
        wb = Workbook(); ws = wb.active; ws.title = "评分响应表"
        for r in rows:
            ws.append(r)
        for c in ws[1]:
            c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="CCCCCC")
            c.alignment = Alignment(horizontal="center")
        for col, w in zip("ABCDEF", [6, 30, 56, 34, 26, 14]):
            ws.column_dimensions[col].width = w
        wb.save(out)
    else:
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="评分响应表生成器 v5（报价行自动合并 + 逐行覆盖度校验）")
    ap.add_argument("--file", help="招标文件文本（txt/md）")
    ap.add_argument("--out", help="输出文件（.xlsx / .csv / .md）")
    ap.add_argument("--coverage", action="store_true", help="执行覆盖度校验（逐行；含报价行必填）")
    ap.add_argument("--response", help="已有响应表（.xlsx / .csv / .md）")
    ap.add_argument("--merge", action="store_true", help="合并模式：把报价条目并入响应表")
    ap.add_argument("--price-rows", help="报价核对表（xlsx 的「响应条目」表，或 md 的「报价响应条目」节，或 csv）")
    args = ap.parse_args()

    if args.merge:
        if not (args.response and args.price_rows and args.out):
            print("合并模式需同时提供 --response、--price-rows、--out", file=sys.stderr)
            return 2
        return merge_price(args.response, args.price_rows, args.out)

    if not args.file:
        print("需提供 --file（生成/校验）或 --merge（合并）", file=sys.stderr)
        return 2
    factors = parse(args.file)
    try:
        text = open(args.file, encoding="utf-8", errors="ignore").read()
    except OSError:
        text = ""
    price_hint = bool(re.search(r"(报价分|价格分|价格评审|投标报价)[^\n]{0,12}?\d{1,3}(?:\.\d)?\s*分", text))

    if args.coverage:
        if not args.response:
            print("覆盖度校验需 --response 指定响应表文件", file=sys.stderr)
            return 2
        return coverage(factors, args.response, price_hint)
    if not args.out:
        print("生成骨架需 --out（或使用 --coverage）", file=sys.stderr)
        return 2
    write_out(build_rows(factors), args.out)
    print(f"OK 已生成响应表骨架：{args.out}")
    print(f"解析评审因素 {len(factors)} 项，其中报价类 {sum(1 for f in factors if f['price'])} 项"
          f"{'（已标【报价行】）' if any(f['price'] for f in factors) else ''}。")
    print("下一步：跑 --merge 并入报价条目，再逐条填写响应情况/响应位置，最后跑 --coverage 校验。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
