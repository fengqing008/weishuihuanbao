#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lucky_draw.py — 摇号抽签命令行工具（密码学安全随机抽取）。

随机源说明：
  * 默认使用 Python 标准库 secrets（CSPRNG，底层 os.urandom），公平且不可预测。
  * 传入 --seed 时切换为可复现的 random.Random(seed) 审计模式，用于事后留痕重放。
  * 两种模式共用同一套「整数权重无放回抽样」算法，保证同一 seed 可逐位复现。

用法示例：
  python3 scripts/lucky_draw.py --input names.txt --count 3 --out winners.txt
  python3 scripts/lucky_draw.py --input staff.csv --name-col 姓名 --weight-col 权重 --count 5 --exclude excluded.txt
  python3 scripts/lucky_draw.py --input names.txt --count 3 --seed 42 --replay --prove draw_proof.json
  python3 scripts/lucky_draw.py --input names.txt --count 2 --rounds 3 --unique --out winners.txt --prove proof.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone

import random as _random

TOOL_NAME = "lucky-draw"
TOOL_VERSION = "1.0.0"
PROOF_SCHEMA = "lucky-draw/proof/1"

# 权重放大倍数：浮点权重统一换算为整数，规避浮点误差导致的不可复现。
WEIGHT_SCALE = 10 ** 6


# --------------------------------------------------------------------------- #
# 随机源
# --------------------------------------------------------------------------- #
class CryptoSource:
    """密码学安全随机源（secrets / os.urandom）。默认模式，不可预测。"""

    mode = "crypto"
    label = "secrets.CSPRNG(os.urandom)"

    def __init__(self):
        self.seed = None
        self.trace = []  # 记录每次抽样使用的原始随机整数，用于生成熵摘要

    def randbelow(self, n: int) -> int:
        if n <= 0:
            raise ValueError("randbelow 的上界必须为正整数")
        value = secrets.randbelow(n)
        self.trace.append(value)
        return value


class SeededSource:
    """可复现随机源（random.Random(seed)）。用于 --seed 审计与重放。"""

    mode = "seeded"
    label = "random.Random(seed)"

    def __init__(self, seed):
        self.seed = seed
        self._rng = _random.Random(seed)
        self.trace = []

    def randbelow(self, n: int) -> int:
        if n <= 0:
            raise ValueError("randbelow 的上界必须为正整数")
        value = self._rng.randrange(n)
        self.trace.append(value)
        return value


# --------------------------------------------------------------------------- #
# 哈希与熵摘要
# --------------------------------------------------------------------------- #
def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_candidates(candidates) -> str:
    """候选池哈希：按原始顺序拼接「索引 + 姓名」。"""
    payload = "\n".join("{}\t{}".format(c["index"], c["name"]) for c in candidates)
    return _sha256_hex(payload)


def hash_winners(winners) -> str:
    """中奖名单哈希：按开出顺序拼接姓名。"""
    return _sha256_hex("\n".join(winners))


def entropy_digest(round_no: int, trace) -> str:
    """单轮随机熵摘要：对本次抽样使用的原始随机整数序列取 SHA256。"""
    payload = "lucky-draw|round={}|trace={}".format(
        round_no, ",".join(str(x) for x in trace)
    )
    return _sha256_hex(payload)


def commitment(candidates_hash: str, winners_hash: str, created_at: str) -> str:
    """总承诺值：名单哈希 + 结果哈希 + 时间戳 三者合成。"""
    payload = "lucky-draw/commit|{}|{}|{}".format(
        candidates_hash, winners_hash, created_at
    )
    return _sha256_hex(payload)


# --------------------------------------------------------------------------- #
# 权重
# --------------------------------------------------------------------------- #
def normalize_weights(weights):
    """浮点权重归一为整数权重；小于最小刻度者提升为 1，保证必被抽到。"""
    out = []
    for w in weights:
        try:
            f = float(w)
        except (TypeError, ValueError):
            raise ValueError("权重必须是数值，收到：{!r}".format(w))
        if f <= 0:
            raise ValueError("权重必须为正数，收到：{}".format(f))
        v = int(round(f * WEIGHT_SCALE))
        out.append(v if v >= 1 else 1)
    return out


# --------------------------------------------------------------------------- #
# 抽取算法
# --------------------------------------------------------------------------- #
def draw_once(pool, k, source):
    """整数权重、无放回抽取 k 个；返回按开出顺序排列的选中项。"""
    pool = list(pool)
    picks = []
    k = min(k, len(pool))
    for _ in range(k):
        total = sum(c["weight_int"] for c in pool)
        if total <= 0:
            break
        r = source.randbelow(total)
        acc = 0
        pos = len(pool) - 1
        for i, c in enumerate(pool):
            acc += c["weight_int"]
            if r < acc:
                pos = i
                break
        chosen = pool.pop(pos)
        picks.append(
            {
                "name": chosen["name"],
                "index": chosen["index"],
                "pool_pos": pos,
                "weight_int": chosen["weight_int"],
            }
        )
    return picks


