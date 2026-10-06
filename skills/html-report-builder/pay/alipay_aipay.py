#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alipay_aipay.py — 支付宝 AI 按量付费（A2M / HTTP 402）核心库
================================================================
实现支付宝「AI 按量付费」（AI 收 · Machine Pay · A2M）协议的服务端三件事：

  1) 402 账单下发：未付费时返回 HTTP 402 + `Payment-Needed`（Base64URL 账单，RSA2 签名）
  2) 验付调用   ：收到 `Payment-Proof` 后调用 alipay.aipay.agent.payment.verify
  3) 履约确认   ：资源返回后异步调用 alipay.aipay.agent.fulfillment.confirm

协议要点
--------
* 签名算法：RSA2（SHA256withRSA），目前仅支持 RSA2。
* 账单加签字段（8 个，按 key 字典序拼 a=b&c=d）：
  amount, currency, goods_name, out_trade_no, pay_before, resource_id, seller_id, service_id
* 加签只用本应用私钥，在本地完成，不请求支付宝服务端。
* 幂等：out_trade_no 全局唯一；同一 trade_no 不重复履约。
* 普通下单 / 异步通知 / 主动查单 均不能替代本按量付费协议。

依赖：cryptography（RSA2 签名/验签）；其余为标准库。
"""
from __future__ import annotations

import base64
import json
import os
import random
import sqlite3
import string
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------- 常量
GATEWAY = "https://openapi.alipay.com/gateway.do"
VERIFY_API = "alipay.aipay.agent.payment.verify"
CONFIRM_API = "alipay.aipay.agent.fulfillment.confirm"
SIGN_TYPE = "RSA2"
CST = timezone(timedelta(hours=8))

# 账单加签字段（支付宝规定，按 key 字典序拼接）
BILL_SIGN_FIELDS = [
    "amount", "currency", "goods_name", "out_trade_no",
    "pay_before", "resource_id", "seller_id", "service_id",
]


# ================================================================ RSA2
def _load_private_key(pem: str):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    return load_pem_private_key(pem.encode("utf-8"), password=None)


def _load_public_key(pem: str):
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    return load_pem_public_key(pem.encode("utf-8"))


def rsa2_sign(content: str, private_key_pem: str) -> str:
    """RSA2（SHA256withRSA）加签，返回标准 Base64 签名串。"""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    sig = _load_private_key(private_key_pem).sign(
        content.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


def rsa2_verify(content: str, sign_b64: str, public_key_pem: str) -> bool:
    """RSA2 验签。"""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    try:
        _load_public_key(public_key_pem).verify(
            base64.b64decode(sign_b64), content.encode("utf-8"),
            padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


def sign_content(fields: dict) -> str:
    """按 key 字典序拼 a=b&c=d（用于账单与网关请求加签）。"""
    return "&".join("%s=%s" % (k, fields[k]) for k in sorted(fields))


# ============================================================ 402 账单
def build_bill(order: dict, cfg: dict) -> tuple:
    """构造账单 JSON（protocol + method 两层） + 返回签名串。

    order: {out_trade_no, amount, resource_id, goods_name?, currency?, pay_before?}
    cfg  : pay_config.json 的 alipay_aipay 段（须含 seller_* / service_id / _private_key_pem）
    """
    ttl = int(cfg.get("bill_ttl_seconds", 300))
    pay_before = order.get("pay_before") or (
        datetime.now(CST) + timedelta(seconds=ttl)).isoformat()
    amount = str(order["amount"])
    goods_name = order.get("goods_name") or cfg.get("goods_name", "")
    fields = {
        "amount": amount,
        "currency": order.get("currency", "CNY"),
        "goods_name": goods_name,
        "out_trade_no": order["out_trade_no"],
        "pay_before": pay_before,
        "resource_id": order["resource_id"],
        "seller_id": cfg["seller_id"],
        "service_id": cfg["service_id"],
    }
    content = sign_content(fields)
    signature = rsa2_sign(content, cfg["_private_key_pem"])
    bill = {
        "protocol": {
            "out_trade_no": order["out_trade_no"],
            "amount": amount,
            "currency": order.get("currency", "CNY"),
            "resource_id": order["resource_id"],
            "pay_before": pay_before,
            "seller_signature": signature,
            "seller_sign_type": SIGN_TYPE,
            "seller_unique_id": cfg["seller_id"],
        },
        "method": {
            "seller_name": cfg["seller_name"],
            "seller_id": cfg["seller_id"],
            "seller_app_id": cfg["seller_app_id"],
            "goods_name": goods_name,
            "seller_unique_id_key": "seller_id",
            "service_id": cfg["service_id"],
        },
    }
    return bill, content


def encode_payment_needed(bill: dict) -> str:
    """账单 → Base64URL（去 padding），用于 Payment-Needed 响应头。"""
    raw = json.dumps(bill, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_payment_needed(header: str) -> dict:
    s = (header or "").strip()
    return json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)).decode("utf-8"))


def build_402(order_ctx: dict, cfg: dict) -> tuple:
    """生成 402 响应三元组 (status, body, headers)。"""
    bill, _ = build_bill(order_ctx, cfg)
    headers = {
        "Payment-Needed": encode_payment_needed(bill),
        "Content-Type": "application/json; charset=utf-8",
    }
    body = {
        "error": "Payment Needed",
        "message": "请先支付 %s %s 以访问资源" % (
            order_ctx["amount"], order_ctx.get("currency", "CNY")),
        "resourceId": order_ctx["resource_id"],
    }
    return 402, body, headers


# ======================================================== Payment-Proof
def parse_payment_proof(header: str):
    """解析 Payment-Proof 请求头（Base64）→ {payment_proof, trade_no, client_session}。"""
    if not header:
        return None
    s = header.strip()
    pad = "=" * (-len(s) % 4)
    raw = None
    for dec in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            raw = dec(s + pad)
            break
        except Exception:
            continue
    if raw is None:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    proto = data.get("protocol", {}) or {}
    method = data.get("method", {}) or {}
    return {
        "payment_proof": proto.get("payment_proof"),
        "trade_no": proto.get("trade_no"),
        "client_session": method.get("client_session"),
    }


# ====================================================== 支付宝网关调用
def alipay_request(method: str, biz_content: dict, cfg: dict, timeout: int = 15) -> dict:
    """调用支付宝开放平台网关（公共参数 + RSA2 签名 + form POST）。"""
    params = {
        "app_id": cfg["seller_app_id"],
        "method": method,
        "format": "JSON",
        "charset": "UTF-8",
        "sign_type": SIGN_TYPE,
        "timestamp": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "biz_content": json.dumps(biz_content, ensure_ascii=False, separators=(",", ":")),
    }
    params["sign"] = rsa2_sign(sign_content(params), cfg["_private_key_pem"])
    body = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        GATEWAY, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode("utf-8")
    data = json.loads(text)
    return data.get(method.replace(".", "_") + "_response", data)


def payment_verify(payment_proof, trade_no, client_session, cfg) -> dict:
    """验付：alipay.aipay.agent.payment.verify。
    返回含 code / msg / active / amount / out_trade_no / trade_no / resource_id。"""
    return alipay_request(VERIFY_API, {
        "payment_proof": payment_proof,
        "trade_no": trade_no,
        "client_session": client_session,
    }, cfg)


def fulfillment_confirm(trade_no, cfg) -> dict:
    """履约回执：alipay.aipay.agent.fulfillment.confirm（返回资源后异步调用）。"""
    return alipay_request(CONFIRM_API, {"trade_no": trade_no}, cfg)


# ============================================================ 幂等存储
class OrderStore:
    """订单/履约幂等存储（sqlite3）。
    保证：out_trade_no 唯一；同一 trade_no 不重复履约。"""

    def __init__(self, path: str = "pay/orders.db"):
        self.path = os.path.expanduser(path)
        d = os.path.dirname(self.path)
        if d:
            os.makedirs(d, exist_ok=True)
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS orders(
                out_trade_no TEXT PRIMARY KEY,
                resource_id  TEXT,
                amount       TEXT,
                goods_name   TEXT,
                trade_no     TEXT,
                status       TEXT DEFAULT 'created',
                created_at   INTEGER,
                confirmed_at INTEGER)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_orders_trade ON orders(trade_no)")

    def create(self, out_trade_no, resource_id, amount, goods_name=""):
        with self._conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO orders(out_trade_no,resource_id,amount,goods_name,created_at)"
                " VALUES(?,?,?,?,?)",
                (out_trade_no, resource_id, str(amount), goods_name, int(time.time())))

    def get(self, out_trade_no):
        with self._conn() as c:
            r = c.execute("SELECT * FROM orders WHERE out_trade_no=?",
                          (out_trade_no,)).fetchone()
        return dict(r) if r else None

    def mark_paid(self, out_trade_no, trade_no, resource_id=None):
        with self._conn() as c:
            if out_trade_no and self.get(out_trade_no):
                c.execute("UPDATE orders SET trade_no=?, status='paid' WHERE out_trade_no=?",
                          (trade_no, out_trade_no))
            else:
                c.execute(
                    "INSERT OR REPLACE INTO orders(out_trade_no,resource_id,amount,trade_no,status,created_at)"
                    " VALUES(?,?,?,?, 'paid', ?)",
                    (out_trade_no or trade_no, resource_id, "", trade_no, int(time.time())))

    def is_fulfilled(self, trade_no) -> bool:
        with self._conn() as c:
            r = c.execute("SELECT 1 FROM orders WHERE trade_no=? AND status='fulfilled' LIMIT 1",
                          (trade_no,)).fetchone()
        return r is not None

    def mark_fulfilled(self, trade_no):
        with self._conn() as c:
            c.execute("UPDATE orders SET status='fulfilled', confirmed_at=? WHERE trade_no=?",
                      (int(time.time()), trade_no))


# ================================================================ 工具
def new_out_trade_no(prefix: str = "ORDER") -> str:
    """生成全局唯一商户订单号（≤32 位）。"""
    return "%s_%d_%s" % (
        prefix, int(time.time() * 1000),
        "".join(random.choices(string.ascii_lowercase + string.digits, k=6)))


def load_config(path: str = "pay/pay_config.json") -> dict:
    """读取 pay_config.json 并内联密钥 PEM，供核心库直接使用。"""
    path = os.path.expanduser(path)
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    a = dict(cfg.get("alipay_aipay", {}))
    base = os.path.dirname(os.path.abspath(path))

    def _key(k):
        if a.get(k):
            return a[k]
        p = a.get(k + "_path")
        if p:
            p = p if os.path.isabs(p) else os.path.join(base, p)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as fh:
                    return fh.read()
        return None

    a["_private_key_pem"] = _key("app_private_key")
    a["_alipay_public_key_pem"] = _key("alipay_public_key")
    a["_config"] = cfg
    return a
