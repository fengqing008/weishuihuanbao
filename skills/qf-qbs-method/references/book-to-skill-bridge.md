# 与内核 book-to-skill 的衔接契约

Step 3 由本技能调用内核完成"书 → 技能"的蒸馏。本文件约定调用参数、路径与产出接续。

## 一、内核位置与能力

| 项目 | 值 |
|:--|:--|
| 安装目录 | `skills/book-to-skill/` |
| 提取脚本 | `skills/book-to-skill/scripts/extract.py` |
| 生成技能输出根 | `skills/` |
| 版本 | v2.0.0（Steps 0-10，含安全扫描 Step 9.5） |
| 支持格式 | PDF/EPUB/DOCX/HTML/MD/纯文本/RTF/MOBI 等 18 种 |

## 二、调用步骤

### 1. 环境预检

```bash
python3 skills/book-to-skill/scripts/extract.py --check
```

缺解析包时按其提示安装，或走文本回退。

### 2. 文本提取

```bash
python3 skills/book-to-skill/scripts/extract.py <书文件路径> \
  --mode text --install-missing ask
```

参数：`--mode text`（叙述类，管理/效率非虚构）或 `--mode technical`（技术类，含代码表格公式）。
输出并打印 `Workdir ->` / `Text ->` / `Meta ->` 三个路径，**路径从输出取，不假设固定位置**。

### 3. 逐阶段推进内核 Steps

按内核 SKILL.md 的 Steps 0-10 执行：范围检查 → 输入验证 → 内容类型确认（1.5）→ 提取 → 成本预估（2.5）→ 章节映射（3）→ 命名（4）→ 建目录（5-6）→ 生成章节（7）→ 生成 glossary/patterns/cheatsheet（8）→ 生成主 SKILL.md → 安全扫描（9.5）。

## 三、四种运行模式（按需选用）

| 模式 | 触发 | 用途 |
|:--|:--|:--|
| 完整转换（默认） | 给出书文件且无特殊指令 | 产出完整技能 |
| 仅分析 | 说 "analyze" / "先看看" | 只出框架/原则/技术清单，不建技能 |
| 基于已有分析生成 | 已有分析笔记 | 跳过提取，直接生成 |
| 更新/合并 | 已有同名技能 | 新内容并入已有技能 |

QBS 法 Step 3 默认走"完整转换"；若用户在 Step 2 只有降级材料，则走"仅分析"。

## 四、产出接续

内核产出目录 `<skill_name>/`：`SKILL.md + chapters/ch*.md + glossary.md + patterns.md + cheatsheet.md`。

QBS 法的接续动作：

1. 记录生成的技能名与路径到台账 `3_skill`。
2. 用 `references/quality-checklist.md` 的"转换门"校验：主 SKILL.md ≤4,000 tokens、安全扫描通过、章节引用可达。
3. 通过后进入 Step 4（调用解题）；未通过则回到内核修正。

## 五、失败处置

| 情形 | 处置 |
|:--|:--|
| 内核不可用 | 中断 Step 3，保留 Step 0—2 产出，待内核恢复续跑 |
| 文本提取失败 | 换格式（PDF→EPUB/DOCX）或改走"仅分析"降级 |
| 安全扫描非零 | 按内核提示清理后重扫，不得跳过 |
| 章节划分被否 | 回到内核 Step 3 调整后重生成 |
