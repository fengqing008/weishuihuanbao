# 文档转Markdown官（markitdown-skill）发布说明

## 一、技能简介

把 PDF、Word（DOCX）、PowerPoint（PPTX）、Excel（XLSX/XLS）、图片（OCR）、音频（转写）、HTML、CSV、JSON、XML、ZIP、YouTube 链接、EPUB 等 15 种以上文件格式批量转成结构化 Markdown，保留标题层级、表格、列表与超链接。输出天然适配大模型文本分析管道，可直接用于条款检索、语料准备、RAG 入库与汇报底稿整理。

本技能在 Microsoft MarkItDown 官方能力之上，补齐汉语化触发词、八步执行工作流、10 条失败模式编码、6 处检查点与 7 条反例红线，并附带零第三方依赖的兜底调度脚本。

- 版本：0.3.0
- 作者：清风明月
- 标识：slug = qf-markitdown-skill；display_name = 文档转Markdown官
- 许可：MIT（沿用上游 MarkItDown 许可）

### 使用说明（6 条）

1. **单文件转 Markdown**：说「把这份 PDF 转成 Markdown」，我保留标题层级、表格与列表。
2. **Office 批量转换**：说「Word / PPT / Excel 批量转 Markdown」，我按目录批量处理。
3. **图片 OCR 提取**：说「从图片里提取文字转 Markdown」，我走 OCR 通道识别并整理。
4. **音视频转写**：说「把这段音频 / 视频转写并整理成文本」，我转写后输出 Markdown。
5. **保留结构批量转换**：说「整个文件夹的文档批量转换，保留标题层级和表格」，我逐文件转换。
6. **多格式入知识库**：说「把 HTML / EPUB / CSV 也转成 Markdown」，我统一格式便于入库。

## 二、使用示例

### 示例一：单文件转 Markdown

```bash
markitdown report.pdf > report.md
markitdown contract.docx | grep -i "违约金"
```

### 示例二：目录批量转换（零依赖调度脚本）

```bash
python3 scripts/md_convert.py --input /path/to/docs --outdir /path/to/out --log run.log
python3 scripts/md_convert.py --input /path/to/docs --dry-run
```

脚本零第三方依赖，处理 `.txt/.log/.html/.htm/.csv`，并输出可追溯的运行日志；PDF/Office 类文件由 markitdown 主程序承担。

### 示例三：Python API 管道集成

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()
for doc in Path("/data/documents").glob("*.*"):
    if doc.suffix.lower() in [".pdf", ".docx", ".pptx", ".xlsx"]:
        result = md.convert(str(doc))
        doc.with_suffix(".md").write_text(result.text_content, encoding="utf-8")
```

## 三、适用场景

1. 合同、制度、报告等 Word/PDF 批量转 Markdown，供条款检索与审查底稿使用。
2. 会议资料、课件、Excel 台账转 Markdown，做语料准备与大模型问答入库。
3. ZIP 资料包整体转换，形成合并 Markdown 便于全文检索。
4. 扫描件 PDF、图片、音频等非文本源，经 OCR 或转写后统一成 Markdown。
5. 在未安装 markitdown 依赖的环境里，用附带脚本对纯文本类文件兜底转换。

## 四、不适用边界

- PDF 创建与编辑：改用 ima-pdf。
- Word 创建与编辑：改用 ima-doc。
- 纯图片美化与处理：改用 image-tools-suite。
- 视频剪辑与转码：改用 ffmpeg-skill。
- 纯在线网页抓取：改用 web-scraper。
- 加密文档的越权解密、扫描件未 OCR 的空文件交付、超过 100MB 单文件一次性加载：均属红线，禁止执行。

## 五、环境依赖

- markitdown 主程序：`pip install 'markitdown[all]'`。
- OCR / 音频转写密钥：`AZURE_DOCUMENT_INTELLIGENCE_KEY`、`AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`、`AZURE_SPEECH_KEY`、`AZURE_SPEECH_REGION`。
- 兜底脚本 scripts/md_convert.py：仅需 Python 3.8+ 标准库，无第三方依赖。

## 六、文件清单

| 文件 | 说明 |
|------|------|
| SKILL.md | 技能主文档（触发词、工作流、失败模式、检查点、反例红线） |
| references/format-support.md | 格式支持与限制明细 |
| references/usage-examples.md | 使用场景示例 |
| references/failure-modes.md | 失败模式与排障命令对照 |
| scripts/md_convert.py | 零依赖 Markdown 转换与批量调度脚本 |
| PUBLISH.md | 本发布说明 |

## 七、版本与作者

- 版本：0.3.0（由 0.2.0 升级）
- 作者：清风明月
- 上游：Microsoft MarkItDown（https://github.com/microsoft/markitdown）
