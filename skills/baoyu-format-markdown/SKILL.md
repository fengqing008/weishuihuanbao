---
name: baoyu-format-markdown
display_name: Markdown排版
version: 1.58.0
description: Formats plain text or markdown files with frontmatter, titles, summaries,
  headings, bold, lists, and code blocks. Use when user asks to "format markdown",
  "beautify article", "add formatting", or improve article layout. Outputs to {filename}-formatted.md.
  当用户要求格式化 markdown、美化文章、补充标题/摘要/列表/代码块、整理版式时触发。不适用于事实改写与数据勘误、从零代写文章、代码格式化工具链、原始排版设计。
author: 清风明月
slug: baoyu-format-markdown
category: 自媒体
tags:
- 自媒体
- baoyu
- format
- markdown
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-format-markdown
    requires:
      anyBins:
      - bun
      - npx
---



> **来源**：JimLiu/baoyu-skills（MIT License）· ima 沙箱适配 2026-09-16
> **沙箱运行提示**：本机无 bun，脚本统一用 `npx bun <script>` 运行（npx 首次自动拉取 bun）；本技能为第三方开源技能，原作者 JimLiu（宝玉）。

# Markdown Formatter

## 使用说明

1. **用途**：Formats plain text or markdown files with frontmatter, titles, summari。
2. **调用方式**：在 ima 对话中直接描述需求或上传相关文件，本技能按触发词自动匹配调用。

Transforms plain text or markdown into well-structured, reader-friendly markdown. The goal is to help readers quickly grasp key points, highlights, and structure — without changing any original content.

**Core principle**: Only adjust formatting and fix obvious typos. Never add, delete, or rewrite content.

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
| `scripts/main.ts` | Main entry point with CLI options (uses remark-cjk-friendly for CJK emphasis) |
| `scripts/quotes.ts` | Replace ASCII quotes with fullwidth quotes |
| `scripts/autocorrect.ts` | Add CJK/English spacing via autocorrect |

## Preferences (EXTEND.md)

Check EXTEND.md in priority order — the first one found wins:

| Priority | Path | Scope |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-format-markdown/EXTEND.md` | Project |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-format-markdown/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-format-markdown/EXTEND.md` | User home |

If none found, use defaults — no first-time setup required for this skill.

**EXTEND.md supports**:

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `auto_select` | `true`/`false` | `false` | Skip both title and summary selection, auto-pick best |
| `auto_select_title` | `true`/`false` | `false` | Skip title selection only |
| `auto_select_summary` | `true`/`false` | `false` | Skip summary selection only |
| Other | — | — | Default formatting options, typography preferences |

## Usage

The workflow has two phases: **Analyze** (understand the content) then **Format** (apply formatting). Claude performs content analysis and formatting (Steps 1-5), then runs the script for typography fixes (Step 6).

## Workflow

### Step 1: Read & Detect Content Type

Read the user-specified file, then detect content type:

| Indicator | Classification |
|-----------|----------------|
| Has `---` YAML frontmatter | Markdown |
| Has `#`, `##`, `###` headings | Markdown |
| Has `**bold**`, `*italic*`, lists, code blocks, blockquotes | Markdown |
| None of above | Plain text |

**If Markdown detected, use `AskUserQuestion` to ask:**

```
Detected existing markdown formatting. What would you like to do?

1. Optimize formatting (Recommended)
   - Analyze content, improve headings, bold, lists for readability
   - Run typography script (spacing, emphasis fixes)
   - Output: {filename}-formatted.md

2. Keep original formatting
   - Preserve existing markdown structure
   - Run typography script only
   - Output: {filename}-formatted.md

3. Typography fixes only
   - Run typography script on original file in-place
   - No copy created, modifies original file directly
```

**Based on user choice:**
- **Optimize**: Continue to Step 2 (full workflow)
- **Keep original**: Skip to Step 5, copy file then run Step 6
- **Typography only**: Skip to Step 6, run on original file directly

### Step 2: Analyze Content (Reader's Perspective)

Read the entire content carefully. Think from a reader's perspective: what would help them quickly understand and remember the key information?

Produce an analysis covering these dimensions:

