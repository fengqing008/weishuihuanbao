---
name: qf-process-manual
display_name: 结算SOP生成
version: 2.3.0
description: '工程结算SOP（标准操作程序/规程）编制与流程图生成器——基于某PPP项目实战蒸馏。

  触发场景：编制工程结算SOP/规程、生成SOP配套流程图、制作"四方签字"流程图、

  按GB/T 9704-2012排版制度文件、Y型瀑布流程图、底线规则红色警示、12章标准结构。

  核心能力：①SOP Word生成（Heading 1/2样式+12章结构+国标排版）②模板风格流程图

  （matplotlib精确手绘·UML活动图符号●起止/圆角矩形/菱形/折角注释·低饱和商务配色·

  阶梯式汇聚·零特殊字符·标题区+图例）③流程图集HTML（PNG内嵌·单文件自包含）

  ④空白节点模板（JSON 自定义节点）⑤mermaid预览版（轻量快速，正式交付用模板风格）⑥四方签字约定（施工+设计+监理+建设）

  ⑦质量门禁（条款编号+法规名+签字方核验）⑧四件齐备入库。

  触发词：SOP、规程、标准操作程序、结算SOP、流程图、Y型瀑布流程图、

  四方签字、GB/T 9704、GB 50500、settlement SOP、flowchart、four-party signature。

  适用：环保水务/市政/建筑工程结算、PPP项目结算、合同结算、变更签证处理。

  不适用：UML类图/时序图（用PlantUML）、程序依赖图（用Graphviz）、

  手绘风格图（用Excalidraw）。

  '
author: 清风明月
slug: qf-process-manual
category: 科技
tags:
- 结算SOP
- 标准操作程序
- 结算规程
- 流程图
- 四方签字
license: MIT
---


## 〇、专家级路由（v2.2.0）

**专家定位**：工程结算 SOP 制度文件 + 配套流程图的一体化生成器（基于某市 PPP 竣工结算 SOP 实战蒸馏）。
**五维评估**：
- 适用场景：①编制 12 章结算 SOP/规程 Word ②生成 Y 型瀑布流程图（`.mmd`/`.png`）③制作"四方签字"流程图 ④四件齐备入库
- 能力边界：不做 UML 类图/时序图（用 PlantUML）、不做程序依赖图（用 Graphviz）、不做手绘架构图（用 Excalidraw）；输入缺项时暂停索取，不猜测填充
- 依赖资产：`scripts/sop_docx_generator.py`、`scripts/flowchart_kit.py`、`scripts/sop_flowchart_total.py`、`scripts/sop_flowchart_diff.py`、`scripts/sop_flowchart_blank.py`、`scripts/sop_flowchart_album.py`、`scripts/sop_flowchart_mermaid.py`、`scripts/sop_flowchart_html.py`、`scripts/sop_quality_check.py`、`scripts/sop_pipeline.py`；`references/{4-party-signature-rule,mermaid-style-guide,sop-chapter-template,gbt-9704-format}.md`
- 交付质量：docx（Heading 1/2 + 12 章）+ mmd（9 种 classDef + 6 种形状）+ png + html 四件齐备；质量门禁四项全 PASS（条款编号连续/法规名规范/四方签字齐/AI 味扫描）
- 性能表现：`sop_pipeline.py` 逐步记录 `degraded` 并落盘 `manifest.json`；PNG 渲染依赖 Node.js + pretty-mermaid

**四级响应（L1-L4）**：L1 轻量问答（12 章结构/签字约定/配色）→给模板或规范直接答；L2 标准任务（SOP+流程图）→5 步工作流；L3 复杂任务（生成异常/门禁 FAIL）→按失败模式降级并回退重跑；L4 专家任务（四件齐备入库）→全流程+四道检查点人工确认
**黄金窗口**：输入确认→资料解析→生成 SOP 正文→生成并渲染流程图→质量门禁→四件齐备入库
**专家件索引**：`scripts/` 五脚本；`references/` 四份规范；12 章标准结构；四方签字约定表；9 种 classDef 配色表；8 步标准工作流

