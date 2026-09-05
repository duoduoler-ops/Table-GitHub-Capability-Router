# Table-GitHub-Capability-Router

这套工具帮你整理收藏的 GitHub 项目，让 Agent 做任务时能找到合适的工具，并查到它们之前的使用结果。

从收集链接、评估项目，到按需安装或留作参考，再到记录检查和使用结果，都有对应的流程。项目资料用 Markdown 保存，脚本负责去重、写入、检查和更新索引。这里的“能力”包括 Skill、Plugin、MCP、CLI、脚本，也包括值得参考的方法。

Organize saved GitHub projects so your Agent can find useful tools and review how they worked before.

[中文说明](README.zh-CN.md) | [English](README.en.md) | [5 分钟开始](QUICKSTART.zh-CN.md) | [Agent 入口](AGENT-START.md)

## Current verified hosts / 当前验证宿主

当前主要维护 **Grok Build 和 Codex**，两者共用 `.agents/skills/github-vault-router/` 项目 Skill。Claude Code 保留 `.claude/skills/github-vault-router/` 兼容入口。

规则正文统一放在 `AGENTS.md`，`CLAUDE.md` 只指向它，方便维护时只改一处。客户端能否发现和调用某项能力，要以当次会话实际提供的工具为准。Hook 是否启用和触发，也需要单独验证。

## Copy this to your Agent / 复制给 Agent

```text
请用这个仓库帮我建立“GitHub 项目入库 + 能力冷库 + 自动路由”：
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

先只读仓库根目录的 AGENT-START.md，按其中流程执行。
把产物放在一个新的独立目录；使用本机已有 Python，不安装依赖。
初始化工作流，生成第一条候选项目记录，再运行校验。
安装、登录、对外发布、删除、修改客户端配置前，必须先问我。
```

Agent 需要在本地执行时，可以把这份工作流源码 clone 到独立目录。若你没有指定产物位置，它会先询问输出路径。核心流程只需要已有的 Python 3，无须安装第三方 Python 包。

## What is automated / 自动化到哪里

| 环节 | 脚本负责什么 | 仍由你和 Agent 决定什么 |
| --- | --- | --- |
| 初始化 | 建目录、配置、索引、路由和维护日志 | 产物放在哪里 |
| 项目入库 | 整理 GitHub 地址、去重、生成候选项目卡 | 证据是否可信，项目是否值得保留 |
| 按任务找项目 | 从正式记录生成简短能力表和详细使用条件，供 Agent 查找 | 最多推荐一个相关项目，也可以直接用现有工具完成 |
| 能力冷库 | 记录安装范围、健康情况和管理状态，按规则更新路由 | 是否安装、启用、卸载或允许自动调用 |
| 检查与使用记录 | 保存检查报告、使用前后记录，核对旧证据是否还适用 | 实际执行检查、验收结果并完成后续处置 |
| 写入保护 | 写入前加锁和备份，拦截旧稿覆盖，失败时尝试恢复 | 并发冲突或中断后如何恢复 |
| 提交检查 | 可选 Git Hook 检查暂存内容；GitHub CI 在 Windows 和 Linux 上验证 | 是否启用本地 Hook、是否合并或发布 |
| 未完成事项提醒 | 可选客户端 Hook 检查已登记但未完成的使用记录 | 是否接入 Hook，以及如何处理待办 |

项目卡和能力记录是主要资料；索引、项目推荐表和路由由脚本生成，可以重建。启用可选使用记录后，相应的证据和回执也由专用命令维护。改资料时走对应命令，避免手工改生成表后被下次重建覆盖。

## Release focus / 每次更新重点

两批新增功能已合并到 `main`，尚未包含在 **v0.4.0 Release** 中。要使用新增命令，请获取当前主分支源码。完整变更见 [CHANGELOG.md](CHANGELOG.md)。

| 版本 | 重点 | 用起来有什么变化 |
| --- | --- | --- |
| 当前 main，待发布新版本 | 写入保护、使用证据和可选 Hook | 旧草稿不能直接覆盖新内容；可追踪每次使用、发现证据过期或文件变化，并检查未完成事项 |
| v0.4.0 | 分开记录项目等级和安装范围 | B 级项目先判断是否有帮助；获批后在当前项目中验证，完成真实任务后再决定是否保留 |
| v0.3.0 | 先查已有项目，再决定怎么做 | Agent 先看简短能力表，找到相关项目后再看具体条件 |
| v0.2.0 | 用脚本稳定维护资料 | 增加入库、重建、校验、写入备份和按任务找项目的规则 |
| v0.1.0 | 提供可复制的起步模板 | 双语模板、入库提示词和公开示例 |

## What's new in v0.4.0 / v0.4.0 新增内容

