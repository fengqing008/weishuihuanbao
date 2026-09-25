---
name: html-report-builder
display_name: HTML 成果输出引擎
slug: qf-html-report
category: 科技
tags: [HTML输出, 单文件自包含, 配色规范, WCAG对比度, 成果交付, 模板库, 版式母题, 设计纪律, KaTeX数学公式, 试题三段式, KPI数据卡, 图形围栏, mermaid流程图, 按需配图, 配图路由, 实景图配图, 商业插画配图, 手绘线稿配图, ima生图类型匹配, 配图色调统一, 无障碍校验, 分享卡片, 打印适配, 图片放大, 目录搜索, 跟随系统深色, 动画增强, 折线面积图]
author: 清风明月
version: 9.0.0
description: "HTML 成果输出引擎——把报告、说明书、方案、汇报、研究成稿、试题输出为单文件自包含 HTML，无外部依赖、可离线打开、可直接打印。内置 10 套经 WCAG 对比度校验的配色与 12 套版式母题（编辑长文、工程图纸、数据叙事、经典报告、执行简报、工程手册、周报、数据报告、竞品拆解、幻灯片、杂志长文、社媒卡片），来源分级与可追溯标注、信息缺口徽标、目录与返回顶部、打印适配与移动端响应式。能力覆盖 KaTeX 数学、callout/KPI 卡、试题三段式、缺口卡、自动 TOC、来源角标；顶部胶囊目录与 scroll-spy、章节 hero 卡与章内二次目录；八大画板与 stat/bignum/icons；图片 base64 内嵌与图注、chart 内联 SVG（bar/donut/line/area）、长表粘性表头与点击排序；图形围栏（mermaid 本地渲染、svg 直嵌）；侧栏布局与深色章节头。v7.0 并入外部最强三项实践——落笔前的设计判断三段、内容保真纪律（技术审查类页面逐条引用 file:line 证据）、反 AI slop 五条（CJK 字体栈、8px 基线网格、回避纯黑纯白、对比度 ≥4.5 带焦点态、禁用占位数据）；并全量嵌入 81 套模板库（13 类）作为可选参考，新增交付面分支（打印、邮件、公众号内联、长图）。触发场景 HTML 成果、单文件 HTML、可视化成果页、Markdown 转 HTML、网页版汇报、打印版报告、HTML 自检、配色对比度校验、无障碍校验、数学题排版、试题排版、流程图报告、架构图、按需配图、HTML 模板、版式母题。英文触发词 single-file HTML report, HTML deliverable, HTML theming, WCAG contrast check, accessibility check, KaTeX math, exam paper HTML, on-demand illustration, HTML template。不适用于 Word/PDF 文档生成（ima-doc / ima-pdf）、公文国标排版（docx-gw-format）、PPT 制作（ima-ppt）、扫描件解析（textin-xparse）。详见 SKILL.md 变更记录。"
---

# HTML 成果输出引擎

## 一、专家定位

把成稿内容变成一份"发出去就能用"的 HTML 成果件。判断标准只有三条——**离线打开不残缺、打印出来不变形、对方不用问来源**。

输出物是单文件自包含 HTML：CSS 与 JS 内嵌，不发起任何外部请求，支持桌面与手机阅读，支持打印，包含目录、返回顶部、来源区块与缺口标注。

不承担的任务：站点与后台开发、需要接口取数的动态页面、纯视觉海报设计（走社交卡片类技能）、Word/PDF 正式公文排版（走 docx-gw-format / contract-format）。

## 二、适用边界

能做：
- 把 Markdown、Word 成稿、结构化数据装配为单文件 HTML 成果页
- 为页面选定经对比度校验的配色，并生成可切换的多套主题
- 按来源分级规范落地角标、参考来源区块、数据来源行
- 用信息缺口徽标与观点块样式区分事实、观点与未证实信息
- 对已有 HTML 交付物做结构级自检并给出修复清单

不能做：
- 访问内网或需登录的资源（页面必须自包含，不得依赖外部链接存活）
- 无头浏览器渲染截图（沙箱无 Chromium；渲染层以结构校验与对比度计算替代）
- 代替业务判断（缺口标注指出问题，不给结论）

## 三、启动协议（三问锁目的）

输出前先确认三件事，目的不同，骨架与配色不同：

| 三问 | 取值 | 对页面的影响 |
|---|---|---|
| 给谁看 | 领导／客户／同事／公众／自己 | 领导看结论置顶，公众看信息密度与配色温度 |
| 看完要做什么 | 决策／学习／执行／了解 | 决策型加结论与风险区；学习型加目录与展开；执行型加清单与勾选 |
| 素材在哪 | 文件／知识库／链接／口述 | 决定入页素材与来源区块的填充方式 |

三问未答清即开工的，按最保守骨架输出（结论置顶 + 完整来源区块 + 缺口显式标注），并在交付说明中列明假设。

## 四、五维评估

对任务做一次快速定级，决定投入：

1. **素材完备度**：成稿齐备 / 需从零撰写 / 需外部采集
2. **可追溯要求**：是否对外发布、是否涉及数据与结论（对外且含数据 → 必须来源区块）
3. **版式复杂度**：单栏长文 / 含表格图表 / 含多级目录与附录
4. **交互需求**：静态阅读 / 需配色切换 / 需目录导航与折叠
5. **交付环境**：离线可用（强制）/ 打印分发 / 需嵌入其他系统

## 五、四级响应

| 级别 | 形态 | 适用 | 交付内容 |
|---|---|---|---|
| L1 | 单页速览 | 内部沟通、一页结论 | 单文件 HTML，无目录 |
| L2 | 标准成果页 | 汇报、说明书、方案 | 单文件 HTML + 目录 + 来源区块 + 10 套配色 |
| L3 | 研报级 | 对外研究、投资与尽调 | L2 + 图表区 + 缺口区块 + 参考来源分级清单 |
| L4 | 成书或站点 | 文集、多篇合辑、培训手册 | 多页装配 + 目次页 + 页眉页脚（走读者排印坊或本技能多页模式） |

## 六、全流程九步

### 落笔前的设计判断（最先执行）

1. 校准处理手法。审查、审计、复盘、简报类页面取实用型：层次真实、间距克制、不设浮夸 Hero；展示、叙事、宣发类页面取编辑型：允许更强的视觉表达。精心排布的页面不会出错，过度设计的页面常常出错。
2. 确定优先级。用户明确要求 > 项目既有设计系统（主题、令牌、组件样式） > 本技能默认选择。改版既有页面时先看令牌再定配色。
3. 先写方案再落笔。动笔前写出 4–6 个命名的十六进制色值、字体角色分配、一句话布局概念；写完自审一遍——这套方案是否对任何类似页面都成立？若成立即为通用套路，须重做差异化部分。

