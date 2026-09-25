# 输出模板（theme-factory）

交付时直接套用以下骨架。字段值须来自实际读取的主题文件与复算结果，缺失项写【待核：字段名】。

## 一、主题应用规格表（Markdown 骨架）

```markdown
# 主题应用规格表

| 项目 | 内容 |
|---|---|
| 目标文件 | 【待填：文件路径】 |
| 场合与受众 | 【待填】 |
| 主题名 | 【待填：如 Ocean Depths 深海之境】 |
| 主题来源 | 【待填：themes/ocean-depths.md 或 自定义】 |
| 配比策略 | 底色 60% / 主色与中性面 30% / 强调色 10% |

## 色彩槽位映射

| 槽位 | 名称 | hex | 用途 |
|---|---|---|---|
| background | 【待填】 | `#______` | 页面/画布底色 |
| primary | 【待填】 | `#______` | 主色、标题条、图表主系列 |
| accent | 【待填】 | `#______` | 强调块、图示高亮（约 10%） |
| text | 【待填】 | `#______` | 正文与浅底 |

## 字体槽位映射

| 槽位 | 拉丁字体 | 中文字体 | 回退链 |
|---|---|---|---|
| heading | 【待填】 | 【待填】 | 【待填】 |
| body | 【待填】 | 【待填】 | 【待填】 |

## 对比度校验记录

| 组合 | 复算值 | 阈值 | 结论 |
|---|---|---|---|
| 正文 / 背景 | 【待填】 | ≥4.5 | 【待填】 |
| 强调 / 背景 | 【待填】 | ≥3.0 | 【待填】 |
| 次级 / 背景 | 【待填】 | ≥3.0 | 【待填】 |

## 抽页复核

| 抽检页 | 位置 | 核对结论 |
|---|---|---|
| 封面 | 【待填】 | 【待填】 |
| 正文页 | 【待填】 | 【待填】 |
| 图表页 | 【待填】 | 【待填】 |

## 降级与待核

- 降级项：【待填：无 或 具体动作与原因】
- 待核项：【待核：字段名 + 待补证物】
- 校验人 / 日期：【待填】 / 【待填】
```

## 二、HTML 样式骨架（套用主题后）

```html
<style>
  :root{
    --tf-bg:      #______;  /* background */
    --tf-primary: #______;  /* primary */
    --tf-accent:  #______;  /* accent：用量约 10% */
    --tf-text:    #______;  /* text */
    --tf-font-head: "【拉丁标题字体】", "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;
    --tf-font-body: "【拉丁正文字体】", "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;
  }
  body{ background: var(--tf-bg); color: var(--tf-text); font-family: var(--tf-font-body); }
  h1,h2,h3{ font-family: var(--tf-font-head); border-left: 6px solid var(--tf-primary); padding-left: .5em; }
  table{ border-collapse: collapse; }
  th{ background: var(--tf-primary); color: var(--tf-text); }
  td{ border-bottom: 1px solid var(--tf-accent); }
  .accent-block{ background: var(--tf-accent); }
</style>
```

## 三、PPT / Word 落地检查骨架

```markdown
| 对象 | 落地位置 | 是否已改 | 备注 |
|---|---|---|---|
| 主题色板 | 母版主题色（4 色） | 【待填】 | 不是逐页手改 |
| 标题样式 | 样式集 Heading 1-3 | 【待填】 | 字体 + 色值 |
| 正文样式 | 样式集 Normal | 【待填】 | 字体 + 色值 |
| 图表配色 | 图表色序 primary → accent → 中性 | 【待填】 | 与主题同源 |
| 表格底纹 | 表头 primary、间隔 accent 淡色 | 【待填】 | 不遮蔽文字 |
```

## 四、自定义主题规格骨架

```markdown
# 自定义主题：【待填：形容词 + 名词】

- 拟定理由：【待填：场合与既有 10 套不匹配之处】
- 色板：bg `#______` / primary `#______` / accent `#______` / text `#______`
- 字体：heading 【待填】 / body 【待填】
- 对比度：正文/背景 【待填】（≥4.5）/ 强调/背景 【待填】（≥3.0）
- 与既有主题重合度：【待填】
- 用户确认：主题名与四色 【待填：经确认 / 待确认】
- 案卷登记：references/case-library.md 第 __ 条
```
