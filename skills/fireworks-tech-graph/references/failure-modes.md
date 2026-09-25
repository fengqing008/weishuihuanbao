# 失败模式库

本文档记录 fireworks-tech-graph 技能在生成技术图时的常见失败模式及对应处置路径。

## SVG 生成阶段

如果 SVG 标签未闭合（缺少 `</svg>`）→ 追加 `</svg>` 关闭标签后重新验证。

如果属性值未加引号（如 `fill=#9dd4c7`）→ 替换为 `fill="#9dd4c7"`，用 Edit 工具修复该行。

如果文本中包含未转义的 `<`、`>`、`&` → 替换为 `&lt;`、`&gt;`、`&amp;`。

如果 `marker-end="url(#arrow-xxx)"` 引用了不存在的 marker → 在 `<defs>` 中补全对应 `<marker id="arrow-xxx">` 定义。

如果 Bash heredoc 生成 SVG 时发生截断或编码损坏 → 切换为 Python 脚本方法（三引号写入），避免 heredoc 问题。

如果 Python 脚本生成的 SVG 仍含转义错误 → 改用 Write 工具直接写入完整 SVG 字符串（L<150 行时）。

## 验证与导出阶段

如果 `rsvg-convert` 报错 "Extra content at the end of the document" → 检查末尾是否有多余内容或缺少 `</svg>`。

如果 `rsvg-convert` 报错 "Couldn't find end of Start Tag"（行 N）→ 读取第 N 行，定位被截断的属性值并补全。

如果 `rsvg-convert` 报错 "Invalid character"（行 N）→ 读取第 N 行，将特殊字符替换为 HTML 实体。

如果 PNG 导出空白 → 检查 SVG 是否包含实际图形元素，而非仅有 `<defs>`。

如果 `rsvg-convert` 不可用 → 向用户报告依赖缺失，输出 SVG 作为最终交付物。

## 布局与样式阶段

如果节点文字溢出矩形框 → 使用 `text-anchor="middle"` 居中 + `clipPath` 裁剪 + 缩短标签。

如果箭头直接穿过节点 → 改用正交路由（L形路径）或贝塞尔曲线绕行。

如果箭头标签与其他元素重叠 → 为标签添加背景矩形（填充画布底色，opacity=0.95）。

如果图中使用超过4种箭头颜色 → 合并语义相近的箭头类型，控制在4种以内。

如果加载的样式参考文件不存在 → 降级到默认 Flat Icon 样式（style-1-flat-icon.md）。

## 重试与降级策略

如果同一错误出现2次 → 立即切换生成方法（如从直接写入切换到 Python 脚本）。

如果3次尝试均失败 → 停止重试，向用户报告完整错误信息、行号和建议修复方案。

如果 rsvg-convert 验证通过但视觉效果异常 → 对比 style 参考文件中的颜色 token，逐项核对填充色和描边色。