# Settlement SOP Generator（工程结算SOP编制与流程图生成器）

> 基于 **某PPP项目竣工结算SOP V1.1** 实战蒸馏的ima技能。覆盖"制度文件编制+配套流程图+四件齐备入库"全流程。

## 适用场景

- ✅ 编制工程结算类SOP/规程/管理办法（12章标准结构）
- ✅ 生成Y型瀑布流程图（适合多分支汇合的制度流程）
- ✅ 制作"四方签字"流程图（施工+设计+监理+建设）
- ✅ GB/T 9704-2012排版的制度文件
- ✅ 9种节点classDef方案+6种形状+商务低饱和配色

## 核心能力

| 能力 | 命令 | 输出 |
|:---|:---|:---|
| ①SOP Word生成 | `python3 scripts/sop_docx_generator.py` | .docx（Heading 1/2样式） |
| **②模板风格流程图（推荐交付）** | `python3 scripts/sop_flowchart_total.py --project 某PPP --out 图1.png` | .png（UML活动图·低饱和·零杂符） |
| **③模板风格差异处理图** | `python3 scripts/sop_flowchart_diff.py --project 某PPP --out 图2.png` | .png（同一视觉体系） |
| **④流程图集HTML** | `python3 scripts/sop_flowchart_album.py --total 图1.png --diff 图2.png --out 图集.html` | .html（PNG内嵌·单文件自包含） |
| **⑤空白节点模板** | `python3 scripts/sop_flowchart_blank.py --config my_flow.json --out 骨架.png` | .png（节点文字可自定义） |
| ⑥mermaid预览版 | `python3 scripts/sop_flowchart_mermaid.py --render png` | .mmd / .png（轻量预览） |
| ⑦质量门禁 | `python3 scripts/sop_quality_check.py` | 校验报告 |
| ⑧一键流水线 | `python3 scripts/sop_pipeline.py` | docx+图+html+入库 |

## 12章标准结构（与SOP V1.1对齐）

```
一、编制目的与依据
二、适用范围与术语
三、结算基准
四、结算书结构
五、工程量核定流程
六、工程量差异处理
七、结算编制公式
八、签证与材料调差规则
九、必备资料清单
十、报送流程与时点
十一、签字盖章与归档
十二、附则
```

## 四方签字约定（核心规则）

| 差异类型 | 模板 | 签字方（按顺序） |
|:---|:---|:---|
| **管网工程量差异** | 《工程量确认表》（四方确认栏版） | ①施工单位项目负责人签字盖章 → ②设计单位专业设计负责人签字盖章 → ③监理单位总监理工程师签字盖章 → ④建设单位项目负责人签字盖章 |
| **站点工程量差异** | 《图纸会审记录》（表D.5） | ①施工单位项目技术负责人签字 → ②设计单位专业设计负责人签字 → ③监理单位项目技术负责人签字 → ④建设单位项目技术负责人签字 |
| **接户管现场收方** | 《接户管工程量三方确认文件》 | 建设单位+监理单位+施工单位三方现场复核（设计单位不参与） |

## 模板风格绘图引擎（v2.1 新增 · 推荐交付形态）

> 针对 mermaid 自动布局存在的**连线回折交叉、节点内特殊字符渲染异常、留白失衡**问题，
> 提供基于 matplotlib 的精确手绘引擎，完全按 UML 活动图模板框架输出。

| 维度 | 规范 |
|:---|:---|
| 符号 | ● 实心圆起始 / ◎ 同心圆终止 / 圆角矩形活动 / 菱形判断 / 折角注释 —— **全部图形绘制，无字符符号，杜绝乱码** |
| 配色 | 白底深灰蓝框 `#5a6c7d` · 浅黄判断 `#fff3cd` · 浅黄绿折角注释 `#f7f8e6` · 浅绿计量结果 `#e6f2e2` · 浅红不予认定 `#fbe0e0` |
| 版式 | 标题区（主标题＋适用单位副标题＋分隔线）＋ 垂直主干居中 ＋ 三列对称分支 ＋ **阶梯式汇聚**（避免共线歧义）＋ 底部符号图例 |
| 字体 | Noto Sans CJK，脚本内以 `fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')` 显式加载 |
| 输出 | `dpi=170`，约 2168×2102 px，可直接插入 Word / PPT |

