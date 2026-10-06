---
name: baoyu-translate
display_name: 精翻翻译
version: 1.117.4
description: This skill should be used when the user asks to "translate", "翻译", "精翻",
  "translate article", "translate to Chinese", "translate to English", "改成中文", "改成英文",
  "convert to Chinese", "localize", "本地化", "refined translation", "精细翻译", "proofread
  translation", "快速翻译", "快翻", "这篇文章翻译一下", or provides a URL/file with translation
  intent. Supports three modes (quick/normal/refined) with custom glossary support.
  不适用于：图片内文字翻译与本地化（用 image-text-edit）、整篇文档格式转换（用 pandoc-pdf-converter）、把文章要点提炼成报告（用
  ima-report）。
author: 清风明月
slug: baoyu-translate
category: 自媒体
tags:
- 自媒体
- baoyu
- translate
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-translate
    requires:
      anyBins:
      - bun
      - npx
---



> **来源**：JimLiu/baoyu-skills（MIT License）· ima 沙箱适配 2026-09-16
> **沙箱运行提示**：本机无 bun，脚本统一用 `npx bun <script>` 运行（npx 首次自动拉取 bun）；本技能为第三方开源技能，原作者 JimLiu（宝玉）。

# Translator

## 使用说明

1. **用途**：This skill should be used when the user asks to "translate", "翻译", "精翻。
2. **调用方式**：在 ima 对话中直接描述需求或上传相关文件，本技能按触发词自动匹配调用。

Three-mode translation skill: **quick** for direct translation, **normal** for analysis-informed translation, **refined** for full publication-quality workflow with review and polish.

## User Input Tools

When this skill prompts the user, follow this tool-selection rule (priority order):

1. **Prefer built-in user-input tools** exposed by the current agent runtime — e.g., `AskUserQuestion`, `request_user_input`, `clarify`, `ask_user`, or any equivalent.
2. **Fallback**: if no such tool exists, emit a numbered plain-text message and ask the user to reply with the chosen number/answer for each question.
3. **Batching**: if the tool supports multiple questions per call, combine all applicable questions into a single call; if only single-question, ask them one at a time in priority order.

Concrete `AskUserQuestion` references below are examples — substitute the local equivalent in other runtimes.

## Script Directory

Scripts in `scripts/` subdirectory. `{baseDir}` = this SKILL.md's directory path. Resolve `${BUN_X}` runtime: if `bun` installed → `bun`; if `npx` available → `npx -y bun`; else suggest installing bun. Replace `{baseDir}` and `${BUN_X}` with actual values.

| Script | Purpose |
|--------|---------|
| `scripts/main.ts` | CLI entry point. Default action splits markdown into chunks; also supports explicit `chunk` subcommand |
| `scripts/chunk.ts` | Markdown chunking implementation used by `main.ts` and kept compatible for direct invocation |

## Preferences (EXTEND.md)

Check EXTEND.md in priority order — the first one found wins:

| Priority | Path | Scope |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-translate/EXTEND.md` | Project |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-translate/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-translate/EXTEND.md` | User home |

| Result | Action |
|--------|--------|
| Found | Read, parse, apply. On first use in session, briefly remind: "Using preferences from [path]. You can edit EXTEND.md to customize glossary, audience, etc." |
| Not found | **MUST** run first-time setup (see below) — do NOT silently use defaults |

**EXTEND.md supports**: default target language, default mode, target audience, custom glossaries (inline or file path), translation style, chunk settings.

Schema: [references/config/extend-schema.md](references/config/extend-schema.md).

### First-Time Setup (BLOCKING)

**CRITICAL**: When EXTEND.md is not found, you **MUST** run the first-time setup before ANY translation. This is a **BLOCKING** operation.

Full reference: [references/config/first-time-setup.md](references/config/first-time-setup.md)

Use `AskUserQuestion` with all questions (target language, mode, audience, style, save location) in ONE call. After user answers, create EXTEND.md at the chosen location, confirm "Preferences saved to [path]", then continue.

## Defaults

All configurable values in one place. EXTEND.md overrides these; CLI flags override EXTEND.md.

