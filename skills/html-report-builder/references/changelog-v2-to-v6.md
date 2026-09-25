# 版本沿革明细（v2.1 – v6.3.0）

本文件由 SKILL.md 迁出，保留逐版变更的完整记录；SKILL.md 正文只保留摘要，以免主干被历史记录稀释。

## 十七、v2.1 新增组件（2026-09-22 · 顶部胶囊目录 + 滚动联动 + 章节 hero）

基于两张茶饮营销方案截图（横向胶囊目录 + STEP 编号 hero + 卡片化正文）的样式诉求，新增五项视觉与交互能力。

### 1. 顶部 sticky 胶囊目录

- 触发条件：`##` 章节 ≥ 3 自动生成 `<nav class="chapter-nav">`，每节一个胶囊 tab
- 样式：横向滚动、sticky 在 topbar 下方（top: 56px）、滚动超过 hero 后变玻璃拟态（backdrop-filter: blur(12px) + 半透明）
- 数字编号：`STEP 01` / `STEP 02` / ... 与章节 hero 徽标一致
- 当前章节：背景填充实色（accent 色）+ 白字 + 阴影；其他：浅色描边 + 灰字
- 移动端：sticky 保留但字号减小、padding 收紧

### 2. 滚动联动（scroll-spy）

- 通过 `onScroll` 监听 scrollY + offsetTop 计算当前激活章节（偏移 200px 探测线）
- 自动滚动当前 tab 到可视中央（`scrollIntoView({inline:'center'})`）
- 同步 URL hash（`history.replaceState` 不污染历史栈）
- 滚到底部强制激活最后一节（避免短末段激活错乱）

### 3. 点击胶囊 → 平滑跳转

- `click` 事件委托给 `<nav>`，拦截后 `scrollTo({behavior:'smooth'})`
- 偏移 70px 让出 topbar + tabbar 高度
- 立即 setActive 反馈 + URL hash 同步

### 4. 章节 hero 卡

- 每节顶部生成 `<div class="chapter-hero">`，含：
  - `STEP N` 数字徽标（accent 色填充 + 白字 + 胶囊形）
  - 章节标题（自动从 `##` 提取）
  - 副标题（自动从首段非标题文本提取，最多 80 字）
- 渐变背景：左 accent 12% 透明 → 右 surface 纯色
- 左侧 4px accent 色条
- 移动端：padding 16px、字号 18px

### 5. 章节正文卡片化与内容丰富化

- 每节正文包入 `<div class="chapter-body">`，圆角 12px + border + 内边距 22×26
- 子标题（`###`）显示为左侧 3px 色条 + accent 色 + 16px
- bullet 美化：自定义 6px accent 实心圆点替代默认 disc
- 新增 `.subcard` 组件：左侧 3px 色条 + 4% accent 浅底，用于二级子卡
- 新增 `.divider-dash` 虚线分隔线
- 章节内引用条：accent 5% 浅底 + 左侧 3px 色条

### 6. 自检新增 3 项

| 校验 | 触发 | 失败后果 |
|---|---|---|
| TABBAR | 章节 ≥ 3 时 | 未生成 tabbar FAIL；tab 数与章节数不一致 WARN |
| HERO | 出现 chapter-hero 容器时 | hero 数与章节数不一致 WARN |
| SCROLL_SPY | 章节 ≥ 3 时 | 未注入 scroll-spy JS 时 WARN |

### 7. 用法（无变化）

```bash
python3 md2report.py 成稿.md -o 成果页.html
python3 md2report.py 成稿.md -o 成果页.html --math --theme forest
```

所有 v2.0 用法保持不变，新能力零配置启用。

## 十八、v3.0 画板组件与设计系统（2026-09-22 · 范本融合重构）

借鉴12篇标杆HTML范本（新媒体洞察/茶饮营销/政策手册/教案/竞品分析/案件报告等）的设计范式，重构视觉基座。全部组件零外部依赖、打印适配、移动端响应式。

### 1. Hero 头部升级（spec 字段）

| 字段 | 类型 | 渲染 |
|---|---|---|
| hero_badges | 字符串 | 标题上方胶囊徽章（描边玻璃态） |
| hero_stats | [{"v","l"}] 或 [字符串] | 首屏玻璃数据卡（自动网格） |
| hero_pills | [字符串] | 标签行 |

另新增几何装饰色块（.hero-deco 1-3）与底部 SVG 波浪过渡（.hero-wave），标题字号 clamp(26px,4.5vw,38px) 响应式。

### 2. 章节头 v3 与二次目录

- 编号徽章升级：STEP 文字徽章 → `.sec-no` 渐变方块（01/02/…，accent→accent-2 渐变 + 投影）
- 章节头可点击折叠（`.sec-fold` 箭头旋转，打印时强制展开）
- **二次目录**：`###` 小节自动生成锚点 id，章节头下方渲染「本节要点」导航条（≥2 个 h3 触发），点击平滑跳转、scroll-margin 让出吸顶栏

### 3. 八大画板围栏（md2report 可用）

| 围栏 | 行格式 | 组件 |
|---|---|---|
| :::bento | 跨列(1-3)\|标题\|数值\|描述 | Bento 不等宽网格看板 |
| :::bar | 标签\|数值原文\|备注 | CSS 横向条形图（按最大值归一化） |
| :::timeline | 时间\|标题\|说明 | 竖排时间轴（节点圆点+连线） |
| :::matrix | 围栏内放 Markdown 表格 | sticky 首列对比矩阵+横向滚动+滑动提示 |
| :::phase | 标题\|说明\|徽标 | 流程阶段卡（自动编号圆形序号） |
| :::law | 《法规》条款\|原文 | 法条引用卡（宋体强调+左色条） |
| :::faq | 问题\|答案 | 原生 details 折叠问答 |
| :::tags | 顿号/竖线分隔 | 标签 chips 行 |

