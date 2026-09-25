# design-system-v3 · 设计范式提炼（源：12篇标杆范本HTML）

> v3.0 重构依据。源范本：银发经济商业机会分析、2026新媒体营销用户洞察、茶饮品牌年度整合营销、
> 高中地理课时教案、高中数学情境化自测卷、思政课改课题研究方案、AI_Agent竞品分析、
> 高效办成一件事政策解读、汇报材料智能撰写工作台、劳动争议法条检索工作台、
> 买卖合同纠纷案件分析报告、中国现制咖啡市场消费趋势调研（2026-09-22 上传分析）。

## 一、从范本中提炼的共性设计语言

| 设计要素 | 范本做法 | v3 落地 |
|---|---|---|
| 头部标题 | 渐变首屏 + 徽章 pill + clamp 大标题 + 装饰（茶饮山形SVG/新媒体hero-cards/银发几何色块） | hero-badge + hero-deco ×3 + hero-wave + clamp 标题 |
| 首屏数据 | 新媒体/银发把核心 KPI 放进首屏半透明卡 | hero-stats 玻璃数据卡 |
| 二次目录 | 咖啡=左侧栏；新媒体/茶饮=吸顶毛玻璃条+scroll-spy；章节内小节用 ①②③ 或 01/02 编号 | 章节级 chapterNav（v2.1 已有）+ 章节内「本节要点」sub-toc（h3 自动收集） |
| 小标题模块 | 新媒体 sec-head（emoji+标题+副描述+可折叠）；地理 sec-num 编号；高效办成 sec-head+sec-desc | sec-no 渐变方块 + h2 + step-sub + sec-fold 折叠 |
| 画板展示 | AI_Agent 对比矩阵（sticky 首列+横向滑动+提示语）；新媒体 bar-track 条形；买卖合同 timeline+law-card；地理 phase 阶段卡；银发 score 矩阵 | :::matrix/:::bar/:::timeline/:::law/:::phase/:::bento 八围栏 |
| 质感细节 | 双档阴影、卡片 hover 上浮、backdrop-filter 毛玻璃、渐变文字/色条 | b-cell/phase hover 上浮 + sec-no 渐变投影 + hero 玻璃态 |
| 配色体系 | 每篇一套 CSS 变量（deep/mid/pale 三档 + ink/muted/paper/card/line） | 沿用 palettes.py 10 套主题（已含三档结构） |
| 字体策略 | 通用 sans 正文 + serif 用于法条/正式标题 | law-name 用 Songti/STSong serif |
| 交互 | IntersectionObserver scroll-spy、折叠面板、localStorage、横向滑动提示 | v2.1 scroll-spy 保留 + v3 章节折叠 + details.faq 原生折叠 + scroll-hint |

## 二、组件选用决策表

| 内容形态 | 首选组件 | 备选 |
|---|---|---|
| 多对象多维度对比 | :::matrix（sticky 首列） | :::bar |
| 时间脉络/里程碑 | :::timeline | :::phase |
| 流程/步骤/责任分工 | :::phase（自动编号） | 有序列表 |
| 关键指标速览 | :::bento（1-3 列跨行） | :::kpi（v2.0） |
| 排名/占比/进度 | :::bar | :::bento |
| 法规/合同条款引用 | :::law | > [!info] callout |
| 问答/口径解释 | :::faq | 普通段落 |
| 关键词/范围圈定 | :::tags | 正文加粗 |

## 三、排版纪律（从范本反推）

1. 首屏必须回答"这是什么、给谁看、核心数字是什么"——badge + h1 + lead + hero_stats 四件不缺。
2. 每章开头一句话副描述（step-sub）交代本节看点，正文才展开。
3. 数据组件每屏不超过两种，避免视觉过载；bento 单屏 ≤6 卡。
4. 条形图数值原文照录（千分位/单位），宽度按最大值归一，不手工换算百分比。
5. 法条卡只放原文关键句，评价另起段落——事实与观点分离。
6. 折叠组件默认展开；打印/导出时强制展开（@media print 已内置）。
7. 二次目录仅当小节 ≥2 时渲染，避免单链接导航条。

## 四、已知边界

- 画板组件不承载交互计算（对比矩阵排序、雷达图叠加等动态需求属 board.py 扩展方向，当前用静态结构）。
- hero_stats 值与正文数据如不一致，以正文为准并在缺口区标注。
- serif 法条字体在无中文字体的 Linux 打印环境回退为 sans，属可接受降级。

## 五、md 一键入口用法（v3.0.4）

hero 头部与八围栏在 Markdown 入口同样可用，零配置：

```yaml
---
title: 报告标题
subtitle: 一句话副标题
audience: 董事会
theme: ocean
hero_badges: 某水务集团 · 季度经营
hero_stats: ["3,327 万元|营业收入", "1,142 万元|净利润"]
hero_pills: 按效付费 · 吨水成本 · 结算审减
---
```

- `hero_stats` 每项 `值|标签`，多项用 `;;` 或列表；引号内逗号（千分位）受保护。
- 八围栏 `:::bar :::bento :::timeline :::matrix :::phase :::law :::faq :::tags` 直接写在章节内，开闭各占一行（闭为单独一行 `:::`）。
- 章内 `###` ≥ 2 时自动生成「本节要点」二次目录；来源章（标题含「来源/参考」）自动抽为「参考来源」分级表；缺口章（含 `:::gap`）自动抽为独立缺口区块。
- 生成后跑 `--check`；`FENCE_LEAK` FAIL 说明有围栏未正确解析（检查拼写与闭合）。
