---
name: image-enhancer
display_name: 图像增强
version: 1.0.0
description: 图像与截图综合增强流水线技能。在真实像素上做一趟流水线处理：分辨率提升（LANCZOS 重采样）、锐化（UnsharpMask 边缘增强）、去噪与 JPEG 压缩伪影清理、对比度与饱和度校正、透明通道与色彩模式保真，并按用途（汇报PPT、文档扫描、网页、印刷、社交平台）套用固化预设，支持整目录批量增强、失败清单对账与断点续跑。适用场景：汇报或PPT里的截图放大后发虚、文档与合同扫描件清晰度不足、聊天与网页截图文字糊、老照片轻微模糊需要提清、整批截图统一规格后入档。中英触发词：图像增强、图片变清晰、截图增强、截图变清晰、锐化、去噪、压缩伪影清理、升清、批量增强图片、image enhancer、enhance image、sharpen screenshot、denoise image、image quality improvement。
author: 清风明月
slug: qf-image-enhancer
category: 科技
tags:
- 图像增强
- 图片变清晰
- 截图增强
- 锐化
- 去噪
- 批量增强
---

## 〇、专家级路由（v1.0.0）

**专家定位**：把发虚的截图、带噪的压缩图、要放进汇报与文档的位图，在一趟流水线里做完分辨率提升、锐化、去噪、压缩伪影清理与用途化调参，并交出可逐张核对的增强交付包。

**五维评估**：
- 适用场景：①汇报PPT与文档里的界面截图发虚 ②合同与档案扫描件清晰度不足 ③聊天、网页截图放大后文字糊 ④老照片轻微模糊需要提清 ⑤整目录截图统一规格后入档
- 能力边界：只做像素级增强与真实重采样，不做生成式补细节、不做图片改字换文案、不做风格重绘、不做人脸修复；"纯放大且要求凭空补细节"的场景转 ai-upscaler
- 依赖资产：scripts/enhance.py（单图增强入口）、scripts/batch_enhance.py（批量入口）、references/quality-checklist.md（质检清单）、references/output-template.md（交付模板）、references/case-library.md（案例库）
- 交付质量：增强图与增强前后对比报告双交付；含文字截图须过 OCR 抽检前 5 行可读；锐化后不得出现可见白边与振铃
- 性能表现：单张 1080p 图 0.3-1.5 秒（Pillow CPU，2x 重采样＋锐化）；批量 100 张约 1-3 分钟；单边上限 4096px，超出先缩后放

**四级响应（L1-L4）**：
- L1 轻量问答（走哪个预设、锐化强度取多少）→ 按第五节预设表直接回答
- L2 标准任务（单张增强）→ 走第四节 1-7 步基础流程，过齐检查点
- L3 复杂任务（批量增强＋按用途分类）→ 加跑 scripts/batch_enhance.py，输出 manifest.json 与 failed.log 对账
- L4 专家任务（汇报级或归档级交付包）→ 全流程 ＋ 第十节范例复用 ＋ 按 references/output-template.md 出增强前后对比报告

**黄金窗口**：单批 10-200 张；输入单边 320-4096px；锐化强度 0.8-2.0；放大倍数优先取 2x，印刷件取 3x
**专家件索引**：references/case-library.md、references/quality-checklist.md、references/output-template.md、scripts/enhance.py、scripts/batch_enhance.py

## 一、定位声明

本技能是位图综合增强执行器：对分辨率不足、边缘发虚、带压缩噪点、对比度偏低的图片与截图做一趟流水线处理，输出可直接进汇报、文档与归档的增强图。

与 ai-upscaler（纯放大）的能力边界差异必须说清：
- ai-upscaler 解决"尺寸不够"——用 AI 模型把低分辨率图放大到 2x/4x，可能臆造细节，产出物不宜作证据图归档；
- 本技能解决"画质不够"——在真实像素上做重采样、锐化、去噪、色调校正，并按用途固化参数、把批量对账与质检做全，不生成新细节；
- 两者可串联：先用本技能去噪与校正对比度，再交 ai-upscaler 放大；只有一个放大诉求时，用本技能的 LANCZOS 重采样即可，无需 AI 介入。

## 二、触发条件