board.py 同步新增 render_timeline / render_bento（JSON groups 内 `timeline` / `bento` 键）。

### 4. 自检修复

- ANCHORS：修复 h 标签 id 元组与字符串比较导致悬空误报的既有 bug（v2.0 引入），修复后 sub-toc 的 h3 锚点纳入校验。

### 5. 用法示例

```bash
python3 md2report.py 成稿.md -o 成果页.html --theme ocean
python3 build_report.py --data spec.json --out 成果页.html --check
python3 html_check.py 成果页.html --node
```

spec.json 新字段示例：`"hero_badges": "某水务集团 · 季度经营", "hero_stats": [{"v":"3,327万","l":"营收"}], "hero_pills": ["按效付费","吨水成本"]`

设计范式提炼详见 references/design-system-v3.md。

## 十九、v3.0.1 顶部栏重做（2026-09-22 · 配色胶囊 + 目录置顶）

### 1. 配色切换单胶囊化

- 原「配色 label + 10 个色点 + 主题名」横排 → 收纳为**单个胶囊按钮**（渐变圆点 + 当前主题名 + 展开箭头）
- 点击弹出**色板浮层**（5 列网格，absolute 定位不挤压目录）；点选后自动收起；点浮层外部也会收起
- 胶囊圆点用 `linear-gradient(135deg, var(--accent) 50%, var(--accent-2) 50%)` 随主题自动变色

### 2. 目录条置顶吸顶

- topbar 与章节胶囊目录**合并为单条置顶栏** `.top-fixed`（sticky top:0 + 毛玻璃 + 底边线）
- 布局：左侧 brand（溢出省略，max-width 200px）｜中部目录胶囊横向滚动（滚动条隐藏）｜右侧配色胶囊
- 原 chapter-nav（页内 sticky 双栏）结构废除，`id="chapterNav"` 移至 fixed-toc 容器，scroll-spy 与点击跳转逻辑不变
- 各级 scroll-margin-top 与 JS 滚动偏移按新栏高（约 56px）重校：section 64px、h3 96px、JS offsetTop-62

### 3. 交互链路

1. 点击目录胶囊 → 平滑滚动至对应章节（-62px 偏移）+ 立即激活该胶囊
2. 正文下滑 → scroll-spy 按章节 offsetTop 探测自动高亮当前章节胶囊（滚到底强制末章）
3. 章节头可点击折叠；折叠后 scroll-spy 按新布局重算
4. 二次目录（本节要点）锚点跳转由 scroll-margin 让位，不遮挡

board.py 同步替换为 top-fixed 结构（无目录时中部留空，胶囊靠右）。

## 二十、v3.0.2 顶栏两行化与排版美化（2026-09-22 · 手机端重叠修复）

### 1. 背景

手机端窄屏下 brand、目录胶囊、配色胶囊三者挤同一行互相压盖（用户截图实证）。修复采用物理分行而非挤压收缩。

### 2. 两行结构

- 第一行 `.tf-row1`：brand（溢出省略）+ 目录胶囊条（flex:1 横滑，独占）
- 第二行 `.tf-row2`：左"主题色"小字 + 右**配色胶囊**（justify-content: flex-end）
- 移动端 640px 以下隐藏"主题色"小字；打印时整行隐藏
- 锚点偏移重校：section 88px（移动端 100/102px）、h3 118px、JS 点击滚动偏移 -84px

### 3. 正文美化

| 项 | 实现 |
|---|---|
| 当前章节胶囊 | active 改渐变底白字（accent→accent-2），扫一眼即知位置 |
| KPI/Bento 数值 | 渐变文字（background-clip:text），打印时回退纯色 |
| 描述性文字 | tl-desc/phase-d/b-d/step-sub 等由纯 --muted 提升为 text 76% 混合，对比度明显提高 |
| 表格表头 | 主题色 9% 渐变底 |
| phase 状态徽标 | 由卡片级右浮改为与标题同行 phase-headrow 右对齐，多卡纵向对齐 |
| FAQ | summary hover 浅色反馈 |
| 章节标题 | h2 字距 .015em |

### 4. 验证

三份技能模拟样例（经营/水质/结算）+ 两条基座样例全部 FAIL=0 WARN=0；结构断言 9/9（两行结构/配色第二行右对齐/phase 对齐/渐变/偏移/打印隐藏）。

## 二十一、v3.0.3 对齐修复（2026-09-22 · 用户截图实证）

手机端两处垂直错位（时间轴圆点相对首行偏上、章节编号方块与标题的视觉重心偏差、阶段卡状态徽标基线漂移、二次目录标签上缘不齐）。修复五处：

| 组件 | 修复 |
|---|---|
| timeline 圆点 | ::before top 5px→8px；.tl-time 行高固定 1.45（消除字体缩放引起的首行漂移） |
| sec-no 编号方块 | line-height:1 + padding-top:1px 数字光学居中；移动端缩至 42px/15px |
| phase 状态徽标 | phase-headrow baseline→center（不同字号盒中心对齐） |
| 二次目录 | sub-toc 增 align-items:center |
| chapter-hero | 编号方块与标题同行时 flex center 保持，换行时各自成行 |

## 二十二、v3.0.4 md2report 入口补齐（2026-09-22）

范本融合的 Hero 头部与章节组件此前只在 build_report.py（spec.json 路径）可用，Markdown 一键入口 md2report.py 缺失，各技能走最常用入口时拿不到头部升级。本次补齐，并修五处落地缺陷。

### 1. Hero 字段接入 md（frontmatter）

