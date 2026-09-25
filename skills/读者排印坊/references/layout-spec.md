# 版式规范全参数（layout-spec）

> 依据：《读者》杂志实物版式 + GB/T 3179-2009《期刊编排格式》+ 出版专业实务版式设计表 + GB/T 788 开本幅面。
> 用途：本技能所有脚本的默认参数来源；`assets/theme.css` 由此派生。

## 一、开本与幅面

| 开本 | 尺寸（宽×高 mm） | 用途 |
|---|---|---|
| 16开（《读者》本） | 185 × 260 | 默认，杂志风味 |
| A4 | 210 × 297 | 打印/内部资料备选 |
| 32开 | 130 × 184 | 口袋本（次要） |

> WeasyPrint 的 `@page size` 只认绝对长度，写 `185mm 260mm`，不要写 `16k`。

## 二、页边距与版心（16开）

| 部位 | 尺寸 | 说明 |
|---|---|---|
| 天头（上） | 22 mm | 页眉区在内；天头大于地脚 |
| 地脚（下） | 18 mm | 页码区在内 |
| 订口（内） | 18 mm | 装订侧 |
| 切口（外） | 15 mm | 翻页侧 |
| **版心** | **152 × 220 mm** | 宽×高 |

双栏时栏间距 8 mm；单栏版心宽同上。

## 三、字体与字号

| 元素 | 字体族 | 字号 | 备注 |
|---|---|---|---|
| 正文 | 宋体 | 五号 10.5pt | 双栏每栏约 19–20 字 |
| 一级标题（章/栏目） | 黑体 | 小3号 15pt | 居中，占 3–4 行 |
| 篇名（杂志体） | 黑体 | 16.5pt | 与正文拉开约 1.6 倍差 |
| 二级标题（一、） | 标宋 | 4号 14pt | 居左，首行空2字 |
| 三级标题（（一）） | 标宋 | 小4号 12pt | 居左，首行空2字 |
| 四级标题（1.） | 黑体 | 5号 10.5pt | 居左，首行空2字 |
| 书眉（页眉） | 楷体 | 小5号 9pt | 天头，奇偶镜像 |
| 页码 | 宋体（白正体数字） | 小5号 9pt | 地脚外侧 |
| 引文 | 仿宋 | 5号 10.5pt | 整体缩进2字，首行空4字 |
| 图题 | 黑体 | 小5号 8.5–9pt | 图下居中 |
| 首字下沉 | 宋体加粗 | ≈ 2.95em | 见第十一节 |
| 注释 | 仿宋 | 小5号 9pt | 章后/页脚 |

## 四、字体回退链（跨环境关键）

沙箱与多数 Linux 无 SimSun/仿宋，必须写回退链，避免落成豆腐块：

```css
:root{
  --font-song: "Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;
  --font-hei:  "Noto Sans CJK SC","Heiti SC","STHeiti","SimHei",sans-serif;
  --font-kai:  "Kaiti SC","STKaiti","KaiTi","Noto Serif CJK SC",serif;
}
```

线上有真宋体时脚本自动替换为 SimSun；沙箱内以 Noto CJK 兜底。

## 五、行距与缩进

- 正文行距：**1.55 倍**（约 16pt 固定值），疏朗不挤
- 段首缩进：**2 字符**（`text-indent: 2em`）
- 段间距：0（杂志体例靠缩进区分段落）
- 两端对齐：`text-align: justify`
- 孤行寡行：`orphans: 2; widows: 2`

## 六、页眉 / 页脚 / 页码

```
页眉 = 小图 + 篇名 + 栏目名
  奇数页（:right）：篇名在左、栏目名在右
  偶数页（:left） ：篇名在右、栏目名在左
页脚 = 作者名，居中，奇偶相同
页码 = 底端外侧：奇数页右下、偶数页左下；阿拉伯数字，起始 1
卷首语页 = 无页眉页脚，保留页码
```

CSS Paged Media 落地：

