---
name: markitdown-skill
version: "0.3.0"
author: 清风明月
display_name: 文档转Markdown官
slug: qf-markitdown-skill
category: 科技
tags: [文档转换, Markdown, PDF转Markdown, Word转Markdown, OCR, 批量转换, 文本抽取]
license: "MIT"
description: 把 PDF、Word（DOCX）、PowerPoint（PPTX）、Excel（XLSX/XLS）、图片（OCR）、音频（转写）、HTML、CSV、JSON、XML、ZIP、YouTube 链接、EPUB 等 15 种以上文件格式批量转成结构化 Markdown，保留标题层级、表格、列表与超链接，输出天然适配大模型文本分析管道。提供 markitdown 命令行、Python API 与本技能附带的零依赖调度脚本三种调用方式，支持插件扩展与 OCR、语音转写集成。当用户需要转成 Markdown、文档转换、Word 转 Markdown、PDF 转 Markdown、提取文档内容、读取 Word/PDF 内容、文档解析、批量转换、文件转文本、OCR 提取、音频转文字时触发；English triggers：convert to markdown, document conversion, extract docx/pdf content, batch convert, file to text, OCR extraction, audio transcription。不适用边界：PDF 创建与编辑改用 ima-pdf，Word 创建与编辑改用 ima-doc，纯图片美化与处理改用 image-tools-suite，视频剪辑改用 ffmpeg-skill，纯在线网页抓取改用 web-scraper。
---

# MarkItDown 技能：把任何文档转成 Markdown

Microsoft 的轻量级 Python 工具，将 15 种以上文件格式转换为结构化 Markdown，输出天然适配 LLM 文本分析管道。本技能在官方能力之上补齐汉语化触发词、执行工作流、失败模式编码、反例红线与零依赖兜底脚本。

🔴 **适用范围声明**：本技能只负责"把已有文档读进来换成 Markdown"，不负责创建、编辑、美化、抓取与转码。边界细节见「反例与红线」章节。

---

## 🔴 检查点 1：环境确认

执行转换前，确认 markitdown 已正确安装：

```bash
# 验证安装
markitdown --version

# 如果未安装，执行以下命令安装完整版
pip install 'markitdown[all]'
```

🔴 **必检**：`markitdown --version` 必须返回版本号（≥0.0.1a3），否则转换命令会报 `command not found`，此时回退到本技能的 `scripts/md_convert.py` 处理纯文本类文件。

---

## 支持的格式

| 类别 | 格式 | 转换质量 | 说明 |
|------|------|----------|------|
| 文档 | PDF（文字层） | ★★★★★ | 直接提取文本，保留标题/表格结构 |
| 文档 | PDF（扫描件） | ★★☆☆☆ | 需 Azure OCR，无 API 密钥时降级 |
| 文档 | Word (DOCX) | ★★★★★ | 完整保留标题层级、表格、列表、超链接 |
| 演示 | PowerPoint (PPTX) | ★★★★☆ | 提取幻灯片标题、正文、备注区文本 |
| 表格 | Excel (XLSX/XLS) | ★★★★☆ | 表头+数据转 Markdown 表格，复杂公式丢弃 |
| 图片 | PNG/JPG/GIF/BMP/TIFF | ★★★☆☆ | EXIF 元数据 + OCR 文字提取（需 API） |
| 音频 | MP3/WAV/M4A/OGG | ★★★☆☆ | EXIF + 语音转文字（需 API） |
| 网页 | HTML | ★★★★★ | 提取正文，自动剔除导航/广告/页脚 |
| 数据 | CSV | ★★★★★ | 原样转 Markdown 表格 |
| 数据 | JSON | ★★★★☆ | 格式化缩进输出 |
| 数据 | XML | ★★★★☆ | 提取文本节点 |
| 压缩 | ZIP | ★★★☆☆ | 一层解压后逐文件转换，不递归子 ZIP |
| 电子书 | EPUB | ★★★★☆ | 按章节提取文本 |
| 视频 | YouTube URL | ★★★☆☆ | 提取字幕与描述（需联网） |

格式级差异与逐条限制见 references/format-support.md。

---

## 🔴 检查点 2：文件格式确认

🔴 **必检**：转换前确认文件扩展名是否在支持列表中。旧版二进制格式（`.doc` / `.xls` / `.ppt`）不支持，必须先转换为 `.docx` / `.xlsx` / `.pptx`。

🔴 **必检**：确认输入文件是否为加密/受保护文档（Office 的"限制编辑"、PDF 的用户密码、ZIP 的压缩密码）。加密文档不做暴力破解，直接按「失败模式」第 6 条降级处置。

---

## 执行工作流