### 调用示例

```bash
# 图1：工程量核对流程（主图）
python3 scripts/sop_flowchart_total.py --project "某PPP" --out "工程量核对.png"

# 图2：工程量差异处理流程
python3 scripts/sop_flowchart_diff.py --project "某PPP" --out "差异处理.png"

# 图集 HTML（PNG base64 内嵌，单文件自包含，移动端可读）
python3 scripts/sop_flowchart_album.py \
    --total "工程量核对.png" --diff "差异处理.png" \
    --subtitle "适用：施工单位 ／ 监理单位 ／ 审计单位 ／ 建设单位" \
    --out "SOP流程图集.html"
```

### 交付建议

- **正式交付用模板风格 PNG / HTML**；mermaid 版仅作快速预览。
- 若目标环境缺 Noto CJK 字体，中文会显示为方框 —— 先安装 `fonts-noto-cjk`。
- 两个 PNG 脚本的**节点文字为结算SOP专用内容**；换用其他流程主题时，复制脚本改节点文字即可（布局引擎通用）。

### 字体与字号（v2.2 校准）

- **Noto Sans CJK Regular + Bold 双字体**：正文用 Regular，标题/强调用 Bold **字体文件**
  （`NotoSansCJK-Bold.ttc`），避免合成假粗体的突兀感。
- 字号基准：标题 25 · 副标题 13.5 · 总原则 14~15 · 节点 12~13.5 · 分支标签/注释 12 · 图例 11。
- 布局遵循"**框体略小、留边紧凑**"：结果小框 2.2×0.78、动作框高 1.3，避免"框大字小"。
- "是/否"与"分支名"等标注一律**置于连线外侧上方**，与连线保持 ≥0.15 数据单位间距（不压线）。
- **汇聚线自每个结果框框底引出**（不可从列中心引出），阶梯式汇入总线。

### 公共绘图库

`scripts/flowchart_kit.py` 提供 `init / rbox / diamond / note / path / line / arrow / label /
start_node / end_node / title_block / save` 等原语与配色常量；三个 flow_* 脚本共享该校。

### 空白节点模板（节点自定义）

```bash
python3 scripts/sop_flowchart_blank.py --out 骨架.png                        # 内置占位骨架
python3 scripts/sop_flowchart_blank.py --config my_flow.json --out 我的流程.png
```

JSON 字段：`title / subtitle / principle / branch_question / branches[{tag,action,decision,yes,no}] /
summary / steps[] / note`（branches 支持 2–3 条，steps 支持 2–6 条）。

### 依赖

`matplotlib`（沙箱已预装）+ Noto Sans CJK（Regular / Bold）字体。

## 流程图设计规范（V7终版）

### 节点形状（6类）

| 节点类型 | 形状 | 用途 |
|:---|:---|:---|
| 起止节点 | `([...])` 体育场形 | 流程开始/结束 |
| 常规操作 | `[...]` 矩形 | 操作动作 |
| 判断节点 | `{"..."}` 菱形 | 二选一/多选一 |
| 关键判断 | `{{"..."}}` 六边形 | 核心分叉判断 |
| 汇总节点 | `[/.../]` 平行四边形 | 输入/汇总 |
| 底线规则 | `{{"..."}}` 八边形（用菱形+红色填充模拟） | 警示底线 |

### 配色规范（9种classDef）

