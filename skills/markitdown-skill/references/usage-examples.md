# MarkItDown 使用示例

## 场景一：批量转换文档目录

将整个目录下的Office文档批量转为Markdown，供AI分析：

```bash
# 转换单个文件
markitdown report.pdf > report.md

# 批量转换目录下所有PDF
for f in /path/to/docs/*.pdf; do
  markitdown "$f" > "${f%.pdf}.md"
done
```

## 场景二：Python API 管道集成

在Python脚本中调用，适合构建自动化文档处理管道：

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()

# 批量转换
input_dir = Path("/data/documents")
for doc in input_dir.glob("*.*"):
    if doc.suffix.lower() in [".pdf", ".docx", ".pptx", ".xlsx"]:
        result = md.convert(str(doc))
        output_path = doc.with_suffix(".md")
        output_path.write_text(result.text_content, encoding="utf-8")
        print(f"✅ {doc.name} → {output_path.name}")
```

## 场景三：带OCR的图片文字提取

对扫描件图片做OCR提取文字（需Azure API密钥）：

```python
from markitdown import MarkItDown
from openai import OpenAI

# 配置LLM客户端用于OCR
client = OpenAI(api_key="your-api-key")
md = MarkItDown(llm_client=client, llm_model="gpt-4o")

result = md.convert("scanned_page.png")
print(result.text_content)
```

## 场景四：提取Excel数据为Markdown表格

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("quarterly_report.xlsx")
# 输出为Markdown表格，直接粘贴到文档或喂给LLM
print(result.text_content)
```

## 场景五：CLI管道处理

```bash
# 转换后提取特定关键词
markitdown contract.docx | grep -i "违约金"

# 转换后统计字数
markitdown thesis.pdf | wc -w

# 多文件合并转换
markitdown file1.docx file2.pdf file3.pptx > combined.md
```

## 场景六：处理ZIP压缩包

```bash
# ZIP内所有支持格式会被解压并逐个转换
markitdown archive.zip > extracted_content.md
```

## 与其他工具配合

- **配合 pandoc**：MarkItDown转Markdown → pandoc转PDF/HTML
- **配合 LLM**：转Markdown → 喂给GPT-4o/Claude做摘要/问答
- **配合知识库**：批量转Markdown → 导入向量数据库做RAG检索