md 文首 YAML frontmatter 直接声明，零配置渲染：

```yaml
---
title: 某市项目第三季度经营分析报告
subtitle: 2026年Q3 · 按效付费与成本管控专题
audience: 董事会
theme: ocean
hero_badges: 某水务集团 · 季度经营
hero_stats: ["1,286.4 万吨|处理水量", "82.3%|平均负荷率"]
hero_pills: 按效付费 · 吨水成本 · 结算审减
---
```

- 键名：`title` `subtitle` `audience`（或 `deliver_to`）`date` `theme` `conclusion` `hero_badges`（或 `badge`）`hero_stats` `hero_pills`
- `hero_stats`：`值|标签`，多项用 `;;` 或 YAML 列表；引号内逗号受保护（`"1,286.4 万吨"` 不被拆断）
- `hero_pills`：分号/顿号/竖线/中点（·）均可作分隔
- frontmatter 未给 `subtitle` 时，自动取 h1 后首个正文段作首屏 lead
- CLI 覆盖：`--hero-badge` `--hero-stats "值|标签;;值|标签"` `--hero-pills "a·b·c"`

### 2. 修复五处落地缺陷

| 缺陷 | 现象 | 修复 |
|---|---|---|
| 围栏行误作副标题 | 章节头出现 `:::gap` 脏文本 | 副标题提取跳过 `:::` 行 |
| 伪「正文」节 | h1 后首段被包成章节，污染 TOC | 前导段改作 lead，仅全文无 `##` 时才成节 |
| 来源章未抽 | 「七、来源」未抽出，「参考来源」块缺失 | 去序号后按首词匹配（来源/参考/参考资料/信息来源） |
| 缺口章重复 | 缺口章与其独立区块同时渲染 | 抽为独立区块后移除原章节（无额外正文时） |
| 未知围栏死循环 | 错拼 `:::tagz` 致进程 OOM 被杀 | 未匹配围栏兜底为文本并前进指针 |

### 3. html_check 增 v3 校验

新增三项：`SEC_NO`（章节编号方块数=章节数）、`SUB_TOC`（章内二次目录）、`FENCE_LEAK`（`:::xxx` 未解析残留 → FAIL）。

### 4. 补入渐入动画（reveal）

范本（新媒体洞察）用 `.reveal` + 错峰延迟做滚动渐入。本基座补入同名机制：章节 section 加 `class="reveal"`，进入视口时 CSS 过渡（opacity + 22px 位移）；`reveal-ready` 由 JS 仅在允许动效时挂载，因此**禁用 JS、prefers-reduced-motion 或打印时内容始终可见**，不牺牲可访问性。

### 5. 实证

综合样例（hero 徽章/数据卡/标签行 + 八围栏 + 3 处 h3 二次目录 + 来源 + 缺口 + 渐入动画）渲染：FAIL=0 WARN=0；错拼围栏样例正确报 FENCE_LEAK FAIL 且不再崩溃。

## 二十三、v3.1.0 布局与美感升级（2026-09-22 · 二次借鉴五份范本）

对照银发经济、新媒体洞察、茶饮营销、地理教案、现制咖啡调研五份范本的布局参数，补七项。

### 1. 默认配色改为日落大道（sunset）

build_report.py 与 md2report.py 的默认主题由 ocean 改为 sunset（燃橙 #b04623 + 赭金 #9c7420 + 深青 #264653，适用市场品牌、活动策划、传播型长图）。CLI `--theme` 与 md frontmatter 的 `theme` 仍可覆盖。

### 2. 布局参数对齐范本

| 项 | 旧 | 新 | 范本依据 |
|---|---|---|---|
| 容器宽 | 1040px | **1100px** | 范本 1080–1140px |
| h1 | clamp(26,4.5vw,38) | clamp(28px,4.6vw,44px) | 银发/地理/新媒体 |
| h2 | 21px 固定 | clamp(19px,3vw,24px) | 范本 clamp(18–20,3vw,23–27) |
| h3 | 16px 固定 | clamp(15.5px,2.3vw,18px) | 范本 15.5–17px |
| bento | repeat(3,1fr) | repeat(auto-fit,minmax(230px,1fr)) | 范本自适应栅格 |
| 阴影 | 单档 | 双档 `--shadow-sm` / `--shadow-lg` | 范本双档阴影 |

### 3. 新增关键数字巨幕 `:::stat`

借鉴银发范本 `clamp(72px,15vw,150px)` 的大数冲击，落地为独立画板组件（渐变数值 + 单位小字 + 标签 + 副说明，自动网格）：

```
:::stat
3,327 万元|营业收入|同比 +12.4%
1,142 万元|净利润|
82.3%|平均负荷率|较上季 +4.1 个百分点
:::
```

### 4. hero 斜纹质感

补 `.hero::before` 细斜纹叠加（借鉴新媒体 `hero-stripes`），提升首屏层次；打印时随背景一并处理。

### 5. 实证

综合样例（含 `:::stat`）默认渲染：配色 sunset、容器 1100px、stat 巨幕 4 卡、hero 斜纹生效，FAIL=0 WARN=0。

## 二十四、v4.0 细节升级（2026-09-22 · 再借鉴五份范本的细节层）

v3.1.0 补的是"骨架参数"，v4.0 补"细节质感"，五项均可单独开关。

### 1. 侧栏目录布局 `--layout sidebar`

借鉴咖啡调研范本 `grid-template-columns:220px 1fr` + `aside.toc{position:sticky}`：目录卡固定左侧、正文右栏、滚动高亮当前节，窄屏（≤900px）自动降级为顶部胶囊。长报告首选。

```bash
python3 md2report.py 长报告.md -o out.html --layout sidebar
```