示例：内部汇报取实用型 → 近黑底 #0d1117、面板 #161b22、正文 #e6edf3、弱化 #8b949e、强调 #d8a657；标题走系统无衬线，数据走等宽；布局为左目录右单栏，结论置顶。

一、锁定目的：跑启动协议三问，定响应级别。
二、清点素材：列出入页内容清单与来源，标记缺失项。
三、选定骨架：从 `references/structure-templates.md` 取通用／汇报／研究三套骨架之一。
四、选定配色：按受众与场景取十套之一，写入数据文件。
五、装配内容：按骨架填章节，数据带角标，缺口打徽标，观点进观点块。
六、落实约束：逐条对照第十节的 12 条硬约束。
七、结构自检：`python3 scripts/html_check.py 页面.html`，FAIL 清零。
八、文本复核：`python3 scripts/html_check.py 页面.html --text-out plain.txt` 抽正文，再送写作质量校验。
九、归档交付：入库成果库、给出短链与 media_id、输出内容预览。

## 七、可追溯与来源标注规范（借鉴「信息收集与整理 v3.0」）

来源分级沿用 P0–P4：

| 级别 | 来源 | 页内标注 |
|---|---|---|
| P0 | 政府文件、财报、国际组织报告 | `<span class="src">P0</span>` |
| P1 | 权威咨询机构 | 同上，附发布日期 |
| P2 | 主流财经媒体 | 同上，单一来源不支撑关键结论 |
| P3 | 行业垂直媒体、分析师 | 同上，附"据 XX" |
| P4 | 社交媒体、论坛 | 仅作情绪参考，不进数据区 |

四条落地规则：
- 关键数据后置来源角标，页面末尾"参考来源"区块列出全量清单，含出处与级别。
- 单一来源的关键数据加 `[单一来源，待交叉验证]`；两源矛盾并列两个数值，不替读者裁决；数据超两年标 `[数据截至年份，时效性待确认]`。
- 未证实或待补数据用缺口徽标 `【待核：具体说明】`，黄底高亮，同时在"信息缺口"区块写明影响与补充渠道。
- 观点性内容进观点块（左侧色条 + 观点标记），与事实叙述在视觉上分离。
- 内容保真：技术审查类页面（代码走查、方案审计、项目复盘）逐条引用证据——文件路径与行号、命令输出或数据源；不得为版面完整编造理由、路径或结论。证据不可得时写明「该项无证据支撑」，不作推测。

## 八、结构骨架

三套骨架的章节配置见 `references/structure-templates.md`，通用约定如下：

```
页头：标题 + 副标题 + 交付对象 + 成文日期
目录：锚点导航（章节数 ≥4 时必挂）
正文：章节按骨架取用，每节一段核心结论开头
结论区：一句话结论 + 核心发现（决策型任务必挂）
来源区：参考来源清单（P 级标注）
缺口区：信息缺口与风险（有缺口时必挂）
页脚：数据来源行 + 落款单位 + 成文日期
```

## 九、配色规范

十套配色取自 theme-factory 主题，已按长文阅读与打印场景补齐容器色、弱化色、边框色，并逐套做过 WCAG 2.1 对比度校验。

| 配色 | 模式 | 强调色 | 适用场景 |
|---|---|---|---|
| 深海蓝调 Ocean Depths | 深 | #56c1c1 | 领导汇报、数据仪表盘 |
| 日落大道 Sunset Boulevard | 浅 | #b04623 | 市场品牌、传播长图 |
| 森林冠层 Forest Canopy | 浅 | #40693f | 环保 ESG、行业长文 |
| 现代极简 Modern Minimalist | 浅 | #36454f | 学术政策、打印分发 |
| 金色时刻 Golden Hour | 浅 | #8a6300 | 餐饮文旅、节庆专题 |
| 极地霜白 Arctic Frost | 浅 | #3a628f | 医疗健康、技术方案 |
| 沙漠玫瑰 Desert Rose | 浅 | #9c5670 | 品牌设计、室内房产 |
| 科技创新 Tech Innovation | 深 | #4d94ff | 技术综述、AI 议题 |
| 植物园 Botanical Garden | 浅 | #3c6b4a | 环保农业、科普 |
| 午夜星河 Midnight Galaxy | 深 | #a490c2 | 投资财务、高端品牌 |

选色与调用：

```bash
python3 "$S/scripts/palettes.py" list                 # 十套配色一览
python3 "$S/scripts/palettes.py" css --theme ocean    # 取某套的 CSS 变量
python3 "$S/scripts/palettes.py" check                # 十套对比度复校
```

对比度门禁：正文对底色 ≥4.5，弱化文字对卡片底 ≥4.5，强调色对底色 ≥4.5，装饰性辅色 ≥3.0，页头白字对渐变两端 ≥4.5。整套不达标即换色，不靠加大字号补救。自定义主题流程见 `references/palette-guide.md`。

## 十、单文件工程硬约束（12 条）

1. 单文件自包含：CSS 与 JS 内嵌，无 `<link rel="stylesheet">`、无外部 `<script src>`。
2. 素材内嵌：图片转 base64 或改用 CSS/文字表达；字体只用系统字体族。
3. 离线可用：断开网络仍完整可读，交互不依赖外部接口。
4. 声明字符集与视口：`<meta charset>` 与 `<meta name="viewport">` 齐备。
5. 语言声明：`<html lang="zh-CN">`。
6. 标题唯一：一个 `<h1>`，层级不跳级。
7. 图片带 alt：装饰性图片用 `alt=""`。
8. 打印适配：含 `@media print` 规则，隐藏交互控件，保留正文与来源。
9. 弱底打印优先：需纸质分发的选亮底配色。
10. 目录与返回顶部：章节 ≥4 挂目录，长页面挂返回顶部。
11. 体积上限：单文件 ≤300KB（不含 base64 大图），超限先裁图再压样式。
12. 免责与来源：页脚含数据来源行与成文日期。

### 设计纪律（反 AI slop 五条，v7.0.0 新增）

来源：alchaincyf/huashu-design 的 Junior-Designer 反 AI slop 清单，已硬编码进外部 81 套模板库，现并入本技能。

