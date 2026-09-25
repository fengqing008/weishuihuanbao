# 五阶段逐阶段操作指引

每阶段的输入、动作、产出与检查点。任一阶段产出未齐即停在原阶段。

## Step 0 — 问题锁定

| 项 | 内容 |
|:--|:--|
| 输入 | 用户的原始诉求（可能是模糊的一句话） |
| 动作 | 收敛为问题陈述卡：领域 / 核心问题 / 已知条件与约束 / 期望产出形态 / 成功标准 |
| 产出 | 问题陈述卡（写入台账 `0_problem`） |
| 检查点 | 向用户复述陈述卡并获确认 |

要点：核心问题要单点化——"如何提升团队产出"优于"想学管理"。模糊诉求先追问，不带猜往下走。
命令：`python3 scripts/qbs_pipeline.py init --problem "<问题陈述>"`

## Step 1 — 荐书

| 项 | 内容 |
|:--|:--|
| 输入 | 问题陈述卡 |
| 动作 | 按四维标准提 3—5 本候选，填 CSV，跑评分表排序 |
| 产出 | 荐书评分表（Markdown + CSV） |
| 检查点 | 用户选定 1—2 本核心书 |

命令：
```bash
python3 scripts/book_recommender.py --problem "<问题>" --candidates candidates.csv --out recommend.md
```
判据见 `references/classic-book-criteria.md`。

## Step 2 — 合规取书

| 项 | 内容 |
|:--|:--|
| 输入 | 选定的核心书 |
| 动作 | 判定公版状态，给合法获取路径，评估可得性 |
| 产出 | 取书路径说明（Markdown） |
| 检查点 | 确认取书方式；无全文时确认降级方案 |

命令：
```bash
python3 scripts/source_guide.py --book "<书名>" --author "<作者>" --death-year <卒年> --out source.md
```
判据见 `references/legal-book-sources.md`。

## Step 3 — 转技能

| 项 | 内容 |
|:--|:--|
| 输入 | 合法取得的书籍文件 |
| 动作 | 调用内核 book-to-skill 完成提取与蒸馏 |
| 产出 | 技能目录（SKILL.md + chapters/ + glossary/patterns/cheatsheet） |
| 检查点 | 通过转换门（安全扫描 + token 上限 + 引用可达） |

契约见 `references/book-to-skill-bridge.md`。

## Step 4 — 调用解题

| 项 | 内容 |
|:--|:--|
| 输入 | 生成的技能 + 问题陈述卡 |
| 动作 | 加载技能作答，逐条结论标注来源框架，显式说明覆盖边界 |
| 产出 | 解题报告（Markdown） |
| 检查点 | 用户认可答案，或提出补充问题（补充问题回到本阶段循环） |

命令：`python3 scripts/qbs_pipeline.py check` 校验四环闭合。

## Step 5 — 留痕入库

| 项 | 内容 |
|:--|:--|
| 输入 | 前四阶段全部产出 |
| 动作 | 汇总问题卡、评分表、取书路径、技能、解题报告；归档技能包与报告 |
| 产出 | QBS 台账（JSON）+ 归档记录 |
| 检查点 | 台账五阶段均标记完成 |

命令：`python3 scripts/qbs_pipeline.py status` 导出台账。

## 阶段间关系

```
Step 0 问题 ─► Step 1 荐书 ─► Step 2 取书 ─► Step 3 转技能 ─► Step 4 解题 ─► Step 5 归档
   │             │             │              │               │
 确认门        确认门        确认门         转换门          解题门
```

- 每个确认门未过，不得进入下一阶段。
- Step 4 的补充问题在本阶段循环，不回退 Step 1—3。
- 一次会话可并行多组闭环（多问题），各自独立建台账。