### 2. 巨幕大数 `:::bignum`

借鉴银发范本 `clamp(72px,15vw,150px)` 的极端大数冲击（本基座取 `clamp(48px,11vw,108px)`，避免单页过长）。值支持千分位与单位：

```
:::bignum
3,327 万元|营业收入
1,142 万元|净利润
82.3%|平均负荷率
:::
```

### 3. 图标卡 `:::icons`

借鉴地理教案范本 `.ico`（圆角渐变图标块 + 标题 + 描述）：首列为图标（emoji 即可），自动网格。

```
:::icons
📋|验收程序|三级组织，程序合规
🔍|外业核查|154 个子项目现场核查
:::
```

### 4. 深色渐变章节头 `--style dark`

借鉴茶饮范本 `.section-head{background:linear-gradient(120deg,...)}` 白字章头；打印时自动降级为左侧色条 + 黑字。

```bash
python3 md2report.py 方案.md -o out.html --style dark
```

### 5. hero 反向斜纹 + 卡片悬停位移

借鉴新媒体范本的双组斜纹（`repeating-linear-gradient` 正/反向叠加）与 `hero-card:hover{transform:translateY(-5px)}`；hero 数据卡悬停上浮 4px。

### 6. 校验器加固

html_check 的 FENCE_LEAK 检测前先剥离 `<style>`/`<script>`，避免 CSS 注释与 JS 字符串里的 `:::` 造成误报。

### 7. 实证

四组组合（默认 / sidebar / dark / sidebar+dark）渲染 4/4 `FAIL=0 WARN=0 PASS`；`:::bignum`、`:::icons`、`:::stat` 三类卡与 hero 斜纹均按预期输出。

## 二十五、v4.1 功能补全（2026-09-22 · 图片 / 数据图表 / 粘性表头）

v4.0 补的是质感，v4.1 补的是三类此前只能绕行的功能空白：带图的报告、要看比例的结论、动辄几十行的长表。三项都留在单文件自包含的范围内，不引入外部库。

### 1. 图片内嵌与自动图注

语法 `![图注文本](相对路径)`，后缀 `{wide}`（默认，占满内容区）或 `{inline}`（居中收窄至 620px）。路径按 Markdown 文件所在目录解析；图片以 base64 内嵌，仍保持单文件离线可看；图注自动编号（图 1、图 2…，全篇连续）；超过 1 MB 的图在图注下标注原图体积。

```
![污水处理站工艺流程图](img/flow.png)

![小图居中示例](img/detail.png){inline}
```

路径不存在时输出虚线占位框并提示实际解析路径，不中断渲染。SVG 走 `data:image/svg+xml;base64`，位图按扩展名匹配 MIME（png/jpg/jpeg/gif/webp/bmp/tif）。

### 2. 数据图表 `:::chart`

行格式「标签 | 值」；值可带千分位、百分号与单位（`19,500 m³/d`、`42.5%`），基座取其中数值做比例，原值用于标注与悬停提示。

柱状对比（柱高按最大值归一，顶部标原值，下方标标签）：

```
:::chart bar 各街办子项目数量
代王街办 | 18
油槐街办 | 15
栎阳街办 | 12
:::
```

构成占比（环形，中心显示合计，下方自动生成图例与百分比）：

```
:::chart donut 验收问题类型构成
围栏与大门的遮挡 | 57
路面沉降 | 34
检查井问题 | 28
:::
```

两类图均为内联 SVG，取色 `var(--accent)`，随主题切换；柱与环段带 `<title>`，鼠标悬停显示原值；打印时整块不拆页。

### 3. 长表粘性表头

Markdown 表格数据行 ≥ 12 行时自动包裹 `.table-scroll`（最大高度 74vh，容器内滚动，表头 `position:sticky` 固定）。窄屏（≤720px）与打印自动取消高度限制、表头回归静态，避免小屏双重滚动；表格下方补一行行数说明。

### 4. 实证与核验

两图 / 柱 / 环三项做过数值核验：柱高归一化与数值比例逐项一致（18/15/12/11/9/7 → 1.0/0.833/0.667/0.611/0.5/0.389）；环形各段 `stroke-dasharray` 之和与周长误差 0.0004%；段占比 42.54% / 25.37% / 20.90% / 7.46% / 3.73% 与理论值一致。四组组合（默认 / sidebar / dark / sidebar+dark）渲染 4/4 `FAIL=0 WARN=0 PASS`。

### 5. 三项参数速查

| 需求 | 写法 | 关键约束 |
|---|---|---|
| 插图 | `![图注](相对路径)` / `{inline}` | 相对 md 所在目录，base64 内嵌 |
| 比大小 | `:::chart bar 标题` | 值可为 `1,234` / `42.5%` / `19500 m³/d` |
| 看占比 | `:::chart donut 标题` | 中心显合计，下方自动图例 |
| 长表 | 普通 Markdown 表格 | ≥12 行自动粘头，无需额外标记 |

## 二十六、v4.2 两条渲染路径对齐 + 看板表格升级（2026-09-22）

v4.1 的三项能力此前只落在 `build_report.py`（spec.json 路径）。本次把缺口补齐，并给看板引擎加两项表格能力。

### 1. md2report 路径补齐图片内嵌（与第二十五节对齐）

`md2report.py` 此前对 `![]()` 无处理，Markdown 成稿走一键入口时图片会丢。现补齐，行为与第二十五节一致：

- `![图注](相对路径)` → base64 内嵌，保持单文件离线可看；`{inline}` 收窄至 620px；
- 图注**自动编号**（图 1、图 2…，全篇连续），缺失图占位也占号；
- 路径不存在 → 虚线占位框并回显解析路径；单图 >1 MB 在图注追加体积提示；
- 远程 `http(s)` 图片保留外链并标 `remote` 类，不强行下载。

