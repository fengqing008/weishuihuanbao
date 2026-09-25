#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_proof.py — 摇号抽签证明文件校验器。

读取 lucky_draw.py --prove 生成的 JSON 证明，逐项校验：
  1. 候选池哈希是否与内嵌候选池一致（名单未被篡改）；
  2. 中奖名单哈希是否与内嵌名单一致（结果未被篡改）；
  3. winners 是否与各轮 picks 的顺序、姓名逐项吻合（结构自洽）；
  4. 每个 pick 的 index 是否指向候选池中同名的条目（索引可追溯）；
  5. 哈希承诺值是否与名单哈希、结果哈希、时间戳三者合成一致；
  6. mode=seeded 时用同一 seed 完整重放抽取，比对结果是否逐项相同。

退出码：0=校验一致；1=校验不符；2=文件或参数错误。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import lucky_draw as ld
except Exception as e:  # pragma: no cover
    print("[错误] 无法导入 lucky_draw.py：{}".format(e), file=sys.stderr)
    raise SystemExit(2)


def _ok(msg):
    print("  [通过] {}".format(msg))


def _fail(msg):
    print("  [失败] {}".format(msg))


def verify(proof, verbose=True):
    """执行全部校验，返回 (是否一致, 消息列表)。"""
    problems = []

    def check(cond, ok_msg, fail_msg):
        if cond:
            if verbose:
                _ok(ok_msg)
        else:
            problems.append(fail_msg)
            if verbose:
                _fail(fail_msg)
        return cond

    # 1. 基本结构
    schema = proof.get("schema", "")
    if not check(
        schema == ld.PROOF_SCHEMA,
        "证明结构标识有效：{}".format(schema),
        "证明结构标识异常：期望 {}，实际 {}".format(ld.PROOF_SCHEMA, schema),
    ):
        return False, problems

    candidates = proof.get("candidates") or []
    winners = proof.get("winners") or []
    draws = proof.get("draws") or []
    params = proof.get("parameters") or {}

    if not candidates:
        problems.append("候选池为空")
        return False, problems

    # 2. 候选池哈希
    recomputed_c = ld.hash_candidates(candidates)
    check(
        recomputed_c == proof.get("candidates_sha256"),
        "候选池 SHA256 与记录一致（名单未被篡改）",
        "候选池 SHA256 不一致：记录 {}，实算 {}".format(
            proof.get("candidates_sha256"), recomputed_c
        ),
    )

    # 3. 中奖名单哈希
    recomputed_w = ld.hash_winners(winners)
    check(
        recomputed_w == proof.get("winners_sha256"),
        "中奖名单 SHA256 与记录一致（结果未被篡改）",
        "中奖名单 SHA256 不一致：记录 {}，实算 {}".format(
            proof.get("winners_sha256"), recomputed_w
        ),
    )

    # 4. 结构自洽：winners 与 draws 逐项吻合
    flat = ld.flatten_winners(draws)
    check(
        flat == winners,
        "winners 与各轮 picks 的顺序、姓名逐项吻合（共 {} 人）".format(len(winners)),
        "winners 与 draws 不一致：draws 展开 {}，winners {}".format(flat, winners),
    )

    # 5. 索引可追溯
    cand_by_index = {c["index"]: c for c in candidates}
    idx_ok = True
    idx_err = ""
    for d in draws:
        for p in d["picks"]:
            i = p.get("index")
            c = cand_by_index.get(i)
            if c is None:
                idx_ok = False
                idx_err = "第 {} 轮出现无法回溯的索引：{}".format(d.get("round"), i)
                break
            if c["name"] != p["name"]:
                idx_ok = False
                idx_err = "第 {} 轮索引 {} 指向 {}，与姓名 {} 不符".format(
                    d.get("round"), i, c["name"], p["name"]
                )
                break
        if not idx_ok:
            break
    check(idx_ok, "全部抽取索引均可回溯到候选池同名条目", idx_err or "索引校验失败")

    # 6. 每轮熵摘要自洽
    ent_ok = True
    ent_err = ""
    for d in draws:
        recomputed_e = ld.entropy_digest(d.get("round"), d.get("random_trace") or [])
        if recomputed_e != d.get("entropy_digest"):
            ent_ok = False
            ent_err = "第 {} 轮熵摘要不匹配".format(d.get("round"))
            break
    check(ent_ok, "每轮随机熵摘要与随机轨迹自洽", ent_err or "熵摘要校验失败")

    # 7. 总承诺值
    recomputed_commit = ld.commitment(
        proof.get("candidates_sha256", ""),
        proof.get("winners_sha256", ""),
        proof.get("created_at", ""),
    )
    check(
        recomputed_commit == proof.get("commitment_sha256"),
        "承诺值 SHA256 与名单哈希+结果哈希+时间戳合成一致",
        "承诺值不一致：记录 {}，实算 {}".format(
            proof.get("commitment_sha256"), recomputed_commit
        ),
    )

    # 8. 去重模式的人数上限
    if params.get("unique"):
        total = params.get("count", 1) * params.get("rounds", 1)
        check(
            len(set(winners)) == len(winners) and len(winners) <= len(candidates),
            "去重模式下中奖者互不重复，且不超过候选池人数",
            "去重模式校验失败：中奖 {} 人，唯一 {} 人".format(
                len(winners), len(set(winners))
            ),
        )

    # 9. 复现重放（仅 seeded 模式可完整重放）
    mode = proof.get("mode")
    if mode == "seeded":
        seed = proof.get("seed")
        src = ld.SeededSource(seed)
        replay_draws = ld.draw_all(
            candidates,
            params.get("count", 1),
            params.get("rounds", 1),
            bool(params.get("unique")),
            src,
        )
        replay_winners = ld.flatten_winners(replay_draws)
        check(
            replay_winners == winners,
            "seed={} 完整重放成功，结果逐项复现".format(seed),
            "重放结果与记录不一致：重放 {}，记录 {}".format(replay_winners, winners),
        )
        total_trace = [t for d in draws for t in (d.get("random_trace") or [])]
        replay_trace = [t for d in replay_draws for t in d["random_trace"]]
        check(
            replay_trace == total_trace,
            "全部 {} 次随机轨迹逐位复现".format(len(replay_trace)),
            "随机轨迹不一致：重放 {}，记录 {}".format(replay_trace, total_trace),
        )
    else:
        print(
            "  [说明] 随机源为密码学模式（secrets），随机序列按设计不可重放；"
            "已完成结构自洽与哈希承诺校验。"
        )

    return len(problems) == 0, problems


