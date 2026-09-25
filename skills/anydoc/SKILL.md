---
name: anydoc
description: "任意文档秒转 Markdown 的本地转换技能（Firecrawl 开源，Rust 实现，毫秒级）。支持 Word（.doc/.docx/.docm）、PowerPoint（.ppt/.pptx/.pptm 等）、Excel（.xls/.xlsx/.xlsm/.xlsb/.csv）、OpenDocument（.odt/.ods/.odp）、RTF、EPUB、PDF 共 20 种格式，按文件内容自动识别格式，无需安装（npx 一键调用，Node 20+）。当用户需要读取/解析/转换 docx、pptx、xlsx、pdf 等办公文档内容为 Markdown、提取文档全文、文档内容分析、把本地文件转成可读文本、文档入库前格式统一时使用。中文触发词：\"转成Markdown\"、\"文档转换\"、\"提取文档内容\"、\"读取Word/PDF内容\"、\"文档解析\"。English triggers: convert to markdown, document conversion, extract docx/pdf content。适用于有文字层的文档（扫描件/纯图片 PDF 不支持 OCR，需用 textin-xparse 技能）。不适用于：扫描件/图片 OCR 识别（用 textin-xparse）、PDF 创建编辑（用 ima-pdf）、Word 创建编辑（用 ima-doc）。"
license: MIT
metadata:
  author: firecrawl
version: 2.0.0
author: 清风明月
display_name: 文档转Markdown
slug: anydoc
category: 科技
tags: ["读取", "解析", "转换", "等办公文档内容为", "提取文档全文", "文档内容分析"]
---

# 任意文档转 Markdown（anydoc）

## 使用说明

1. **用途**：任意文档秒转 Markdown 的本地转换技能（Firecrawl 开源，Rust 实现，毫秒级）。
2. **典型问法**：“读取”、“解析”、“转换”、“等办公文档内容为”。
3. **调用方式**：在 ima 对话中直接描述需求或上传相关文件，本技能按触发词自动匹配调用。
4. **注意事项**：扫描件/图片 OCR 识别（用 textin-xparse）、PDF 创建编辑（用 ima-pdf）、Word 创建编辑（用 ima-doc）。

> v2.0.0 专家级（2026-09-07）：补齐九要素结构——定位声明、触发条件、分步工作流、输出规范、边界与反模式、依赖降级、实战范例；原 CLI 命令、格式清单与调用规则全部保留。

## 〇、专家级路由（v2.0.0）

**专家定位**：20 种办公文档毫秒级转 Markdown 的本地转换专家。文件不出本机。给文档问答、入库、格式统一任务打前站。

**五维评估**：
- 适用场景：读 docx/pptx/xlsx/pdf 内容；入库前统一转 md；批量提全文；抽表格章节
- 能力边界：不做扫描件 OCR、PDF 编辑、Word 编辑；无文字层必失败
- 依赖资产：npx + npm 包 @firecrawl/anydoc（Node 20+）；无本地脚本
- 交付质量：退出码 0、标题表格保留、UTF-8 无乱码、与源文件一一对应
- 性能表现：毫秒级/份；大文件一律 -o 落盘后分片读

**四级响应（L1-L4）**：
- L1 单文件快转/格式咨询 → 直接给命令与结果
- L2 单文档转换 → npx 转换 + 退出码与内容抽查
- L3 批量转换（≥3 份）→ 逐份转换 + 清单核对 + 失败单列
- L4 入库前格式统一工程 → 转换 + 质检 + 命名对齐 + 归档交付

**黄金窗口**：单文件 ≤50 页/≤10MB 直转；超限先落盘再分片读
**专家件索引**：无本地 references/；核心资产为 npm 包 @firecrawl/anydoc 与正文"支持格式/使用规则"两节

## 定位声明

本技能是一个本地文档格式转换器：把 20 种办公文档毫秒级转换为 GitHub 风格 Markdown，供后续阅读、分析、知识入库使用。给需要"先把文档变成可处理文本"的任何任务用——文档问答、内容抽取、批量入库、格式统一。基于 Firecrawl 开源的 Rust 实现，本地运行、文件不出本机，通过 `npx` 一键调用（Node 20+），无需安装。

## 触发条件

**场景清单**（与 description 呼应）：

- 用户提供 docx/pptx/xlsx/pdf 等本地文档，要求读取、解析、总结或分析内容
- 文档入库/建知识库前，需要把 Office 格式统一转成 Markdown
- 批量文档需要提取全文文本
- 从 Word/Excel/PPT 里抽表格、抽章节

**中文触发词**：转成Markdown、文档转换、提取文档内容、读取Word内容、读取PDF内容、文档解析、文档全文提取。
**English triggers**: convert to markdown、document conversion、extract docx/pdf content、parse document。

**不适用**：扫描件/纯图片 PDF（无文字层，OCR 用 textin-xparse）；PDF 创建/编辑（用 ima-pdf）；Word 创建/编辑（用 ima-doc）。

## 分步工作流

**输入**：1 个或多个有文字层的本地文档 → **处理**：格式自动识别 + 转 Markdown → **输出**：stdout 文本或 .md 文件 → **检查点**：退出码与内容抽查。

1. **确认输入可用**：文件存在且非扫描件。首页无文字的 PDF 先走 textin-xparse OCR，不要硬转。
2. **小文件直接转**：
   ```bash
   npx -y @firecrawl/anydoc <file>              # Markdown 输出到 stdout
   ```
