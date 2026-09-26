---
name: 读者排印坊
display_name: 读者排印坊
version: 1.9.0
description: 《读者》杂志版式排印与成书引擎。把任意文章、文集、合订稿按《读者》杂志版式（16开、正文宋体五号、卷首语等宽两栏、页眉"小图+篇名+栏目"奇偶页镜像、页码底端外侧、目次页2/3目次+1/3版本记录）排成杂志页或整本成书；支持图文混排（跨栏大图/栏内浮图）、卷首语首字下沉、引文提花与封面元素；联动 theme-factory 十套主题一键换肤（--theme）；配图走「AI 主通道 + 程序化线稿兜底」（对接 qf-lineart v2.1：AI 提示词通道出图，缺位由 32 类母题的线稿引擎补位），配图一律米白纸实底、不用透明底；目次页 HTML 单列、PDF 双栏。产出可打印 PDF、微信可读单文件 HTML、可编辑 Word 三种形态。覆盖版式规范速查、栏目结构与排序、封面/扉页/版权页/目次/正文册页装配、成书七步工作流、排印质检门禁。触发词：读者版式、读者杂志排版、读者排印、杂志排版、成书、出书、合订本、文集排版、卷首语排版、目次页、双栏排版、页眉页码、16开排版、书籍内页排版、reader layout、magazine typesetting、book assembly。
author: 清风明月
slug: qf-reader-typesetting
category: 教育
tags:
- 读者版式
- 杂志排版
- 成书出书
- 合订本文集
- 16开排版
---

## 〇、专家级路由（v1.4.2）

**专家定位**：《读者》杂志版式排印与整本成书引擎。一面负责把版式参数落成像素级样式（开本、字体字号、分栏、页眉页脚、页码、目次页），一面负责把散装文章装配成一本有封面、有目次、有栏目节奏的成书。
**五维评估**：
- 适用场景：①按《读者》版式排单篇样张 ②把文集/合订稿排成整本书（PDF/HTML/Word）③复刻杂志封面页、目次页、版权页 ④校核既有排版的字号、行距、页码、目次合规性 ⑤为公众号/内部资料做杂志风味排版
- 能力边界：本技能只做**版式与装配**，不生产文章内容；文章内容走"读者杂志知识库"技能取用。版式风格用于自有或已授权内容，不得冒用《读者》刊名、刊号、商标
- 输入形态：Markdown 文集、单篇 Markdown/txt、结构化 JSON 稿件清单、既有 docx 底稿
- 输出形态：A4/16开整册 PDF（WeasyPrint 精排）、单文件自包含 HTML（微信可读）、挂接样式的 Word
- 协作技能：读者杂志知识库（取文/取栏目/取文风）、contract-format（协议类排版）、docx-gw-format（公文排版）、theme-factory（配色主题）

**栏目序列基线**（按《读者》常规顺序）：卷首语 → 文苑 → 人物 → 社会 → 人生 → 生活 → 文明 → 悦读 → 点滴 → 互动。子栏目（文苑=书林一叶/原创精品；社会=杂谈随感/话题；人生=人世间/人生之旅/两代之间/青年一代/婚姻家庭；生活=生活之友/心理人生/经营之道；人物=名人轶事/回忆）。

## 一、适用边界

**做**：版式复刻、成书装配、排印质检、样式模板派生。
**不做**：文章创作（转读者杂志知识库）、图书 ISBN/刊号申领、印刷厂出片、版权授权谈判。
**红线**：输出物不得出现《读者》刊名刊号作本刊身份；封面署名须为用户自有名称或留白。

## 二、能力矩阵

| 能力 | 入口 | 交付物 |
|---|---|---|
| A 版式规范 | `references/layout-spec.md` | 参数表 + `assets/theme.css` |
| B 成书装配 | `scripts/book_builder.py` | 整册 HTML |
| C PDF 出片 | `scripts/export_pdf.py` | 16开/A4 精排 PDF |
| D 排印质检 | `scripts/layout_check.py` | 质检报告 JSON + 终端表 |
| E 样张试排 | `scripts/book_builder.py --sample` | 单篇样张 |
| F 图文混排 | `book_builder.py` 的 `{wide}`/浮图语法 + `theme.css` | 跨栏大图 / 栏内浮图 / 图题 |
| G 主题换肤 | `--theme <name>`（style_builder / book_builder） | 10 套主题配色成品 |
| H 配图（AI 主 / 手绘兜底） | AI 通道：`qf-lineart/scripts/prompt_builder.py` 出提示词 + 绘图后端；兜底：`scripts/illustration_draw.py` + `--auto-images` | 每篇 1 张跨栏大图 + 1 张栏内小图，一律米白纸实底 |

