---
name: 姓氏溯源
version: 1.1.0
description: "姓氏溯源技能——输入任意姓氏，查询其起源源流、郡望堂号、历史名人，并生成全国/省/地区三级人口分布可视化 HTML 报告。数据源自公安部《全国姓名报告》与第七次全国人口普查（全国排名与人口），地区级采用姓氏地名密度反推法（高德 POI）侧面反映宗族聚居。输出为单文件自包含 HTML，含 KPI 卡、源流考据、郡望堂号、交互地图与免责声明。触发场景：百家姓、姓氏起源、查姓氏、姓氏分布、我的姓氏、同姓分布、郡望堂号、姓氏溯源、寻根问祖、姓什么。中英触发词：百家姓、姓氏起源、姓氏分布、姓名报告、寻根问祖、surname、family name、surname distribution。不适用于：族谱编纂与家谱校对、基因溯源与血缘鉴定、名人谥号谥法等非姓氏查询场景。"
author: 清风明月
display_name: 姓氏溯源
slug: qf-surname-atlas
category: 教育
tags: [传统文化, 百家姓, 姓氏, 数据可视化, 人口分布]
---

# 姓氏溯源

## 专家定位

以「文化解读 + 数据可视化」为基调的姓氏文化工具。将公安部官方姓名报告数据、公版姓氏学典籍与高德地图能力整合，输出既有考据深度、又具可视化表现力的姓氏报告。定位为**文化溯源与数据可视化**，不做算命、改运或吉凶判断。

## 适用边界

**适用**：查姓氏起源源流、郡望堂号、历史名人；看全国/省/地区人口分布；生成可视化姓氏报告。

**不适用**：族谱编纂与家谱校对（属专门谱牒工作）；基因溯源与血缘鉴定（属科学检测）；名人谥号、名号考释（非姓氏查询）。

## 数据来源与口径

| 层级 | 来源 | 口径 |
|---|---|---|
| 全国排名 | 公安部户政管理研究中心《二〇一九年全国姓名报告》 | 官方，按户籍人口数量排序 |
| 全国人口 | 第七次全国人口普查·百家姓排名（2022年发布） | 官方约数，前10位有逐姓数据 |
| 省级第一大姓 | 公安部《二〇一九年全国姓名报告》 | 官方，31省区市逐省公布 |
| 省级人口 | 按「全国占比 × 省常住人口」估算（省常住人口用2020七普） | 【估算值】，非官方逐省统计 |
| 地区级 | 姓氏地名密度（高德 POI：姓+村/庄/家/营/寨/屯） | 侧面证据，不作人口数字断言 |

**口径纪律**：官方数据标来源；估算值一律带【估算值】；地区级只作侧面参考。

## 工作流程

1. **识别姓氏**：从用户输入提取姓氏（含复姓，如欧阳）。
2. **基础查询**：运行 `scripts/surname_query.py` 取排名、人口、源流、郡望、堂号、名人。
3. **三级测算**：运行 `scripts/pop_calc.py` 出全国/省级口径。
4. **地名扫描**：需要地区级视角时，运行 `scripts/place_scan.py` 扫描姓氏地名密度。
5. **渲染报告**：运行 `scripts/report_render.py` 装配底稿并产出单文件 HTML。

## 脚本工具

**1. 姓氏基础查询**

```bash
python3 scripts/surname_query.py --surname 王
python3 scripts/surname_query.py --surname 王 --format json
python3 scripts/surname_query.py --list 20
```

**2. 三级人口测算**

```bash
python3 scripts/pop_calc.py --surname 王 --province 陕西
python3 scripts/pop_calc.py --surname 王 --province 陕西 --format json
```

**3. 姓氏地名扫描（需环境变量 AMAP_KEY）**

```bash
python3 scripts/place_scan.py --surname 王 --city 西安 --format json > scan.json
```

**4. 报告渲染（HTML 基座 v9）**

