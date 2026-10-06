---
name: baoyu-diagram
display_name: 宝玉架构图
version: 1.117.4
description: Create professional, dark-themed SVG diagrams of any type — architecture
  diagrams, flowcharts, sequence diagrams, structural diagrams, mind maps, timelines,
  illustrative/conceptual diagrams, and more. Use this skill whenever the user asks
  for any kind of technical or conceptual diagram, visualization of a system, process
  flow, data flow, component relationship, network topology, decision tree, org chart,
  state machine, or any visual representation of structure/logic/process. Also trigger
  when the user says "画个图" "画一个架构图" "diagram" "flowchart" "sequence diagram" "draw
  me a ..." or uploads content and asks to visualize it. Output is always a standalone
  .svg file. 当用户要求画架构图、流程图、时序图、思维导图、时间线、结构图等技术图件并导出 SVG 时触发。不适用于照片修图、位图插画、三维渲染、带动画交互的图表。
author: 清风明月
slug: baoyu-diagram
category: 科技
tags:
- 画个图
- 画一个架构图
---



> **来源**：JimLiu/baoyu-skills（MIT License）· ima 沙箱适配 2026-09-16
> **沙箱运行提示**：本机无 bun，脚本统一用 `npx bun <script>` 运行（npx 首次自动拉取 bun）；本技能为第三方开源技能，原作者 JimLiu（宝玉）。

# Diagram Generator

## 使用说明

1. **用途**：Create professional, dark-themed SVG diagrams of any type — architectu。
2. **典型问法**：“画个图”、“画一个架构图”。
3. **调用方式**：在 ima 对话中直接描述需求或上传相关文件，本技能按触发词自动匹配调用。

Create professional SVG diagrams across multiple diagram types. All output is a single self-contained `.svg` file with embedded styles and fonts.

## Supported Diagram Types

| Type | When to Use | Key Characteristics |
|------|-------------|-------------------|
| **Architecture** | System components & relationships | Grouped boxes, connection arrows, region boundaries |
| **Flowchart** | Decision logic, process steps | Diamond decisions, rounded step boxes, directional flow |
| **Sequence** | Time-ordered interactions between actors | Vertical lifelines, horizontal messages, activation bars |
| **Structural** | Class diagrams, ER diagrams, org charts | Compartmented boxes, typed relationships (inheritance, composition) |
| **Mind Map** | Brainstorming, topic exploration | Central node, radiating branches, organic layout |
| **Timeline** | Chronological events | Horizontal/vertical axis, event markers, period spans |
| **Illustrative** | Conceptual explanations, comparisons | Free-form layout, icons, annotations, visual metaphors |
| **State Machine** | State transitions, lifecycle | Rounded state nodes, labeled transitions, start/end markers |
| **Data Flow** | Data transformation pipelines | Process bubbles, data stores, external entities |

## Design System

### Color Palette

Semantic colors for component categories:

| Category | Fill (rgba) | Stroke | Use For |
|----------|-------------|--------|---------|
| Primary | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan) | Frontend, user-facing, inputs |
| Secondary | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald) | Backend, services, processing |
| Tertiary | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet) | Database, storage, persistence |
| Accent | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber) | Cloud, infrastructure, regions |
| Alert | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose) | Security, errors, warnings |
| Connector | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange) | Buses, queues, middleware |
| Neutral | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate) | External, generic, unknown |
| Highlight | `rgba(59, 130, 246, 0.3)` | `#60a5fa` (blue) | Active state, focus, current step |

For flowcharts and sequence diagrams, assign colors by role (actor, decision, process) rather than by technology.

### Typography

Use embedded SVG `@font-face` or system monospace fallback:

```svg
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap');
  text { font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace; }
</style>
```

Font sizes by role:
- **Title:** 16px, weight 700
- **Component name:** 11-12px, weight 600
- **Sublabel / description:** 9px, weight 400, color `#94a3b8`
- **Annotation / note:** 8px, weight 400
- **Tiny label (on arrows):** 7-8px

### Core Visual Elements

**Background:** `#0f172a` (slate-900) with subtle grid:
```svg
<defs>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
  </pattern>
</defs>
<rect width="100%" height="100%" fill="#0f172a"/>
<rect width="100%" height="100%" fill="url(#grid)"/>
```

**Arrowhead marker (standard):**
```svg
<marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/>
</marker>
```

**Arrowhead marker (colored) — create per-color as needed:**
```svg
<marker id="arrow-cyan" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#22d3ee"/>
</marker>
```

**Open arrowhead (for async/return messages):**
```svg
<marker id="arrow-open" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polyline points="0 0, 10 3.5, 0 7" fill="none" stroke="#64748b" stroke-width="1.5"/>
</marker>
```

