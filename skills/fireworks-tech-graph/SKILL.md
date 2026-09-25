---
name: fireworks-tech-graph
version: 1.2.0
author: 清风明月
display_name: 技术图绘制官
slug: qf-fireworks-tech-graph
category: 科技
tags: [技术图, 架构图, 流程图, 序列图, SVG, PNG, 思维导图, 类图, ER图, 状态机图, 网络拓扑, UML]
description: 生产级技术图绘制官，把文字描述的技术结构渲染成可交付的 SVG 与 PNG 图件，覆盖架构图、数据流图、流程图、序列图、Agent 架构图、记忆架构图、思维导图、类图、用例图、状态机图、ER 图、网络拓扑图、对比矩阵与时间线共 14 类图型，内置 UML 14 类覆盖映射、形状词汇表、箭头语义系统、正交路由、标签背景防遮挡、8px 网格对齐、7 套视觉风格（Flat Icon / Dark Terminal / Blueprint / Notion Clean / Glassmorphism / Claude Official / OpenAI Official）与写入前五项自检、Quick Fix 修复协议。当用户说 画图、帮我画个架构图、生成流程图、画序列图、出个技术图、画思维导图、画网络拓扑、画 ER 图、画状态机图、可视化一下系统结构、做个对比矩阵、画个时间线、generate diagram、draw diagram、visualize architecture、create flowchart、sequence diagram、mind map、ER diagram、network topology 时触发。不适用于照片编辑与修图、位图手绘风格插画、三维渲染与物理仿真、带动画或交互逻辑的图表（D3.js、Plotly、SMIL）、需要实时数据绑定的动态大屏。
---

# 技术图绘制官 · Fireworks Tech Graph

把文字描述的技术结构渲染成生产级 SVG 图件并导出 PNG 的专用技能。默认风格为 Flat Icon，另备 6 套可选风格；输出为纯静态 SVG，不依赖外部字体文件与外部样式表，可用任意浏览器打开，也可用命令行无损转为高分辨率 PNG。

## 一、技能定位

**本技能做**：判读用户描述 → 归类型 → 提炼层/节点/连线 → 选风格 → 排布局 → 写 SVG → 写入前自检 → 命令行校验 → 导出 PNG → 报告文件路径。

**本技能不做**：图外内容创作、文案撰写、数据核实、位图修图、三维渲染、交互动画。

适用图型共 14 类：架构图、数据流图、流程图、序列图、Agent 架构图、记忆架构图、思维导图、类图、用例图、状态机图、ER 图、网络拓扑图、对比矩阵、时间线/Gantt。

## 二、触发场景与触发词

**中文触发词**：画图、帮我画、生成图、出图、做个图、画架构图、画流程图、画序列图、画时序图、画思维导图、画 ER 图、画类图、画状态机图、画网络拓扑图、可视化一下、技术图、技术架构图、系统结构图、流程图怎么画。

**英文触发词**：generate diagram、draw diagram、visualize、visualize architecture、create flowchart、sequence diagram、mind map、class diagram、ER diagram、state machine diagram、network topology、timeline chart。

**边界**：仅处理二维静态技术图。需要交互逻辑、动画、三维效果、照片级写实渲染的请求不在范围内，遇到此类请求应当说明边界并给出替代路径（例如改用前端图表库或绘图软件）。

## 三、使用示例

### 示例 1 · 三层微服务架构图

用户说："帮我画个架构图，最上面是用户端和定时任务，中间是网关和订单服务，最下面接 MySQL 和 Redis，用蓝图风格。"

处置：归类型为架构图 → 分成接入层/服务层/数据层三行 → 加载 `references/style-3-blueprint.md` 取蓝色技术风令牌 → 执行渲染命令。

```bash
python3 scripts/render_diagram.py --spec specs/order-arch.json --out out/order-arch-style3.svg --style 3 --width 1920 --png
python3 scripts/check_svg.py out/order-arch-style3.svg --cjk
```

交付：`out/order-arch-style3.svg` 与 `out/order-arch-style3.png`（1920px 宽）。

### 示例 2 · 数据库 ER 图

用户说："把订单、订单明细、商品、客户四张表画成 ER 图，标出主外键和一对多关系。"