1. CJK 优先字体栈：中文用 "Noto Sans SC" / "PingFang SC" / "Microsoft YaHei"，拉丁用 "Inter"，以系统字体族收尾，禁止只写西文字体。
2. 8px 基线网格：间距、内边距、行高取 8 的倍数（8/16/24/32/48/64），字号走模块化字阶。
3. 圆角分级配柔和阴影，回避纯黑 #000 与纯白 #fff，改用近黑近白。
4. 对比度 ≥4.5，每个交互元素带 :focus-visible 焦点态。
5. 禁用占位数据（lorem ipsum、示例数字、虚构人名），一律使用真实数据。

与既有约束的衔接：第 3、4 条由第十节硬约束与第九节配色门禁兜底，第 5 条由第七节可追溯规范兜底，第 1、3 条另由 html_check.py 的 CJK_FONT 与 PURE_BW 两项提示性检查覆盖。

## 十一、脚本工具

```bash
# 1. 结构级自检（本技能核心门禁）
python3 "$S/scripts/html_check.py" 页面.html
python3 "$S/scripts/html_check.py" 页面.html --json          # 机器可读结果
python3 "$S/scripts/html_check.py" 页面.html --node          # 追加 JS 语法校验
python3 "$S/scripts/html_check.py" 页面.html --text-out plain.txt   # 抽正文纯文本

# 2. 从数据文件构建页面（含骨架、目录、来源区、缺口区、配色）
python3 "$S/scripts/build_report.py" --init --out spec.json
python3 "$S/scripts/build_report.py" --data spec.json --out 成果页.html --theme ocean --check

# 3. 配色工具
python3 "$S/scripts/palettes.py" check --json

# 4. 一键入口：Markdown 成稿 → 底座级 HTML（供各技能调用）
python3 "$S/scripts/md2report.py" 成稿.md -o 成果页.html --theme forest --audience 某负责人 --check
python3 "$S/scripts/md2report.py" --list-themes

# 5. 看板入口：指标 JSON → 数据看板（KPI 卡 + 条形对比 + 阈值预警）
python3 "$S/scripts/board.py" --init -o board.json
python3 "$S/scripts/board.py" --data board.json -o 看板.html --theme galaxy --check

# 6. 智能配图：识别配图点 → 出任务单（再由 ima 文生图逐张出图）→ 瘦身回填
python3 "$S/scripts/illustrate.py" plan 成稿.md --theme sunset --max 4
python3 "$S/scripts/illustrate.py" apply 成稿.md --plan illustration/plan.json
python3 "$S/scripts/illustrate.py" check 成稿_illustrated.md --plan illustration/plan.json
python3 "$S/scripts/illustrate.py" styles
```

自检项的判定与修复动作见 `references/quality-checklist.md`；工具细节与扩展方式见 `references/output-spec.md`。

### 统一底座与技能接入契约（一键入口）

本技能是全库统一的 HTML 渲染底座。任何技能产出 Markdown 成稿后，用同一条命令即可生成达标 HTML，无需自建模板：

```bash
python3 skills/html-report-builder/scripts/md2report.py <成稿md> -o <成果页.html> --theme <配色id> --check
```

自动完成的语义着色（无需改 md 写法）：

- 来源角标：`(P0)`~`(P4)`（全/半角括号均可）→ 着色角标
- 缺口标注：`【待核：…】`/`【信息缺口：…】` → 黄底徽标
- 观点块：`> …` 引用行 → 观点卡
- 来源抽取：末章标题含「来源/参考」→ 自动生成「参考来源」分级表

接入契约（各技能在交付环节追加，原产物不动）：

1. 原始产物（Word/Excel/PDF/Markdown）保持不变——HTML 是伴生增量，不替换原件。
2. 由 md 底稿调用 md2report.py 生成 `XX_成果页.html`，与原件一并交付。
3. 生成后跑 `--check`（或 html_check.py），FAIL 清零；归档时 HTML 与原件一并入库。

配色速选：内部汇报 `ocean`／环保低碳 `forest`·`botanical`／打印分发 `minimal`·`arctic`／投资财务 `galaxy`·`golden`／技术前沿 `tech`。

**看板型技能**（数据/测算/台账类）改用看板入口，把关键指标组织成 KPI：

```bash
python3 skills/html-report-builder/scripts/board.py --data board.json -o <名称>_看板.html --theme galaxy --check
```

board 参数文件三段：`kpis`（label/value/unit/delta/status，status 取 ok|warn|crit，自动红黄绿着色）、`groups`（bars 条形对比 + table 明细，纯 CSS 无外链图表库）、`alerts`（阈值预警，超标自动标红）。同一门禁：`--check` 的 FAIL 清零方可交付。

## 十二、质量门禁 🔴

- 🔴 **门 1 结构自检**：`html_check.py` 输出 FAIL 必须清零，占位符残留、外链残留、变量缺失三项为零容忍。
- 🔴 **门 2 对比度**：页面实际使用的配色五项对比度全达标，`palettes.py check` 与页面内嵌变量一致。
- 🔴 **门 3 文本质量**：抽正文送写作质量校验，达 A 级（≥90）方可交付；不达标返工文案，不改小字号凑可读。
- 🔴 **门 4 可追溯**：含数据的页面必须挂来源区块，关键数据有角标；缺口项均有徽标与缺口区块记录。
- 🔴 **门 5 离线**：断网打开无缺失元素，无 404 依赖。
- 🔴 **门 6 打印**：打印预览中正文、表格、来源区完整，交互控件不出现。
- 🔴 **门 7 归档**：入库成果库并提供短链与 media_id，旧版本条目隐藏。
- 🔴 **门 8 配图**：按需配图并遵循路由——v5.3 起按成果类型自动匹配 ima 生图类型（调研/规划类实景图、文章/散文类杂志插画、生活文化类暖调手绘、政务类扁平矢量、技术前沿类科技抽象、品牌类 3D 渲染、技术工程类线稿、数据类图表）；`route` 判定相符、`plan` 提示词已注入文档主题色卡（配图色调与全文一致）；图片经 `illustrate.py apply` 处理（阈值 900KB、长边 ≤1920、q92，未超阈值不压缩）；渲染后 `html_check.py` 的 `IMG_EMBED`/`AI_FIG`/`IMG_ALT` 须为 OK，含图页用 `--max-kb 2000`；AI 生成图带「AI 配图」角标（`{ai}`），实景图不加角标但须标来源。
- 🔴 **门 9 无障碍与交付细节**：`html_check.py` 的 FOCUS_VISIBLE / SKIP_LINK / OG_META / THEME_COLOR / TH_SCOPE / ARIA_CURRENT / PAGE_RULE 七项须为 OK（新交付页面）；键盘 Tab 可走通顶部导航与正文交互，Esc 可关闭弹层；打印预览中长章节不出现大片空白、长表跨页重复表头。