def draw_all(candidates, count, rounds, unique, source):
    """完成全部轮次抽取，返回 draws 结构（含每轮随机轨迹与熵摘要）。"""
    draws = []
    used = set()
    for r in range(1, rounds + 1):
        if unique:
            pool = [c for c in candidates if c["index"] not in used]
        else:
            pool = list(candidates)
        start = len(source.trace)
        picks = draw_once(pool, count, source)
        for p in picks:
            used.add(p["index"])
        trace = source.trace[start:]
        draws.append(
            {
                "round": r,
                "pool_size": len(pool),
                "picks": picks,
                "random_trace": list(trace),
                "entropy_digest": entropy_digest(r, trace),
            }
        )
    return draws


def flatten_winners(draws):
    """把各轮摘出结果按顺序展开为名单。"""
    winners = []
    for d in draws:
        for p in d["picks"]:
            winners.append(p["name"])
    return winners


# --------------------------------------------------------------------------- #
# 输入读取
# --------------------------------------------------------------------------- #
def _clean_name(name) -> str:
    if name is None:
        return ""
    return str(name).strip().lstrip("\ufeff").strip()


def load_names(path, name_col=None, weight_col=None):
    """读取名单：txt（每行一名）/ csv（指定列）/ json（数组或对象数组）。"""
    if not os.path.isfile(path):
        raise FileNotFoundError("名单文件不存在：{}".format(path))
    ext = os.path.splitext(path)[1].lower()
    names, weights = [], []

    if ext == ".json":
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON 名单须为数组")
        for item in data:
            if isinstance(item, str):
                nm, w = _clean_name(item), 1.0
            elif isinstance(item, dict):
                nm = _clean_name(
                    item.get(name_col)
                    or item.get("name")
                    or item.get("姓名")
                    or item.get("名称")
                )
                w = item.get(weight_col) or item.get("weight") or item.get("权重") or 1.0
            else:
                continue
            if nm:
                names.append(nm)
                weights.append(w)
        return names, weights

    if ext == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            if not fields:
                raise ValueError("CSV 缺少表头")
            nc = name_col or fields[0]
            if nc not in fields:
                raise ValueError(
                    "CSV 未找到姓名列 {!r}，实际列：{}".format(nc, fields)
                )
            wc = weight_col
            if wc and wc not in fields:
                raise ValueError(
                    "CSV 未找到权重列 {!r}，实际列：{}".format(wc, fields)
                )
            for row in reader:
                nm = _clean_name(row.get(nc))
                if not nm:
                    continue
                names.append(nm)
                weights.append(row.get(wc) if wc else 1.0)
        return names, weights

    # 纯文本：每行一名，# 开头为注释
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            names.append(raw)
            weights.append(1.0)
    return names, weights


