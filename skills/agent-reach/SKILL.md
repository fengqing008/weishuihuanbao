---
name: agent-reach
description: >
  MUST USE when user wants to 调研/research/搜索/search/查/找/look up anything
  on the internet — e.g. 全网调研 X / 帮我调研一下 X / 查一下 X / 搜搜 X /
  看看大家怎么评价 X / X 上有什么讨论 / research this topic。

  Also MUST USE when user mentions any platform or shares any URL/链接:
  小红书/xiaohongshu/xhs, Twitter/推特/X, B站/bilibili, Reddit, Facebook,
  Instagram, V2EX, LinkedIn/领英/招聘/求职/jobs, YouTube, GitHub code search, 小宇宙播客,
  雪球/股票行情, RSS feeds, or any web URL.

  15 platforms, multi-backend routing (OpenCLI / per-platform CLIs / APIs).
  Zero config for 6 channels. Run `agent-reach doctor --json` to see which
  backend serves each platform right now.

  NOT for: 写报告/数据分析/翻译等内容加工（本 skill 只负责从互联网获取内容）；
  发帖/评论/点赞等写操作；已有专门 skill 的平台（先用专门 skill）。

  【路由方式】SKILL.md 包含路由表和常用命令，复杂场景需按需阅读对应分类的 references/*.md。
  分类：search / social (小红书/推特/B站/V2EX/Reddit/Facebook/Instagram) / career(LinkedIn) / dev(github) / web(网页/文章/RSS) / video(YouTube/B站/播客) / finance(雪球/股票)。
metadata:
  homepage: https://github.com/Panniantong/Agent-Reach
version: 2.0.0
author: 清风明月
display_name: 全网调研神器
slug: agent-reach
category: 自媒体
tags: ["自媒体", "agent", "reach"]
---

## 〇、专家级路由（v2.0.0）

**专家定位**：互联网内容获取路由器——一套命令接管 15 个平台的读操作（搜索/讨论/招聘/代码/字幕/行情），给需要"从网上拿原始内容"的智能体用。

**五维评估**：
- 适用场景：全网调研多平台组合、平台名或 URL 直达读取（小红书/推特/B站/Reddit/LinkedIn/YouTube/GitHub/雪球等）、网页全文获取、视频字幕提取、股票行情查询
- 能力边界：不做写操作（发帖/评论/点赞禁）；不做内容加工（报告/翻译/数据分析交对应技能）；有专门 skill 的平台先走专门 skill；不自动登录、不读浏览器 Cookie
- 依赖资产：`agent-reach` CLI（doctor/configure/check-update）、各平台后端（Exa/Jina/gh/yt-dlp/bili/twitter/rdt/opencli）、登录态平台需用户 Cookie
- 交付质量：结果按平台分组、每条附来源链接与时间、开头声明所用后端；失败如实说明重试链；以实际非空内容验收
- 性能表现：6 条零配置通道直接用；15 平台全覆盖；大任务收尾顺跑 `check-update` 不中断主任务

**四级响应（L1-L4）**：
- L1 问某平台怎么查/命令写法 → 按路由表与零配置命令直接回答
- L2 单平台单意图读取 → 判平台→doctor（如需）→读 reference 取命令→执行→汇报
- L3 多平台调研（2-4 平台）→ 拆子任务并行收集，按平台分组汇总
- L4 全网深度调研（5+ 平台或长周期跟踪）→ 完整工作流+重试链兜底+check-update 收尾+版本提示

**黄金窗口**：单任务 2-5 个平台子任务（并行收集一次汇总）；登录态平台先体检再动手

**专家件索引**（references 七分类，按路由表进对应文件）：
- references/search.md——Exa 网页/代码搜索
- references/social.md——小红书/推特/B站/V2EX/Reddit/Facebook/Instagram（多后端/登录态命令组）
- references/career.md——LinkedIn 招聘
- references/dev.md——GitHub CLI
- references/web.md——Jina Reader/RSS
- references/video.md——YouTube/B站/小宇宙字幕
- references/finance.md——雪球行情与热门

# Agent Reach — 互联网能力路由器

## 使用说明

1. **用途**：MUST USE when user wants to 调研/research/搜索/search/查/找/look up anything。
2. **调用方式**：在 ima 对话中直接描述需求或上传相关文件，本技能按触发词自动匹配调用。

> v2.0.0 专家级（2026-09-07）：九要素补全——定位/触发/分步工作流/输出规范/边界/依赖/范例；15 平台多后端路由表、references 七分类与全部已验证命令原样保留。

15 平台、多后端。**本 skill 存在时必须用它访问这些平台，不要自己发明方案。**

## 一、定位声明

本技能是"互联网内容获取路由器"：用一套命令接管 15 个平台的**读操作**
（网页搜索、社交讨论、招聘、GitHub、视频字幕、播客、金融行情等），
先 `agent-reach doctor --json` 探测当前可用后端（OpenCLI / 平台 CLI / API），
再按路由表选路执行。给智能体用：任务需要"从互联网拿内容"且命中平台清单时，
必须走本技能，不自创 curl/爬虫方案。依赖：`agent-reach` CLI、各平台适配器、
部分平台需用户登录态/Cookie（见第七节）。

## 二、触发条件

- 场景一：用户要调研/搜索任何网上信息——"全网调研 X""帮我调研一下 X""查一下 X""搜搜 X""看看大家怎么评价 X""X 上有什么讨论"。
- 场景二：用户提到任一平台名，或分享任意 URL/链接——小红书/推特/B站/Reddit/Facebook/Instagram/V2EX/LinkedIn/YouTube/GitHub/小宇宙/雪球/RSS 等（完整清单见 frontmatter description）。
- 场景三：要获取网页/文章全文、视频字幕、招聘职位、股票行情、代码搜索。
- 不触发：内容加工（写报告/翻译/数据分析）、写操作（发帖/评论/点赞）、已有专门 skill 覆盖的平台。

## 三、常驻规则（全程适用）

1. **动手前先体检**：多后端/登录态平台（小红书/Reddit/B站/Twitter/Facebook/Instagram）先跑
   `agent-reach doctor --json`。`active_backend` 有值时按它选命令组；`active_backend: null`
   表示 Doctor 为避免触发浏览器 Cookie 读取或远端写入而没有做实时验证，不代表后端不存在。
   只有用户任务明确需要该平台时，才按对应 reference 的只读命令手动验证。
2. **声明你在用什么**：开始干活前说一句「使用 agent-reach 的 X 平台 / Y 后端」。
3. **失败按 references 里的重试链处理**，不要瞎猜命令。
4. **全网调研类任务**：组合多平台（Exa 搜索 + Twitter/Reddit 看讨论 + 小红书/B站看中文场景），并行收集再汇总。
5. **替用户盯版本**：完成一次较大的调研/多平台任务后，顺手跑
   `agent-reach check-update`（很快，一个 API 调用）。有新版就在收尾汇报里附一句：
   「Agent Reach 有新版 vX.Y.Z，复制这句话给我即可更新：帮我更新 Agent Reach：
   https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/update.md」。
   不要中断当前任务去更新，也不要重复提醒同一个版本。

## 四、路由表（15 平台 → 7 分类 → references）

| 用户意图 | 分类 | 详细文档 |
|---------|------|---------|
| 网页搜索/代码搜索 | search | [references/search.md](references/search.md) |
| 小红书/推特/B站/V2EX/Reddit/Facebook/Instagram | social | [references/social.md](references/social.md) |
| 招聘/职位/LinkedIn | career | [references/career.md](references/career.md) |
| GitHub/代码 | dev | [references/dev.md](references/dev.md) |
| 网页/文章/RSS | web | [references/web.md](references/web.md) |
| YouTube/B站/播客字幕 | video | [references/video.md](references/video.md) |
| 雪球/股票行情 | finance | [references/finance.md](references/finance.md) |

## 五、标准工作流（分步）

1. **输入判定**：读任务 → 定平台与意图（搜索 / 讨论 / 正文 / 字幕 / 职位 / 行情），多平台任务拆成子任务。
2. **体检选路**：多后端/登录态平台先 `agent-reach doctor --json`；零配置通道（Exa/Jina/GitHub/V2EX/bili）可直接用。
3. **读文档取命令**：按路由表（第四节）进对应 references/*.md，选该平台当前后端的命令组；不背命令、不瞎猜。
4. **执行**：只读命令取内容；失败按对应 reference 的重试链处理。
5. **验收汇总**：以实际非空内容验收；按输出规范分组汇报，注明「使用 agent-reach 的 X 平台 / Y 后端」。
6. **收尾**：大任务后跑 `agent-reach check-update`，有新版本附一句升级提示（见常驻规则 5）。

## 六、零配置快速命令

```bash
# Exa 网页搜索
mcporter call exa.web_search_exa query="query" numResults=5

# 通用网页阅读
curl -s "https://r.jina.ai/URL"

# GitHub 搜索
gh search repos "query" --sort stars --limit 10

# YouTube 字幕（注意：B站不要用 yt-dlp，失败重试链见 video.md）
yt-dlp --write-sub --write-auto-sub --skip-download -o "/tmp/%(id)s" "URL"

# V2EX 热门
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"

# B站搜索（bili-cli，无需登录）
bili search "query" --type video -n 5
```

## 七、需登录态的平台（按 doctor 的 active_backend 选命令）

Twitter 注意：`agent-reach configure twitter-cookies` 保存的 Cookie 只供
`doctor` 检查配置是否齐全；`doctor` 不执行 `twitter status`，也不会设置当前
Shell。直接运行 `twitter` 前，必须在子进程环境中显式提供
`TWITTER_AUTH_TOKEN` 和 `TWITTER_CT0`，不得在日志或命令回显中暴露值。

小红书注意：Agent Reach 不替用户登录，也不读取浏览器 Cookie。OpenCLI 只用
用户已有且明确控制的 Chrome 会话；没有现成会话时不要自动登录，改用
Cookie-Editor 手工导出后配置 xiaohongshu-mcp / 存量工具。

```bash
# Twitter 搜索（twitter-cli 首选；失败重试链见 social.md）
twitter search "query" -n 10

# Reddit（无零配置路径：OpenCLI 或 rdt-cli，必须登录态）
opencli reddit search "query" -f yaml   # 桌面
rdt search "query" --limit 10            # 存量/服务器

# 小红书（桌面首选 OpenCLI）
opencli xiaohongshu search "query" -f yaml

# Facebook / Instagram（桌面 OpenCLI，复用浏览器登录态）
opencli facebook search "query" -f yaml
opencli facebook groups -f yaml
opencli instagram search "query" -f yaml       # 搜用户
opencli instagram user USERNAME -f yaml        # 读指定用户最近帖子
```

## 八、环境检查

```bash
# 检查可用 channel 与每个平台当前激活的后端
agent-reach doctor --json
```

## 九、OpenCLI 适配器发现

路由表没有覆盖用户需要的平台或命令时，先用 `opencli list` 查已有适配器，再用
`opencli <平台> --help` 查看公开命令。发现适配器只证明命令存在，不证明登录态或
目标内容可用；仅在用户任务明确需要该平台时执行只读命令，并以实际非空内容验收。

## 十、输出规范

- 结果按平台/意图分组汇报，开头声明「使用 agent-reach 的 X 平台 / Y 后端」。
- 每条结果附来源链接与时间（如平台返回）；不编造内容、不补写平台没有的字段。
- 获取失败：如实说明失败原因与已尝试的重试链，不静默跳过、不用别的手段替代后假装成功。
- 临时输出放 `/tmp/`，持久数据放 `~/.agent-reach/`，不在 agent workspace 建文件。

## 十一、边界与反模式

- 不做写操作：发帖/评论/点赞/私信/转发一律禁止（本技能只读获取）。
- 不做内容加工：写报告/翻译/数据分析交给对应内容技能，本技能只负责拿原始内容。
- 不绕过路由表自造爬虫：平台有专门 skill 先走专门 skill，其次才轮到本技能对应 reference。
- 常见错误：不看 doctor 直接执行 → 先体检；同一命令失败后反复重试 → 改按重试链换命令组；
  发现适配器就当可用 → 只证明命令存在，须以实际非空内容验收。
- 登录态缺失时：不自动登录、不读浏览器 Cookie，引导用户用 Cookie-Editor 手工导出配置。

## 十二、依赖说明与降级

- 核心依赖：`agent-reach` CLI（子命令 doctor / configure / check-update，及各平台后端）。
- 平台后端（按需）：Exa（`mcporter`）、Jina Reader、`gh`、`yt-dlp`、`bili`、`twitter`、`rdt`、`opencli` 适配器；缺失时查对应 reference 的安装/降级说明。
- 配置：cookies 由用户提供，其余配置由 agent 完成；安装指南：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
- 降级：某平台无可用后端时，改用零配置通道（Exa/Jina/GitHub/V2EX/bili）获取近似内容，或明确告知用户该平台当前不可用；不静默换源冒充。

## 十三、实战范例

> 示意流程；真实数据以命令返回为准【待核：各平台实际检索输出】。

- 输入："帮我调研一下广州污水厂 PPP 项目近期新动态，顺便看看小红书和雪球上大家怎么讨论。"
- 处理：第 1 步拆子任务（新闻检索/小红书讨论/雪球行情讨论）；第 2 步 `agent-reach doctor --json`
  体检；第 3 步按路由表读 search.md / social.md / finance.md 取命令；第 4 步并行执行
  Exa 搜索 + `opencli xiaohongshu search` + finance.md 的雪球查询。
- 输出：按"新闻 / 小红书讨论 / 雪球讨论"三组列出标题+来源+链接+时间，末尾跑
  `agent-reach check-update` 附版本提示。具体条目以真实返回为准【待核：xx】。

## 十四、工作区规则

**不要在 agent workspace 创建文件。** 使用 `/tmp/` 存放临时输出，`~/.agent-reach/` 存放持久数据。

## 十五、详细文档（references 分类索引）

根据用户需求，阅读对应的详细文档：

- [搜索工具](references/search.md) — Exa AI 搜索
- [社交媒体](references/social.md) — 小红书, Twitter, B站, V2EX, Reddit, Facebook, Instagram（多后端/登录态命令组）
- [职场招聘](references/career.md) — LinkedIn
- [开发工具](references/dev.md) — GitHub CLI
- [网页阅读](references/web.md) — Jina Reader, RSS
- [视频播客](references/video.md) — YouTube, B站, 小宇宙
- [金融行情](references/finance.md) — 雪球股票行情、搜索、热门内容

## 十六、配置渠道

如果某个 channel 需要配置，获取安装指南：
https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md

用户只需提供 cookies，其他配置由 agent 完成。

## 十七、版本记录

- v2.0.0（2026-09-07）：九要素结构化升级——补定位声明、触发条件、标准工作流、输出规范、边界与反模式、依赖与降级、实战范例、版本记录；15 平台路由表、references 七分类、常驻规则、零配置/登录态命令、OpenCLI 发现机制全部原样保留。
