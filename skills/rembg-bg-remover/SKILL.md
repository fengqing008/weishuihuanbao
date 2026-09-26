---
name: rembg-bg-remover
display_name: 图片去背景
version: 2.0.1
description: 基于 rembg 的本地图片去背景/抠图技能（CPU推理，无需GPU）。支持 u2netp/u2net/isnet-general-use 等多种模型，输出带透明通道的 PNG。当用户需要去除图片背景、抠图、提取前景、做公章抠图、透明背景、做商品图、人物抠图、或替换阿里百炼 image-text-edit 中的去背景环节时，触发此技能。触发词：去背景/抠图/抠公章/透明背景/提取前景/人物抠图/商品图/remove background/background removal/cutout/transparent PNG/matting。
author: 清风明月
slug: qf-rembg-bg-remover
category: 科技
tags:
- 去背景
- 抠图
- 透明背景
- 提取前景
- 商品图
---

## 〇、专家级路由（v2.0.0）

**专家定位**：本地CPU抠图执行器；输出透明PNG；给商品图、人像、章粗提用；图片不出本机。
**五维评估**：
- 适用场景：①商品图转透明底 ②人像抠图（发丝场景） ③公章粗提底稿 ④目录批量抠图 ⑤动漫图抠图
- 能力边界：不做红色章精细提取（走 seal-extractor）；不补缺损内容；半透明物体抠不净
- 依赖资产：scripts/rembg_remove.py（single/batch/models）；rembg+onnxruntime；模型首次自动下载
- 交付质量：深/浅双色底核验主体完整、边缘无残留；批量数量对账+每5张抽1
- 性能表现：u2netp单图1-2秒；isnet 4-8秒；CPU 3核/4GB基线

**四级响应（L1-L4）**：
- L1 轻量问答（模型怎么选）→ 给模型路由表直接回答
- L2 标准任务（单图抠图）→ 识图选型→执行→双色底核验
- L3 复杂任务（目录批量）→ batch+数量对账+抽验+已处理清单续跑
- L4 专家任务（素材交付）→ 全流程+双范例复用（章粗提/人像批量）

**黄金窗口**：单批≤100张；首跑预留模型下载时间与磁盘
**专家件索引**：scripts/rembg_remove.py（唯一入口）；暂无references目录

> v2.0.0 专家级（2026-09-07）：补齐九要素——定位/触发/工作流/输出规范/反模式/实战范例；模型路由、命令、性能与依赖版本逐字保留，重复的依赖章节合并。

# RemBG BG Remover - 本地图片去背景/抠图

## 定位声明
本技能用 rembg 在本地（CPU 推理、无需 GPU、图片不出本机）把任意图片的背景去掉，输出带透明通道的 PNG，供需要抠图素材的用户使用。解决"云端抠图要付费+传隐私图"的问题。依赖 Python 包 rembg+onnxruntime 与首次运行自动下载的模型。

## 触发条件
- 用户要去背景/抠图/提取前景/透明背景，未指定必须在线工具
- 明确场景：商品图、人物抠图、公章抠图（粗提）、文档扫描件透明化
- 英文触发：remove background, background removal, cutout, transparent PNG, matting
- 不触发：红色公章精细提取（→ seal-extractor，本技能仅做粗提底稿）、AI 改图内容（→ image-text-edit）、尺寸/格式批处理（→ image-tools-suite）

## 能力
- **图片去背景**：输入任意图片 → 输出带透明通道的 PNG
- **批量去背景**：一次处理多张图片
- **模型选择**：u2netp（轻量4.7MB）/ u2net（标准176MB）/ isnet-general-use（精细168MB）
- **应用场景**：商品图抠图、公章抠图、人物抠图、文档扫描件透明化

## 模型路由
- 默认 `u2netp`：体积小（4.7MB）、速度快、精度够用
- 复杂场景 → `isnet-general-use`：精度最高，体积168MB
- 人物发丝细节 → `u2net_human_seg`：176MB
- 动漫图 → `isnet-anime`：168MB

## 分步工作流
1. **输入**：确认图片路径与数量；看一眼图（识图）判断主体类型，按模型路由选模型。
2. **执行**：单图 `single`，目录批量 `batch`；发丝/边缘苛刻场景加 `--alpha-matting`。
3. **检查点（🔴 交付前）**：把输出 PNG 放到深色/浅色两种底上各看一次——主体完整、边缘无残留背景、无镂空破洞才算过；不过则换模型重跑（u2netp→isnet-general-use）。
4. **输出**：透明 PNG 交用户；需要白底/纯色底的再合成，不默认替用户填底色。
5. **批量对账**：batch 后核对输出文件数=输入文件数，逐张抽验（每 5 张至少看 1 张）。

