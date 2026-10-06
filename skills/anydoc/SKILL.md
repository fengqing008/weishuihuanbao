---
name: anydoc
display_name: 文档转Markdown
version: 2.1.0
description: '任意文档秒转 Markdown 的本地转换技能（Firecrawl 开源，Rust 实现，毫秒级）。支持 Word（.doc/.docx/.docm）、PowerPoint（.ppt/.pptx/.pptm
  等）、Excel（.xls/.xlsx/.xlsm/.xlsb/.csv）、OpenDocument（.odt/.ods/.odp）、RTF、EPUB、PDF
  共 20 种格式，按文件内容自动识别格式，无需安装（npx 一键调用，Node 20+）。当用户需要读取/解析/转换 docx、pptx、xlsx、pdf 等办公文档内容为
  Markdown、提取文档全文、文档内容分析、把本地文件转成可读文本、文档入库前格式统一时使用。中文触发词："转成Markdown"、"文档转换"、"提取文档内容"、"读取Word/PDF内容"、"文档解析"。English
  triggers: convert to markdown, document conversion, extract docx/pdf content。适用于有文字层的文档（扫描件/纯图片
  PDF 不支持 OCR，需用 textin-xparse 技能）。不适用于：扫描件/图片 OCR 识别（用 textin-xparse）、PDF 创建编辑（用
  ima-pdf）、Word 创建编辑（用 ima-doc）。'
author: 清风明月
slug: anydoc
category: 科技
tags:
- 读取
- 解析
- 转换
- 等办公文档内容为
- 提取文档全文
- 文档内容分析
license: MIT
metadata:
  author: firecrawl
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

> 更多用法与示例见 `references/usage-and-examples.md`；案例库见 `references/case-library.md`。

## 能力边界（不适用范围与场景路由）

**能力边界**：本技能只做一件事——把**有文字层**的办公文档/PDF 转成 Markdown 文本。除此之外均不在范围内。

**不适用范围 / 不在范围**：

- 扫描件、纯图片 PDF、拍照截图 → 转 textin-xparse（OCR）
- PDF 创建、合并、拆分、加密、表单填写 → 转 ima-pdf
- Word 创建、编辑、套模板排版 → 转 ima-doc
- 网页抓取与正文提取 → 转 web-scraper
- 图片美化、批量缩放与格式转换 → 转 image-tools-suite
- 文档内容的事实改写、翻译、摘要生成 → 属写作类任务，不属转换范围

**场景路由表**：

| 用户场景 | 判据 | 走向 |
|---|---|---|
| docx/pptx/xlsx 读内容 | 扩展名在支持清单且未加密 | 本技能 npx 转换 |
| 有文字层 PDF | 首页文字可选中 | 本技能 npx 转换 |
| 无文字层 PDF / 图片 / 截图 | 首页不可选中文字 | textin-xparse OCR |
| 一批 Office 文件入库前格式统一 | ≥3 份同类文件 | 本技能 + `scripts/anydoc_check.py` 质检 |
| CSV 无扩展名 / stdin 输入 | 无扩展名 | 本技能 `--format` 显式指定 |
| 加密或损坏文档 | 打开即报错 | 让用户另存可读副本后再转 |

**English triggers**: convert to markdown, document conversion, extract docx/pdf content, parse document, office to markdown.

## 降级路径与失败模式（异常处理预案）

文档转换的**失败模式**，多数不是"命令打错"，而是"输入不具备可转换条件"。下表覆盖六类失败分支与**降级处置**，触发即按其执行，不得绕道臆断。

| 序号 | 场景 | 触发条件 | 降级处置（含兜底方案） |
|---|---|---|---|
| F1 | 无文字层 | PDF/图片为扫描件，首页文字不可选中；退出码 1 | **不重试**同一命令；降级为 OCR 通道（textin-xparse）取文字层后再回归 |
| F2 | 加密/损坏文档 | 打开即报错或退出码 1 | 终止该项，请用户另存为可读副本；不尝试解密；记录"待人工授权" |
| F3 | 依赖不可用 | 无 Node 20+ 或 npm 源不可达，`npx` 失败 | **回退（fallback）到备用解析路径**：有文字层 PDF 走 `pdftotext` 或平台自带解析；Office 走 textin-xparse / ima-doc |
| F4 | 产物不合格 | 表格错列、乱码、空产物 | 编码类 **回退** text-io 的 `convert` 先修源文件；结构类人工核对重建；复跑 `anydoc_check.py` 确认 |
| F5 | 大文档超窗口 | 单文件 >50 页或 >10MB | 降级为 `-o` 落盘 + 分片读取；必要时按目录切片，逐段处理，避免一次性载入 |
| F6 | 批量部分失败 | 目录内个别件转换失败 | **断点续跑**：只重跑失败件，已合格件不重跑；失败件单列原因并给替代通道 |

**容错与补救原则**：①任一结论须可复算可回溯，产物与源文件一一对应；②退出码先判（0 成功 / 1 无法转换 / 2 用法错误），按码处置，不盲目重试；③**边界条件**——空产物、纯元数据产物一律视为失败交付；④已交付材料口径有误的，出具更正说明并留痕；⑤对不可转换输入采用**防御**姿态（先判定再动手），不做无效尝试。

