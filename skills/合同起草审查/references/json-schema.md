# 生成脚本 JSON 数据结构规范

> 本文件承载 合同起草审查 技能调用 gen_contract_docx.py 的 JSON 数据结构。Phase 5 数据准备按本文件执行。

## 一、起草模式 JSON 结构

```json
{
  "mode": "draft",
  "title": "合同标题",
  "parties": {
    "party_a": "甲方名称",
    "party_b": "乙方名称"
  },
  "sections": [
    {
      "heading": "第一条 合同主体",
      "paragraphs": [
        {"type": "normal", "text": "甲方：xxx，乙方：xxx"}
      ]
    }
  ]
}
```

字段说明：
- `mode`：固定为 `"draft"`
- `title`：合同标题（如"设备买卖合同"）
- `parties`：甲乙双方名称
- `sections`：按"第X条"组织的章节列表；每章 `heading` + `paragraphs` 数组
- 段落 `type`：起草模式一般用 `"normal"`

## 二、审查模式 JSON 结构

```json
{
  "mode": "review",
  "title": "合同标题",
  "review_summary": {
    "overall_risk": "中高风险",
    "total_issues": 5,
    "high_risk": 2,
    "medium_risk": 2,
    "low_risk": 1
  },
  "sections": [
    {
      "heading": "第三条 价款与支付",
      "paragraphs": [
        {
          "type": "unchanged",
          "text": "本合同总价款为人民币100万元。"
        },
        {
          "type": "delete",
          "text": "甲方应在合同签订后3日内支付全部价款。"
        },
        {
          "type": "insert",
          "text": "甲方应在合同签订后支付30%预付款，交付验收合格后支付60%，余款10%作为质保金于质保期满后支付。"
        }
      ]
    }
  ],
  "review_notes": [
    {
      "location": "第三条",
      "risk_level": "high",
      "issue": "一次性付全款对甲方风险极大，无任何付款保障",
      "suggestion": "改为分阶段付款"
    }
  ]
}
```

字段说明：
- `mode`：固定为 `"review"`
- `review_summary`：总体风险评级+各级问题计数
- `sections.paragraphs[].type`：`unchanged`（保留原文）/ `delete`（删除标记，Word 中显示为修订删除）/ `insert`（插入标记，Word 中显示为修订插入）
- `review_notes`：逐条审查意见（位置/风险等级/问题/建议），与段落修订对应

## 三、脚本调用

```bash
python3 合同起草审查/scripts/gen_contract_docx.py outputs/{filename}.json
```

- 脚本在 JSON 同目录生成 `.docx` 文件
- 审查模式使用 Word 真实修订标记（OpenXML `w:ins`/`w:del`），用户可在 Word 审阅选项卡中接受/拒绝修订
- 生成后使用 `provide_file` 提供下载链接给用户

## 四、数据准备检查点

- [ ] `mode` 与当前工作模式一致
- [ ] 起草模式：核心条款模块无遗漏（主体/标的/价款/交付/权利义务/违约/不可抗力/争议解决/生效）
- [ ] 审查模式：`delete` 段落与 `insert` 段落成对出现（除非纯插入），文本与确认稿逐字一致
- [ ] `review_notes` 与 `sections` 中的修订一一对应
- [ ] JSON 写入 workspace 临时文件后再调用脚本，文件名不含空格与中文标点