## 三、五维评估

1. **形态**：单篇样张 / 整册成书 / 既有稿校核 —— 决定走 B 还是 D
2. **开本**：16开（185×260mm）杂志本 / A4 打印本 —— 决定 `@page size`
3. **栏式**：卷首语等宽两栏、正文双栏、长文通栏 —— 决定 `column-count`
4. **装配层级**：封面 → 扉页 → 版权页 → 目次 → 正文册页 —— 决定页序与页码起始
5. **交付形态**：PDF / HTML / Word —— 决定导出通道

## 四、四级响应 L1–L4

- **L1 快排**（≤1篇，单栏）：直接 `book_builder.py` 出样张 HTML，`export_pdf.py` 出 PDF。适用内部速览。
- **L2 标准**（1册，含目次）：走完整七步工作流，产出 PDF+HTML 双形态，过门禁 🔴G1–G4。
- **L3 精排**（多栏目/合订本）：栏目页眉镜像、卷首语双栏、目录页码回填（两遍编译），过全部门禁 G1–G6。
- **L4 出版级**（对外分发）：在 L3 基础上加版权页、页边留白打样核对、逐页目次页码一致性抽检、缺字（豆腐块）全量扫描。

## 五、版式规范速查（核心参数）

| 项目 | 参数 | 依据 |
|---|---|---|
| 开本 | 16开 185×260mm（A4 备选 210×297mm） | 《读者》开本 |
| 正文 | 宋体五号（10.5pt），行距 1.5–1.6 倍 | GB/T 3179-2009 正文≥5号 |
| 卷首语 | 等宽两栏，标题行/作者行/出处行 **不分栏** | 《读者》卷首语版式 |
| 正文栏式 | 双栏，栏间距约 2 字符 | 16开杂志常规 |
| 页眉 | 小图 + 篇名 + 栏目名；**奇数页**：图名在左、栏目在右；**偶数页**：图名在右、栏目在左 | 《读者》页眉规范 |
| 页脚 | 作者名居中，奇偶相同 | 《读者》页脚规范 |
| 页码 | 底端外侧（单页右下、双页左下），阿拉伯数字，起始 1 | GB/T 3179-2009 |
| 卷首语页 | 无页眉页脚，保留页码 | 《读者》样文 |
| 目次页 | 上部 2/3 排目次（栏目+篇名+作者+页码），下部 1/3 排版本记录 | 出版实务 |
| 标题层级 | 一级小3号黑体居中、二级4号标宋居左空2字、三级小4号标宋、四级5号黑体 | 书籍版式设计表 |
| 纸张 | 封面/彩页 120g 铜版纸，内页 70g 淡黄书写纸 | 《读者》用料 |
| 图片 | 跨栏大图 `{wide}` 通栏；栏内浮图 42% 左浮（通栏文章转居中） | 图文混排 |
| 首字下沉 | 卷首语默认启用，字高≈3行，顶对齐首行、底对齐第3行 | 杂志体例 |
| 差错率 | 万分之 0.5 以下（对标《读者》13校次） | 《读者》编校质量 |

完整参数（页边距、版心、字体回退链、色彩）见 `references/layout-spec.md`。

## 六、成书标准工作流（七步）

```
① 收稿定清单   → 稿件 md 目录 / JSON 清单，确认栏目归属与排序
② 定开本栏式   → 选 16开/A4，定每篇栏式（卷首语两栏、正文双栏/通栏）
③ 套版式样式   → 生成/复用 theme.css（$S/assets/theme.css）
④ 装配册页     → 封面 + 扉页 + 版权页 + 目次 + 分栏目正文
⑤ 两遍编译     → 第一遍出册页量页码 → 回填目次 → 第二遍定稿
⑥ 导出三形态   → PDF（WeasyPrint）+ HTML（自包含）+ Word（挂样式）
⑦ 排印质检     → layout_check.py 过 G1–G6 门禁
```

