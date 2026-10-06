# 中文字体与渲染（cjk-font-and-render）

> 来源：FM-017（中文字体渲染）处置固化。出图 / 出网页前必读。

## 一、中文字体渲染（FM-017，中）

**现象**：Python 绘图（matplotlib / PIL）中文显示为方框（tofu）；HTML 未指定 CJK 字体栈时落到系统默认或被替换。

**处置**：
1. 绘图前**显式注册 CJK 字体**（Noto Sans CJK SC / 思源黑体），设置 `rcParams['font.sans-serif']` 并 `axes.unicode_minus=False`；
2. 缺字体时优先用**系统已装字体**，其次下载到本地字体目录（非系统盘，避免权限问题）；
3. HTML 一律给**完整 CJK 字体栈**：`-apple-system, "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`；
4. 出图后**目视抽检**中文是否正常——自动化检查无法完全替代肉眼确认。