## 十三、失败模式

| 情况 | 后果 | 处置 |
|---|---|---|
| 直接拿 Markdown 贴进 HTML 标签 | 表格与引用样式全丢 | 用 `build_report.py` 装配，正文按骨架结构化 |
| 页面引用了 CDN 的 CSS 或图标字体 | 断网或内网打开样式残缺 | 内嵌样式，图标改用字符或内联 SVG |
| 用大图做页头背景 | 体积爆到数 MB | 改用 CSS 渐变或内联 SVG |
| 深底配色用于纸质分发 | 打印费墨且灰度发灰 | 换亮底配色（极地霜白／现代极简／森林冠层） |
| 只用字号加粗强调弱对比文字 | 打印与低亮屏不可读 | 换达标配色，不靠字号补救 |
| 数据无角标、来源堆在正文 | 对方追问来源，可信度打折 | 数据后置角标，末尾来源区块列全量清单 |
| 缺口信息用"暂无数据"一句话带过 | 读者误当作已确认结论 | 用缺口徽标并写入缺口区块，注明影响与补充渠道 |
| 直接把 HTML 源文件送写作质量校验 | CSS 色值被误判为未千分位数字 | 先 `--text-out` 抽正文再送检 |
| 页面加了外部图表库 | 离线失效、体积翻倍 | 图表用内联 SVG 或 CSS 绘制，数据表兜底 |
| 目录锚点与标题 id 不一致 | 点击跳转失效 | 自检脚本会校验锚点指向，失效即修 |

## 十四、反例黑名单

- 不要用外链图片占位（`https://via.placeholder.com` 之类），一律内联或文字替代。
- 不要用 `<marquee>`、`<blink>`、自动播放音视频。
- 不要为观感堆模糊大背景图、玻璃拟态与多层阴影。
- 不要用纯色文字（#999 灰字）承载正文，弱化文字须过对比度。
- 不要在正文中写"点击这里下载"却指向沙箱本地路径。
- 不要输出需要联网加载的中文字体（如 Google Fonts）。

## 十五、方法论来源与借鉴登记

本技能把「信息收集与整理 v3.0」的六项机制移植到 HTML 输出场景：

| v3.0 机制 | 本技能落地形态 |
|---|---|
| 启动协议三问（先锁目的） | 第三节三问表，决定骨架、配色与信息密度 |
| 来源优先级 P0–P4 | 第七节来源角标 + 参考来源区块 + 页脚数据来源行；v2.0 扩展识别 `(P0 \| 日期)` 格式 |
| 交叉验证 if-then 规则 | 单一来源标注、矛盾并列、超期时效标注，写入第七节 |
| 信息缺口显式标注 | 缺口徽标 `【待核：】` + 缺口区块（影响与补充渠道） + v2.0 :::gap 围栏三列式 |
| 事实与观点分离 | 观点块样式，与事实叙述视觉分离 |
| 交付六项自检 | 门 1–门 7 质量门禁 + `html_check.py` 结构级自检（v2.0 增加 callout/锚点/TOC/数学公式校验） |

本技能 v2.0 同时整合 `structured-proposition-master` 的诉求：把 JSON 结构化试题渲染为三段式 HTML（题号/分值/难度/题干/子问题），并支持 KaTeX 数学公式渲染。

## 十六、v2.0 新增组件与语法（2026-09-22）

基于「信息收集与整理 v3.0」与「高中数学命题 skill」的实际输出对比，新增五类视觉组件与四项自检。

### 1. 强化 callout（GitHub 风格）

```markdown
> [!info] 这是一段提示信息
> 跨多行也行。

> [!warn] 这是一个警示
> 需要读者注意。

> [!crit] 这是一个风险
> 不处理可能造成损失。

> [!ok] 这是达标项
> 已确认通过。
```

渲染为 `.callout-info / .callout-warn / .callout-crit / .callout-ok`，左侧色条 + 顶部类型徽标。

### 2. KPI 数据卡（围栏语法）

```markdown
:::kpi
项目完成率 | 87 | % | 同比+5pp
预算执行率 | 92 | % | 略超预算
项目总数 | 156 | 个 | 新增22个
达标率 | 98.5 | % | 行业领先
:::
```

渲染为自适应网格（4 列起步，窄屏降到 2 列），每卡含标签/大数字/单位/趋势色与说明。

### 3. 试题三段式（围栏语法）

```markdown
:::q-card
Q1 | 4分 | 易 | 难度系数 0.25
已知函数 $f(x)=x^2+1$，求 $f(2)$ 的值。
(1) 写出 $f(x)$ 的表达式；
(2) 求 $f(2)$；
(3) 类比推广到一般情形。
:::
```

渲染为 `.q-card`，含题号 + 分值 + 难度色块（易/中/难），题干与子问题分段。

### 4. 缺口卡（围栏语法）

```markdown
:::gap
陕北项目数据 | 缺失导致结论仅适用陕南 | 榆林/延安住建局年报
2026中央一号文件涉水条款 | 决定后续投资节奏 | 中央农办官网
:::
```

渲染为三列式表格（缺口/影响/补充渠道），自动从「信息缺口与风险」章节识别并抽出。

### 5. 数学公式（KaTeX 自包含）

行内：`$f(x)=x^2+1$` → `.math-inline`
块级：
```markdown
$$
h(t) = 460 + 60e^{-t/30}
$$
```
→ `.math-block`，head 自动注入 `katex@0.16.11` CDN（自检白名单：仅 KaTeX 视为可接受外链）。

### 6. 自动 TOC

`##` 章节 ≥ 4 时自动生成目录气泡，锚点 id 与 section id 一一对应；自检校验两者一致。

### 7. 命令行参数

```bash
python3 md2report.py 成稿.md -o 成果页.html \
    --theme ocean --audience 某负责人 --check \
    --math           # 启用 KaTeX 数学公式（数学题必备）
    --no-toc         # 关闭自动 TOC
```

### 8. 新增自检项

| 校验 | 触发 | 失败后果 |
|---|---|---|
| CALLOUT | 出现 `> [!info]` 等 callout 时 | 检查开闭标签是否平衡 |
| ANCHORS | 出现 `href="#xxx"` 时 | 锚点指向不存在的 section id 时 WARN |
| TOC_MATCH | 出现 TOC 链接时 | TOC 链接数与章节数不一致时 WARN |
| MATH | 出现 `.math-inline/.math-block` 时 | 仅做平衡提示（KaTeX 注入是预期行为） |
| EXTERNAL_RES | KaTeX CDN 引入时 | 全部为 jsdelivr.net/npm/katex 时降级为 OK 并说明降级行为 |

