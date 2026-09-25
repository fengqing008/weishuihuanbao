#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ali-asr 兼容入口：转发到 scripts/transcribe.py（部分链路按技能根目录查找）。"""
import pathlib
import runpy
import sys

TARGET = pathlib.Path(__file__).resolve().parent / 'scripts' / 'transcribe.py'
sys.argv[0] = str(TARGET)
runpy.run_path(str(TARGET), run_name='__main__')
