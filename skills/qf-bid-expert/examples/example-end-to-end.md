# 端到端样例：从招标片段到带目录的标书 Word

> 脱敏样例，仅示流程与产物形态。项目名、金额、单位均作虚构处理。

## 场景

拿到《某县乡镇污水处理厂委托运营服务项目招标文件》（虚构编号 XZ-2026-018）节选，要求 5 个工作日内交出技术标初稿。

## 第 1 步 废标红线扫描

```bash
python3 scripts/bid_red_line_checker.py --file 招标文件节选.md --out 废标核查表.md
```

输出：命中 12 处红线条款片段，并生成 18 项勾选清单。

## 第 2 步 评分办法拆解

```bash
python3 scripts/scoring_matrix.py --file 招标文件节选.md --out 得分点清单.xlsx
```

输出：抓取到 技术分 70、商务分 20、报价分 10；并生成技术标 7 项、商务标 6 项得分点准备清单（分值列标注"待核"）。

**结论**：报价仅 10 分，主力投 70 分技术方案与 20 分业绩资质。

## 第 3 步 生成标书骨架

```bash
python3 scripts/bid_book_builder.py --type technical --project "某县乡镇污水处理厂委托运营项目" --out 技术标骨架.md
```

输出：七板块 Markdown 骨架，含各级标题与【待填】占位。

## 第 4 步 按骨架填充内容

按 `references/02-technical-bid.md` 七板块与 `references/05-writing-templates.md` 话术填充；评分响应表按 `references/04-scoring-response.md` 五列范式编制，置于分册最前。

## 第 5 步 排版、挂大纲、出目录

```bash
python3 scripts/bid_docx_formatter.py -i 技术标.md -o 技术标.docx --type technical
python3 scripts/bid_docx_formatter.py --verify 技术标.docx
```

校验输出：

```
== 大纲与目录校验 ==
Heading 1 段落数: 7
Heading 2 段落数: 23
Heading 3 段落数: 41
含 TOC 域: True
updateFields 已设: True
结论: PASS（可一键生成目录）
```

交付：Word 打开后自动更新目录；导航窗格可见"一、项目理解与总体筹划 → 1.1 项目概况"完整层级。

## 第 6 步 交付前质检

按 `references/07-quality-checklist.md` 八项质检逐条过，重点核对主体信息一致性与业绩匹配。
