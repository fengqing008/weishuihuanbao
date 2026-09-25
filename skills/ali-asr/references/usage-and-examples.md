# ali-asr · 用法与示例

## 一、适用场景

阿里云 DashScope 非实时文件转写入口，把音频/视频文件或公开 URL 转成文字。命中以下即用：会议/访谈录音整理、视频字幕生成、逐句时间戳、说话人分离、专有名词热词纠错。
被 `meeting-minutes-pipeline`（会议纪要）与 `link-report-archiver`（链接归档）作为转写后端调用。
不适用：纯本地离线转写（用 whisper-local）、实时语音对话（用 qwen-audio realtime）、图片文字识别（用 textin-xparse）。

## 二、典型用法

入口脚本 `scripts/transcribe.py`（兼容转发入口为技能根目录下的 `transcribe.py`）。

```bash
# 基础转写（本地文件或公开 URL）
python3 scripts/transcribe.py <音频文件或URL> --out 结果.json
# 说话人分离
python3 scripts/transcribe.py 会议.m4a --diarization --speakers 3 --out 结果.json
# 热词纠错（提升专有名词准确率）
python3 scripts/transcribe.py 录音.mp3 --vocab "某市:5,PPP:5,街办:4" --out 结果.json
```

长音频（>1 小时）按 10 分钟切段并行调用，再合并 `sentences`。脚本自包含，仅依赖 `requests` 与 `DASHSCOPE_API_KEY`。

## 三、参数说明

| 参数 | 含义 | 默认值 | 示例 |
|---|---|---|---|
| 位置参数 | 音频文件路径或公开 URL | 无 | `会议.m4a` |
| `--out` / `-o` | 结果 JSON 输出路径 | 无 | `--out 结果.json` |
| `--diarization` | 开启说话人分离 | 关闭 | `--diarization` |
| `--speakers N` | 说话人数量 | 无 | `--speakers 3` |
| `--lang` | 语言提示 | `zh` | `--lang en` |
| `--vocab` | 热词及权重，逗号分隔 | 无 | `--vocab "某市:5"` |
| `--model` | 指定转写模型 | `qwen-audio-3.0-asr-flash-filetrans` | `--model <name>` |

## 四、场景示例

**示例 1：股东会录音做纪要（走 meeting-minutes-pipeline）**：输入 `股东会录音.m4a`（3 人发言）→ `python3 scripts/transcribe.py 股东会录音.m4a --diarization --speakers 3 --vocab "某市:5,PPP:5" --out 结果.json` → 输出结构化 JSON（`text` / `transcripts` / `sentences`），上层链路据此生成公文格式 Word 纪要。

**示例 2：链接视频音轨转稿（走 link-report-archiver）**：输入从视频链接提取的音轨文件或公开 URL → `python3 scripts/transcribe.py <URL> --out 结果.json` → 输出逐句文本和顶层全文 `text`，供结构化报告使用。

**示例 3：低码率录音先归一化再转**：输入 16kHz/24kbps 类低码率音频（识别质量下降）→ 先 `ffmpeg` 归一化为 16kHz 单声道，再跑 `transcribe.py`；仍不可用改用 qwen-audio transcribe 通道交叉验证 → 输出归一化后的转写文本。

## 五、注意事项与常见问题

- 转写前确认音频存在且非空；本地路径含中文先复制到 ASCII 临时路径，避免上传编码问题。
- `--speakers` 要与真实会话人数一致，取值偏差会显著拉低分离准确率；不确定就不传。
- 交付前核对 JSON 中 `text` 与 `sentences` 是否一致、有无截断；长音频分段结果段间衔接需人工抽查。
- 敏感内容（隐私、未公开经营信息）按内部资料管理，不外传、不入公网。
- 缺 `DASHSCOPE_API_KEY` → 立即报错退出（退出码 1），可写入环境变量或 `/root/.dashscope_config.json`。
- 任务 FAILED/UNKNOWN/CANCELED 不重试同一任务，避免重复计费；返回 Arrearage（欠费）时全部请求不可用。
- 上层链路按候选路径查找脚本，需保证 `ali-asr/scripts/transcribe.py` 与 `ali-asr/transcribe.py` 同时存在。详见 SKILL.md 第五、八节。