| 类型 | 填充 | 边框 | 用途 |
|:---|:---|:---|:---|
| start | #FFFFFF | #5A6B7A | 起止节点 |
| principle | #FFFFFF | #5A6B7A | 总原则 |
| decision | #FFF8DC | #D4A574 | 判断菱形 |
| keyDecision | #F5E6C8 | #D4A574 | 关键判断（六边形） |
| normal | #FFFFFF | #5A6B7A | 常规操作 |
| action | #FFFFFF | #31859C | 启动流程动作 |
| annotation | #F5F5DC | #8B8B5A | 注释/补充 |
| result | #E2EFDA | #548235 | 结果节点 |
| summary | #FFFFFF | #31859C | 汇总节点 |
| warn | #FBE5D6 | #C00000 | 警示/补正 |
| critical | #C00000 | #5C0000 | 底线规则（深红填充白字） |
| criticalGood | #E2EFDA | #548235 | 底线规则"是"分支 |

## 法规引用规范

SOP依据文件按效力层级排列：

```
（一）法律法规
    《建设工程价款结算暂行办法》（财建〔2004〕369号）
    《建设工程工程量清单计价规范》（GB 50500-2013）
    《建设工程文件归档规范》（GB/T 50328-2019）
    《市政工程工程量计算规范》（GB 50857-2013）

（二）合同与会议纪要
    本项目《施工总承包合同》（专用条款第X.X条）
    本项目《竣工结算专题会议纪要》（建设单位内部印发）

（三）地方性文件
    《陕西省建设工程造价管理办法》
    2019年X月当期《陕西工程造价管理信息》材料信息价
```

## 工作流（5步）

```
Step 1 解析输入
        ↓
Step 2 生成SOP Word（脚本①）
        ↓
Step 3 生成流程图（脚本②+③）
        ↓
Step 4 质量门禁（脚本⑤）
        ↓
Step 5 四件齐备入库（脚本⑥）
```

## 使用方式

### 方式1：单步调用

```bash
# 生成SOP Word
python3 scripts/sop_docx_generator.py \
    --title "XXX项目竣工结算SOP" \
    --contract-name "XXX项目施工总承包合同" \
    --baseline-date "2020年3月" \
    --output "XXX_SOP_V1.0.docx"

# 生成流程图mmd
python3 scripts/sop_flowchart_mermaid.py \
    --type "总图" \
    --output "XXX_流程图_总图.mmd"

# 渲染PNG（需pretty-mermaid技能）
python3 scripts/sop_flowchart_mermaid.py \
    --type "总图" --render png \
    --output "XXX_流程图_总图.png"

# 生成HTML
python3 scripts/sop_flowchart_html.py \
    --mmd-files "*.mmd" \
    --output "XXX_流程图.html"
```

### 方式2：一键流水线

```bash
python3 scripts/sop_pipeline.py \
    --project "某PPP" \
    --baseline-date "2019年7月" \
    --chapter-config chapters.json \
    --output-dir outputs/
```

## 依赖资产

- **Python 3.10+** + `python-docx`
- **Node.js 18+** + pretty-mermaid技能（PNG/SVG渲染）
- **可选**：D2（本地安装版）—— 用于生成更高质量流程图

## 触发词

- 中文：结算SOP、竣工结算、流程图、四方签字、Y型流程图、SOP编制、规程、GB/T 9704
- 英文：settlement SOP、flowchart、four-party signature、Y-shape flow、standard operating procedure

## 边界

**不适用**：
- UML类图/时序图（用PlantUML技能）
- 程序依赖图/调用图（用Graphviz）
- 手绘风格架构图（用Excalidraw）
- 大型技术架构图（用D2）

## 配套资源

- `references/4-party-signature-rule.md` - 四方签字约定详解
- `references/mermaid-style-guide.md` - 9种classDef+节点形状规范
- `references/sop-chapter-template.md` - 12章标准模板
- `references/gbt-9704-format.md` - GB/T 9704-2012排版规范

## 标准工作流（8步，每步标「输入 → 输出」）