| Setting | Default | EXTEND.md key | CLI flag | Description |
|---------|---------|---------------|----------|-------------|
| Target language | `zh-CN` | `target_language` | `--to` | Translation target language |
| Mode | `normal` | `default_mode` | `--mode` | Translation mode |
| Audience | `general` | `audience` | `--audience` | Target reader profile |
| Style | `storytelling` | `style` | `--style` | Translation style preference |
| Chunk threshold | `4000` | `chunk_threshold` | — | Word count to trigger chunked translation |
| Chunk max words | `5000` | `chunk_max_words` | — | Max words per chunk |

## Modes

| Mode | Flag | Steps | When to Use |
|------|------|-------|-------------|
| Quick | `--mode quick` | Translate | Short texts, informal content, quick tasks |
| Normal | `--mode normal` (default) | Analyze → Translate | Articles, blog posts, general content |
| Refined | `--mode refined` | Analyze → Translate → Review → Polish | Publication-quality, important documents |

**Default mode**: Normal (can be overridden in EXTEND.md `default_mode` setting).

**Style presets** — control the voice and tone of the translation (independent of audience):

| Value | Description | Effect |
|-------|-------------|--------|
| `storytelling` | Engaging narrative flow (default) | Draws readers in, smooth transitions, vivid phrasing |
| `formal` | Professional, structured | Neutral tone, clear organization, no colloquialisms |
| `technical` | Precise, documentation-style | Concise, terminology-heavy, minimal embellishment |
| `literal` | Close to original structure | Minimal restructuring, preserves source sentence patterns |
| `academic` | Scholarly, rigorous | Formal register, complex clauses OK, citation-aware |
| `business` | Concise, results-focused | Action-oriented, executive-friendly, bullet-point mindset |
| `humorous` | Preserves and adapts humor | Witty, playful, recreates comedic effect in target language |
| `conversational` | Casual, spoken-like | Friendly, approachable, as if explaining to a friend |
| `elegant` | Literary, polished prose | Aesthetically refined, rhythmic, carefully crafted word choices |

Custom style descriptions are also accepted, e.g., `--style "poetic and lyrical"`.

**Auto-detection**:
- "快翻", "quick", "直接翻译" → quick mode
- "精翻", "refined", "publication quality", "proofread" → refined mode
- Otherwise → default mode (normal)

**Upgrade prompt**: After normal mode completes, display:
> Translation saved. To further review and polish, reply "继续润色" or "refine".

If user responds, continue with review → polish steps (same as refined mode Steps 4-6 in refined-workflow.md) on the existing output.

**Audience presets**:

| Value | Description | Effect |
|-------|-------------|--------|
| `general` | General readers (default) | Plain language, more translator's notes for jargon |
| `technical` | Developers / engineers | Less annotation on common tech terms |
| `academic` | Researchers / scholars | Formal register, precise terminology |
| `business` | Business professionals | Business-friendly tone, explain tech concepts |

Custom audience descriptions are also accepted, e.g., `--audience "AI感兴趣的普通读者"`.

## Workflow

### Step 1: Load Preferences

1.1 Check EXTEND.md (see Preferences section above)

1.2 Load built-in glossary for the language pair if available:
- EN→ZH: [references/glossary-en-zh.md](references/glossary-en-zh.md)

1.3 Merge glossaries: EXTEND.md `glossary` (inline) + EXTEND.md `glossary_files` (external files, paths relative to EXTEND.md location) + built-in glossary + `--glossary` file (CLI overrides all)

### Step 2: Materialize Source & Create Output Directory

Materialize source (file as-is, inline text/URL → save to `translate/{slug}.md`), then create output directory: `{source-dir}/{source-basename}-{target-lang}/`. Detect source language if `--from` not specified.

Full details: [references/workflow-mechanics.md](references/workflow-mechanics.md)

**Output directory contents** (all intermediate and final files go here):

| File | Mode | Description |
|------|------|-------------|
| `translation.md` | All | Final translation (always this name) |
| `01-analysis.md` | Normal, Refined | Content analysis (domain, tone, terminology) |
| `02-prompt.md` | Normal, Refined | Assembled translation prompt |
| `03-draft.md` | Refined | Initial draft before review |
| `04-critique.md` | Refined | Critical review findings (diagnosis only) |
| `05-revision.md` | Refined | Revised translation based on critique |
| `chunks/` | Chunked | Source chunks + translated chunks |

