#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QBS 法 · 合规取书路径生成器（零第三方依赖）

按书名/作者生成合法获取路径清单，并依「作者卒年 + 50 年」判定公有领域状态。
"""
import argparse
import sys
from datetime import datetime


def main():
    ap = argparse.ArgumentParser(description="QBS 合规取书路径生成器")
    ap.add_argument("--book", required=True, help="书名")
    ap.add_argument("--author", required=True, help="作者")
    ap.add_argument("--first-pub-year", type=int, default=0, help="首版年份")
    ap.add_argument("--death-year", type=int, default=0, help="作者卒年（用于公版判断）")
    ap.add_argument("--out", default="source.md", help="输出 Markdown 路径（默认 source.md）")
    ap.add_argument("--now-year", type=int, default=datetime.now().year, help="基准年份（默认当前年）")
    args = ap.parse_args()

    pd = False
    ancient = False
    reason = "作者卒年未提供，无法判定公版状态；按在版作品处理。"
    if args.death_year and args.now_year - args.death_year >= 50:
        pd = True
        reason = "作者卒年 %d，距今 %d 年，已超 50 年保护期，属公有领域作品。" % (
            args.death_year, args.now_year - args.death_year)
    elif args.death_year:
        reason = "作者卒年 %d，距今 %d 年，尚在 50 年保护期内，属在版作品。" % (
            args.death_year, args.now_year - args.death_year)
    elif args.first_pub_year and args.now_year - args.first_pub_year > 100:
        pd = True
        ancient = True
        reason = "首版于 %d 年，距今 %d 年，属历史作品，极可能已进入公有领域（本版本译注者/编校者的版权须另行核验）。" % (
            args.first_pub_year, args.now_year - args.first_pub_year)

    lines = []
    lines.append("# 合规取书路径：%s\n" % args.book)
    lines.append("- **作者**：%s" % args.author)
    if args.first_pub_year:
        lines.append("- **首版年份**：%d" % args.first_pub_year)
    lines.append("- **版权状态**：%s" % reason)
    lines.append("")
    lines.append("## 合法获取路径\n")
    if pd:
        lines.append("**A. 公有领域免费全文（首选）**\n")
        lines.append("| 来源 | 说明 |")
        lines.append("|:--|:--|")
        lines.append("| 古登堡计划（gutenberg.org） | 公版西文图书全文，可免费下载 |")
        lines.append("| 中国哲学书电子化计划（ctext.org） | 公版中文古籍与典籍 |")
        lines.append("| 维基文库（zh.wikisource.org） | 公版中文作品全文 |")
        lines.append("")
    lines.append("**B. 正版电子书平台**（购买/订阅后合法阅读）\n")
    lines.append("| 类型 | 常见渠道 |")
    lines.append("|:--|:--|")
    lines.append("| 综合电子书城 | 微信读书、京东读书、当当云阅读、豆瓣阅读 |")
    lines.append("| 外文原版 | Kindle、Google Play Books、出版社官方电子版 |")
    lines.append("")
    lines.append("**C. 公共图书馆借阅**（免费或低成本）\n")
    lines.append("| 类型 | 说明 |")
    lines.append("|:--|:--|")
    lines.append("| 国家图书馆 / 省市图书馆 | 办证后借阅纸质书与部分电子资源 |")
    lines.append("| 高校图书馆 / 馆际互借 | 通过合作馆调配 |")
    lines.append("| 超星 / 读秀等学术检索 | 部分提供在线阅读 |")
    lines.append("")
    lines.append("**D. 纸质购买**：各电商与实体书店，按权威出版社新译本优先选购。")
    lines.append("")
    lines.append("## 版权边界与降级\n")
    lines.append("- 不采用影子图书馆（Z-Library 等）等盗版渠道：存在法律风险，文本质量与版本完整性无保障。")
    lines.append("- 无法取得全文时降级使用高质量二手材料：权威书评、作者公开讲义、再版序言与导读；在解题报告中标注降级事实。")
    lines.append("- 转换与使用限定于自有或已获授权的内容。")
    lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("已生成取书路径：%s（版权状态：%s）" % (args.out, "公有领域" if pd else "在版作品"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