def load_exclude(path):
    """读取排除名单：txt/json/csv 通用，取首个字段。"""
    if not path:
        return []
    if not os.path.isfile(path):
        raise FileNotFoundError("排除名单文件不存在：{}".format(path))
    ext = os.path.splitext(path)[1].lower()
    out = []
    if ext == ".json":
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else []
        for item in items:
            nm = _clean_name(item if isinstance(item, str) else item.get("name"))
            if nm:
                out.append(nm)
        return out
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            raw = line.strip().lstrip("\ufeff").strip()
            if not raw or raw.startswith("#"):
                continue
            if "," in raw:
                raw = raw.split(",")[0].strip()
            if raw:
                out.append(raw)
    return out


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #
def render_winners_text(draws, rounds):
    """生成输出文本：单轮逐行姓名；多轮带轮次小标题。"""
    lines = []
    if rounds <= 1:
        for d in draws:
            for p in d["picks"]:
                lines.append(p["name"])
    else:
        for d in draws:
            lines.append("== 第 {} 轮 ==".format(d["round"]))
            for p in d["picks"]:
                lines.append(p["name"])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(
        prog="lucky_draw.py",
        description="摇号抽签：基于 secrets 密码学安全随机数从名单中公平抽取中奖者。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python3 lucky_draw.py --input names.txt --count 3 --out winners.txt\n"
            "  python3 lucky_draw.py --input staff.csv --name-col 姓名 --weight-col 权重 --count 5 --exclude excluded.txt\n"
            "  python3 lucky_draw.py --input names.txt --count 3 --seed 42 --replay --prove draw_proof.json\n"
        ),
    )
    p.add_argument("--input", required=True, help="名单文件（txt/csv/json）")
    p.add_argument("--name-col", default=None, help="CSV/JSON 姓名列名")
    p.add_argument("--weight-col", default=None, help="CSV/JSON 权重列名（缺省等权）")
    p.add_argument("--count", type=int, default=1, help="每轮抽取人数（默认 1）")
    p.add_argument("--exclude", default=None, help="排除名单文件（txt/csv/json）")
    p.add_argument("--rounds", type=int, default=1, help="抽取轮数（默认 1）")
    p.add_argument(
        "--unique",
        action="store_true",
        help="跨轮去重：已中奖者不再进入后续轮次",
    )
    p.add_argument("--seed", type=int, default=None, help="复现审计种子（给出后切换为可复现模式）")
    p.add_argument(
        "--replay",
        action="store_true",
        help="显式开启复现审计模式，必须与 --seed 同时使用",
    )
    p.add_argument("--out", default=None, help="中奖名单输出路径")
    p.add_argument("--prove", default=None, help="证明文件（JSON）输出路径")
    p.add_argument("--quiet", action="store_true", help="仅输出结果，不打印摘要")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.replay and args.seed is None:
        print("[错误] --replay 复现审计模式必须配合 --seed 使用。", file=sys.stderr)
        return 2
    if args.count < 1:
        print("[错误] --count 至少为 1。", file=sys.stderr)
        return 2
    if args.rounds < 1:
        print("[错误] --rounds 至少为 1。", file=sys.stderr)
        return 2

    try:
        names, weights = load_names(args.input, args.name_col, args.weight_col)
        exclude = load_exclude(args.exclude)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print("[错误] 读取输入失败：{}".format(e), file=sys.stderr)
        return 2

    if not names:
        print("[错误] 名单为空，无法抽签。", file=sys.stderr)
        return 2

    exclude_set = set(exclude)
    weight_ints = normalize_weights(weights)

    candidates = []
    dup = {}
    for i, nm in enumerate(names):
        if nm in exclude_set:
            continue
        # index 取候选池内序号（0..n-1），保证证明中的索引可直接回溯到候选池条目
        candidates.append(
            {"index": len(candidates), "name": nm, "weight_int": weight_ints[i]}
        )
        dup[nm] = dup.get(nm, 0) + 1

    if not candidates:
        print("[错误] 排除后候选池为空，无法抽签。", file=sys.stderr)
        return 2

    total_slots = args.count * args.rounds
    if args.unique and total_slots > len(candidates):
        print(
            "[错误] 去重模式下需抽出 {} 人，候选池仅 {} 人。".format(
                total_slots, len(candidates)
            ),
            file=sys.stderr,
        )
        return 2

    source = SeededSource(args.seed) if args.seed is not None else CryptoSource()
    draws = draw_all(candidates, args.count, args.rounds, args.unique, source)
    winners = flatten_winners(draws)

    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    cand_hash = hash_candidates(candidates)
    win_hash = hash_winners(winners)
    commit = commitment(cand_hash, win_hash, created_at)

    out_text = render_winners_text(draws, args.rounds)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_text)

    proof_path = None
    if args.prove:
        proof = {
            "schema": PROOF_SCHEMA,
            "tool": TOOL_NAME,
            "version": TOOL_VERSION,
            "created_at": created_at,
            "mode": source.mode,
            "replay": bool(args.replay),
            "random_source": source.label,
            "seed": source.seed,
            "parameters": {
                "count": args.count,
                "rounds": args.rounds,
                "unique": bool(args.unique),
            },
            "input_file": os.path.abspath(args.input),
            "exclude_file": os.path.abspath(args.exclude) if args.exclude else None,
            "exclude": exclude,
            "candidates": candidates,
            "candidates_sha256": cand_hash,
            "draws": draws,
            "winners": winners,
            "winners_sha256": win_hash,
            "commitment_sha256": commit,
            "output_file": os.path.abspath(args.out) if args.out else None,
        }
        proof_path = args.prove
        with open(args.prove, "w", encoding="utf-8") as f:
            json.dump(proof, f, ensure_ascii=False, indent=2)

    if not args.quiet:
        dup_names = [n for n, c in dup.items() if c > 1]
        print("== 摇号抽签结果 ==")
        print("随机源     : {} ({})".format(source.label, source.mode))
        if source.seed is not None:
            print("seed       : {}".format(source.seed))
        print("候选池人数 : {}（原始 {}，排除 {}）".format(len(candidates), len(names), len(exclude)))
        if dup_names:
            print("重复名提醒 : {}（同名者在候选池中重复计数）".format("、".join(dup_names)))
        print("抽取设置   : {} 轮 × {} 人{}".format(args.rounds, args.count, "，跨轮去重" if args.unique else ""))
        print("-" * 34)
        if args.rounds <= 1:
            for i, nm in enumerate(winners, 1):
                print("{:>3}. {}".format(i, nm))
        else:
            for d in draws:
                print("第 {} 轮（池 {} 人）：".format(d["round"], d["pool_size"]))
                for i, p in enumerate(d["picks"], 1):
                    print("  {:>3}. {}".format(i, p["name"]))
        print("-" * 34)
        for d in draws:
            print("第 {} 轮熵摘要 : {}".format(d["round"], d["entropy_digest"][:32] + "..."))
        print("候选池 SHA256 : {}".format(cand_hash[:32] + "..."))
        print("中奖名单 SHA256: {}".format(win_hash[:32] + "..."))
        print("时间戳        : {}".format(created_at))
        if args.out:
            print("名单已写入    : {}".format(os.path.abspath(args.out)))
        if proof_path:
            print("证明已写入    : {}".format(os.path.abspath(proof_path)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
