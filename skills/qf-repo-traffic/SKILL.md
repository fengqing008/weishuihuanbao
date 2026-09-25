---
name: "qf-repo-traffic"
description: "GitHub 仓库流量数据取数与趋势汇报，覆盖访问量、克隆量、Stars、Release 下载与引用来源。 触发场景：下载量统计、仓库流量、views、clones、stars查看、访问量汇报、仓库数据监控。"
version: "1.0.0"
license: "MIT"
category: "devops"
author: "清风明月"
---

# GitHub 流量取数

## 这个技能做什么

调取 GitHub 仓库的流量与互动数据，生成可读报告或 JSON 快照，支持与历史快照对比计算增量。用于跟踪已发布仓库的关注度变化。

## 什么时候用

用户提出「看看仓库有多少人访问」「下载量统计」「每天汇报一下数据」「仓库流量趋势」等问题时触发。

## 执行步骤

第一步，确认仓库清单。单个仓库用 `--repo`，多个仓库写入清单文件用 `--repos`。

第二步，准备 Token。需要 `repo` 权限（Classic Token）或仓库的 `Administration: Read` 权限（细粒度）；traffic 接口只对仓库有权限的账号开放。

第三步，取数。执行脚本，输出报告或 JSON。

第四步，对比增量。把上次的 JSON 快照传给 `--baseline`，即可看到变化量。

第五步，汇报。把关键指标整理成简洁结论，重点说增量而非绝对值。

## 用法

```bash
# 单仓库
GH_TOKEN=xxx python3 scripts/traffic_report.py --repo owner/name

# 多仓库（清单文件每行一个 owner/name）
GH_TOKEN=xxx python3 scripts/traffic_report.py --repos repos.txt

# 输出 JSON 快照 + 与上次对比
GH_TOKEN=xxx python3 scripts/traffic_report.py --repo owner/name \
    --json snapshot-$(date +%F).json --baseline snapshot-昨日期.json
```

## 可获取的指标

| 指标 | 接口 | 说明 |
|:---|:---|:---|
| views | `/traffic/views` | 仓库页面访问量，含每日明细 |
| clones | `/traffic/clones` | 仓库克隆量，含每日明细 |
| stars / forks / watchers | `/repos/{r}` | 当前累计值 |
| referrers | `/traffic/popular/referrers` | 流量来源站点 |
| popular_paths | `/traffic/popular/paths` | 最常访问的页面 |
| release 下载量 | `/releases` | Release 资源累计下载次数 |

## 关键限制（必须向用户说明）

1. **GitHub 不提供「技能文件下载次数」**。技能库不是 Release，无法统计单个文件被下载的次数。技能库场景下，`views` 与 `clones` 是仅有的可得流量数据。
2. **滚动 14 天窗口**。所有 traffic 数据只保留最近 14 天，更早数据无法补取。若要长期留档，必须**定期抓取并保存快照**。
3. **新仓库短期内必然为 0**。仓库创建当天或未做任何推广时，全部指标为 0 是正常现象，不代表接口异常。
4. **访问量为 0 通常意味着缺曝光**。此时应优先补 `description` 与 `topics` 提升检索命中，再到技术社区分享，而非反复取数。

## 长期留档建议

traffic 窗口只有 14 天，建议每日或每周执行一次并把 JSON 快照按日期存档：

```bash
mkdir -p snapshots
GH_TOKEN=xxx python3 scripts/traffic_report.py --repo owner/name \
    --json "snapshots/$(date +%F).json" --quiet
```

存档后可自行汇总为趋势表，突破 14 天限制。

## 输出格式

1. **终端报告**：仓库概览、views 明细、clones 明细、Release 下载、引用来源、热门页面。
2. **JSON 快照**：结构化数据，便于入库与增量对比。
3. **汇报结论**：建议用「本期增量 + 累计值 + 异常说明」三段式，避免只报绝对值。

## 边界与限制

- 报告只呈现数据，**不做流量归因的因果推断**。访问量上升可能来自搜索引擎、社区分享或爬虫，需结合 referrers 判断。
- 存量快照缺失时无法回溯历史，**首次使用即应开始留档**。
- 本技能不主动对外分享仓库，也不修改仓库设置。