1. **输入确认**：**输入**：项目名称、合同名称、基准价日期（如「2019年7月」）、12章结构配置 → **输出**：任务参数清单；缺项则暂停向用户索取，不猜测填充。
2. **资料解析**：**输入**：竣工图清单、工程量确认表、图纸会审记录、当期材料信息价 → **输出**：结构化输入（`chapters.json` + 关键参数）；执行 `python3 scripts/sop_docx_generator.py --help` 核对参数名。
3. **生成SOP正文**：**输入**：结构化输入 → **输出**：`XXX_SOP_V1.0.docx`（Heading 1/2 样式 + 12章标准结构）；命令见「方式1：单步调用」。
4. **生成流程图源**：**输入**：流程类型（总图 / 差异处理） → **输出**：`.mmd` 文件（9种classDef + 6种节点形状）；执行 `python3 scripts/sop_flowchart_mermaid.py --type "总图" --output "总图.mmd"`。
5. **渲染PNG**：**输入**：`.mmd` 源文件 → **输出**：`.png`（依赖 pretty-mermaid 与 Node.js）；渲染失败时按「失败模式与降级路径」兜底为 `.mmd` 交付。
6. **生成HTML交互页**：**输入**：全部 `.mmd` 文件 → **输出**：单文件自包含 `.html`（mermaid.js CDN + 图例 + 节点形状图例）；执行 `python3 scripts/sop_flowchart_html.py --mmd-files "*.mmd" --output "SOP流程图.html"`。
7. **质量门禁**：**输入**：SOP 文档 → **输出**：`sop_quality_check.py` 校验报告；条款编号连续性、法规名称规范性、四方签字约定、AI味扫描四项逐条核验，任一 FAIL 即回退修改。
8. **四件齐备入库**：**输入**：docx + mmd + png + html → **输出**：`manifest.json` 清单与入库记录；执行 `python3 scripts/sop_pipeline.py --project "某PPP" --baseline-date "2019年7月" --output-dir outputs/`。

> 第 1、7 步为硬门禁：未获人工确认不得进入下一步。

## 失败模式与降级路径

| 失败场景 | 触发条件 | 降级 / 回退路径 |
|---|---|---|
| Word 生成异常 | `python-docx` 缺失或样式模板冲突 | 先重试 1 次；仍失败则降级输出 Markdown 正文，`manifest.json` 记 `word:failed` |
| PNG 渲染失败 | 无 Node.js 或 pretty-mermaid 不可达 | 降级保留 `.mmd` 源文件，HTML 交互页照常生成，记 `png:*:failed` |
| mmd 全部缺失 | 流程图脚本报错 | 跳过 HTML 步骤，兜底只交付 Word + 质量门禁报告，并明示降级 |
| 质量门禁 FAIL | 条款编号断号 / 法规名不规范 / 四方签字缺项 | 回退到第 3 步修改后重跑门禁，禁止带 FAIL 入库 |
| 输入材料不齐 | 基准价日期、合同名称等必填字段缺失 | 暂停并向用户索取，不做假设填充 |

> 任何异常都不得静默吞掉：`scripts/sop_pipeline.py` 逐步记录 `degraded` 列表并落盘 `manifest.json`，交付时须明示降级项与残余风险。

## 检查点与人工确认

SOP 编制全程设四道显性检查点，关键决策前必须停下等确认：

- 🔴 **检查点 1（输入确认）**：项目名称、基准价日期、12章结构、四方签字模板是否齐备；不齐备则暂停。
- 🔴 **检查点 2（结构与口径确认）**：12章结构、结算公式、四方法定签字顺序形成后，须经人工确认再生成 Word。
- 🔴 **检查点 3（质量门禁确认）**：`sop_quality_check.py` 四项全 PASS 且经确认后，方可进入入库步骤。
- 🔴 **检查点 4（入库确认）**：确认 docx / mmd / png / html 四件齐备（`four_pieces_complete=true`）且已回填产物路径，方可宣告完成。

> STOP：任一检查点未获人工确认，不得进入下一步；降级交付须在交付说明中列出需确认项。

## 版本