按以下八步执行一次转换任务。每步标注 **输入 → 动作 → 输出**，命令可直接复制运行。

1. **环境侦察**（输入：本地终端 → 动作：校验 markitdown 与 Python 可用性 → 输出：版本号与退出码）

   ```bash
   markitdown --version
   python3 --version
   python3 -c "import markitdown, sys; print(getattr(markitdown, '__version__', 'unknown'))"
   ```

   若 `markitdown` 不可用，转「失败模式」第 1 条，用本技能脚本对纯文本类文件兜底。

2. **文件盘点**（输入：待处理目录 → 动作：按扩展名清点数量并分流 → 输出：可直转清单与需预处理清单）

   ```bash
   find /path/to/docs -type f \( -name '*.pdf' -o -name '*.docx' -o -name '*.pptx' \) | wc -l
   find /path/to/docs -type f -name '*.doc' -o -name '*.xls' -o -name '*.ppt'
   ```

3. **预处理**（输入：旧版格式文件、非 UTF-8 文件、加密文件 → 动作：LibreOffice 转 OOXML、iconv 转 UTF-8、解密后另存 → 输出：可被 MarkItDown 识别的干净文件）

   ```bash
   libreoffice --headless --convert-to docx old_file.doc
   iconv -f GBK -t UTF-8 gbk.txt > gbk_utf8.txt
   ```

4. **单文件转换**（输入：一个干净文件 → 动作：运行 markitdown 并重定向 → 输出：Markdown 文件）

   ```bash
   markitdown report.pdf > report.md
   markitdown contract.docx | grep -i "违约金"
   ```

5. **批量调度**（输入：整个目录 → 动作：调用本技能零依赖脚本 scripts/md_convert.py 做目录级转换并写运行日志 → 输出：`.md` 集合与 `run.log`）

   ```bash
   python3 scripts/md_convert.py --input /path/to/docs --outdir /path/to/out --log run.log
   python3 scripts/md_convert.py --input /path/to/docs --dry-run
   ```

   该脚本零第三方依赖，处理 `.txt/.log/.html/.htm/.csv`，对 PDF/Office 类文件仍由 markitdown 主程序承担。

6. **质量校验**（输入：产物 `.md` → 动作：检查文件非空、标题数与表格数是否合理 → 输出：每件产物的校验结论）

   ```bash
   [ -s report.md ] && echo "✅ 非空" || echo "❌ 空文件"
   grep -c '^#' report.md
   grep -c '^|' report.md
   ```

7. **结构修补**（输入：校验不合格的 `.md` → 动作：按「失败模式」对应分支回退重跑（改编码、转 OOXML、拆分大文件、先 OCR） → 输出：修补后的 `.md`）

   ```bash
   pdftk large.pdf cat 1-50 output part1.pdf
   markitdown part1.pdf > part1.md
   ```

8. **归档交付**（输入：合格 `.md` → 动作：落库到目标管道或喂给大模型 → 输出：交付记录与转换参数留痕）

   ```bash
   cp *.md /path/to/kb/markdown/
   grep -c '^#' /path/to/kb/markdown/*.md
   ```

---

## 使用方式

### 命令行 CLI

```bash
# 转换单个文件
markitdown <input_file> > output.md

# 批量转换目录（PDF 示例）
for f in /path/to/docs/*.pdf; do
  markitdown "$f" > "${f%.pdf}.md"
done

# 转换 ZIP（一层解压后逐文件处理）
markitdown archive.zip > combined.md

# 多文件合并转换
markitdown file1.docx file2.pdf file3.pptx > combined.md
```

### Python API

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()

input_dir = Path("/data/documents")
for doc in input_dir.glob("*.*"):
    if doc.suffix.lower() in [".pdf", ".docx", ".pptx", ".xlsx"]:
        result = md.convert(str(doc))
        out = doc.with_suffix(".md")
        out.write_text(result.text_content, encoding="utf-8")
        print(f"✅ {doc.name} → {out.name}")
```

### 带 LLM 客户端（图片 OCR 与音频转写）

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI(api_key="your-key")
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("image.png")
print(result.text_content)
```

---

## 🔴 检查点 3：API 密钥检查

🔴 **必检**：图片 OCR 和音频转写需要 Azure Document Intelligence 或 LLM API 密钥。执行前检查环境变量：

```bash
# 检查 Azure 密钥是否配置
echo $AZURE_DOCUMENT_INTELLIGENCE_KEY
echo $AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
echo $AZURE_SPEECH_KEY
echo $AZURE_SPEECH_REGION
```

🔴 **必检**：以上变量为空时，图片与音频转换只输出文件元数据（文件名、大小、格式），不含 OCR 文字或转录文本。此时按「失败模式」第 3 条降级到本地转写工具，不要静默交付空内容。

