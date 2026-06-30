# Privacy and Sanitization / 隐私与脱敏

English | [中文](#中文)

Do not publish your real working vault directly. Publish a cleaned starter kit, a demo vault, or selected templates.

## Never Publish

- API keys, tokens, cookies, OAuth files, private SSH keys.
- `.env`, `.env.*`, `.mcp.json`, `settings.local.json`.
- Local agent config folders such as `.claude/`, `.codex/`, `.cursor/`.
- Raw command logs.
- Full cloned repositories that belong outside the vault.
- Personal resumes, job applications, real interview notes, or private project plans.
- Screenshots that reveal account names, emails, private file paths, or browser sessions.
- Obsidian workspace files that reveal private filenames or reading history.

## Usually Replace

| Private value | Public replacement |
| --- | --- |
| real user path | `{{VAULT_PATH}}` |
| local clone directory | `{{EXTERNAL_REPO_ROOT}}` |
| real test log path | `{{TEST_LOG_DIR}}` |
| real capability library | `{{CAPABILITY_LIBRARY}}` |
| real email | `you@example.com` |
| real project name | `sample-project` |
| real health status | `example: healthy / unverified` |

## Suggested Scan

Run this before pushing:

```powershell
rg -n --hidden -i "C:\\Users|D:\\|API[_ -]?KEY|TOKEN|COOKIE|SECRET|Bearer|password|private key|BEGIN OPENSSH|BEGIN RSA|email|phone|身份证|手机号|邮箱" .
```

Also inspect file names:

```powershell
Get-ChildItem -Recurse -Force | Select-Object FullName
```

## Public Repo Review Checklist

Before you make a repository public, check:

- Does it contain local agent config?
- Does it contain `.env` or `.local` files?
- Does it contain private paths?
- Does it contain personal names, emails, phone numbers, or location details?
- Does it contain generated logs or ZIP packages?
- Does it contain dependency folders such as `node_modules`?
- Does GitHub Pages expose a live website you forgot about?
- Does commit history contain removed secrets?

If a secret was ever committed, deleting the file in a later commit is not enough. Rotate the secret and rewrite history only after you understand the impact.

## 中文

不要直接公开真实工作 vault。应该发布清洗后的 starter kit、demo vault 或精选模板。

## 绝对不要公开

- API Key、Token、Cookie、OAuth 文件、私有 SSH Key；
- `.env`、`.env.*`、`.mcp.json`、`settings.local.json`；
- `.claude/`、`.codex/`、`.cursor/` 等本地 Agent 配置目录；
- 原始命令日志；
- 本应放在 vault 外部的完整 clone 仓库；
- 简历、投递记录、真实面试笔记、私人项目计划；
- 暴露账号、邮箱、私有路径或浏览器会话的截图；
- 会暴露私有文件名和阅读历史的 Obsidian workspace 文件。

## 通常需要替换

| 私人信息 | 公开替代 |
| --- | --- |
| 真实用户路径 | `{{VAULT_PATH}}` |
| 本地 clone 目录 | `{{EXTERNAL_REPO_ROOT}}` |
| 真实测试日志路径 | `{{TEST_LOG_DIR}}` |
| 真实能力库目录 | `{{CAPABILITY_LIBRARY}}` |
| 真实邮箱 | `you@example.com` |
| 真实项目名 | `sample-project` |
| 真实健康状态 | `example: healthy / unverified` |

## 建议扫描

推送前运行：

```powershell
rg -n --hidden -i "C:\\Users|D:\\|API[_ -]?KEY|TOKEN|COOKIE|SECRET|Bearer|password|private key|BEGIN OPENSSH|BEGIN RSA|email|phone|身份证|手机号|邮箱" .
```

同时检查文件名：

```powershell
Get-ChildItem -Recurse -Force | Select-Object FullName
```

## 公开仓库检查清单

把仓库设为 public 前，先检查：

- 是否包含本地 Agent 配置？
- 是否包含 `.env` 或 `.local` 文件？
- 是否包含私人路径？
- 是否包含姓名、邮箱、手机号、位置等个人信息？
- 是否包含生成日志或 ZIP 包？
- 是否包含 `node_modules` 等依赖目录？
- 是否有 GitHub Pages 正在公开展示你忘记的网站？
- commit 历史里是否曾经出现过已删除的 secret？

如果 secret 曾经提交过，后续删除文件并不够。应该先轮换 secret，再谨慎处理历史。

