# 单文件工程规范与自检细则（output-spec）

## 一、十二条硬约束的判定方法

| # | 约束 | 判定方法 | 常见违反 |
|---|---|---|---|
| 1 | 单文件自包含 | 全文搜索 `<link rel="stylesheet"`、`<script src=`，命中即为违反 | 从模板粘贴时带入了 CDN 引用 |
| 2 | 素材内嵌 | 搜索 `src="http`、`url(http`，命中即为违反 | 引用在线图片或图标字体 |
| 3 | 离线可用 | 断网打开页面，逐项点按 | 图表依赖外部 JS 库 |
| 4 | 字符集与视口 | 检查 `<meta charset>` 与 `<meta name="viewport">` | 手写骨架时漏视口声明 |
| 5 | 语言声明 | `<html lang="zh-CN">` | 用编辑器模板生成的页面常缺 |
| 6 | 标题唯一 | 统计 `<h1>` 数量为 1 | 每个章节都用 h1 |
| 7 | 图片带 alt | 统计 `<img>` 中缺 `alt` 的数量 | 装饰图未加空 alt |
| 8 | 打印适配 | 搜索 `@media print` | 只做屏幕样式 |
| 9 | 弱底打印优先 | 纸质分发时选浅色主题 | 深色页直接打印 |
| 10 | 目录与返回顶部 | 章节 ≥4 时页面含锚点导航 | 长页面无导航 |
| 11 | 体积上限 | 单文件 ≤300KB | 内嵌多张大图 |
| 12 | 免责与来源 | 页脚含数据来源行与成文日期 | 只写标题与正文 |

## 二、自检项与代码对照

`html_check.py` 输出的代码与含义：

| 代码 | 级别 | 含义 | 修复动作 |
|---|---|---|---|
| META_CHARSET | FAIL | 缺字符集声明 | 补 `<meta charset="UTF-8">` |
| META_VIEWPORT | FAIL | 缺视口声明 | 补 viewport meta |
| HTML_LANG | FAIL | html 缺 lang | 补 `lang="zh-CN"` |
| TITLE | FAIL | 缺页面标题 | 补 `<title>` |
| EXTERNAL_RES | FAIL | 有外部资源引用 | 内嵌样式与素材 |
| SELF_CONTAINED | WARN | 未同时检测到内嵌样式与脚本 | 确认自包含与交互需求 |
| PLACEHOLDER | FAIL | 有未替换占位符 | 替换为空值或真实内容 |
| TODO_LEFT | WARN | 有待办/待补字样 | 换成缺口徽标或补齐 |
| TAG_BALANCE | FAIL | 标签不配对 | 修闭合 |
| H1_UNIQUE | FAIL | 一级标题数量异常 | 保留一个 h1 |
| H_SKIP | WARN | 标题层级跳级 | 补齐中间层级 |
| IMG_ALT | WARN | 图片缺 alt | 补 alt |
| CSS_VAR | FAIL | 调用未定义变量 | 补变量定义 |
| CONTRAST | FAIL/WARN | 对比度未达标或无法解析 | 换达标配色 |
| PRINT_CSS | WARN | 缺打印样式 | 补 `@media print` |
| TOC | WARN | 多章节无锚点导航 | 补目录或返回顶部 |
| SOURCE_BLOCK | WARN | 未见来源标注 | 挂来源区块与数据来源行 |
| GAP_BLOCK | WARN | 有【待核】无缺口区块 | 补缺口区块 |
| SIZE | WARN | 体积超上限 | 压缩素材 |
| JS_SYNTAX | FAIL/WARN | JS 语法错误或未校验 | 修语法或安装 node |
| TEXT_OUT | OK | 正文文本已导出 | — |

调用：

```bash
python3 "$S/scripts/html_check.py" 页面.html --node
python3 "$S/scripts/html_check.py" 页面.html --json > check.json
python3 "$S/scripts/html_check.py" 页面.html --text-out plain.txt
```

## 三、体积控制

- base64 图片：单张控制在 80KB 以内，公式为 `文件字节 × 1.37`。超限先缩放再转码。
- 优先内联 SVG：图标、流程图、箭头用内联 SVG，体积远小于位图且打印不糊。
- 头像与截图：网页中长边不超过 900px 再转码，超过即缩放。
- 样式：合并重复规则，删除未使用的主题块（只用一套配色时删掉其余九套变量）。
- 字体：只用系统字体族，禁止内嵌字体文件。

## 四、扩展检查项

`html_check.py` 的检查项集中在 `main()` 中顺序调用，新增一项的三步：

一、在 `main()` 对应分组内调用 `add(level, code, msg, fix)`。
二、`level` 取 `OK` / `WARN` / `FAIL`，`FAIL` 会阻断交付并令退出码为 1。
三、在本文档第二节的对照表中登记新代码，保证文档与脚本同步。

## 五、多页装配（L4）

单文件模式覆盖 L1—L3。需要成书或站点时切换为多页装配：

- 目录页（目次）单独成页，链接指向各分册文件。
- 每页共用同一套配色变量，变量块由 `palettes.py css` 统一生成。
- 每页保留自己的页脚（数据来源行 + 成文日期），便于单独转发。
- 分册文件仍按单文件规范自包含，禁止跨文件引用样式。

## 六、与写作质量校验的衔接

结构自检只覆盖"页面是否完整可交付"，不覆盖"文字是否达标"。两步走：

```bash
# 第一步：结构自检
python3 "$S/scripts/html_check.py" 页面.html --node --text-out plain.txt
# 第二步：正文文本送写作质量校验（抽文本可避免 CSS 色值被误判为数字）
python3 scripts/report_checker_pro.py --file plain.txt --report-type technical
```

第二步不达标时返工文案，不改字号凑可读性；返工后重跑两步。
