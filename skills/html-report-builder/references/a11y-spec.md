# 无障碍与交付细节规范（v6.0.0）

> 本文件是 html-report-builder v6.0.0 新增能力的落地细则。底座在生成页面时已自动注入下列能力，本文件供技能调用方与人工复核参考。

## 一、无障碍（WCAG 2.1 AA 取向）

| 项 | 落地 | 校验码 |
|---|---|---|
| 键盘焦点可见 | 全站 `:focus-visible` 焦点环（`--accent` 2px + offset 2px），覆盖目录胶囊、配色钮、抽屉按钮、返回顶部、表头排序、可折叠章节头 | `FOCUS_VISIBLE` |
| 跳至正文 | `<a class="skip-link" href="#content">跳至正文</a>`，获焦时左上角出现，正文容器 `id="content"` | `SKIP_LINK` |
| 表格语义 | 所有生成表头带 `scope="col"`（split_table / :::gap / 来源表 / 缺口表） | `TH_SCOPE` |
| 当前位置 | scroll-spy 高亮章同步写 `aria-current="true"` | `ARIA_CURRENT` |
| 弹层语义 | 抽屉目录 `role="dialog"` + `aria-modal`，lightbox 关闭按钮带 `aria-label`，Esc 可关 | — |
| 图片替代文本 | 图片 `alt` 齐备；图表 SVG `role="img"` + `aria-label`；装饰性元素 `aria-hidden="true"` | `IMG_ALT` |

**键盘可达性检查清单**：①Tab 依次可到目录胶囊 → 配色钮 → 返回顶部；②Enter/Space 触发可折叠章节、配色、表头排序；③Esc 关闭抽屉与图片放大；④焦点环在深底与浅底主题下均可见（对比度 ≥3:1）。

## 二、分享与元信息

- `<meta name="description">`：取副标题，缺失时留空。
- Open Graph：`og:type=article`、`og:title`、`og:description`、`og:locale=zh_CN`——转发微信/飞书/IM 显示标题与摘要卡。
- `<meta name="theme-color">`：初始为主题背景色，切换配色时由 JS 写回（`apply()` 内）。
- 内联 SVG favicon：data URI 内嵌，零外链，标签页不再显示默认图标。

## 三、打印与 PDF

- `@page { size: A4; margin: 16mm 13mm 16mm }` 定义版心。
- **局部避断**：章节不整体避断（避免超一页时出现大片空白），改为卡片/图/表/引用/法条卡/FAQ 局部避断。
- `thead { display: table-header-group }`：长表跨页时重复表头。
- 外链打印展开 URL：`a[href^="http"]::after { content: " (" attr(href) ")" }`，便于纸质回溯。
- 页码：浏览器打印在「更多设置」勾选「页眉和页脚」；批量 PDF 用 WeasyPrint 时可用 `@page { @bottom-center { content: counter(page) } }`。

## 四、交互增强

- **图片点击放大**（lightbox）：`.fig img / .g-cell img / .fig-diagram img` 可点击放大，无图时整段 JS 不注入（体积零负担）。
- **抽屉目录搜索**：移动端目录面板顶部搜索框实时过滤章节，无结果给提示。
- **长表点击排序**：数值列自动识别并加 `data-sort`，点击表头升降序，支持键盘 Enter/Space。
- **跟随系统深色**：无 `localStorage` 用户选择时按 `prefers-color-scheme` 自动选深色主题（galaxy）；用户点选后记忆其选择，不再自动跟随。

## 五、动画安全（强制约束）

动画一律**渐进增强**：只在 `root.classList.add('anim-ready')` 成功后生效；`prefers-reduced-motion: reduce` 与 `@media print` 下全部还原静态。新增动画须同时满足：

1. 不改内容布局尺寸（用 `transform` / `opacity` / `translate` 属性，不触发重排）；
2. 单元素时长 ≤1.1s，错峰步长 ≤95ms、总延迟 ≤520ms；
3. JS 不可用时不出现「内容不可见」（初始态由 CSS 类控制，内容默认可读）。

## 六、自检命令

```bash
# 结构 + 无障碍 + 打印 全量自检
python3 "$S/scripts/html_check.py" 页面.html --node
# 抽正文送写作质量校验
python3 "$S/scripts/html_check.py" 页面.html --text-out plain.txt
```

门禁：`FOCUS_VISIBLE / SKIP_LINK / OG_META / THEME_COLOR / TH_SCOPE / ARIA_CURRENT / PAGE_RULE` 七项须为 OK（新交付页面）。