### 2. board 表格升级：数值列自动条形 + sparkline 趋势线

看板（`board.py`）的表格此前是纯文本。现按数据自动增强，无需改 JSON 结构：

| 能力 | 触发条件 | 表现 |
|---|---|---|
| 数值列自动条形 | 某列 ≥3 个可解析值且占比 ≥60% | 单元格内叠加主题色迷你条，长度按该列最大值归一 |
| sparkline 趋势线 | 单元格为逗号/空格分隔的 ≥3 个数字 | 渲染内联 SVG 折线 + 末点圆点 |
| 防呆 | 全部列都是数值 | 只保留最左一列出条，避免整表刷条 |

可解析格式：`1,234`、`42.5%`、`19500 m³/d`、`2.215 kWh/m³`。条形取 `var(--accent)`，随配色切换。

**实证**：真实数据样板「三层岩厂 2026年1月运行看板」——5 条周趋势 sparkline（31 天日进水量）+ 19 处自动条形，`FAIL=0 WARN=0 PASS`；「某市竣工结算推进看板」12 处自动条形，同指标通过。

### 3. 配套：门禁前移（外部，见工作区 scripts 目录下的 completion_checker.py v1.3.0）

`completion_checker` 新增 **C5 HTML 伴生交付**门：技能声明 HTML 伴生交付即必须有 HTML 且过 `html_check`；`auto_quality_gate.sh v2.4` 门2 已自动透传 `--skill-dir` 与 `--html-path`，实现"声明即校验"。

## 二十七、v5.0.0 智能配图板块（ima 文生图全自动链路）

把「需要配图」从人工找图改为基座自动完成：识别配图点 → 生成提示词 → 调 ima 原生文生图出图 → 瘦身回填 → 渲染内嵌。脚本承担首尾两段，出图一段由调用方（ima 文生图 image_gen）执行，二者以「配图任务单」交接。

### 1. 三段链路

| 段 | 执行者 | 动作 | 产物 |
|---|---|---|---|
| ① 规划 | `illustrate.py plan` | 扫描章节，命中语义者入选，生成中英提示词 | `illustration/plan.json` + `plan.md` |
| ② 出图 | ima 原生文生图（image_gen） | 按任务单逐张出图，文件名用任务单给定值 | `images/ai_01.jpg…` |
| ③ 回填 | `illustrate.py apply` | 瘦身（长边 ≤1440、q82、>350KB 才压）并插入 `![图注](…){wide,ai}` | `*_illustrated.md` |

### 2. 全自动用法

```bash
S=技能目录
# ① 出任务单
python3 "$S/scripts/illustrate.py" plan 成稿.md --theme sunset --max 4 --style business-2.5d
# ② 按任务单逐张调用 ima 文生图（image_gen），prompt 用 plan.md 的 prompt_en，图存到 images/
# ③ 瘦身 + 回填
python3 "$S/scripts/illustrate.py" apply 成稿.md --plan illustration/plan.json
# ④ 渲染 + 校验（配图页体积上限放宽到 1200KB）
python3 "$S/scripts/md2report.py" 成稿_illustrated.md -o 成果页.html --theme sunset --check --max-kb 2000
```

### 3. 配图点识别规则

- 标题命中强语义（工艺/流程/工序/步骤/现场/布置/平面/管网/系统/结构/构成/分布/对比/示意/场景/规划/设备/构筑物…）即入选；
- 标题命中弱语义（概况/背景/总述/目标/成效/风险/措施/计划…）入选，权重次之；
- 无标题语义但正文 ≥160 字的长章节作为补充候选；
- 已含图片或 `:::chart` 的章节跳过（不与数据图重复）；「来源/参考/附录」章跳过；
- 按分数取前 `--max` 处（默认 4），再按原文顺序回排，保证插图落位与行文一致。

### 4. 提示词与风格

- 四条风格预设：`business-2.5d`（默认，2.5D 等距商业插画）、`lineart`（手绘线稿）、`photo`（写实摄影）、`diagram`（扁平信息示意）；
- 提示词 = 风格前缀 + 报告主题 + 图注 + 主题强调色（读 `palettes.BY_ID`）+ 负面约束（无文字/字母/数字/水印/logo/边框）；
- 任务单同时给中英两版，出图优先用 `prompt_en`；多图复用同一风格前缀以保证整册视觉统一。

### 5. 图组与标注

- 单图：`![图注](images/x.jpg){wide}` 或 `{inline}`；加 `ai`（可组合 `{wide,ai}`）渲染「AI 配图」角标；
- 图组：`:::gallery 标题` + 每行「路径 | 图注」，≥3 张三列、≤2 张两列，窄屏与打印自动单列；
- 图片一律 base64 内嵌，保持单文件离线可看；缺失图输出虚线占位并提示实际解析路径。

### 6. 质检要点

- 单张配图瘦身后宜 ≤250KB（阈值 350KB 触发压缩）；
- 配图页体积上限用 `--max-kb 2000`（普通页默认 300KB）；
- `illustrate.py check` 校验图注非空、文件可达、任务单落位；
- `html_check.py` 的 `IMG_EMBED`（内嵌张数）与 `AI_FIG`（AI 角标数）两项须为 OK。

### 7. 边界

- 配图仅用于氛围、场景与结构示意；含精确数据的表达仍用 `:::chart` 或表格，不用 AI 图替代数据；
- AI 生成图一律加「AI 配图」角标，便于读者区分生成图与实拍图；
- 出图环节依赖 ima 原生文生图能力，离线环境仅能执行规划与回填两段。