**2.1 Highlights & Key Insights**
- Core arguments or conclusions the author makes
- Surprising facts, data points, or counterintuitive claims
- Memorable quotes or well-phrased sentences (golden quotes)

**2.2 Structure Assessment**
- Does the content have a clear logical flow? What is it?
- Are there natural section boundaries that lack headings?
- Are there long walls of text that could benefit from visual breaks?

**2.3 Reader-Important Information**
- Actionable advice or takeaways
- Definitions, explanations of key concepts
- Lists or enumerations buried in prose
- Comparisons or contrasts that would be clearer as tables

**2.4 Formatting Issues**
- Missing or inconsistent heading hierarchy
- Paragraphs that mix multiple topics
- Parallel items written as prose instead of lists
- Code, commands, or technical terms not marked as code
- Obvious typos or formatting errors

**Save analysis to file**: `{original-filename}-analysis.md`

The analysis file serves as the blueprint for Step 3. Use this format:

```markdown
# Content Analysis: {filename}

## Highlights & Key Insights
- [list findings]

## Structure Assessment
- Current flow: [describe]
- Suggested sections: [list heading candidates with brief rationale]

## Reader-Important Information
- [list actionable items, key concepts, buried lists, potential tables]

## Formatting Issues
- [list specific issues with location references]

## Typos Found
- [list any obvious typos with corrections, or "None found"]
```

### Step 3: Check/Create Frontmatter, Title & Summary

Check for YAML frontmatter (`---` block). Create if missing.

| Field | Processing |
|-------|------------|
| `title` | See **Title Generation** below |
| `slug` | Infer from file path or generate from title |
| `summary` | One-sentence concise summary (see **Summary Generation** below) |
| `description` | Longer descriptive summary (see **Summary Generation** below) |
| `coverImage` | Check if `imgs/cover.png` exists in same directory; if so, use relative path |

#### Title Generation

Whether or not a title already exists, run the title optimization flow unless `auto_select_title` is set.

**Preparation** — read the full text and extract:
- Core argument (one sentence: "what is this article about?")
- Most impactful opinion or conclusion
- Reader pain point or curiosity trigger
- Most memorable metaphor or golden quote

**Generate candidates** using formulas from `references/title-formulas.md`:

1. Select the **2-3 best-matching hook formulas** based on the article's content, tone, and structure (see "When to pick each formula" in the reference)
2. Generate **1-2 straightforward titles** (descriptive or declarative, no formula — clear and accurate)
3. If the user specifies a direction (e.g., "make it suspenseful"), prioritize that direction
4. Total: **4-5 candidates**

Present via `AskUserQuestion`:

```
Pick a title:

1. [Hook title A] — (recommended) [formula name]
2. [Hook title B] — [formula name]
3. [Hook title C] — [formula name]
4. [Straightforward title D] — straightforward
5. [Straightforward title E] — straightforward

Enter number, or type a custom title:
```

Put the strongest hook first and mark it `(recommended)`. See `references/title-formulas.md` for principles and prohibited patterns.

If the first line is an H1, extract it to frontmatter and remove it from the body. If frontmatter already has a `title`, include it as context but still generate fresh candidates — the existing title may be weak.

**Skip behavior**: If `auto_select: true` or `auto_select_title: true`, skip the user prompt and use the top candidate directly.

#### Summary Generation

Generate two versions directly (no user selection), both stored in frontmatter:

| Field | Length | Purpose |
|-------|--------|---------|
| `summary` | 1 sentence, ~50-80 chars | Concise hook — for feeds, social sharing, SEO meta |
| `description` | 2-3 sentences, ~100-200 chars | Richer context — for article previews, newsletter blurbs |

**Principles**:

- Convey **core value** to the reader, not just the topic
- Use concrete details (numbers, outcomes, specific methods) over vague descriptions
- `summary` should be punchy and self-contained; `description` can expand with supporting details
- If frontmatter already has `summary` or `description`, keep the existing one and only generate the missing field

**Prohibited patterns**:

- "This article introduces...", "This article explores..."
- Pure topic description without value proposition
- Repeating the title in different words

