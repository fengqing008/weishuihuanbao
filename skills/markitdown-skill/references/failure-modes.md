# MarkItDown 失败模式与排障指南

## 失败模式清单

### FM-01：旧版二进制格式不支持
- **症状**：`.doc` / `.xls` / `.ppt` 文件转换报错或输出为空
- **原因**：MarkItDown仅支持OOXML格式（.docx/.xlsx/.pptx），不支持旧版二进制格式（.doc/.xls/.ppt）
- **解决方案**：用LibreOffice命令行转换为新版格式后再处理：
  ```bash
  libreoffice --headless --convert-to docx old_file.doc
  markitdown old_file.docx
  ```

### FM-02：扫描件PDF无文字层
- **症状**：PDF转Markdown输出为空或仅含少量元数据
- **原因**：PDF为纯图片扫描件，无嵌入文字层，且未配置Azure OCR
- **解决方案**：配置Azure Document Intelligence API密钥，或先用OCR工具（如Tesseract）提取文字层

### FM-03：音频转写无API密钥
- **症状**：MP3/WAV等音频文件转换后仅输出文件元数据，无转录文本
- **原因**：语音转写功能依赖Azure Speech Services或LLM API，未配置密钥
- **解决方案**：设置环境变量 `AZURE_SPEECH_KEY` 和 `AZURE_SPEECH_REGION`，或使用 `--use-plugins` 参数配合本地Whisper模型

### FM-04：Excel复杂公式丢失
- **症状**：含VLOOKUP/SUM等公式的单元格输出为上次计算的值或空值
- **原因**：MarkItDown读取的是Excel存储的缓存值，不执行公式重算
- **解决方案**：转换前用LibreOffice打开并保存一次（强制公式重算）：
  ```bash
  libreoffice --headless --calc --convert-to xlsx formula_file.xlsx
  ```

### FM-05：编码乱码
- **症状**：中文文档输出出现乱码或UnicodeDecodeError
- **原因**：源文件为GBK/GB2312编码，MarkItDown默认按UTF-8读取
- **解决方案**：先用 `iconv` 转换编码：
  ```bash
  iconv -f GBK -t UTF-8 source.txt > source_utf8.txt
  markitdown source_utf8.txt
  ```

### FM-06：大文件内存溢出
- **症状**：处理超过100MB的PDF或Excel时进程被OOM Killer终止
- **原因**：MarkItDown一次性加载整个文件到内存
- **解决方案**：分文件/分页处理；对PDF用 `pdftk` 拆分后逐个转换

### FM-07：ZIP内子文件不递归
- **症状**：ZIP中的ZIP子包未被转换，输出缺失部分内容
- **原因**：MarkItDown对ZIP仅做一层解压，不递归处理嵌套压缩包
- **解决方案**：手动递归解压后再批量转换：
  ```bash
  find . -name "*.zip" -exec unzip -o {} -d extracted/ \;
  find extracted/ -type f -exec markitdown {} \;
  ```

### FM-08：HTML正文提取失败
- **症状**：某些动态渲染的网页转换后内容为空
- **原因**：MarkItDown使用静态HTML解析，无法处理JavaScript动态加载内容
- **解决方案**：先用浏览器渲染并保存为完整HTML，或用 `--use-plugins` 配合Playwright插件
