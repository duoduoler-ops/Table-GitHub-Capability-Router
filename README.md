# Table-GitHub-Capability-Router

Give an Agent one repository link. Get a versioned GitHub intake vault, capability cold storage, semantic project references, and a thin routing layer that can be validated and rebuilt.

把一个仓库链接交给 Agent，建立一套可版本化、可校验、可重建的 GitHub 项目入库、能力冷库、项目语义参考和薄路由系统。

[中文说明](README.zh-CN.md) | [English](README.en.md) | [5 分钟开始](QUICKSTART.zh-CN.md) | [Agent 唯一入口](AGENT-START.md)

## Current verified hosts / 当前验证宿主

The current maintained path is **Grok Build + Codex**. Both clients use the repo-scoped Skill at `.agents/skills/github-vault-router/`. Claude Code remains supported through the compatibility copy at `.claude/skills/github-vault-router/`; it is no longer the current default host.

当前维护主线是 **Grok Build + Codex**。两者共用 `.agents/skills/github-vault-router/` 项目级 Skill；Claude Code 仍通过 `.claude/skills/github-vault-router/` 保留兼容支持，但不再是当前默认宿主。

`AGENTS.md` is the single canonical rules file. Root `CLAUDE.md` is intentionally kept as a minimal compatibility pointer: a local check with Grok Build 1.0.0 found that Grok still loaded this root file even when Claude compatibility import was disabled, so it must point to `AGENTS.md` rather than duplicate policy.

## Copy this to your Agent / 复制给 Agent

```text
请用这个工作流仓库帮我建立“GitHub 项目入库 + 能力冷库 + 自动路由”：
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

先只读仓库根目录的 AGENT-START.md，按其中门禁执行。
把产物建立在一个新的隔离目录；使用本机已有 Python，不安装依赖。
初始化、生成第一条候选记录并校验；安装、登录、外发、删除、修改客户端配置前必须先问我。
```

需要本地执行时，Agent 可以把公开源码 clone 到隔离目录。clone 不等于安装；不得自动安装 Python 或第三方依赖。若缺少输出路径，只询问这一项。

## What is automated / 自动化到哪里

| Layer | Automated | Human gate |
| --- | --- | --- |
| Bootstrap | Directory structure, rules pointer, config, indexes, router, log | Choose output path |
| GitHub intake | Canonical URL, stable ID, deduplication, candidate card, derived views | Evidence judgment and retained/reference promotion |
| Semantic project references | Generated thin discovery + full semantic table, eligibility, duplicate and drift checks | Confirm the project deserves retained/reference status |
| Capability cold storage | Manifest, explicit deployment scope, health/state rules, route eligibility, automatic quarantine | Install, removal, enablement, active/auto promotion, client config |
| Write safety | Lock, transaction manifest, before backup, atomic replace, rollback, validation | Removing unknown locks or deleting data |
| Agent routing | Shared Grok Build/Codex repo Skill, Claude Code compatibility Skill, and generated L1/L2 router | Persistent wiring into another project or global config |

Canonical project and capability records are the source of truth. Indexes, the thin discovery + full semantic project-reference table, and the capability router are generated artifacts. The optional capability audit is read-only and does not create a second routing policy.

项目卡和能力记录是事实源；索引、薄发现 + 完整语义命中表和能力路由表是脚本生成的派生产物。可选能力审计保持只读，不构成第二套路由规则。

## Release focus / 每次更新重点

Every release adds one concise focus row here; implementation details stay in [CHANGELOG.md](CHANGELOG.md).
每次发布都在这里补一行重点；完整实现细节统一写入 [CHANGELOG.md](CHANGELOG.md)。

| Version | Focus | User-visible change |
| --- | --- | --- |
| v0.4.0 | Judge B-grade task increment, then settle first real use / 先判断 B 级任务增量，再结算首次真实使用 | Schema v3 separates grade from deployment scope; low-risk executable candidates use T0, approved project scope, and the current project's first real task as T1 / Schema v3 拆开等级与部署范围；低风险可执行候选经过 T0 和项目级批准后，当前项目第一次真实任务就是 T1 |
| v0.3.0 | Discover saved GitHub capabilities before deciding they are irrelevant / 先发现，再判断是否使用 | Substantive tasks must check a generated thin table; `gated` projects can be mentioned before runtime approval, while reading, installation, and execution remain gated / 实质任务先查薄表；`gated` 项目可先提醒，但读取、安装和执行仍受门禁约束 |
| v0.2.0 | Deterministic intake and semantic references / 确定性入库与语义参考 | Added schema-driven records, CLI rebuild/validation, transactions, and one full semantic routing table / 增加 Schema 事实源、CLI 重建校验、事务写回和完整语义表 |
| v0.1.0 | Publish-safe Markdown starter / 可公开的 Markdown 起步模板 | Established bilingual templates, intake prompts, and a sanitized example / 建立双语模板、入库提示词和脱敏示例 |