- v2.2.0（2026-09-11）— 视觉修正：改用 Noto Sans CJK Regular+Bold 双字体（消除假粗体）；字号整体上调（标题 25 / 节点 12~13.5）、节点框体收紧（消除"框大字小"）；"是/否"与"分支名"标注移至连线外侧上方（消除压线）；修复汇聚线未从结果框引出的断线 bug；抽出公共绘图库 `flowchart_kit.py`；新增空白节点模板 `sop_flowchart_blank.py`（JSON 自定义节点）
- v2.1.0（2026-09-11）— 新增模板风格绘图引擎（`sop_flowchart_total.py` / `sop_flowchart_diff.py` / `sop_flowchart_album.py`）：UML 活动图符号＋低饱和商务配色＋阶梯式汇聚＋零特殊字符；`sop_docx_generator.py` 支持 `--date/--doc-no/--drafting-unit`；`sop_quality_check.py` 修复"章-节体例"编号误报与"非法规书名号"误报
- v1.0.0（2026-09-09）— 基于某PPP项目竣工结算SOP V1.1实战蒸馏

## 主题配色（可选）

本技能输出的 HTML 可一键换肤，套用「专业视觉主题工厂」的成套主题（四色色板 + 标题/正文字体配对），10 套可选。

```bash
# 列出可选主题
python3 scripts/themeize.py --list-themes

# 生成后换肤（不改动原生成脚本）
python3 scripts/themeize.py -i 报告.html -t ocean-depths                 # 输出 报告_ocean-depths.html
python3 scripts/themeize.py -i 报告.html -t midnight-galaxy --mode dark  # 深色模式
python3 scripts/themeize.py -i 报告.html -t tech-innovation --keep "#123456"
```

主题清单：ocean-depths 深海之境 / sunset-boulevard 落日大道 / forest-canopy 森林之冠 / modern-minimalist 现代极简 / golden-hour 金色时刻 / arctic-frost 极地霜华 / desert-rose 沙漠玫瑰 / tech-innovation 科技创新 / botanical-garden 植物园 / midnight-galaxy 午夜星河。
语义色（警示红 / 通过绿 / 提示黄）不随主题变化；中文字体回退链自动补齐；换肤输出色值映射表与对比度校验结果。

## 依赖安装

本技能脚本依赖第三方库，首次使用（或沙箱/换机重置）后请先安装：

```bash
python3 -m pip install -r requirements.txt
```

## HTML 成果页接入（底座已内嵌 · html-report-builder v4.1.0）

本技能产出 HTML 时**统一走内嵌底座**（`scripts/htmlbase/`：md2report.py / palettes.py / build_report.py / board.py / html_check.py），自包含运行，不引用外部技能；底座升版后用 `python3 scripts/sync_htmlbase.py --all --apply` 重新分发。

```bash
python3 scripts/htmlbase/md2report.py <成稿md> -o <名称>_成果页.html --theme <配色id> --audience <交付对象> --check
```

看板型（指标／台账／测算类）改用看板入口：`python3 scripts/htmlbase/board.py --data board.json -o <名称>_看板.html --theme galaxy --check`。交付前 `--check` 的 FAIL 须清零；归档时 HTML 与原件一并入库成果库（kb_id=`ztJsLCMwR3pgWo250gemdopQbgBCLefIJCGns0HK9D0=`）。

配色速选：内部汇报 `ocean`／环保低碳 `forest`·`botanical`／打印分发 `minimal`·`arctic`／投资财务 `galaxy`·`golden`／技术前沿 `tech`。

本技能原有的专用渲染器（如交互计算器、雷达图、地图、专用版式）保留用于其特有交互；**通用报告页/说明页以底座版为准**。

## 降级路径与失败模式（完整版）

> 上表为常见情形的精简清单；本节给出覆盖全部健壮性关键词的完整失败模式编码，作为兜底与容错细则，逐条对应一个可执行的 fallback 动作。

