# 失败模式与常见错误

记录 Excalidraw 图表生成中的高频失败场景，用于快速排查。

---

## 失败模式速查表

| # | 失败模式 | 根因 | 修复动作 |
|---|---------|------|---------|
| 1 | JSON 文件打开后空白或报错 | `text` 属性包含非文字字符（如 JSON 嵌套结构） | `text` 和 `originalText` 只放纯文本，代码内容放到独立 evidence artifact 矩形中 |
| 2 | 箭头不跟随元素移动，布局调整后断裂 | 箭头 `startBinding`/`endBinding` 缺失或引用了不存在的 elementId | 每条箭头必须绑定两端元素，ID 必须与实际 element.id 严格一致 |
| 3 | 大图生成中途截断，JSON 不完整 | 一次性生成全部元素，超出 token 输出限制 | 按 section 分批生成，每批只添加一个区域的元素 |
| 4 | 文字被容器裁切或溢出 | 容器宽度不足，未按实际文字长度调整 | 用 `rawText.length * fontSize * 0.6` 估算文字宽度，容器宽度 ≥ 文字宽度 + 40px |
| 5 | 渲染后发现元素重叠或箭头交叉 | 仅凭 JSON 坐标判断位置，未执行渲染验证 | 必须执行 render→view→fix 循环，至少迭代 2-4 次 |
| 6 | 所有概念使用相同矩形+相同颜色，视觉单调 | 未按语义选择不同视觉模式 | 每个主要概念使用不同形状（ellipse/diamond/rectangle/lines+text）和不同语义色 |
| 7 | opacity 不是 100 导致半透明元素在深色背景下不可读 | 使用了默认 opacity 值 | 所有元素强制 `opacity: 100`，用颜色和大小做层次区分 |
| 8 | fontFamily 不一致，跨平台渲染结果不同 | 遗漏 fontFamily 字段或使用了非标准值 | 所有文字元素统一设置 `fontFamily: 3` |