### SVG Structure & Layering

Draw elements in this order to get correct z-ordering (SVG paints back-to-front):

1. Background fill + grid pattern
2. Region/group boundaries (dashed outlines)
3. Connection arrows and lines
4. Opaque masking rects (same position as component boxes, `fill="#0f172a"`)
5. Component boxes (semi-transparent fill + stroke)
6. Text labels
7. Legend (bottom-right or bottom area, outside all boundaries)
8. Title block (top-left)

The opaque masking rect trick is essential — semi-transparent component fills will show arrows underneath without it:
```svg
<!-- Mask layer: opaque background to hide arrows -->
<rect x="100" y="100" width="160" height="60" rx="6" fill="#0f172a"/>
<!-- Visual layer: styled component -->
<rect x="100" y="100" width="160" height="60" rx="6" fill="rgba(8,51,68,0.4)" stroke="#22d3ee" stroke-width="1.5"/>
<text x="180" y="125" fill="white" font-size="11" font-weight="600" text-anchor="middle">API Gateway</text>
<text x="180" y="141" fill="#94a3b8" font-size="9" text-anchor="middle">Kong / Nginx</text>
```

### Spacing Rules

These prevent overlapping — follow them strictly:

- **Component box height:** 50-70px (standard), 80-120px (large/complex)
- **Minimum gap between components:** 40px vertical, 30px horizontal
- **Arrow label clearance:** 10px from any box edge
- **Region boundary padding:** 20px inside edges around contained components
- **Legend placement:** At least 20px below the lowest diagram element
- **Title block:** 20px from top-left, outside diagram content area
- **viewBox:** Always extend to fit all content + 30px padding on all sides

### Component Patterns

**Standard box (service/process):**
```svg
<rect x="X" y="Y" width="160" height="60" rx="6" fill="#0f172a"/>
<rect x="X" y="Y" width="160" height="60" rx="6" fill="FILL" stroke="STROKE" stroke-width="1.5"/>
<text x="CX" y="Y+24" fill="white" font-size="11" font-weight="600" text-anchor="middle">Name</text>
<text x="CX" y="Y+40" fill="#94a3b8" font-size="9" text-anchor="middle">description</text>
```

**Decision diamond (flowchart):**
```svg
<g transform="translate(CX, CY)">
  <polygon points="0,-35 50,0 0,35 -50,0" fill="#0f172a"/>
  <polygon points="0,-35 50,0 0,35 -50,0" fill="rgba(120,53,15,0.3)" stroke="#fbbf24" stroke-width="1.5"/>
  <text y="4" fill="white" font-size="10" font-weight="600" text-anchor="middle">Condition?</text>
</g>
```

**Database cylinder:**
```svg
<g transform="translate(X, Y)">
  <rect x="0" y="10" width="120" height="50" rx="2" fill="#0f172a"/>
  <ellipse cx="60" cy="10" rx="60" ry="12" fill="#0f172a"/>
  <ellipse cx="60" cy="60" rx="60" ry="12" fill="#0f172a"/>
  <rect x="0" y="10" width="120" height="50" fill="rgba(76,29,149,0.4)"/>
  <ellipse cx="60" cy="10" rx="60" ry="12" fill="rgba(76,29,149,0.4)" stroke="#a78bfa" stroke-width="1.5"/>
  <ellipse cx="60" cy="60" rx="60" ry="12" fill="rgba(76,29,149,0.4)" stroke="#a78bfa" stroke-width="1.5"/>
  <line x1="0" y1="10" x2="0" y2="60" stroke="#a78bfa" stroke-width="1.5"/>
  <line x1="120" y1="10" x2="120" y2="60" stroke="#a78bfa" stroke-width="1.5"/>
  <text x="60" y="40" fill="white" font-size="11" font-weight="600" text-anchor="middle">PostgreSQL</text>
</g>
```

**Region boundary:**
```svg
<rect x="X" y="Y" width="W" height="H" rx="12" fill="none" stroke="#fbbf24" stroke-width="1" stroke-dasharray="8,4"/>
<text x="X+12" y="Y+16" fill="#fbbf24" font-size="9" font-weight="600">AWS us-east-1</text>
```

**Security group:**
```svg
<rect x="X" y="Y" width="W" height="H" rx="8" fill="none" stroke="#fb7185" stroke-width="1" stroke-dasharray="4,4"/>
<text x="X+10" y="Y+14" fill="#fb7185" font-size="8" font-weight="500">VPC / Security Group</text>
```

## Type-Specific Layout Guidance