命中任一即触发：
- 用户提到触发词："图像增强 / 图片变清晰 / 截图增强 / 截图变清晰 / 锐化 / 去噪 / 压缩伪影清理 / 升清 / 批量增强图片 / image enhancer / enhance image / sharpen screenshot / denoise"
- 用户上传截图或照片并描述"放大后糊、文字看不清、有点脏、颜色发灰"
- 输入图要放进 PPT、可研报告、竣工资料、公众号推文，需在放大后仍保持文字可读
- 用户给出一个目录，要求"把这个文件夹的图都处理一遍"
- 输入图存在可见 JPEG 压缩块（8x8 块状伪影）、边缘振铃或低对比度雾感

不触发（属其他技能范围）：
- 只要放大、要求 AI 补细节 → ai-upscaler
- 改图内文字、去水印文字 → image-text-edit
- 只做格式互转、缩略图、EXIF 清理 → image-tools-suite
- 拍照纸质件自动裁边并合成 PDF → image-scanner-to-pdf

## 三、常驻规则

1. 原图零改动：所有写操作只落新文件，命名 `<原名>_enhanced.<ext>`，禁止覆盖源图；批处理前先做一次只读体检。
2. 预设优先于手调：先按用途选预设（ppt / doc / web / print / social），仅当预设质检不过才逐项调参；任何手调参数必须写进 manifest.json 以便复现。
3. 小样先跑：批量前抽 3 张代表性图（最小尺寸、最大尺寸、含文字最多各一张）试跑，人工确认后再全量执行。
4. 增强不过度：锐化后若出现白边、振铃或噪点被放大，回退一档参数重跑；JPEG 二次压缩质量不低于 92 且 subsampling=0。
5. 每张图过质检：按 references/quality-checklist.md 逐项勾选，未过项写进 failed.log 并注明原因，不得静默放过。
6. 报告随图交付：交付含增强前后对比报告一份（套 references/output-template.md），列明尺寸、体积、参数与质检结论。

## 四、标准工作流

1. **输入盘点** — 输入：图片路径或目录。动作：列目录、读扩展名与文件体积，剔除非位图文件、零字节文件与符号链接。输出：可处理清单 processed.txt ＋ 排除清单 skipped.txt（含排除原因）。
2. **图像诊断** — 输入：可处理清单内每张图。动作：跑 `python3 scripts/enhance.py --analyze <图>`，取尺寸、色彩模式、是否含透明通道、估算锐度评分与压缩块强度。输出：诊断 JSON（如 out/diag_<原名>.json），用于决定预设与参数。
3. **用途路由与预设匹配** — 输入：诊断 JSON ＋ 用户交付用途。动作：按 5.1 节预设表匹配；图文类截图走 ppt 或 doc，纯照片走 social，印刷件走 print；单边超 4096px 时先缩到 4096px 再增强。输出：每张图的最终参数集（预设名＋覆盖参数）。
4. **小样试跑** — 输入：3 张代表性图（最小、最大、含文字最多各一张）＋ 参数集。动作：逐张执行，产出增强图并跑一次尺寸与体积自检，含文字图抽跑 OCR。输出：试跑样张 ＋ 自检结果，交人工确认（确认点见第九节）。
5. **批量执行** — 输入：可处理清单 ＋ 确认后的参数集。动作：跑 `python3 scripts/batch_enhance.py`，保留相对目录结构，单图异常隔离不中断。输出：增强图目录 ＋ manifest.json ＋ failed.log。
6. **质检核验** — 输入：增强图目录 ＋ 原图目录。动作：按 references/quality-checklist.md 逐项核对；尺寸、体积、透明通道项由脚本自动核，视觉项人工放大 200% 目视。输出：质检记录（含未过项与处置）。
7. **交付与报告** — 输入：增强图 ＋ 质检记录 ＋ manifest.json。动作：按 references/output-template.md 生成增强前后对比报告，写出逐图明细与失败说明。输出：交付包（增强图目录＋报告.md＋manifest.json＋failed.log）。
8. **失败对账与重试** — 输入：failed.log。动作：逐条判定原因（损坏／格式不支持／透明通道／参数过度／体积超限），按第八节降级表处置后局部重跑。输出：重试结果与最终失败清单。

## 五、核心方法与命令

### 5.1 增强流水线与预设表（Pillow 实现）