```bash
python3 scripts/report_render.py --surname 王 --province 陕西 --city 西安 \
  --scan-json scan.json --out 王姓溯源报告.html
```

配色用 `--theme`（golden/sunset/forest/ocean/minimal/botanical/galaxy/arctic/desert/tech），版式用 `--motif`（editorial/narrative/blueprint/classic）；基座缺失时加 `--no-base` 走简易模板。

## 输出规范

1. 报告为单文件自包含 HTML，含 KPI 卡、源流考据、郡望堂号、迁徙分布、本省本地五章以上；
2. 每章正文不少于 300 字；
3. 页脚固定免责声明「本内容属中国传统文化研究范畴，供文化了解与民俗参考，不构成任何决策依据」；
4. 渲染后须跑 html_check.py，要求 FAIL=0。

**默认配图**：报告默认内嵌「姓氏人口排名示意」（对应一章，全国前十姓条形图 + 本姓排名定位，本姓自动高亮）。该图由 `scripts/diagram.py` 依排名数据程序化绘制为 SVG，随报告生成并 base64 内嵌，零外部依赖、零版权风险；输出目录下会同步留存 `images/` 原图。图注已声明数字为约数。加 `--no-images` 可关闭配图。

## 🔴 关键检查点（执行前必读）

- 🔴 **数据溯源**：所有人口数字须标注来源；省级估算值必须带【估算值】，不得将估算当官方数据输出。
- 🔴 **红线把关**：全文不得出现算命、改运、吉凶、旺衰等表述，只做文化解读。
- 🔴 **围栏语法**：`:kpi` 等围栏须单独成行，内容行用竖线分隔；行内写内容会导致围栏泄漏（FENCE_LEAK FAIL）。
- 🔴 **密度校验**：渲染后必须跑 html_check，DENSITY 未达 300 字/章须补足底稿再交付。
- 🔴 **高德降级**：AMAP_KEY 缺失或限流时，地区级扫描降级为说明文字，不得中断报告生成。

## 失败模式

1. **数据集未收录**：查询不在前100大姓与前20详细源流库中的姓氏，surname_query 返回空并退出码 2；此时应改出通用源流说明，不编造具体源流。
2. **高德限流/超时**：place_scan 连续调用触发 429 或超时，脚本已内置 0.5s 间隔与逐词重试；仍失败则该章降级为说明文字。
3. **围栏泄漏**：把 `:kpi「...」` 写成行内会残留原文（FENCE_LEAK FAIL），须改为块状写法。
4. **密度不足**：底稿各章偏短会触发 DENSITY FAIL/WARN，须为每章补足 300 字以上有信息量的正文。
5. **基座副本缺失**：`scripts/htmlbase/` 未就位时报告降级为简易模板，须先补齐基座副本。
6. **复姓误切**：单字切分会把「欧阳」拆成「欧」，须先按复姓表整体匹配。

## 反例黑名单

- ✗ 用估算值冒充官方口径；
- ✗ 输出「你姓王，一生大富大贵」类判断；
- ✗ 编造未收录姓氏的具体源流；
- ✗ 把地区级地名密度换算成人口数字；
- ✗ 报告缺少免责声明。

## 专家件索引

- `references/origin-methodology.md`：姓氏起源考据方法与六类源流
- `references/data-caliber.md`：三级数据口径与精度说明
- `references/quality-checklist.md`：交付前质检清单
- `references/failure-modes.md`：失败模式与处置
- `references/case-library.md`：案例登记模板与检索指引

## 使用示例

**示例一**：用户说「我姓王，帮我查查王姓的起源和分布」，则依次跑 surname_query、pop_calc，再 report_render 生成《王姓溯源与人口分布》HTML。

**示例二**：用户说「看看西安有多少姓王的」，则跑 place_scan --surname 王 --city 西安，以姓氏地名密度呈现，并说明其为侧面证据。

**示例三**：用户说「全国前20大姓有哪些」，则跑 `surname_query.py --list 20` 输出排名表。