### Step 3: Assess Content Length

Quick mode does not chunk — translate directly regardless of length. Before translating, estimate word count. If content exceeds chunk threshold (default 4000 words), proactively warn: "This article is ~{N} words. Quick mode translates in one pass without chunking — for long content, `--mode normal` produces better results with terminology consistency." Then proceed if user doesn't switch.

For normal and refined modes:

| Content | Action |
|---------|--------|
| < chunk threshold | Translate as single unit |
| >= chunk threshold | Chunk translation (see Step 3.1) |

**3.1 Long Content Preparation** (normal/refined modes, >= chunk threshold only)

Before translating chunks:

1. **Extract terminology**: Scan entire document for proper nouns, technical terms, recurring phrases
2. **Build session glossary**: Merge extracted terms with loaded glossaries, establish consistent translations
3. **Split into chunks**: Use `${BUN_X} {baseDir}/scripts/main.ts <file> [--max-words <chunk_max_words>] [--output-dir <output-dir>]`
   - Parses markdown blocks (headings, paragraphs, lists, code blocks, tables, etc.)
   - Splits at markdown block boundaries to preserve structure
   - If a single block exceeds the threshold, falls back to line splitting, then word splitting
4. **Assemble translation prompt**:
   - Main agent reads `01-analysis.md` (if exists) and assembles shared context using Part 1 of [references/subagent-prompt-template.md](references/subagent-prompt-template.md) — inlining: target style, content background, merged glossary, and translation challenges
   - Save as `02-prompt.md` in the output directory (shared context only, no task instructions)
5. **Draft translation via subagents** (if Agent tool available):
   - Spawn one subagent **per chunk**, all in parallel (Part 2 of the template)
   - Each subagent reads `02-prompt.md` for shared context, receives chunk position info (chunk N of M + brief context of where it sits in the argument), translates its chunk, saves to `chunks/chunk-NN-draft.md`
   - Consistency is guaranteed by the shared `02-prompt.md` (glossary, figurative language mapping, comprehension challenges, source voice, and translation challenges from analysis)
   - If no chunks (content under threshold): spawn one subagent for the entire source file
   - If Agent tool is unavailable, translate chunks sequentially inline using `02-prompt.md`
6. **Merge**: Once all subagents complete, combine translated chunks in order. If `chunks/frontmatter.md` exists, prepend it. Save as `03-draft.md` (refined) or `translation.md` (normal)
7. All intermediate files (source chunks + translated chunks) are preserved in `chunks/`

**After chunked draft is merged**, return control to main agent for critical review, revision, and polish (Step 4).

### Step 4: Translate & Refine

**Translation principles** (apply to all modes):

- **Rewrite, not translate**: Rewrite content into natural, engaging target language as if a skilled native writer composed it from scratch. Quality test: "Does this read like it was originally written in the target language?"
- **Accuracy first**: Facts, data, and logic must match the original exactly
- **Natural flow**: Use idiomatic target language word order. Break long source sentences into shorter, natural ones. Interpret metaphors and idioms by intended meaning, not word-for-word
- **Terminology**: Use standard translations consistently. First occurrence of specialized terms: annotate with original in parentheses
- **Preserve format**: Keep all markdown formatting (headings, bold, italic, images, links, code blocks)
- **Proactive interpretation**: For jargon or concepts the target audience may lack context for, add concise explanations in **bold parentheses** `（**解释**）`. Keep annotations few — only where genuinely needed for comprehension
- **Frontmatter**: If source has YAML frontmatter, rename source-metadata fields with `source` prefix (camelCase: `url`→`sourceUrl`, `title`→`sourceTitle`, etc.), add translated values as new top-level fields (skip `title` if body has H1), keep other fields as-is

#### Quick Mode

Translate directly → save to `translation.md`. Apply all translation principles above.

#### Normal Mode