| 场景 | 触发条件 | 降级处置（fallback） |
|---|---|---|
| 输入缺失 / 空文件 | 基准价日期、合同名称等必填项为空，或上传文件 0 字节、编码乱码 | 走失败分支暂停并向用户索取，不做假设填充（返回非零退出码） |
| 输入格式不支持 | 二进制、加密或损坏的图纸清单 / 计量表无法解析 | 回退到「先转 Markdown 再重试」；仍失败列入未处理清单并明示影响 |
| Word 生成异常 | `python-docx` 缺失或样式模板冲突 | 重试 1 次；仍失败则降级输出 Markdown 正文，`manifest.json` 记 `word:failed` |
| PNG 渲染失败 | 无 Node.js 或 pretty-mermaid 不可达 | 降级保留 `.mmd` 源文件，HTML 交互页照常生成，记 `png:*:failed` |
| mmd 全部缺失 | 流程图脚本报错导致无源文件 | 兜底只交付 Word + 质量门禁报告，跳过 HTML 步骤，并明示降级口径 |
| 质量门禁 FAIL | 条款编号断号 / 法规名不规范 / 四方签字缺项 | 回退到第 3 步修改后重跑门禁，禁止带 FAIL 入库 |
| 门禁工具异常 | `sop_quality_check.py` 自身报错（无 docx 依赖等） | 异常捕获后退化为「文本正则 + 人工四目核验」，记录降级项 |
| 字体缺失 | 目标环境无 `fonts-noto-cjk`，中文显示方框 | 兜底改用系统可用 CJK 字体族；无可用字体时交付 `.mmd` 源并标注 |
| 主题换肤失败 | 主题 id 不存在或 HTML 无匹配色值槽位 | 回退保留原始配色产物，输出未换肤文件并记录失败主题名 |
| 入库中断 | 入库步骤网络超时或权限不足 | 保留产物与 `manifest.json`，支持断点续跑，仅重跑未完成步骤 |
| 检查点未确认 | 四道人工检查点任一项未获确认 | 停止推进，列出待确认项与已生成产物，等待裁决 |
| 边界条件越界 | 请求属于 UML / Graphviz / Excalidraw 领域 | 拒绝并给出替代技能建议，不做越界承诺 |

**容错与防御**：全流程设置错误处理与异常捕获；每个步骤设边界条件校验（空输入、编码、必填项）；对不可逆动作做防御性二次确认；失败时保留中间产物以便补救；支持幂等重试与断点续跑。任何 fallback 一旦启用，都必须在交付说明中显式告知用户当前降级口径，不得静默降级。

## 引用依据与溯源

本技能的 12 章结构、结算公式、签字约定与排版规范参考以下权威依据（全称 + 编号/文号 + 来源）：

| # | 依据全称 | 编号 / 文号 | 来源 |
|---|---|---|---|
| 1 | 《建设工程价款结算暂行办法》 | 财建〔2004〕369号 | 财政部、建设部 |
| 2 | 《建设工程工程量清单计价标准》 | GB/T 50500-2024 | 住房和城乡建设部 |
| 3 | 《党政机关公文格式》 | GB/T 9704-2012 | 国家质量监督检验检疫总局、国家标准化管理委员会 |
| 4 | 《建设工程文件归档规范》 | GB/T 50328-2014 | 住房和城乡建设部 |
| 5 | 《建设工程质量管理条例》 | 国务院令第279号 | 国务院 |
| 6 | 《中华人民共和国民法典》（合同编） | 中华人民共和国主席令第四十五号 | 全国人民代表大会常务委员会 |
| 7 | 《建设工程施工合同（示范文本）》 | GF-2017-0201 | 住房和城乡建设部、国家工商行政管理总局 |

**标注规则**：SOP 正文引用的条款编号、法规名称、计量口径必须以依据原文为准；无法核实的条款一律标注 `【待核：…】`，不得臆造、不杜撰、不编造依据条文与来源。

## 能力边界（不适用范围）

**适用**：工程结算类 SOP / 规程 / 管理办法的制度文件编制（12 章标准结构）、配套 Y 型瀑布流程图与「四方签字」流程图生成、GB/T 9704-2012 排版、四件齐备（docx + mmd + png + html）交付入库。

**不适用 / 不在范围**：

