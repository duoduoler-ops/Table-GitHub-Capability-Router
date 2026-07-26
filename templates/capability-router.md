# Capability Router / 能力路由表（一级薄路由 + 二级索引）

> Why this file exists: the agent should never scan your whole capability library. It reads this thin router first (Level 1), then only the matching registry rows (Level 2), then one capability card (Level 3). See [What Your Agent Actually Sees](../docs/context-and-routing.md).
>
> 这个文件的作用：Agent 不扫描全量能力库，先读这张薄路由（L1），再只读命中的 Registry 行（L2），最后只读一张能力卡（L3）。原理见 [Agent 实际看到什么](../docs/context-and-routing.md)。

GitHub project references belong in the separate generated `indexes/project-semantic-routing.md`. They are read-only suggestions, never executable capability rows. A project match keeps `no-extra-project` as an alternative and cannot authorize clone, installation, login, script execution, configuration changes, or publishing.

GitHub 项目参考进入单独生成的 `indexes/project-semantic-routing.md`，只提供只读建议，不能写进可执行能力 Registry。项目命中始终保留 `no-extra-project`，也不能授权 clone、安装、登录、运行脚本、改配置或发布。

## Writing rules / 写作规则

- Level-1 entries: one line each, purpose first, roughly 30-50 characters. Must make sense standing alone. / 一级条目一行一项，用途先行，约 30-50 字，单独成立。
- Level-2 rows: trigger AND do-not-use conditions within roughly 80-120 characters, restrictions never at the end. / 二级行在约 80-120 字内写清触发和禁用条件，限制不放末尾。
- Card summaries: "Only for ..." first, "Do not use for ..." second, both in the first two lines. / 能力卡摘要先写"仅用于"，再写"不要用于"，都放前两行。
- One entry serves one task type. No "also useful for..." phrasing. / 一条入口只服务一个任务类型，不写"也可以用于"。
- When registry rows change, update the Level-1 candidate lists in the same edit. / Registry 行变化时，同一次编辑里同步一级路由的候选列。
- "Use no extra tool" is always a legitimate route. / "不调用额外工具"永远是合法路由。

## Level 0: Native visibility policy / L0 客户端原生可见性策略

The thin router guides the agent's decision, but it does not hide native Skills, Plugins, MCP tools, or Hooks by itself. Record client-specific visibility and invocation controls separately. Disabling a capability, changing implicit invocation, editing Hooks, or changing client configuration requires explicit user approval.

薄路由负责引导 Agent 决策，但本身不会隐藏客户端原生的 Skill、Plugin、MCP 工具或 Hook。客户端可见性和调用策略要单独记录；禁用能力、改变隐式调用、修改 Hook 或客户端配置，都必须先获得用户明确批准。

## Level 1: Thin router / 一级薄路由

Replace the example rows with your own task categories. Keep this table under roughly 10 rows.
把示例行换成你自己的任务分类，整表控制在 10 行左右。

| Task type / 任务类型 | One-line boundary / 一句话边界 | Candidates / 候选行 |
| --- | --- | --- |
| Answer directly / 直接作答 | Given info is enough; complete without any tool / 已给信息足够就直接完成，不加任何工具 | baseline-direct |
| Public web lookup / 联网查公开信息 | Public pages and official docs; never logged-in data / 查公开网页与官方文档，不碰登录态 | your-web-search |
| Document delivery / 文档交付 | Read and produce Word / PDF / spreadsheets / 读写并交付 Word、PDF、表格 | your-docs-tool |
| Local search / 本地检索 | Search local text and version history / 本地文本搜索与版本历史 | your-cli-search |
| External writes / 外部写入 | Create PRs, issues, posts; gated, confirm before executing / 创建 PR、Issue、发布内容；有门禁，执行前确认 | your-github-tool |

If no row matches: consider `baseline-direct` first; only then query the full catalog. Never scan the whole library.
一级路由未命中时：先考虑 `baseline-direct`；确有缺口再查全量 Catalog，不扫描整库。

## Level 2: Thin registry rows / 二级索引（薄 Registry 行）

One row per routable capability. Keep the whole table small (a few dozen rows at most). Suggested columns:
每个可路由能力一行，整表保持薄（最多几十行）。建议字段：