## 专家件索引

- `references/output-spec.md` —— 单文件工程规范与自检项细则
- `references/palette-guide.md` —— 十套配色细则、对比度门禁、自定义主题流程
- `references/traceability-spec.md` —— 来源分级、缺口徽标、观点标注落地规范
- `references/structure-templates.md` —— 通用／汇报／研究三套骨架
- `references/quality-checklist.md` —— 交付前逐项清单与命令
- `references/failure-modes.md` —— 失败模式扩写与处置
- `references/case-library.md` —— 案例登记模板与数据来源指引
- `references/illustration-guide.md` —— 智能配图规范：识别规则、提示词模板、风格与体积门禁
- `references/illustration-routing.md` —— 配图路由规范：成果类型→配图源与 ima 生图类型、主题色卡、三类图标注、画质与体积（v5.3.0）
- `references/a11y-spec.md` —— 无障碍与交付细节规范：焦点/跳转/表格语义/ARIA、分享元信息、打印版心与避断、交互增强、动画安全（v6.0.0）

## 版本沿革（v2.1 – v6.3.0）

逐版明细见 `references/changelog-v2-to-v6.md`。摘要：v2.0 画板组件与自动 TOC；
v2.1 顶部胶囊目录与 scroll-spy、章节 hero 卡；v3.0 八大画板与设计系统重构；
v4.x 侧栏布局、图片内嵌与图注、数据图表、长表粘性表头；v5.x 智能配图三段链路与
生图类型路由、图形围栏；v6.0 无障碍与交付细节、内容动效增强；v6.1 hero 渐变与
mermaid 字号修正；v6.2 设计纪律层与四套版式母题；v6.3 内容密度与文风两项检查。

## 变更记录

> 以下为各版本迭代沿革（原记录于 description，为控制元信息长度迁至此处）。

- v9.0.0 围栏别名打通与时间轴两列（2026-09-24）——① **修复「逐日行程未按时间轴渲染」的根因**：底座原仅识别冒号围栏 `:::timeline`，而各技能文档普遍写反引号围栏（三反引号 + timeline），内容因此被当作普通代码块输出；现新增围栏别名表，`timeline / bar / bento / phase / law / faq / tags / matrix / stat / bignum / icons / kpi / gap` 等反引号围栏与冒号围栏完全等价，解析异常时降级为等宽代码块、不阻断整篇渲染。② **时间轴改为卡片内两列**（左时间 + 右内容），时间列用等宽数字右对齐、窄屏回落单列，更贴近移动端行程卡版式；圆点悬停同步放大。③ **图片块纳入入场动效**（图片与图片格错峰淡入上浮）。

- v8.0.0 导航单击修复与动效升级（2026-09-24）——① **修复顶部胶囊目录「须点两次才跳转」**：原实现于 `pointerdown` 立即 `setPointerCapture` 并加 `.dragging`，前者会把后续 click 的 target 改写成容器本身、后者给胶囊设了 `pointer-events:none`，二者叠加致首次点击落空；现改为位移超过 8px（判定为真拖动）后才捕获与加类，并在 click 处理中用按下时刻记录的元素兜底。② **时间轴卡片化**：对齐移动端行程卡版式——渐变竖线 + 圆点外光晕 + 圆角卡片（浅底、细边框、hover 微抬升），条目间距放宽至 12px，窄屏同步收窄。③ **动效升级为 CSS 滚动驱动**（渐进增强）：阅读进度条改用 `animation-timeline: scroll(root)`，时间轴竖线用 `view(block)` 随卡片进入视口生长，均在合成器线程运行、不再逐帧计算；不支持该特性的浏览器自动回退原有 JS 实现。④ **主题切换接入 View Transitions** 做跨主题淡变（不支持或已开启减弱动效时静默回退）。⑤ 新增 `@media (hover: hover)` 卡片抬升微交互；`prefers-reduced-motion` 与打印下全部还原静态。

- v6.3.0 新增内容密度与文风门禁（2026-09-24）—— html_check 增加 DENSITY（每章中文字数：低于 300 字/章 WARN、低于 225 字/章 FAIL，分母排除参考来源章）与 AI_TONE（黑话与序列化路标：命中 3 处以上 FAIL）两项检查，新增 --density-min / --no-density / --no-tone 参数；用于拦截「组件多、正文少」的空架子页面与 AI 腔文风。反向验证：旧版样例被判 DENSITY FAIL，新版样例全 PASS。
- v6.2.1 修复缺口区块判定口径（2026-09-24）—— html_check 的 GAP_BLOCK 原仅匹配 `class="gap"`，而渲染器输出 `class="gap-table"`，致含缺口卡的页面误报 WARN；正则放宽为 `class="gap`，三份样例复校后 WARN 清零。
- v6.2.0 设计纪律层与版式母题（2026-09-24）—— 引入 frontend-design 方法论，新增 `--motif` （editorial/blueprint/narrative/classic）与 `motifs.py`/`motif_check.py`；圆角分级收口、强调单色化、动效按母题编排、字体配对与模块化字阶、Hero 去默认化；66 副本分发漂移 0。
- v5.3.1 模拟测试修订（2026-09-24）——① 新增**公文文种优先规则**：命中「请示/批复/此函/来函/复函/收悉/现将/报告如下/请予批复/贵局/贵公司」等公文文种特征词 ≥2 处时直接判为政务公文（扁平矢量插画），修复「政务报告因含工程词汇被误判为工程方案」的偏差；② 修复 `plan --images-dir` 未作用于 `filename` 的旧 bug（原固定写 `images/` 前缀，同目录多篇成稿配图会互相覆盖），现 filename 随 images_dir 生成；③ 实测：18 例成果路由 **18/18 命中**；政务公文（minimal/flat-vector）与传统文化（golden/ink-watercolor）两组端到端各 2 张配图，组内风格统一、色调与主题色一致、无文字水印；渲染 FAIL=0。