**兜底通道标注**：走兜底或降级通道产出的文本，须在交付说明中如实标注所用通道与精度差异，不隐去降级事实。

**错误处理速查**：退出码 2 → 检查路径与 `--format` 写法；退出码 1 → 判定加密/损坏/无文字层，换通道；stderr 单行 `anydoc: <message>`，无多余提示。

## 引用依据与溯源

本节固定引用口径：涉及格式规范、编码与字符集的技术结论，一律落到"标准全称＋编号＋来源"，不以俗称代替。

| 层级 | 标准/文件全称 | 编号 | 来源与核验入口 |
|---|---|---|---|
| 文件格式（Office） | 《信息技术 办公软件文档格式规范》 | GB/T 20916-2007 | 国家标准全文公开系统 |
| 文件格式（OOXML） | ISO/IEC 29500-1:2016 Office Open XML | ISO/IEC 29500 | ISO 官网 / ECMA-376 |
| 版式文档 | 《电子文件存储与交换格式 版式文档》 | GB/T 33190-2016 | 国家标准全文公开系统 |
| 字符集 | RFC 3629 UTF-8, a transformation format of ISO 10646 | IETF RFC 3629 | IETF Datatracker |
| 表格数据 | RFC 4180 Common Format and MIME Type for CSV Files | IETF RFC 4180 | IETF Datatracker |
| 标记语言 | CommonMark Spec（GitHub Flavored Markdown 为其扩展） | CommonMark 0.31.2 / GFM Spec | commonmark.org / GitHub Docs |
| 数据安全 | 《中华人民共和国网络安全法》 | 主席令第五十三号（2017-06-01 施行） | 中国政府网 |

**溯源纪律**：①格式支持范围与退出码语义以本技能 `scripts/anydoc_check.py` 与官方 CLI 行为为准；②技术标准以现行有效版本为准，效力存疑时标注并提示用户核对；③本技能全部规则为条文与官方文档转述，**不编造、不杜撰**未见于公开资料的行为描述；④用户文档仅用于本任务，不外发、不转送，处理全程在本地完成。

## 合规红线（固定拒绝口径）

1. **不得**对扫描件/纯图片 PDF 反复重试转换——无文字层必然失败，应分流 OCR；`不适用` 即拒，不做无效尝试。
2. **不得**用本技能创建、编辑、美化任何文档（PDF/Word/PPT/Excel 的生成与修改均不在范围）。
3. **不得**编造或改写原文内容——转换只做结构搬运，原文没有的文字一个字不加。
4. **不得**把大文档全文灌入上下文——一律先 `-o` 落盘再按需分片读取。
5. **不得**将用户文档向外部传输或送交第三方——本地运行，文件不出本机；涉及敏感内容的，遵守脱敏与隐私要求。
6. **不得**把未经 `anydoc_check.py` 质检的产物当最终交付物——空产物、纯元数据产物一律视为失败交付。

## 可交付物与输出规范

| 产出 | 格式 | 说明 |
|---|---|---|
| 单份/批量 Markdown | `.md`（UTF-8 无 BOM） | `npx @firecrawl/anydoc <file> -o <stem>.md`，命名沿用源文件名干 |
| 转换质检报告 | 文本 / JSON | `python3 scripts/anydoc_check.py --source <dir> --md-dir <dir> [--json]` |
| 缺件与失败清单 | 文本 | 质检输出的缺件、空件、结构异常逐项列出并给替代通道 |
| 交付说明 | Markdown | 列明通道（主用/兜底）、成功与失败件数、需人工核对项 |

**输出纪律**：①stdout 模式给 GitHub 风格 Markdown；②文件模式 UTF-8 无 BOM，多文档保持一一对应；③保留原文结构与数据，不做增删改写；④凡走降级/兜底通道的，在交付说明中标注。

## 版本沿革（CHANGELOG）

| 版本 | 日期 | 变更 |
|---|---|---|
| 2.1.0 | 2026-10 | 新增「降级路径与失败模式」表（F1–F6）与容错补救原则；新增「引用依据与溯源」小节（七条标准依据）；新增「合规红线」六条固定拒绝口径、「能力边界与场景路由」表与「可交付物与输出规范」表；新增 `scripts/anydoc_check.py` 转换质检脚本（退出码 0/1/2）与 `references/case-library.md` 案例库；补英文触发词 |
| 2.0.0 | 2026-09-07 | 补齐九要素（定位/触发/工作流/输出规范/边界/依赖/范例）；原 CLI 命令、格式清单、使用规则与 ima 平台调用规则原文保留 |
| 1.1.0 | — | 格式清单与退出码语义固化 |
| 1.0.0 | — | 首版 |

**版本维护约定**：CLI 退出码语义、支持格式清单、质检脚本行为变更时升次版本号；新增脚本与案例库不改变既有触发语义。

## 脚本调用速查

```bash
# 单份产物抽查
python3 scripts/anydoc_check.py --sample out.md --json

# 批量对账（源目录 vs 产物目录）
python3 scripts/anydoc_check.py --source ./合同 --md-dir ./合同_md --min-bytes 32
```

退出码：0 = 全部通过；1 = 存在不合格项，按降级路径处置；2 = 输入不足或路径不可用。