## 用法
```bash
# 单图去背景
python3 scripts/rembg_remove.py single photo.jpg photo_nobg.png

# 指定模型
python3 scripts/rembg_remove.py single photo.jpg out.png --model u2netp

# 批量去背景
python3 scripts/rembg_remove.py batch ./photos/ ./nobg/ --ext jpg,png

# 查看可用模型
python3 scripts/rembg_remove.py models
```

## 输出规范
- 输出一律 PNG + alpha 通道，文件名默认 `<原名>_nobg.png`（由调用方传输出路径）。
- 批量输出目录结构镜像输入目录，文件名不变、仅换扩展名为 png。
- 交付说明需含：所用模型、是否开 alpha-matting、抽验结果；不满意处明确告知（如"发丝边缘建议换 u2net_human_seg"）。

## 边界与反模式
- **不修内容**：只抠不补——主体缺损就换模型/换图，不用 AI 臆造补全。
- **公章场景不首选本技能**：印章要保原始红色像素、去黑线，用 seal-extractor；本技能仅适合"完全无干扰的纯章图"粗提。
- **不做半透明物体**：玻璃/烟雾/水面倒影抠不干净，提前告知用户预期。
- **不超大批量不确认**：>100 张先报数量确认；批量失败不停在半程——记录已处理清单便于续跑。
- **常见错误**：忘了首次运行会下载模型（需网络+磁盘）；输出成 jpg 丢 alpha 通道。

## 依赖
- Python包：rembg（含onnxruntime、pymatting等）
- 模型：首次运行自动下载到 ~/.rembg/models/
- 版本清单：
```
rembg==2.0.81
onnxruntime==1.29.0
pillow>=11.0
numpy>=2.0
scipy>=1.18
```

## 安装说明
沙箱已装：
- `pip install rembg onnxruntime`（约500MB，含依赖）
- 模型需从 GitHub 下载（沙箱用 gh-proxy.com 代理）

如未安装：`pip install rembg onnxruntime` 后重试；仍失败则降级告知用户"本环境无抠图能力，建议改用在线工具或提供已抠图素材"。

## 性能（CPU 3核/4GB内存）
- u2netp: 单图1-2秒（512x512）
- u2net: 单图3-5秒
- isnet-general-use: 单图4-8秒

## 局限
- CPU推理较慢（GPU加速需 `pip install rembg[gpu]`+ CUDA环境）
- 边缘细节（如发丝）通用模型精度一般，建议用 u2net_human_seg
- 半透明物体（如玻璃、烟雾）效果较差

## vs 付费方案
| 维度 | 阿里百炼 image-text-edit | IMA Studio 抠图 | **rembg本地** |
|---|---|---|---|
| 费用 | 按图付费 | 按pts扣 | **完全免费** |
| API Key | 需要 | 需要 | **无需** |
| 数据隐私 | 上传云端 | 上传云端 | **本地处理** |
| 批量能力 | 单图 | 单图 | **批量** |
| 模型选择 | 1款 | 1款 | **5+款** |

## 实战范例
**范例A：公章抠图透明背景（环保水务——验收资料用章，配合 seal-extractor）**
1. 输入：施工合同扫描页局部截图，红章清晰、无表格线穿过（【待核：若章上有黑线/手写字，应直接走 seal-extractor】）。
2. 处理：
```bash
python3 scripts/rembg_remove.py single 合同页.png 章_粗提.png --model isnet-general-use
```
3. 检查点：红色印章主体完整、白纸背景全透明；边缘发虚则改用 seal-extractor 的 OpenCV 红色像素管线重做。
4. 输出：`章_粗提.png`（透明背景），供插入验收报告封面/落款处。
**范例B：污水厂开放日纪念品——员工人像抠图**
1. 输入：20 张员工工作照（【待核：实际张数】），背景为厂区车间。
2. 处理：`batch` + `u2net_human_seg`（发丝优先）。
3. 输出：20 张透明 PNG，合成到统一文化衫海报模板上；抽验每 5 张看 1 张，重点查安全帽边缘。

## 版本与变更记录
| 版本 | 变化 |
|---|---|
| 1.0 | 初版：single/batch/models 三命令 |
| 1.1 | 补模型路由、性能、付费方案对比 |
| **2.0.0（2026-09-07）** | 九要素结构化：定位/触发/工作流/输出规范/反模式/双范例（公章粗提+人像批量）；合并重复依赖章节，命令与版本清单未动 |

## 依赖与失败模式

- 关键依赖：rembg、onnxruntime
- 失败模式与防护：启动即预检 rembg，缺失则提示 `pip install rembg onnxruntime` 并退出码 2。
- 原则：依赖缺失或输入非法时**显式报错并非零退出**，绝不静默降级，也绝不输出空结果或假结论。