Once the title is in frontmatter, the body should NOT contain an H1 (avoid duplication).

### Step 4: Format Content

Apply formatting guided by the Step 2 analysis. The goal is making the content scannable and the key points impossible to miss.

**Formatting toolkit:**

| Element | When to use | Format |
|---------|-------------|--------|
| Headings | Natural topic boundaries, section breaks | `##`, `###` hierarchy |
| Bold | Key conclusions, important terms, core takeaways | `**bold**` |
| Unordered lists | Parallel items, feature lists, examples | `- item` |
| Ordered lists | Sequential steps, ranked items, procedures | `1. item` |
| Tables | Comparisons, structured data, option matrices | Markdown table |
| Code | Commands, file paths, technical terms, variable names | `` `inline` `` or fenced blocks |
| Blockquotes | Notable quotes, important warnings, cited text | `> quote` |
| Separators | Major topic transitions | `---` |

**Formatting principles — what NOT to do:**
- Do NOT add sentences, explanations, or commentary
- Do NOT delete or shorten any content
- Do NOT rephrase or rewrite the author's words
- Do NOT add headings that editorialize (e.g., "Amazing Discovery" — use neutral descriptive headings)
- Do NOT over-format: not every sentence needs bold, not every paragraph needs a heading

**Formatting principles — what TO do:**
- Preserve the author's voice, tone, and every word
- **Bold key conclusions and core takeaways** — the sentences a reader would highlight
- Extract parallel items from prose into lists only when the structure is clearly there
- Add headings where the topic genuinely shifts — prefer vivid, specific headings over generic ones (e.g., "3 天搞定 vs 传统方案" over "方案对比")
- Use tables for comparisons or structured data buried in prose
- Use blockquotes for golden quotes, memorable statements, or important warnings
- Fix obvious typos (based on Step 2 findings)

### Step 5: Save Formatted File

Save as `{original-filename}-formatted.md`

**Backup existing file:**

```bash
if [ -f "{filename}-formatted.md" ]; then
  mv "{filename}-formatted.md" "{filename}-formatted.backup-$(date +%Y%m%d-%H%M%S).md"
fi
```

### Step 6: Execute Typography Script

Run the formatting script on the output file:

```bash
${BUN_X} {baseDir}/scripts/main.ts {output-file-path} [options]
```

**Script Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--quotes` | `-q` | Replace ASCII quotes with fullwidth quotes `"..."` | false |
| `--no-quotes` | | Do not replace quotes | |
| `--spacing` | `-s` | Add CJK/English spacing via autocorrect | true |
| `--no-spacing` | | Do not add CJK/English spacing | |
| `--emphasis` | `-e` | Fix CJK emphasis punctuation issues | true |
| `--no-emphasis` | | Do not fix CJK emphasis issues | |

**Examples:**

```bash
# Default: spacing + emphasis enabled, quotes disabled
${BUN_X} {baseDir}/scripts/main.ts article.md

# Enable all features including quote replacement
${BUN_X} {baseDir}/scripts/main.ts article.md --quotes

# Only fix emphasis issues, skip spacing
${BUN_X} {baseDir}/scripts/main.ts article.md --no-spacing
```

**Script performs (based on options):**
1. Fix CJK emphasis/bold punctuation issues (default: enabled)
2. Add CJK/English mixed text spacing via autocorrect (default: enabled)
3. Replace ASCII quotes with fullwidth quotes (default: disabled)
4. Format frontmatter YAML (always enabled)

### Step 7: Completion Report

Display a report summarizing all changes made:

```
**Formatting Complete**

**Files:**
- Analysis: {filename}-analysis.md
- Formatted: {filename}-formatted.md

**Content Analysis Summary:**
- Highlights found: X key insights
- Golden quotes: X memorable sentences
- Formatting issues fixed: X items