```css
@page article:right { @top-left{content:string(article-title)} @top-right{content:string(column-name)} @bottom-center{content:string(article-author)} @bottom-right{content:counter(page)} }
@page article:left  { @top-right{content:string(article-title)} @top-left{content:string(column-name)}  @bottom-center{content:string(article-author)} @bottom-left {content:counter(page)} }
@page cover { @top-left{content:none} @top-right{content:none} @bottom-left{content:none} @bottom-right{content:none} }
```

首页页码置 1 用**分册合并**实现（前置册与正文册分开编译后合并），不依赖 `counter-reset:page`（WeasyPrint 不支持）。

## 七、目次页

- 版面切分：**上部 2/3 排目次表，下部 1/3 排版本记录**
- 目次四要素：**栏目 · 篇名 · 作者 · 页码**（GB/T 3179-2009 §7.4）
- 栏目行：栏目名 + 下边框线，作为分组标题
- 条目行：篇名（左）+ 作者（灰）+ 点线 + 页码（右对齐）
- 目次行用 **table 布局**（`display:flex` 会在 WeasyPrint 分页时塌陷）
- 目次页不计入正文连续页码

## 八、色彩（《读者》暖调）

| 槽位 | 色值 | 用途 |
|---|---|---|
| 页面底 | #FBF8F0 | 内页淡黄纸底色 |
| 墨色 | #1A1A1A | 正文 |
| 栏目色 | #8C2F2F | 栏目名/页眉/期号框/首字（深赭红） |
| 辅助线 | #D9CFBE | 分隔线/边框 |
| 强调 | #2F5D62 | 卷首语引文/题花 |

## 九、纸张用料（对标说明，非电子约束）

- 封面/彩页：120g 铜版纸
- 内页：70g 高级淡黄色书写纸（护眼）

## 十、封面构成

```
顶栏双线（赭红+灰）→ 右上同心圆装饰 → 书名（42pt 黑体赭红）
→ 副题（14pt 楷体） → 期号方框（描边，12pt 黑体） → 导语（11pt 楷体）
→ 底部署名（11pt 楷体）+ 出版信息行（9pt，上叠细线）
```

封面不编页眉页脚、不编正文页码（`@page cover`）。

## 十一、图片与首字下沉规范（v1.1 新增）

**图片两类**
| 类型 | 语法 | 形态 | 适用 |
|---|---|---|---|
| 跨栏大图 | `![题注](路径){wide}` | 通栏（列宽=版心152mm），`column-span:all` | 开篇氛围图、章节图 |
| 栏内浮图 | `![题注](路径)` | 栏内左浮，宽≈44%，文字环绕 | 文内小图、装饰图 |

- 图题：居中，黑体 8.5–9pt，居中于图下，与图间距 2.6mm
- 图片不得溢出栏宽（`img{max-width:100%}`）；跨栏图 `break-inside:avoid`
- 图片来源：自有或已授权。程序化装饰图仅作版式占位，正式使用须替换为实拍/授权图

**首字下沉（drop cap）**
```
卷首语默认启用（manifest 的 "dropcap": true/false 可覆盖）
字高 ≈ 3 行；顶部对齐首行顶线、底部对齐第 3 行底线
font-size ≈ 2.95em、line-height 1.0、margin-top ≈ 0.24em、右侧留 3.8mm
族：宋体加粗（与正文同族，避免突兀）；色：深赭红
```
> 微调关键：float 元素的 `margin` 以 `em` 计，`em` 相对**该元素自身 font-size**（约 31pt），故位移量 = em × 31pt，需按此换算。

**引文提花**：左 3pt 赭红竖条 + 5.5% 赭红底 + 大号引号（`::before`），上下间距 5.5mm。

**篇末花饰**：`◆ ◆ ◆` 居中，赭红，字距 0.6em。

## 十二、完整参数可机器读取

`$S/scripts/style_builder.py --json` 输出全参数 JSON，供成书脚本消费；改版式只改此脚本参数，不要手改 theme.css。


## 十三、主题换肤（联动 theme-factory，v1.2）