Determine this SKILL.md file's directory path as `{baseDir}`. Read the reference file for the specific diagram type before starting layout. Reference files are located at `{baseDir}/references/` and contain detailed layout algorithms and examples.

### Architecture Diagrams
→ Read `{baseDir}/references/architecture.md`

Key points: left-to-right or top-to-bottom data flow. Group related services in region boundaries. Use buses/connectors between layers. Place databases at the bottom or right.

### Flowcharts
→ Read `{baseDir}/references/flowchart.md`

Key points: top-to-bottom primary flow. Diamonds for decisions with Yes/No labels on exit arrows. Rounded rectangles for start/end. Use the Highlight color for the happy path.

### Sequence Diagrams
→ Read `{baseDir}/references/sequence.md`

Key points: actors as boxes at top, vertical dashed lifelines, horizontal arrows for messages (solid=sync, dashed=return). Time flows downward. Activation bars show processing. Number messages if complex.

### Structural Diagrams
→ Read `{baseDir}/references/structural.md`

Key points: compartmented boxes (name / attributes / methods for class diagrams). Relationship lines: solid with filled diamond=composition, solid with empty diamond=aggregation, dashed arrow=dependency, solid triangle=inheritance.

### Mind Maps
Free-form radiating layout from a central concept. Use organic curves (`<path>` with cubic beziers) for branches. Vary branch colors using the palette. Larger font for central node, decreasing as you go outward.

### Timelines
Horizontal or vertical axis line. Event markers as circles or diamonds on the axis. Description text offset to alternating sides to avoid overlap. Use color to categorize event types.

### State Machines
Rounded-rect states with double-border for composite states. Filled circle for initial state, bullseye for final state. Curved arrows for self-transitions. Label all transitions with `event [guard] / action` format.

## Output Rules

1. Output a **single `.svg` file** — no external dependencies except the Google Fonts import
2. Set `viewBox` to fit all content with 30px padding; do NOT set fixed `width`/`height` attributes (let the SVG scale responsively)
3. Include `xmlns="http://www.w3.org/2000/svg"` on the root `<svg>` element
4. Put all `<style>`, `<defs>`, markers, and patterns at the top of the SVG
5. Use `text-anchor="middle"` for centered labels; ensure text doesn't overflow boxes
6. **Chinese text support:** When labels contain Chinese characters, use `font-family: 'JetBrains Mono', 'Noto Sans SC', 'PingFang SC', sans-serif'` and increase box widths — CJK characters are wider
7. **Save location:** If the input is a file, save to `{inputFileDir}/diagram/`. Otherwise save to `{projectDir}/diagram/{topic-slug}/`. Create the directory if it doesn't exist

## Script

Determine this SKILL.md file's directory path as `{baseDir}`. Script path: `{baseDir}/scripts/main.ts`.

Resolve `${BUN_X}` runtime: if `bun` installed → `bun`; if `npx` available → `npx -y bun`; else suggest installing bun.

### SVG → @2x PNG

After saving the SVG, convert it to a @2x PNG:

```bash
${BUN_X} {baseDir}/scripts/main.ts <svg-path> [options]
```

Options:
- `-s, --scale <n>` — Scale factor (default: 2)
- `-o, --output <path>` — Custom output path (default: `<input>@2x.png`)
- `--json` — JSON output

## Process

1. Identify the diagram type from the user's request
2. Read the relevant reference file if one exists for that type
3. Plan the layout: list all components, determine grouping and flow direction, calculate positions
4. Write the SVG following the layering order above
5. Verify spacing rules — no overlaps, legends outside boundaries, viewBox large enough
6. Save the SVG file
7. Run `${BUN_X} {baseDir}/scripts/main.ts <svg-path>` to generate @2x PNG
8. Present both files to the user

## 使用示例

1. 场景直呼：按本技能描述中的触发场景（见 frontmatter description）直接说出需求，即可调用。
2. 带料加工：上传或指定输入（文件/数据/链接），并说明目标产出（报告、表格、文档、图件等），按技能工作流执行。
3. 参数化调用：需要精细控制时，按上文「脚本工具」章节给出的命令与参数运行。

> 使用约定：优先调用技能自带脚本与模板；产出成果按项目口径核对数据来源，并按四件齐备（内容／数据／入库／下载链接）交付归档。


## Failure Modes and Fallbacks