关键代码调用：

```bash
# 生成成书 HTML（含封面/目次/分栏目正文）
python3 $S/scripts/book_builder.py --manifest book.json --theme $S/assets/theme.css --out book.html

# 导出 PDF（16开精排，页眉页脚页码由 CSS Paged Media 控制）
python3 $S/scripts/export_pdf.py --html book.html --out book.pdf --size 16k

# 排印质检
python3 $S/scripts/layout_check.py --html book.html --report qc.json
```

## 七、脚本工具

| 脚本 | 用途 | 关键参数 |
|---|---|---|
| `$S/scripts/style_builder.py` | 由参数派生 theme.css 与规格 JSON | `--size 16k\|a4`、`--columns 2\|1`、`--out` |
| `$S/scripts/book_builder.py` | 稿件清单 → 整册 HTML | `--manifest`、`--theme`、`--out`、`--sample` |
| `$S/scripts/export_pdf.py` | HTML → PDF（WeasyPrint） | `--html`、`--out`、`--size`、`--pdf-only` |
| `$S/scripts/layout_check.py` | 排印质检 | `--html`、`--report`、`--strict` |

## 八、质量门禁 🔴

- 🔴G1 **正文不小于五号字**：`font-size` < 10.5pt 直接判不合格（对标 GB/T 3179-2009）
- 🔴G2 **目次四要素齐全**：栏目、篇名、作者、页码缺一不可
- 🔴G3 **页码连续且起始为 1**：正文页码连续、无跳号、无重号
- 🔴G4 **页眉奇偶镜像正确**：奇数页篇名在左、偶数页篇名在右，栏目名对侧
- 🔴G5 **卷首语行内不分栏**：标题、作者、出处三行不得落入两栏排版
- 🔴G6 **无缺字**：全文中文字符均能被字体链覆盖，无 tofu（□）占位
- 🔴G7 **未冒用刊号**：输出物无《读者》刊名/刊号身份标识

## 九、失败模式、常见错误与教训

以下为排印实测的常见错误与处置教训。每条给出症状、根因与失败分支，处置手段涵盖回退（改用稳定方案）、重试（重编译或重排）、降级（换布局或字体）、兜底（人工核对）与错误处理，并覆盖异常、边界条件与断点续跑。

1. **两遍编译缺失致目次页码错位**：单遍编译时正文页码尚未定，目次页码只能写死或留空。对策：先出一遍量得各篇起始页，回填目次后再编译第二遍。
2. **WeasyPrint 不支持 flex 部分特性**：复杂 flex 布局在分页时塌陷。对策：成书页脚页眉一律用 CSS Paged Media 的 `@page` margin box，不用 flex。
3. **中文字体缺失落成豆腐块**：字体链未含中文字体时正文变 □。对策：字体栈固定写 `"Noto Serif CJK SC","Songti SC","SimSun",serif`，交付前用 `layout_check.py` 扫 tofu。
4. **卷首语被整体分栏**：把标题、作者也套进 `column-count`，标题被拆到右栏。对策：标题/作者/出处行包在 `.no-column` 容器外，仅正文段 `.col-body` 分栏。
5. **页眉奇偶镜像写反**：`@page :left/:right` 对应关系弄反，奇数页栏目名跑到左侧。对策：`:right` 页（奇）篇名左、栏目右；`:left` 页（偶）篇名右、栏目左。
6. **页码起始含封面**：封面、扉页、版权页计入正文页码，正文从第 4 页起。对策：前置页用 `@page :first`/命名页单独计数，正文页 `counter-reset: page 1`。
7. **开本单位混用**：`@page size` 写 `16k` 关键字 WeasyPrint 不识别，退化成默认。对策：换算为绝对长度 `185mm 260mm`。
8. **目次页码按 Markdown 顺序而非排版顺序**：栏目排序与正文顺序不一致。对策：以 manifest 中的 `order` 字段为唯一排序源。
9. **长文通栏与双栏混排断页**：单篇内栏式切换未加 `break-before`，跨栏断字。对策：栏式切换处强制 `break-before: column`。
10. **导出 PDF 中文路径报错**：WeasyPrint 目标为中文名时偶发写盘失败。对策：先写 ASCII 临时路径再改名。
11. **列表与表格被挤成长段**：解析器不支持 `- ` 条目与 `| 表格 |` 时，多行被拼接成一整段，版面失去条目感。对策：排版引擎须解析无序／有序列表与表格，并给两栏内的列表与表格配紧凑样式；《江江手记》成书实际用到 458 处列表与 11 张表格。
12. **目次篇名断行成孤字**：目次表列宽固定、或由首行合并列均分时，长篇名会只剩一字换行（如「…到项／目副总」）。对策：目次表改弹性列宽（篇名主列 88mm、作者 24mm、页码 9mm），并复核全部条目单行完整显示。