## What's new in v0.4.0 / v0.4.0 新增内容

- Grade, deployment scope, management state, health, and invocation are separate schema v3 fields or axes. A does not mean global installation.
- Method-only B projects remain reference and are not installed.
- Low-risk executable B candidates get T0, then explicit approval for `project` scope; the current project's first real task is T1.
- T1 pass settles to A/retained + active/project. Failure or an inconclusive result stays B/reference and recommends uninstall; deletion still requires confirmation.
- `migrate-v3` requires an explicit deployment scope for every capability; `capability-deployment` records facts but never installs or removes files.
- Grok Build and Codex share the repo-scoped `.agents/skills/github-vault-router/` Skill; Claude Code retains a compatibility copy.
- No durable `project-trial` state is introduced. Isolation is reserved for elevated permissions, real credentials, external writes, background services, heavy caches, unclear source/license/rollback, or no project-level installation path.

- 等级、部署范围、管理状态、健康和调用方式在 schema v3 中分别记录；A 不代表全局安装。
- B 级只有方法价值时维持 reference，不安装。
- 低风险可执行候选先做 T0，再询问是否按 `project` 范围安装；当前项目第一次真实任务就是 T1。
- T1 通过结算为 A/retained + active/project；失败或结论不清则保持 B/reference 并建议卸载，真正删除仍需确认。
- `migrate-v3` 要求为每项能力明确部署范围；`capability-deployment` 只登记事实，不执行安装或卸载。
- Grok Build 与 Codex 共用 `.agents/skills/github-vault-router/` 项目 Skill；Claude Code 保留兼容副本。
- 不新增长期 `project-trial` 状态；只有高权限、真实凭据、外部写入、后台服务、重缓存、来源/License/回滚不清或无项目级安装方式时才要求隔离。

## What's new in v0.3.0 / v0.3.0 新增内容

| New in v0.3.0 | What it changes |
| --- | --- |
| Mandatory thin discovery gate | Every substantive task checks one compact capability-summary table before the Agent may conclude that no saved project is relevant |
| Thin discovery + full semantic details | The same generated file supports cheap Top-1 discovery first and detailed positive/negative routing only after a match |
| Remind-first `gated` semantics | `high_confidence` and `gated` may both be mentioned; `gated` controls later reading or execution, not discovery |
| Schema v2 capability summaries | Every eligible project has one distinct verb + object + output summary; exact duplicates fail validation |
| Transactional `migrate-v2` | Upgrades v0.2 workflow roots only after the user supplies summaries for retained/reference projects, then rebuilds and validates atomically |
| Three-route reminder | Keeps `no-extra-project`, offers minimum Markdown reading after the user chooses, and asks before installation or enablement only when runtime is required |

## What's new in v0.2.0 / v0.2.0 新增内容

| New in v0.2.0 | What it changes |
| --- | --- |
| Deterministic, dependency-free Python CLI | Initializes, updates, transitions, rebuilds, validates, and rolls back workflow data |
| Schema-driven canonical records | Prevents IDs, URLs, approval state, and generated views from drifting apart |
| Semantic project-reference routing | Lets everyday user wording suggest one relevant retained/reference GitHub project while keeping the no-extra-project option |
| Positive and negative routing evidence | Requires at least two ordinary-language examples plus explicit do-not-route conditions |
| Automatic consistency checks + optional pre-commit gate | Catches missing, duplicate, ineligible, and stale semantic routing records before release or, when explicitly enabled, before commit |
| Shared Grok Build/Codex Skill and Claude Code compatibility Skill | Shares the workflow rules while preserving client-specific configuration |
| Optional read-only capability audit | Preserves PR #1's cross-client inventory for Codex, Claude Code, Kimi Code, and generic agents |
| Transactional writes and validation | Adds locking, backups, atomic replacement, rollback, repository validation, and history privacy scans |

> Historical note / 历史说明：v0.2.0 introduced `high_confidence`, `gated`, and explicit-only routing evidence. v0.3.0 changed discovery so `gated` projects may be mentioned first while later reading or execution remains gated. v0.4.0 keeps that behavior and adds B-grade first-use settlement. / v0.2.0 引入了 `high_confidence`、`gated` 和仅点名路由证据；v0.3.0 已改为 `gated` 项目可先提醒，后续读取或执行仍受门禁约束。v0.4.0 保留该行为，并增加 B 级首次真实使用结算。

