# 脚本数据字典与样例

本技能三个脚本各读取一份 JSON。金额单位统一为「万元」，允许小数；未出现的字段按 0 处理。执行任一脚本前，先用最小样例跑通，再灌入项目数据。

## 一、audit_check.py —— 审计数据校验

对关键审计口径逐条判定：报表勾稽、四类投资归集、资产贯通、核减率、超概算、尾工 5% 上限、建设管理费控制额、资金缺口来源。

| 字段 | 含义 | 必填 |
|---|---|---|
| `project` | 项目名称（报告抬头） | 建议 |
| `overview.approve_amount` | 批准概算总投资 | 是 |
| `overview.actual_amount` | 实际完成投资（审定口径，须等于决算表基本建设支出） | 是 |
| `settlement.send_amount` | 送审投资合计 | 是 |
| `settlement.audited_amount` | 审定投资合计 | 是 |
| `settlement.items[].name/send/audited` | 分类送审与审定（建安、设备、待摊） | 是 |
| `table2.source_total` / `use_total` | 决算表资金来源合计 / 资金占用合计 | 是 |
| `table2.capital_construction_expenditure` | 决算表基本建设支出 | 是 |
| `table2.delivered_assets` | 决算表交付使用资产 | 是 |
| `expenditure.construction/equipment/overhead/other` | 四类投资归集（审定） | 是 |
| `table3.total` | 交付使用资产总表合计 | 是 |
| `tail_work.amount` | 尾工工程金额 | 否 |
| `mgmt_fee.base/claimed/standard` | 建设管理费计费基数 / 申报 / 控制额 | 否 |
| `funds.allocated/gap/gap_source` | 到位资金 / 缺口 / 缺口来源 | 否 |

最小样例：

```json
{
  "project": "××污水处理工程",
  "overview": {"approve_amount": 1591.75, "actual_amount": 894.11},
  "settlement": {
    "send_amount": 940.08,
    "audited_amount": 894.11,
    "items": [
      {"name": "建筑安装工程投资", "send": 667.86, "audited": 628.61},
      {"name": "设备、工器具投资", "send": 167.68, "audited": 167.68},
      {"name": "待摊投资", "send": 104.54, "audited": 97.82}
    ]
  },
  "table2": {"source_total": 894.13, "use_total": 894.13,
             "capital_construction_expenditure": 894.11, "delivered_assets": 894.11},
  "expenditure": {"construction": 628.61, "equipment": 167.68, "overhead": 97.82, "other": 0.0},
  "table3": {"total": 894.11},
  "tail_work": {"amount": 0.0},
  "mgmt_fee": {"base": 894.11, "claimed": 18.43, "standard": 17.88},
  "funds": {"allocated": 711.68, "gap": 182.43, "gap_source": "项目公司自筹"}
}
```

判定规则：R1—R5 为关键勾稽，左右差额超 `--tolerance`（默认 0.01）判失败；R6 尾工超概算 5% 上限、R7 建设管理费超控制额、R8 缺口未写来源，三项触发即列入须复核。退出码 0=全部通过，1=存在须复核项，2=输入错误。

## 二、audit_report_builder.py —— 审计报告生成

| 字段 | 含义 |
|---|---|
| `title` | 报告标题（换行用 `\n`） |
| `report_no` | 报告编号（事务所 `××审字〔20××〕××号`；审计机关 `×审××报〔20××〕××号`） |
| `entity` | 被审计单位（收件人） |
| `project` | 审计项目名称 |
| `sections[].heading` | 章节标题（挂 Heading 1） |
| `sections[].body[]` | 章节正文段落数组；以「（一）」等开头的段落自动挂 Heading 2 |
| `signature[]` | 落款行（出具单位、签字人、日期） |

`--type cpa` 预设十节（项目概况／审核依据／审核范围与程序／资金到位与使用／决算报表审核／概算执行分析／交付使用资产／债权债务清理／问题及整改建议／审核结论）；`--type gov` 预设八要素，均可被 `sections` 覆盖。生成 Word 挂 Heading 1/2 大纲级别并插入可更新目录域，字体按 GB/T 9704-2012。

## 三、audit_working_paper.py —— 审计工作底稿生成

`items[]` 每项六字段：`no`（编号，缺省自动 WP-001）、`matter`（审计事项）、`procedure`（实施程序）、`evidence`（证据来源）、`conclusion`（核对结论）、`deviation`（偏差与处理）。

```json
{"items": [
  {"no": "WP-001", "matter": "建设程序合规性", "procedure": "核对立项、概算、招投标、监理、验收文件",
   "evidence": "立项批复、概算批复、中标通知书、监理报告、竣工验收报告",
   "conclusion": "程序齐备，未发现缺失", "deviation": "无"},
  {"no": "WP-002", "matter": "建安工程投资", "procedure": "抽查工程量与单价，抽查比例 30%",
   "evidence": "施工合同、结算书、竣工图、变更签证", "conclusion": "核减 39.25 万元",
   "deviation": "多算重算，按实核减"}
]}
```

参数 `--project/--editors/--reviser/--date` 写入表头；缺省 `--input` 时用内置审计事项模板（`--demo`）。

## 四、常见错误

1. 金额误填「元」而字段口径为「万元」，导致核减率放大一万倍——填数前统一换算。
2. `overview.actual_amount` 填送审数而非审定数，R2 概算对照必然失败——实际完成投资一律取审定口径。
3. 分类审定之和与 `audited_amount` 不等，R5 失败——两项须同源同口径。
4. 报告 `sections[].body` 误传字符串而非数组，脚本按字符逐字成段——一律传数组。
5. 生成 docx 后目录为空——Word 中右键「更新域」或在打印预览时更新。