| Field / 字段 | Content / 内容 |
| --- | --- |
| ID | Stable identifier, referenced by Level 1 / 稳定标识，被一级路由引用 |
| Capability slot / 能力槽 | verb + object + output / 动词 + 对象 + 产物 |
| Type & platform / 类型与平台 | Skill / Plugin / MCP / CLI / Script; which client / 所属客户端 |
| Deploy & health / 部署与健康 | installed / configured; healthy / unverified / degraded / broken / missing |
| Invocation / 调用策略 | auto / conditional / explicit-only / disabled |
| Authorization / 授权级别 | ordinary record / lifecycle update / routing proposal / configuration change / 普通记录、生命周期更新、路由提案、配置修改 |
| Trigger + do-not-use / 触发与禁用 | Truncation-safe: purpose and restrictions up front / 截断安全：用途和限制前置 |
| Risk & fallback / 风险与回退 | low / medium / high; what to fall back to / 回退到什么 |
| Card link / 详情卡 | Link to the capability manifest / 指向能力 manifest |

Example row / 示例行：

```text
ID: your-yt-dlp
Slot: download public videos and keep subtitle metadata
Type: CLI / shared
Deploy & health: installed / healthy (verified 2026-06-22)
Invocation: explicit-only
Trigger + do-not-use: Only for public, owned, or licensed content the user names.
  Do not use for restricted resources or anything requiring cookies.
Risk & fallback: medium; fall back to browser download
Card: manifests/your-yt-dlp.md
```

## Level 3: Capability card summary / 能力卡摘要格式

The full card lives in the [Capability Manifest](capability-manifest.md). Its first two lines must be:
完整卡片用 [能力 Manifest 模板](capability-manifest.md)。前两行必须是：

```text
Only for: <one task type, concrete trigger scenarios>
Do not use for: <exclusion scenarios, stated plainly, no trailing conditionals>

仅用于：<一个任务类型 + 具体触发场景>
不要用于：<排除场景，直白陈述，不用末尾转折>
```

## Manager-type capabilities / 总管型能力标记

If a capability matches any of these, mark it `manager-type` in its registry row and require an explicit allowlist decision (see [context-and-routing.md](../docs/context-and-routing.md#6-manager-type-capabilities-recognizing-routing-power-grabs)):

- startup-wide trigger descriptions ("use when starting any conversation");
- rewrites the agent's default flow;
- pushes the agent to invoke more of its own family;
- injects content via session-start hooks.

命中任一特征就在 Registry 行标 `manager-type`，并要求显式 allowlist 决策（识别标准见 [context-and-routing.md](../docs/context-and-routing.md#6-总管型能力识别路由权抢占)）：启动型宽触发、改默认流程、自我强化、SessionStart Hook 注入。

Governance: propose only the smallest verified sub-capability, never the whole package because of its name. Promotion into Registry/L1 or automatic invocation requires explicit human approval.
治理原则：只提议放行已验证的最小子能力，绝不因包名放行整包；进入 Registry/L1 或自动调用前必须获得人工明确批准。

## Recycle / 任务后回收

After a task that temporarily enabled anything, return it to its pre-task state (cold / disabled / explicit-only). Content already loaded in the current session cannot be unloaded; start a new session when you need a clean state.

任务里临时启用过的能力，任务结束后恢复到任务前状态（cold / disabled / 仅显式调用）。已进入当前会话的内容收不回来，需要干净状态就开新会话。

## Always-visible budget / 常驻层预算

Everything that actually stays visible in every session (rules files, active Skill descriptions, hook injections, and any MCP instructions or schemas the client loads up front) shares one budget. Some clients defer MCP tool definitions, so measure the real startup context instead of assuming every schema is always resident. Review it periodically with clean new-session measurements; do not let it grow silently.

所有实际在每次会话常驻可见的内容（规则文件、active Skill 描述、Hook 注入，以及客户端启动时直接加载的 MCP instructions/schema）共享一份预算。部分客户端会延迟加载 MCP 工具定义，因此必须测真实启动上下文，不能默认所有 schema 都常驻。定期用干净新会话实测复查，不让它悄悄膨胀。
