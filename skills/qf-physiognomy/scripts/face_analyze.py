#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""face_analyze.py —— 面容特征录入与校验工具（相学文化技能）

职责边界：
  本脚本负责【读取照片基本信息 + 生成特征模板 + 校验特征是否合规】，
  不承担视觉识别。面部形态的观察由使用本技能的 AI 助手（多模态读图）完成，
  或由使用者按 --template 人工录入，最终都以 features JSON 为准。

用法：
  python3 scripts/face_analyze.py --image 照片.jpg                 # 读图信息 + 生成待填模板
  python3 scripts/face_analyze.py --image 照片.jpg --out f.json    # 模板写入文件
  python3 scripts/face_analyze.py --template --out f.json          # 仅出模板
  python3 scripts/face_analyze.py --validate f.json                # 校验特征合规性
  python3 scripts/face_analyze.py --manual f.json --image 照片.jpg # 人工录入 + 规范化输出
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

PARTS = ["face_shape", "brow", "eye", "nose", "mouth", "ear", "forehead", "chin"]
PART_CN = {"face_shape": "脸型", "brow": "眉", "eye": "眼", "nose": "鼻",
           "mouth": "口", "ear": "耳", "forehead": "额", "chin": "颏"}

DISCLAIMER = ("本报告为中国传统相学文化的知识介绍与形态描述整理，不构成任何判断、"
              "预测或决策依据。面部形态识别存在误差，结果仅供文化了解。")


def load_vocab():
    p = os.path.join(ASSETS, "vocab.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def image_info(path):
    """读取图片基本信息；缺 Pillow 时降级为仅文件信息。"""
    info = {"path": path, "exists": os.path.exists(path)}
    if not info["exists"]:
        return info, ["文件不存在: %s" % path]
    warn = []
    info["size_bytes"] = os.path.getsize(path)
    try:
        from PIL import Image
        with Image.open(path) as im:
            info["format"] = im.format
            info["mode"] = im.mode
            info["width"], info["height"] = im.size
            info["ratio"] = round(im.size[0] / float(im.size[1]), 3)
    except ImportError:
        warn.append("未安装 Pillow，跳过尺寸读取；不影响特征录入与后续流程")
    except Exception as e:
        warn.append("图片读取失败：%s" % e)
    return info, warn


def build_template():
    v = load_vocab()
    tpl = {"source_image": "", "filled_by": "ai|manual",
           "face_shape": {"value": "", "note": ""},
           "santing": {"upper": "", "middle": "", "lower": ""},
           "features": {}}
    for k in PARTS:
        if k == "face_shape":
            continue
        tpl["features"][k] = {"value": "", "note": ""}
    tpl["_vocab_hint"] = {k: v.get(k, []) for k in PARTS}
    return tpl


def normalize(data, vocab):
    """把录入数据规范化：只保留合法特征词，超出词库的记入 warnings。"""
    warnings = []
    out = {"source_image": data.get("source_image", ""),
           "filled_by": data.get("filled_by", "manual"),
           "features": {}, "santing": data.get("santing", {}),
           "warnings": []}

    fs = data.get("face_shape")
    if isinstance(fs, dict):
        val = (fs.get("value") or "").strip()
        out["face_shape"] = {"value": val, "note": fs.get("note", "")}
    else:
        out["face_shape"] = {"value": (fs or "").strip(), "note": ""}
    if out["face_shape"]["value"] and out["face_shape"]["value"] not in vocab["face_shape"]:
        warnings.append("脸型「%s」不在词库内，规则库将无对应条文" % out["face_shape"]["value"])

    feats = data.get("features", {})
    for part in PARTS:
        if part == "face_shape":
            continue
        raw = feats.get(part)
        if raw is None:
            continue
        if isinstance(raw, dict):
            val = (raw.get("value") or "").strip()
            note = raw.get("note", "")
        else:
            val, note = (raw or "").strip(), ""
        if not val:
            continue
        out["features"][part] = {"value": val, "note": note}
        if val not in vocab.get(part, []):
            warnings.append("%s「%s」不在词库内，规则库将无对应条文" % (PART_CN[part], val))

    if not out["features"] and not out["face_shape"]["value"]:
        warnings.append("未录入任何特征，报告将为空壳")
    out["warnings"] = warnings
    return out


def cmd_analyze(a):
    vocab = load_vocab()
    if a.manual:
        with open(a.manual, encoding="utf-8") as f:
            data = json.load(f)
        if a.image:
            data["source_image"] = a.image
        norm = normalize(data, vocab)
        _emit(norm, a.out, "人工录入特征")
        return 0

    info, warn = image_info(a.image) if a.image else ({}, [])
    tpl = build_template()
    tpl["source_image"] = a.image or ""
    tpl["image_info"] = info
    tpl["warnings"] = list(warn)
    payload = {"image_info": info, "template": tpl,
               "usage": "由多模态读图或人工填写 template 后，用 rule_engine.py 匹配条文",
               "disclaimer": DISCLAIMER}
    _emit(payload, a.out, "特征模板")
    return 0


def _emit(obj, out, what):
    txt = json.dumps(obj, ensure_ascii=False, indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(txt + "\n")
        print("[OK] %s 已写入 %s" % (what, out))
    else:
        print(txt)


def cmd_validate(a):
    vocab = load_vocab()
    with open(a.validate, encoding="utf-8") as f:
        data = json.load(f)
    norm = normalize(data, vocab)
    n = len(norm["features"]) + (1 if norm["face_shape"]["value"] else 0)
    print("[校验] %s" % a.validate)
    print("  有效特征数：%d" % n)
    for w in norm["warnings"]:
        print("  [WARN] " + w)
    if not norm["warnings"]:
        print("  全部特征均在词库内，可通过 rule_engine.py 匹配条文")
    return 0 if n else 1


def main():
    ap = argparse.ArgumentParser(description="面容特征录入与校验（相学文化）")
    ap.add_argument("--image", help="照片路径（读取基本信息并生成模板）")
    ap.add_argument("--manual", help="人工录入的特征 JSON")
    ap.add_argument("--template", action="store_true", help="仅生成空白模板")
    ap.add_argument("--validate", help="校验指定特征 JSON 是否合规")
    ap.add_argument("--out", help="输出文件路径")
    a = ap.parse_args()

    if a.validate:
        return cmd_validate(a)
    if a.image or a.manual or a.template:
        return cmd_analyze(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