处置：归类型为 ER 图 → 实体矩形最小宽度 160px，主键加下划线，外键标 (FK)，关系用菱形并标注基数 `1` 与 `0..*` → 风格取 4 Notion Clean（便于贴进 Confluence 与 Notion）。

### 示例 3 · 时序图并切换风格

用户说："画一张下单支付的时序图，参与者是用户、订单服务、支付网关、银行，然后换成暗色终端风格再出一份。"

处置：参与者为垂直生命线，消息按时间自上而下，激活框用细填充矩形，alt/loop 帧用虚线矩形框并在左上角标注；第一版用 `references/style-1-flat-icon.md`，第二版用 `references/style-2-dark-terminal.md`，ViewBox 高度按 `80 + 消息数 × 50` 计算。

```bash
python3 scripts/render_diagram.py --spec specs/pay-seq.json --out out/pay-seq-style1.svg --style 1
python3 scripts/render_diagram.py --spec specs/pay-seq.json --out "out/【待填：项目代号】-pay-seq-style2.svg" --style 2 --png
```

## 四、执行工作流（九步，按序执行）

1. **判读图型** —— 输入：用户自然语言描述；动作：对照 14 类图型清单归类，识别主图型与是否含子图；输出：图型名称与需要加载的参考文件清单。
2. **提炼结构** —— 输入：描述文本；动作：抽出层（layer）、节点（node）、连线（edge）、语义分组；输出：可写成 JSON 规格的层/节点/边三元结构。规格缺字段时按 `id`、`label`、`sub` 三项最小集补齐，缺 `from`/`to` 的边直接丢弃。
3. **选定风格** —— 输入：使用场景（文档/博客/汇报/路演）；动作：查 `references/style-adaptation-matrix.md` 的图型×风格适配表，默认取 1 Flat Icon，用户指定则以其为准；输出：风格编号 1—7 与对应 `references/style-1-flat-icon.md` 等令牌文件。
4. **排布布局** —— 输入：结构三元组与风格；动作：按图型套用布局规则（分层图自上而下、序列图垂直生命线、思维导图中心辐射、矩阵按行列）；所有节点中心对齐 8px 基础网格，同层水平间距 120px，层间垂直间距 120px；输出：每个节点的 `x`、`y` 坐标。
5. **指派形状与箭头** —— 输入：节点语义与连线语义；动作：查形状词汇表把语义映射为形状，把连线映射为 4 类以内箭头语义色；输出：形状与箭头样式映射表。
6. **生成 SVG** —— 输入：坐标、形状、风格令牌；动作：按行数选择生成方式（少于 150 行直接写文件；150—300 行用 Python 渲染器；300 行以上分块写入），用 `scripts/render_diagram.py` 出图；输出：UTF-8 编码的 `.svg` 文件。
7. **写入前五项自检** —— 输入：SVG 文本；动作：逐项核对标签平衡、属性引号、特殊字符转义、marker 引用、闭合标签；任一项不通过先修复再写入；输出：自检通过标记。
8. **命令行校验与导出** —— 输入：SVG 文件；动作：运行 `scripts/check_svg.py` 做静态复核，通过后用 `rsvg-convert` 导 PNG；命令不可用时按降级路径处理；输出：PNG 文件或明确的依赖缺失说明。
9. **报告交付** —— 输入：产物路径；动作：确认文件真实存在且 PNG 非空，列出 SVG 与 PNG 的绝对路径、风格编号、画布尺寸；输出：交付清单。

```bash
# 步骤 6-8 的完整命令链
python3 scripts/render_diagram.py --demo --out out/demo.svg --style 1 --png
python3 scripts/check_svg.py out/demo.svg --cjk --json
bash scripts/validate-svg.sh out/demo.svg
bash scripts/generate-diagram.sh -t architecture -s 1 -o out/arch.svg -w 2400
```

## 五、图表类型与布局要点