```python
from PIL import Image, ImageEnhance, ImageFilter

PRESETS = {                       # 预设随用途固化，避免每次手调
    "ppt":    dict(scale=2.0, sharpen=1.35, denoise=0, contrast=1.06, color=1.04, fmt="PNG"),
    "doc":    dict(scale=1.5, sharpen=1.20, denoise=1, contrast=1.04, color=1.00, fmt="PNG"),
    "web":    dict(scale=1.0, sharpen=0.95, denoise=1, contrast=1.02, color=1.02, fmt="JPEG"),
    "print":  dict(scale=3.0, sharpen=1.50, denoise=1, contrast=1.08, color=1.06, fmt="PNG"),
    "social": dict(scale=1.5, sharpen=1.10, denoise=1, contrast=1.03, color=1.08, fmt="JPEG"),
}


def enhance(src, dst, preset="ppt", **overrides):
    cfg = {**PRESETS[preset], **overrides}
    im = Image.open(src)
    has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    if cfg["denoise"]:                                    # 压缩伪影与噪点清理
        im = im.filter(ImageFilter.MedianFilter(size=3))
    if cfg["scale"] != 1.0:                               # 分辨率提升（真实重采样）
        w, h = im.size
        im = im.resize((round(w * cfg["scale"]), round(h * cfg["scale"])), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(              # 锐化：半径 1.6 保文字不糊
        radius=1.6, percent=round(cfg["sharpen"] * 100), threshold=3))
    im = ImageEnhance.Contrast(im).enhance(cfg["contrast"])   # 对比度校正
    im = ImageEnhance.Color(im).enhance(cfg["color"])         # 饱和度校正
    im = ImageEnhance.Sharpness(im).enhance(cfg["sharpen"])   # 整体清晰度微调
    if cfg["fmt"] == "JPEG" and not has_alpha:            # 含透明通道一律转 PNG，防丢通道
        im.convert("RGB").save(dst, quality=95, subsampling=0, optimize=True)
    else:
        im.save(dst)
    return cfg, has_alpha
```

### 5.2 诊断片段（决定预设与参数）

```python
import json
from PIL import Image, ImageFilter, ImageStat

def analyze(path):
    im = Image.open(path)
    g = im.convert("L")
    edge = g.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edge)
    sharpness = round(stat.stddev[0], 2)          # 越大越锐；<6 判为发虚
    return {
        "file": str(path), "size": im.size, "mode": im.mode,
        "has_alpha": im.mode in ("RGBA", "LA") or "transparency" in im.info,
        "sharpness_score": sharpness,
        "verdict": "needs_enhance" if sharpness < 6 else "already_ok",
    }
```

### 5.3 可执行命令

```bash
# 1) 单图增强：PPT 预设，2x 放大，保留透明通道
python3 scripts/enhance.py raw/screen_login.png out/screen_login_enhanced.png --preset ppt --scale 2

# 2) 先体检：输出诊断 JSON，判断是否值得增强
python3 scripts/enhance.py --analyze raw/screen_login.png --json out/diag_screen_login.json

# 3) 文档扫描件：1.5x ＋ 去噪一档，清理 JPEG 压缩块
python3 scripts/enhance.py raw/scan_contract.jpg out/scan_contract_enhanced.png --preset doc --denoise 1

# 4) 整目录批量：并发 4，写 manifest 与失败清单，支持断点续跑
python3 scripts/batch_enhance.py raw/ out/ --preset ppt --jobs 4 \
  --manifest out/manifest.json --failed-log out/failed.log --resume

# 5) 质检自检：尺寸倍数、体积下限、透明通道三项
python3 -c "
from PIL import Image
s = Image.open('raw/screen_login.png'); d = Image.open('out/screen_login_enhanced.png')
assert d.size == (s.size[0]*2, s.size[1]*2), '尺寸倍数不符'
assert d.mode in ('RGB','RGBA'), '色彩模式异常'
print('OK', s.size, '->', d.size, d.mode)"
```

参数速查：`input` 与 `output` 位置参数（批量入口改为 `src_dir` 与 `out_dir`）；`--preset` 取 ppt/doc/web/print/social（默认 ppt）；`--scale` 浮点（默认取预设值）；`--sharpen` 0.8-2.0（>2.0 易出白边）；`--denoise` 0/1（默认取预设）；`--analyze` 只诊断不出图；`--json` 诊断落盘路径；`--jobs` 并发数；`--manifest` 参数与结果台账；`--failed-log` 失败清单；`--resume` 跳过 manifest 内已完成项。