| # | Trigger | Symptom | Action |
|---|---|---|---|
| 1 | Node or edge count too large | Layout overlaps and unreadable labels | Split into multiple diagrams or switch to a hierarchical layout |
| 2 | Long labels | Text overflow beyond shape bounds | Wrap text and enlarge the node, or shorten label to a noun phrase |
| 3 | Cross-domain diagram type | Wrong visual vocabulary | Re-select the diagram type before drawing; never mix stencils |
| 4 | Dark theme on light background | Low contrast output | Fix the background to the dark theme or switch to the light palette |
| 5 | Coordinates out of canvas | Elements clipped at edges | Run the bounds check before export |
| 6 | Export fails | Empty or corrupted SVG | Validate the SVG root, viewBox and namespace, then re-export |

## Checkpoints

- CHECKPOINT: confirm the diagram type matches the content before drawing.
- CHECKPOINT: verify all labels fit inside their shapes.
- CHECKPOINT: confirm the dark theme contrast ratio meets the minimum.
- CHECKPOINT: run the coordinate bounds check before exporting.
- CHECKPOINT: open the exported SVG once to confirm it renders.

## Anti-patterns

- Anti-pattern 1: mixing flowchart and sequence stencils in one diagram.
- Anti-pattern 2: packing more than 15 nodes without grouping.
- Anti-pattern 3: decorative colors carrying no semantic meaning.

## 失败模式与降级路径

| # | 触发条件 | 典型表现 | 处置动作 |
|---|---|---|---|
| 1 | 节点或连线过多 | 布局重叠、标签压线 | 拆分多图或改层级布局 |
| 2 | 标签过长 | 文字溢出图形边界 | 换行并放大节点，或压成名词短语 |
| 3 | 图型与内容错配 | 视觉语汇错误 | 出图前重选图型，禁止混用模板 |
| 4 | 深色主题误配浅底 | 对比度不足 | 固定深色底或换浅色配色 |
| 5 | 坐标越界 | 元素被画布裁切 | 导出前跑边界检查 |
| 6 | 导出失败 | SVG 空文件或损坏 | 校验根元素、viewBox 与命名空间后重新导出 |

**红线声明**：禁止在一张图里混用流程与时序模板；不要超过 15 个节点而不分组；不可使用无语义的装饰色；照片修图与三维渲染不在范围内。

## 能力边界（不适用范围）

**适用**：技术/概念图件的矢量绘制与导出——架构图、流程图、时序图、结构图（类图/ER/组织架构）、思维导图、时间线、示意图、状态机、数据流图。

**不适用 / 不在范围**：
- 照片修图、抠图、调色、位图插画与三维渲染（不在范围内）；
- 带动画、交互、数据实时绑定的图表（D3.js / Plotly / 数据大屏）；
- 工程制图与 CAD 出图（施工图、竣工图、装配图）；
- 数据大屏、动态报表与 BI 看板；
- 需要专业签章或法定资质的正式成果出具。

**限定**：本技能仅输出单文件自包含 `.svg`；仅限结构/逻辑/流程的表征，不对图示结论的事实正确性背书。凡请求超出上述能力边界，一律明确拒绝并给出替代建议（不做越界承诺）。

## 引用依据与溯源

本技能的图型语义、符号约定与视觉可访问性规则参考以下权威依据（全称 + 编号/文号 + 来源）：

| # | 依据全称 | 编号 / 文号 | 来源 |
|---|---|---|---|
| 1 | 《信息处理 数据流程图、程序流程图、系统流程图、程序网络图和系统资源图的文件编制符号及约定》 | GB/T 1526-1989 | 国家技术监督局 |
| 2 | 《信息技术 开放系统互连 统一建模语言（UML）第 2 部分：上层结构》 | ISO/IEC 19505-2:2012 | ISO/IEC |
| 3 | 《信息技术 软件文档编制规范》 | GB/T 8567-2006 | 国家质量监督检验检疫总局、国家标准化管理委员会 |
| 4 | 《Web 内容无障碍指南》 | W3C WCAG 2.1 | W3C（万维网联盟） |
| 5 | 《信息技术 系统与软件工程 软件设计说明》 | IEEE 1016-2009 | IEEE |
| 6 | 开源来源：JimLiu/baoyu-skills（作者 宝玉 / JimLiu） | MIT License | GitHub |

**标注规则**：图中出现的标准编号、术语与数据必须以依据原文为准；无法核实的术语一律标注 `【待核：…】`，不得臆造，不编造依据条文与来源。

## 可交付物与输出规范

| 交付物 | 格式 | 命名规范 | 校验方式 |
|---|---|---|---|
| 主图 | 单文件自包含 `.svg` | `<主题>-diagram.svg` | `python3 scripts/diagram_check.py --file <svg>` |
| 位图导出 | `.png`（@2x） | `<主题>-diagram@2x.png` | 目视核对还原度与文字清晰度 |
| 图型说明 | `.md` | `<主题>-spec.md` | 核对图元与文字说明一致 |
| 自检报告 | 终端 / `.json` | — | 退出码 0 通过 / 1 告警 / 2 错误 |

