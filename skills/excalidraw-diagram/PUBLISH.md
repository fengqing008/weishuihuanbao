# 手绘图生成官（excalidraw-diagram）· 发布说明

> 版本：2.2.0　|　作者：清风明月　|　slug：qf-excalidraw-diagram　|　category：可视化与图表生成

## 一、技能简介

把一句自然语言需求，转成可直接在 Excalidraw 打开、可继续编辑的 `.excalidraw` 手绘风格图表 JSON。
产出遵循"图要论证、不要陈列"的原则：形状本身承载语义（扇形发散＝一对多、漏斗汇聚＝多对一、时间线＝序列、循环箭头＝闭环迭代），并强制走"生成 JSON → 渲染 → 看图 → 修正"的闭环，杜绝交付重叠、越界、错连的成品。

配套 `scripts/excalidraw_check.py`（零第三方依赖）在生成后做静态体检：坐标越界、元素重叠、箭头错连、文字溢出、ID 重复一次报出。

### 使用说明（6 条）

1. **生成 .excalidraw 文件**：说「把手绘流程图生成 .excalidraw 文件」，输出可直接在 Excalidraw 打开编辑。
2. **手绘架构图**：说「画个手绘风格架构图，能在 Excalidraw 里继续改」，我按手绘风格出图。
3. **可视化论证**：说「用一张图做可视化论证」，我按论点-论据结构组织图形。
4. **一句话需求转图**：说「一句话需求转成手绘图」，我把自然语言转成图元与连线。
5. **结构体检**：说「检查手绘图有没有元素重叠 / 越界」，我跑坐标与重叠检查脚本。
6. **概念示意图**：说「做概念图 / 示意图，手绘风格」，我按概念关系出图。

## 二、使用示例

### 示例 1：流程类手绘图

> 帮我画一张手绘流程图：用户提交工单 → 系统校验 → 通过则派单，不通过则退回。

- 触发：`画手绘图` + `流程图`
- 产物：`ticket-flow.excalidraw`，含起点椭圆、判断菱形、两条分支箭头与自由文本标注。
- 体检：`python3 scripts/excalidraw_check.py --file ticket-flow.excalidraw`

### 示例 2：架构类手绘图

> 出一张 Excalidraw 架构图，展示客户端 → 网关 → 三个微服务 → 数据库的调用关系。

- 触发：`Excalidraw` + `架构图`
- 产物：`arch.excalidraw`，含容器分区、跨区绑定箭头、真实接口名 evidence artifact。
- 体检：`python3 scripts/excalidraw_check.py --file arch.excalidraw --json`

### 示例 3：概念类可视化论证

> 做一张可视化论证：把"信息衰减"画成漏斗，越往下越窄。

- 触发：`可视化论证`
- 产物：`funnel.excalidraw`，用宽度递减的椭圆链＋汇聚箭头表达衰减，不堆方框。

## 三、适用场景

- 技术讲解配图（流程、协议、调用链、数据流）
- 架构与部署关系图（组件、边界、依赖）
- 概念与心智模型图（对比、分层、循环、漏斗）
- 汇报材料、课程讲义里的手绘风示意图
- 需要后续在 Excalidraw 中继续拖拽编辑的原生 `excalidraw` 文件

## 四、不适用边界

- 位图精修、照片增强、去水印：走图像处理类技能
- UI 高保真设计稿、交互原型：走设计稿类工具
- 3D 渲染、工程制图（CAD/竣工图）：走 CAD 类技能
- 纯数据大屏、可交互 BI 看板：走数据可视化平台
- 需要精确工程尺寸标注的机械/建筑图：本技能不做尺寸链与公差

## 五、依赖与运行环境

- 本技能核心（生成 JSON + 静态体检 `scripts/excalidraw_check.py`）：Python 3.8+，**零第三方依赖**，开箱即用。
- 可选渲染管线（`references/render_excalidraw.py`，用于渲染 PNG 后目视校验）：
  `uv sync` 安装 `references/pyproject.toml` 中的依赖，并执行 `uv run playwright install chromium`。

## 六、版本记录

| 版本 | 说明 |
|------|------|
| 2.2.0 | 汉语化改造：frontmatter 补 author/display_name/slug/category/tags；新增「执行工作流」「反例与红线」「使用示例」章节；失败模式扩至 9 条并统一「如果 X → 则 Y」格式；新增 `scripts/excalidraw_check.py` 结构体检脚本；新增本发布说明。 |
| 2.1.0 | 原英文版：核心设计方法论 + 渲染验证闭环。 |

## 七、作者与许可

- 作者：清风明月
- 本技能在原有 Excalidraw Diagram Skill 设计方法论基础上做汉语化与工程化增强。
