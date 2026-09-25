# Fireworks Tech Graph - Scripts

辅助脚本集合，用于提高 SVG 图表生成的稳定性和效率。

## 脚本列表

### 1. validate-svg.sh

SVG 验证脚本，检查 SVG 语法并报告详细错误。

**用法：**
```bash
./validate-svg.sh <svg-file>
```

**检查项目：**
- 标签平衡（开标签 vs 闭标签）
- 属性引号完整性
- 特殊字符转义
- Marker 引用完整性
- 闭合标签 `</svg>`
- rsvg-convert 验证

**示例：**
```bash
./validate-svg.sh /path/to/diagram.svg
```

### 2. generate-diagram.sh

SVG 图表生成脚本，提供自动验证和 PNG 导出。

**用法：**
```bash
./gegram.sh [OPTIONS]
```

**选项：**
- `-t, --type TYPE` - 图表类型（architecture|flowchart|sequence|agent|memory）
- `-s, --style STYLE` - 风格编号（1-8，默认：1）
- `-o, --output PATH` - 输出路径（默认：当前目录）
- `-w, --width WIDTH` - PNG 宽度（像素，默认：1920）
- `--no-validate` - 跳过验证
- `-h, --help` - 显示帮助

**示例：**
```bash
# 生成架构图（Style 1）
./generate-diagram.sh -t architecture -s 1 -o ./output/arch.svg

# 生成流程图（Style 2，2400px 宽）
./generate-diagram.sh -t flowchart -s 2 -w 2400
```

**注���：** SVG 内容生成需要 Claude Code，此脚本提供验证和导出功能。

### 3. test-all-styles.sh

批量测试脚本，测8 种风格的样例图表。

**用法：**
```bash
./test-all-styles.sh
```

**功能：**
- 检查所有风格的参考文件
- 验证现有的 SVG 样例文件
- 导出 PNG 文件到 `test-output/` 目录
- 生成测试报告

**输出：**
- 测试摘要（通过/失败统计）
- PNG 文件（带时间戳）
- 详细的验证错误信息

**示例：**
```bash
./test-all-styles.sh
```

## 依赖

所有脚本需要以下工具：

- **rsvg-convert** - SVG 转 PNG
  ```bash
  brew install librsvg
  ```

- **grep, sed, awk** - 文本处理（macOS 自带）

## 目录结构

```
fireworks-tech-graph/
├── SKILL.md                    # Skill 主文档
├── references/                 # 风格参考文件
│   ├── style-1-flat-icon.md
│   ├── style-2-dark-terminal.md
│   └── ...
├── scripts/                    # 辅助脚本（本目录）
│   ├── README.md              # 本文档
│   ├── validate-svg.sh        # SVG 验证
│   ├── generate-diagram.sh    # 图表生成
│   └── test-all-styl.sh     # 批量测试
└── test-output/               # 测试输出目录（自动创建）
```

## 使用场景

### 场景 1：验证现有 SVG

```bash
cd ~/.claude/skills/fireworks-tech-graph/scripts
./validate-svg.sh /path/to/your-diagram.svg
```

### 场景 2：生成并验证图表

1. 使用 Claude Code 生成 SVG 内容
2. 运行验证和导出：
   ```bash
   ./generate-diagram.sh -t architecture -s 1 -o ./output/arch.svg
   ```

### 场景 3：批量测试所有风格

```bash
cd ~/.claude/skills/fireworks-tech-graph/scripts
./test-all-styles.sh
```

查看测试输出：
```bash
ls -lh ../test-output/
```

## 故障排除

### 问题：rsvg-convert 未找到

**解决方案：**
```bash
brew install librsvg
```

### 问题：权限被拒绝

**解决方案：**
```bash
chmod +x *.sh
```

### 问题：SVG 验证失败

**解决方案：**
1. 查看详细错误信息
2. 使用 Edit 工具修复语法错误
3. 重新运行验证

## 开发说明

### 添加新的验证规则

编辑 `validate-svg.sh`，在现有检查项后添加新的检查逻辑：

```bash
# Check N: Your new check
echo -n "Checking something... "
# Your validation logic here
if [ condition ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${RED}✗ Fail${NC}"
fi
```

### 扩展支持的图表类型

编辑 `generate-diagra，在 `--type` 参数处理中添加新类型。

## 版本历史

- **v1.0.0** (2026-04-11) - 初始版本
  - SVG 验证脚本
  - 图表生成脚本
  - 批量测试脚本

## 许可证

MIT License - 与 fireworks-tech-graph skill 相同

## Python 脚本（v1.2.0 新增）

### 4. render_diagram.py

渲染器：读取分层结构 JSON 规格，按 7 套风格之一生成符合规范的技术图 SVG，校验 XML 合法性后按需导出 PNG。

**用法：**
```bash
python3 scripts/render_diagram.py --spec spec.json --out out/arch.svg --style 3 --width 1920 --png
python3 scripts/render_diagram.py --demo --out out/demo.svg --style 2 --png
```

**参数：**
- `--spec` 规格 JSON 路径（与 `--demo` 二选一）
- `--demo` 使用内置演示规格
- `--out` 输出 SVG 路径（必填）
- `--style` 风格编号 1-7（默认 1）
- `--width` PNG 宽度像素（默认 1920）
- `--png` / `--no-png` 是否导出 PNG

**规格 JSON 结构：**
```json
{"title": "图标题", "legend": true,
 "layers": [{"name": "接入层", "nodes": [{"id": "a", "label": "用户端", "sub": "Web/App"}]}],
 "edges": [{"from": "a", "to": "b", "label": "请求", "kind": "primary"}]}
```

`kind` 取值：primary / control / read / write / async / transform。
PNG 导出按 `rsvg-convert` → `cairosvg` → `inkscape` → ImageMagick `convert` 顺序回退，全部缺失时保持 SVG 交付。

### 5. check_svg.py

交付前静态自检器：标签平衡、属性引号、特殊字符转义、marker 引用、结构与闭合标签、XML 解析，另附中文字体检查。

**用法：**
```bash
python3 scripts/check_svg.py out/arch.svg
python3 scripts/check_svg.py out/arch.svg --cjk --json
```

退出码 0 表示全部通过，1 表示存在问题需修复后重检。

## 路径可移植性说明

`generate-diagram.sh`、`test-all-styles.sh`、`validate-svg.sh` 通过脚本自身位置自动定位技能根目录，
可用环境变量 `SKILL_DIR` 覆盖；风格令牌按编号匹配 `references/style-N-*.md`，不再依赖固定安装路径。
