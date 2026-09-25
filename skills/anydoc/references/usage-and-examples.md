# anydoc · 用法与示例

## 一、适用场景

本地把 20 种办公文档毫秒级转成 GitHub 风格 Markdown，文件不出本机。命中以下即用：读 docx/pptx/xlsx/pdf 内容并分析、入库前统一转 md、批量提取全文、从 Office 抽表格章节。
核心资产为 npm 包 `@firecrawl/anydoc`（npx 一键调用，Node 20+），无本地脚本。
不适用：扫描件/纯图片 PDF（无文字层，OCR 用 textin-xparse）、PDF 创建编辑（用 ima-pdf）、Word 创建编辑（用 ima-doc）。

## 二、典型用法

```bash
# 小文件直接转（Markdown 输出到 stdout）
npx -y @firecrawl/anydoc <file>

# 大文件落盘再按片段读
npx -y @firecrawl/anydoc <file> -o out.md

# stdin 流式输入（CSV 等无扩展名场景需 --format 显式指定）
npx -y @firecrawl/anydoc - --format csv < f
```

首次调用会下载 npm 包（约几秒），之后走 npx 缓存。大文档一律 `-o` 落盘后分片读。
支持格式：`.doc .docx .docm .odt .rtf .epub .pdf .ppt .pps .pot .pptx .pptm .ppsx .ppsm .odp .xls .xlsx .xlsm .xlsb .ods .csv`。

## 三、参数说明

| 参数 | 含义 | 默认值 | 示例 |
|---|---|---|---|
| 位置参数 | 输入文件路径，`-` 表示 stdin | 无 | `报告.pdf` |
| `-o` | 输出 .md 文件路径 | 无（默认 stdout） | `-o out.md` |
| `--format <name>` | 显式指定格式（仅 stdin/扩展名缺失或错误时用） | 按内容自动识别 | `--format csv` |

退出码：`0`=成功；`1`=文档无法转换；`2`=用法错误。失败时 stderr 输出一行 `anydoc: <message>`，CLI 从不交互提示。

## 四、场景示例

**示例 1：合同文档入库前统一转 Markdown**
- 输入：`./合同/` 下 N 份 .docx
- 操作：逐份 `npx -y @firecrawl/anydoc "./合同/某某施工合同.docx" -o "./合同_md/某某施工合同.md"`
- 输出：同名 .md 一一对应；每份退出码 0；抽查标题行与金额表格是否保留；汇报成功/失败份数

**示例 2：读取 PDF 报告做摘要**
- 输入：`行业报告.pdf`
- 操作：`npx -y @firecrawl/anydoc 行业报告.pdf -o /tmp/行业报告.md` → 按章节读片段
- 输出：基于原文提炼的要点，关键结论标注来源章节

**示例 3：代码中调用库**
- 输入：Node/Python/Rust 工程需内嵌转换能力
- 操作：用库 `@firecrawl/anydoc`（npm）、`firecrawl-anydoc`（PyPI）、`anydoc`（crates.io），均暴露同一 `to_markdown` / `toMarkdown` API
- 输出：函数返回的 Markdown 字符串

## 五、注意事项与常见问题

- 先确认文件非扫描件：首页无文字的 PDF 先走 textin-xparse OCR，不要硬转。
- 大文件全文读进对话上下文属禁止行为，用 `-o` 落盘后按片段读。
- 转换结果表格错位：源文件复杂合并单元格导致，需人工核对或换库调用。
- 退出码 1：文档加密、损坏或无文字层——换 textin-xparse 或让用户换文件，禁止反复重试。
- 退出码 2：参数/用法错误，检查文件路径与 `--format` 写法。
- 网络不可用时降级用 textin-xparse 或平台自带解析；已有 npx 缓存则离线可用；沙箱重置后无需重装。详见 SKILL.md「使用规则」「依赖说明」两节。
