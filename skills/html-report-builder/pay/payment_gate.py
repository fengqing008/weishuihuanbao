#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
payment_gate.py — 支付宝 A2M 付费闸口（供技能业务端点调用）
================================================================
把受保护的业务端点包一层「付费闸口」，完整走支付宝 AI 按量付费（402）链路：

    无凭证      → 402 + Payment-Needed（Base64URL 账单，RSA2 签名）
    有凭证      → 解析 Payment-Proof → 调 alipay.aipay.agent.payment.verify
                  → 校验 active/amount/out_trade_no/resource_id
                  → 通过则交付资源 + 异步调 alipay.aipay.agent.fulfillment.confirm
    凭证无效    → 再次 402
    重复 trade_no → 幂等命中，不重复计费与履约

用法（业务侧）
--------------
    from payment_gate import PaymentGate
    gate = PaymentGate("pay/pay_config.json")

    def endpoint(request):
        return gate.protect(
            proof_header=request.headers.get("Payment-Proof"),
            resource_id="html-report/render",
            deliver=lambda: render_html(request.body),   # 验付通过后执行
        )  # -> (status, body_dict, headers_dict)

自测
----
    python3 payment_gate.py --selftest        # 离线自测（无需真实密钥/网络）
    python3 payment_gate.py --challenge RES   # 生成一次 402 账单（调试）
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alipay_aipay as A  # noqa: E402


class PaymentGate:
    """支付宝 A2M 付费闸口。"""

    def __init__(self, config_path="pay/pay_config.json", store_path="pay/orders.db",
                 verify_fn=None, confirm_fn=None):
        self.cfg = A.load_config(config_path)
        self.price = str(self.cfg["_config"]["pay_skill"]["price"])
        self.resource_default = self.cfg["_config"].get("endpoints", {}).get("resource", "html-report/render")
        self.store = A.OrderStore(store_path)
        self._verify = verify_fn or (
            lambda **kw: A.payment_verify(
                kw["payment_proof"], kw["trade_no"], kw["client_session"], self.cfg))
        self._confirm = confirm_fn or (lambda trade_no: A.fulfillment_confirm(trade_no, self.cfg))

    # ------------------------------------------------------------ 订单
    def new_order(self, resource_id, goods_name=None):
        out = A.new_out_trade_no()
        self.store.create(out, resource_id, self.price,
                          goods_name or self.cfg.get("goods_name", ""))
        return {"out_trade_no": out, "amount": self.price, "currency": "CNY",
                "resource_id": resource_id,
                "goods_name": goods_name or self.cfg.get("goods_name", "")}

    def challenge(self, resource_id=None, order_ctx=None):
        """生成 402 响应三元组。order_ctx 缺 out_trade_no 时自动新建订单。"""
        if not order_ctx or "out_trade_no" not in order_ctx:
            order_ctx = self.new_order(resource_id or self.resource_default)
        return A.build_402(order_ctx, self.cfg)

    # -------------------------------------------------------- 付费闸口
    def protect(self, proof_header, resource_id, deliver, order_ctx=None):
        """返回 (status, body, headers)。

        proof_header : 请求头 Payment-Proof 原值（缺失则触发 402）
        resource_id  : 本次访问的资源标识
        deliver      : 无参函数，验付通过后执行并返回业务结果
        order_ctx    : 期望校验的订单上下文（含 out_trade_no）；缺省仅校验金额与资源
        """
        order_ctx = order_ctx or {"amount": self.price, "currency": "CNY",
                                  "resource_id": resource_id,
                                  "goods_name": self.cfg.get("goods_name", "")}

        # 1) 无凭证 → 402 下发账单
        if not proof_header:
            return self.challenge(resource_id=resource_id)

        # 2) 解析 Payment-Proof
        proof = A.parse_payment_proof(proof_header)
        if not proof or not proof.get("payment_proof") or not proof.get("trade_no"):
            return self.challenge(resource_id=resource_id)

        # 3) 幂等：同一 trade_no 已履约 → 不重复计费（返回放行标记）
        if self.store.is_fulfilled(proof["trade_no"]):
            return 200, {"replay": True, "trade_no": proof["trade_no"],
                         "result": deliver()}, {}

        # 4) 验付
        try:
            vr = self._verify(payment_proof=proof["payment_proof"],
                              trade_no=proof["trade_no"],
                              client_session=proof["client_session"])
        except Exception as exc:                      # 网络/接口异常 → 让用户重试支付
            return self.challenge(resource_id=resource_id)

        ok, reason = self._validate(vr, order_ctx)
        if not ok:
            _, _, headers = self.challenge(resource_id=resource_id)
            return 402, {"error": "Payment Needed",
                         "message": "支付凭证校验未通过：%s" % reason,
                         "resourceId": resource_id}, headers

        # 5) 交付资源 + 记录 → 异步履约回执
        self.store.mark_paid(order_ctx.get("out_trade_no", ""), proof["trade_no"],
                             resource_id=resource_id)
        result = deliver()
        self.store.mark_fulfilled(proof["trade_no"])
        threading.Thread(target=self._safe_confirm, args=(proof["trade_no"],),
                         daemon=True).start()
        return 200, {"result": result, "trade_no": proof["trade_no"]}, {}

    # ------------------------------------------------------------ 校验
    def _validate(self, vr, order_ctx):
        """按支付宝规范逐项校验，任一不符即拒绝。"""
        if str(vr.get("code")) != "10000":
            return False, "verify code=%s msg=%s" % (vr.get("code"), vr.get("msg"))
        if vr.get("active") is not True:
            return False, "active != true"
        if str(vr.get("amount")) != str(order_ctx["amount"]):
            return False, "金额不符（账单 %s / 凭证 %s）" % (order_ctx["amount"], vr.get("amount"))
        if str(vr.get("resource_id") or "") != str(order_ctx["resource_id"]):
            return False, "resource_id 不符"
        if order_ctx.get("out_trade_no") and str(vr.get("out_trade_no")) != str(order_ctx["out_trade_no"]):
            return False, "out_trade_no 不符"
        return True, "ok"

    def _safe_confirm(self, trade_no):
        try:
            self._confirm(trade_no)
        except Exception:
            pass