## 十、反例黑名单（避坑与易错清单）

- × 目次只列篇名不列页码（违反 G2/G3）
- × 为省版面把正文压到 9pt（违反 G1）
- × 封面直接印"读者"字样充当刊物身份（违反 G7）
- × 卷首语与正文同栏式，丢失杂志特征（违反 G5）
- × 页眉只放篇名不放栏目，弱化栏目导航（削弱栏目节奏）
- × 交付只给 PDF 不给可编辑源（Word/HTML），回改困难
- × 直接改 theme.css 覆盖而不走 style_builder.py，参数与环境脱钩

## 十一、配图联动（v1.4.3：AI 主通道 + 手绘兜底）

本技能的自动配图环节由 **qf-lineart** 承担；本技能负责选题、落位与入版。

- **主通道（AI 出图）**：按文生成插画提示词（`qf-lineart/scripts/prompt_builder.py`，含具体场景描述与结尾负面约束），交由外部/平台绘图后端出图；每篇 1 张跨栏大图 + 1 张栏内小图。
- **兜底通道（程序化线稿）**：AI 出图缺位或失败时，用 `scripts/illustration_draw.py` 补位，保证图文齐备。
- **底色口径**：所有配图一律铺**米白纸实底**（`paper=True`），不使用透明底——透明底在深色界面与深色底纹上会呈黑底观感；确需透明底才显式 `--transparent`。
- 引擎正本：`qf-lineart/scripts/lineart_engine.py`（v2.1）；本技能 `scripts/lineart_engine.py` 为随包副本，`scripts/illustration_draw.py` 按「随包副本 → qf-lineart 技能 → 工作区软链」三级解析，单技能亦可独立运行。
- 选题口径：场景母题（三级台阶／工位／处理池／图纸／验收清单／合同／天平／函件／档案柜等）权重 ×1.5，贴合文章内容的具象场景优先于抽象符号。
- 风格口径：《读者》内页淡黄纸，默认 `--palette sepia`（暖褐，与纸色同族）+ `--style pencil`（铅笔，纸感最贴印刷）。
- 全册统一：清单 JSON 的 `illustration` 字段可写 `{"palette": "...", "style": "..."}`，覆盖命令行默认。
- 换风格：节庆选题 `rosewood`+`brush`；需更醒目 `ochre`+`fountain`；印刷小图 `ink`+`fountain`。
- 配图质检沿用本技能 G1–G7 门禁中与图相关项（不压字、不溢出、比例适配、底色适配）。
- **图跟文走（v1.5.0）**：配图清单条目可带 `anchor`（`kn:关键词`）；`_insert_auto_figures` 先按关键词定位段落、把图插在该段之后，命中不到再回退中段——对应图书版式惯例「先文后图，图跟文走，图文紧靠」。
- **文意提取（v1.5.0）**：选题优先走 qf-lineart 的文意提取通道（按正文写画面指令），母题选题退为兜底；画面立于文中具体物件与场景，不用符号化图解。

## 十一之三、图片去框化与三型形态（v1.7.0）

矩形图直接放到版面上会形成"贴图感"，与纸面割裂。设计界的解法是**退底与图底融合**——"作图与背景的融合，能使画面与版面融为一体，过渡自然，减少画面的割裂感"（《谈书籍装帧中插图及图片的处理技巧》）。

