# pay/ — 支付宝 AI 按量付费（A2M / 402）接入模块

本模块让 `html-report-builder` 作为 **Pay Skill** 被 AI Agent 调用时，
通过**支付宝 AI 按量付费（AI 收 · Machine Pay · A2M）** 协议完成自动收款。
每次调用定价 **0.20 元**（按调用量计费）。

> 支付链路为**支付宝 A2M 协议**（`Payment-Needed` / `Payment-Proof` /
> `alipay.aipay.agent.payment.verify` / `alipay.aipay.agent.fulfillment.confirm`），
> 不含任何其他支付渠道的实现。

## 一、协议链路（4 步）

| 步骤 | 动作 | 关键要素 |
|---|---|---|
| 1. 402 账单下发 | 请求无有效凭证时返回 `HTTP 402 Payment Required` | `Payment-Needed` 响应头（Base64URL 账单，RSA2 签名） |
| 2. 携带凭证重试 | 用户支付后，Agent 带凭证重发原请求 | `Payment-Proof` 请求头（解出 `payment_proof` / `trade_no` / `client_session`） |
| 3. 验付调用 | 服务端调用 `alipay.aipay.agent.payment.verify` | 校验 `active` / `amount` / `out_trade_no` / `resource_id` 一致 |
| 4. 履约确认 | 资源返回后**异步**调用 `alipay.aipay.agent.fulfillment.confirm` | 参数 `trade_no`；不重复履约 |

不通过任一步校验 → 重新返回 402，让 Agent 重新支付。

## 二、目录清单

| 文件 | 作用 |
|---|---|
| `alipay_aipay.py` | 核心库：RSA2 加签/验签、账单构造、`Payment-Needed` 编解码、`Payment-Proof` 解析、网关调用（verify / confirm）、幂等存储 |
| `payment_gate.py` | 付费闸口：`PaymentGate.protect(...)` 一行接入业务端点；含离线自测 |
| `pay_config.json` | 计费与商户配置（单价、`seller_*`、`service_id`、密钥路径、单价三处核对清单） |
| `requirements.txt` | 依赖：`cryptography` |
| `keys/` | 应用私钥 / 支付宝公钥放置目录（见 `keys/README.md`） |

## 三、账单结构（Payment-Needed 解码后）

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

**加签字段（8 个，按 key 字典序拼 `k=v&k=v`）**：
`amount, currency, goods_name, out_trade_no, pay_before, resource_id, seller_id, service_id`
—— 用**应用私钥**在本地加签（不请求支付宝服务端）。

## 四、接入业务端点

```python
from payment_gate import PaymentGate

gate = PaymentGate("pay/pay_config.json")

def render_endpoint(request):
    return gate.protect(
        proof_header=request.headers.get("Payment-Proof"),
        resource_id="html-report/render",
        deliver=lambda: build_report(request.body),   # 验付通过后才执行
    )   # -> (status, body_dict, headers_dict)
```

## 五、部署与配置

1. 在**支付宝开放平台**创建应用，生成应用私钥、上传应用公钥、获取 `seller_id(seller_app_id)`。
2. 开通「AI 按量付费」，获取 `service_id`（见 https://ideservice.alipay.com/cms/site/0j7uos ）。
3. 填写 `pay_config.json` 的 `alipay_aipay` 段（`seller_id` / `seller_name` / `seller_app_id` / `service_id`）。
4. 放入密钥：`keys/app_private_key.pem`、`keys/alipay_public_key.pem`。
5. 安装依赖：`pip install -r pay/requirements.txt`。
6. 用 `npx -y @alipay/alipay-aipay@latest install` 安装官方 AI 付 Skill，**完成沙箱测试与签约入驻**。

## 六、自测

```bash
python3 pay/payment_gate.py --selftest          # 离线自测，逐项打印 9 项结果
python3 pay/payment_gate.py --challenge html-report/render   # 生成一次 402 账单（调试）
```

## 七、幂等与对账

- `out_trade_no`：全局唯一，用于幂等与防重复支付（≤32 位）。
- `trade_no`：**不应被重复履约**，避免同一笔支付被多次使用。
- `pay_before`：账单有效期（`bill_ttl_seconds`，默认 300s），过期账单不可继续支付。
- 订单 / 履约记录落库（`orders.db`），支持「支付、用量、履约」三账核对。

## 八、常见问题

- **费率**：单笔 1.0%；个人开发者优惠期 2026-04-15 至 2026-12-31 零费率，以账单为准。
- **普通下单/异步通知/主动查单** 不能替代本按量付费协议。
- **客户端显示成功** 不能作为凭证验证或履约完成的依据，必须以服务端 verify 为准。