### 5.4 无 Pillow 环境降级命令

```bash
# ImageMagick 兜底：LANCZOS 重采样 + unsharp 锐化 + 去噪（Pillow 不可用时）
convert raw/screen_login.png -filter Lanczos -resize 200% \
  -despeckle -unsharp 0x1.6 -quality 95 out/screen_login_enhanced.png
```

### 5.5 相关资产引用

- 质检逐项清单：references/quality-checklist.md
- 交付报告骨架：references/output-template.md
- 案例登记与来源指引：references/case-library.md
- 单图与批量入口：scripts/enhance.py、scripts/batch_enhance.py

## 六、输出规范

- 文件命名：`<原名>_enhanced.<ext>`；批量输出保留相对目录结构，如 `raw/2026/screen_a.png` → `out/2026/screen_a_enhanced.png`
- 格式选择：含文字或透明通道一律 PNG；纯照片可用 JPEG（quality 95、subsampling=0）；印刷件用 PNG 并注明 3x
- 逐图台账：manifest.json 记录 `file / preset / params / in_size / out_size / in_bytes / out_bytes / status`
- 失败清单：failed.log 每行 `file | reason | action`，reason 取自第八节失败模式表
- 交付报告：Markdown 一份，套 references/output-template.md，含逐图明细表与质检结论
- 回报格式：`增强完成 N 张 / 失败 M 张 | 输出目录 | 预设 | 质检通过率 | 体积变化率`

## 七、边界与反模式

不在范围（转其他技能）：
- 纯放大且要求 AI 补细节、老人像修复 → ai-upscaler
- 图内文字替换、去水印文字 → image-text-edit
- 批量加水印、拼图、骑缝章 → batch-watermark
- 拍照件透视矫正、自动裁边、合成 PDF → image-scanner-to-pdf
- 只做格式互转、白底化、EXIF 清理 → image-tools-suite

禁止行为：
- 禁止覆盖、移动或删除源图；一切写操作只落新文件
- 禁止未做小样确认就直跑全量批量
- 禁止在锐化已出现白边、振铃、噪点放大时仍交付
- 禁止把增强图当原始证据图归档；法律与审计场景以原图为准，增强图仅作展示件

反模式（黑名单）：
- 反模式一：一步拉满参数（锐化 3.0 ＋ 放大 4x），文字笔画粘连，OCR 反而不通过
- 反模式二：对 PNG 界面截图先转 JPEG 再去噪，二次有损压缩引入新伪影
- 反模式三：只报尺寸不看内容，未做文字可读性抽检即交付
- 反模式四：批量无断点续跑设计，任务中断后从头重来并覆盖已处理文件
- 反模式五：把去噪拉到最强档，文字边缘被抹平，扫描件反而更糊

## 八、失败模式与降级

| 失败模式 | 触发条件 | 动作与降级路径 |
|---|---|---|
| 图片损坏或零字节 | `Image.open` 抛异常或文件 0 字节 | 捕获异常，记入 failed.log，跳过继续下一张，不中断批量 |
| 格式不支持 | 扩展名不可解码（含 heic/psd/未知扩展） | 报错并转报 image-tools-suite 或 anydoc 转换，记 `unsupported` |
| 透明通道丢失 | 源图含 alpha 但目标格式为 JPEG | 强制改存 PNG，manifest 标 `alpha_preserved`，禁止静默丢通道 |
| 增强过度产生伪影 | 锐化后白边、振铃、噪点被放大 | 锐化回退一档重试，最多 2 次；仍不过则回退预设原值并标注 |
| 批量任务中断 | 进程被杀、磁盘写满、超时 | 读 manifest.json 断点续跑，跳过 status=done 项，仅重跑失败与未完成项 |
| 内存不足 | 单边超大图（> 4096px）或并发过高 | 先缩到 4096px 再增强，`--jobs` 降到 1 重试一次 |
| 输出目录不可写 | 无权限或路径不存在 | 退出码非零并回报明确路径，不静默失败 |
| 源图已达标 | 锐度评分 ≥ 6 且无压缩块 | 标注 `already_ok`，不强行增强，避免无意义处理 |

降级顺序：脚本原流程 → 降并发／降倍数 → ImageMagick 兜底 → 仅做 LANCZOS 重采样 → 回报无法增强并给出原图。

