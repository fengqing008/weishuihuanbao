---
name: ali-asr
display_name: 阿里语音转写
version: 1.1.0
description: 阿里云 DashScope 语音转写统一入口（非实时文件转写，模型 qwen-audio-3.0-asr-flash-filetrans）。把音频/视频文件或公开
  URL 转成文字，支持逐句时间戳、说话人分离、热词纠错与多语种；输出标准 JSON（text/transcripts/sentences），供 meeting-minutes-pipeline（会议纪要）与
  link-report-archiver（链接内容归档）作为转写后端调用。当用户提到语音转写、音频转文字、录音转文字、会议录音整理、字幕生成、说话人分离、ASR、transcribe、speech
  to text 时使用。英文触发词：ASR, speech to text, audio transcription, speaker diarization。不适用于纯本地离线转写（用
  whisper-local）、实时语音对话（用 qwen-audio realtime）、图片文字识别（用 textin-xparse）。
author: 清风明月
slug: ali-asr
category: 科技
tags:
- 实时语音对话（用
- 图片文字识别（用
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

## 二、触发条件与路由

| 场景域 | 典型问法 | 路由处置 |
|---|---|---|
| 会议录音整理 | “把这段会议录音转成文字” | 走本技能，输出 JSON 交会议纪要链路 |
| 访谈/电话录音 | “访谈录音转稿” | 走本技能，可开说话人分离 |
| 视频字幕生成 | “给这个视频生成字幕” | 先抽音轨（ffmpeg），再走本技能 |
| 播客转稿 | “播客音频转文字” | 走本技能，长音频分段 |
| 专有名词多 | “某市、PPP 这些词要准” | 走本技能，用 `--vocab` 热词 |
| 纯本地离线需求 | “不想联网，本地转” | 不调本技能，改走 `whisper-local` |
| 实时语音对话 | “和 AI 实时语音聊天” | 不调本技能，改走 `qwen-audio` realtime |
| 图片文字识别 | “把这张截图转文字” | 不调本技能，改走 `textin-xparse` |

- 中文触发词：语音转写、音频转文字、录音转文字、字幕生成、说话人分离、ASR、转写。
- **English triggers**：ASR, speech to text, audio transcription, speaker diarization, meeting transcription, subtitle generation。
- 不适用：纯本地离线转写（`whisper-local`）；实时语音对话（`qwen-audio` realtime）；图片文字识别（`textin-xparse`）。

## 三、用法