- UML 类图 / 时序图 / 用例图 → 改用 PlantUML 类技能；
- 程序依赖图 / 调用图 → 改用 Graphviz 类技能；
- 手绘风格架构图 → 改用 Excalidraw 类技能；
- 工程结算的造价计价与定额套用、结算审减 → 属造价与结算审核技能范围；
- 出具具有法定效力的结算审核结论或司法鉴定意见 → 不在范围，不做越界承诺。

**限定**：本技能产出的是制度文件与配套图件，仅限流程与体例的表征；不对结算金额的实体正确性背书，输入缺项时暂停索取、不猜测填充。

## 红线声明（完整版）

1. 严禁编造、杜撰结算条款、法规名称与文号；无法核实者一律标注 `【待核：…】`。
2. 不替代造价、法律、审计等专业资质判断，不出具具有法定效力的结论。
3. 不承诺结算金额、审减率或任何商业结果。
4. 输入涉密或个人隐私（合同金额、个人信息）时，提示先脱敏再处理。
5. 禁止带质量门禁 FAIL 入库；四道人工检查点未确认不得推进。
6. 不可静默降级：任何回退方案与未覆盖缺口都须在交付说明中显式告知。

## 可交付物与输出规范

| 交付物 | 格式 | 命名规范 | 校验方式 |
|---|---|---|---|
| SOP 制度文件 | `.docx`（Heading 1/2 + 12 章） | `<项目>_SOP_V<版本>.docx` | `python3 scripts/sop_quality_check.py --file <docx>` |
| 流程图源 | `.mmd`（9 种 classDef + 6 种形状） | `<图名>.mmd` | 目视核对节点与分支 |
| 流程图位图 | `.png`（模板风格，dpi 170） | `<图名>.png` | 目视核对字号与连线 |
| 流程图集页 | `.html`（PNG base64 内嵌·单文件自包含） | `<项目>_流程图集.html` | 直接打开确认离线可读 |
| 交付清单 | `manifest.json` | `manifest.json` | 核对四件齐备与 `degraded` 列表 |
| 打包自检报告 | 终端 / `.json` | — | `python3 scripts/sop_pack_check.py --dir <交付目录>`，退出码 0 通过 / 1 告警 / 2 错误 |

**输出规范**：正式交付用模板风格 PNG / HTML，mermaid 版仅作快速预览；docx 名称、文号、编制单位按 GB/T 9704-2012 体例；交付前必须跑 `sop_quality_check.py` 与 `sop_pack_check.py` 各一次，FAIL 须清零。

## 触发条件与英文触发词

**中文触发词**：结算SOP、竣工结算、流程图、四方签字、Y型流程图、SOP编制、规程、标准操作程序、GB/T 9704、GB 50500、变更签证处理。
**English triggers**: settlement SOP, settlement standard operating procedure, SOP drafting, flowchart generation, four-party signature, Y-shape waterfall flowchart, construction settlement procedure, GB/T 9704 formatting.

## 版本沿革（CHANGELOG）

| 版本 | 日期 | 变更 |
|---|---|---|
| 2.3.0 | 2026-10-04 | TRACE 改造：增补降级路径与失败模式完整表、引用依据与溯源、能力边界、红线声明、可交付物与输出规范、英文触发词与版本沿革；新增打包自检脚本 `sop_pack_check.py` 与 `references/case-library.md` |
| 2.2.0 | 2026-09-11 | 视觉修正：Noto Sans CJK Regular+Bold 双字体、字号上调与框体收紧、标注移至连线外侧、修复汇聚线断线；抽出 `flowchart_kit.py`，新增空白节点模板 `sop_flowchart_blank.py` |
| 2.1.0 | 2026-09-11 | 新增模板风格绘图引擎（`sop_flowchart_total.py` / `sop_flowchart_diff.py` / `sop_flowchart_album.py`）；`sop_docx_generator.py` 支持 `--date/--doc-no/--drafting-unit` |
| 1.0.0 | 2026-09-09 | 基于某市 PPP 项目竣工结算 SOP V1.1 实战蒸馏首版 |

> 实测案例详见 `references/case-library.md`；完整失败模式编码见上文「降级路径与失败模式（完整版）」。