- v6.1.0 体验层微调：hero 配色 / SVG 字号 / 配图通道（2026-09-24）——① **hero 渐变弃用黑色**：原 `mix(accent, #000000, w)` 改为各主题「接近主题色的深色」做过渡——亮模式用 `text`（深字色）、暗模式用 `surface`（卡片色），hero1/hero2 不再突兀，与主题色协调；CONTRAST 全主题 70 项最低 3.02 全达标；② **图形围栏 SVG 字号校正**：mermaid 节点 text `font-size="13"` 在 viewBox 缩放下实际渲染偏大，新增 `.fig-diagram svg text { font-size: 14px }` CSS 覆盖为显示端 14px（与正文 15px 协调）；③ **配图严格走 ima image_gen**：`illustrate.py plan --source` 默认改为 `ai`（强制 image_gen 通道），`cmd_lineart` 加 DEPRECATED 警告（明确非 image_gen 兜底），`cmd_plan` 在 lineart 分支改推 ai；④ **`dist_htmlbase.py` 修复**：硬编码 `VER="v6.0.0"` 改为直接读权威源 `_version.txt`，drift 函数 `_version.txt` 比对改读权威源；73 副本分发漂移 0/73。实测 5 主题回归 + 主/补充双用例 28 项全 PASS。
- v6.0.0 无障碍 / 分享 / 打印 / 交互细节与动画增强（2026-09-24）——① 无障碍：全站 `:focus-visible` 焦点环、跳至正文 skip-link、表头 scope、scroll-spy 写 aria-current；② 分享元信息：description + Open Graph（og:type/title/description/locale）+ theme-color（随主题动态）+ 内联 SVG favicon；③ 打印：@page 版心、局部避断替代整章避断、跨页重复表头、外链 URL 展开；④ 交互：图片点击放大 lightbox、抽屉目录搜索、长表点击排序（数值列自动识别）、跟随系统深色（无用户选择时）；⑤ 动画增强：环形图分段淡入、时间轴节点弹出、目录胶囊过渡、章节展开淡入、返回顶部淡隐、进度条过渡、hero 装饰漂浮（reduced-motion / print 全部还原）；⑥ html_check 新增 7 项校验（FOCUS_VISIBLE/SKIP_LINK/OG_META/THEME_COLOR/TH_SCOPE/ARIA_CURRENT/PAGE_RULE），ANCHORS 认可任意元素 id；⑦ `:::chart` 扩展 line / area。实测 5 组主题（sunset / sidebar / dark / sidebar+dark / forest）FAIL=0 WARN=0。
- v5.3.0 ima 生图类型库与成果类型路由（2026-09-24）——① 新增 **ima 生图类型库**（11 种视觉风格：2.5D 商业插画 / 扁平矢量 / 杂志编辑插画 / 暖调手绘水彩 / 科技抽象 / 信息图解 / 水墨国风 / 3D 渲染 / 写实摄影 / 手绘线稿 / 扁平信息示意）；② 路由由「文档类型→源」升级为「**成果文件类型（17 类）→ 源 + ima 生图类型**」，对全文关键词投票自动匹配，`--source`/`--style` 可覆盖；③ **配图色调与文档主题色一致**：ai 通道提示词注入主题色卡（accent/accent2/bg），线稿通道 `--palette auto` 按主题色温映射（sunset→terracotta、forest→olive、golden→amber、desert→rosewood、冷色→ink）；④ 统一 16:9 构图与「主体突出、留白充足、光线统一」美观约定；⑤ `illustrate.py styles` 新增类型库与路由表速查；⑥ 含图页 `--max-kb` 统一提至 2000（3—4 张高清图可用 2400）。实测 6 类成果路由 100% 命中、3 张水彩图色调与 sunset 主题一致。

