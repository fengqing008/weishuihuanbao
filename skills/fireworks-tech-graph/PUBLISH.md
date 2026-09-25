# PUBLISH · 技术图绘制官（fireworks-tech-graph）

## 一、技能简介

**技术图绘制官**是面向技术文档、研发沟通与汇报交付的生产级出图技能。输入一段文字描述的技术结构，
输出可直接放进文档、Wiki、README 或演示稿的 SVG 图件，并可按需导出高分辨率 PNG。

- **图型覆盖**：架构图、数据流图、流程图、序列图、Agent 架构图、记忆架构图、思维导图、类图、
  用例图、状态机图、ER 图、网络拓扑图、对比矩阵、时间线/Gantt，共 14 类。
- **视觉风格**：7 套（Flat Icon / Dark Terminal / Blueprint / Notion Clean / Glassmorphism /
  Claude Official / OpenAI Official），每套含精确颜色令牌与字体栈。
- **规范内置**：UML 14 类覆盖映射、形状词汇表、箭头语义系统、正交路由、标签背景防遮挡、
  8px 网格对齐、写入前五项自检、Quick Fix 修复协议。
- **可执行后端**：`scripts/render_diagram.py`（规格 JSON → SVG → PNG）与
  `scripts/check_svg.py`（交付前静态自检），另有 3 个 shell 脚本做校验与批量回归。

### 使用说明（6 条）

1. **系统架构图**：说「画一个系统架构图，输出 SVG + PNG」，我按风格模板出图。
2. **流程与序列图**：说「画这个流程的流程图 / 序列图」，我按文字描述生成规范图件。
3. **数据流图**：说「把这段描述画成数据流图」，我落成带箭头语义的数据流图。
4. **Agent / 记忆架构图**：说「画一张 Agent 架构图 / 记忆架构图」，我按分层结构出图。
5. **思维导图 / ER 图 / 状态机图**：说「出个思维导图 / ER 图 / 状态机图」，我按对应图型渲染。
6. **对比矩阵与时间线**：说「画一张对比矩阵或时间线」，我输出矩阵或时间轴图件。

## 二、使用示例

**示例 1 · 三层微服务架构图**

```bash
python3 scripts/render_diagram.py --spec specs/order-arch.json --out out/order-arch-style3.svg --style 3 --width 1920 --png
python3 scripts/check_svg.py out/order-arch-style3.svg --cjk
```

**示例 2 · 内置演示规格，用于自检与冒烟测试**

```bash
python3 scripts/render_diagram.py --demo --out out/demo.svg --style 2 --png
# 输出：[通过] SVG 语法校验 OK  out/demo.svg  (960x824, style 2 / dark-terminal)
# 输出：[通过] PNG 导出 OK  out/demo.png  (imagemagick, 1920px)
```

**示例 3 · 用自然语言直接提出出图请求**

> "画一张下单支付的时序图，参与者是用户、订单服务、支付网关、银行，先出 Flat Icon 版本，
> 再出一版暗色终端风格。"

处置路径：归类型为序列图 → 生命线垂直排布，消息按时间自上而下，alt/loop 帧用虚线矩形框 →
第一版取 `references/style-1-flat-icon.md`，第二版取 `references/style-2-dark-terminal.md` →
写入前五项自检 → 校验 → 导出 PNG → 报告两份产物的绝对路径。

## 三、适用场景

| 场景 | 说明 |
|------|------|
| 技术文档与设计文档 | 架构图、数据流图、模块分层图，贴进 Word / Markdown / Confluence |
| 研发协作 | 时序图、状态机图、类图、ER 图，用于评审与交接 |
| 汇报与路演 | Glassmorphism 或 Flat Icon 风格的概览图，导出 1920px PNG 进演示稿 |
| 开发者文章与 README | Dark Terminal 风格，适配 GitHub 暗色主题 |
| 内网知识库 | Blueprint 或 Notion Clean 风格，正式且克制 |
| 批量出图回归 | 用 `scripts/test-all-styles.sh` 一次跑通 7 套风格并汇总校验结果 |

## 四、不适用边界

- 不适用于照片编辑、修图、抠图与调色。
- 不适用于位图手绘风格插画与艺术创作。
- 不适用于三维渲染图与物理仿真图。
- 不适用于带动画或交互逻辑的图表（D3.js、Plotly、SMIL）。
- 不适用于需要实时数据绑定的动态大屏。
- 不负责图外内容创作：图中文字只取自用户描述，不代写方案与文案。

## 五、版本与作者

| 项目 | 内容 |
|------|------|
| 技能名 | `fireworks-tech-graph` |
| 显示名 | 技术图绘制官 |
| 版本 | 1.2.0 |
| 作者 | 清风明月 |
| slug | `qf-fireworks-tech-graph` |
| 分类 | 可视化生成 |
| 许可 | 见技能目录下 `LICENSE` |
| 依赖 | Python 3、ImageMagick `convert`（或无则回退至 `rsvg-convert` / `cairosvg` / `inkscape`） |

## 六、安装与自检

```bash
python3 -m py_compile scripts/render_diagram.py scripts/check_svg.py
python3 scripts/render_diagram.py --demo --out /tmp/demo.svg --style 1 --png
python3 scripts/check_svg.py /tmp/demo.svg --cjk
```
