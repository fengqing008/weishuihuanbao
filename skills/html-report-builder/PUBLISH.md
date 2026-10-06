# 发布资料 · HTML 成果输出引擎（html-report-builder）

## 一、技能简介

**HTML 成果输出引擎**把报告、说明书、方案、汇报、研究成稿、试题一键输出为**单文件自包含 HTML**——无外部依赖、可离线打开、可直接打印。内置 10 套经 WCAG 对比度校验的配色、自动目录与返回顶部、来源分级与信息缺口标注、八大画板组件（KPI 数据卡 / 横向条形图 / 时间轴 / 对比矩阵 / 流程阶段 / 法条卡 / 折叠问答 / 标签行）与 stat 巨幕、大数、图标卡；支持 KaTeX 数学公式（`$...$` 与 `$$...$$`）、callout 卡、试题三段式、图片 base64 内嵌与自动图注、chart 内联 SVG、长表粘性表头；**智能配图链路**（识别配图点 → 生成提示词任务单 → 调 ima 文生图出图 → 瘦身回填 → base64 内嵌）与 `:::gallery` 图组、「AI 配图」角标；适配侧栏布局、深色章节头、移动端横滑胶囊目录与打印版式。

| 项目 | 内容 |
|------|------|
| 显示名 | HTML 成果输出引擎 |
| 技能标识 | html-report-builder |
| slug | qf-html-report-2 |
| 版本 | 9.6.2 |
| 作者 | 清风明月 |
| 类别 | 科技（SkillHub 付费技能 pay-skill） |
| 计费 | 按调用量计费 · 0.2 元/次 |
| 依赖 | 无（技能主体基于 Python 标准库；PaySkill 网关需 cryptography） |

## 二、使用说明（7 条）

1. **把报告做成单文件 HTML**：对我说「把这份调研报告做成单文件 HTML，要能离线打开、可直接打印」，我会生成一个自包含 `.html`，图片 base64 内嵌、断网可看。
2. **给报告配达标的配色**：说「给这份 Markdown 配一套对比度达标的主题」，我从 10 套经 WCAG 校验的配色里选，并可切侧栏布局或深色章节头。
3. **加数据卡与图表组件**：说「报告里加 KPI 数据卡和横向条形图」，我用八大画板组件按围栏语法渲染，关键数字带滚动计数。
4. **试题/试卷排成网页版**：说「把这几道题排成网页版，带公式和答案折叠」，我按试题三段式 + KaTeX 公式 + 折叠答案输出。
5. **自动目录与来源标注**：说「要自动目录、返回顶部和来源角标」，我会生成顶部胶囊目录（scroll-spy 高亮）与可追溯的来源分级标注、信息缺口徽标。
6. **成品自检**：交付前说「帮我校验这份 HTML」，我跑结构检查脚本，核配色对比度、组件围栏、外链与数学公式渲染完整性。
7. **自动配图**：说「给这份报告配几张插图」，我识别需要配图的章节、生成中英提示词、调 ima 文生图逐张出图，再瘦身并内嵌成单文件 HTML（AI 生成图带「AI 配图」角标）。

## 三、使用示例

### 示例一：Markdown 报告 → HTML 成果页

```bash
python3 scripts/md2report.py 报告.md --theme ocean --layout sidebar -o 报告.html
```

### 示例二：自检（结构 / 配色对比度 / 组件）

```bash
python3 scripts/html_check.py 报告.html
```

### 示例三：智能配图（规划 → 出图 → 回填）

```bash
python3 scripts/illustrate.py plan 报告.md --theme ocean --max 3
# 按任务单逐张调用 ima 文生图（image_gen）出图到 images/
python3 scripts/illustrate.py apply 报告.md --plan illustration/plan.json
python3 scripts/md2report.py 报告_illustrated.md -o 报告.html --theme ocean --check --max-kb 1200
```

退出码：0 = 全部通过；1 = 存在 FAIL 项（须修复后再交付）。