- v5.2.0 配图路由与画质优先（2026-09-24）——① 新增**配图路由**：`illustrate.py route` 按文档类型自动判定配图源（调研/规划/行业类→互联网实景图；散文/文章类→ima 商业插画；技术/工程类→本地线稿或图形围栏；数据类→文字化图表），`plan --source {auto,photo,ai,lineart,chart}` 支持覆盖；② 实景图通道（photo）生成检索任务单、按实景照片特征交付，不加「AI 配图」角标但须标来源；③ 散文/文章类自动启用 article 模式（标题无视觉关键词、篇幅 ≥60 字亦可入选），解决散文配不出图的问题；④ **放宽压缩保画质**：阈值 350→900KB、长边 1440→1920、q82→q92，含图页体积上限 1200→2000KB，新增 `--no-compress`/`--max-side`/`--quality`/`--threshold-kb`；⑤ 新增 references/illustration-routing.md。
- v1.1.0 新增 md2report.py 一键入口（Markdown 成稿直接渲染为底座级 HTML）与「全库统一底座」接入契约，作为各技能 HTML 伴生交付的公共渲染层；
- v1.2.0 新增 board.py 数据看板引擎（KPI 卡 + 条形对比 + 阈值预警）；
- v3.0.3 对齐修复（用户截图实证）——时间轴圆点下移与首行文字垂直居中且时间行行高固定 1.45、sec-no 编号方块数字光学居中（line-height:1+padding-top:1px）、phase 状态徽标 baseline 改 center 对齐、二次目录行 align-items:center、移动端编号方块 42px 缩档；（第一行 brand+目录横滑、第二行主题色胶囊靠右）+正文排版美化（active 目录胶囊渐变底、KPI/Bento 数值渐变字、描述文字对比度提升至 76% 混合、表头渐变、phase 状态徽标与标题同行右对齐）；配色切换缩为单胶囊（点击弹出色板浮层、选中自动收起）、目录条整体置顶吸顶（毛玻璃单栏，brand 溢出省略）、点击目录平滑跳转正文 + 下滑自动高亮当前章节（scroll-spy 偏移适配新栏高）；Hero 头部升级（徽章/玻璃数据卡/标签行/几何装饰/底部波浪）、章节渐变编号方块+副描述+点击折叠、章节内二次目录（h3 自动收集为「本节要点」导航条）、八大画板组件（:::bento 网格看板/:::bar 横向条形图/:::timeline 时间轴/:::matrix 对比矩阵/:::phase 流程阶段/:::law 法条卡/:::faq 折叠问答/:::tags 标签行）；
- v2.0.0 整合两项借鉴（信息收集与整理 v3.0 的语义徽标与来源分级 + structured-proposition-master 的 JSON→HTML 三段式渲染需求），新增 5 类视觉组件与 4 项结构校验；
- v3.0.4 把 Hero 头部与章节组件补齐到 md2report 一键入口（frontmatter 直读 title/subtitle/audience/theme/hero_badges/hero_stats/hero_pills），并修复围栏行误作副标题、伪「正文」节、来源章未抽、缺口章重复、未知围栏死循环五处落地缺陷，html_check 增 SEC_NO/SUB_TOC/FENCE_LEAK 三项校验；
- v3.1.0 二次借鉴 5 份范本的布局参数，默认配色改日落大道（sunset）、容器放宽至 1100px、h1/h2/h3 字号 clamp 化、bento 改自适应栅格、双档阴影、hero 斜纹质感，并新增 `:::stat` 关键数字巨幕画板；
- v4.0.0 落细节层：侧栏目录布局（--layout sidebar）、巨幕大数 `:::bignum`、图标卡 `:::icons`、深色渐变章节头（--style dark）、hero 反向斜纹与卡片悬停位移。
- v4.1.0 补三项功能空白：图片内嵌与自动图注（`![图注](相对路径)` 加 `{wide}`/`{inline}`，base64 单文件自包含）、数据图表围栏 `:::chart bar|donut 标题`（内联 SVG，零外部依赖，随主题换色）、长表粘性表头（数据行 ≥12 自动套 .table-scroll，表头随滚动固定）。
- v4.2.0 把 v4.1 三项能力补齐到 md2report 一键入口（图片 base64 内嵌 + 图注自动编号 + 缺失虚线占位 + >1MB 体积提示），并给 board 看板引擎新增「表格数值列自动条形」与「sparkline 趋势线」两项表格能力，使 spec.json 与 Markdown 两条渲染路径能力对齐。
- v4.2.0 把 v4.1 三项能力补齐到 md2report 一键入口（图片 base64 内嵌 + 图注自动编号 + 缺失占位），并给 board 看板加「表格数值列自动条形」与「sparkline 趋势线」，实现两条渲染路径能力对齐。
- v4.2.1 修复（2026-09-22 模拟测试发现）：md2report 在未启用数学块（未传 --math）时遇 `$$` 块级公式行会死循环（段落分支指针不推进），已加兜底推进修复；并明确八大画板围栏的数据行须独立成行，不得与 `:::xxx` 同行书写。
- v4.3.0 新增移动端抽屉式目录：≤640px 下隐藏顶部横向胶囊与配色行，改由「目录」按钮弹出全屏章节抽屉（含配色主题行、当前章节高亮、点选即跳转并自动收起），触控热区 ≥46px；同步修正 html_check 的 TABBAR 统计口径（限定顶部栏内计数）并新增 MOBILE_TOC 校验。
- v4.4.0 曾加「抽屉子目录」，按用户要求已在
- v4.5.0 回滚。
- v4.5.0 顶部目录条增强——窄屏（≤640px）恢复顶部横滑胶囊栏（此前为隐藏），当前章节自动滚至栏内正中（只动横向、不动页面纵向），支持手指/鼠标按住左右拖动（位移超 6px 判定为滑动并抑制误触跳转）；抽屉按钮保留作章节全览入口。
- v4.6.0 顶部栏左侧大标题支持多行显示（最多 3 行、不再单行省略号截断），顶部栏实际高度由 JS 实时写入 CSS 变量 --topH，锚点 scroll-margin-top 与各跳转偏移（胶囊点击／hash 初始定位／抽屉跳转）统一改为 calc(var(--topH) + Npx) 与 topOffset() 动态取值，顶栏变高时不再遮挡章节标题。
- v4.7.0 顶部大标题改为「标题胶囊」入目录条（取消左上角独立 .brand 块），用独立类名 .brand-tab 以免影响 html_check 的 TABBAR 计数口径。
- v4.8.0 标题胶囊由目录条最左移到最右（右上角）钉住（position:sticky;right:0）。
- v4.9.0 抽屉目录面板（≤640px 点 ☰）顶部改为显示文档标题（.dp-title 最多 3 行），原「章节目录」降为下方小标签 .dp-kicker。
- v4.10.0 按要求取消目录条右上角标题胶囊（brand-tab 全部移除），文档标题只在抽屉面板顶部显示。
- v4.11.0 按内容增加动效：数据卡／时间轴／流程卡／法条卡错峰淡入、条形图横向生长（scaleX）、图表淡入、KPI 与关键数字滚动计数（保留千分位／小数位／单位前后缀）；reduced-motion 与打印自动还原静态；html_check 新增 FX 检查项（仅提示不判 FAIL）。
- v4.13.0 首屏结构重构（修 v4.12.0 兼容缺陷）：数据卡此前无 grid 容器（.hero-stats 为死代码）致卡片纵向 4 行，现补容器并固定 2 列，恒为 2 行 2 列；Hero 双栏改由 .hero-grid/.hero-col-l/.hero-col-r 的 flex 结构实现（右列 :empty 整列隐藏），不再依赖 :has()，旧内核 WebView 亦生效；章节头 flex-wrap 改 nowrap 且 .step-text 取消 200px 下限，编号方块与章节标题恒定同行对齐。
- v5.0.0 智能配图板块（ima 文生图全自动链路）——新增 `illustrate.py`（plan 识别配图点并生成中英提示词任务单 / apply 图片瘦身与回填 / check 完整性校验 / styles 风格速查），新增 `:::gallery` 图组围栏与图片 `{ai}`「AI 配图」角标，md2report 新增 `--max-kb` 体积上限透传；配图点识别按「标题强语义 > 标题弱语义 > 长章节篇幅」三级排序，四条风格预设（business-2.5d / lineart / photo / diagram），图片统一 base64 内嵌且离线可看。
- v5.1.0 图形围栏与按需配图（2026-09-23）——① 新增**图形围栏**：```mermaid 经 pretty-mermaid 本地渲染为 base64 SVG 内嵌（配色随报告主题），```svg 直接内嵌，dot/plantuml/excalidraw 等无本地渲染器语言降级为源码卡；新增 `render_diagrams.py` 渲染器（三级路径探测）与通用代码块（```python 等）；② **配图改按需触发**（默认不配图）；③ 新增**本地手绘线稿通道** `illustrate.py lineart`（qf-lineart 引擎，按章节关键词自动选母题，确定性、不出纯色），配图默认风格改 lineart；④ 新增**出图像素校验** `validate_image()`（边缘均值判据，拦「纯色/大片渐变」，实测 AI 低结构图 2.6 / 线稿 9.3–14.1 / 照片 18–25，阈值 5.0），apply/check 双处生效并支持 `--allow-solid` 放行；⑤ 顶部目录胶囊与「目录」按钮**垂直居中对齐**，置顶两行（.tf-row1/.tf-row2）宽与内边距对齐正文（1100px + 22px），消除胶囊下沉与左右不对齐；⑥ 新增 references/diagrams-guide.md。
- v4.13.1 来源表行内渲染：参考来源表单元格现支持 `**粗体**` 与反引号代码，修复 `**待核**` 原样漏出（正文段落与正文表格此前已支持，仅来源表用 esc 直出）。
- v4.12.0 首屏观感修复（据实页反馈，该版双栏依赖 :has() 兼容性不足，已由 v4.13.0 取代）：桌面端（≥960px）Hero 改双栏——左列为徽章／标题／导语／标签，右列为 2×2 数据卡，消除右半幅留白；底部波浪高度 46→38px、首节上边距收至 30px（移动端 22px），压缩首屏下沿空白；天气类内容支持 emoji 前缀（☀️ 晴／⛅ 多云／🌦️ 小雨／🌙 夜间／🌡️ 温差），在标签图例与数字卡中直接呈现。
据卡，消除右半幅留白；底部波浪高度 46→38px、首节上边距收至 30px（移动端 22px），压缩首屏下沿空白；天气类内容支持 emoji 前缀（☀️ 晴／⛅ 多云／🌦️ 小雨／🌙 夜间／🌡️ 温差），在标签图例与数字卡中直接呈现。

## 内容密度与 Word/PDF 导出规范（统一件）

本技能以单文件 HTML 为第一交付形态，Word/PDF 为伴生形态，二者共用同一份 Markdown 底稿，禁止两套内容。

### 一、内容密度指引

| 部位 | 参考量 | 说明 |
|------|--------|------|
| 首屏 hero | 数据卡 2–4 张 | 关键指标前置，超过 4 张移入正文 |
| 正文各章 | 800–2500 字 | 低于 800 字与相邻章合并 |
| KPI / 巨幕 | 每章 3–6 张 | 数值须带单位与口径 |
| 图表 | 每章 1–2 张 | 数据图用 `:::chart`，勿用文字复述数据 |
| 长表 | ≤ 20 行 | 超出折叠或启用粘性表头 |
| 配图 | 每篇 2–4 张 | `illustrate.py` 自动识别；数据对比用 `:::chart`，实景/流程用配图 |

### 二、Word / PDF 导出

- Word：Markdown 底稿经 pandoc `-f markdown-smart` 转 docx，再跑 docx-gw-format 技能挂接 Heading 大纲级别、字体、页码与目录域
- PDF：优先浏览器打印（保留 CSS 分页），批量场景用 WeasyPrint；须核对分页与页眉页脚

### 三、质检门禁（交付前必跑）

1. 运行本技能的 html_check.py 校验成品，须 FAIL=0（含 CSS 变量定义、围栏语法、对比度）
2. 运行工作区 scripts 目录下的 report_checker_pro.py 校验写作质量，A 级（≥90）方可通过
3. 单文件自包含（图片 base64 内嵌、无外部依赖）；未核实数据标【待核】

## 内容密度与各章字数指引（统一件）

HTML 报告无固定章节数，按下列密度控制，可按内容体量上下浮动 20%。

| 部位 | 参考量 |
|------|--------|
| 首屏 hero 数据卡 | 2–4 张 |
| 正文各章 | 800–2500 字 |
| KPI / 巨幕 | 每章 3–6 张 |
| 图表 | 每章 1–2 张 |
| 长表 | ≤ 20 行（超出折叠或粘性表头） |

密度原则：数据优先于叙述，同一数据不在正文与图表重复；章节过短（<800 字）与相邻章合并。

## 版式母题扩充（v7.0.0 · 4 → 12 套）

原 4 套（编辑长文、工程图纸、数据叙事、经典报告）扩至 12 套，新增 8 套取自外部 81 套模板的版式实践：

| 母题 id | 中文名 | 适用 |
|---|---|---|
| briefing | 执行简报 | 决策备忘、一页结论 |
| runbook | 工程手册 | 运行手册、操作细则 |
| weekly | 周期周报 | 周报、进度通报 |
| datareport | 数据报告 | 数据盘点、指标报告 |
| teardown | 竞品拆解 | 竞品分析、对标评估 |
| deck | 幻灯片 | 演讲、路演 |
| magazine | 杂志长文 | 特稿、深度长文 |
| card | 社媒卡片 | 小红书、图文卡 |

用法：`python3 scripts/motifs.py list`；渲染时 `--motif <id>`，与十套配色正交组合。

## 模板参考库（81 套全量嵌入，v7.0.0）

81 套外部精选模板已全量嵌入 `templates/`（来源 nexu-io/html-anything，Apache-2.0），13 类覆盖：幻灯片 23、文档 8、仪表盘 8、网页原型 8、视频帧 8、社媒卡片 7、海报 5、长文 4、数据 3、移动端 3、财务 2、邮件 1、简历 1。

```bash
python3 scripts/templates.py list                  # 全部模板
python3 scripts/templates.py list --cat slides     # 按分类
python3 scripts/templates.py search 仪表盘          # 关键词检索
python3 scripts/templates.py show data-report      # 读设计指令与示例路径
```

定位：模板库为可选参考，不替换本技能既有渲染路径。视觉型制品（海报、社媒卡、落地页、视频帧）优先取模板；交付型报告（汇报、说明、方案、研究）走本技能骨架与门禁。

## 交付面分支（v7.0.0）

同一份 Markdown 底稿可按交付面分发四种形态，内容零改动：

| 交付面 | 关键动作 | 关注点 |
|---|---|---|
| 打印 | 走 @page 与 @media print | 亮底配色，交互控件隐藏 |
| 邮件 | 单文件 HTML 作附件或内联 | 体积 ≤300KB，无外链 |
| 公众号内联 | 内联样式（juice 思路） | 不依赖 class，表格版式 |
| 长图 | 固定宽度整页截图 | 单列布局，避开 fixed 元素 |

## v7.0.0 升级记录（2026-09-24 · 吸收外部三项最强实践）

对齐全网 8 强 HTML 输出技能后的落地改造，分三级：

| 级别 | 事项 | 落点 |
|---|---|---|
| P0-1 | 设计判断三段（校准手法、定优先级、先写方案再落笔） | 第六章 |
| P0-2 | 内容保真纪律（技术审查类逐条引用证据，禁为版面编造） | 第七章 |
| P1-1 | 反 AI slop 五条 | 第十章子节 + html_check 增 CJK_FONT / PURE_BW |
| P1-2 | 版式母题 4 → 12 套 | motifs.py |
| P2-1 | 81 套模板库全量嵌入 + templates.py | templates/ |
| P2-2 | 交付面分支（打印、邮件、公众号内联、长图） | 本章 |

外部证据来源：visual-explainer 9.7k 星（设计判断与证据纪律）、huashu-design 19.5k 星（反 AI slop 清单）、html-anything 8.9k 星（81 套模板）；交叉验证过程与依赖实测见本次对标评估报告。