| 图型 | 关键布局规则 | 典型 ViewBox |
|------|-------------|-------------|
| 架构图 | 水平分层，层间距 120px，虚线圆角矩形容器分组 | `0 0 960 600` |
| 数据流图 | 每条箭头标注数据类型，主数据路径加粗至 2.5px | `0 0 960 600` |
| 流程图 | 顶底优先，菱形决策、圆角矩形过程、平行四边形 I/O | `0 0 960 800` |
| 序列图 | 垂直生命线，激活框表示处理中，alt/loop 帧 | 高 = 80 + 消息数×50 |
| Agent 架构图 | 输入层/核心层/记忆层/工具层/输出层，循环箭头表示迭代 | `0 0 960 800` |
| 记忆架构图 | 读路径与写路径分色，工作记忆→短期→长期→外部存储 | `0 0 960 800` |
| 思维导图 | 中心辐射，一级分支均分 360/N 度，贝塞尔曲线连接 | `0 0 960 600` |
| 类图 | 三格矩形（类名/属性/方法），继承用空心三角箭头 | `0 0 960 600` |
| 用例图 | 系统边界居中，参与者置于边界外，参与者用火柴人 | `0 0 960 600` |
| 状态机图 | 初始态填充圆、终态双圆、转换箭头带事件与守卫条件 | `0 0 960 600` |
| ER 图 | 实体矩形 ≥160px，菱形关系，基数标注 `1` / `0..*` | `0 0 1200 600` |
| 网络拓扑 | Internet→Edge→Core→Access→Endpoints 分层 | `0 0 960 600` |
| 对比矩阵 | 列头=系统，行头=属性，行高 40px，列宽 ≥120px | 按列数自定 |
| 时间线/Gantt | X 轴为时间，Y 轴为任务，里程碑用菱形或实心圆 | `0 0 960 400` |

ViewBox 三档速查：标准 `0 0 960 600`、高堆栈 `0 0 960 800`、宽布局 `0 0 1200 600`。
节点尺寸：标准 180×90px，核心节点 1.25 倍加 3—4px 描边，次要节点标准尺寸配 2—2.5px 描边。
完整英文原文规则（含 UML 14 类覆盖映射、形状词汇表、箭头语义表、布局原则、最佳实践）见 `references/layout-rules-full.md`，速查表见 `references/diagram-types.md`。

## 六、七套视觉风格

| # | 名称 | 背景 | 适合场景 |
|---|------|------|---------|
| 1 | Flat Icon（默认） | 白色 | 博客、文档、演示 |
| 2 | Dark Terminal | `#0f0f1a` | GitHub、开发者文章 |
| 3 | Blueprint | `#0a1628` | 架构说明书、基础设施文档 |
| 4 | Notion Clean | 白色极简 | Notion、Confluence、内网 Wiki |
| 5 | Glassmorphism | 深色渐变 | 产品页、路演、主题演讲 |
| 6 | Claude Official | 暖米色 `#f8f6f3` | 对标 Anthropic 视觉体系 |
| 7 | OpenAI Official | 纯白 `#ffffff` | 对标 OpenAI 视觉体系 |

生成前按风格编号加载对应令牌文件：`references/style-1-flat-icon.md`、`references/style-2-dark-terminal.md`，依次到 `references/style-7-openai.md`。图型与风格的适配评分（优/良/差）见 `references/style-adaptation-matrix.md`；产品图标与品牌标识见 `references/icons.md`。

## 七、形状词汇与箭头语义

形状词汇表把语义固定到形状，保证跨图一致：人用圆加身体路径；模型/LLM 用圆角矩形加渐变；编排器用六边形；短期记忆用虚线圆角矩形；长期记忆用圆柱；向量库用带横线的圆柱；图数据库用三圆叠加；工具用带扳手记号的矩形；网关用单边框六边形；队列用水平管状；文档用折角矩形；决策用菱形；过程用圆角矩形；外部服务用虚线矩形；数据用平行四边形。

箭头语义按流程类型分配颜色与线型，同图不超过 4 种：

| 流程类型 | 颜色 | 线宽 | 虚线 | 含义 |
|---------|------|------|------|------|
| 主数据流 | 蓝 `#2563eb` | 2px | 无 | 主请求/响应路径 |
| 控制触发 | 橙 `#ea580c` | 1.5px | 无 | 一个系统触发另一个 |
| 记忆读 | 绿 `#059669` | 1.5px | 无 | 从存储检索 |
| 记忆写 | 绿 `#059669` | 1.5px | `5,3` | 写入/落库 |
| 异步事件 | 灰 `#6b7280` | 1.5px | `4,2` | 非阻塞、事件驱动 |
| 变换/嵌入 | 紫 `#7c3aed` | 1px | 无 | 数据变换 |
| 反馈回路 | 紫 `#7c3aed` | 1.5px 曲线 | 无 | 迭代推理回路 |

