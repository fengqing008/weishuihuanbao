# 成书装配 SOP（book-assembly-sop）

> 从"一堆 Markdown"到"一本可打印的杂志"的七步法。核心难点在**两遍编译**与**前置页/正文页分计数**。

## 前置：稿件清单（manifest）

成书输入统一为 JSON 清单（样例见 `$S/assets/sample-manifest.json`）：

```json
{
  "book": { "title": "文集名", "subtitle": "副题", "editor": "编者", "issue": "2026·秋" },
  "articles": [
    { "order": 1, "column": "卷首语", "title": "篇名", "author": "作者", "body": "article1.md", "layout": "two-column-nobreak" },
    { "order": 2, "column": "文苑", "title": "篇名", "author": "作者", "body": "article2.md", "layout": "two-column" }
  ]
}
```

`order` 是**唯一排序源**；`layout` 取 `two-column`（双栏）/`one-column`（通栏）/`two-column-nobreak`（卷首语两栏、首几行不分栏）。

## 七步法

### ① 收稿定清单
把文章 md 汇总到工作目录，逐篇确认：栏目归属、作者、篇幅、是否卷首语。产出 manifest。

### ② 定开本栏式
选 16开或 A4；定每篇栏式。卷首语固定 `two-column-nobreak`，长文默认 `two-column`，短章可 `one-column`。

### ③ 套版式样式
`python3 $S/scripts/style_builder.py --size 16k --columns 2 --out theme.css`，或直接复用 `$S/assets/theme.css`。**不要手改 theme.css**，参数从脚本走。

### ④ 装配册页
前置页序列：**封面 → 扉页 → 版权页 → 目次页 → 正文**。
- 封面：书名艺术化、期号、编者
- 版权页：版本记录（书名、编者、成书年月、版次）——对标 GB/T 3179-2009 §6
- 目次页：上部 2/3 目次（栏目·篇名·作者·页码），下部 1/3 版本记录

### ⑤ 两遍编译（关键）
1. 第一遍：正文页正常生成，测出每篇**起始页码**（WeasyPrint 可用 `document.make_bookmark_tree()` 或对 HTML 加锚点后量页）。
2. 回填：把起始页码写入目次。
3. 第二遍：目次页码定稿，重新编译出终稿 PDF。
> 单遍编译会把目次页码写死或留空，是目次页码错位的根因。

### ⑥ 导出三形态
- **PDF**：`export_pdf.py`（WeasyPrint，CSS Paged Media 控页眉页脚页码）
- **HTML**：`book_builder.py` 输出的自包含单文件（微信可直接打开）
- **Word**：`book_builder.py --docx` 走 python-docx，标题挂 Heading 样式便于二次编辑

### ⑦ 排印质检
`layout_check.py` 过 G1–G7 门禁，输出 JSON 报告。任一 🔴 不通过即回退修正。

## 页码计数规则

```
封面/扉页/版权页/目次页 —— 不编入正文页码（用 @page cover/matter 命名页，无页码）
正文首页 —— counter-reset: page 1
卷首语页 —— 有页码、无页眉页脚
```

### ⑧ 图文混排落位（v1.1）

- 跨栏大图：`![题注](路径){wide}` → 通栏，用于开篇氛围图、章节图
- 栏内浮图：`![题注](路径)` → 栏内左浮、文字环绕，右/下留白 6mm/4mm
- 图题：居中，黑体 9pt，图下 2.6mm
- 首字下沉：卷首语默认启用（manifest 的 `"dropcap": false` 可关）；CSS 微调按 `em × 31pt` 换算位移
- 短篇（点滴类）用 `one-column` 通栏，避免短内容被迫跨栏断句
- 图片为自有或已授权素材；程序化装饰图仅作版式占位

### ⑨ 主题换肤与栏目扉页（v1.2）

- 换肤：`book_builder.py --theme <name>`（10 套，见 assets/themes.json），整册一次性套用同一主题
- 栏目扉页：manifest 设 `"column_pages": true`；每栏目首篇前插整页栏目名 + 可选导语（`columns_intro`）
- 栏目扉页用 `@page columnpage`（无页眉、编连续页码）；两遍编译时目次页码以正文册页脚同号为准
- 换肤后重跑对比度校验与排印质检 G1–G7

### ⑩ 自动配图落位（v1.4，对接 qf-lineart 引擎）

- 先跑 `illustration_draw.py` 出配图清单（每篇 2–3 张暖色线稿 + role 规划），整套图锁定同一 palette 与 style
- 再跑 `book_builder.py --auto-images auto_images.json`，按 role 自动插入：wide 跨栏、inline 栏内浮图、inline-end 靠后
- 图与正文同页时注意与首字下沉、引文块、栏目扉页的相互避让；页数增加属正常，复核每篇图数是否达标
- 图风格须统一（同一册内同笔触同配色），不混用钢笔与炭笔、不混用暖褐与纯黑
- 落位后目视复核：插图无压字、无溢出、无越界线条；深色底场景改铺暖纸底

## 交付清单

- [ ] book.pdf（16开精排）
- [ ] book.html（自包含，可预览）
- [ ] book.docx（可编辑，标题挂样式）
- [ ] qc.json（质检报告）