## 二十八、v5.1.0 图形围栏与按需配图（2026-09-23）

### 1. 图形围栏（可视化主通道）

把「流程图 / 时序图 / 架构图 / 状态图」直接写进 Markdown，渲染为内嵌 SVG：

| 写法 | 渲染方式 |
|---|---|
| ```` ```mermaid ````（flowchart / sequenceDiagram / stateDiagram-v2 / classDiagram / erDiagram / xychart-beta） | 本地渲染（pretty-mermaid，**无浏览器、无网络**）→ base64 SVG 内嵌 |
| ```` ```svg ```` | 直接内嵌（任意绘图技能导出的 SVG 成品） |
| ```` ```plantuml ```` / ```` ```dot ```` / ```` ```excalidraw ```` 等 | 沙箱无本地渲染器 → **源码卡 + 处置提示**（不静默丢内容） |
| ```` ```python ```` 等普通语言 | 等宽代码块 |

- **图注**：围栏语言后跟文本即图注，例 ```` ```mermaid 工艺流程图 ````；自动编号，与图片共用计数器。
- **配色随主题**：先定报告主题，再把 surface/text/border/accent/muted 映射为 mermaid 主题色。实测 ocean 主题下渲染出的 SVG 背景 = `#1e2c3f`，与页面同调。
- **渲染器探测**：三级（基座 `scripts/vendors/pretty-mermaid` → `pretty-mermaid` → 工作区软链）；缺失自动降级为源码卡，**不阻断整篇渲染**。
- **内嵌方式**：`data:image/svg+xml;base64` + `<img>`，完全隔离 CSS，单文件自包含、离线可看。

```bash
S=<技能目录>
python3 "$S/scripts/render_diagrams.py" check          # 渲染器可用性（须「可用」）
python3 "$S/scripts/md2report.py" 成稿.md -o 成果页.html --check --max-kb 2000
```

### 2. 配图规则：按需触发（默认不配）

