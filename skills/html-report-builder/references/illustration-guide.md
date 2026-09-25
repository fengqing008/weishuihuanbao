# 配图规范（illustration-guide.md）

> 适用技能：html-report-builder **v5.3.0** 起。配图的触发条件、路由、通道、主题色调一致、像素校验基准与验收清单。
> **配图源与 ima 生图类型路由（按成果文件类型选实景图/插画/线稿/图表，配图色调随主题）见 `illustration-routing.md`。**
> 图形类可视化（流程图/时序图/架构图）见 `diagrams-guide.md`，本文件只管「插图」。

## 一、什么时候配图：按需触发

**默认不配图。** 仅当用户明确要求时才执行配图链，例如说「配图 / 加图 / 插图 / 来几张图 / 给某章配图 / 加张示意图」。

未明确要求时，正文可视化交给：

- **图形围栏** ```` ```mermaid ```` —— 流程、时序、架构（首选，精确且零成本）；
- **文字化图表** `:::chart` / `:::timeline` / `:::matrix` / `:::phase` / `:::bar` —— 数据与关系。

**该配**（用户要求且章节确有视觉价值）：工艺流程、现场场景、系统构成、布置走向、规划布局。
**不该配**：纯数据论证（用 `:::chart`）、法条制度（用 `:::law`/`:::timeline`）、篇幅 <160 字且标题无视觉语义的短章、已有图或图表的章节。

**数量**：每篇 2–4 张为宜。

## 二、两条通道

| 通道 | 命令 | 适用 |
|---|---|---|
| **A. 实景图（调研/规划类首选）** | `plan --source photo --theme forest` → 联网检索 → `apply` | 调研报告、旅游规划、行业研究；真实照片、来源可追溯；**不加 AI 角标** |
| **B. ima 商业插画（文章/文化/政务/技术类）** | `plan --source ai --style editorial` → image_gen 出图 → `apply` | 散文/文章（editorial）、生活文化（handdrawn-warm）、政务（flat-vector）、科普（infographic）、技术前沿（tech-abstract）、传统文化（ink-watercolor）、品牌（3d-render）、汇报（business-2.5d）；**加 AI 角标** |
| **C. 本地手绘线稿** | `illustrate.py lineart 成稿.md --max 3 --palette auto --theme sunset --stroke pencil` | 技术/工程/内部材料；确定性渲染、不出纯色、零成本 |

线稿通道可调：`--palette`（sepia / ochre / amber / terracotta / rosewood / olive / ink）、
`--stroke`（fountain / pencil / brush / marker / charcoal）、`--size`（跨栏 1500x820 / 栏内 760x980）。

- **色调与主题一致**：ai 通道提示词注入文档主题色卡（主 / 辅 / 底色），线稿通道 `--palette auto` 按主题色温映射（sunset→terracotta、forest/botanical→olive、golden→amber、desert→rosewood、冷色/深色主题→ink）；`--theme` 传配色 id，缺省读成稿 frontmatter 的 `theme:`。

## 三、配图点识别（plan 与 lineart 共用 pick_points）

| 优先级 | 规则 | 权重 |
|---|---|---|
| 1 | 标题命中强语义词（工艺/流程/工序/步骤/环节/时间线/进度/节点/现场/实景/布置/总平面/布局/平面/鸟瞰/管网/系统/结构/构成/分布/对比/示意/场景/规划/方案/选型/设备/装置/构筑物/池体/车间/园区/路线/地理） | 每词 +4 |
| 2 | 标题命中弱语义词（概况/背景/总述/总体/总结/结论/综述/目标/任务/成效/亮点/难点/风险/建议/措施/计划/安排/范围） | 每词 +2 |
| 3 | 正文命中强语义词 | 每词 +1 |
| 4 | 章节篇幅 | 每 150 字 +1（上限 +4） |

入选条件：标题有强/弱语义命中，或正文 ≥ `--min-chars`（默认 160）；按分数取前 `--max`，再按原文顺序回排。

## 四、出图像素校验（防「配图是一块纯色」）

`apply` 与 `check` 均调用 `validate_image()`，判据为**边缘均值**（240px 缩略 + FIND_EDGES 均值），
而非方差——线稿是「白底 + 线条」，方差天然低但有结构，用方差会误拦：

| 图类型 | 边缘均值 | 唯一色 | 判定 |
|---|---|---|---|
| AI 大片渐变（低结构，视觉即一片色） | ≈2.6 | 80–94 | **拦截，拒绝落位** |
| 手绘线稿 | 9.3–14.1 | 108–181 | 通过 |
| 真实照片 | 18–25 | 1700+ | 通过 |

- 阈值 `min_edge=5.0`（可 `validate_image(path, min_edge=…)` 覆盖）；
- 被判低结构者不插图，输出中列出处置建议：重出该图 / 改用线稿通道 / 确认无误时 `--allow-solid` 放行；
- 唯一色数仅作诊断展示，不参与硬拦（避免误伤简单母题线稿）。

## 五、AI 通道提示词模板（按需使用）

提示词 = **ima 生图类型前缀 + 主题 + 图注（画面内容）+ 主题色卡 + 构图约定 + 负面约束**。v5.3 起 `build_prompts` 自动注入文档主题色卡（accent/accent2/bg）并要求「低饱和、与主题色统一、无冲突高饱和杂色」，同时固定「主体突出、留白充足、层次清晰、光线柔和统一」的构图约定。

| 章节类型 | 画面内容写法 |
|---|---|
| 工艺流程 | 主体工艺单元依次串联（格栅—沉砂—调节—生化—二沉—消毒），管线清晰，模块化排布 |
| 现场施工 | 小型厂站施工/调试现场，主体结构与设备安装、场坪与围栏，作业人员小比例出现 |
| 系统构成 | 管网—泵站—厂站—排放口的系统拓扑，重力流与提升段区分 |
| 规划布局 | 厂区总平面鸟瞰，功能分区色块（预处理区/生化区/泥处理区/辅助区） |
| 运营值守 | 中控室值守与设备巡检场景，仪表屏与操作台 |

负面约束固定：`画面中不出现任何文字、字母、数字、水印、logo、商标、边框`。
**注意**：AI 出图对「抽象工程术语」易产出大面积渐变色块（即被像素校验拦截的那类），
提示词须写明具体主体名词与要素顺序，避免抽象形容词。

## 六、图注与落位

- 单图：`![图注](images/lineart_01.png){wide}`；`{inline}` 收窄；`{ai}` 加「AI 配图」角标。
- 线稿通道落位不加 `{ai}`（本地渲染，非 AI 生成）；AI 通道落位默认加 `{ai}`。
- 图组：`:::gallery 标题` + 每行「路径 | 图注」。
- 图注自动编号（图 1、图 2…）全篇连续，与 mermaid 图形共用计数器。

## 七、体积

| 用途 | 尺寸 | 说明 |
|---|---|---|
| 正文宽图 `{wide}` | 1536×864（AI）/ 1500×820（线稿） | 默认，占满内容区 |
| 正文窄图 `{inline}` | 1024×768 / 760×980 | 居中收窄 |
| 封面 | 1536×640 | `plan --cover` 生成 |

**v5.3.0 画质优先**：单张 >**900KB** 才触发压缩（长边 ≤**1920**、JPEG q**92**）；低于阈值**不压缩**；含图页用 `--max-kb 2000`（3—4 张高清图可用 2400）。需要完全保留原图：`apply --no-compress`；可 `--max-side/--quality/--threshold-kb` 微调。

## 八、失败模式

| 现象 | 原因 | 处置 |
|---|---|---|
| `apply` 报「像素校验未过」 | 图是大片纯色/渐变 | 改用 `lineart` 通道；或重出并写实提示词；确认无误用 `--allow-solid` |
| `apply` 报「锚点未匹配」 | plan 之后章节标题被改 | 用最新稿重跑 `plan` 再 `apply` |
| `lineart` 报未找到引擎 | qf-lineart 不在预期路径 | 确认 `qf-lineart/scripts/lineart_engine.py` 存在 |
| 图未瘦身 | 未安装 Pillow | `pip install pillow`；或 `--no-compress` |
| 体积超限 | 图未压或张数偏多 | 先 `apply` 瘦身；用 `--max-kb 2000`（高清 3—4 张可 2400）；仍超则减张数 |
| 散文配不出图 | 章节短且标题无视觉词 | ai 通道已自动启用 article 模式（≥60 字入选），确认 `--source ai` |

## 九、验收清单

```bash
S=<技能目录>
python3 "$S/scripts/illustrate.py" lineart 成稿.md --max 3 --palette sepia   # ① 线稿出图+回填
python3 "$S/scripts/illustrate.py" check 成稿_lineart.md                      # ② 配图自检（须 PASS）
python3 "$S/scripts/md2report.py" 成稿_lineart.md -o 成果页.html --theme sunset --check --max-kb 2000
```

判定：`check` 输出 PASS；`md2report --check` 输出 `FAIL=0`，`IMG_EMBED`、`AI_FIG`、`IMG_ALT` 为 OK。
（AI 通道则为 `plan → 出图 → apply → check` 四步。）
