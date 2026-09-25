#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""meeting_stats.py — 会议转录发言统计（meeting-insights-analyzer 技能配套脚本）

输入：带说话人与时间信息的转录件（.txt/.md/.vtt/.srt/.docx）
输出：stats.json（逐场逐人指标）+ 发言比表.md（人读表格）

仅依赖 Python 3.8+ 标准库；.docx 解析需可选依赖 python-docx，缺失时跳过该文件。

用法：
  python3 scripts/meeting_stats.py --input ./transcripts --me "我" --out ./reports --json
  python3 scripts/meeting_stats.py --input ./transcripts/示例-周例会.vtt --me "我" --top-n 8
  python3 scripts/meeting_stats.py --input ./transcripts --me "我" --filler both --min-turn 12
"""
import argparse
import json
import re
import sys
from pathlib import Path

VERSION = "1.0.0"

SUPPORTED = (".txt", ".md", ".vtt", ".srt", ".docx", ".markdown")

SPEAKER_RE = re.compile(
    r'^\s*(?:\[(?P<t>\d{1,2}:\d{2}(?::\d{2})?)\]\s*)?'
    r'(?P<sp>[\u4e00-\u9fa5A-Za-z][\w\u4e00-\u9fa5·\- ]{0,11})\s*[:：]\s*(?P<tx>.+?)\s*$'
)
VTT_VOICE_RE = re.compile(r'<v\s+([^>]+)>(.*)')
VTT_TIME_RE = re.compile(r'^(\d{1,2}:\d{2}(?::\d{2})?)[.,]\d{3}\s*-->')
SRT_TIME_RE = re.compile(r'^(\d{1,2}:\d{2}:\d{2})[.,]\d{3}\s*-->')
NOTE_RE = re.compile(r'^(WEBVTT|NOTE\b|STYLE\b|REGION\b|\d+$)', re.I)

FILLER_CN = ["嗯", "呃", "那个", "这个", "就是", "就是说", "怎么说呢", "是吧", "对吧"]
FILLER_EN = ["um", "uh", "like", "you know", "actually", "basically", "sort of", "kind of"]
HEDGE_CN = ["可能", "也许", "大概", "稍微", "有点", "我觉得", "我个人认为", "差不多"]
HEDGE_EN = ["maybe", "perhaps", "potentially", "i think", "i guess", "sort of", "kind of"]
LISTEN_CN = ["你说的", "你刚才", "你提到", "如你所说", "我复述一下", "我确认一下",
             "补充一点", "就你所说", "沿着你的思路"]
LISTEN_EN = ["as you said", "you mentioned", "to build on", "just to confirm",
             "let me paraphrase", "going back to your point"]
DECISION_CN = ["就这么定", "定了", "下一个议题", "今天到此", "结论是", "拍板"]
ACTION_CN = ["谁负责", "什么时候交", "截止", "跟进", "下一步"]


def hms_to_sec(t):
    if not t:
        return None
    parts = [int(p) for p in t.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def parse_docx(path):
    try:
        import docx  # type: ignore
    except Exception:
        return None, "python-docx 未安装，跳过 .docx 文件"
    d = docx.Document(str(path))
    lines = []
    for p in d.paragraphs:
        if p.text.strip():
            lines.append(p.text.strip())
    for tb in d.tables:
        for row in tb.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(": ".join(cells[:2]) if len(cells) >= 2 else cells[0])
    return "\n".join(lines), None


def read_text(path):
    if path.suffix.lower() == ".docx":
        text, err = parse_docx(path)
        if err:
            return None, err
        return text, None
    return path.read_text(encoding="utf-8", errors="replace"), None


def parse_transcript(path, speaker_map=None):
    """返回 turns = [{sp, tx, t(sec or None), order}] 与解析备注列表"""
    raw, err = read_text(path)
    if err:
        return [], [err]
    notes = []
    suffix = path.suffix.lower()
    turns, cur = [], None

    for line in raw.splitlines():
        line = line.strip()
        if not line or NOTE_RE.match(line):
            continue
        if suffix == ".vtt":
            m = VTT_VOICE_RE.search(line)
            if m:
                sp = m.group(1).strip()
                tx = m.group(2).strip()
                if tx:
                    cur = {"sp": sp, "tx": tx, "t": None, "order": len(turns)}
                    turns.append(cur)
                continue
        m = VTT_TIME_RE.match(line) or SRT_TIME_RE.match(line)
        if m:
            if cur is not None:
                cur["t"] = cur.get("t") or hms_to_sec(m.group(1))
            continue
        sm = SPEAKER_RE.match(line)
        if sm:
            sp = sm.group("sp").strip().strip("[]")
            tx = sm.group("tx").strip()
            cur = {"sp": sp, "tx": tx, "t": hms_to_sec(sm.group("t")), "order": len(turns)}
            turns.append(cur)
        elif cur is not None:
            cur["tx"] += " " + line

    if speaker_map:
        for t in turns:
            t["sp"] = speaker_map.get(t["sp"], t["sp"])

    if turns and all(t["t"] is None for t in turns):
        notes.append("无时间轴，改用序位编号代替时间")
    if turns and len({t["sp"] for t in turns}) == 1:
        notes.append("检测到单一说话人：可能缺少说话人标签，逐人统计不可用")
    total_len = sum(len(t["tx"]) for t in turns)
    for t in turns:
        t["span"] = round(100.0 * len(t["tx"]) / total_len, 2) if total_len else 0.0
    return turns, notes


def count_hits(text, words):
    low = text.lower()
    return sum(low.count(w.lower()) for w in words)


def is_question(tx):
    return tx.rstrip().endswith(("?", "？")) or tx.rstrip().endswith(("吗", "呢", "吧"))


def overlap_flag(turns):
    """粗糙重叠检测：相邻两轮时间差 < 2 秒且都非空"""
    cnt = 0
    for a, b in zip(turns, turns[1:]):
        if a["t"] is not None and b["t"] is not None and 0 <= (b["t"] - a["t"]) < 2:
            cnt += 1
    return cnt


def analyse(path, me, min_turn=10, filler_scope="both", speaker_map=None, top_n=5):
    turns, notes = parse_transcript(path, speaker_map)
    if not turns:
        return {"file": path.name, "error": "无法解析出有效发言轮次", "notes": notes}

    filler = list(FILLER_CN) + (list(FILLER_EN) if filler_scope in ("both", "en") else [])
    if filler_scope == "en":
        filler = list(FILLER_EN)
    hedge = list(HEDGE_CN) + list(HEDGE_EN)
    listen = list(LISTEN_CN) + list(LISTEN_EN)

    total_chars = sum(len(t["tx"]) for t in turns)
    total_words = sum(len(re.findall(r"[A-Za-z']+", t["tx"])) for t in turns)
    spk, order = {}, []
    for t in turns:
        if t["sp"] not in spk:
            spk[t["sp"]] = {
                "turns": 0, "chars": 0, "words": 0, "questions": 0,
                "filler": 0, "hedge": 0, "listen": 0,
                "interrupt_given": 0, "interrupt_received": 0,
                "long_turns": 0, "supportive": 0,
            }
            order.append(t["sp"])
        s = spk[t["sp"]]
        s["turns"] += 1
        s["chars"] += len(t["tx"])
        s["words"] += len(re.findall(r"[A-Za-z']+", t["tx"]))
        s["questions"] += 1 if is_question(t["tx"]) else 0
        s["filler"] += count_hits(t["tx"], filler)
        s["hedge"] += count_hits(t["tx"], hedge)
        s["listen"] += count_hits(t["tx"], listen)
        if len(t["tx"]) >= 200:
            s["long_turns"] += 1
        if len(t["tx"]) < min_turn:
            s["supportive"] += 1

    # 打断启发式：短轮切入长轮之后
    evidence = {}
    for a, b in zip(turns, turns[1:]):
        if a["sp"] != b["sp"] and len(a["tx"]) >= min_turn * 3 and len(b["tx"]) < min_turn:
            spk[b["sp"]]["interrupt_given"] += 1
            spk[a["sp"]]["interrupt_received"] += 1
            key = b["sp"]
            evidence.setdefault(key, [])
            if len(evidence[key]) < top_n:
                ts = "[%02d:%02d:%02d]" % (b["t"] // 3600, b["t"] % 3600 // 60, b["t"] % 60) if b["t"] else "(no-ts)"
                evidence[key].append({"ts": ts, "quote": b["tx"][:80], "after": a["tx"][:60]})

    # 填充词/限定语证据
    filler_ev = []
    for t in turns:
        if t["sp"] == me and count_hits(t["tx"], hedge) > 0:
            ts = "[%02d:%02d:%02d]" % (t["t"] // 3600, t["t"] % 3600 // 60, t["t"] % 60) if t["t"] else "(no-ts)"
            filler_ev.append({"ts": ts, "quote": t["tx"][:100],
                              "hedge_hits": count_hits(t["tx"], hedge)})
        if len(filler_ev) >= top_n:
            break

    for name in order:
        s = spk[name]
        s["share_chars"] = round(s["chars"] / total_chars, 3) if total_chars else 0.0
        s["share_words"] = round(s["words"] / total_words, 3) if total_words else 0.0
        s["avg_turn_chars"] = round(s["chars"] / s["turns"], 1) if s["turns"] else 0.0
        s["question_ratio"] = round(s["questions"] / s["turns"], 3) if s["turns"] else 0.0
        s["filler_per_1k"] = round(1000.0 * s["filler"] / s["chars"], 1) if s["chars"] else 0.0
        s["hedge_per_1k"] = round(1000.0 * s["hedge"] / s["chars"], 1) if s["chars"] else 0.0

    dur = 0
    if turns[-1]["t"] is not None and turns[0]["t"] is not None:
        dur = max(t["t"] for t in turns if t["t"] is not None) or 0

    mine = spk.get(me)
    return {
        "file": path.name,
        "format": path.suffix.lower(),
        "turns": len(turns),
        "speakers": order,
        "duration_sec": dur,
        "total_chars": total_chars,
        "min_turn": min_turn,
        "filler_scope": filler_scope,
        "overlap_pairs": overlap_flag(turns),
        "me": me,
        "me_metrics": mine,
        "all": spk,
        "interrupt_evidence": evidence,
        "hedge_evidence": filler_ev,
        "notes": notes,
    }


def render_md(results, me):
    lines = ["# 会议发言比表", ""]
    lines.append("| 场次 | 发言人 | 轮次 | 平均轮长(字) | 占比(字符) | 占比(词数) | 提问比 | 填充词/千字 | 限定语/千字 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        if r.get("error") or not r.get("all"):
            continue
        for name, s in r["all"].items():
            mark = " ★" if name == me else ""
            lines.append("| %s | %s%s | %d | %s | %.2f | %.2f | %.2f | %s | %s |" % (
                r["file"], name, mark, s["turns"], s["avg_turn_chars"],
                s["share_chars"], s["share_words"], s["question_ratio"],
                s["filler_per_1k"], s["hedge_per_1k"]))
    lines.append("")
    lines.append("注：★ 为分析对象；占比为行内并列双口径；冲突规避信号=限定语密度超 8/千字；打断口径=短轮切入长轮之后的启发式计数，须回读上下文复核。")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="会议转录发言统计（meeting-insights-analyzer）")
    ap.add_argument("--input", required=True, help="转录文件或目录")
    ap.add_argument("--me", default="", help="分析对象在转录中的标识名")
    ap.add_argument("--out", default="./reports", help="输出目录，默认 ./reports")
    ap.add_argument("--json", action="store_true", help="同时把完整 JSON 打到标准输出")
    ap.add_argument("--top-n", type=int, default=5, help="每类证据保留条数，默认 5")
    ap.add_argument("--filler", choices=["both", "cn", "en"], default="both", help="填充词词表范围")
    ap.add_argument("--min-turn", type=int, default=10, help="实质发言最小字数阈值，默认 10")
    ap.add_argument("--speaker-map", default=None, help="别名映射 JSON 文件：{别名: 规范名}")
    ap.add_argument("--quiet", action="store_true", help="静默模式，仅写文件")
    ap.add_argument("--version", action="version", version="meeting_stats.py " + VERSION)
    args = ap.parse_args(argv)

    src = Path(args.input)
    if not src.exists():
        print("[ERR] 输入路径不存在：%s" % src, file=sys.stderr)
        return 2
    files = [src] if src.is_file() else sorted(
        p for p in src.rglob("*") if p.suffix.lower() in SUPPORTED)
    if not files:
        print("[ERR] 目录内未发现支持的转录件（%s）" % ", ".join(SUPPORTED), file=sys.stderr)
        return 3

    smap = None
    if args.speaker_map:
        smap = json.loads(Path(args.speaker_map).read_text(encoding="utf-8"))

    results = []
    for f in files:
        r = analyse(f, args.me, min_turn=args.min_turn, filler_scope=args.filler,
                    speaker_map=smap, top_n=args.top_n)
        results.append(r)

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool": "meeting_stats.py",
        "version": VERSION,
        "input": str(src),
        "me": args.me,
        "params": {"min_turn": args.min_turn, "filler_scope": args.filler, "top_n": args.top_n},
        "sessions": results,
    }
    (outdir / "stats.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "发言比表.md").write_text(render_md(results, args.me), encoding="utf-8")

    if not args.quiet:
        ok = sum(1 for r in results if not r.get("error"))
        print("[OK] %d files parsed | turns=%d | speakers=%d | duration_sec=%d" % (
            ok, sum(r.get("turns", 0) for r in results),
            len({s for r in results for s in r.get("speakers", [])}),
            sum(r.get("duration_sec", 0) for r in results)))
        for r in results:
            m = r.get("me_metrics")
            if m and r.get("me"):
                print("[ME] %s | share_chars=%.2f | share_words=%.2f | turns=%d | avg_turn_chars=%s" % (
                    r["me"], m["share_chars"], m["share_words"], m["turns"], m["avg_turn_chars"]))
                print("[CHK] filler_per_1k=%s | hedge_per_1k=%s | question_ratio=%.2f | interrupt_given=%d" % (
                    m["filler_per_1k"], m["hedge_per_1k"], m["question_ratio"], m["interrupt_given"]))
            for n in r.get("notes", []):
                print("[NOTE] %s: %s" % (r["file"], n))
        print("written: %s" % (outdir / "stats.json"))
        print("written: %s" % (outdir / "发言比表.md"))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