**默认不出图**。仅当用户明确要求配图（「配图 / 加图 / 插图 / 来几张图 / 给某章配图」）时才执行配图链。
未明确要求时，正文可视化由**图形围栏**（```mermaid）与**文字化图表**（:::chart / :::timeline / :::matrix / :::phase）承担，不调用任何出图。

### 3. 两条配图通道

| 通道 | 命令 | 特点 |
|---|---|---|
| **本地手绘线稿（首选）** | `illustrate.py lineart 成稿.md --max 3 --palette sepia --stroke pencil` | 确定性渲染、整册风格统一、**不出纯色**、零成本；按章节关键词自动选母题（32 母题含 plant 处理池 / checklist 验收清单 / contract 合同 / scales 天平 / letter 函件 / blueprint 图纸 / lab 化验台 / meeting 会议桌 等） |
| AI 文生图（按需） | `plan → 出图 → apply` 三段式 | 适合场景化氛围图；**出图后必经像素校验** |

### 4. 出图像素校验（防「配图是一块纯色」）

`illustrate.py apply` / `check` 内置 `validate_image()`，判据为**边缘均值**（画面结构密度，240px 缩略 + FIND_EDGES）：

| 图类型 | 边缘均值 | 唯一色 | 判定 |
|---|---|---|---|
| AI 大片渐变（低结构，视觉即一片色） | ≈2.6 | 80–94 | **拦截，拒绝落位** |
| 手绘线稿（白底 + 线条） | 9.3–14.1 | 108–181 | 通过 |
| 真实照片 | 18–25 | 1700+ | 通过 |

阈值 `min_edge=5.0`。被判低结构者不插图，并在输出中列出处置建议（重出 / 改用线稿通道 / `--allow-solid` 放行）。

### 5. 验收

- `illustrate.py check` 输出 PASS（图注非空、文件可达、无纯色图）；
- `md2report --check` 输出 `FAIL=0`，其中 `IMG_EMBED` 张数 = 图片数 + mermaid 图数 + svg 图数，`FENCE_LEAK` 须为 OK；
- 含图页体积用 `--max-kb 2000`。

### 6. 边界

- 含精确数据的表达一律用 `:::chart` / 表格，不用配图承载数值；
- AI 生成图保留「AI 配图」角标；本地线稿与自绘 SVG 不加该角标；
- 图形围栏依赖 Node.js（沙箱已装），渲染全程本地、离线可用。

## 二十九、v5.2.0 配图路由与画质优先（2026-09-24）

把「配图」从单通道升级为**按文档类型自动分流**，并放宽压缩以保住画质。配图仍为**按需触发**（默认不配，用户要求时才执行）。

### 1. 配图路由（文档类型 → 配图源）

| 文档类型 | 配图源 | 通道 |
|---|---|---|
| 调研报告 / 旅游规划 / 行业研究 / 项目报告 / 实地考察 | **互联网实景图（真实照片）** | 联网检索 → 下载 → `apply` |
| 散文 / 随笔 / 文章 / 品牌软文 / 文化 | **ima 商业插画** | `image_gen` → `apply` |
| 技术方案 / 工程 / 工艺 / 系统 | 本地线稿 / 图形围栏 | `illustrate.py lineart` / 图形围栏 |
| 数据 / 财务 / 台账 / 指标 | 不配图 | `:::chart` / 表格 |

判定：对全文关键词投票，得分最高者胜，全为 0 默认实景图。完整规则见 `references/illustration-routing.md`。

```bash
S=<技能目录>
python3 "$S/scripts/illustrate.py" route 成稿.md                            # 查看路由判定
python3 "$S/scripts/illustrate.py" plan 成稿.md --source photo --max 4      # 调研类 → 实景图任务单
python3 "$S/scripts/illustrate.py" plan 成稿.md --source ai --style business-2.5d  # 文章类 → 商业插画任务单
python3 "$S/scripts/illustrate.py" apply 成稿.md --plan illustration/plan.json
```

### 2. 三类图的标注与角标

- **实景图**：不加「AI 配图」角标，图注须标来源（图源：XX）；
- **商业插画**：加「AI 配图」角标（`{ai}`）；
- **本地线稿与自绘 SVG**：不加角标。

### 3. 画质优先（压缩放宽）

| 项 | 旧 | 新 |
|---|---|---|
| 触发压缩阈值 | 350KB | **900KB** |
| 瘦身长边上限 | 1440 | **1920** |
| JPEG 质量 | q82 | **q92** |
| 含图页体积上限 | `--max-kb 2000` | **`--max-kb 2000`** |

低于阈值**不压缩**；需要完全保留原图用 `apply --no-compress`；可 `--max-side/--quality/--threshold-kb` 微调。

### 4. 散文/文章的 article 模式

ai 通道自动启用：配图点不再要求标题含视觉关键词，篇幅 ≥60 字的章节即可入选，使散文、随笔能正常配图。

### 5. 验收

- `illustrate.py route` 给出预期配图源；
- `illustrate.py check` 输出 PASS；
- `md2report --check` `FAIL=0`；实景图不加角标、插画加角标。

## 三十、v5.3.0 ima 生图类型库与成果类型路由（2026-09-24）

在 v5.2.0「按文档类型分流」的基础上，把 ai 通道细分为 **ima 生图类型库**，把路由从「源」升级为「**成果类型 → 源 + 生图类型**」，并让**配图色调与文档主题色保持一致**。

### 1. ima 生图类型库（11 种）

`illustrate.py styles` 可速查。`tone=True` 的类型会注入文档主题色卡。

| 类型 id | 名称 | 适用成果 |
|---|---|---|
| business-2.5d | 2.5D 等距商业插画 | 汇报总结、行业分析、方案说明 |
| flat-vector | 扁平矢量插画 | 政务公文、政策解读、流程说明、科普 |
| editorial | 杂志编辑插画 | 文章、散文、评论、杂谈 |
| handdrawn-warm | 暖调手绘水彩 | 生活、文化、游记、亲子、情感 |
| tech-abstract | 科技抽象 | 技术前沿、AI、数字化、产品发布 |
| infographic | 信息图解 | 科普、教程、方法、知识卡片 |
| ink-watercolor | 水墨国风 | 传统文化、人文历史、国学、民俗 |
| 3d-render | 3D 渲染拟物 | 品牌、营销、活动、产品、传播 |
| photo | 写实摄影 | 实景类兜底（一般走联网实景图） |
| lineart / diagram | 手绘线稿 / 扁平信息示意 | 技术工程、结构、流程 |

### 2. 成果类型路由（17 类，自动匹配）

调研考察报告 / 旅游规划 / 行业研究 / 区域规划 → 联网实景图；
政务公文 → 扁平矢量；工程方案 → 线稿；数据报告 → 图表；
散文随笔 → 杂志编辑插画；生活文化 / 游记见闻 / 亲子教育 → 暖调手绘水彩；
科普教程 → 信息图解；技术前沿 → 科技抽象；传统文化 → 水墨国风；
品牌营销 → 3D 渲染；汇报总结 → 2.5D 商业插画。

判定：对 frontmatter + 标题 + 正文做关键词投票，得分最高者胜；全为 0 默认实景图。`--source` 覆盖配图源，`--style` 覆盖 ai 生图类型。完整表见 `references/illustration-routing.md`。

```bash
S=<技能目录>
python3 "$S/scripts/illustrate.py" styles                        # 列出 11 类生图类型 + 17 类成果路由
python3 "$S/scripts/illustrate.py" route 成稿.md --theme sunset  # 判定成果类型/配图源/生图类型/色卡
python3 "$S/scripts/illustrate.py" plan 成稿.md --source ai --style editorial --theme sunset
```

### 3. 配图色调与主题色一致

- **ai 通道**：提示词自动注入文档主题色卡（主色 accent、辅色 accent2、底色 bg），要求低饱和、与全文色调统一、无冲突高饱和杂色；
- **线稿通道**：`--palette auto` 按主题色温就近映射（sunset→terracotta、forest/botanical→olive、golden→amber、desert→rosewood、冷色/深色主题→ink）；
- **实景图通道**：以真实性为先，不强制改色，由版面与图注统一观感。
- `--theme` 传配色 id（如 sunset），未指定时从成稿 frontmatter 的 `theme:` 读取。

### 4. 综合美观与画质

- 统一 16:9 横图（1536×864），提示词含「主体突出、留白充足、层次清晰、光线柔和统一」；
- 同一文档所有配图使用同一生图类型，整册风格统一，不混搭；
- 画质优先：阈值 900KB、长边 ≤1920、q92，低于阈值不压缩；3—4 张高清配图时含图页 `--max-kb` 可用 2400。

### 5. 验收

`illustrate.py styles/route` 给出预期类型与色卡；`check` PASS；`md2report --check` `FAIL=0`；ai 图带角标、实景图不带。

## 三十一、v6.0.0 无障碍 / 分享 / 打印 / 交互细节与动画增强（2026-09-24）

### 1. 无障碍（WCAG）
- 焦点可见：全站 `:focus-visible` 统一焦点环（`--accent` 2px + offset 2px），键盘 Tab 可见当前位置。
- 跳至正文：`<a class="skip-link" href="#content">跳至正文</a>`，获焦时左上角出现。
- 表格语义：生成表头均带 `scope="col"`（split_table / :::gap / 来源表 / 缺口表）。
- 当前位置：scroll-spy 高亮章同步写 `aria-current="true"`（读屏可感知）。
- 既有基础：图表 SVG `role="img"` + `aria-label`、交互按钮 `aria-label/expanded/controls/pressed`。

### 2. 分享与元信息
- `<meta name="description">` 与 Open Graph（og:type/title/description/locale）→ 转发微信/飞书/IM 显示标题卡。
- `<meta name="theme-color">` 随主题色动态更新（apply 时写回）。
- 内联 SVG favicon（data URI，零外链，标签页不再默认图标）。

### 3. 打印与 PDF
- `@page { size: A4; margin: 16mm 13mm 16mm }` 定义版心。
- 整章避断改为**局部避断**（卡片/图/表/引用/法条卡），长章节不再产生大片空白；`thead { display: table-header-group }` 跨页重复表头。
- 外链打印展开 URL（`a[href^="http"]::after { content: " (" attr(href) ")" }`），便于纸质回溯。

### 4. 交互
- 图片点击放大（lightbox）：`.fig img / .g-cell img / .fig-diagram img` 可点击放大，Esc 关闭，无图不注入。
- 抽屉目录搜索：移动端目录面板顶部搜索框实时过滤章节，无结果给出提示。
- 长表点击排序：数值列自动加 `data-sort`，点击表头升降序（键盘 Enter/Space 可触发）。
- 跟随系统深色：无用户选择时按 `prefers-color-scheme` 自动选深色主题，用户点选后记忆其选择。

### 5. 动画增强
- 环形图分段错峰淡入（`.donut-seg`）；时间轴节点弹出（`.tl-item::before` scale）。
- 目录胶囊背景/颜色过渡；章节展开淡入（`unfoldIn`）；配色切换时组件颜色过渡。
- 返回顶部淡入淡出 + 上移；进度条宽度线性过渡；hero 装饰缓慢漂浮（`translate` 属性，保留 rotate）。
- 安全：`prefers-reduced-motion` 与 `@media print` 下全部还原静态。

### 6. 自检新增
`html_check.py` 新增 7 项提示校验：FOCUS_VISIBLE / SKIP_LINK / OG_META / THEME_COLOR / TH_SCOPE / ARIA_CURRENT / PAGE_RULE；`ANCHORS` 扩展为认可任意元素 id（如跳转锚点 `#content`）。