本技能提供 `scripts/image_feather.py`：把图片四边向版面纸色渐隐，**内部区域完全保留原像素**（不削弱主体），只在外缘过渡，视觉上"像画在纸上"。

```bash
# 纸色须与 theme.css 的 --paper 一致（默认 #FBF8F0）
python3 scripts/image_feather.py --src illustrations/opt --out illustrations/fade --paper "#FBF8F0" --band 64 --flat 0.42
```

参数口径：`--band` 渐隐带宽（像素或 `8%` 短边比）；`--flat` 内部完全清晰占比（0.42 = 内 58% 原样保留）。纸色取错会让边界重新显形，故**改 theme.css 的 --paper 后须重跑本脚本**。

### 三型形态（避免"全册同一处理"造成的审美疲劳）

`scripts/image_style.py` 按内容特征产出三种形态，整册按比例混用：

| 型 | class | 做法 | 适用 |
|---|---|---|---|
| **退底型** | `img-cut` | 主体从不规则轮廓中"浮"出（alpha 轮廓 + 低频抖动 + 透明区合纸色），无矩形边界 | 主体集中、四周留白的图（最多） |
| **圆形型** | `img-round` | 圆形取景 + 细圆环 + 圆内浅衬底，形成"舷窗"聚焦 | 物件特写（瓶/杯/印/门/窗等） |
| **渐隐型** | `img-fade` | 矩形保留，四边向纸色渐隐 | 画面铺满、无明显主体的图 |

```bash
python3 scripts/image_style.py --src illustrations/opt --out illustrations/v7 --mode cut --paper "#FBF8F0"
python3 scripts/image_style.py --src one.jpg --out one.png --mode round --ring "#96795C"
python3 scripts/image_style.py --src one.jpg --out one.jpg --mode fade --band 64 --flat 0.42
```

三条口径（勿回退）：
1. **底色必须先归一**——AI 生成图米白底实测 `#E6DED3`，比版面纸色 `#FBF8F0` 深约 44，不归一必显矩形。
2. **圆形必须有可见边界**——白底线稿裁圆后四角本是空白，与纸色无异，故须**圆内浅衬底 + 细圆环**，否则圆形成立但看不出。
3. **透明区合纸色存 JPEG**——同视觉下体积比 PNG 小一个数量级（实测 137 页成书 26 MB → 12 MB）。
4. **墨色加深** `--depth 1.5`——AI 线稿偏淡，围绕纸色放大差异可加深线条而不脏纸面。

### 配图尺寸口径（双栏版式）

栏宽 =（版心 152mm − 栏间距 8mm）/ 2 = 72mm。**半栏浮动图会把正文挤到 4–5 字/行**（版式惯例亦警告"绕图排文…尤其当环绕文字处于物体的左侧时"读起来困难），故栏内图取"占满一栏、居中"：

| 角色 | figure 宽 | 图宽 | 位置 |
|---|---|---|---|
| 跨栏大图 | 152mm | 128mm（版心 84%） | 版心居中，两侧不排文字 |
| 栏内小图 | 72mm | 66mm（栏宽 92%） | 栏内居中，正文保持完整栏宽 |
| 单栏篇（col-1） | 152mm | 96mm | 版心居中 |

要点（踩过的坑，勿回退）：`.article figure img{width:100%}` 特异性高于 `.figure-wide img`，改图尺寸必须写成 `.article .figure-wide img` 才会生效；WeasyPrint 对 column 内 `margin:auto` 与 `width:100%` 的容器居中支持不稳，figure 与图**都写固定 mm 尺寸**。

## 十一之二、目次页的两种呈现（HTML 单列 / PDF 双栏）

目次由 `book_builder.py` 的 `_toc_html()` 生成**同一份双栏结构**（`.toc-two` + `.toc-td` + `.toc-line`），由 CSS 按媒体分流：

- **HTML / 屏幕**：`@media screen` 下 `.toc-td` 转块级 → 单列连续排布；
- **PDF / print**：两栏 inline-block 并排，左右按加权行数（栏目名计 1.6 行）自动均分，栏目名与所属条目不被拆栏。

要点（踩过的坑，勿回退）：

