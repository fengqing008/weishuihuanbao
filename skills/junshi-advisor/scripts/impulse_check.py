#!/usr/bin/env python3
"""狗头军师 · 冲动拦截
对你准备发送的消息做冲动指数评估，给出「发 / 缓 / 删」建议与冷静动作。
维度：长度、情绪词、质问、通牒、深夜、标点密度、连发、索取、自我贬低。
"""
import argparse, re, sys

EMO_WORDS = ["气死", "受够", "委屈", "难受", "凭什么", "过分", "恶心", "烦死",
             "绝了", "崩溃", "心寒", "失望透顶", "不可理喻"]
ABSOLUTE = ["从来", "总是", "永远", "根本不", "一点都不", "再也不"]
BLAME = ["都是你", "怪你", "因为你", "你害"]
SELF_DOWN = ["我不重要", "随便你", "无所谓", "算了", "反正", "不配"]
DEMAND = ["你为什么不回", "说清楚", "给我个交代", "你必须", "你得给个说法"]
ULTIMATUM = ["最后一次", "否则", "不然", "必须", "要么", "别怪我"]


def score(text, hour, lines):
    reasons, total = [], 0
    n = len(text)

    if n > 200:
        total += 15; reasons.append(f"消息过长（{n} 字）：长文是冲动放大器 +15")
    elif n > 100:
        total += 8; reasons.append(f"消息偏长（{n} 字）+8")

    hit_emo = [w for w in EMO_WORDS if w in text]
    if hit_emo:
        pts = min(len(hit_emo) * 8, 30)
        total += pts; reasons.append(f"情绪词 {hit_emo} +{pts}")

    hit_abs = [w for w in ABSOLUTE if w in text]
    if hit_abs:
        total += min(len(hit_abs) * 6, 12); reasons.append(f"绝对化表达 {hit_abs}")

    hit_blame = [w for w in BLAME if w in text]
    if hit_blame:
        total += min(len(hit_blame) * 8, 16); reasons.append(f"指责句式 {hit_blame}")

    q = len(re.findall(r"(为什么|凭什么|你到底|是不是|你敢)", text))
    if q:
        total += min(q * 8, 20); reasons.append(f"质问句 x{q}")

    hit_ult = [w for w in ULTIMATUM if w in text]
    if hit_ult:
        total += min(len(hit_ult) * 12, 24); reasons.append(f"通牒式表达 {hit_ult}")

    hit_dem = [w for w in DEMAND if w in text]
    if hit_dem:
        total += min(len(hit_dem) * 10, 20); reasons.append(f"索取交代 {hit_dem}")

    hit_sd = [w for w in SELF_DOWN if w in text]
    if hit_sd:
        total += min(len(hit_sd) * 8, 16); reasons.append(f"自我贬低 {hit_sd}")

    ex = text.count("!"); ex += text.count("！")
    if ex:
        total += min(ex * 3, 12); reasons.append(f"感叹号 x{ex}")

    if lines and lines > 3:
        total += 10; reasons.append(f"连发 {lines} 段：多段轰炸 +10")

    if hour is not None and (hour >= 23 or hour < 7):
        total += 12; reasons.append(f"发送时段 {hour} 点：深夜决策 +12")

    return min(total, 100), reasons


def level(s):
    if s < 25: return "冷静区", "可以发。核对一遍措辞即可。"
    if s < 45: return "略热区", "可以发，但删掉情绪词与绝对化表达。"
    if s < 65: return "升温区", "建议缓发：先放 30 分钟，回来再读一遍。"
    if s < 85: return "高危区", "建议别发：这条大概率让你后悔，今晚先存草稿。"
    return "失控区", "删了重写：现在发出去的是情绪，不是你想说的话。"


def main():
    ap = argparse.ArgumentParser(description="评估待发消息的冲动指数并给拦截建议")
    ap.add_argument("--text", help="你准备发送的消息")
    ap.add_argument("--file", help="从文件读取消息")
    ap.add_argument("--hour", type=int, help="发送时段（0-23）")
    args = ap.parse_args()

    if not args.text and not args.file:
        ap.error("请提供 --text 或 --file")
    text = args.text or open(args.file, encoding="utf-8", errors="ignore").read()
    lines = len([l for l in text.splitlines() if l.strip()])

    s, reasons = score(text, args.hour, lines)
    name, advice = level(s)

    print("=" * 56)
    print("狗头军师 · 冲动拦截")
    print("=" * 56)
    print(f"\n冲动指数：{s}/100 —— {name}")
    print(f"建议：{advice}\n")
    if reasons:
        print("扣分项：")
        for r in reasons:
            print(f"  · {r}")
    else:
        print("未检出明显冲动特征，节奏平稳。")
    print("\n现在就做的一件事：把这条消息原样复制到备忘录，定个 20 分钟后的闹钟，"
          "闹钟响了再决定发不发。多数时候你会自己删掉它。")


if __name__ == "__main__":
    main()