同图出现 2 种以上箭头类型时必须配图例；图例置于右上角或左下角，含箭头类型、节点类型与颜色语义。

## 八、SVG 技术规则

- ViewBox 默认 `0 0 960 600`，高堆栈 `0 0 960 800`，宽布局 `0 0 1200 600`。
- 字体用 `<style>` 内嵌或根元素 `font-family` 属性声明，禁止 `@import` 外部字体，否则渲染会断。
- 中文图必须把 `'Noto Sans CJK SC'`、`'PingFang SC'`、`'Microsoft YaHei'` 写进字体栈，否则导出 PNG 时中文缺字形。
- `<defs>` 集中放箭头 marker、渐变、滤镜、裁剪路径；箭头统一用 `<marker>` 加 `marker-end`，尺寸 `markerWidth="10" markerHeight="7"`。
- 字号下限 12px；节点主标签 16—18px，副标签 13—14px，箭头标签 12—13px，图例 11—12px，标题 24—28px。
- 投影用 `<feDropShadow>`，只给核心节点使用。
- 曲线路径用 `M x1,y1 C cx1,cy1 cx2,cy2 x2,y2`；文本可能溢出节点时加 `<clipPath>`。
- 连线连接点取节点边框中点，禁止连到四角；同向多条箭头在 Y 轴方向错开 15—20px。

## 九、SVG 写入前五项自检

🔴 **CHECKPOINT 自检门｜写入前必须逐项核对**：五项任一不通过，先修复再写文件，禁止把未通过自检的 SVG 落盘。

**规则 1 标签平衡**：统计 `<rect`、`<text`、`<g`、`<line`、`<path`、`<circle` 开标签数，与自闭合 `/>` 加对应闭标签数比对，两侧必须相等。
**规则 2 属性引号**：所有属性值必须带引号，写作 `fill="#9dd4c7"`，不得写作 `fill=#9dd4c7`。
**规则 3 特殊字符**：文本节点内不得出现未转义的 `<`、`>`、`&`，一律替换为 `&lt;`、`&gt;`、`&amp;`。
**规则 4 marker 引用**：每个 `marker-end="url(#arrow-x)"` 必须在 `<defs>` 中存在同名 `<marker id="arrow-x">`。
**规则 5 闭合标签**：文件末尾单独一行写 `</svg>`；分块写入时把闭合标签放进最后一块。

```xml
<!-- 箭头标签必须带背景矩形，避免压住节点与连线 -->
<rect x="label_x - 4" y="label_y - 14" width="label_width + 8" height="18" fill="canvas_bg" opacity="0.95"/>
<text x="label_x" y="label_y" font-size="12" text-anchor="middle">标签文字</text>
```

## 十、Quick Fix 修复协议

校验报错后按报错信息对应处置，同一错误只做一次快速修复：

| 报错信息 | 根因 | 修复动作 |
|---------|------|---------|
| `Extra content at the end of the document` | 缺少 `</svg>` 或末尾有多余内容 | 追加 `</svg>` 后重新校验 |
| `Couldn't find end of Start Tag`（第 N 行） | 属性值被截断 | 读第 N 行补全属性值 |
| `Invalid character`（第 N 行） | 文本含未转义特殊字符 | 替换为 HTML 实体 |
| `Undefined marker` | marker 引用无定义 | 在 defs 补 `<marker id="...">` |
| PNG 全白 | SVG 只有 defs 没有图形元素 | 检查图形元素是否写入 |

```bash
# 快速修复后复检一条命令链
printf '%s\n' '</svg>' >> out/broken.svg
python3 scripts/check_svg.py out/broken.svg
rsvg-convert -w 1920 out/broken.svg -o out/broken.png 2>&1
```

## 十一、失败模式与降级路径

以下为本技能在出图链路中的已知失败模式与对应处置。完整清单见 `references/failure-modes.md`。

**生成阶段**

