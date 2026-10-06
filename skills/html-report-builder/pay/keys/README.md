# 密钥放置说明

本目录放置支付宝应用密钥。**不要提交到任何公开仓库，也不要写入技能发布包。**

| 文件 | 内容 | 获取方式 |
|---|---|---|
| `app_private_key.pem` | 应用私钥（PKCS8 PEM），用于账单与网关请求的 RSA2 加签 | 支付宝开放平台 → 密钥工具生成 |
| `alipay_public_key.pem` | 支付宝公钥，用于校验支付宝响应签名 | 开放平台应用详情页 |

生产环境建议改用环境变量注入（如 `ALIPAY_APP_PRIVATE_KEY` / `ALIPAY_PUBLIC_KEY`）
或密钥管理服务，避免明文落盘。`pay_config.json` 的 `app_private_key_path` /
`alipay_public_key_path` 可直接指向外部路径。