- 项目值不值得用、装在哪里、是否启用、最近是否正常、怎样调用，分别记录。评为 A 级也可以只装在一个项目里。
- B 级项目如果只有方法参考价值，就保留资料供阅读。如果有低风险、可执行的帮助，先做初步检查（T0），获得项目级安装批准后，用当前项目的第一次真实任务验证（T1）。
- T1 通过后，按审批流程登记为 A/retained 和 active/project；失败或结论不清时保持 B/reference，并提出卸载建议。实际卸载仍要确认。
- `migrate-v3` 要求明确每项能力的安装范围。`capability-deployment` 只登记已经发生的安装或部署事实。
- Grok Build 和 Codex 共用项目 Skill，Claude Code 保留兼容入口。
- 不增加长期挂着的 `project-trial` 状态；涉及高权限、真实凭据、外部写入或难以回退等情况时，先隔离验证。具体条件见 [Agent 入口](AGENT-START.md)。

## What's new in v0.3.0 / v0.3.0 新增内容

| 新增内容 | 解决什么问题 |
| --- | --- |
| 先查简短能力表 | 做具体任务前，先看看库里有没有相关项目，减少“收藏了却想不起来用” |
| 简表和详细表分开 | 先找最相关的一项，再读它适用和不适用的情况 |
| `gated` 项目可以先提醒 | 可以先告诉你有这个项目，后续读取、安装和执行再按权限处理 |
| 每项能力有独立摘要 | 用一句“做什么、得到什么”区分项目，重复摘要会被校验拦截 |
| 迁移时补齐摘要 | 当时通过 `migrate-v2` 升级旧资料；当前版本统一使用 `migrate-v3` |
| 保留直接完成的选项 | 可以用现有工具直接做，也可以只读项目资料，确需运行时再决定是否安装 |

## What's new in v0.2.0 / v0.2.0 新增内容

| 新增内容 | 解决什么问题 |
| --- | --- |
| 无第三方依赖的 Python 命令 | 入库、更新、重建和校验有统一做法 |
| 固定的记录格式 | 项目 ID、地址、状态和批准信息可以相互核对 |
| 按任务找参考项目 | 用户用日常话描述需求，也能找到相关的已保留项目 |
| 适用示例和排除条件 | 同时说明什么时候推荐、什么时候不该推荐 |
| 一致性校验和可选提交检查 | 找出遗漏、重复、不该入表的项目和过期生成表 |
| 客户端接入入口 | 工作流规则集中管理，保留客户端各自的调用方式 |
| 可选只读能力盘点 | 查看客户端可见的能力和接入边界 |
| 写入备份与恢复 | 增加锁、备份、逐文件替换、失败恢复和历史隐私扫描 |

> 历史说明：v0.3.0 调整了 `gated` 的含义，允许先提醒项目存在；后续操作仍按权限处理。v0.4.0 延续这一做法，增加首次真实使用后的处理流程。

## Deterministic core / 确定性核心

下面三条命令会建立工作流、登记一个 GitHub 项目，再检查生成结果。先把占位符替换为实际路径和地址，在源码目录执行。

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language zh-CN --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

Windows 已装 Python 启动器时，可把 `python` 换成 `py -3`；macOS/Linux 可使用已有的 `python3`。同一个 GitHub 地址会对应同一条记录，重复入库不会再建一份。

已有 schema v1/v2 数据，按 [v0.3 → v0.4 迁移说明](docs/migrations/v0.3-to-v0.4.md) 使用 `migrate-v3`。已有 v3 数据无须迁移；更新源码后运行 `rebuild` 和 `validate`，刷新生成的指引即可。旧的正文更新脚本需要补上 `--expected-sha256`，用来确认草稿仍基于当前记录。

## Optional read-only capability audit / 可选只读能力审计

想先看看本机有哪些能力入口，可以使用独立的只读盘点工具。它覆盖 Grok Build、Codex、Claude Code、Kimi Code 和通用 Agent，查看能力目录与客户端支持情况，不修改客户端配置。

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

