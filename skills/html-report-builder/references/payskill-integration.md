# PaySkill 接入规范 · 支付宝 AI 按量付费（A2M / 402）

> 适用对象：把技能封装为 SkillHub 付费技能（Pay Skill）并**通过支付宝 AI 按量付费**收款的开发者与接入方。
> 本规范据支付宝官方文档整理，配套实现见同目录上级 `pay/`。

---

## 一、协议总览

支付宝 **AI 按量付费**（AI 收 · Machine Pay · **A2M**）基于 `HTTP 402 Payment Required`，
让 API、数字内容或算力资源**直接向访问它们的 AI 智能体发起自动收款**。

- **按量收费**：每次调用可独立定价，不依赖包月订阅。
- **原生适配 Agent**：用 402 告诉智能体"这个资源需要先付款"。
- **链路更短**：用户无需在商家侧注册 / 登录 / 跳转。

**服务端必须完成三件事**：
1. 未付费 → 返回 `402` 与 `Payment-Needed` 账单；
2. 已付费 → 读取 `Payment-Proof` 并调用支付宝验凭证接口；
3. 验证通过并返回资源后 → 调用支付宝履约回执接口。

---

## 二、链路四步

| 步骤 | 触发 | 关键要素 |
|---|---|---|
| **① 402 账单下发** | 请求无 `Payment-Proof` | `HTTP 402 Payment Required` + `Payment-Needed` 响应头（Base64URL 账单） |
| **② 携带凭证重试** | 用户支付后 | `Payment-Proof` 请求头（Base64），解出 `payment_proof` / `trade_no` / `client_session` |
| **③ 验付调用** | 服务端收到重试请求 | `alipay.aipay.agent.payment.verify`，逐项校验 |
| **④ 履约确认** | 资源返回后 | `alipay.aipay.agent.fulfillment.confirm`（异步，参数 `trade_no`） |

> ⚠️ 普通下单、异步通知、主动查单**均不能**替代本协议；客户端显示支付成功**不能**作为验付/履约依据。

---

## 三、Payment-Needed 账单结构

`Payment-Needed` 响应头 = **Base64URL（可去 padding）** 编码的账单 JSON：

```json
{
  "protocol": {
    "out_trade_no": "ORDER_1739836600000_abc123",
    "amount": "0.20",
    "currency": "CNY",
    "resource_id": "html-report/render",
    "pay_before": "2026-09-25T22:55:00+08:00",
    "seller_signature": "YYYYxxxx=",
    "seller_sign_type": "RSA2",
    "seller_unique_id": "2088xxxxxxxx"
  },
  "method": {
    "seller_name": "清风明月",
    "seller_id": "2088xxxxxxxx",
    "seller_app_id": "app_123456",
    "goods_name": "HTML 成果输出引擎",
    "seller_unique_id_key": "seller_id",
    "service_id": "xxxx_12344"
  }
}
```

| 字段 | 说明 |
|---|---|
| `out_trade_no` | 商户订单号，全局唯一，用于**幂等与防重复支付**（≤32 位） |
| `amount` | 应付金额 |
| `currency` | 币种（默认 `CNY`） |
| `resource_id` | 资源唯一标识（防串号） |
| `pay_before` | 支付截止时间（ISO8601），**过期账单不可支付** |
| `seller_signature` / `seller_sign_type` | 商家签名 / 签名算法（**仅支持 RSA2**） |
| `seller_unique_id` | 卖家唯一标识（此处即 `seller_id`） |
| `seller_name` / `seller_id` / `seller_app_id` | 收款方名称 / userId（2088ID）/ 商户应用 ID |
| `goods_name` / `service_id` | 商品标题 / 服务 ID（获取见 https://ideservice.alipay.com/cms/site/0j7uos ） |

---

## 四、加签规则（RSA2）

- **加签字段（8 个）**：`amount`、`currency`、`goods_name`、`out_trade_no`、`pay_before`、`resource_id`、`seller_id`、`service_id`
- **签名串**：按 key **字典序**排序，拼成 `key=value&key=value`
  例：`amount=0.20&currency=CNY&goods_name=HTML 成果输出引擎&out_trade_no=ORDER_...&pay_before=...&resource_id=html-report/render&seller_id=2088xxxxxxxx&service_id=xxxx_12344`
- **算法**：RSA2（SHA256withRSA），签名结果 Base64 编码
- **密钥**：用**应用私钥**（第三方代调用用三方应用私钥）；**加签在本地完成，不请求支付宝服务端**

---

## 五、验付与业务校验

调用 `alipay.aipay.agent.payment.verify`，入参来自买家 `Payment-Proof`：

| 入参 | 说明 |
|---|---|
| `payment_proof` | 支付凭证 |
| `trade_no` | 支付宝订单号 |
| `client_session` | 买家客户端会话标识 |

返回示例：

