# 六类产出物模板

QBS 法闭环的六类产出，字段与格式约定。填写时未确认项统一标注【待核：具体说明】。

## 一、问题陈述卡

```markdown
# 问题陈述卡
- 领域：
- 核心问题（单点）：
- 已知条件与约束：
- 期望产出形态：
- 成功标准（可检验）：
- 立案时间：
```

## 二、荐书评分表

由 `scripts/book_recommender.py` 生成，结构：

```markdown
# QBS 荐书评分表
**问题**：<问题陈述>
基准年份：<年>｜加权口径：时间检验 0.30 + 权威性 0.25 + 跨代验证 0.20 + 匹配度 0.25

| 排名 | 书名 | 作者 | 首版年 | 时间检验 | 权威性 | 跨代验证 | 匹配度 | 加权总分 | 备注 |
|:--:|:--|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... | ... |

## 时间检验校验
- ✅/⚠️ <书名>：距今 N 年（...）

> 入选建议：...
```
配套 CSV 同目录留存，便于复核。

## 三、取书路径说明

由 `scripts/source_guide.py` 生成，含作者、首版年、版权状态、合法获取路径（A 公版 / B 正版平台 / C 图书馆 / D 纸质）、版权边界与降级。

## 四、生成的技能

标准技能目录：

```
<skill_name>/
├── SKILL.md            （≤4,000 tokens）
├── chapters/ch<NN>-<slug>.md
├── glossary.md
├── patterns.md
└── cheatsheet.md
```

登记项：技能名、路径、主 SKILL.md token 数、安全扫描结果、章节数。

## 五、解题报告

```markdown
# 解题报告：<问题>
## 一、结论
<直接回答，结论先行>

## 二、依据与溯源
| 结论要点 | 来自书中哪个框架/原则 | 出处章节 |
|:--|:--|:--|
| ... | ... | ... |

## 三、覆盖边界
<该书未覆盖、需另行处理的部分>

## 四、遗留问题
<未解决项与后续动作>
```

## 六、QBS 台账

由 `scripts/qbs_pipeline.py` 维护，JSON 结构：

```json
{
  "problem": "<问题陈述>",
  "created": "YYYY-MM-DD HH:MM:SS",
  "stages": {
    "0_problem":  {"done": true,  "artifact": "", "note": ""},
    "1_recommend":{"done": false, "artifact": "", "note": ""},
    "2_source":   {"done": false, "artifact": "", "note": ""},
    "3_skill":    {"done": false, "artifact": "", "note": ""},
    "4_solve":    {"done": false, "artifact": "", "note": ""},
    "5_archive":  {"done": false, "artifact": "", "note": ""}
  }
}
```

## 归档命名建议

- 单组闭环：`QBS_<问题关键词>_<YYYYMMDD>/`
- 报告文件：`01_问题卡.md`、`02_荐书评分表.md`、`03_取书路径.md`、`04_生成的技能/`、`05_解题报告.md`、`06_台账.json`