## Deterministic core / 确定性核心

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language zh-CN --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

Existing schema v1/v2 roots use `migrate-v3`. Every capability needs an explicit `CAPABILITY_ID=SCOPE` mapping; direct v1 migration also needs one `PROJECT_ID=SUMMARY` for every retained/reference project. See the [v0.3 to v0.4 migration](docs/migrations/v0.3-to-v0.4.md).

No third-party Python package is required. The same GitHub URL always resolves to the same `gh-owner-repo` record.

零第三方 Python 依赖。同一个 GitHub 地址始终命中同一条 `gh-owner-repo` 记录。

## Optional read-only capability audit / 可选只读能力审计

PR #1 added an independent, audit-only inventory entry. It now covers Grok Build alongside the existing Codex, Claude Code, Kimi Code, and generic-agent profiles. It discovers capability roots and client support boundaries but never installs, enables, disables, or rewrites configuration.

PR #1 增加了独立的只读能力盘点入口。当前已在原有 Codex、Claude Code、Kimi Code 和通用 Agent profile 基础上加入 Grok Build；它只发现能力目录和客户端支持边界，不安装、不启停，也不改写配置。

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

See [Optional capability optimizer](docs/optional-capability-optimizer.md). Thanks to [@Calvingen3](https://github.com/Calvingen3) for the initial contribution.

## Proof / 可验证证据

Unreleased reliability changes add base-hash draft protection, protected rollback, actual-index pre-commit checks, and Windows/Linux CI. Existing body-update callers must add `--expected-sha256`; schema stays v3. See [write protocol](docs/write-protocol.md), [hook and CI](docs/optional-pre-commit.md), and [changelog](CHANGELOG.md). CI results must be verified from an actual GitHub run.

未发布的可靠性更新包含旧稿 hash 拦截、回滚保护、真实暂存区检查和 Windows/Linux CI。旧的正文更新调用须补 `--expected-sha256`，Schema 保持 v3；CI 是否通过以 GitHub 实际运行结果为准。

- [Generated demo](examples/generated-demo-v1/README.md) / 真实生成的公开脱敏演示
- [State machine](docs/state-machine.md) / 状态机
- [Deterministic write protocol](docs/write-protocol.md) / 确定性写回协议
- [Grok Build client profile](docs/client-profiles/grok-build.md) / Grok Build 客户端接入边界
- [Generic client profile](docs/client-profiles/generic-agent.md) / 通用客户端接入边界
- [Optional capability audit](docs/optional-capability-optimizer.md) / 可选能力审计
- [Optional pre-commit gate](docs/optional-pre-commit.md) / 可选提交前门禁
- `python -m unittest discover -s tests -v`
- `node --test integrations/optimize-agent-capabilities/tests/audit.test.mjs`
- `python scripts/workflow.py validate-repo`

## Safety boundary / 安全边界

This is strong workflow automation, not an unattended service. Target repository content is untrusted evidence, never an instruction to execute. The workflow never installs, logs in, publishes, deletes, or changes client configuration without explicit approval.

这是一套强工作流自动化，不是无人值守服务。目标仓库内容只是不可信证据，不能变成执行指令。未经明确批准，本工作流不会安装、登录、外发、删除或修改客户端配置。

`active`, `retained/reference`, deployment-scope changes, and automatic invocation are approval-gated. Manager-type capabilities cannot use automatic invocation in schema v3. An unhealthy active capability is automatically quarantined and removed from the generated capability router. Discovery remains a read-only reminder and never authorizes repository reading, clone, installation, login, unknown script execution, configuration changes, or publishing.

## Learn more / 更多资料

- [English guide](README.en.md)
- [中文说明](README.zh-CN.md)
- [5 分钟快速开始](QUICKSTART.zh-CN.md)
- [Privacy and sanitization](docs/privacy-and-sanitization.md)
- [Migrate v0.1.0 to v0.2.0](docs/migrations/v0.1-to-v0.2.md)
- [Migrate v0.2.0 to v0.3.0](docs/migrations/v0.2-to-v0.3.md)
- [Migrate v0.3.0 to v0.4.0](docs/migrations/v0.3-to-v0.4.md)
- [上集 · 你收藏的 GitHub 神器，真的值得装吗](https://www.youtube.com/watch?v=c4d23apzOEY)
- [下集 · 这个仓库背后的 Agent 能力冷库工作流](https://www.youtube.com/watch?v=juIsuIy55mQ)
- [进阶篇 · Advanced guide](https://www.youtube.com/watch?v=k7S5ewLaMVI&t=16s)

MIT licensed. See [SECURITY.md](SECURITY.md) before adapting the kit for a public vault.