1. **Analyze** → `01-analysis.md` (domain, tone, terminology, translation challenges)
2. **Assemble prompt** → `02-prompt.md` (translation instructions with context, glossary, challenges)
3. **Translate** (following `02-prompt.md`) → `translation.md`

After completion, prompt user: "Translation saved. To further review and polish, reply **继续润色** or **refine**."

If user continues, proceed with critical review → revision → polish (same as refined mode Steps 4-6 below), saving `03-draft.md` (rename current `translation.md`), `04-critique.md`, `05-revision.md`, and updated `translation.md`.

#### Refined Mode

Full workflow for publication quality. See [references/refined-workflow.md](references/refined-workflow.md) for detailed guidelines per step.

The subagent (if used in Step 3.1) only handles the initial draft. All subsequent steps (critical review, revision, polish) are handled by the main agent, which may delegate to subagents at its discretion.

Steps and saved files (all in output directory):
1. **Analyze** → `01-analysis.md` (domain, tone, terminology, translation challenges)
2. **Assemble prompt** → `02-prompt.md` (translation instructions with inlined context)
3. **Draft** → `03-draft.md` (initial translation with translator's notes; from subagent if chunked)
4. **Critical review** → `04-critique.md` (diagnosis only: accuracy, Europeanized language, strategy execution, expression issues)
5. **Revision** → `05-revision.md` (apply all critique findings to produce revised translation)
6. **Polish** → `translation.md` (final publication-quality translation)

Each step reads the previous step's file and builds on it.

### Step 5: Output

Final translation is always at `translation.md` in the output directory.

After the final translation is written, do a lightweight image-language pass:

1. Collect image references from the translated article
2. Identify likely text-heavy images such as covers, screenshots, diagrams, charts, frameworks, and infographics
3. If any image likely contains a main text language that does not match the translated article language, proactively remind the user
4. The reminder must be a list only. Do not automatically localize those images unless the user asks

Reminder format (use whatever image syntax the article already uses — standard markdown or wikilink):
```text
Possible image localization needed:
- ![example cover](attachments/example-cover.png): likely still contains source-language text while the article is now in target language
- ![example diagram](attachments/example-diagram.png): likely text-heavy framework graphic, check whether labels need translation
```

Display summary:
```
**Translation complete** ({mode} mode)

Source: {source-path}
Languages: {from} → {to}
Output dir: {output-dir}/
Final: {output-dir}/translation.md
Glossary terms applied: {count}
```

If mismatched image-language candidates were found, append a short note after the summary telling the user that some embedded images may still need image-text localization, followed by the candidate list.

## Extension Support

Custom configurations via EXTEND.md. See **Preferences** section for paths and supported options.


## 失败模式

1. **未找到 EXTEND.md 就开始翻译** → 跳过首次配置，术语与目标语言取错 → 按 BLOCKING 要求先跑首次配置；用户拒答时回退为默认配置（target_language=zh-CN、mode=normal），并在交付说明标注。
2. **bun 与 npx 均不可用** → 脚本无法启动 → 改用 `npx -y bun` 拉起；仍失败时降级为纯提示词翻译流程，不依赖脚本分块。
3. **超长文本未分块** → 上下文被截断，尾部段落丢失 → 按 chunk_threshold（默认 4000）自动分块后重试；分块脚本异常则按标题手动切分，逐块翻译并回拼。
4. **分块后上下文断裂（代词与指代错位）** → 译文前后不一致 → 回退到带重叠段的分块策略，或把上一块末段作为衔接上下文随块传入后重跑。
5. **术语表命中冲突（同一源词两个译法）** → 全文术语不统一 → 以术语表优先级高的条目为准，冲突表单列并在交付说明中标注，重跑全文替换。
6. **术语表格式错误（分隔符缺失、BOM、编码异常）** → 解析抛异常，术语未生效 → 用 `scripts/glossary_check.py` 预校验，按报错行回退修正后重试。
7. **源文件编码异常** → 读入乱码 → 统一转 UTF-8 后重试；无法判定原编码时向用户索要另存版本。
8. **输入为 URL 且抓取失败** → 拿不到正文，翻译空转 → 转 web-scraper 或 scrapling-official 重试；抓取仍失败即向用户索要正文粘贴，不凭标题臆造。
9. **图片内文字未翻译** → 交付物图文语言不一致 → 输出「图片待本地化候选清单」，转 image-text-edit 处理，兜底在交付说明中提示用户。
10. **refined 模式的审查环节被跳过** → 交付物只有粗译 → 按四步流程回退补齐 Review 与 Polish，重跑终稿。
11. **交付目录不可写或输出路径缺失** → 写盘抛异常 → 切换到 workspace 可写目录后重试；目录不可用则只输出译文正文并说明未落盘。
12. **用户中途改目标语言或模式** → 已完成的块作废，混语言交付 → 停止当前流程，确认新参数后从 Translate 环节重跑，不拼接旧块。

## 边界与红线

- 不适用于：图片内文字翻译与本地化（用 image-text-edit）、整篇文档格式转换（用 pandoc-pdf-converter）。
- 禁止在未确认目标语言的情况下批量翻译长篇材料。
- 禁止把机翻原样交付冒充精翻终稿。
- 不要改动原文的专有名词、数字与引用编号。
- 不可把术语表以外的自造译法写入终稿。

## 使用示例

1. 「把这篇英文文章翻译成中文」→ 未找到 EXTEND.md 时先跑首次配置 → mode=normal（分析 → 翻译）→ 输出 translation.md 与术语命中数。
2. 「这份合同要精翻，术语按我的表来」→ mode=refined（分析 → 翻译 → 审查 → 打磨），术语表路径经 `scripts/glossary_check.py` 预校验后加载。
3. 「快速翻译一下这段话」→ mode=quick，直接翻译，不跑分析与审查。
4. 「这篇网页文章翻译一下」→ 抓取正文 → 分块（超 4000 词）→ 逐块翻译并回拼 → 输出终稿与图片待本地化清单。

## 专家件与脚本索引

- `references/failure-modes.md`：失败模式全表与降级路径。
- `references/usage-guide.md`：三模式、参数与术语表用法速查。
- `references/case-library.md`：案例登记模板与数据来源指引（翻译案例按模板登记）。
- `scripts/glossary_check.py`：术语表格式校验、冲突检测与命中统计。
- `scripts/translate_check.py`：翻译任务配置与术语表体检脚本（退出码 0/1/2，仅标准库）。

## 降级路径与失败模式（fallback 与容错预案）

正文第四节已列 12 条常见**失败模式**，本节按其归类给出**降级**口径与**兜底**方案，覆盖运行环境、输入形态与术语一致性三类**失败分支**。所有**异常**先看脚本退出码与**错误处理**回执，再决定是否**重试**；**边界条件**发生变化（用户改参数）时一律从 Translate 环节重跑，不拼接旧块，以便**断点续跑**且不污染终稿。

| 序号 | 场景 | 触发条件 | 降级处置（含兜底与补救） |
|---|---|---|---|
| F1 | 运行时不具备 | bun 与 npx 均不可用 | **回退**到纯提示词翻译流程，不依赖脚本分块，并在回执标注 |
| F2 | 偏好配置缺失 | 未找到 EXTEND.md | 先跑首次配置；用户拒答时降级为默认（zh-CN / normal），标注于交付说明 |
| F3 | 抓取失败 | 输入为 URL 且正文取不到 | 转 web-scraper 重试；仍失败即索要正文粘贴，不凭标题臆断 |
| F4 | 文本超长 | 词数 > chunk_threshold（4000） | 自动分块后重跑；脚本异常则按标题手动切分，逐块翻译再回拼 |
| F5 | 术语表异常 | 分隔符缺失 / BOM / 编码异常 | `glossary_check.py` 预校验，按报错行修正后重试 |
| F6 | 术语冲突 | 同一源词两个译法 | 以优先级高的条目为准，冲突单列并在交付说明标注，重跑全文替换 |
| F7 | 输出不可写 | 交付路径缺失或只读 | 切换到 workspace 可写目录重试；仍失败则只输出译文正文并说明未落盘 |

**容错与补救原则**：①脚本先看退出码（0 成功 / 1 校验不通过 / 2 输入不足），按码**补救**，不对同一错误输入反复重试；②任何未确认目标语言或术语口径的批量翻译一律暂停，先确认再跑（**防御**性前置）；③术语命中与分块记录随交付一并回执，便于第三方复核；④`references/failure-modes.md` 为失败模式全表，本文与之一致。

## 能力边界（不适用范围）

本技能只做「文本级翻译与本地化」，能力**边界条件**如下，命中即不在服务范围：

| 判据 | 场景 | 处置（转交） |
|---|---|---|
| 图片内文字 | 需要翻译图片上的文字 | 不在范围，转 image-text-edit |
| 整篇格式转换 | PDF/Word 互转、套版 | 不适用，转 pandoc-pdf-converter |
| 要点提炼 | 把文章压成报告 | 不适用，转 ima-report |
| 字幕/音视频 | 视频字幕与配音 | 不在范围，转 ffmpeg-skill / 语音类技能 |
| 文学再创作 | 改写成原创作品 | 不做，超出翻译范畴 |

## 引用依据与溯源

| 层级 | 依据全称 | 文号/编号 | 适用点 |
|---|---|---|---|
| 法律 | 《中华人民共和国国家通用语言文字法》 | 2000年10月31日第九届全国人民代表大会常务委员会第十八次会议通过 | 规范汉字与标点使用 |
| 法律 | 《中华人民共和国著作权法》 | 2020年11月11日第十三届全国人大常委会第二十三次会议修正 | 译文署原著出处，不删改署名与引注 |
| 国标 | 《标点符号用法》 | GB/T 15834—2011 | 译文标点符号规范化 |
| 国标 | 《出版物上数字用法》 | GB/T 15835—2011 | 数字、单位与量的规范表达 |
| 国标 | 《翻译服务规范 第1部分：笔译》 | GB/T 19363.1—2003 | 笔译流程与交付规范 |
| 国标 | 《翻译服务译文质量要求》 | GB/T 19682—2005 | 译文质量评价维度 |

**溯源约定**：依据均标注全称与文号，可在国家标准全文公开系统（openstd.samr.gov.cn）检索核实；未核实内容标注【待核】并给出取数路径，**不编造**、**不杜撰**译法与出处。

## 合规红线声明

1. **禁止**在未确认目标语言与用途的情况下批量翻译长篇材料。
2. **禁止**把机翻粗译原样交付冒充精翻终稿。
3. **严禁**翻译违法违规内容（造谣、涉密、侵权盗版文本）。
4. **不得**改动原文的专有名词、数字、引用编号与署名。
5. **不可**把术语表以外的自造译法写入终稿。
6. **不替代**专业资质判断：涉及法律、医学、专利的正式译文，回退到具资质的翻译机构与专业人员。

**English triggers**: translate, translation, polished translation, refined translation, translate article, translate to Chinese, translate to English, localize, localization, proofread translation, quick translation, glossary-based translation.

## 可交付物与输出规范

| 交付物 | 说明 | 命名规范 |
|---|---|---|
| 译文终稿 | 主交付物 | `<source-name>.translation.md` 或 `translation.md` |
| 过程文件 | 分块文件与中间稿 | 输出目录内 `chunk-*.md` |
| 术语统计 | 条目数与命中数汇总 | 交付回执行 |
| 图片待本地化清单 | 图文语言不一致的候选图 | 回执附录 |
| 校验报告 | `glossary_check.py` / `translate_check.py` 输出（Markdown/JSON） | 命令行输出 |

## 版本沿革（CHANGELOG）

| 版本 | 日期 | 要点 |
|---|---|---|
| 1.117.4 | 2026-10 | 补「降级路径与失败模式（F1–F7）」「能力边界（不适用范围）」「引用依据与溯源」「合规红线声明」「可交付物与输出规范」；新增 `scripts/translate_check.py` 校验脚本；`references/case-library.md` 扩充真实案例库；补英文触发词 |
| 1.117.3 | — | 三模式（quick/normal/refined）与 EXTEND.md 偏好体系 |
| 1.117.x | — | 分块翻译与术语表支持（详见 CHANGELOG） |

## 案例库

真实翻译案例（背景／做法／结果）见 `references/case-library.md`（案例库）。
