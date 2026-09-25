# 图形围栏规范（diagrams-guide.md）

> 适用技能：html-report-builder v5.1.0 起。「流程图/架构图/时序图」等图形如何写进 Markdown 并渲染为单文件 HTML。

## 一、写哪种图

| 需求 | 写法 | 渲染方式 |
|---|---|---|
| 流程、判断分支、系统架构、数据流 | ```` ```mermaid ```` + `flowchart LR` | 本地渲染为内嵌 SVG |
| 接口调用、消息时序、交互过程 | ```` ```mermaid ```` + `sequenceDiagram` | 同上 |
| 状态流转、生命周期 | ```` ```mermaid ```` + `stateDiagram-v2` | 同上 |
| 类/模块关系、ER 实体关系 | ```` ```mermaid ```` + `classDiagram` / `erDiagram` | 同上 |
| 数据形态（柱/折线） | ```` ```mermaid ```` + `xychart-beta` | 同上；精确数据仍优先 `:::chart` |
| 已有 SVG 产物（任意绘图技能导出） | ```` ```svg ```` + `<svg …>` | 直接内嵌 |
| PlantUML / DOT / Excalidraw 源码 | ```` ```plantuml ```` / ```` ```dot ```` / ```` ```excalidraw ```` | 沙箱无本地渲染器 → **源码卡 + 处置提示**（不静默丢内容） |
| 普通代码 | ```` ```python ```` 等 | 等宽代码块 |

## 二、mermaid 渲染链

- 渲染器：**pretty-mermaid**（`scripts/render.mjs`，纯 JS 本地渲染，**无浏览器、无网络**）；
- 定位方式：三级探测（基座 `scripts/vendors/pretty-mermaid` → `pretty-mermaid` → 工作区软链）；
- 渲染器缺失 → 自动降级为源码卡，**不阻断整篇渲染**；
- 图注：围栏语言后可直接跟图注文本，例：```` ```mermaid 工艺流程图 ````；图注自动编号（与图片共用计数器）。

## 三、配色随主题

图与页面同色系由 `md2report.py` 自动完成：先定报告主题，再把该主题的
`surface / text / border / accent / muted / surface2` 映射为 mermaid 的
`--bg / --fg / --line / --accent / --muted / --surface / --border`。

实测（ocean 主题）：mermaid 输出 SVG 的 `--bg` = `#1e2c3f`，与报告容器色一致。

## 四、体积与内嵌

- SVG 走 `data:image/svg+xml;base64` **data URI + `<img>`** 内嵌，完全隔离 CSS（不会被图形内部样式污染报告样式），且单文件自包含；
- 实测：2 张 mermaid（6.1KB / 3.9KB）+ 1 张自绘 SVG（200B）≈ 无感体积；
- 图形页体积门禁同配图页：`--max-kb 1200`。

## 五、验收清单

```bash
S=技能目录
python3 "$S/scripts/render_diagrams.py" check                 # ① 渲染器可用性（须「可用」）
python3 "$S/scripts/md2report.py" 成稿.md -o 成果页.html --check --max-kb 1200
```

判定：

- `html_check.py` 的 `IMG_EMBED` 张数 = 图片数 + mermaid 图数 + svg 图数；
- `FENCE_LEAK` 须为 OK（无未解析围栏残留）；
- 降级卡存在时属预期（无本地渲染器语言），但须确认卡片里保留了完整源码。

## 六、失败模式与处置

| 现象 | 原因 | 处置 |
|---|---|---|
| 图未渲染，出「本图未渲染」卡 | 渲染器缺失 / node 不可用 / mermaid 语法错 | `render_diagrams.py check` 探因；语法错按其报错行修最小失败语句后重渲染 |
| 图渲染成功但配色突兀 | 未走主题映射 | 确认 `md2report` 传入 theme（CLI `--theme` 或 frontmatter `theme:`） |
| 图过宽溢出 | 图本身横向节点过多 | 改 `flowchart LR` → `flowchart TB`，或拆分两张图 |
| 图中文字被裁切 | 节点标签过长 | 标签缩短到 ≤8 字，或加 `--padding` 类参数（经 render.mjs） |
| 需要 DOT/PlantUML | 沙箱无本地渲染器 | 用 graphviz / uml / bpmn 技能导出 SVG，再以 ```` ```svg ```` 贴入 |