1. `.toc-page` 必须**显式定宽**（`width:152mm`，= 16 开 185mm 减左右边距 15+18mm）。宽度 auto 时该容器会塌陷到约 80pt，导致栏宽异常、条目折行成窄条——故由 `book_builder` 写成 section 内联样式（优先级最高）。
2. 目次**行内**不用 `display:table`／`flex`（前者在 td 内触发宽度异常，后者触发异常分页），改用 `inline-block` 三段（篇名 84% + 点线 + 页码 14%）；页码右对齐、篇名过长自动省略不折行。
3. 条目**不带作者列**（全册同一作者时冗余），作者信息在版权页与正文署名著录。

```bash
python3 scripts/illustration_draw.py --manifest <清单>.json --per-article 3 \
    --outdir samples/images/auto --palette sepia --style pencil -o auto_images.json
python3 scripts/book_builder.py --manifest <清单>.json --auto-images auto_images.json --part body
```

## 十一之四、网页版适配（v1.9.0：独立样式表并行）

**PDF 双栏精排，网页单栏顺读**，两套由不同样式表承担：print 走 `theme.css`，web 走 `assets/web_theme.css`（合成时注入 HTML 末尾、全部 `!important`）。

> v1.7.0 曾用 `@media screen` 分流，规则写在 `theme.css` 中部被后续 print 规则**同特异性覆盖**（手机上仍双栏、右侧大片空白）。v1.9.0 起改为独立样式表，勿回退。

| 项目 | PDF（print） | 网页（screen） |
|---|---|---|
| 正文 | 双栏（栏宽 72mm） | **单栏**（窄屏双栏不可读） |
| 配图 | 固定 mm（跨栏 128/114/98mm，栏内 66/62/54mm） | **百分比**（跨栏 88%，栏内 86%，圆形 62%） |
| 目次 | 双栏 + 页码 | **单列 + 篇名锚点跳转**，页码隐藏（网页无分页） |
| 卷首语 | 等宽两栏 | 单栏 |

目次条目写成 `<a class="toc-line" href="#art-{order}">`，与正文 `<article id="art-{order}">` 配对——网页版点目次即跳转。

**屏幕留白**：PDF 靠 `@page margin`，屏幕没有——故 `@media screen` 须自给：`body{padding:0 18px}` + 正文容器 `max-width:760px; margin:0 auto`。否则正文贴屏幕左缘、行宽失控。

**踩过的坑**：`.toc-page` 曾同时用于"目次页 section"与"页码 span"（类名撞车），导致屏幕端想把 section 放宽时页码也被改。v1.7.0 起页码 span 独立为 `.toc-pg`。

## 十一之五、文章主题色（v1.8.0：少量文章的点缀）

整册若只有一种强调色，翻久了会单调。做法：**少量文章**取 theme-factory 十套主题里的其他色，替换该篇的 `--column`（栏目名/题花/装饰随之变色），其余篇保持默认赭红。

选色三条口径：
1. **与默认赭红同调**——低饱和、明度接近（避免各色并列成"彩虹条"）。
2. **色相仍可辨**——赭红／墨绿／藏青／赭橙四选，跨度不贪多。
3. **小字可读**——对纸色对比 ≥4.5:1。

用法（manifest 里给篇目加 `theme` 字段即可）：

```json
{"order": 15, "column": "文明", "title": "读书笔记管理与法律", "theme": "ocean"}
```

| 值 | 色 | 出处 |
|---|---|---|
| （缺省） | 赭红 `#8C2F2F` | 读者经典 |
| `forest` | 墨绿 `#416B4E` | Forest Canopy |
| `ocean` | 藏青 `#33608A` | Ocean Depths |
| `sunset` | 赭橙 `#A0703C` | Sunset Boulevard |

**两条口径（勿回退）**：①数量取"少量"——52 篇里 8 篇（约 15%）成点缀，多了即失统摄力；②**页眉右栏色须改中性灰**——`@page` 上下文不继承 article 的 CSS 变量，若仍写 `var(--column)` 会与文章内主题色冲突（页眉暗红、正文藏青）。

## 十二、一键成书（v1.9.0）

一条命令跑完七步，产出 **PDF 与网页版两套并行排版**：