---

## 关键特性

| 特性 | 说明 |
|------|------|
| 结构保留 | 输出 Markdown 保留标题层级、表格、有序/无序列表、超链接 |
| Token 效率 | Markdown 格式比纯文本节省约 30% token 消耗 |
| LLM 原生 | 输出格式天然适配 GPT-4o、Claude 等大模型的输入要求 |
| 插件扩展 | 通过 `--use-plugins` 参数加载第三方转换插件 |
| OCR 集成 | Azure Document Intelligence 支持多语言图片文字提取 |
| 音频转写 | 支持 MP3/WAV/M4A/OGG 等格式的语音转文字 |
| 零依赖兜底 | 本技能 scripts/md_convert.py 在无 markitdown 时处理纯文本类文件 |

---

## 🔴 检查点 4：输出质量验证

🔴 **必检**：转换完成后检查输出文件。执行以下验证：

```bash
# 检查输出文件是否存在且非空
[ -s output.md ] && echo "✅ 转换成功" || echo "❌ 转换失败：输出为空"

# 检查文件大小是否合理
wc -c output.md

# 检查标题与表格是否落地
grep -c '^#' output.md
```

输出为空时按「失败模式」逐条排查：格式是否受支持、是否为扫描件 PDF、编码是否正确。

---

## 🔴 检查点 5：编码与大文件处理

🔴 **必检**：处理中文文档时确认编码，处理大文件时注意内存。

```bash
# 中文乱码时，先转换编码
iconv -f GBK -t UTF-8 source.txt > source_utf8.txt
markitdown source_utf8.txt

# 大文件（>100MB）拆分处理
pdftk large.pdf cat 1-50 output part1.pdf
markitdown part1.pdf > part1.md
```

🔴 **必检**：单文件超过 100MB 时不要一次性加载，先按页或按工作表拆分，再逐件转换并对账件数。

---

## 使用示例

### 使用示例一：合同 Word 批量转 Markdown 供条款检索

输入一个装有多份 `.docx` 合同的目录，批量转换后按关键词定位条款：

```bash
python3 scripts/md_convert.py --input /data/contracts --outdir /data/contracts_md --log convert.log
grep -rn "违约金" /data/contracts_md/
```

转换产物保留标题层级与表格，条款检索命中位置可直接回填到审查底稿。

### 使用示例二：扫描件 PDF 先 OCR 再转 Markdown

扫描件无文字层时，先用 OCR 产出文字层，再交给 MarkItDown：

```bash
python3 scripts/md_convert.py --input scan.txt --outdir ocr_out
markitdown scan.pdf > scan.md
```

若 OCR 服务未配置，按「失败模式」第 2 条降级到本地 OCR 工具，不要直接交付空文件。

### 使用示例三：ZIP 资料包整体转换

把压缩包内的受支持文件一次性转成合并 Markdown：

```bash
markitdown archive.zip > combined.md
grep -n '^#' combined.md
```

嵌套子 ZIP 不在一次转换范围内，按「失败模式」第 7 条先递归解压再批量转换。更多场景见 references/usage-examples.md。

---

## 已知限制

- 扫描件 PDF 无文字层时，OCR 依赖 Azure Document Intelligence API，未配置则输出为空
- Excel 公式仅保留缓存值，不执行重算；图表、图片、SmartArt 不转换
- Word 多栏排版、文本框、艺术字可能丢失格式；VBA 宏代码不提取
- 音频转写精度取决于语音清晰度，方言和背景噪音会降低准确率
- ZIP 仅一层解压，嵌套 ZIP 不递归处理
- 动态渲染的 HTML（JavaScript 加载内容）无法提取，仅处理静态 HTML
- 单文件超过 100MB 可能触发内存溢出，需分段处理
- 加密文档（Office 限制编辑、PDF 用户密码、加密 ZIP）不支持直接读取

---

## 失败模式

以下为转换过程中常见的失败场景与对应处置。每条格式为"如果 X → 则 Y（降级 / 回退 / 重试 / 兜底）"。

**失败模式 1 — 环境缺失**：如果 `markitdown` 命令不存在 → 则先 `pip install 'markitdown[all]'` 重试；安装不可行时回退到本技能零依赖脚本 scripts/md_convert.py 处理纯文本类文件（兜底降级）。

**失败模式 2 — 扫描件 PDF 无文字层**：如果 PDF 是纯图片扫描件且未配置 OCR → 则输出为空或仅含元数据，必须先走 OCR 提取文字层，再转换；无 OCR 时标记为"需人工处理"，不得交付空文件（回退并标注）。

