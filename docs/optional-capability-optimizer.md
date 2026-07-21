# Optional cross-client capability optimizer

The repository remains Markdown-first and zero-install. The optional
[`optimize-agent-capabilities`](../integrations/optimize-agent-capabilities/SKILL.md) Skill adds a
repeatable audit entry for users who maintain several coding-agent clients.

## Why the optimizer uses adapters

Agent Skills are portable as instructions, but capability discovery and invocation controls are
client-specific. A model may understand the intent of an unfamiliar Skill and still be unable to
prove that a guessed config key is valid. The optimizer therefore separates:

1. Shared policy: L0-L4 routing, need gates, status classes, permissions, rollback, and verification.
2. Client profiles: discovery paths, rules files, explicit invocation mechanisms, and support level.
3. Future adapters: separately reviewed, deterministic configuration changes for one verified client.

Unknown clients use the generic profile. They can read the goal and adapter contract, inventory
their environment, and propose a native implementation. They must not mutate configuration until
their client mechanism is documented and the user explicitly approves the diff.

## Initial support

| Client | Level | Behavior |
| --- | --- | --- |
| Codex | `audit-only` | Discover native Skill locations and report the documented invocation control. |
| Claude Code | `audit-only` | Discover native Skill locations and report the documented invocation control. |
| Kimi Code | `audit-only` | Account for merged Kimi, Claude, Codex, and generic Skill roots. |
| Other agents | `unknown` | Inspect generic Agent Skills and produce an adapter plan without config writes. |

The profile format is intentionally small. This contribution performs no configuration writes.
OpenCode, Pi, Warp, and future agents should begin as `audit-only` or `unknown`; any promotion to
`managed` belongs in a separate PR after all adapter operations are tested.

## Run

```bash
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

Install or explicitly invoke the Skill only when a repeatable command is useful. The original
Markdown workflow remains the source of truth.

Official references used for the initial profiles:

- Codex Skills and configuration: <https://learn.chatgpt.com/docs/build-skills>
- Claude Code Skills: <https://code.claude.com/docs/en/skills>
- Kimi Code Agent Skills: <https://moonshotai.github.io/kimi-code/en/customization/skills.html>

## 中文

本仓库仍以 Markdown-first、零安装为默认路线。可选的
[`optimize-agent-capabilities`](../integrations/optimize-agent-capabilities/SKILL.md) Skill 只为需要维护多个
coding-agent 客户端的用户提供可重复审计入口。

### 为什么使用 adapter

Agent Skills 的指令格式可以通用，但能力发现目录、Plugin 结构、显式调用和配置控制都由客户端决定。
模型看得懂目标，不代表它猜出的配置键就是安全的。因此优化器拆成三部分：

1. 通用规则：L0-L4 路由、Need Gate、状态分类、权限、回滚和验收。
2. 客户端 profile：发现路径、规则文件、显式调用机制和支持级别。
3. future adapter：单独审查，只负责一个经过验证的客户端，执行确定性的配置修改。

未知客户端使用 `generic-agent` profile。它可以理解目标、盘点本机并提出原生适配方案，但在机制未经
官方文档和本机测试确认前，不得修改配置。

### 首版支持

| 客户端 | 级别 | 行为 |
| --- | --- | --- |
| Codex | `audit-only` | 识别原生 Skill 路径并报告官方调用控制，不自动改配置。 |
| Claude Code | `audit-only` | 识别原生 Skill 路径并报告官方调用控制，不自动改配置。 |
| Kimi Code | `audit-only` | 处理 Kimi、Claude、Codex 和 generic Skill 根目录合并。 |
| 其他 Agent | `unknown` | 盘点通用 Agent Skills，只生成 adapter 方案。 |

本次贡献不执行任何配置写入。OpenCode、Pi、Warp 和未来客户端都先从 profile 开始；只有
`detect`、`inventory`、`plan`、`apply`、`verify` 全部有测试后，才在单独 PR 中讨论 `managed`。

```bash
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

只有确实需要固定触发入口时才安装或显式调用这个 Skill；原始 Markdown 工作流始终是唯一事实源。