3. **大文件落盘再读片段**：
   ```bash
   npx -y @firecrawl/anydoc <file> -o out.md    # 写入文件
   ```
   之后按需读取 out.md 的指定片段，避免全文灌入上下文。
4. **stdin 流式输入**（CSV 等无扩展名场景需 `--format` 显式指定）：
   ```bash
   npx -y @firecrawl/anydoc - --format csv < f
   ```
5. **检查点**：退出码 0 且首行非空即成功；再抽查标题/表格是否保留，异常时转 textin-xparse。

首次调用会下载 npm 包（约需几秒），之后走 npx 缓存。

## 支持格式

`.doc` `.docx` `.docm` `.odt` `.rtf` `.epub` `.pdf` `.ppt` `.pps` `.pot` `.pptx` `.pptm` `.ppsx` `.ppsm` `.odp` `.xls` `.xlsx` `.xlsm` `.xlsb` `.ods` `.csv`

## 使用规则

1. 格式按文件内容自动识别，无需指定。仅当 stdin 传 CSV 或扩展名缺失/错误时，才用 `--format <name>` 显式指定。
2. 退出码：0=成功；1=文档无法转换；2=用法错误。失败时 stderr 输出一行 `anydoc: <message>`，CLI 从不交互提示。
3. 大文档用 `-o out.md` 写入文件，再按需读取片段，避免全文灌入上下文。
4. 扫描件/纯图片 PDF 无法转换（无 OCR），此类文件改用 textin-xparse 技能处理。
5. 在 Node/Python/Rust 代码中优先用库：npm `@firecrawl/anydoc`、PyPI `firecrawl-anydoc`、crates.io `anydoc`，均暴露同一 `to_markdown` / `toMarkdown` API。

## 输出规范

- **stdout 模式**：GitHub 风格 Markdown 文本，标题用 `#`、表格用管道表、列表用 `-`。
- **文件模式**：`-o out.md` 输出 UTF-8 文件；命名沿用源文件名（扩展名替换为 .md），多文档批量时保持一一对应。
- **错误**：stderr 单行 `anydoc: <message>`，无多余提示。
- 交付用户时保留原文结构与数据，不做增删改写。

## 边界与反模式

**不适用场景**：扫描件 OCR、PDF 编辑、Word 编辑（见上文分工）。

**禁止行为**：

- 禁止对扫描件 PDF 反复重试转换——无文字层必然失败（退出码 1），应转 OCR 流程。
- 禁止把大文件全文直接读进对话上下文——用 `-o` 落盘后按片段读取。
- 禁止把转换结果当"最终交付物"直接回复而不检查——表格类内容需抽查列对齐。

**常见错误**：

- `退出码 2`：参数/用法错误，检查文件路径与 `--format` 写法。
- `退出码 1`：文档加密、损坏或无文字层，换 textin-xparse 或让用户换文件。
- 转换结果表格错位：源文件用了复杂合并单元格，人工核对或换库调用。

## 依赖说明

| 依赖 | 说明 | 降级方案 |
|------|------|---------|
| Node.js 20+ | `npx` 运行环境 | 无 Node 时用 textin-xparse 或平台自带文档解析 |
| npm 包 `@firecrawl/anydoc` | 首次调用自动下载 | 沙箱重置后无需重装，npx 自动拉取 |
| 网络（仅首次） | 下载 npm 包 | 网络不可用时降级用 textin-xparse 或平台自带解析；已有 npx 缓存则离线可用 |

## 调用规则（ima 平台生效）

- **适用场景**：需要读取本地办公文档/PDF（有文字层）内容转 Markdown 时优先调用本技能，毫秒级、离线、免费。
- **与其他技能的优先级**：本地 Office 文档（docx/pptx/xlsx 等）及有文字层的 PDF → 先用 anydoc 转换；扫描件、纯图片 PDF、截图照片 → 用 textin-xparse（OCR）；PDF 创建/编辑 → ima-pdf；Word 创建/编辑 → ima-doc。
- **沙箱重置后**：无需重装，npx 自动拉取；网络不可用时降级用 textin-xparse 或平台自带解析。

## 实战范例

### 范例：合同文档入库前统一转 Markdown

用户：「这批 Word 版合同要放进知识库，帮我转成 Markdown。」

1. **输入**：`./合同/` 下 N 份 .docx（【待核：实际份数与文件名】）。
2. **处理**：逐份执行 `npx -y @firecrawl/anydoc "./合同/某某施工合同.docx" -o "./合同_md/某某施工合同.md"`。
3. **检查点**：每份退出码为 0；抽查第一份的标题行与金额表格是否保留。
4. **输出**：同名 .md 文件一一对应；向用户汇报成功 N 份、失败 0 份（失败单列原因）。

### 范例 2：读取 PDF 报告做摘要

用户：「读一下这份行业报告 PDF，给我要点。」

1. `npx -y @firecrawl/anydoc 行业报告.pdf -o /tmp/行业报告.md`。
2. 检查退出码 0；按章节读 /tmp/行业报告.md 片段。
3. 基于原文提炼要点，关键结论标注来源章节。

## 版本与变更记录

- **v2.0.0（2026-09-07）**：补齐九要素（定位/触发/工作流/输出规范/边界/依赖/范例）；原 CLI 命令、格式清单、使用规则与 ima 平台调用规则原文保留。
- **v1.1.0**：格式清单与退出码语义固化。
- **v1.0.0**：首版。

> 更多用法与示例见 `references/usage-and-examples.md`。
