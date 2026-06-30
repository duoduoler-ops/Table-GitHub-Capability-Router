# Table-GitHub-Capability-Router / GitHub入库与能力路由表

English | [中文](#中文)

An Obsidian + coding-agent workflow for GitHub project intake, capability cold storage, and agent routing.

**GitHub description:** GitHub intake + capability routing for Obsidian/Codex/Claude Code｜GitHub项目自动入库 + Agent能力冷库与调用路由

This repository is a Markdown-first starter kit. It does not ship an automation engine, and it does not ask you to install more tools by default. It gives you a small set of bilingual rules, templates, and prompts that help Codex, Claude Code, or another coding agent maintain your knowledge base with evidence, privacy boundaries, and clear update points.

Use it when you want your AI assistant to stop treating GitHub repos, prompts, tools, and project notes as scattered chat history, and start maintaining them as a reusable personal knowledge workbench.

## What It Solves

- GitHub projects stop becoming a random bookmark pile.
- Agent Skills, Plugins, MCP servers, scripts, and CLIs are tracked by status, health, risk, and rollback path.
- Obsidian becomes the readable control surface for decisions, not the place where large repos and raw logs are dumped.
- Important conclusions are written back to the vault, so the next agent session can reuse them.

## How It Works

```text
Raw input or GitHub URL
-> Inbox note
-> Agent reads the workflow rules
-> 30-second positioning
-> Evidence-based project card
-> Capability slot comparison
-> Optional cold-storage manifest
-> Index and maintenance log update
```

For executable capabilities:

```text
Need gate
-> Search 1-3 candidates, including "use no extra tool"
-> Describe the top candidate
-> Preflight health, permissions, risk, and rollback
-> Execute the smallest useful step
-> Verify the result
-> Write back only meaningful state changes
```

See [How It Works](docs/how-it-works.md) for the full bilingual explanation.

## Quick Start

1. Copy the template files into your own Obsidian vault.
2. Replace placeholder paths:
   - `{{VAULT_PATH}}`
   - `{{EXTERNAL_REPO_ROOT}}`
   - `{{CAPABILITY_LIBRARY}}`
   - `{{TEST_LOG_DIR}}`
3. Choose your own goals and scoring weights in [Customization Guide](docs/customization.md).
4. Put raw notes in your inbox folder.
5. Ask your agent to read the rules and process one GitHub project using the project-card template.

Example first prompt:

```text
Open {{VAULT_PATH}}. Read the vault rules, the project-intake workflow, and the GitHub project-card template.
Evaluate this GitHub project in lightweight mode. Do not clone or install anything.
Create or update the project card, update the relevant index, and append a short maintenance-log entry.
Project URL: <paste URL here>
```

## What You Should Customize

The defaults are examples, not universal truth.

- Goals: learning, building, productivity, content, career, research, teaching, business, or something else.
- Weights: adjust the score weights to match your life and current stage.
- Evidence gates: decide when a project can move from candidate to retained.
- Capability slots: rename the verbs and outputs to fit your work.
- Risk rules: tighten or relax what counts as high-risk.
- Paths: keep cloned repos, raw logs, and runtime files outside the Obsidian vault.
- Language: use English, Chinese, or bilingual pages.

## Privacy First

Do not publish your real vault directly. Publish a sanitized starter kit or a demo vault.

Before pushing, run a local scan like:

```powershell
rg -n "C:\\Users|D:\\|API[_ -]?KEY|TOKEN|COOKIE|SECRET|Bearer|password|email|phone|身份证|手机号|邮箱" .
```

See [Privacy and Sanitization](docs/privacy-and-sanitization.md).

## Included Files

- `LICENSE`: MIT license.
- `docs/how-it-works.md`: the end-to-end workflow.
- `docs/customization.md`: what users should modify.
- `docs/privacy-and-sanitization.md`: what not to publish.
- `templates/github-project-card.md`: project evaluation template.
- `templates/capability-manifest.md`: cold-storage capability manifest template.
- `prompts/github-intake-prompt.md`: copy-paste prompt for agent-assisted intake.

## License

MIT. You can use, modify, and redistribute this starter kit. If you adapt it for your own work, replace the goals, scoring weights, paths, and privacy rules with your own.

## 中文

这是一个基于 Obsidian + coding agent 的 AI 知识库工作流模板，用来把 GitHub 项目自动入库、Agent 能力冷库和能力调用路由整理成一个可维护、可验证、可复用的工作台。

**GitHub 简介：** GitHub intake + capability routing for Obsidian/Codex/Claude Code｜GitHub项目自动入库 + Agent能力冷库与调用路由

这个仓库是 Markdown-first starter kit，不是自动化引擎，也不是让你默认安装更多工具。它提供一组中英双语规则、模板和提示词，让 Codex、Claude Code 或其他 coding agent 可以用更稳的方式维护你的知识库。

当你不想再让 GitHub repo、提示词、工具和项目笔记散落在聊天记录里，而是希望 AI 助手把它们维护成一个可复用的个人知识工作台时，可以使用这套模板。

## 它解决什么问题

- GitHub 项目不再变成随机收藏夹。
- Skill、Plugin、MCP、脚本、CLI 可以按状态、健康、风险和回滚方式管理。
- Obsidian 作为可阅读的控制面，而不是堆完整源码、运行时和原始日志的地方。
- 有价值的结论会写回 vault，下次 Agent 会话可以继续复用。

## 它怎么运作

```text
原始资料或 GitHub URL
-> 收件箱笔记
-> Agent 读取工作流规则
-> 30 秒定位
-> 基于证据创建项目卡
-> 对比能力槽和现有方案
-> 必要时创建冷库 manifest
-> 更新索引和维护日志
```

对于可执行能力：

```text
Need Gate：是否需要额外能力
-> Search：搜索 1-3 个候选，包括“不调用额外工具”
-> Describe：读取 Top-1 候选详情
-> Preflight：检查健康、权限、风险和回滚
-> Execute：执行最小有用步骤
-> Verify：验证结果
-> Write Back：只把有意义的状态变化写回
```

完整说明见 [How It Works](docs/how-it-works.md)。

## 快速开始

1. 把模板文件复制到你自己的 Obsidian vault。
2. 替换占位符路径：
   - `{{VAULT_PATH}}`
   - `{{EXTERNAL_REPO_ROOT}}`
   - `{{CAPABILITY_LIBRARY}}`
   - `{{TEST_LOG_DIR}}`
3. 在 [Customization Guide](docs/customization.md) 中设置你自己的目标和权重。
4. 把原始资料放进收件箱。
5. 让 Agent 读取规则，并按项目卡模板处理一个 GitHub 项目。

第一条提示词示例：

```text
打开 {{VAULT_PATH}}。先阅读 vault 规则、项目入库流程和 GitHub 项目卡模板。
请对这个 GitHub 项目做轻量评估。不要 clone，不要安装，不要运行脚本。
创建或更新项目卡，更新相关索引，并追加一条维护日志。
项目 URL：<粘贴 URL>
```

## 哪些地方应该按自己情况修改

这里的默认值只是示例，不是通用标准。

- 目标：学习、构建项目、提效、内容、求职、研究、教学、商业，都可以换。
- 权重：评分权重必须按你自己的阶段调整。
- 证据门槛：自己决定什么情况下项目可以从候选进入正式保留。
- 能力槽：按你的工作重命名“动词 + 对象 + 产物”。
- 风险规则：按自己的权限边界调整高风险定义。
- 路径：完整 clone、原始日志和运行时不要放进 Obsidian vault。
- 语言：可以中文、英文或中英双语。

## 隐私优先

不要直接公开自己的真实 vault。公开前应该抽象成 starter kit 或 demo vault。

推送前建议运行：

```powershell
rg -n "C:\\Users|D:\\|API[_ -]?KEY|TOKEN|COOKIE|SECRET|Bearer|password|email|phone|身份证|手机号|邮箱" .
```

详细检查见 [Privacy and Sanitization](docs/privacy-and-sanitization.md)。

## 包含文件

- `LICENSE`：MIT 许可证。
- `docs/how-it-works.md`：端到端工作流说明。
- `docs/customization.md`：哪些地方应该自行修改。
- `docs/privacy-and-sanitization.md`：哪些内容不要公开。
- `templates/github-project-card.md`：项目评价模板。
- `templates/capability-manifest.md`：能力冷库 manifest 模板。
- `prompts/github-intake-prompt.md`：Agent 辅助入库提示词。

## 许可证

MIT。你可以使用、修改和重新发布这套 starter kit。如果你把它改成自己的工作流，请替换目标、评分权重、路径和隐私规则。
