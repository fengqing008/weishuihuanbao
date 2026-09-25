# 交付前清单（quality-checklist）

## 一、构建前

- 启动协议三问已答：给谁看、看完做什么、素材在哪。
- 响应级别已定（L1—L4），骨架已选。
- 配色已选且符合受众场景；纸质分发选浅色主题。
- 数据文件（spec.json）中每个数字都能对应到来源。

## 二、构建后（命令逐条执行）

```bash
S=html-report-builder

# 1 结构自检 + JS 语法 + 抽正文
python3 "$S/scripts/html_check.py" 成果页.html --node --text-out plain.txt

# 2 配色对比度复校
python3 "$S/scripts/palettes.py" check

# 3 正文文本送写作质量校验
python3 scripts/report_checker_pro.py --file plain.txt --report-type technical
```

判定标准：第 1 条 FAIL=0；第 2 条十套全通过；第 3 条达 A 级（≥90 分）。

## 三、门禁对照

| 门禁 | 检查手段 | 通过线 |
|---|---|---|
| 门 1 结构自检 | html_check.py | FAIL=0 |
| 门 2 对比度 | palettes.py check 与页面内嵌变量一致 | 10/10 通过 |
| 门 3 文本质量 | report_checker_pro.py 对抽出的正文 | A 级 ≥90 |
| 门 4 可追溯 | 页面含来源区块，关键数据有角标 | SOURCE_BLOCK 为 OK |
| 门 5 离线 | 断网打开逐项点按 | 无缺失元素 |
| 门 6 打印 | 打印预览 | 正文、表格、来源区完整 |
| 门 7 归档 | 入库并给短链与 media_id | 有可点击入口 |

## 四、人工复核项（脚本查不到）

- 打开页面点一遍配色切换，确认十套都不刺眼、文字不丢。
- 用手机打开或缩放浏览器到 375px 宽，确认无横向滚动。
- 断网打开（或禁用网络后刷新），确认交互仍可用。
- 打印预览一页，确认页头不重复、表格不截断。
- 逐条读结论区，确认没有"预计/可能/大致"之类模糊表述承载关键数据。

## 五、归档与交付

```bash
# 走平台上传通道（docx/md/pdf/html 均支持）
python3 ima-knowledge/scripts/upload_file.py \
  --file-path 成果页.html --knowledge-base-id <kb_id> --rename 成果页名称-定稿
```

交付回复须包含：内容预览（Markdown 呈现正文要点）、短链（provide_file）、成果库 media_id、数据来源说明、门禁结果。更新版本时上传新条目并用 `update_knowledge_access_status(access_status=1)` 隐藏旧条目。

## 六、常见返工点

- 抽正文校验未做，直接拿 HTML 源文件送检，CSS 色值被误判为未千分位数字。
- 目录锚点与章节 id 不一致，点击无反应。
- 配色只换 --accent 不换 --hero-1/--hero-2，页头与正文色系脱节。
- 缺口写了徽标却没写缺口区块，读者看不到影响与补渠道。
- 打印样式漏隐藏交互控件，打印稿出现配色圆点。