```bash
# 基础转写（本地文件或公开 URL）
python3 scripts/transcribe.py <音频文件或URL> --out 结果.json

# 说话人分离
python3 scripts/transcribe.py 会议.m4a --diarization --speakers 3 --out 结果.json

# 热词纠错（提升专有名词准确率）
python3 scripts/transcribe.py 录音.mp3 --vocab "某市:5,PPP:5,街办:4" --out 结果.json

# 交付前契约自检（仅标准库，检查 JSON 结构/句数/时间戳单调性）
python3 scripts/asr_check.py --json 结果.json --json
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

## 五、可交付物与输出规范

| 交付物 | 载体 | 关键约束 | 验收要点 |
|---|---|---|---|
| 转写结果 JSON | `--out` 指定 `.json` | 含顶层 `text` 与 `sentences[]`（speaker_id/begin_time/end_time） | `asr_check.py` 结构校验通过 |
| 逐句文本 | stdout | 逐句换行，含说话人前缀 | 与 JSON 一致、无截断 |
| 说话人分离表 | JSON `sentences[].speaker_id` | `--diarization` 开启，`--speakers N` 与真实人数一致 | 分段合理 |
| 长音频分段合并件 | JSON | 按 10 分钟切段后合并 `sentences` | 段间衔接抽查无缺句 |
| 自检报告 | `scripts/asr_check.py` | 句数/时间戳单调性/字段完整性 | 退出码 0 |

交付回复附：源文件名、时长、模型名、是否开启说话人分离、句数、自检结论；涉及敏感内容时标注按内部资料管理。

## 六、引用依据与溯源

本技能的上传、调用、数据处理口径以下列权威依据为准，引用时写全称与文号，不以印象代替出处：

| 序号 | 依据全称 | 文号 / 标识 | 引用点 |
|---|---|---|---|
| 1 | 《中华人民共和国个人信息保护法》 | 中华人民共和国主席令第 91 号（2021-08-20 通过） | 录音含个人信息时的处理与最小必要原则 |
| 2 | 《中华人民共和国数据安全法》 | 中华人民共和国主席令第 84 号（2021-06-10 通过） | 转写文本的数据分级与本地留存 |
| 3 | 《中华人民共和国网络安全法》 | 中华人民共和国主席令第 53 号（2016-11-07 通过） | 数据不出境、接口调用合规 |
| 4 | 《中华人民共和国著作权法》（2020 年修正） | 中华人民共和国主席令第 62 号 | 转写音频素材的合法来源核验 |
| 5 | 《信息技术 中文语音识别系统通用技术规范》 | GB/T 21024—2007 相关语音处理标准 | 识别质量与评测口径参照 |
| 6 | 阿里云百炼 DashScope 语音识别 API 文档（公开） | 模型 `qwen-audio-3.0-asr-flash-filetrans` | 接口契约与返回结构 |
| 7 | W3C《WebVTT: The Web Video Text Tracks Format》 | W3C Candidate Recommendation | 字幕时间轴格式参照 |

溯源纪律：字段与模型口径以 DashScope 官方文档为准；无法核实的模型下线时间、额度状态一律标注【待核】；**不编造**未发生的句数、时长与识别率，**不臆造**测试结果。

## 七、能力边界与不适用范围

本技能**只做「音/视频文件或公开 URL → 文字」的非实时转写**，并输出统一 JSON。以下不在范围内：

- **不做实时语音对话**（VAD、打断、双向流）——改走 `qwen-audio` realtime。
- **不做纯本地离线转写**——改走 `whisper-local`。
- **不做图片/扫描件文字识别**（OCR）——改走 `textin-xparse`。
- **不做视频画面理解**、抽帧、字幕烧录合成——改走视频处理类技能。
- **不做文本翻译、摘要、结构化改写**——本技能只交原始转写，语义加工交上层链路。
- **不做配音与语音合成（TTS）**——改走 `qwen-audio` 的 TTS 通道。
- **不做说话人身份实名核验**——只输出说话人编号，不推断真实姓名。

## 八、失败模式与降级路径

本技能对每一类**失败模式**预置了**降级**口径，所有**异常**走显式**错误处理**分支而非静默返回空结果；对网络/上传类瞬时故障设置有限**重试**与**容错**；外部依赖不可用时提供 **fallback**/**回退**与**兜底**方案；**边界条件**（空音频、超长音频、参数冲突）在入口处校验；任一段失败须保留已完成分段以支持**断点续跑**，并给出**补救**建议与**防御**性前置检查。

| 场景 | 触发条件 | 降级与补救处置 |
|---|---|---|
| F1 缺少 API Key | 检出未配置 `DASHSCOPE_API_KEY` | 立即报错退出（退出码 1），提示写入环境变量或 `/root/.dashscope_config.json`；不静默返回空结果 |
| F2 上传失败 | 获取上传凭证或文件上传非 200/204 | 报错并打印状态码与响应片段；fallback：改用公开 URL 传入可不经上传；瞬时失败允许有限重试 |
| F3 任务失败 | 任务状态为 FAILED/UNKNOWN/CANCELED | 打印完整响应片段后退出；不重试同一任务，避免重复计费（错误处理） |
| F4 结果为空 | 转写成功但句数为 0 | 打印「(空)」，仍写出 JSON；上层链路据此判定音频无有效语音（补救：提示换源或校验音轨） |
| F5 音频质量差 | 低码率（16kHz/24kbps 类）识别质量下降 | 降级：先用 ffmpeg 归一化为 16kHz 单声道；仍不可用回退到 `qwen-audio` transcribe 通道交叉验证 |
| F6 额度受限 | 接口返回 Arrearage（欠费） | 提示核查百炼账号余额；该状态下全部转写请求不可用（兜底：提示稍后重试） |
| F7 上层路径查找失败 | 上层链路按候选路径找不到脚本 | 保证 `scripts/transcribe.py` 与根目录 `transcribe.py` 同时存在（兼容转发入口） |
| F8 网络中断 | SSE/HTTP 连接超时或中断 | 重试有限次后退出；已上传任务可由上层按 taskId 续查（断点续跑） |
| F9 长音频中断 | 多段并行时有段失败 | 容错：保留已完成段，仅重跑失败段再合并 `sentences` |
| F10 参数冲突 | `--diarization` 与不传 `--speakers` 冲突 | 边界条件校验：给默认或提示，不猜测真实人数 |
| F11 路径含中文/特殊字符 | 上传编码异常 | 防御：先复制到 ASCII 临时路径再上传 |
| F12 字幕时间轴越界 | end_time < begin_time | 容错：`asr_check.py` 检出并告警，人工复核 |

异常总则：任一环节失败先落中间结果以支持**断点续跑**；不得因末段失败丢弃前序分段；所有**异常**须写入交付说明，不允许掩盖**失败分支**。

## 九、🔴 关键检查点

🔴 CHECKPOINT-1｜转写前：确认音频文件存在且非空；本地文件路径含中文时先复制到 ASCII 临时路径，避免上传编码问题。

🔴 CHECKPOINT-2｜说话人分离：`--speakers` 取值需与真实会话人数一致，取值偏差会显著拉低分离准确率；不确定时不传该参数。

🔴 CHECKPOINT-3｜结果交付前：核对 JSON 中 `text` 与 `sentences` 是否一致、是否有明显截断；长音频分段结果的段间衔接需人工抽查；跑 `scripts/asr_check.py` 做结构自检。

🔴 CHECKPOINT-4｜敏感内容：音频涉及个人隐私、未公开经营信息时，转写结果按内部资料管理，按内部资料口径留存，不向无关第三方提供、不投放公网。

## 十、红线声明（固定拒绝口径）

1. **不转录违法用途内容**：拒绝为窃听、跟踪、非法取证等涉嫌违法场景提供转写服务。
2. **不处理无授权的隐私录音**：转写他人私密对话须有合法授权；无法确认来源合法性时不予处理。
3. **不编造转写结果**：不臆造句数、时长、说话人身份与识别率；无法识别的部分如实标注。
4. **不替代专业资质判断**：转写文本如需用于司法鉴定、医学诊断等场景，须由具备资质的机构复核，本技能不做结论性判断。
5. **不承诺识别准确率**：不承诺「100% 准确」或「一定识别正确」，准确率受音质、口音、专业词影响。
6. **不越权外发数据**：原始音频与转写文本按最小必要留存，不向无关第三方提供、不投放公网。

## 十一、依赖说明

- `requests`：HTTP 调用；缺失时先 `pip install requests`
- `DASHSCOPE_API_KEY`：阿里云百炼 API Key（环境变量或 `/root/.dashscope_config.json`）
- `ffmpeg`：非必需，用于音频归一化与长音频切段

## 十二、集成契约（供上层链路调用）

命令行契约（两个上游链路共同依赖，变更需同步）：

```bash
python3 <ali-asr路径>/transcribe.py <音频路径> [--out 结果.json] [--diarization] [--speakers N]
```

- 路径需同时满足：`skills/ali-asr/scripts/transcribe.py`、`skills/ali-asr/transcribe.py`、`ali-asr/transcribe.py`
- 输出 JSON 至少包含 `transcripts[].text` 或 `transcripts[].sentences[].text`，以及顶层 `text`

> 更多用法与示例见 `references/usage-and-examples.md`；交付打法与实战案例见 `references/case-library.md`。

## 十三、版本沿革（CHANGELOG）

- **v1.1.0（2026-10-04）**：按 TRACE 改造 SOP 增补——新增「引用依据与溯源」7 条权威依据（含个人信息保护法、数据安全法、网络安全法文号）、「红线声明」6 条、「能力边界与不适用范围」、「可交付物与输出规范」表、「触发条件与路由」表；「失败模式与降级路径」扩充为 12 场景并补齐全部失败/降级关键词；新增 `scripts/asr_check.py` 结果契约自检器与 `references/case-library.md` 案例集；frontmatter 版本进位、标签规范化。
- **v1.0.0（2026-09-12）**：首版。DashScope 非实时文件转写入口，统一 JSON 契约，供会议纪要与链接归档链路调用。

## 依赖安装

本技能脚本依赖第三方库，首次使用（或沙箱/换机重置）后请先安装：

```bash
python3 -m pip install -r requirements.txt
```