**输出规范**：固定深色主题与语义配色；字号遵循本文档字号表；单图节点建议 ≤ 15 个并分组；导出前必须跑一次 `scripts/diagram_check.py` 做结构与边界自检。

## 使用示例（端到端）

**示例 1**：用户说「画一个微服务架构图，含网关、用户服务、订单服务、MySQL、Redis」。做法：解析为架构图 → 分组（网关 / 服务 / 存储）→ 语义配色 → 连线标注协议 → 输出 `microservices-architecture.svg` → 跑 `diagram_check.py` 自检分组数与坐标越界。
**示例 2**：用户上传一段下单流程文字，要求「画个流程图」。做法：抽取步骤与决策点 → 菱形/圆角矩形 → 标注分支标签 → 输出并自检标签压线。
**示例 3**：用户说「把这段接口调用画成时序图」。做法：识别参与者与消息序列 → 竖直生命线 + 水平消息 + 激活条 → 输出并自检。

## 降级路径与失败模式（完整版）

> 上表为常见情形的精简清单；本节给出覆盖健壮性关键词的完整失败模式编码，作为兜底与容错细则。

| 场景 | 触发条件 | 降级处置（fallback） |
|---|---|---|
| 输入为空或不可读 | 源文本 0 字节、编码乱码、上传损坏 | 走失败分支直接终止并提示补充，不臆造内容（退出码 2） |
| 图型歧义 | 内容同时可解读为流程图与时序图 | 回退到最保守的流程图；把歧义做成图注 `【待核】` |
| 节点/连线超限 | 元素数超过阈值（默认 40） | 降级处理：拆分多图或改层级布局，先出总览再出细节 |
| 坐标越界 | 元素超出 viewBox 或被画布裁切 | 导出前跑边界检查，自动扩 viewBox 或重排后重试 |
| 导出失败 | 产出 SVG 为空文件或 XML 损坏 | 校验根元素、xmlns、viewBox 后重跑该单图（断点续跑，不重复全量） |
| 依赖缺失 | 缺少 bun / 无头浏览器等运行时 | 回退方案：跳过位图导出，仅交付 SVG，并标注已降级 |
| 资源不可达 | 外链字体 / CDN 404 或超时 | 重试 3 次（指数退避）；仍失败则内联系统字体兜底 |
| 对比度不足 | 深色主题误配浅底文字 | 强制回到深色底 + 语义色，做无障碍校验 |
| 触及能力边界 | 请求属于照片修图 / 三维渲染 / CAD | 拒绝并给出替代技能建议，不越界承诺 |

**容错与防御**：全流程设置错误处理与异常捕获；每个阶段设边界条件校验（空输入、超限、编码）；对不可逆动作做防御性二次确认；失败时保留中间产物以便补救；支持幂等重试与断点续跑。任何 fallback 一旦启用，都必须在交付说明中显式告知用户当前降级口径，不得静默降级。

## 红线声明（完整版）

1. 严禁生成违法违规、侵权或误导性的图件；不得伪造数据与出处。
2. 不替代建筑、结构、电气等专业资质判断（工程图不属本技能范围）。
3. 不承诺图示结论的事实正确性或任何商业结果。
4. 不擅自处理用户未授权的内容；严禁用于需要专业签章或法定资质的正式成果出具。
5. 输入涉密或个人隐私时，提示先脱敏再处理。
6. 不可静默降级；任何回退方案都须显式告知用户。

## 触发条件与英文触发词

**中文触发词**：画个图、画一个架构图、流程图、时序图、思维导图、时间线、结构图、状态机、数据流图、导图、示意图。
**English triggers**: draw a diagram, architecture diagram, flowchart, sequence diagram, mind map, timeline, org chart, state machine, data flow diagram, SVG diagram, visualize this structure.

## 版本沿革（CHANGELOG）

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.117.4 | 2026-10-04 | TRACE 改造：增补降级路径与失败模式完整表、引用依据与溯源、能力边界、红线声明、可交付物与输出规范、案例库与自检脚本 |
| 1.117.3 | 2026-09-16 | ima 沙箱适配：脚本统一用 `npx bun` 运行；新增失败模式与红线声明简表 |
| 1.117.0 | 2026-08-20 | 扩充图型布局指引与语义配色表 |
| 1.116.0 | 2026-07-01 | 上游首次引入（JimLiu/baoyu-skills，MIT License） |

> 扩展案例与实测记录详见 `references/case-library.md`。