### 示例四：PaySkill 支付宝付费链路自检

```bash
python3 pay/payment_gate.py --selftest                        # 402 账单/验付/履约/幂等 9 项自检
python3 pay/payment_gate.py --challenge html-report/render    # 生成一次 402 账单（调试）
```

## 四、适用场景

- 报告、说明书、方案、汇报材料、研究成稿、试题的输出交付。
- 需要「一个文件、离线可看、直接打印」的对外或内部成果页。
- 需要统一视觉风格、来源可追溯、缺口可标注的正式文稿。
- 需要嵌数学公式、图表、长表、对比矩阵的技术类成果。

## 五、不适用边界

| 场景 | 处理方式 |
|------|----------|
| Word / PDF 文档生成 | 改用 ima-doc / ima-pdf 类能力 |
| 党政机关公文国标排版（GB/T 9704） | 改用 docx-gw-format |
| PPT 演示文稿制作 | 改用 ima-ppt 类能力 |
| 扫描件 / 图片 PDF 解析 | 改用 textin-xparse 类 OCR 能力 |

## 六、资源清单

| 路径 | 用途 |
|------|------|
| `SKILL.md` | 主文档：能力说明、组件语法、变更记录、PaySkill 付费调用 |
| `references/` | 配色、组件、排版与交付规范 |
| `references/payskill-integration.md` | 支付宝 A2M 接入规范（402 账单 / 验付 / 履约 / 签名 / 自查） |
| `scripts/md2report.py` | Markdown → 单文件 HTML 转换 |
| `scripts/html_check.py` | 结构与配色自检 |
| `scripts/palettes.py` | 10 套主题色板定义 |
| `scripts/illustrate.py` | 智能配图：识别配图点、生成任务单、瘦身回填 |
| `scripts/board.py` | 数据看板引擎（KPI + 条形对比 + 阈值预警） |
| `pay/pay_config.json` | 支付宝 A2M 计费与商户配置（0.20 元/次、seller_*、service_id、单价三处核对） |
| `pay/alipay_aipay.py` | A2M 核心库：RSA2 加签、账单构造、Payment-Needed 编解码、Payment-Proof 解析、verify/confirm 调用、幂等存储 |
| `pay/payment_gate.py` | 付费闸口：`PaymentGate.protect()` 接入业务端点 + 离线自测 |
| `pay/keys/README.md` | 应用私钥 / 支付宝公钥放置说明 |
| `pay/README.md` | 支付宝 A2M 接入与部署说明 |
| `PUBLISH.md` | 本发布资料 |

## 七、PaySkill 付费化（支付宝 AI 按量付费 / A2M · 402）

按**支付宝 AI 按量付费（A2M）**协议改造为付费技能，计费 **0.20 元/次**：

- **协议链路（4 步）**：① 无凭证 → `HTTP 402` + `Payment-Needed`（Base64URL 账单，RSA2 签名）→ ② 用户支付后 Agent 带 `Payment-Proof` 重试 → ③ 服务端调 `alipay.aipay.agent.payment.verify` 验付（校验 active/amount/out_trade_no/resource_id）→ ④ 返回资源后异步调 `alipay.aipay.agent.fulfillment.confirm` 履约回执。
- **加签规则**：RSA2，8 字段按字典序拼 `k=v&k=v`（amount/currency/goods_name/out_trade_no/pay_before/resource_id/seller_id/service_id），用应用私钥本地加签。
- **硬约束**：三处单价一致（0.20 元/次）；私钥仅存服务端；`out_trade_no` 幂等、`trade_no` 不重复履约。
- **费率**：单笔 1.0%；个人开发者优惠期 2026-04-15 至 2026-12-31 零费率。
- **发布通道**：SkillHub 网页后台手工上传 zip，分类选 pay-skill（CLI 不支持 pay-skill）。

## 八、版本与作者

- 版本：9.6.2
- 作者：清风明月
- 更新日期：2026-10-03
- 反馈渠道：【待填：反馈渠道】