def build_parser():
    p = argparse.ArgumentParser(
        prog="verify_proof.py",
        description="校验 lucky_draw.py 生成的抽签证明文件。",
    )
    p.add_argument("--proof", required=True, help="证明文件（JSON）路径")
    p.add_argument("--quiet", action="store_true", help="仅输出最终结论")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if not os.path.isfile(args.proof):
        print("[错误] 证明文件不存在：{}".format(args.proof), file=sys.stderr)
        return 2

    try:
        with open(args.proof, "r", encoding="utf-8") as f:
            proof = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print("[错误] 证明文件解析失败：{}".format(e), file=sys.stderr)
        return 2

    if not args.quiet:
        print("== 抽签证明校验 ==")
        print("证明文件   : {}".format(os.path.abspath(args.proof)))
        print("模式       : {}".format(proof.get("mode")))
        print("随机源     : {}".format(proof.get("random_source")))
        print("seed       : {}".format(proof.get("seed")))
        print("生成时间   : {}".format(proof.get("created_at")))
        print("中奖人数   : {}".format(len(proof.get("winners") or [])))
        print("-" * 34)

    ok, problems = verify(proof, verbose=not args.quiet)

    print("-" * 34)
    if ok:
        print("[结论] 校验一致（exit 0）：名单、结果、索引与承诺值全部自洽。")
        return 0
    print("[结论] 校验不符（exit 1）：发现 {} 处问题。".format(len(problems)))
    for p in problems:
        print("  - {}".format(p))
    return 1


if __name__ == "__main__":
    sys.exit(main())
