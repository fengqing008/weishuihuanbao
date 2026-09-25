#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""image-enhancer 批量增强入口

用法：
  python3 scripts/batch_enhance.py raw/ out/ --preset ppt --jobs 4 \
      --manifest out/manifest.json --failed-log out/failed.log --resume

特性：目录递归、保留相对路径、单图异常隔离不中断、manifest 断点续跑、失败清单对账。
退出码：0 全部成功或部分成功（失败项见 failed.log）；1 参数错误；2 源目录不可读。
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enhance import PRESETS, SUPPORTED, check_source, enhance  # noqa: E402


def collect(src_dir: Path):
    files, skipped = [], []
    for p in sorted(src_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SUPPORTED:
            skipped.append((p, "unsupported_format"))
            continue
        ok, reason = check_source(p)
        if ok:
            files.append(p)
        else:
            skipped.append((p, reason))
    return files, skipped


def load_manifest(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"params": {}, "items": []}
    return {"params": {}, "items": []}


def main():
    ap = argparse.ArgumentParser(description="image-enhancer 批量增强入口")
    ap.add_argument("src_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--preset", default="ppt", choices=list(PRESETS))
    ap.add_argument("--scale", type=float)
    ap.add_argument("--sharpen", type=float)
    ap.add_argument("--denoise", type=int, choices=[0, 1])
    ap.add_argument("--jobs", type=int, default=1, help="并发数，内存紧张时取 1")
    ap.add_argument("--manifest", default="manifest.json")
    ap.add_argument("--failed-log", default="failed.log")
    ap.add_argument("--resume", action="store_true", help="跳过 manifest 中 status=done 的项")
    args = ap.parse_args()

    src_dir, out_dir = Path(args.src_dir), Path(args.out_dir)
    if not src_dir.is_dir():
        sys.stderr.write(f"源目录不可读：{src_dir}\n")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    man_path, fail_path = Path(args.manifest), Path(args.failed_log)

    man = load_manifest(man_path)
    man["params"] = {"preset": args.preset, "scale": args.scale, "sharpen": args.sharpen,
                     "denoise": args.denoise, "jobs": args.jobs}
    done = {i["src"] for i in man["items"] if i.get("status") == "done"}

    files, skipped = collect(src_dir)
    tasks, results, failed = [], [], []
    for p in files:
        rel = p.relative_to(src_dir)
        if args.resume and str(p) in done:
            results.append({"src": str(p), "status": "skipped_done"})
            continue
        tasks.append((p, out_dir / rel.parent / f"{p.stem}_enhanced.png"))

    def work(pair):
        p, dst = pair
        try:
            cfg, alpha, out_size, mode = enhance(
                p, dst, args.preset, args.scale, args.sharpen, args.denoise)
            return {"src": str(p), "dst": str(dst), "params": cfg,
                    "in_size": list(__import__("PIL.Image", fromlist=["Image"]).open(p).size),
                    "out_size": list(out_size), "out_mode": mode, "alpha_preserved": alpha,
                    "out_bytes": dst.stat().st_size, "status": "done"}
        except Exception as exc:
            return {"src": str(p), "dst": str(dst), "status": "failed",
                    "reason": f"{type(exc).__name__}", "action": "记入 failed.log 并继续"}

    if tasks:
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            for res in pool.map(work, tasks):
                (failed if res["status"] == "failed" else results).append(res)

    failed += [{"src": str(p), "reason": r, "status": "failed",
                "action": "非位图或源图不可用，转 image-tools-suite 或跳过"} for p, r in skipped]
    man["items"] = [i for i in man["items"] if i.get("status") == "done"] + results + failed
    man["summary"] = {
        "total": len(files), "done": sum(1 for i in man["items"] if i["status"] == "done"),
        "failed": len(failed), "skipped": len(skipped),
    }
    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    fail_path.write_text("".join(
        f"{i['src']} | {i.get('reason','')} | {i.get('action','')}\n" for i in failed),
        encoding="utf-8")

    print(json.dumps({"summary": man["summary"], "manifest": str(man_path),
                      "failed_log": str(fail_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