1. 如果文字溢出节点矩形遮罩（文字被裁掉或压出边框）→ 则改用 `text-anchor="middle"` 居中，套 `<clipPath>` 裁剪，并把标签压到 3 个词以内、细节移入副标签；仍溢出则把节点放大到 1.25 倍标准尺寸。
2. 如果 SVG 渲染失败（`rsvg-convert` 报语法错误或导出空白图）→ 则先按 Quick Fix 协议做一次定向修复并重试；同一错误第 2 次出现即切换到另一种生成方式；第 3 次失败停止重试，向用户报告完整错误信息与行号，交付 SVG 源码作为兜底。
3. 如果风格不一致（图内颜色与所选风格令牌不符、混入其他风格色值）→ 则回退到默认 1 Flat Icon 重新出图，并逐项核对 `references/style-1-flat-icon.md` 中的填充色、描边色与字体栈。
4. 如果节点过多导致布局重叠（节点框相互压盖、连线穿过节点内部）→ 则启用降级策略：按语义拆成两张子图，或改为分泳道布局并把同层节点间距放宽到 80px 以上、层间距保持 120px；连线改走正交路由绕行。
5. 如果中文字体缺失（PNG 中文显示为方块或空白）→ 则在根元素 `font-family` 中补齐 `'Noto Sans CJK SC'`、`'PingFang SC'`、`'Microsoft YaHei'` 字体栈并重新导出；本机字体确实缺失时交付 SVG（浏览器端可用系统字体正常显示）。
6. 如果 `rsvg-convert` 命令不可用 → 则依次回退到 `cairosvg`、`inkscape`、ImageMagick `convert` 三个渲染后端；四个后端全部缺失时输出 SVG 并在交付说明中写明 PNG 导出依赖缺失。
7. 如果规格 JSON 非法（缺 `layers` 数组、节点缺 `id`/`label`、边引用了不存在的节点）→ 则渲染器以退出码 1 中止并打印失败原因，按报错补齐规格后重跑，不得带着非法规格继续出图。
8. 如果图内箭头语义色超过 4 种 → 则合并语义相近的箭头类型压到 4 种以内，并把合并后的语义登记进图例。
9. 如果长链路生成中断（分块写入过程中会话中断）→ 则按断点续跑：检查已写文件末尾是否已含 `</svg>`，未闭合时先补闭合标签，再按块号从断点继续，避免整图重做。
10. 如果交付目录不存在或不可写 → 则先在用户指定的父目录下创建输出目录，创建失败时改写到当前工作目录并在交付说明中标注路径变更。

## 十二、检查点清单

🔴 **CHECKPOINT A｜风格确认**：写入任何 SVG 前先确认风格编号与令牌文件已加载；用户未指定时默认 1 Flat Icon，并在交付时说明所用风格。

🔴 **CHECKPOINT B｜自检门**：五项自检全部通过才能进入命令行校验；未通过时先修复，禁止跳过。

🔴 **CHECKPOINT C｜校验门**：`scripts/check_svg.py` 与 `rsvg-convert` 均须零问题通过；有报错则先走 Quick Fix 协议，同一错误只修一次。

🔴 **CHECKPOINT D｜重试纪律**：同一错误出现 2 次立即切换生成方式；3 次均失败停止重试并报告，禁止无限循环重试。

🔴 **CHECKPOINT E｜交付前复核**：报告路径前核对 SVG 与 PNG 文件真实存在、PNG 体积大于 0、画布尺寸与风格符合约定；需要人工确认时暂停并列出待确认项。

🔴 **CHECKPOINT F｜规格变更确认**：用户在中途改变图型或风格时，先停下确认新规格再重出图，不得在旧图上叠改。

## 十三、反例与红线

以下为使用本技能时的明确禁忌与不可逾越的边界。违反红线即视为交付不合格。

### 绝对禁止

- ❌ **禁止交付缺少 `</svg>` 闭合标签的 SVG** —— 会导致校验失败与 PNG 导出异常。
- ❌ **禁止在未通过校验的情况下交付 PNG** —— 未校验的 PNG 可能整体空白或半图渲染。
- ❌ **禁止跳过风格令牌文件直接凭印象配色** —— 会产生风格漂移，颜色值与 `references/style-1-flat-icon.md` 等文件不一致。
- ❌ **禁止使用未加引号的 SVG 属性值** —— `fill=#9dd4c7` 属非法写法，必须写成 `fill="#9dd4c7"`。
- ❌ **禁止在同图使用超过 4 种箭头语义色** —— 超出后语义无法辨识，应合并相近类型。
- ❌ **禁止节点不经过 8px 网格对齐** —— 未对齐会导致节点错位、连线扭曲。
- ❌ **禁止第 3 次重试失败后继续循环** —— 必须停止并报告，不得空转。
- ❌ **禁止擅自改写用户给定的业务语义与术语** —— 节点文案只能取自用户描述，不得自造。

