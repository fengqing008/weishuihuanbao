# 联动调用契约

本技能定位为「插图引擎」，输出图与落位清单，由承载技能负责落版。以下三份契约保证跨技能联动不跑偏。

## 一、批量契约

**输入**：稿件清单 JSON。

```json
{
  "book": {"title": "书名"},
  "articles": [
    {"order": 1, "title": "篇名", "column": "文苑", "body": "01-xx.md"},
    {"order": 2, "title": "篇名", "column": "点滴", "body": "02-xx.md"}
  ]
}
```

**输出**：配图清单 JSON，键为 `order`，值为图项数组。

```json
{
  "1": [
    {"file": "images/auto/art1_1_lamp.png", "motif": "lamp", "role": "wide"},
    {"file": "images/auto/art1_2_book.png", "motif": "book", "role": "inline"}
  ]
}
```

**命令**：

```bash
python3 scripts/lineart_cli.py --manifest book.json --per-article 3 \
    --outdir images/auto --palette sepia --style pencil -o auto_images.json
```

要点：`--outdir` 相对于清单文件所在目录；每篇 2–3 张由 `--per-article` 控制。

## 二、落位契约

| role | 尺寸 | 落位规则 |
|---|---|---|
| `wide` | 1500×820 | 跨栏大图，置于首段之后，占满栏宽 |
| `inline` | 760×980 | 栏内浮图，置于中段，浮于一侧 |
| `inline-end` | 760×980 | 栏内浮图，靠篇末，收尾用 |

篇数与落位对应：1 张→wide；2 张→wide + inline；3 张→wide + inline + inline-end。

承载技能按 role 决定图宽、浮动方向与段落插入点，不需要再换算比例。

## 三、风格契约

同一批图必须同 `--palette` 与 `--style`，由主控技能一次传入并写入清单；本引擎不做跨批自动协调。

- 书刊成套：`--palette sepia --style pencil`
- 推文套图：`--palette ochre --style brush`
- 汇报配图：`--palette terracotta --style fountain`
- 节庆主题：`--palette rosewood --style brush`

## 四、四种接入场景

| 接入方 | 取用方式 | 消费字段 |
|---|---|---|
| 书刊排版 | 批量出图 + 落位清单 | `file` / `role` |
| 公众号推文 | 单张或成套出图 | `file`（头图与文内插图） |
| 演示文稿 | 按分节出图 | `file`（可分节换配色但同节内统一） |
| 报告与方案 | 按章节出图 | `file`（正文单栏，统一走 wide 比例更稳） |

## 五、库调用

```python
import sys
sys.path.insert(0, "scripts")
import lineart_engine as E

E.render("moon", out="moon.png", style="brush", palette="ochre",
         size=(760, 980), seed=2026, paper=True)

motifs = E.pick_motifs("长夜里的灯与远方", n=3, seed=2026)   # 关键词选题
roles = E.plan_roles(3)                                       # ['wide','inline','inline-end']
```

## 六、与排版技能的对接样例

书刊排版技能可按下述两步串联（命令以各技能实际脚本名为准）：

```bash
# 第一步：出图，得 auto_images.json
python3 scripts/lineart_cli.py --manifest <清单>.json --per-article 3 \
    --outdir images/auto --palette sepia --style pencil -o auto_images.json

# 第二步：排版引擎消费 auto_images.json，把图按 role 插入正文
python3 <排版技能>/scripts/book_builder.py --manifest <清单>.json \
    --auto-images auto_images.json --part body
```

## 七、引擎的两种取用形态

- **命令行**：适合主控技能以 subprocess 调起，路径无关、返回码清晰；
- **库**：适合需要在同一进程内循环出图、或按需定制母题的场景。

两条路径共用 `lineart_engine.py`，行为一致。