- 色板来源：theme-factory 技能 10 套主题（色值取自 themes/*.md，不手抄）
- 槽位映射：主题四色 → paper（底）/ ink（正文）/ column（栏目）/ rule（线）/ accent（强调）；muted 由 ink 与 paper 混合派生
- 对比度门禁：正文/底 ≥4.5、栏目/底 ≥3.0；不达标时同色系提亮底色或加深栏目色，并在规格表标注 derived
- 调用：`style_builder.py --list-themes` 列主题，`--theme <name>` 生成对应 theme.css；`book_builder.py --theme <name>` 直接出成品
- 映射表与校验值存放：`assets/themes.json`
- 栏目扉页：manifest 设 `"column_pages": true` 开启，每栏目首页前加整页大栏目名（无页眉，编连续页码）

| 主题 | 底色 | 正文 | 栏目 | 正文/底 |
|---|---|---|---|---|
| ocean-depths 深海之境 | #f1faee | #1a2332 | #2d8b8b | 14.77 |
| sunset-boulevard 落日大道 | #e9c46a | #264653 | 同色系加深红 | 6.03 |
| forest-canopy 森林之冠 | #faf9f6 | #2d4a2b | #2d4a2b | 9.38 |
| modern-minimalist 现代极简 | #ffffff | #36454f | #708090 | 9.90 |
| golden-hour 金色时刻 | #d4b896 | #4a403a | 同色系加深 | 5.32 |
| arctic-frost 极地霜华 | #fafafa | #4a6fa5 | #4a6fa5 | 4.90 |
| desert-rose 沙漠玫瑰 | #e8d5c4 | #5d2e46 | 同色系加深 | 7.58 |
| tech-innovation 科技创新 | #ffffff | #1e1e1e | #0066ff | 16.67 |
| botanical-garden 植物园 | 提亮底 | #4a7c59 | #b7472a | 4.53 |
| midnight-galaxy 午夜星河 | #e6e6fa | #2b1e3e | #4a4e8f | 12.57 |


## 十四、手绘线稿配图（v1.4，对接 qf-lineart 引擎）

- 引擎：`qf-lineart`（手绘线稿插图引擎）正本位于 `qf-lineart/scripts/lineart_engine.py`；本技能 `scripts/lineart_engine.py` 为随包副本，`scripts/illustration_draw.py` 为对接入口（三级解析：随包副本 → qf-lineart 技能 → 工作区软链）
- 母题库（16 类）：叶 leaf / 芽 sprout / 山 mountain / 窗 window / 灯 lamp / 书 book / 鸟 bird / 云 cloud / 月 moon / 水波 ripple / 舟 boat / 纹样 pattern / 一盏茶 tea / 桥 bridge / 星 star / 小屋 home
- 笔触（5 种）：fountain 钢笔 / pencil 铅笔（本刊默认）/ brush 毛笔 / marker 马克笔 / charcoal 炭笔
- 配色（7 套暖色墨）：sepia 暖褐（本刊默认）/ ochre 赭石 / amber 暖金 / terracotta 陶土 / rosewood 玫瑰木 / olive 暖橄榄 / ink 传统墨
- 自动选题：按标题与正文的关键词命中数排序，取前 2–3 个母题；无命中时按 fallback 补齐
- 落位规则：第 1 张作跨栏大图（放第 2 段后）、第 2 张作栏内浮图（放中段）、第 3 张靠后（inline-end）
- 尺寸：跨栏图 1500×820、栏内图 760×980；线宽基准 1.35（跨栏）/ 1.7（栏内），保证缩至版面后仍清晰
- 线色口径：暖色墨对版面底色对比度不低于 4.5（本册 sepia 对米黄纸 7.37）；不使用写实图与 AI 生成图，避免版权问题
- 全册统一：清单 JSON 的 `illustration` 字段写 `{"palette": "sepia", "style": "pencil"}` 覆盖命令行默认
- 调用：`illustration_draw.py --list-motifs / --list-styles / --list-palettes` 看清单；`--manifest book.json --per-article 3 --outdir samples/images/auto --out auto_images.json --palette sepia --style pencil` 批量配图；`book_builder.py --auto-images auto_images.json` 落位