### 明确边界

- ❌ 不负责生成非 SVG 格式的矢量图（PDF 矢量、EPS）。
- ❌ 不负责图外内容创作与文案撰写，图中文字只取自用户描述。
- ❌ 不处理需要实时数据绑定的动态图表，本技能输出静态 SVG。
- ❌ 不处理照片编辑、位图修图、手绘风格插画。
- ❌ 不处理三维渲染与物理仿真图。
- ❌ 不处理带动画或交互逻辑的图表（D3.js、Plotly、SMIL）。

### 反模式与黑名单

- 🚫 一次性把整张复杂图写成未分块的单条超长命令（易触发截断）。
- 🚫 用 heredoc 写含大量引号的 SVG 却不做转义（易触发编码异常）。
- 🚫 先导 PNG 再补 SVG 自检（顺序颠倒，返工成本翻倍）。
- 🚫 把图例、标题、画布边距压到画布边缘 40px 以内。
- 🚫 在未确认用户业务术语前自行翻译或缩写节点名称。

## 十四、交付与输出

- 默认输出到当前目录：`./[derived-name].svg` 与 `./[derived-name].png`。
- 指定路径用 `--out` 参数，例如 `--out out/arch.svg`；PNG 宽度用 `--width`，默认 1920px（2 倍图）。
- 交付时列出 SVG 与 PNG 的绝对路径、风格编号、画布尺寸与所用渲染后端。
- PNG 后端按 `rsvg-convert` → `cairosvg` → `inkscape` → ImageMagick 顺序回退，交付说明中写明实际后端。
- 批量自检与回归用 `bash scripts/test-all-styles.sh out/`，逐套风格出图并汇总校验结果。

## 十五、资源清单

**参考文件（`references/`）**

| 文件 | 内容 |
|------|------|
| `references/diagram-types.md` | 14 类图型速查表、ViewBox 与节点尺寸规范 |
| `references/layout-rules-full.md` | 图型布局规则、UML 覆盖映射、形状词汇、箭头语义、布局原则、最佳实践（英文原文归档） |
| `references/style-adaptation-matrix.md` | 七套风格总览与图型×风格适配矩阵 |
| `references/style-1-flat-icon.md` 至 `references/style-7-openai.md` | 七套风格的精确颜色令牌、字体栈与 SVG 片段 |
| `references/style-2-dark-terminal.md`、`references/style-3-blueprint.md` | 暗色与蓝图风格令牌 |
| `references/svg-layout-best-practices.md` | 间距、连接点、正交路由、图层顺序通用规则 |
| `references/failure-modes.md` | 失败模式完整清单与处置路径 |
| `references/icons.md` | 常见产品与品牌图标画法 |

**可执行脚本（`scripts/`）**

| 脚本 | 用途 | 调用示例 |
|------|------|---------|
| `scripts/render_diagram.py` | JSON 规格 → SVG → PNG，内置 7 套风格令牌 | `python3 scripts/render_diagram.py --spec spec.json --out out/x.svg --style 3 --png` |
| `scripts/check_svg.py` | 写入前五项自检 + XML 解析 + 中文字体检查 | `python3 scripts/check_svg.py out/x.svg --cjk` |
| `scripts/generate-diagram.sh` | 生成、校验与导出的一体化 shell 入口 | `bash scripts/generate-diagram.sh -t architecture -s 1 -o out/arch.svg -w 2400` |
| `scripts/validate-svg.sh` | SVG 语法与结构校验 | `bash scripts/validate-svg.sh out/x.svg` |
| `scripts/test-all-styles.sh` | 七套风格批量出图回归测试 | `bash scripts/test-all-styles.sh out/` |
| `scripts/README.md` | 脚本参数说明与用法汇总 | — |