```bash
python3 scripts/build_book.py --manifest manifest.json --name 成书名 --auto-images auto_images.json
python3 scripts/build_book.py --manifest manifest.json --name 试排 --sample 6      # 试排前 6 篇
python3 scripts/build_book.py --manifest manifest.json --name 仅网页 --skip-pdf    # 只出网页版
```

流程：①排正文（双栏）→ ②出 body PDF → ③提页码（逐篇单调递增定位）→ ④排前置（封面/扉页/目次/版权，回填页码）→ ⑤合并 PDF 并重压缩 → ⑥合成网页版（注入 `assets/web_theme.css`）→ ⑦跑 G1–G7 质检 → 列交付清单。

### 两套排版如何并行

| | PDF（print） | 网页版（web） |
|---|---|---|
| 样式来源 | `assets/theme.css` | `assets/theme.css` + **`assets/web_theme.css`**（注入在最后，全部 `!important`） |
| 正文 | 双栏（栏宽 72mm） | 单栏 |
| 配图 | 固定 mm（跨栏 128/114/98，栏内 66/62/54） | 百分比（跨栏 94%，栏内 92%，圆形 66%） |
| 目次 | 双栏 + 页码 | 单列 + 篇名锚点跳转，页码隐藏 |
| 留白 | `@page margin` | `body{padding:0 20px}` + 容器 `max-width:800px` 居中 |

**为什么独立成一套表**（踩过的坑，勿回退）：早期把网页版规则写成 `@media screen{...}` 放在 `theme.css` **中部**，被后面的 print 规则（如 `.col-2 .col-body{column-count:2}`）按"同特异性后定义者胜"覆盖——手机上仍是双栏、右侧一大片空白。现改为：`theme.css` 只留 print 规则；网页版规则单独放 `web_theme.css`，由合成脚本追加到 HTML 末尾并全部 `!important`。

### 主题与配图的一键衔接

- **主题**：`theme.css` 内置"读者经典"；`--theme <theme-factory 主题名>` 可整册换肤；单篇配色在 manifest 里写 `"theme": "forest|ocean|sunset"`。
- **配图**：先跑 `image_style.py` 出三型图集与 `style_map.json`，再按 `{order: [{file, role, style, anchor}]}` 组装 `auto_images.json` 交给 `--auto-images`。

**过程件命名**：`_body_<名>.html/.pdf`、`_front_<名>.html/.pdf`、`_pagemap_<名>.json`、`_cmp_<名>.json`——同名可覆盖，便于反复重排。

## 十三、专家件索引

- `references/layout-spec.md` —— 版式规范全参数（开本/版心/字体链/色彩/页眉页脚细则）
- `references/column-structure.md` —— 栏目结构、子栏目、排序与节奏
- `references/book-assembly-sop.md` —— 成书七步 SOP 与两遍编译详解
- `references/quality-checklist.md` —— G1–G7 门禁逐条判据与抽检表
- `references/failure-modes.md` —— 12 类排印故障的现场症状与处置
- `references/case-library.md` —— 案例登记模板与真实案例位（数据来源指引）
- `assets/theme.css` —— 默认版式样式模板（读者经典）
- `assets/sample-manifest.json` —— 稿件清单样例
- `assets/themes.json` —— theme-factory 10 套主题到版式 5 槽位的映射与对比度校验
- `scripts/illustration_draw.py` —— 手绘线稿配图（对接 qf-lineart 引擎：16 母题 + 5 笔触 + 7 套暖色 + 关键词选题 + 落位规划）
- `scripts/lineart_engine.py` —— qf-lineart 引擎随包副本（正本见 qf-lineart 技能）

## HTML 底座（已内嵌 · 可选增强）

本技能已内嵌 html-report-builder 底座 5 脚本（`scripts/htmlbase/`：md2report.py / palettes.py / build_report.py / board.py / html_check.py），自包含运行。

**本技能的主输出仍走其专用渲染器**（保证特有版式与交互不被替换）；当需要输出一份通用报告页/说明页（非本技能专用版式）时，直接调用内嵌底座：

```bash
python3 scripts/htmlbase/md2report.py <成稿md> -o <名称>_成果页.html --theme <配色id> --check
```

底座升版后用 `python3 scripts/sync_htmlbase.py --all --apply` 重新分发。
