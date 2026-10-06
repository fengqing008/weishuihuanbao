# 案例库（CASE LIBRARY）

> 本案例库为 agent-reach（互联网内容获取路由器）的实战复盘。
> 检索结果为示意结构，实际条目以命令真实返回为准【待核】。

## 案例一 · 全网调研多平台组合（L3）

- **背景**：用户提出「帮我调研一下某地污水厂 PPP 项目近期动态，顺便看看小红书和雪球上怎么讨论」。
- **做法**：拆为三路子任务（新闻检索 / 小红书讨论 / 雪球行情讨论）；先 `agent-reach doctor --json` 体检；按路由表读 `search.md`、`social.md`、`finance.md` 取命令；并行执行 Exa 搜索 + `opencli xiaohongshu search` + 雪球查询。
- **结果**：按「新闻 / 小红书讨论 / 雪球讨论」三组输出标题+来源+链接+时间；收尾跑 `agent-reach check-update` 附版本提示。来源：`references/search.md`、`references/social.md`、`references/finance.md`。

## 案例二 · 后端未激活的降级处理

- **背景**：`doctor` 对某平台（小红书）返回 `active_backend: null`，看似不可用。
- **做法**：判定为「后端未激活」失败模式——`null` 仅表示 Doctor 未做实时验证（避免读浏览器 Cookie），不代表后端不存在；按 `references/social.md` 的只读命令手动验证 OpenCLI 路径。
- **结果**：以实际非空内容确认可用并完成检索。教训：**不要**把 `null` 直接当「平台不可用」；**不可**未验证就宣称失败。

## 案例三 · 登录态缺失的合规回退

- **背景**：Reddit/Twitter 命令报鉴权错误，无零配置路径。
- **做法**：按红线不自动登录、不读浏览器 Cookie；回退为引导用户用 Cookie-Editor 手工导出后配置 `xiaohongshu-mcp` / `rdt` 等；Twitter 需在子进程显式提供 `TWITTER_AUTH_TOKEN` 与 `TWITTER_CT0`，且不在日志回显中暴露值。
- **结果**：用户在获得登录态后完成检索。红线提醒：Cookie/Token **不可**明文暴露，**严禁**绕过登录。

## 案例四 · 平台无可用后端时的兜底

- **背景**：目标平台在当前环境无 OpenCLI/CLI 适配器。
- **做法**：判定为「平台无可用后端」失败模式，先按零配置通道（Exa/Jina/GitHub/V2EX/bili）获取近似内容，同时**如实告知**用户该平台当前不可用；不静默换源冒充。
- **结果**：用户拿到近似内容并清楚知道缺口。教训：失败须写清重试链，**不编造**、**不补写**平台没有的字段。

> 使用建议：常规调研照案例一；`null` 后端照案例二；登录态照案例三；无后端照案例四。