## 九、关键检查点

🔴 检查点 1（源图体检后）：诊断 JSON 的尺寸与色彩模式可读、锐度评分已出，人工确认哪些图确实需要增强。
🔴 检查点 2（小样试跑后）：3 张试跑样张人工放大 200% 目视确认，文字无粘连、无白边，确认后才进全量。
🔴 检查点 3（批量前）：确认输出目录为空或已备份，源图目录只读挂载，STOP 待确认，未确认不得启动批量。
🔴 检查点 4（质检核验）：对照 references/quality-checklist.md 逐项核对，任一项未过即 STOP，不得进入交付。
🔴 检查点 5（交付前）：增强图、报告、manifest.json、failed.log 四件齐备，失败项已逐条说明原因与处置。
🔴 检查点 6（归档场景）：涉及法律、审计、结算用途时，须人工确认增强图不替代原图归档，并保留原图路径记录。

## 十、实战范例

**范例 1：PPT 里糊掉的系统截图**
```
输入：raw/screen_plant_scada.png（分辨率【待填：实际尺寸】，界面文字发虚）
命令：python3 scripts/enhance.py raw/screen_plant_scada.png out/screen_plant_scada_enhanced.png --preset ppt --scale 2
预期输出：
  尺寸 原尺寸 x2；格式 PNG；透明通道保留
  manifest：{"preset":"ppt","scale":2.0,"sharpen":1.35,"contrast":1.06,"status":"done"}
  质检：OCR 抽检前 5 行文字可读；无白边振铃
回报：screen_plant_scada_enhanced.png | 原尺寸→2x | 预设 ppt | 质检通过
```

**范例 2：合同扫描件清晰度不足**
```
输入：raw/scan_contract_page.jpg（含 JPEG 压缩块）
命令：python3 scripts/enhance.py raw/scan_contract_page.jpg out/scan_contract_page_enhanced.png --preset doc --denoise 1
预期输出：
  先去噪清理压缩块，再 1.5x 重采样，末段 UnsharpMask 锐化
  failed.log 为空；体积变化率【待填：实测值】
  质检：印章边缘完整、骑缝线不断、正文可读
回报：scan_contract_page_enhanced.png | 1.5x | 预设 doc | 质检通过
```

**范例 3：整目录截图批量入档**
```
输入：raw/ 目录（【待填：文件数】张界面截图）
命令：python3 scripts/batch_enhance.py raw/ out/ --preset ppt --jobs 4 \
  --manifest out/manifest.json --failed-log out/failed.log --resume
预期输出：
  out/ 下按相对路径生成 *_enhanced.png
  manifest.json 含逐图参数与体积对比；failed.log 列明失败图与原因
  中断后重跑同命令，已完成项被跳过（断点续跑生效）
回报：批量完成 N 张 / 失败 M 张 | 输出目录 out/ | 预设 ppt | 质检通过率 X%
```

## 十一、依赖说明与降级

- 必装依赖：Pillow ≥ 9.0。自检命令 `python3 -c "import PIL; print(PIL.__version__)"`
- 可选依赖：pytesseract ＋ tesseract-ocr-chi-sim（文字截图 OCR 抽检）；numpy（锐度评分加速）
- Pillow 不可用时：改用 ImageMagick 兜底命令（见 5.4 节），功能对等但参数需手工换算
- OCR 不可用时：改为人工放大 200% 目视核对文字可读性，并在报告中注明抽检方式
- 资源上限：单边 4096px、单批 200 张、并发 4；超限时先降规格再处理，不得静默截断
- 与其他技能的衔接：需 AI 放大 → ai-upscaler；需扫描成 PDF → image-scanner-to-pdf；需格式互转 → image-tools-suite；需改字 → image-text-edit

## 十二、版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0.0 | 2026-09-17 | 由英文单文件技能改造为 ima 专家级中文技能：补齐专家级路由与四级响应、8 步标准工作流、失败模式与降级表、6 个检查点、5 个反模式黑名单；新增 references 三件（case-library.md、quality-checklist.md、output-template.md）与 scripts 两件（enhance.py、batch_enhance.py）；明确与 ai-upscaler 纯放大路线的能力边界 |

## 依赖安装

本技能脚本依赖第三方库，首次使用（或沙箱/换机重置）后请先安装：

```bash
python3 -m pip install -r requirements.txt
```