**失败模式 3 — 音频转写无密钥或模型未装**：如果音频转换后只有元数据没有转录文本 → 则检查 `AZURE_SPEECH_KEY`；密钥缺失且本地未装语音模型时，降级到本地转写工具先出文本，再合并进 Markdown（降级 + 兜底）。

**失败模式 4 — Excel 公式值丢失**：如果 Excel 含 VLOOKUP/SUM 等公式 → 则输出为缓存值或空值，先用 `libreoffice --headless --calc --convert-to xlsx formula_file.xlsx` 强制重算，再重试转换（重试）。

**失败模式 5 — 编码乱码**：如果源文件为 GBK/GB2312 编码 → 则输出乱码或触发 UnicodeDecodeError，先用 `iconv -f GBK -t UTF-8 source.txt > source_utf8.txt` 转码后重试（回退重跑）。

**失败模式 6 — 加密文档**：如果文档带密码或限制编辑 → 则 MarkItDown 读取异常或抛错，先解密并另存为可读副本再转换；无法解密时终止该项并在日志记录"待人工授权"，严禁暴力破解（终止 + 记录）。

**失败模式 7 — 超大文件内存溢出**：如果处理超过 100MB 的 PDF 或 Excel → 则进程被 OOM Killer 终止，先用 `pdftk` 拆页或按工作表拆分后逐件转换，并对账件数（分段重试）。

**失败模式 8 — 扫描表格结构丢失**：如果扫描件中的表格被 OCR 后压成一行纯文本 → 则先转成 CSV/表格结构再转 Markdown，或人工补表头与分隔行；结构无法机器还原时标注"表格待核"（结构补救）。

**失败模式 9 — ZIP 内子文件不递归**：如果 ZIP 内含嵌套 ZIP → 则子包内容不会被转换，先 `find . -name "*.zip" -exec unzip -o {} -d extracted/ \;` 递归解压后批量转换（补跑）。

**失败模式 10 — 动态 HTML 内容丢失**：如果网页依赖 JavaScript 动态加载 → 则转换输出为空或缺失正文，先用浏览器保存为完整 HTML 或配合 Playwright 插件（`--use-plugins`）后重试（降级替换）。

失败模式清单另见 references/failure-modes.md，排障细节与命令对照表一并收录。

---

## 反例与红线

🔴 **红线一**：不要用 MarkItDown 创建或编辑 PDF、Word、PPT、Excel。这类任务不适用本技能，改用专用工具（PDF 走 ima-pdf，Word 走 ima-doc，表格走 xlsx 类技能）。

🔴 **红线二**：严禁把扫描件 PDF 当文字层 PDF 直接处理。未 OCR 就交付空文件属于不可接受的失败交付，必须按「失败模式」第 2 条回退并标注。

🔴 **红线三**：禁止跳过编码检测直转 GBK 文件。中文乱码会污染下游检索与训练语料，必须先 `iconv` 转 UTF-8。

🔴 **红线四**：不可对加密文档盲目重试或尝试破译。无授权凭据时终止该项并留痕，越权解密是红线行为。

🔴 **红线五**（黑名单做法）：把 ZIP 当递归包一次转完、把视频当音频转写、对超过 100MB 单文件一次性加载——这三类反模式一律不要做。

🔴 **红线六**（反模式）：不要在未校验产物非空、未核对件数的情况下，把 Markdown 直接喂给大模型或落库。先过「检查点 4」，再交付。

🔴 **红线七**：不在范围内的任务不做——视频剪辑、图片美化、在线网页抓取、PDF/Word 创建编辑，均属边界之外。

---

## 🔴 检查点 6：交付前自检

🔴 **必检**：交付前逐项核对，任一项不通过就停下整改：

```bash
# 1. 件数对账：源文件数 vs 产物数
find /path/to/docs -type f \( -name '*.pdf' -o -name '*.docx' \) | wc -l
ls /path/to/out/*.md | wc -l

# 2. 空文件扫描
find /path/to/out -name '*.md' -size 0

# 3. 结构抽检：标题与表格是否落地
grep -c '^#' /path/to/out/sample.md
```

🔴 **人审**：对扫描件、音频、加密文档三类高风险输入，产物需经人工确认后方可落库。

---

## 参考资料

- GitHub：https://github.com/microsoft/markitdown
- PyPI：https://pypi.org/project/markitdown/
- 官方文档：https://microsoft.github.io/markitdown/
- 格式支持详情：references/format-support.md
- 使用示例：references/usage-examples.md
- 失败模式排障：references/failure-modes.md
- 零依赖调度脚本：scripts/md_convert.py
- 发布说明：PUBLISH.md