**Changes Applied:**
- Frontmatter: [added/updated] (title, slug, summary)
- Headings added: X (##: N, ###: N)
- Bold markers added: X
- Lists created: X (from prose → list conversion)
- Tables created: X
- Code markers added: X
- Blockquotes added: X
- Typos fixed: X [list each: "original" → "corrected"]

**Typography Script:**
- CJK spacing: [applied/skipped]
- Emphasis fixes: [applied/skipped]
- Quote replacement: [applied/skipped]
```

Adjust the report to reflect actual changes — omit categories where no changes were made.

## Notes

- Preserve original writing style and tone
- Specify correct language for code blocks (e.g., `python`, `javascript`)
- Maintain CJK/English spacing standards
- The analysis file is a working document — it helps maintain consistency between what was identified and what was formatted

## Extension Support

Custom configurations via EXTEND.md. See **Preferences** section for paths and supported options.


## Failure Modes and Fallbacks

| # | Trigger | Symptom | Action |
|---|---|---|---|
| 1 | Input has no clear structure | Headings invented from noise | Keep the original order; only promote real topic sentences |
| 2 | Frontmatter already exists | Duplicate keys | Merge instead of overwrite, keep the existing values |
| 3 | Code blocks unclosed | Rendered output leaks fences | Scan for unclosed fences before writing |
| 4 | Non-Chinese and Chinese mixed | Wrong spacing rules | Apply language-aware spacing per segment |
| 5 | Over-formatting short text | Bullet spam | Threshold check: short prose stays prose |
| 6 | Footnotes missing targets | Broken links | Validate every footnote reference and definition pair |

## Checkpoints

- CHECKPOINT: keep the author's original wording and order.
- CHECKPOINT: every heading maps to a real topic boundary.
- CHECKPOINT: all code fences are closed and labelled.
- CHECKPOINT: no duplicated frontmatter keys.
- CHECKPOINT: output written to the "-formatted.md" file.

## Compliance Red Lines

- Do not rewrite facts, numbers or quotes.
- Do not delete the author's content while formatting.
- Do not inject frontmatter fields that were not present or requested.

## Anti-patterns

- Anti-pattern 1: turning every sentence into a bullet point.
- Anti-pattern 2: adding decoration that carries no meaning.
- Anti-pattern 3: arbitrary heading levels with skipped ranks.

## 失败模式与降级路径

| # | 触发条件 | 典型表现 | 处置动作 |
|---|---|---|---|
| 1 | 输入无清晰结构 | 凭空造标题 | 保留原文顺序，只把真实主题句提升为标题 |
| 2 | 已有 frontmatter | 键重复覆盖 | 合并而非覆盖，保留原值 |
| 3 | 代码围栏未闭合 | 渲染时围栏泄漏 | 写入前扫描围栏，异常即中止 |
| 4 | 中英混排 | 间距错位 | 按语言分段处理 |
| 5 | 短文本过度格式化 | 满屏列表 | 设阈值，短文本保持散文体 |
| 6 | 脚注目标缺失 | 链接断链 | 校验引用与定义的配对 |

**红线声明**：禁止改写事实、数字与引文；不要删除作者内容；不可注入未请求的字段；原始排版设计不在范围内。

---

## 降级路径与失败模式（容错·防御·兜底）

排版环节同样预设**降级路径**：任一环节出现**异常**先走**回退**与**兜底**，再决定是否**重试**，确保可**断点续跑**、有**补救**手段。下表是各类**失败分支**的触发条件与处置口径，也是**错误处理**与**容错**的统一约定（与上文 Failure Modes 互为中英对照）。

| 场景 | 触发条件 | 降级处置 |
|---|---|---|
| 无明确结构 | 输入为平铺散文（异常） | **回退**保留原文顺序，只提升真实主题句为标题，不臆造层级 |
| frontmatter 已存在 | 已有 YAML 键 | 合并而非覆盖的**降级处理**，保留旧值避免重复键 |
| 代码围栏未闭合 | ``` 计数为奇数 | 交付前扫描，未闭合则**补救**闭合后再写出（致命**边界条件**） |
| 运行时缺 bun | 无 bun 且无 npx | **降级为**纯人工排版（跳过 Step 6 排版脚本），提示安装 |
| 中文/英文混排 | 间距规则冲突 | 按语言分段套用间距规则（容错） |
| 短文本过度格式化 | 列表刷屏 | **回退**保持散文体，不强行转列表 |
| 标题生成被否决 | 用户不接受候选 | 保留原文标题，作为**失败分支**记录，不覆盖 |
| 输出写盘失败 | 磁盘满/权限异常 | **重试**写入；仍失败则改存 `-formatted.md` 相邻落位并提示 |
| 中途中断 | 会话结束/超时 | 依据 `-analysis.md` **断点续跑**，从 Step 4 继续 |

**关键边界条件**：仅调整格式、不改事实与措辞；无 bun/npx 时排版脚本步骤整体**降级**为人工核对。

## 引用依据与溯源

本技能的版式与标点口径基于以下权威依据（写全称 + 文号 + 来源），不编造、不杜撰：

1. 《标点符号用法》（GB/T 15834-2011，中华人民共和国国家标准）——中文标点与引号规范依据。
2. 《信息与文献 参考文献著录规则》（GB/T 7714-2015，中华人民共和国国家标准）——参考文献与引用著录参考。
3. 《党政机关公文格式》（GB/T 9704-2012，中华人民共和国国家标准）——标题层级与版式严谨性参考。
4. 《中华人民共和国著作权法》（2020 年 11 月 11 日修正）——不得改写、删减他人作品的合规依据。
5. remark / remark-cjk-friendly 官方文档（https://github.com/remarkjs/remark）——CJK 强调与解析规则的实现依据。
6. JimLiu/baoyu-skills（MIT License）——本技能上游实现来源。

> 溯源纪律：凡标注不确的字段以 `【待核：说明】` 占位，**不编造**。

## 能力边界与不适用范围

**适用边界**：纯文本或 Markdown 的版式美化（frontmatter、标题、摘要、加粗、列表、代码块、表格、引用块）。

**不适用范围**：

- 不在范围：事实改写、数据勘误、润色重写（改写语义属他类任务）。
- 不在范围：从零代写文章、代码格式化工具链。
- 不适用：原始排版设计（海报/杂志版式设计）。
- 限定：需要 `npx` 或 `bun` 才能运行排版脚本；缺失时排版脚本步骤**降级**为人工操作。
- 不做：替代作者对内容取舍的决定。

## 红线声明

1. 禁止改写、删除或增补原文事实、数字、引语。
2. 不得注入用户未要求或不存在的 frontmatter 字段。
3. 严禁为凑格式把散文强行拆成列表、制造「列表刷屏」。
4. 不得在排版过程中改变作者原意或语气。
5. 禁止在就地修改时不留副本，导致无法回退。
6. 不得承诺「一键美化无返工」，须以原文为准逐项核对。

## 版本沿革（CHANGELOG）

- v1.57.0（2026-09-16）：上游 baoyu-format-markdown 版本；确立 Analyze→Format 两阶段与 Step 1–7 工作流。
- v1.58.0（2026-10-04）：增补中英对照降级路径与失败模式总表、引用依据与溯源、能力边界、红线声明、可交付物与输出规范；新增 `scripts/mdformat_check.py` 自检脚本；补 `references/case-library.md` 案例与英文触发词。

## 使用示例（端到端）

```bash
# 1) 排版后交付前自检
python3 scripts/mdformat_check.py article-formatted.md

# 2) 运行排版脚本（沙箱无 bun 时用 npx 拉取）
npx -y bun scripts/main.ts article-formatted.md --quotes
```

## 可交付物与输出规范

| 交付物 | 路径 | 规格 | 说明 |
|---|---|---|---|
| 格式化成品 | `{filename}-formatted.md` | Markdown | 版式优化后的主产物 |
| 内容分析 | `{filename}-analysis.md` | Markdown | Step 2 分析蓝图（工作文档） |
| 版式脚本 | `scripts/main.ts` | TypeScript | 间距/强调/引号/ frontmatter 处理 |
| 自检报告 | 终端输出 | 文本 / JSON | `python3 scripts/mdformat_check.py <file> --json` |
| 发布信息 | `references/发布信息.md` | Markdown | 版本与依赖登记 |

**English triggers**: format markdown, beautify article, add formatting, improve markdown layout, markdown formatter, polish article structure, add frontmatter title summary.