```json
{"code":"10000","msg":"Success","active":true,"amount":"0.20",
 "out_trade_no":"ORDER_...","trade_no":"2026032400...","resource_id":"html-report/render"}
```

**业务校验（不止看接口成功）**：

- `active` 必须为 `true`；
- `amount` 必须等于本次资源价格；
- `out_trade_no` 必须是本商户订单号；
- `resource_id` 必须与本次访问资源一致；
- `trade_no` **不应被重复履约**。

任一不符 → 返回 402，让 Agent 重新支付。

---

## 六、履约确认

资源返回后，**异步**调用 `alipay.aipay.agent.fulfillment.confirm`，入参 `trade_no`。

---

## 七、Agent 侧交互

```
1. 用户下达指令 → Agent 请求商家付费资源
2. 商家返回 402 + Payment-Needed
3. Agent 把账单交给支付宝支付能力 → 用户确认支付
4. 支付成功后，Agent 带 Payment-Proof 再次请求同一资源
5. 商家 verify 通过 → 返回资源内容 → 异步 confirm 回执
```

---

## 八、幂等与对账

| 要求 | 说明 |
|---|---|
| `out_trade_no` 唯一 | 全局唯一，用于幂等与防重复支付 |
| `trade_no` 不重复履约 | 避免同一笔支付被多次使用 |
| 账单有效期 | `pay_before` 过期不可支付 |
| 三账核对 | 业务订单号关联「计量账 / 支付账 / 履约账」，定期排查金额不一致、已支付未履约等异常 |

---

## 九、费率与准入

- **费率**：单笔 **1.0%**；**个人开发者优惠期 2026-04-15 至 2026-12-31 享零费率**（实际扣费以账单为准）。
- **准入**：需 `seller_id`（2088ID）、`seller_app_id`、`service_id`，以及应用私钥与支付宝公钥。
- **接入形态**：自研应用，或第三方应用代调用（传 `app_auth_token`）。

---

## 十、服务端接入步骤

1. 支付宝开放平台创建应用 → 生成应用私钥、上传应用公钥 → 获取 `seller_id` / `seller_app_id`。
2. 开通「AI 按量付费」→ 获取 `service_id`。
3. 填写 `pay/pay_config.json` 的 `alipay_aipay` 段。
4. 放入密钥 `pay/keys/app_private_key.pem` 与 `pay/keys/alipay_public_key.pem`。
5. 受保护端点接入 `pay/payment_gate.py` 的 `PaymentGate.protect(...)`。
6. `npx -y @alipay/alipay-aipay@latest install` 安装官方 AI 付 Skill，完成**沙箱测试与签约入驻**。
7. 自检：`python3 pay/payment_gate.py --selftest`（应 9/9 通过）。

---

## 十一、常见问题与自查清单

**常见问题**
- **401/402 分不清**：本协议用 `402 Payment Required`，账单在 `Payment-Needed` 头。
- **接口调通但买家拿不到内容**：多因未携带 `Payment-Proof` 重试，或未校验 `active`。
- **重复扣费**：`out_trade_no` 不唯一或未做 `trade_no` 幂等。
- **审核被判不合规**：包内出现非支付宝支付渠道的协议标识——须确保只保留支付宝 A2M 链路。

**自查清单（发布前逐项过）**
- [ ] 402 响应带 `Payment-Needed`，账单为 Base64URL 且 RSA2 签名可验；
- [ ] 加签 8 字段齐备、按字典序拼接；
- [ ] 已实现 `Payment-Proof` 解析与携带凭证重试；
- [ ] 已调 `alipay.aipay.agent.payment.verify` 并校验 active/amount/out_trade_no/resource_id；
- [ ] 资源返回后异步调 `alipay.aipay.agent.fulfillment.confirm`；
- [ ] `out_trade_no` 唯一、`trade_no` 不重复履约（幂等）；
- [ ] 三处单价一致；
- [ ] 私钥仅存服务端；
- [ ] `python3 pay/payment_gate.py --selftest` 全通过。

---

## 十二、参考资料

| 用途 | 链接 |
|---|---|
| 支付宝 AI 付官网 | https://aipay.alipay.com/ |
| 产品介绍（费率） | https://opendocs.alipay.com/open/0ix1m4 |
| 产品接入指南 | https://aipay.alipay.com/docs/ai-receive/MACHINE_PAY.html |
| 最佳实践 | https://aipay.alipay.com/article/271 |
| 验付接口文档 | https://ideservice.alipay.com/cms/site/0j7uot |
| 履约接口文档 | https://ideservice.alipay.com/cms/site/0j7sw0 |
| service_id 获取 | https://ideservice.alipay.com/cms/site/0j7uos |
| 示例代码仓库 | https://github.com/alipay/ai/tree/main/code_example/aipay-402-example |
| 官方 Skill 安装 | `npx -y @alipay/alipay-aipay@latest install` |
