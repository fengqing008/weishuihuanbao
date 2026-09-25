#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 仓库流量取数工具

用法：
    # 单仓库取数
    python3 traffic_report.py --repo owner/name --token $GH_TOKEN

    # 多仓库批量
    python3 traffic_report.py --repos repos.txt --token $GH_TOKEN

    # 输出 JSON 便于入库/对比
    python3 traffic_report.py --repo owner/name --token $GH_TOKEN --json out.json

    # 与上次快照对比，显示增量
    python3 traffic_report.py --repo owner/name --token $GH_TOKEN --baseline snapshot.json

指标说明：
    views   —— 仓库页面访问量（近 14 天，含每日明细）
    clones  —— 仓库克隆量（近 14 天，含每日明细）
    stars/forks/watchers —— 当前累计值
    releases —— Release 资源下载量（若有 Release）

重要限制：
    GitHub 不提供公开仓库的「技能文件下载次数」指标。
    技能库场景下，views 与 clones 是仅有的可得流量数据。
    全部指标均为近 14 天滚动窗口，更早数据无法获取。
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error

API = "https://api.github.com"


def call(path: str, token: str):
    req = request.Request(
        f"{API}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "traffic-report",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:200]
        return {"_error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"_error": str(e)}


def collect(repo: str, token: str):
    out = {"repo": repo, "fetched_at": datetime.now(timezone.utc).isoformat()}

    info = call(f"/repos/{repo}", token)
    if "_error" in info:
        out["error"] = info["_error"]
        return out

    out["full_name"] = info.get("full_name")
    out["private"] = info.get("private")
    out["created_at"] = info.get("created_at")
    out["pushed_at"] = info.get("pushed_at")
    out["stars"] = info.get("stargazers_count", 0)
    out["forks"] = info.get("forks_count", 0)
    out["watchers"] = info.get("subscribers_count", 0)
    out["open_issues"] = info.get("open_issues_count", 0)
    out["size_kb"] = info.get("size", 0)

    for key, ep in (("views", "views"), ("clones", "clones")):
        d = call(f"/repos/{repo}/traffic/{ep}", token)
        if "_error" in d:
            out[key] = {"error": d["_error"]}
        else:
            out[key] = {
                "total": d.get("count", 0),
                "uniques": d.get("uniques", 0),
                "daily": [
                    {"date": v["timestamp"][:10], "count": v["count"], "uniques": v["uniques"]}
                    for v in d.get(ep, [])
                ],
            }

    ref = call(f"/repos/{repo}/traffic/popular/referrers", token)
    out["referrers"] = ref if isinstance(ref, list) else []

    paths = call(f"/repos/{repo}/traffic/popular/paths", token)
    out["popular_paths"] = paths if isinstance(paths, list) else []

    rel = call(f"/repos/{repo}/releases", token)
    if isinstance(rel, list) and rel:
        total_dl = 0
        items = []
        for r in rel:
            for a in r.get("assets", []):
                total_dl += a.get("download_count", 0)
                items.append({
                    "release": r.get("tag_name"),
                    "asset": a.get("name"),
                    "downloads": a.get("download_count", 0),
                })
        out["release_downloads"] = {"total": total_dl, "assets": items}
    else:
        out["release_downloads"] = {"total": 0, "assets": []}

    return out


def render(data: dict, baseline: dict | None = None):
    if "error" in data:
        print(f"✗ {data['repo']}: {data['error']}")
        return

    print(f"\n{'=' * 58}")
    print(f" {data['full_name']}  ({'私有' if data['private'] else '公开'})")
    print(f"{'=' * 58}")
    print(f"  Stars {data['stars']}  |  Forks {data['forks']}  |  Watchers {data['watchers']}")

    def delta(cur, old, label):
        if baseline is None:
            return ""
        key = label
        prev = baseline.get(key, 0)
        d = cur - prev
        return f"   (较上次 {'+' if d >= 0 else ''}{d})"

    print(f"\n  【访问量 views】近 14 天")
    v = data.get("views", {})
    if "error" in v:
        print(f"    ⚠️ {v['error']}")
    else:
        print(f"    总次数 {v['total']}  独立访客 {v['uniques']}{delta(v['total'], (baseline or {}).get('views_total', 0), 'views_total')}")
        daily = [d for d in v.get("daily", []) if d["count"] > 0]
        if daily:
            for d in daily:
                print(f"      {d['date']}   {d['count']:4d} 次 / {d['uniques']:3d} 人")
        else:
            print("      （14 天内无访问记录）")

    print(f"\n  【克隆量 clones】近 14 天")
    c = data.get("clones", {})
    if "error" in c:
        print(f"    ⚠️ {c['error']}")
    else:
        print(f"    总次数 {c['total']}  独立克隆者 {c['uniques']}{delta(c['total'], (baseline or {}).get('clones_total', 0), 'clones_total')}")
        daily = [d for d in c.get("daily", []) if d["count"] > 0]
        if daily:
            for d in daily:
                print(f"      {d['date']}   {d['count']:4d} 次 / {d['uniques']:3d} 人")
        else:
            print("      （14 天内无克隆记录）")

    rd = data.get("release_downloads", {})
    print(f"\n  【Release 下载量】")
    if rd.get("total"):
        print(f"    总计 {rd['total']}")
        for a in rd.get("assets", [])[:10]:
            print(f"      {a['release']}/{a['asset']}: {a['downloads']}")
    else:
        print("    （无 Release 或无下载）")

    if data.get("referrers"):
        print(f"\n  【引用来源】")
        for r in data["referrers"][:10]:
            print(f"    {r.get('referrer')}: {r.get('count')} 次 / {r.get('uniques')} 人")
    else:
        print(f"\n  【引用来源】无")

    if data.get("popular_paths"):
        print(f"\n  【热门页面】")
        for p in data["popular_paths"][:5]:
            print(f"    {p.get('path')}: {p.get('count')} 次")

    print()


def main():
    ap = argparse.ArgumentParser(description="GitHub 仓库流量取数")
    ap.add_argument("--repo", help="单个仓库 owner/name")
    ap.add_argument("--repos", help="仓库清单文件（每行一个 owner/name）")
    ap.add_argument("--token", default=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    ap.add_argument("--json", dest="json_out", help="输出 JSON 报告")
    ap.add_argument("--baseline", help="上次快照 JSON，用于计算增量")
    ap.add_argument("--quiet", action="store_true", help="仅输出 JSON 不打印报告")
    args = ap.parse_args()

    if not args.token:
        print("✗ 缺少 Token：用 --token 或设置 GH_TOKEN 环境变量", file=sys.stderr)
        return 1

    repos = []
    if args.repo:
        repos.append(args.repo)
    if args.repos:
        p = Path(args.repos)
        if not p.is_file():
            print(f"✗ 清单不存在：{p}", file=sys.stderr)
            return 1
        repos += [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
    if not repos:
        ap.error("需要 --repo 或 --repos")

    baseline = None
    if args.baseline and Path(args.baseline).is_file():
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    results = []
    for repo in repos:
        data = collect(repo, args.token)
        results.append(data)
        if not args.quiet:
            base = None
            if baseline:
                # 单仓库时直接对比顶层；多仓库时按 repo 名查
                base = baseline if baseline.get("repo") == repo else baseline.get(repo)
            render(data, base)

    if args.json_out:
        payload = results[0] if len(results) == 1 else {r["repo"]: r for r in results}
        Path(args.json_out).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON 已写入：{args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