这项可选功能需要已有的 Node.js。盘点到文件或入口，不代表当前会话已经能调用。详见 [能力盘点说明](docs/optional-capability-optimizer.md)。感谢 [@Calvingen3](https://github.com/Calvingen3) 在 PR #1 中提供最初贡献。

## Optional evidence lifecycle / 可选证据闭环

新增的使用记录回答四个问题：**用的是哪个版本、在哪个项目里用、结果是否通过、后续事项是否处理完。** 旧记录里写过“健康”，不会被直接当作这次任务成功的证据。

| 命令 | 用来做什么 |
| --- | --- |
| `record-evidence` | 保存调用方已经完成的发现或轻量检查结果；命令本身不执行检查 |
| `use-begin` | 在已获批的实际使用前登记一次使用；相同请求重复登记不会产生第二条 |
| `use-finish` | 记录验收结果，以及临时安装、启用等后续事项是否已处理完 |
| `capability-check` | 只读检查旧证据是否仍适用于当前能力和项目 |
| `lifecycle-status` | 列出尚未完成的使用记录，方便中断后继续处理 |

证据会关联调用方提供并复核的客户端和能力版本、明确列出的文件及其实际哈希、所在项目和文件位置。检查时发现版本或所列文件变化、证据过期、后续失败记录，或仍有未完成使用，就会要求复核。默认有效期是 30 天；客户端和版本信息需要调用方先核实，再传给命令。

这仍然是一套记录和复核流程：实际检查由你或 Agent 执行并报告。轻量检查通过、真实任务验收通过、客户端当前确实能调用，要分别确认。记录成功不会自动升级项目等级、修改健康状态或启用工具。

**Hook 适合补上容易忘的提醒。** 本批提供 Codex 和 Grok Build 的可选示例，只检查已登记的未完成使用：

| 客户端 | 开始或结束时的行为 |
| --- | --- |
| Codex | 开始会话时可把待办放入上下文；结束时可显示界面提醒 |
| Grok Build | 默认只保存本地待办文件；显式选用 `--grok-feedback` 后，结束时可请求一次继续处理，会增加模型用量 |

示例不会随初始化自动安装。适配器和输入样例已有测试，真实客户端中的启用、信任与事件触发仍需接入后验证。Hook 看不到从未登记的使用，也不自动测试、卸载或结算。Git 提交前 Hook 则负责检查提交内容，作用不同。

现有 Vault 仍用 schema v3，新增证据和回执使用独立的 version 1 格式。启用这些记录后，请使用新版 CLI。详见 [使用说明与完整命令](docs/capability-lifecycle.md)、[虚构演示](examples/lifecycle-demo.py)和 [Hook 接入说明](docs/optional-lifecycle-hooks.md)。

## Proof / 可验证证据

第一批更新主要减少误写和漏检：

- **防止旧稿覆盖新内容**：先用 `record-hash` 保存原记录哈希，再带 `--expected-sha256` 写回草稿。原记录变过，就先合并新内容。
- **恢复时保留别人的修改**：失败恢复只处理仍属于本次写入的内容；遇到并发改动或备份异常，会留下恢复记录。
- **检查真正要提交的文件**：可选 pre-commit Hook 读取 Git 暂存区，未暂存的修复不能掩盖错误提交。
- **两种系统持续验证**：GitHub CI 对主分支推送和 PR 执行 Python 测试、Node 盘点测试、演示、入门流程和仓库检查。

[自动生成演示](examples/generated-demo-v1/README.md)包含 2 个虚构项目、3 个虚构能力及其索引、路由和写入记录。[使用记录演示](examples/lifecycle-demo.py)另行展示成功、文件变化、失败和中断。它们不代表真实工具已经安装或通过验收。

```powershell
python -m unittest discover -s tests -v
node --test integrations/optimize-agent-capabilities/tests/audit.test.mjs
python scripts/workflow.py validate --root examples/generated-demo-v1
python scripts/workflow.py validate-repo
python scripts/workflow.py validate-staged --root .
```

运行结果以 [GitHub Actions](https://github.com/duoduoler-ops/Table-GitHub-Capability-Router/actions) 中对应提交为准。检查范围和限制见 [写回协议](docs/write-protocol.md)与 [提交前 Hook 和 CI](docs/optional-pre-commit.md)。

## Safety boundary / 安全边界

自动化负责维护记录和执行明确的检查，具体决策和实际工具操作由你与 Agent 按权限完成。安装、登录、对外发布、删除、修改客户端配置，都需要明确批准。被评估仓库的文字和代码只作为待核实资料，不能自行变成执行指令。

项目正式保留、能力启用、安装范围变更和自动调用都受审批规则约束。总管型能力不能设为自动调用。通过 `capability-health` 登记 active 能力健康降级后，系统会把该记录隔离并移出路由；这不会替你关闭客户端中的真实工具。

写入保护也有边界：强制结束进程或断电后，可能需要人工恢复。使用记录只保存必要字段和脱敏摘要；对外提交前仍要检查是否包含私人信息。

## Learn more / 更多资料

- [English guide](README.en.md)
- [中文说明](README.zh-CN.md)
- [5 分钟快速开始](QUICKSTART.zh-CN.md)
- [状态机](docs/state-machine.md)
- [Grok Build 接入说明](docs/client-profiles/grok-build.md)
- [通用客户端接入说明](docs/client-profiles/generic-agent.md)
- [隐私与脱敏](docs/privacy-and-sanitization.md)
- [v0.1 → v0.2 迁移](docs/migrations/v0.1-to-v0.2.md)
- [v0.2 → v0.3 迁移](docs/migrations/v0.2-to-v0.3.md)
- [v0.3 → v0.4 迁移](docs/migrations/v0.3-to-v0.4.md)
- [上集 · 你收藏的 GitHub 神器，真的值得装吗](https://www.youtube.com/watch?v=c4d23apzOEY)
- [下集 · 这个仓库背后的 Agent 能力冷库工作流](https://www.youtube.com/watch?v=juIsuIy55mQ)
- [进阶篇 · Advanced guide](https://www.youtube.com/watch?v=k7S5ewLaMVI&t=16s)

采用 [MIT License](LICENSE)。准备公开自己的资料库前，请阅读 [SECURITY.md](SECURITY.md)。
