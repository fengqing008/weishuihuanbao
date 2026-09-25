---
name: "qf-skill-publish"
description: "技能脱敏与发布到 GitHub 的全流程，含敏感词扫描、通用代称替换、元数据规范化、DNS 污染绕过与 Token 授权排障。 触发场景：技能脱敏、发布到GitHub、开源技能库、敏感信息清理、技能上传、仓库推送、DNS污染、Token 403。"
version: "1.0.0"
license: "MIT"
category: "devops"
author: "清风明月"
---

# 技能脱敏发布

## 这个技能做什么

把本地技能库（或任意文档集）经过**脱敏处理**后发布到 GitHub 公开仓库。覆盖从敏感信息扫描、通用代称替换、元数据规范化，到网络排障、授权配置、推送验证的完整链路。

适用对象：企业内部沉淀的业务技能、含真实客户名称的案例库、带内部标识的流程文档。

## 什么时候用

用户提出「把技能脱敏后发布到 GitHub」「开源我的技能库」「清理敏感信息后上传仓库」「推送到 GitHub 报 403」等问题时触发。

## 执行步骤

### 第一步：范围界定（必须先确认）

**关键判断**：区分「自研技能」与「平台内置 / 第三方技能」。

| 类型 | 识别特征 | 处理 |
|:---|:---|:---|
| 自研技能 | 自有命名前缀（如 `qf-*`）、`_meta.json` 含自己的 ownerId | ✅ 可发布 |
| 平台内置连接器 | `computer-use`、`figma-connector`、`github-connector` | ❌ 不发布 |
| 第三方官方技能 | 目录名为数字 ID（`skill_2053...`）、SKILL.md 含 `slug`/`display_name` | ❌ 版权存疑 |

必须向用户确认三件事：**发布范围、脱敏档位、仓库落地方式**。

### 第二步：敏感信息全量扫描

按以下维度逐项扫描，**先出报告再动手改**：

```bash
# 维度1：真实企业/项目/人名（按用户实际业务补充词表）
grep -rniE "企业名A|企业名B|项目地名" --include="*" . 

# 维度2：密钥凭证
grep -rniE "(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN.*PRIVATE KEY)" .

# 维度3：本地绝对路径/系统用户名
grep -rnoE "(/Users/[A-Za-z0-9._-]+|[A-Z]:\\\\Users\\\\[A-Za-z0-9._-]+)" .

# 维度4：内部平台域名
grep -rniE "(内部域名\.com|oa\.com)" .

# 维度5：内部知识库 ID
grep -rniE "kb_id=" .
```

### 第三步：通用代称替换（核心）

用脚本替换，**规则按字符串长度降序应用**——否则长串会被短串先吃掉。

```python
RULES = sorted([
    ("完整企业全称", "某水务项目公司"),      # 最长优先
    ("企业简称", "某环保上市公司"),
    ("项目地名", "某市"),
], key=lambda x: -len(x[0]))
```

代称命名建议：

| 原类型 | 代称 |
|:---|:---|
| 雇主企业 | 某环保上市公司 |
| 关联子公司 | 某水务集团 |
| 央国企联合体 | 某央企环境集团 |
| 项目地名 | 某市 / 某县 / 某区 |
| 本项目 | 示例项目A / 示例PPP |
| 招标编号 | 招标编号略 |

**必须做第二轮**：清理机械替换产生的重复修饰语（如「某市某水务集团」）。

### 第四步：元数据规范化

统一所有 SKILL.md 的 front-matter，字段顺序固定：

```yaml
---
name: "skill-name"
description: "一句话能力 + 触发场景关键词"
version: "1.0.0"
license: "MIT"
category: "environmental-engineering"
author: "笔名"
---
```

**常见坑**：
- 脚本重建 front-matter 时易产生**双重引号**（`description: ""内容""`）
- 多行 description 用块标量 `>-` 时易出现嵌套 `>-`
- 改完必须用 `yaml.safe_load()` 校验

### 第五步：五维复扫 + 语法校验

```bash
# 复扫
grep -rniE "残留词表" . || echo "✅ 无残留"
# Python 语法
for f in $(find . -name "*.py"); do python3 -m py_compile "$f" || echo "✗ $f"; done
# YAML 校验
python3 -c "import yaml,pathlib; [yaml.safe_load(open(p).read().split('---')[1]) for p in pathlib.Path('.').glob('*/SKILL.md')]"
```

### 第六步：网络排障（沙箱必踩）

**症状**：`gh auth status` 报 token invalid、`git push` 报 TLS 握手失败、`api.github.com` 返回 `EOF`。

