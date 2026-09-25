---
name: theme-factory
version: 1.1.0
author: 清风明月
description: 专业视觉主题工厂——内置 10 套成套主题（Ocean Depths、Sunset Boulevard、Forest Canopy、Modern Minimalist、Golden Hour、Arctic Frost、Desert Rose、Tech Innovation、Botanical Garden、Midnight Galaxy），每套含四色色板（hex 值）与标题/正文字体配对，可套用到 PPT、Word 文档、HTML 页面、汇报报告与信息图，也能按场合现场生成自定义主题并输出主题应用规格表。用于给汇报、演示、报告、方案统一视觉风格：选定主题、读取 themes/ 下的主题文件、把色彩与字体按槽位落到目标成品、逐项校验对比度与字体回退链。触发词：主题工厂、主题配色、PPT 配色、幻灯片配色、换主题、配色方案、统一视觉风格、配色表、字体配对、theme、theme factory、color palette、apply theme。
---

## 〇、专家级路由（v1.1.0）

**专家定位**：视觉主题工厂，把零散的配色灵感落成可复用、可验证、可交付的成套主题规格，让一份材料从头到尾只有一个视觉身份。

**五维评估**：
- 适用场景：幻灯片/汇报 PPT、Word 报告与方案、HTML 页面与信息图、图表配色的统一换肤。
- 能力边界：只做色彩与字体的成套规格与落地，不做品牌 VI 全套设计、印刷色卡管理、字体版权采购。
- 依赖资产：themes/ 下 10 个主题规格文件、theme-showcase.pdf 总览、LICENSE.txt 使用条款；管理规范见 references/quality-checklist.md。
- 交付质量：成品 + 主题应用规格表 + 对比度与字体回退校验记录，三件齐交。
- 性能表现：单份材料换肤 1 轮内落地，全套材料统一 2 轮内收敛。