# ================================================================ 自测
def _selftest():
    """离线自测：临时 RSA 密钥，验证账单签名/Base64URL/Proof 解析/402/验付/幂等/金额校验。"""
    import tempfile
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()
    pub = key.public_key().public_bytes(serialization.Encoding.PEM,
                                        serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    cfg = {"seller_id": "2088xxxxxxxx", "seller_name": "测试商家",
           "seller_app_id": "app_123456", "service_id": "xxxx_12344",
           "goods_name": "HTML 成果输出引擎", "bill_ttl_seconds": 300,
           "_private_key_pem": priv, "_alipay_public_key_pem": pub,
           "_config": {"pay_skill": {"price": "0.20"}}}

    fails = []

    # 1) 账单构造 + RSA2 签名/验签
    order = {"out_trade_no": A.new_out_trade_no(), "amount": "0.20",
             "resource_id": "html-report/render", "goods_name": "HTML 成果输出引擎"}
    bill, content = A.build_bill(order, cfg)
    if A.rsa2_verify(content, bill["protocol"]["seller_signature"], pub):
        print("PASS  1. 账单 RSA2 加签/验签")
    else:
        fails.append("账单签名")
        print("FAIL  1. 账单签名")

    # 2) 8 个加签字段齐备
    if all(f in content for f in A.BILL_SIGN_FIELDS):
        print("PASS  2. 账单 8 个加签字段齐备（字典序拼接）")
    else:
        fails.append("加签字段")
        print("FAIL  2. 加签字段缺失")

    # 3) Payment-Needed 编解码
    hdr = A.encode_payment_needed(bill)
    dec = A.decode_payment_needed(hdr)
    if dec["protocol"]["out_trade_no"] == order["out_trade_no"] and "=" not in hdr:
        print("PASS  3. Payment-Needed Base64URL 编解码")
    else:
        fails.append("Payment-Needed")
        print("FAIL  3. Payment-Needed 编解码")

    # 4) Payment-Proof 解析
    proof_obj = {"protocol": {"payment_proof": "abc123def456", "trade_no": "2026040900828111317760000001"},
                 "method": {"client_session": "sess-xyz"}}
    ph = base64.b64encode(json.dumps(proof_obj).encode()).decode()
    p = A.parse_payment_proof(ph)
    if p and p["trade_no"] == "2026040900828111317760000001" and p["payment_proof"] == "abc123def456":
        print("PASS  4. Payment-Proof 解析（凭证/订单号/会话）")
    else:
        fails.append("Payment-Proof")
        print("FAIL  4. Payment-Proof 解析")

    # 5) 闸口：无凭证 → 402 + Payment-Needed
    gate = PaymentGate.__new__(PaymentGate)
    gate.cfg = cfg
    gate.price = "0.20"
    gate.resource_default = "html-report/render"
    gate.store = A.OrderStore(os.path.join(tempfile.mkdtemp(), "t.db"))
    gate._confirm = lambda tn: None
    gate._verify = lambda **kw: {"code": "10000", "msg": "Success", "active": True,
                                 "amount": "0.20", "resource_id": "html-report/render",
                                 "out_trade_no": order["out_trade_no"],
                                 "trade_no": kw["trade_no"]}
    st, body, hdrs = gate.protect(None, "html-report/render", lambda: "OUTPUT")
    if st == 402 and "Payment-Needed" in hdrs:
        print("PASS  5. 无凭证 → 402 + Payment-Needed")
    else:
        fails.append("402")
        print("FAIL  5. 无凭证 402")

    # 6) 携带凭证 → 验付通过 → 200 放行
    gate._verify = lambda **kw: {"code": "10000", "msg": "Success", "active": True,
                                 "amount": "0.20", "resource_id": "html-report/render",
                                 "out_trade_no": order["out_trade_no"],
                                 "trade_no": kw["trade_no"]}
    st, body, hdrs = gate.protect(ph, "html-report/render", lambda: "OUTPUT")
    if st == 200 and body.get("result") == "OUTPUT":
        print("PASS  6. 携带凭证 → 验付通过 → 200 交付")
    else:
        fails.append("验付放行")
        print("FAIL  6. 验付放行")

    # 7) 重复 trade_no → 幂等命中
    st, body, hdrs = gate.protect(ph, "html-report/render", lambda: "OUTPUT")
    if st == 200 and body.get("replay") is True:
        print("PASS  7. 重复 trade_no 幂等命中（不重复计费）")
    else:
        fails.append("幂等")
        print("FAIL  7. 幂等命中")

    # 8) 金额不符 → 402（用新 trade_no，避免命中幂等）
    def _mk_proof(tn):
        o = {"protocol": {"payment_proof": "pf_" + tn, "trade_no": tn},
             "method": {"client_session": "s_" + tn}}
        return base64.b64encode(json.dumps(o).encode()).decode()

    gate._verify = lambda **kw: {"code": "10000", "msg": "Success", "active": True,
                                 "amount": "0.01", "resource_id": "html-report/render",
                                 "out_trade_no": order["out_trade_no"], "trade_no": kw["trade_no"]}
    st, _, _ = gate.protect(_mk_proof("T2"), "html-report/render", lambda: "OUTPUT")
    if st == 402:
        print("PASS  8. 金额不符 → 402 拒绝")
    else:
        fails.append("金额校验")
        print("FAIL  8. 金额校验")

    # 9) active=false → 402
    gate._verify = lambda **kw: {"code": "10000", "msg": "Success", "active": False,
                                 "amount": "0.20", "resource_id": "html-report/render",
                                 "out_trade_no": order["out_trade_no"], "trade_no": kw["trade_no"]}
    st, _, _ = gate.protect(_mk_proof("T3"), "html-report/render", lambda: "OUTPUT")
    if st == 402:
        print("PASS  9. active=false → 402 拒绝")
    else:
        fails.append("active 校验")
        print("FAIL  9. active 校验")

    print("\n[selftest] %s（%d/9 通过）" % ("全部通过" if not fails else "存在失败",
                                           9 - len(fails)))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="支付宝 A2M 付费闸口")
    ap.add_argument("--selftest", action="store_true", help="离线自测（无需真实密钥/网络）")
    ap.add_argument("--challenge", metavar="RESOURCE_ID", help="生成一次 402 账单（调试）")
    ap.add_argument("--config", default="pay/pay_config.json", help="pay_config.json 路径")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    if args.challenge:
        gate = PaymentGate(args.config)
        st, body, hdrs = gate.challenge(resource_id=args.challenge)
        print("HTTP", st)
        print(json.dumps(body, ensure_ascii=False, indent=2))
        print("Payment-Needed:", hdrs.get("Payment-Needed"))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