**根因**：DNS 污染。`getent hosts github.com` 若返回 **`198.18.0.x`**（RFC 2544 保留网段），即为污染。

**突破方法**：从可达镜像取真实 IP，写入 hosts 绕过 DNS。

```bash
# 1. 取真实 IP（镜像站可达时）
curl -sS "https://gh-proxy.com/https://raw.githubusercontent.com/521xueweihan/GitHub520/main/hosts"
# 或实测可用 IP：api.github.com → 20.205.243.168、github.com → 140.82.113.3

# 2. 写入 hosts
echo "20.205.243.168 api.github.com" >> /etc/hosts
echo "140.82.113.3 github.com" >> /etc/hosts

# 3. 验证
curl -sS -m 10 -o /dev/null -w "%{http_code}\n" https://api.github.com/user
```

单次测试可用 `curl --resolve`：

```bash
curl --resolve "api.github.com:443:20.205.243.168" https://api.github.com/user
```

### 第七步：Token 授权排障

**必做诊断**（区分网络问题与权限问题）：

```bash
TOKEN="<token>"
# 身份验证
curl -sS -H "Authorization: Bearer $TOKEN" https://api.github.com/user
# 权限范围（Classic Token 会返回 x-oauth-scopes）
curl -sS -D - -o /dev/null -H "Authorization: Bearer $TOKEN" https://api.github.com/user | grep -i x-oauth-scopes
# 写权限实测
curl -sS -o /dev/null -w "%{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/git/blobs -d '{"content":"x","encoding":"utf-8"}'
```

**结果判读**：

| 现象 | 含义 | 对策 |
|:---|:---|:---|
| `HTTP:000` / `EOF` / TLS 错误 | 网络问题 | 走第六步 DNS 绕过 |
| 写接口 `403 Resource not accessible by personal access token` | 细粒度 Token 缺权限 | 重签 Token，勾 `Contents: Read and write` |
| 写接口 `409` | 权限正常（空仓库无父提交） | 直接推送 |
| `Permission to X.git denied to X` | Token 只读 | 换 Classic Token 勾 `repo` |

**关键坑**：细粒度 Token（`github_pat_` 开头）的权限在**签发时固化**，在网页上改权限对已签发的 Token **无效**，必须重新生成。Classic Token（`ghp_` 开头）勾 `repo` 一项即可覆盖全部子权限，更省事。

### 第八步：推送与验证

```bash
cd <repo>
git init -q
git branch -M main
git config user.name "<笔名>"
git config user.email "<笔名>@users.noreply.github.com"
git add -A && git commit -q -m "feat: 首次发布"
git remote add origin https://github.com/<user>/<repo>.git

# 推送（用 base64 编码的 Basic 认证头，避免密码交互）
TOKEN="<token>"
GIT_TERMINAL_PROMPT=0 git -c http.extraHeader="Authorization: Basic $(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)" \
  push -u origin main
```

**推送后必须核验**：

```bash
# commit hash 比对
L=$(git rev-parse HEAD)
R=$(git ls-remote origin refs/heads/main | awk '{print $1}')
[ "$L" = "$R" ] && echo "✅ 一致" || echo "⚠️ 不一致"

# 远端文件清单核验（走 API，避免触发下载）
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<user>/<repo>/git/trees/main?recursive=1" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('文件数:', len([x for x in d['tree'] if x['type']=='blob']))"
```

### 第九步：安全收尾（必须提醒）

**Token 一旦在对话中明文出现，必须提醒用户立即吊销**：https://github.com/settings/tokens

另外建议补设仓库元信息，便于检索：

```bash
gh api -X PATCH repos/<user>/<repo> \
  -f description="仓库描述" \
  -f homepage="" \
  -F 'topics[]=agent-skills' -F 'topics[]=ppp' -F 'topics[]=wastewater'
```

## 输出格式

1. **脱敏对照报告**（`DESENSITIZATION.md`）：脱敏范围、代称映射表、处理统计、复扫结果。
2. **发布仓库**：README（技能清单 + 触发场景表 + 免责声明）、LICENSE、脱敏后的技能目录。
3. **推送验证结果**：commit hash 一致性、远端文件数。
4. **安全提醒**：Token 吊销提示。

## 边界与限制

- 脱敏**无法保证 100% 不可反查**。案例的行业属性、时间线、技术参数组合仍可能被推断出项目。涉及核心商业秘密的内容，建议不发布。
- 代称替换后必须**人工复核语病**，机械替换易产生「某市某水务集团」类重复修饰。
- 法规标准引用、专业结论须提示以现行有效版本与实际材料为准。
- 本技能不代替用户做发布决策，发布范围与脱敏档位**必须由用户确认**。
