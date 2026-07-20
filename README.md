# Table-GitHub-Capability-Router / GitHub入库与能力路由表

English | [中文](#中文)

An Obsidian LLM Wiki + coding-agent workflow for GitHub project intake, capability cold storage, and agent routing.

**Positioning:** Prompt-triggered GitHub intake + capability routing for Obsidian/Codex/Claude Code｜发命令后由 Agent 自动入库 + 能力冷库与薄路由

This repository is a Markdown-first, prompt-triggered, agent-executed workflow. Give Codex, Claude Code, or another coding agent the repository URL or local Markdown files plus one command; the agent reads the SOP, performs the checks, creates the requested records, and writes meaningful results back to your vault.

No Skill or Plugin installation is required. This is not a standalone CLI or background service, and it does not change agent configuration by itself. All work happens inside the agent session and remains subject to your permission, confirmation, privacy, and rollback gates.

Use it when you want your AI assistant to stop leaving GitHub repos, prompts, tools, and project notes scattered across temporary context, and start maintaining them as a reusable personal knowledge workbench.

**Companion videos (中文):** [Part 1 · Why you shouldn't install every "must-have" AI tool](https://www.youtube.com/watch?v=c4d23apzOEY) · [Part 2 · The capability cold-vault workflow behind this repo](https://www.youtube.com/watch?v=juIsuIy55mQ)

## Design Principle: Own the First Routing Layer

Coding agents can discover capabilities from exposed skill / plugin / MCP metadata. Broad descriptions can win ambiguous routing; when a client truncates exposed text to fit its budget, restrictions placed at the end can disappear. This kit lets you put a thin router you own in front of that discovery layer:

```text
The default mechanism lays every tool out on the table and lets the agent pick.
A thin router hands the agent the thinnest possible map
and opens one drawer at a time.
```

The repository does not override native discovery on its own. Persistent routing starts only after you add a short rule to your `AGENTS.md`, `CLAUDE.md`, or equivalent guidance file that points the agent to your generated Level-1 router.

This kit is not a skill storage box — it is routing-power governance: deciding what the agent sees by default, when, how much, and who qualifies for the first layer. Exact loading and truncation behavior varies by client and version. [Codex officially documents](https://developers.openai.com/codex/concepts/customization) metadata-first Skill discovery and progressive disclosure; [Claude Code documents](https://code.claude.com/docs/en/context-window) its own startup-context and compaction behavior. The mechanism, official sources, cross-client inferences, and local-measurement boundaries are separated in [What Your Agent Actually Sees](docs/context-and-routing.md).

## What It Solves

- After you trigger it, guides the coding agent to turn GitHub links, READMEs, or saved repos into structured project cards, candidate/rejection records, capability-slot updates, and maintenance logs.
- Screens existing Skills, Plugins, MCP servers, scripts, and CLIs into an inventory/cold-storage system instead of letting every tool compete for context.
- Lets you place a user-controlled layered router (thin router -> registry rows -> capability card -> capability itself) in front of native discovery once it is wired into agent guidance, so the agent reads the minimum instead of scanning the whole library.
- Keeps every exposed routing entry truncation-safe: purpose and restrictions up front, so budget cuts cannot silently delete the "do not use for..." half.
- Flags manager-type capabilities (startup-wide triggers, session-start hook injections) that grab the first routing layer, and governs them unbundled instead of allowing whole packages by name.
- Distills reusable ideas from retained projects into existing workflow, concept, or project pages instead of creating duplicate project summaries.
- Reduces context size and token cost by keeping full clones, runtimes, raw logs, and large tool details outside the hot Obsidian layer.
- Avoids tool noise and unstable triggering by separating `active`, `cold`, `disabled`, and `reference` assets, then routing through need gates and preflight checks.
- Writes useful conclusions back to the vault, so the next agent session can reuse them.

## How It Works

GitHub project intake:

```text
Raw input or GitHub URL
-> Inbox note
-> Agent reads the workflow rules
-> 30-second positioning
-> current capability and duplicate check
-> evidence-based project card
-> capability-slot comparison
-> reusable knowledge distilled into a workflow, concept, or project page
-> optional cold-storage manifest
-> index and maintenance-log update
```

The split is intentional:

| Page | Main question |
| --- | --- |
| Project card | Why is this source worth keeping, testing, or rejecting? |
| Distillation page | What reusable method, checklist, prompt, or architecture did we extract from it? |
| Reference manifest | How can an agent safely rediscover and read the minimum useful reference later? |
| Thin registry | Can this task directly route to an executable capability now? |

Existing capability intake:

```text
Existing Skill / Plugin / MCP / script / CLI
-> inventory or manual capture
-> source, scope, permission, and duplicate check
-> status, health, and risk classification
-> cold-storage manifest or reference note
-> thin registry decision
-> index and maintenance-log update
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
-> Recycle temporarily enabled capabilities back to their pre-task state
```

Routing is layered so the agent never scans the whole library:

```text
Rules files (always visible, kept thin)
-> Level-1 thin router: task categories, truncation-safe one-liners
-> Level-2 registry rows: triggers and do-not-use conditions
-> Level-3 capability card: full detail of one capability
-> Level-4 the capability itself: loaded only when enabled
```

See [How It Works](docs/how-it-works.md) for the full bilingual explanation, and [What Your Agent Actually Sees](docs/context-and-routing.md) for why the router is layered this way.

## Quick Start

### Fastest path: give the Markdown to your agent

No installation is required. Give your agent this repository URL or a local copy and send:

```text
Read this repository's README, docs/context-and-routing.md, docs/how-it-works.md,
templates/capability-router.md, and templates/capability-manifest.md.
Using those rules, inspect my current agent environment and create a first-pass
capability ledger, Level-1 thin router, and capability manifests in <OUTPUT_DIR>.
Do not modify any existing configuration. Ask before installation, login,
external publishing, deletion, or configuration changes.
```

This is the zero-install route and the repository's primary promise: the Markdown is the workflow. A Skill or Plugin may provide a convenient trigger later, but it must not become a second source of truth.

### Persistent setup

1. Copy the template files into your own Obsidian vault.
2. Replace placeholder paths:
   - `{{VAULT_PATH}}`
   - `{{EXTERNAL_REPO_ROOT}}`
   - `{{CAPABILITY_LIBRARY}}`
   - `{{TEST_LOG_DIR}}`
3. Choose your own goals and scoring weights in [Customization Guide](docs/customization.md).
4. Put raw notes in your inbox folder.
5. Ask your agent to read the rules and process one GitHub project using the project-card template.
6. If the project produces a reusable idea, update an existing workflow, concept, or project page. Create a new distillation page only when it introduces a genuinely new method.
7. For existing tools, ask your agent to screen installed Skills, Plugins, MCP servers, scripts, or CLIs into capability manifests before adding them to the active registry.
8. Build your thin router from `templates/capability-router.md`: define under ten task categories, keep every exposed entry truncation-safe, and point your agent rules at the router instead of full-library scans.

Add one short routing rule to `AGENTS.md`, `CLAUDE.md`, or your client's equivalent guidance file:

```text
When a task may need an extra Skill, Plugin, MCP server, CLI, or script,
read {{CAPABILITY_LIBRARY}}/router/level1-router.md first.
Read only the matching category and the Top-1 capability card; never scan the whole library.
Ask before installation, login, external publishing, deletion, or configuration changes.
```

Example first prompt:

```text
Open {{VAULT_PATH}}. Read the vault rules, the project-intake workflow, and the GitHub project-card template.
Evaluate this GitHub project in lightweight mode. Do not clone or install anything.
Create or update the project card, update the relevant workflow/concept/project page if reusable knowledge should be distilled, update the relevant index, and append a short maintenance-log entry.
Project URL: <paste URL here>
```

Existing capability prompt:

```text
Open {{VAULT_PATH}}. Read the capability cold-storage workflow, the capability manifest template, and the registry rules.
Screen this existing capability without enabling new permissions or changing global config.
Record source, scope, permissions, health, risk, duplicate group, activation method, rollback path, and whether it should be active, cold, disabled, reference, or retired.
Capability: <paste tool/skill/plugin/MCP/script name or path here>
```

## What You Should Customize

The defaults are examples, not universal truth.

- Goals: learning, building, productivity, content, career, research, teaching, business, or something else.
- Weights: adjust the score weights to match your life and current stage.
- Evidence gates: decide when a project can move from candidate to retained.
- Capability slots: rename the verbs and outputs to fit your work.
- Distillation pages: decide whether reusable knowledge should live under workflows, concepts, or a specific project.
- Risk rules: tighten or relax what counts as high-risk.
- Paths: keep cloned repos, raw logs, and runtime files outside the Obsidian vault.
- Language: use English, Chinese, or bilingual pages.

## Privacy First

This section is for people who copy, fork, or adapt this template and want to publish their own version. It does not give anyone permission to push to this repository. Only the repository owner and explicitly added collaborators can publish changes here.

Do not publish your real vault directly. Publish a sanitized starter kit or a demo vault.

The command below is a pre-publish safety check for your own copy. It searches for common private paths, tokens, cookies, passwords, emails, phone labels, and Chinese ID/phone/email keywords. If it finds a hit, read the line and decide whether it is a real secret, a private path, or just an example inside the documentation.

Before pushing, run a local scan like:

```powershell
rg -n "C:\\Users|D:\\|API[_ -]?KEY|TOKEN|COOKIE|SECRET|Bearer|password|email|phone|身份证|手机号|邮箱" .
```

See [Privacy and Sanitization](docs/privacy-and-sanitization.md).

## Included Files

- `LICENSE`: MIT license.
- `docs/context-and-routing.md`: first principles — what the agent actually sees, truncation, routing power, manager-type capabilities.
- `docs/how-it-works.md`: the end-to-end workflow.
- `docs/customization.md`: what users should modify.
- `docs/privacy-and-sanitization.md`: what not to publish.
- `templates/capability-router.md`: thin router template (Level-1 categories + Level-2 registry rows + writing rules).
- `templates/github-project-card.md`: project evaluation template.
- `templates/capability-manifest.md`: cold-storage capability manifest template.
- `prompts/github-intake-prompt.md`: copy-paste prompts for intake, capability screening, and always-visible layer audits.

## License

MIT. You can use, modify, and redistribute this starter kit. If you adapt it for your own work, replace the goals, scoring weights, paths, and privacy rules with your own.

## 中文

这是一个基于 Obsidian LLM Wiki + coding agent 的 AI 知识库工作流模板，用来把 GitHub 项目自动入库、Agent 能力冷库和能力调用路由整理成一个可维护、可验证、可复用的工作台。

**定位：** Prompt-triggered GitHub intake + capability routing for Obsidian/Codex/Claude Code｜发命令后由 Agent 自动入库 + 能力冷库与薄路由

这是一套 Markdown-first、命令触发、由 Agent 执行的自动化工作流。把仓库链接或本地 Markdown 加一句命令交给 Codex、Claude Code 等 coding agent，它会读取 SOP、完成检查、生成所需记录，并把有长期价值的结果写回知识库。

这条路线不要求安装 Skill 或 Plugin。它不是独立 CLI 或后台服务，也不会自己修改 Agent 配置；所有工作都发生在 Agent 会话里，并继续受权限、确认、隐私和回滚门禁约束。

当你不想再让 GitHub repo、提示词、工具和项目笔记散落在临时上下文里，而是希望 AI 助手把它们维护成一个可复用的个人知识工作台时，可以使用这套模板。

**配套视频：** [上集 · 你收藏的 GitHub 神器，真的值得装吗](https://www.youtube.com/watch?v=c4d23apzOEY) · [下集 · 这个仓库背后的 Agent 能力冷库工作流](https://www.youtube.com/watch?v=juIsuIy55mQ)

## 设计原则：自己掌握第一层路由

coding agent 可以通过暴露的 Skill / Plugin / MCP metadata 发现能力。描述过宽时可能抢到模糊任务入口；客户端为控制预算裁剪暴露文本时，放在末尾的限制可能丢失。这套模板让你可以在原生发现层前面放一张自己掌握的薄路由：

```text
默认机制是把所有工具摆在桌上，让 Agent 自己挑；
薄路由是先给 Agent 一张极薄的地图，一次只开一个抽屉。
```

仓库本身不会自动覆盖原生发现层。只有当你在 `AGENTS.md`、`CLAUDE.md` 或对应客户端的持久规则里加一条短指令，让 Agent 先读生成后的一级路由表，长期路由才真正接通。

这套模板不是 Skill 收纳箱，而是路由权治理：决定 Agent 默认看见什么、什么时候看见、看见多少，以及谁有资格进入第一层。不同客户端和版本的加载、截断行为并不完全相同：[Codex 官方文档](https://developers.openai.com/codex/concepts/customization)确认 Skill 采用 metadata 优先与渐进加载，[Claude Code 官方文档](https://code.claude.com/docs/en/context-window)则公开了自己的启动上下文和压缩行为。机制、官方来源、跨客户端推断和本机实测边界统一见 [Agent 实际看到什么](docs/context-and-routing.md)。

## 它解决什么问题

- 用户触发后，引导 coding agent 把 GitHub URL、README 或收藏项目自动整理成结构化项目卡、候选/否决记录、能力槽更新和维护日志。
- 把已有 Skill、Plugin、MCP、脚本、CLI 先筛查入库，而不是让所有工具都挤进上下文里互相抢触发。
- 在写入 Agent 持久规则后，用用户掌握的分层路由（薄路由 -> Registry 行 -> 能力卡 -> 能力本体）接管第一层能力选择，让 Agent 每次只读最小必要信息，不扫描整库。
- 所有暴露给 Agent 的路由入口保持截断安全：用途和限制前置，预算裁剪不会悄悄删掉"不要用于……"那一半。
- 识别并标记总管型能力（启动型宽触发、SessionStart Hook 注入这类抢占第一层路由的能力），拆包治理，不因包名放行整包。
- 把正式保留项目里的可复用方法提炼进已有工作流页、概念页或具体项目页，而不是重复写一份项目介绍。
- 通过薄 Registry 和冷库 manifest 减少上下文占用和 token 消耗；完整 clone、运行时、原始日志和大段工具细节留在热层之外。
- 通过 `active`、`cold`、`disabled`、`reference` 分层，以及 Need Gate / Preflight，减少工具噪声、误触发和调用不稳定。
- 把有价值的结论写回 vault，下次 Agent 会话可以继续复用。

## 它怎么运作

GitHub 项目自动入库：

```text
原始资料或 GitHub URL
-> 收件箱笔记
-> Agent 读取工作流规则
-> 30 秒定位
-> 现有能力与重复关系筛查
-> 基于证据创建项目卡
-> 对比能力槽和现有方案
-> 把可复用知识提炼进工作流页、概念页或项目页
-> 必要时创建冷库 manifest
-> 更新索引和维护日志
```

这里的分工是刻意拆开的：

| 页面 | 主要回答 |
| --- | --- |
| 项目卡 | 这个来源为什么值得保留、测试或否决？ |
| 提炼页 | 从它里面抽出了什么可复用方法、清单、提示词或架构？ |
| reference manifest | Agent 以后怎么安全找到它，并只读取最小必要参考？ |
| 薄 Registry | 当前任务现在能不能直接路由到某个可执行能力？ |

已有能力筛查入库：

```text
已有 Skill / Plugin / MCP / 脚本 / CLI
-> 盘点或手动捕获
-> 来源、作用域、权限和重复组检查
-> 管理状态、健康状态和风险分级
-> 创建冷库 manifest 或 reference 笔记
-> 判断是否进入薄 Registry
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
-> Recycle：把临时启用的能力恢复到任务前状态
```

路由是分层的，Agent 从不扫描整库：

```text
规则文件（常驻可见，保持薄）
-> 一级薄路由：任务分类，每项截断安全的一句话
-> 二级 Registry 行：触发与禁用条件
-> 三级能力卡：单个能力的完整说明
-> 四级能力本体：启用时才进入上下文
```

完整说明见 [How It Works](docs/how-it-works.md)；为什么这样分层，见 [Agent 实际看到什么](docs/context-and-routing.md)。

## 快速开始

### 最快路线：直接把 Markdown 给 Agent

不需要安装。把本仓库链接或本地副本交给 Agent，再发送：

```text
请阅读本仓库的 README、docs/context-and-routing.md、docs/how-it-works.md、
templates/capability-router.md 和 templates/capability-manifest.md。
按这些规则盘点我当前的 Agent 环境，把第一版能力账本、一级薄路由和能力卡
全部写到 <输出目录>。不要修改任何现有配置；涉及安装、登录、外发、删除、
改配置时先停下来问我。
```

这是零安装路线，也是本仓库的主要承诺：Markdown 本身就是工作流。以后可以用 Skill / Plugin 提供更方便的触发入口，但不能让它们变成第二份方法事实源。

### 长期使用

1. 把模板文件复制到你自己的 Obsidian vault。
2. 替换占位符路径：
   - `{{VAULT_PATH}}`
   - `{{EXTERNAL_REPO_ROOT}}`
   - `{{CAPABILITY_LIBRARY}}`
   - `{{TEST_LOG_DIR}}`
3. 在 [Customization Guide](docs/customization.md) 中设置你自己的目标和权重。
4. 把原始资料放进收件箱。
5. 让 Agent 读取规则，并按项目卡模板处理一个 GitHub 项目。
6. 如果项目产出可复用方法，优先更新已有工作流页、概念页或项目页。只有真的形成新方法时，才新建提炼页。
7. 对已有工具，让 Agent 先把已安装或已保存的 Skill、Plugin、MCP、脚本、CLI 筛查成能力 manifest，再决定是否进入 active Registry。
8. 用 `templates/capability-router.md` 搭你的薄路由：定义十个以内的任务分类，所有暴露条目保持截断安全，并把 Agent 规则指向薄路由，不做整库扫描。

在 `AGENTS.md`、`CLAUDE.md` 或对应客户端的持久规则里增加一条短路由：

```text
任务可能需要额外 Skill、Plugin、MCP、CLI 或脚本时，先读
{{CAPABILITY_LIBRARY}}/router/level1-router.md。
只读取命中类别和 Top-1 能力卡，不扫描整库；涉及安装、登录、外发、删除、
改配置时先停下来确认。
```

第一条提示词示例：

```text
打开 {{VAULT_PATH}}。先阅读 vault 规则、项目入库流程和 GitHub 项目卡模板。
请对这个 GitHub 项目做轻量评估。不要 clone，不要安装，不要运行脚本。
创建或更新项目卡；如果有可复用知识，更新相关工作流页、概念页或项目页；更新相关索引，并追加一条维护日志。
项目 URL：<粘贴 URL>
```

已有能力筛查提示词示例：

```text
打开 {{VAULT_PATH}}。先阅读能力冷库流程、能力 manifest 模板和 Registry 规则。
请筛查这个已有能力，不要启用新权限，不要修改全局配置。
记录来源、作用域、权限、健康状态、风险、重复组、激活方式、回滚方式，以及它应该是 active、cold、disabled、reference 还是 retired。
能力名称或路径：<粘贴 Skill / Plugin / MCP / 脚本 / CLI 名称或路径>
```

## 哪些地方应该按自己情况修改

这里的默认值只是示例，不是通用标准。

- 目标：学习、构建项目、提效、内容、求职、研究、教学、商业，都可以换。
- 权重：评分权重必须按你自己的阶段调整。
- 证据门槛：自己决定什么情况下项目可以从候选进入正式保留。
- 能力槽：按你的工作重命名“动词 + 对象 + 产物”。
- 提炼页：决定可复用知识应该进入工作流、概念，还是某个具体项目页。
- 风险规则：按自己的权限边界调整高风险定义。
- 路径：完整 clone、原始日志和运行时不要放进 Obsidian vault。
- 语言：可以中文、英文或中英双语。

## 隐私优先

这一节是给“复制、fork 或改造这个模板，并准备发布自己版本的人”看的。它不是授权别人往这个仓库发布内容。只有仓库 owner 和被明确添加的 collaborator 才能 push 到这里。

不要直接公开自己的真实 vault。公开前应该抽象成 starter kit 或 demo vault。

下面这条命令只是你发布自己版本前的保险检查：它会搜索常见私人路径、Token、Cookie、密码、邮箱、手机号标签，以及“身份证/手机号/邮箱”等中文关键词。命中后不要紧张，逐条看它是真隐私、私人路径，还是文档里的示例。

推送前建议运行：

```powershell
rg -n "C:\\Users|D:\\|API[_ -]?KEY|TOKEN|COOKIE|SECRET|Bearer|password|email|phone|身份证|手机号|邮箱" .
```

详细检查见 [Privacy and Sanitization](docs/privacy-and-sanitization.md)。

## 包含文件

- `LICENSE`：MIT 许可证。
- `docs/context-and-routing.md`：第一性原理——Agent 实际看到什么、截断机制、路由权、总管型能力。
- `docs/how-it-works.md`：端到端工作流说明。
- `docs/customization.md`：哪些地方应该自行修改。
- `docs/privacy-and-sanitization.md`：哪些内容不要公开。
- `templates/capability-router.md`：薄路由模板（一级分类 + 二级 Registry 行 + 写作规则）。
- `templates/github-project-card.md`：项目评价模板。
- `templates/capability-manifest.md`：能力冷库 manifest 模板。
- `prompts/github-intake-prompt.md`：入库、能力筛查与常驻层体检提示词。

## 许可证

MIT。你可以使用、修改和重新发布这套 starter kit。如果你把它改成自己的工作流，请替换目标、评分权重、路径和隐私规则。
