---
name: ali-asr
description: "阿里云 DashScope 语音转写统一入口（非实时文件转写，模型 qwen-audio-3.0-asr-flash-filetrans）。把音频/视频文件或公开 URL 转成文字，支持逐句时间戳、说话人分离、热词纠错与多语种；输出标准 JSON（text/transcripts/sentences），供 meeting-minutes-pipeline（会议纪要）与 link-report-archiver（链接内容归档）作为转写后端调用。当用户提到语音转写、音频转文字、录音转文字、会议录音整理、字幕生成、说话人分离、ASR、transcribe、speech to text 时使用。英文触发词：ASR, speech to text, audio transcription, speaker diarization。不适用于纯本地离线转写（用 whisper-local）、实时语音对话（用 qwen-audio realtime）、图片文字识别（用 textin-xparse）。"
version: 1.0.0
author: 清风明月
display_name: 阿里语音转写
slug: ali-asr
category: 科技
tags: ["实时语音对话（用", "图片文字识别（用"]
---

# ali-asr — 语音转写（DashScope）

## 使用说明

1. **用途**：阿里云 DashScope 语音转写统一入口（非实时文件转写，模型 qwen-audio-3.0-asr-flash-filetrans）。
2. **典型问法**：“语音转写”、“音频转文字”、“录音转文字”、“会议录音整理”。
3. **调用方式**：在 ima 对话中直接描述需求或上传相关文件，本技能按触发词自动匹配调用。
4. **注意事项**：纯本地离线转写（用 whisper-local）、实时语音对话（用 qwen-audio realtime）、图片文字识别（用 textin-xparse）。

## 一、定位声明

阿里云 DashScope 非实时文件转写统一入口，为上层链路提供稳定的转写服务与统一 JSON 结构。当前后端模型为 `qwen-audio-3.0-asr-flash-filetrans`（2026-09-12 实测可用；该模型名不在百炼 2026-10-10 下线清单内）。脚本自包含，仅依赖 `requests` 与 `DASHSCOPE_API_KEY`。

被以下技能作为转写后端调用：

- `meeting-minutes-pipeline`：录音 → 转写 → 结构化 → 公文格式 Word 纪要
- `link-report-archiver`：链接内容解析 → 视频音轨 → 转写 → 结构化报告

## 二、触发条件

- 关键词：语音转写、音频转文字、录音转文字、字幕生成、说话人分离、ASR、转写
- 场景：会议录音整理、访谈录音整理、视频字幕生成、播客转稿
- English：ASR, speech to text, audio transcription, speaker diarization

不适用：纯本地离线转写（`whisper-local`）；实时语音对话（`qwen-audio` realtime）；图片文字识别（`textin-xparse`）。

## 三、用法

```bash
# 基础转写（本地文件或公开 URL）
python3 scripts/transcribe.py <音频文件或URL> --out 结果.json

# 说话人分离
python3 scripts/transcribe.py 会议.m4a --diarization --speakers 3 --out 结果.json

# 热词纠错（提升专有名词准确率）
python3 scripts/transcribe.py 录音.mp3 --vocab "某市:5,PPP:5,街办:4" --out 结果.json
```

参数：`--out/-o` 结果 JSON 路径；`--diarization` 开启说话人分离；`--speakers N` 说话人数量；`--lang` 语言提示（默认 zh）；`--vocab` 热词；`--model` 指定转写模型。

长音频（>1 小时）按 10 分钟切段并行调用，再合并 `sentences`。

## 四、输出格式

`--out` 指定 `.json` 时写入结构化结果，字段与上层链路契约一致：

```json
{
  "text": "全文（逐句换行，含说话人前缀）",
  "transcripts": [{"text": "全文", "sentences": [{"text": "句子", "speaker_id": "0", "begin_time": 120, "end_time": 2400}]}],
  "sentences": [{"text": "句子", "speaker_id": "0", "begin_time": 120, "end_time": 2400}]
}
```

`stdout` 同时打印逐句文本，供只读 stdout 的链路直接捕获。

## 五、失败模式与降级路径

1. **F1 缺少 API Key**：检出未配置 `DASHSCOPE_API_KEY` → 立即报错退出（退出码 1），提示写入环境变量或 `~/.dashscope_config.json`；不静默返回空结果。
2. **F2 上传失败**：获取上传凭证或文件上传非 200/204 → 报错并打印状态码与响应片段；改用公开 URL 传入可不经上传。
3. **F3 任务失败**：任务状态为 FAILED/UNKNOWN/CANCELED → 打印完整响应片段后退出；不重试同一任务，避免重复计费。
4. **F4 结果为空**：转写成功但句数为 0 → 打印「(空)」，仍写出 JSON；上层链路据此判定音频无有效语音。
5. **F5 音频质量差**：低码率（16kHz/24kbps 类）音频识别质量下降 → 先用 ffmpeg 归一化为 16kHz 单声道；如仍不可用，改用 `qwen-audio` 的 transcribe 通道交叉验证。
6. **F6 额度受限**：接口返回 Arrearage（欠费）→ 提示核查百炼账号余额；该状态下全部转写请求不可用。
7. **F7 上层链路路径查找失败**：`meeting-minutes-pipeline` 按候选路径查找本脚本 → 需保证 `ali-asr/scripts/transcribe.py` 与 `ali-asr/transcribe.py` 同时存在（根目录为兼容转发入口）。

## 六、🔴 关键检查点

🔴 CHECKPOINT-1｜转写前：确认音频文件存在且非空；本地文件路径含中文时先复制到 ASCII 临时路径，避免上传编码问题。

🔴 CHECKPOINT-2｜说话人分离：`--speakers` 取值需与真实会话人数一致，取值偏差会显著拉低分离准确率；不确定时不传该参数。

🔴 CHECKPOINT-3｜结果交付前：核对 JSON 中 `text` 与 `sentences` 是否一致、是否有明显截断；长音频分段结果的段间衔接需人工抽查。

🔴 CHECKPOINT-4｜敏感内容：音频涉及个人隐私、未公开经营信息时，转写结果按内部资料管理，不外传、不入公网。

## 七、依赖说明

- `requests`：HTTP 调用；缺失时先 `pip install requests`
- `DASHSCOPE_API_KEY`：阿里云百炼 API Key（环境变量或 `~/.dashscope_config.json`）
- `ffmpeg`：非必需，用于音频归一化与长音频切段

## 八、集成契约（供上层链路调用）

命令行契约（两个上游链路共同依赖，变更需同步）：

```bash
python3 <ali-asr路径>/transcribe.py <音频路径> [--out 结果.json] [--diarization] [--speakers N]
```

- 路径需同时满足：`skills/ali-asr/scripts/transcribe.py`、`skills/ali-asr/transcribe.py`、`ali-asr/transcribe.py`
- 输出 JSON 至少包含 `transcripts[].text` 或 `transcripts[].sentences[].text`，以及顶层 `text`

> 更多用法与示例见 `references/usage-and-examples.md`。

## 依赖安装

本技能脚本依赖第三方库，首次使用（或沙箱/换机重置）后请先安装：

```bash
python3 -m pip install -r requirements.txt
```