**四级响应（L1-L4）**：
- L1 轻量：单个 HTML/单页 → 直接给出 4 个色彩变量与 2 个字体变量。
- L2 标准：一份 PPT 或 Word 换肤 → 读 themes/*.md，按槽位落地，出规格表。
- L3 复杂：多份材料统一视觉体系 → 主题规格表 + 对比度校验 + 字体回退链 + 抽页复核。
- L4 专家：自定义主题生成并落地全套材料 → 命名入库、对比度全检、更新案卷 references/case-library.md。

**黄金窗口**：主题选定确认后 1 轮内完成落地；一次会话内不超过 2 次往返确认。

**专家件索引**：references/case-library.md（案例登记模板与来源指引）、references/quality-checklist.md（15 项质量门）、references/output-template.md（主题应用规格表骨架）。

## 一、定位声明

本技能提供成套的专业色彩与字体主题。每套主题由四色色板（hex 值）+ 标题字体 + 正文字体 + 适配场合构成，可套用到任何已生成或将生成的材料：幻灯片、Word 文稿、HTML 页面、汇报报告、信息图。装配依据为源技能方法论四条主干：选主题 → 读主题文件 → 按槽位应用到成品 → 校验对比度与一致性。10 套主题逐套规格存放于 themes/ 目录，可视总览为 theme-showcase.pdf，使用条款见 LICENSE.txt。

## 二、触发条件

**中文触发词**：主题工厂、主题配色、PPT 配色、幻灯片配色、换主题、配色方案、统一视觉风格、配色表、字体配对、给汇报配色、报告配色。

**英文触发词**：theme、theme factory、color palette、apply theme、slide theme、font pairing、deck styling。

**触发场景**：
1. 用户提交一份幻灯片/文档/HTML，要求"换个配色""统一风格""配个色"。
2. 用户询问有哪些可用主题、某套主题的色值或字体是什么。
3. 用户给出场合（政务汇报、财务、环保、科技发布、婚礼策划）要求挑选或定制主题。
4. 用户要求把同一套主题应用到多份材料，需要一致性保证。

## 三、常驻规则

1. themes/ 下 10 个主题文件、theme-showcase.pdf、LICENSE.txt 均为只读资产，任何情况下不得删改，展示与读取不改变文件本身。
2. 一切色彩取自主题文件的 hex 值或用户明确给定的值，严禁凭印象编造色值、字体名或主题名。
3. 正文文字与背景的对比度须 ≥4.5:1，大字与图形元素须 ≥3:1，未达标不得交付。
4. 主题选定属用户决策，落笔前须获明确确认，不得替用户拍板。
5. 中文材料必须补齐中文字体回退链，拉丁字体不可直接充当中文正文字体。
6. 交付时随附主题应用规格表，字段套用 references/output-template.md 骨架。

## 四、标准工作流

1. **呈现总览**。输入：用户材料与场合信息。动作：展示 theme-showcase.pdf 供用户比较，只读不改。输出：候选主题总览说明。
2. **读取主题规格**。输入：用户初选主题名。动作：读取对应 themes/*.md，取回色板、字体、适配场合。输出：该主题的完整规格快照（如 themes/ocean-depths.md）。
3. **确认选择**。输入：规格快照。动作：报出主题名、四色 hex、字体配对与场合匹配度，停在确认点等用户答复。输出：经确认的主题名与替换方案。
4. **建立槽位映射**。输入：目标材料的样式结构。动作：把主题四色映射到 background / primary / accent / text 四个槽位，字体映射到 heading / body 两个槽位。输出：槽位映射表。
5. **落地应用**。输入：槽位映射表与目标文件。动作：按对象类型改写样式（PPT 母版与主题色、Word 样式集、HTML 的 CSS 变量、Markdown 导出样式表），同类元素在全篇保持同一色与同一字体。输出：换肤后的成品文件。
6. **校验对比度与字体链**。输入：成品样式。动作：用正文的核算代码复算正文/背景、强调色/背景对比度，检查中文字体回退链是否闭合。输出：校验数值记录。
7. **抽页复核**。输入：成品文件。动作：抽封面、正文页、图表页各一页核对色值与字体是否与规格表一致，核对图表配色是否与主题同源。输出：复核结论。
8. **出规格表并交付**。输入：全流程记录。动作：按 references/output-template.md 填规格表，标注降级项与【待核】项。输出：成品 + 规格表 + 校验记录。

## 五、核心方法与命令

**10 套内置主题速查表**（名称 / 定位 / 主色系 / 适配场合，完整规格见 themes/ 下同名文件）：

| 主题 | 定位 | 主色系（hex） | 字体（标题/正文） | 适配场合 |
|---|---|---|---|---|
| Ocean Depths 深海之境 | 专业沉静的海事调 | 深海军蓝 `#1a2332`、青绿 `#2d8b8b`、海沫 `#a8dadc`、奶油 `#f1faee` | DejaVu Sans Bold / DejaVu Sans | 企业汇报、财务报告、咨询方案 |
| Sunset Boulevard 落日大道 | 温暖热烈的日落调 | 焦橙 `#e76f51`、珊瑚 `#f4a261`、暖沙 `#e9c46a`、深紫 `#264653` | DejaVu Serif Bold / DejaVu Sans | 创意提案、营销方案、生活方式 |
| Forest Canopy 森林之冠 | 自然沉稳的大地色 | 森林绿 `#2d4a2b`、鼠尾草 `#7d8471`、橄榄 `#a4ac86`、象牙 `#faf9f6` | FreeSerif Bold / FreeSans | 环保汇报、可持续报告、健康内容 |
| Modern Minimalist 现代极简 | 干净克制的灰阶 | 炭灰 `#36454f`、石板灰 `#708090`、浅灰 `#d3d3d3`、白 `#ffffff` | DejaVu Sans Bold / DejaVu Sans | 技术方案、架构作品集、数据可视化 |
| Golden Hour 金色时刻 | 浓郁温暖的秋色调 | 芥末黄 `#f4a900`、陶土红 `#c1666b`、暖米 `#d4b896`、巧克力棕 `#4a403a` | FreeSans Bold / FreeSans | 餐饮酒店、节庆物料、手作品牌 |
| Arctic Frost 极地霜华 | 清冷精准的冬日调 | 冰蓝 `#d4e4f7`、钢蓝 `#4a6fa5`、银灰 `#c0c0c0`、净白 `#fafafa` | DejaVu Sans Bold / DejaVu Sans | 医疗健康、科技方案、清洁能源 |
| Desert Rose 沙漠玫瑰 | 柔和高级的灰调粉 | 灰玫瑰 `#d4a5a5`、陶土 `#b87d6d`、沙色 `#e8d5c4`、深酒红 `#5d2e46` | FreeSans Bold / FreeSans | 时尚美妆、婚礼策划、室内设计 |
| Tech Innovation 科技创新 | 高对比前卫科技感 | 电光蓝 `#0066ff`、霓虹青 `#00ffff`、深灰 `#1e1e1e`、白 `#ffffff` | DejaVu Sans Bold / DejaVu Sans | 产品发布、创业路演、AI 展示 |
| Botanical Garden 植物园 | 清新有机的花园色 | 蕨绿 `#4a7c59`、万寿菊黄 `#f9a620`、陶土红 `#b7472a`、奶油 `#f5f3ed` | DejaVu Serif Bold / DejaVu Sans | 园艺食品、农场到餐桌、自然产品 |
| Midnight Galaxy 午夜星河 | 戏剧性的深空紫 | 深紫 `#2b1e3e`、宇宙蓝 `#4a4e8f`、薰衣草 `#a490c2`、银 `#e6e6fa` | FreeSans Bold / FreeSans | 娱乐活动、游戏发布、奢侈品展示 |

**步骤 A：读取主题规格与预览资产**

```bash
# 列出 10 套主题文件与总览资产（只读）
ls themes/*.md
ls theme-showcase.pdf LICENSE.txt

# 取回选定主题的完整规格（色板 + 字体 + 适配场合）
cat themes/ocean-depths.md

# 核对输出规格表骨架，按字段填写
sed -n '1,40p' references/output-template.md

# 交付前逐条对照质量门
sed -n '1,60p' references/quality-checklist.md
```

**步骤 B：对比度核算（交付前必跑）**

```python
python3 - <<'PY'
import pathlib, re

def lum(hexcolor):
    c = [int(hexcolor[i:i+2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)

# 从主题文件解析色值，避免手抄出错
spec = pathlib.Path("themes/ocean-depths.md").read_text(encoding="utf-8")
hexes = re.findall(r"#([0-9a-fA-F]{6})", spec)
print("主题色值:", ["#" + h for h in hexes])
navy, teal, seafoam, cream = ["#" + h for h in hexes[:4]]
print("正文/背景 :", ratio(navy, cream), "（须 ≥4.5）")
print("强调/背景 :", ratio(teal, cream), "（须 ≥3.0）")
print("次级/背景 :", ratio(seafoam, cream), "（须 ≥3.0）")
PY
```

**步骤 C：槽位落地（HTML 版，CSS 变量）**

```css
:root{
  --tf-bg:      #1a2332;   /* background：页面/画布底色 */
  --tf-primary: #2d8b8b;   /* primary：主色，标题条与图表主系列 */
  --tf-accent:  #a8dadc;   /* accent：强调块、图示高亮 */
  --tf-text:    #f1faee;   /* text：正文与浅底 */
  --tf-font-head: "DejaVu Sans", "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;
  --tf-font-body: "DejaVu Sans", "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;
}
```

**步骤 D：配色配比与中文字体回退**

- 配比按 60/30/10：底色 60%，主色与中性面 30%，强调色 10%，强调色只用于标题条、关键数字与图表重点系列。
- 字体回退链固定为"主题拉丁字体 → 中文字体（Noto Sans CJK SC / Source Han Sans SC / 微软雅黑）→ 通用族"，使拉丁字符走主题字体、汉字走中文字体。
- PPT/Word 落地时同步改主题色板与样式集，不只改单页；图表系列的色序按 primary → accent → 中性色排布。

**步骤 E：自检**

```
python3 wikiskill/scripts/wikiskill_audit.py --only theme-factory --sort score
```

**步骤 F：一键落地（scripts/theme_apply.py）**

主题落地器把"选主题 → 注入四色两字体 → 校验"合成一条命令，可直接接在任意 HTML 生成技能之后，实现"生成即换肤"。

```bash
python3 scripts/theme_apply.py list                             # 列出 10 套主题与色板
python3 scripts/theme_apply.py info forest-canopy               # 单套主题槽位与对比度
python3 scripts/theme_apply.py apply -t ocean-depths -i 报告.html -o 报告_深海之境.html
python3 scripts/theme_apply.py apply -t forest-canopy -i 报告.html --mode dark
python3 scripts/theme_apply.py apply -t tech-innovation -i 报告.html --keep "#123456"
python3 scripts/theme_apply.py demo -o 主题工厂演示.html        # 10 套主题实时切换演示页
python3 scripts/theme_apply.py palette -o 主题色板总览.png      # 色板总览图
python3 scripts/theme_apply.py check "#1a2332" "#f1faee"        # 对比度校验
```

- 双策略换肤：优先重写目标 `:root` 的通用 CSS 变量；无变量可改时，退回对硬编码色值的映射，按明度与饱和度归入 bg / ink / primary / sub / line 五类槽位，并输出映射表供核对。
- 语义色豁免：警示红 `#c0392b`、通过绿 `#6da33f`、提示黄 `#d99b1a` 等列入豁免名单，不随主题变化，保证"达标 / 预警"判断在全套材料中含义一致。
- 中文字体回退链自动补齐，拉丁字体不充当中文正文字体；执行顺序固定为先映射色值、后注入变量，避免注入色被二次替换。
- 与 HTML 生成类技能串联：先生成 HTML，再 `apply` 换肤，最后一并交付；同一批材料固定同一主题，即得统一视觉身份。

