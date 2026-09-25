#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP一键流水线（四件齐备）
- 编排 ①SOP Word ②流程图mmd ③PNG渲染 ④HTML交互页 ⑤质量门禁
- 每步独立可重试；任一子步骤失败降级而不中断整体
- 结束输出四件齐备清单（manifest.json）供入库核验

Usage:
    python3 scripts/sop_pipeline.py --project "示例PPP" --baseline-date "2019年7月" \
        --output-dir outputs/
    python3 scripts/sop_pipeline.py --project "示例项目B" --baseline-date "2021年3月" \
        --output-dir outputs/ --no-render-png --skip-word
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
FLOW_TYPES = ["总图", "差异处理"]


def run_step(label, cmd, retries=1):
    """执行单个子步骤：失败重试 retries 次，仍失败返回 (False, 错误摘要)。

    任何异常都不静默吞掉：返回 False 并记录 stderr 尾部，由主流程决定降级路径。
    """
    last_err = ""
    for attempt in range(retries + 1):
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SKILL_ROOT))
        if proc.returncode == 0:
            return True, proc.stdout.strip()
        last_err = (proc.stderr or proc.stdout or "").strip()[-500:]
        if attempt < retries:
            print(f"[重试] {label} 第 {attempt + 2} 次执行")
    print(f"[降级] {label} 失败，跳过该步骤：{last_err}")
    return False, last_err


def main():
    ap = argparse.ArgumentParser(description="工程结算SOP一键流水线")
    ap.add_argument("--project", required=True, help="项目名称，如 示例PPP")
    ap.add_argument("--baseline-date", required=True, help="基准价日期，如 2019年7月")
    ap.add_argument("--output-dir", default="outputs/", help="产物输出目录")
    ap.add_argument("--title", help="SOP文档标题（默认 <项目>竣工结算SOP）")
    ap.add_argument("--theme", default="zinc-light", help="PNG渲染主题")
    ap.add_argument("--width", type=int, default=1800, help="PNG宽度")
    ap.add_argument("--render-png", dest="render_png", action="store_true", default=True)
    ap.add_argument("--no-render-png", dest="render_png", action="store_false",
                    help="跳过PNG渲染（无Node.js环境时的兜底开关）")
    ap.add_argument("--skip-word", action="store_true", help="跳过Word生成（仅出流程图）")
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    title = args.title or f"{args.project}竣工结算SOP"
    stem = title.replace(" ", "_")

    manifest = {"project": args.project, "baseline_date": args.baseline_date,
                "title": title, "artifacts": {}, "degraded": [], "status": "ok"}

    # ① SOP Word
    docx_path = out / f"{stem}_V1.0.docx"
    if args.skip_word:
        manifest["degraded"].append("word:skipped")
    else:
        ok, msg = run_step("①SOP Word", [
            sys.executable, str(SCRIPTS / "sop_docx_generator.py"),
            "--title", title, "--project-name", args.project,
            "--baseline-date", args.baseline_date, "--output", str(docx_path),
        ])
        manifest["artifacts"]["docx"] = str(docx_path) if ok else None
        if not ok:
            manifest["degraded"].append("word:failed")

    # ② 流程图 mmd（总图 + 差异处理）
    mmd_files = []
    for ftype in FLOW_TYPES:
        mmd_path = out / f"{stem}_流程图_{ftype}.mmd"
        ok, _ = run_step(f"②流程图mmd({ftype})", [
            sys.executable, str(SCRIPTS / "sop_flowchart_mermaid.py"),
            "--type", ftype, "--render", "mmd", "--output", str(mmd_path),
        ])
        if ok and mmd_path.exists():
            mmd_files.append(str(mmd_path))
        else:
            manifest["degraded"].append(f"mmd:{ftype}:failed")
    manifest["artifacts"]["mmd"] = mmd_files

    # ③ PNG 渲染（依赖 pretty-mermaid + Node.js；失败则降级保留 mmd）
    png_files = []
    if args.render_png and mmd_files:
        for mmd in mmd_files:
            png_path = Path(mmd).with_suffix(".png")
            ok, _ = run_step(f"③PNG渲染({png_path.name})", [
                sys.executable, str(SCRIPTS / "sop_flowchart_mermaid.py"),
                "--type", "总图" if "总图" in mmd else "差异处理",
                "--render", "png", "--theme", args.theme,
                "--width", str(args.width), "--output", str(png_path),
            ])
            if ok and png_path.exists():
                png_files.append(str(png_path))
            else:
                manifest["degraded"].append(f"png:{png_path.name}:failed")

    # ④ HTML 交互页（缺 mmd 文件则跳过）
    html_path = out / f"{stem}_流程图.html"
    if mmd_files:
        ok, _ = run_step("④HTML交互页", [
            sys.executable, str(SCRIPTS / "sop_flowchart_html.py"),
            "--mmd-files", *mmd_files, "--output", str(html_path),
        ])
        manifest["artifacts"]["html"] = str(html_path) if ok else None
        if not ok:
            manifest["degraded"].append("html:failed")
    else:
        manifest["artifacts"]["html"] = None
        manifest["degraded"].append("html:no-mmd")

    # ⑤ 质量门禁（有 docx 才跑）
    if manifest["artifacts"].get("docx"):
        ok, out_txt = run_step("⑤质量门禁", [
            sys.executable, str(SCRIPTS / "sop_quality_check.py"),
            "--file", manifest["artifacts"]["docx"],
        ])
        manifest["quality_gate"] = {"passed": ok, "report": out_txt[-1500:]}

    # 四件齐备核验
    four = [manifest["artifacts"].get("docx"),
            bool(manifest["artifacts"].get("mmd")),
            bool(png_files) or None,
            manifest["artifacts"].get("html")]
    manifest["artifacts"]["png"] = png_files
    manifest["four_pieces_complete"] = all(four)
    if not manifest["four_pieces_complete"]:
        manifest["status"] = "degraded"

    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(f"\n✓ 流水线结束：{manifest['status']}，四件齐备={manifest['four_pieces_complete']}")
    print(f"✓ 清单已写出：{manifest_path}")
    return 0 if manifest["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
