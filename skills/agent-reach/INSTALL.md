# Agent-Reach 技能本地安装说明

- 来源：https://github.com/Panniantong/Agent-Reach（71,614 Star，MIT 协议，2026-08-12 更新）
- 安装日期：2026-08-14
- 技能定位：给 AI Agent 装上"互联网眼睛"，15 平台多后端路由（小红书/推特/B站/Reddit/Facebook/Instagram/V2EX/LinkedIn/YouTube/GitHub/小宇宙/雪球/RSS/Exa 搜索等）
- 官方安装文档：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md

## 目录结构

```
agent-reach/
├── SKILL.md                  # 主技能文件（含 frontmatter，ima 平台兼容）
├── SKILL_en.md               # 英文版
├── references/               # 7 个分类详细文档（按需路由阅读）
│   ├── search.md             # Exa AI 搜索
│   ├── social.md             # 小红书/推特/B站/V2EX/Reddit/Facebook/Instagram
│   ├── career.md             # LinkedIn 职场招聘
│   ├── dev.md                # GitHub CLI
│   ├── web.md                # Jina Reader / RSS
│   ├── video.md              # YouTube/B站/小宇宙播客
│   └── finance.md            # 雪球股票行情
└── scripts/
    └── transcribe_xiaoyuzhou.sh  # 小宇宙播客转写脚本
```

## 沙箱依赖安装状态（2026-08-14）

| 工具 | 状态 | 说明 |
|------|------|------|
| agent-reach CLI | ✅ 已装 v0.1.0 | pip install agent-reach |
| yt-dlp | ✅ 已装 2026.07.04 | YouTube/B站字幕 |
| mcporter | ✅ 已装 0.9.0 | Exa 搜索 MCP 调用 |
| gh CLI | ❌ 不可用 | GitHub release 直连超时 + apt 源无包；可用 GitHub API 替代 |
| opencli / bili-cli / twitter-cli / rdt-cli | ❌ 未装 | 需登录态的渠道，按需安装 |

注意：沙箱每次会话重置，pip/npm 包需重新安装（agent-reach/yt-dlp/mcporter）。

## 常用命令速查

```bash
agent-reach doctor --json          # 渠道体检
agent-reach list --all             # 可用渠道列表
agent-reach install rss            # 安装渠道
mcporter call exa.web_search_exa query="关键词" numResults=5   # Exa 搜索
curl -s "https://r.jina.ai/URL"    # 网页阅读
yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"      # YouTube 字幕
bili search "关键词" --type video -n 5                          # B站搜索
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"  # V2EX
```

## 使用边界

- 本 skill 只负责从互联网获取内容，不负责写报告/数据分析/翻译等加工
- 不执行发帖/评论/点赞等写操作
- 需登录态平台（Twitter/Reddit/小红书/Facebook/Instagram）：不自动登录，需用户提供 Cookie 或复用现有浏览器会话