## 六、输出规范

1. **交付三件**：换肤后的成品文件；主题应用规格表（骨架取自 references/output-template.md）；校验记录（对比度数值、字体回退链、抽页复核结论）。
2. **规格表字段**：目标文件、主题名、四色槽位映射、字体槽位映射、对比度数值、降级或【待核】项、复核页清单。
3. **命名**：自定义主题按"形容词 + 名词"命名，与既有 10 套语义不重叠，文件中给出四色 hex 与字体配对。
4. **格式**：全文 UTF-8；除 🔴 外不使用 emoji；色值统一写作 `#rrggbb` 小写。
5. **语言**：规格表与说明用中文，主题英文名首次出现时附中文注名。

## 七、边界与反模式

- **不在范围**：品牌 VI 全套设计与商标规范、印刷 CMYK 色卡与专色管理、字体商业授权采购、视频调色与三维渲染。
- **禁止**：改动或删除 themes/*.md、theme-showcase.pdf、LICENSE.txt；臆造主题名、色值、字体名；把对比度未达标的配色交付。
- **红线**：正文文字与背景对比度 <4.5:1 即不得交付；中文字体回退链缺失导致汉字回退到系统默认字体，同样视为未达标。
- **反模式**：同一份材料混用多套主题；霓虹色（如 Tech Innovation 的霓虹青）大面积铺底；把强调色当正文色；只改封面不改内页样式集。
- **不适用**：仅需一句话色值查询的问答（直接答 hex 即可，不必走全流程）；材料尚未成形时的空谈配色。
- **不要**：在用户未选定主题时替其拍板；把候选主题数量堆到三套以上，令选择成本高于收益。

## 八、失败模式与降级

| 失败模式 | 触发条件 | 降级动作 |
|---|---|---|
| 主题文件不可读 | themes/*.md 路径失效或读取报错 | 用本正文速查表的四色 hex 兜底成稿，规格表标注【待核：完整规格】 |
| 总览无法预览 | theme-showcase.pdf 打不开或不可渲染 | 以速查表 + 色块文字说明替代呈现，不臆造截图 |
| 主题字体缺失 | DejaVu/FreeSans 未安装 | 走回退链至 Noto Sans CJK SC / Source Han Sans SC，规格表记录替换 |
| 对比度不达标 | 复算值 <4.5:1（正文）或 <3:1（大字与图形） | 换用主题内更深/更浅一档色充当文字色，重算至达标；仍不达标则改选主题 |
| 用户迟迟不选主题 | 两轮追问仍未定 | 按场合给出 2 套候选并附对比度数据，停在选择点等确认 |
| 自定义主题与既有重复 | 新主题色系与 10 套中某套高度重合 | 复用既有主题，不重复建档 |
| 应用后样式串味 | 页面局部仍残留旧主题色或旧字体 | 全篇检索旧色值/旧字体名并清空，异常项记入规格表 |
| 多材料不同源 | 同一套主题落到多份材料后口径不一 | 以规格表为唯一基准逐份回改，改完复核三件齐备 |

## 九、关键检查点

- 🔴 **主题选定确认**：完成步骤 3 前不进入落地；未获用户明确答复即停止。
- 🔴 **对比度达标**：步骤 6 复算值写入规格表；不达标不交付。
- 🔴 **字体回退链闭合**：中文材料的 heading/body 槽位必须挂中文字体，缺链暂停交付。
- 🔴 **只读资产保护**：交付前核对 themes/*.md、theme-showcase.pdf、LICENSE.txt 未被改动，校验和不一致即停止并回报。
- 🔴 **自定义主题入库确认**：新建主题须经用户确认命名与四色后方可写入规格表与案卷。
- 🔴 **抽页复核**：封面、正文页、图表页各抽一页对照规格表，三页全部一致方可交付。

## 十、实战范例

**范例一：单页 HTML 汇报套用 Ocean Depths**

输入：一份汇报 HTML，用户指定"要专业、沉稳"。动作：读 themes/ocean-depths.md；四色入槽位；写入 CSS 变量；复算对比度。命令与预期输出：

```
$ cat themes/ocean-depths.md    # 取回 4 色与字体
$ python3 - <<'PY' ... PY       # 复算对比度
主题色值: ['#1a2332', '#2d8b8b', '#a8dadc', '#f1faee']
正文/背景 : 14.32 （须 ≥4.5）
强调/背景 : 3.56 （须 ≥3.0）
次级/背景 : 1.42 （须 ≥3.0）
```

据此判断：海沫 `#a8dadc` 不可承担文字或小图标，只作装饰色块；交付规格表在 accent 槽位注明"仅装饰，不作文字色"。

**范例二：产品发布 PPT 换肤为 Tech Innovation**

输入：24 页产品发布 PPT。动作：读 themes/tech-innovation.md；电光蓝 `#0066ff` 作 primary，深灰 `#1e1e1e` 作 background，白 `#ffffff` 作 text，霓虹青 `#00ffff` 仅作 10% 强调；同步改母版主题色与图表色序。预期输出：PPT + 规格表，规格表标注"霓虹青仅用于强调，不得用于正文或大面积色块"，抽页复核封面、第 8 页数据页、第 18 页图表页三页一致。

**范例三：自定义主题生成**

输入：环保宣讲场合，用户要求"接近自然、但不能与既有主题雷同"。动作：起草四色（深底 + 主色 + 辅助 + 浅底），按"形容词 + 名词"命名，复算对比度，经用户确认后写入规格表并按 references/case-library.md 模板登记案卷。预期输出：

```
主题名：Moss Stream 苔溪
槽位：bg #22302c / primary #3f7d6a / accent #cbb98a / text #f4f1e9
字体：FreeSerif Bold / FreeSans（heading / body）
对比度：正文/背景 11.8（≥4.5 通过）
确认项：主题名与四色 → 经用户确认后写入规格表
```

登记后依 references/quality-checklist.md 逐条勾选，缺失项标【待核】。

## 十一、依赖说明与降级

1. **必备资产**：themes/ 下 10 个主题文件（色板与字体来源）、theme-showcase.pdf（可视总览）、LICENSE.txt（使用条款）。三者均在技能目录内，不依赖网络。
2. **运行环境**：对比度核算只需 Python 3 标准库；如需批量改写 PPT/Word 样式，另装 python-pptx / python-docx，缺失时改为手工改样式集并在规格表记录操作路径。
3. **字体依赖**：DejaVu、FreeSans 属于常见自由字体，环境缺失时按回退链降级，降级不改变色板取值。
4. **降级原则**：任一资产或依赖不可用时，改走正文速查表兜底，并在规格表逐项标注【待核】，不得中断交付，也不得静默略过。
5. **条款边界**：资产使用范围以 LICENSE.txt 为准，超出范围的使用须由用户自行确认授权。

## 十二、版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.1.0 | 2026-09-17 | 新增 scripts/theme_apply.py 主题落地器（list / info / apply / demo / check / palette 六子命令）：双策略换肤（CSS 变量重写 + 色值映射）、语义色豁免、10 套主题槽位标定表、中文字体回退链自动补齐、对比度校验；可接在任意 HTML 生成技能之后实现"生成即换肤" |
| 1.0.0 | 2026-09-17 | ima 专家级中文改造：补专家级路由、12 节骨架、10 套主题速查表、对比度核算与字体回退链方法；新建 references/case-library.md、references/quality-checklist.md、references/output-template.md 三件；源技能资产 themes/、theme-showcase.pdf、LICENSE.txt 原样保留 |

## 依赖安装

本技能脚本依赖第三方库，首次使用（或沙箱/换机重置）后请先安装：

```bash
python3 -m pip install -r requirements.txt
```

## HTML 底座（已内嵌 · 可选增强）

本技能已内嵌 html-report-builder 底座 5 脚本（`scripts/htmlbase/`：md2report.py / palettes.py / build_report.py / board.py / html_check.py），自包含运行。

**本技能的主输出仍走其专用渲染器**（保证特有版式与交互不被替换）；当需要输出一份通用报告页/说明页（非本技能专用版式）时，直接调用内嵌底座：

```bash
python3 scripts/htmlbase/md2report.py <成稿md> -o <名称>_成果页.html --theme <配色id> --check
```

底座升版后用 `python3 scripts/sync_htmlbase.py --all --apply` 重新分发。