### 7. 图表围栏扩展
`:::chart` 由 bar / donut 扩展为 **bar / donut / line / area**（折线、面积图为内联 SVG，随主题换色）。

## 三十二、v6.2.0 设计纪律层与版式母题（2026-09-24 · frontend-design 方法论）

### 背景
借鉴 Anthropic 官方 frontend-design 技能对 AI 生成页面「模板痕迹」的判定（统一圆角套装 / 每节渐入 / Hero 恒为大数字+小标签+渐变 / 宽字距全大写标签 / 与内容无关的编号），在既有十套配色之上新增一层**设计纪律层**，把「如何排版与用色」从「用什么颜色」中解耦。

### 版式母题（`--motif`，与十套配色正交）

| id | 名称 | 圆角 | 强调 | 动效 | Hero | 适用 |
|---|---|---|---|---|---|---|
| editorial（默认） | 编辑长文 | 直角 | 单色 | 一次编排 | 衬线大字标题＋规则线 | 年度报告、调研、长文 |
| blueprint | 工程图纸 | 直角 | 单色 | 无动效 | 图纸式标题栏 | 工艺说明、技术方案 |
| narrative | 数据叙事 | 极微圆角 | 单色 | 一次编排 | 大留白、数据为主 | 经营分析、数据故事 |
| classic | 经典报告 | 圆润 | 渐变 | 错峰入场 | 渐变 Hero＋装饰 | 汇报、宣发（兼容旧观感） |

用法：`python3 scripts/md2report.py in.md -o out.html --theme ocean --motif editorial`（`build_report.py` 同名参数）。

### 纪律层做了什么
1. **圆角分级收口**：全部容器改走 `--ds-r-sm/md/lg/pill`，不再「一个圆角套所有层级」；直角母题下 pill 亦收为直角。
2. **强调单色化**：装饰性 `linear-gradient(accent→accent2)` 默认关闭，强调改单色 `var(--accent)`；classic 母题保留渐变。
3. **动效按母题**：`orchestrated`＝整页一次编排（取消逐节 fade-and-slide-up）；`off`＝无动效；`staggered`＝旧错峰行为。
4. **字体配对与模块化字阶**：`--font-display/body/mono` 三角色 ＋ 1.25 比率字阶 `--fs-xs…4xl`。
5. **Hero 去默认化**：非 classic 母题隐藏几何装饰块与波浪；editorial 走「衬线大标题＋规则线」、blueprint 走「图纸边栏」、narrative 走「大留白」。

### 新增脚本
- `scripts/motifs.py`：母题定义与纪律层 CSS（`list` / `css --motif X` / `json`）。
- `scripts/motif_check.py`：设计纪律体检（ROUNDING / GRADIENT / ENTRANCE / CAPS / MOTIF 五项，OK/WARN 级、不阻断），`--strict` 时 WARN 退出码 1。

### 分发与回归
`dist_htmlbase.py --apply` 全量分发至 66 个内嵌基座的技能，漂移 0；副本回归（settlement-audit / env-three-waste-test-report / deep-research）FAIL=0，设计纪律四项全 OK。

### 工程约束
- 纪律层 CSS 追加在主题 CSS **之后**并以 `!important` 覆盖，保证优先级；
- 母题模块缺失时 `build_report` 优雅降级（不报错、回退无母题行为）；
- 不改变既有 `html_check` 口径、不新增 FAIL 级校验，向后兼容。

