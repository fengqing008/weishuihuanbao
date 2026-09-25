#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接受 Word 文档中的所有修订（Track Changes），产出干净定稿。

移植自 anthropics/skills docx skill 的 accept_changes 脚本（LibreOffice 宏方案）。
对比 pandoc --track-changes=accept 的优势：能正确处理"整段删除后合并到下一段"，
不会留下空的自动编号段落。

用法：
    python accept_changes.py 修订稿.docx 定稿.docx
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

LIBREOFFICE_PROFILE = "/tmp/libreoffice_docx_profile"
MACRO_DIR = f"{LIBREOFFICE_PROFILE}/user/basic/Standard"

ACCEPT_CHANGES_MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub AcceptAllTrackedChanges()
        Dim document As Object
        Dim dispatcher As Object
        document = ThisComponent.CurrentController.Frame
        dispatcher = createUnoService("com.sun.star.frame.DispatchHelper")
        dispatcher.executeDispatch(document, ".uno:AcceptAllTrackedChanges", "", 0, Array())
        ThisComponent.store()
        ThisComponent.close(True)
    End Sub
</script:module>"""


def _setup_macro() -> bool:
    macro_file = Path(MACRO_DIR) / "Module1.xba"
    if macro_file.exists() and "AcceptAllTrackedChanges" in macro_file.read_text():
        return True
    subprocess.run(
        ["soffice", "--headless",
         f"-env:UserInstallation=file://{LIBREOFFICE_PROFILE}", "--terminate_after_init"],
        capture_output=True, timeout=30, check=False,
    )
    Path(MACRO_DIR).mkdir(parents=True, exist_ok=True)
    macro_file.write_text(ACCEPT_CHANGES_MACRO)
    return True


def accept_changes(input_file: str, output_file: str) -> None:
    src = Path(input_file)
    out = Path(output_file)
    if not src.exists() or src.suffix.lower() != ".docx":
        print(f"Error: 输入必须是 .docx 文件: {src}", file=sys.stderr)
        sys.exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out)
    if not _setup_macro():
        print("Error: LibreOffice 宏初始化失败", file=sys.stderr)
        sys.exit(1)
    cmd = [
        "soffice", "--headless",
        f"-env:UserInstallation=file://{LIBREOFFICE_PROFILE}", "--norestore",
        "vnd.sun.star.script:Standard.Module1.AcceptAllTrackedChanges?language=Basic&location=application",
        str(out.absolute()),
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    print(f"已接受全部修订：{src} -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="接受 Word 全部修订，产出定稿")
    ap.add_argument("input_file", help="含修订的 .docx")
    ap.add_argument("output_file", help="定稿输出 .docx")
    args = ap.parse_args()
    accept_changes(args.input_file, args.output_file)
