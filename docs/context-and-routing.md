# What Your Agent Actually Sees / Agent 实际看到什么

English | [中文](#中文)

This document explains the first principles behind the whole kit: how capabilities enter the model's context, how truncation happens, and why the real thing you are governing is **routing power** — who gets to stand in front of your agent by default.

If you only read one doc before customizing the templates, read this one.

## 1. What a single "hello" actually sends

When you type "hello" to a coding agent, the model does not receive two words. It receives a package. Depending on the client and version, the package typically includes:

1. The system prompt: identity, behavior rules, environment info.
2. Your rules files (project and user level, e.g. `CLAUDE.md` / `AGENTS.md`).
3. Injected memory.
4. The skill discovery layer: name + description of every visible skill.
5. Components contributed by plugins (skills, agents, hooks, MCP servers).
6. MCP: server instructions + tool names / descriptions / schemas (some clients defer-load these).
7. Whatever session-start hooks inject.
8. Finally, your message.

So every capability has **two costs**:

```text
Discovery cost: paid on every session, even when the capability is never used.
Invocation cost: paid when it triggers and its full content enters the session.
```

A large skill may cost a dozen tokens of metadata but tens of thousands of tokens once invoked — and that content can stay in the session afterwards.

The always-visible layer is a scarce budget. Every capability you leave auto-discoverable spends it.

## 2. Truncation is budget control, not meaning-preserving compression

When too many descriptions compete for the discovery layer, clients cut. Three visibility states result:

```text
Fully visible: name + description present; easy to auto-trigger.
Half visible: name present, description cut or dropped; the agent can no longer judge when to use it.
Initially invisible: omitted from the initial list; implicit discovery becomes unreliable.
```

Truncation preserves budget, not meaning:

```text
Original: I love you?
Truncated: I love you
```

One missing question mark changes the meaning. In a capability description it is worse:

```text
Original: Only for GitHub project intake checks. Do not use for ordinary code fixes.
Truncated: Only for GitHub project intake checks. Do not use for ordinary
```

The restriction is gone, and the capability now triggers **more** often, not less. Unstable triggering is often exactly this: a crowded discovery layer plus meaning-blind cuts.

## 3. The reframe: govern routing power, not files

The default mechanism is:

```text
Let the agent find capabilities by itself
inside a pile of skill / plugin / MCP descriptions.
```

Under that mechanism, broader descriptions can win ambiguous entry points and get invoked more often. The fix is not "write better descriptions for everything". The fix is to add a user-owned decision layer:

```text
Add your own thin router above native discovery.
The router guides the decision; it does not hide native capabilities by itself.
The agent reads the thinnest possible map first,
then opens exactly one drawer when needed.
```

One sentence:

> This kit is not a skill storage box. It is routing-power governance: deciding what the agent sees by default, when it sees it, how much of it, and who qualifies for the first layer.

## 4. Routing layers

| Layer | Content | Residency | Artifact in this kit |
| --- | --- | --- | --- |
| L0 Native visibility policy | Client settings + always-visible rules determine what is exposed and what may auto-invoke | Every session | Client-specific controls + a short rules pointer |
| L1 Thin router | Task-category entry points, each truncation-safe | Read first when routing | [Capability Router template](../templates/capability-router.md) |
| L2 Category index | Candidates per category + trigger / do-not-use conditions | Read only matching rows | Thin registry rows |
| L3 Capability card | Full description of one capability | Read only the top candidate | [Capability Manifest template](../templates/capability-manifest.md) |
| L4 Capability itself | Full SKILL.md / MCP server / repo | Enters context only when enabled | Cold storage + external clones |

Project semantic references run beside this executable L1-L4 chain, not inside it. The generated file first provides a mandatory thin discovery table for substantive tasks, then full semantic details. A meaning match selects at most one approved project reference, preserves `no-extra-project`, and grants no repository-reading or execution permission. `high_confidence` and `gated` both allow a reminder; `gated` controls later reading or execution.

L1 is **soft governance** when it exists only as an instruction in `AGENTS.md`, `CLAUDE.md`, or an equivalent rules file. Stronger isolation requires L0 client controls such as disabling a capability, removing it from implicit discovery, or requiring explicit invocation. Those controls are client-specific configuration and must not be changed without user approval.

The executable loop stays the same, with one added step:

```text
Need gate
-> Search 1-3 candidates (including "use no extra tool")
-> Describe the top candidate only
-> Preflight health, permissions, risk, rollback
-> Execute the smallest useful step
-> Verify the result
-> Write back meaningful changes
-> Recycle: return temporarily enabled capabilities to their pre-task state
```

Recycling caveat: content already loaded into the current session cannot be unloaded; config-level disabling takes effect for new sessions. When you need a clean state, start a new session.

## 5. Truncation-safe writing rules

Everything that stays exposed to the agent — L1 entries, registry rows, card summaries, MCP server instructions that remain visible after enabling — must survive being cut:

1. The first ~100 characters express the purpose on their own.
2. Trigger scenarios and do-not-use scenarios appear within the first ~200 characters.
3. Never put "do not use for..." at the end.
4. Do not rely on question marks, contrastive words, or long conditionals to carry core meaning.
5. No "this can also..." catch-all phrasing.
6. One entry serves exactly one task type.

Boundary: this is **not** a rule for every skill in your library. Capabilities already discovered through your router instead of native discovery do not need their original descriptions rewritten. Only the exposed layer needs it.

## 6. Manager-type capabilities: recognizing routing-power grabs

Some capabilities are not "a tool that does one thing" but "a manager that changes how your agent works". Recognize them by mechanism, not motive:

1. **Startup-wide triggers**: descriptions like "Use when starting any conversation" — trying to stand at the head of every session.
2. **Default-flow rewrites**: requiring the agent to check them first, before answering anything.
3. **Self-reinforcement**: once invoked, they push the agent to invoke more of their own family.
4. **Light surface, heavy effect**: a short description, but the full content reshapes behavior once loaded.
5. **Methodology takeover**: not helping with one task, but taking over how tasks are done.

Also: **a session-start hook injection is a first-layer routing act in itself.** It skips description competition entirely and puts content at the head of every session. Treat it as manager-type by definition.

Governance rules:

```text
1. Third-party capabilities do not qualify for the first routing layer by default.
2. Manager-type capabilities require an explicit allowlist decision,
   and are governed unbundled: allow only the smallest verified sub-capability,
   never the whole package because of its name.
3. Hook-injected content counts against the always-visible budget;
   measure it with clean new-session comparisons.
4. When reviewing a manager-type capability, ask what default behaviors it rewrites,
   not just how many tokens it costs.
```

When you talk about such capabilities publicly, describe the mechanism, not the motive:

> It is not an ordinary capability; it is a capability manager. When a third-party capability manager stands on the first routing layer by default, it is no longer just a tool — it is rewriting your agent's working habits.

## 7. Default mechanism vs. thin router

| | Default mechanism | Thin router |
| --- | --- | --- |
| Discovery | Agent searches all descriptions | Classify first, route, then enable on demand |
| Entry point | Broad descriptions can win ambiguous routing | Your router chooses preferred candidates; L0 still decides actual native visibility |
| Main risks | Truncated descriptions, crowded-out key tools, over-broad triggers, manager-type grabs, post-invocation pollution, oversized MCP returns | Maintenance cost; a stale router misroutes |
| Lever | Mostly description quality and client defaults | Combine L0 visibility controls with an L1 user-owned decision path |

Two metaphors that summarize the whole design:

```text
The default mechanism lays every tool out on the table and lets the agent pick.
A thin router hands the agent the thinnest possible map
and opens one drawer at a time.
```

```text
What needs governing is not the number of capabilities, but the default entry point.
Whoever stands on the first routing layer shapes how your agent thinks.
```

## 8. Verify before you rely on numbers

Injection order, budgets, and truncation behavior vary by client and version. This document freezes the mechanism, not the numbers. Before quoting specific token budgets or thresholds, check current official docs and measure clean new sessions on your own machine.

Last verified 2026-07-21: Codex documents metadata-first Skill discovery, progressive disclosure, implicit-invocation control, and per-Skill enablement. Claude Code documents Skill invocation controls and default MCP Tool Search that defers tool definitions until needed. These facts support the L0/L1 distinction; they do not make this repository a configuration controller.

- Claude Code skills: <https://code.claude.com/docs/en/skills>
- Claude Code MCP: <https://code.claude.com/docs/en/mcp>
- Codex skills: <https://learn.chatgpt.com/docs/build-skills>
- Codex configuration: <https://learn.chatgpt.com/docs/config-file/config-reference>
- Codex MCP: <https://developers.openai.com/codex/mcp>

## 中文

这份文档解释整套模板背后的第一性原理：能力怎么进入模型上下文、截断怎么发生，以及你真正要治理的东西——**路由权**：谁有资格默认站在 Agent 面前。

如果你在改模板前只读一份文档，读这份。

## 1. 一句"你好"实际发出了什么

你对 coding agent 说一句"你好"，模型收到的不是两个字，而是一个包裹。按客户端和版本不同，通常包括：

1. 系统提示：身份、行为规则、环境信息。
2. 你的规则文件（项目级和用户级，如 `CLAUDE.md` / `AGENTS.md`）。
3. 注入的记忆（memory）。
4. Skill 发现层：所有可见 Skill 的 name + description。
5. Plugin 贡献的组件（Skills、Agents、Hooks、MCP）。
6. MCP：server instructions + 工具名称 / 描述 / schema（部分客户端延迟加载）。
7. SessionStart 等 Hook 注入的内容。
8. 最后，才是你的消息。

所以每个能力都有**两层成本**：

```text
发现成本：每次会话都在付，哪怕这个能力从来没被用过。
调用成本：触发后全文进入会话时付。
```

一个大型 Skill 的 metadata 可能只有十几个 token，但调用一次可能加载数万 token——而且这些内容之后可能一直留在会话里。

常驻可见层是稀缺预算。每留一个自动可发现的能力，都在花这份预算。

## 2. 截断是预算控制，不是语义保真压缩

description 太多、挤爆发现层时，客户端会裁剪。结果出现三种可见状态：

```text
完整可见：name + description 都在，容易被自动触发。
半可见：name 在，description 被截短或丢失，Agent 没法判断使用场景。
初始不可见：被省略出初始列表，隐式发现基本靠不住。
```

截断只保预算、不保语义：

```text
原文：我爱你？
截断：我爱你
```

少一个问号，意思就变了。放到能力描述里更糟：

```text
原文：仅用于 GitHub 项目入库体检，不要用于普通代码修复。
截断：仅用于 GitHub 项目入库体检，不要用于普通
```

限制条件被截掉之后，这条能力反而**更容易**被误触发。触发不稳定的一个重要来源，就是发现层拥挤 + 不保语义的裁剪。

## 3. 换框架：治理路由权，不是治理文件

默认机制本质上是：

```text
让 Agent 在一堆 Skill / Plugin / MCP 的 description 里自己找能力。
```

在这种机制下，描述越宽的能力越可能抢到模糊入口，也更容易被调用。解法不是"把所有 description 都写好"，而是增加一层用户自己掌握的决策入口：

```text
在原生发现层之上增加自建薄路由。
薄路由负责引导决策，本身不会隐藏客户端原生能力。
Agent 先读最薄的一张地图，
需要时才打开对应的那一个抽屉。
```

一句话：

> 这套模板不是 Skill 收纳箱，而是路由权治理：决定 Agent 默认看见什么、什么时候看见、看见多少，以及谁有资格进入第一层。

## 4. 路由分层

| 层 | 内容 | 常驻性 | 本套模板对应 |
| --- | --- | --- | --- |
| L0 原生可见性策略 | 客户端设置 + 常驻规则共同决定哪些能力可见、哪些可自动调用 | 每次会话都在 | 客户端原生控制 + 规则里的短指针 |
| L1 一级薄路由 | 任务分类入口，每项截断安全 | 路由时先看 | [能力路由模板](../templates/capability-router.md) |
| L2 二级索引 | 分类内候选 + 触发 / 禁用条件 | 只读相关行 | 薄 Registry 行 |
| L3 能力卡 | 单个能力的完整说明 | 只读 Top-1 那张 | [能力 Manifest 模板](../templates/capability-manifest.md) |
| L4 能力本体 | SKILL.md 全文 / MCP server / repo | 启用才进入 | 冷库 + 外部 clone |

项目语义参考与这条可执行 L1-L4 链并列，不进入链内。生成文件先提供实质任务必查的薄发现表，再提供完整语义详情；语义命中最多选择一个经批准的项目参考，保留 `no-extra-project`，且不授予仓库读取或执行权限。`high_confidence` 与 `gated` 都可先提醒，`gated` 只限制后续读取或执行。

如果 L1 只是写在 `AGENTS.md`、`CLAUDE.md` 或同类规则文件里的指令，它属于**软治理**。更强隔离需要配合 L0 客户端控制，例如禁用能力、移出隐式发现或改为仅显式调用。这些操作属于客户端配置修改，未经用户确认不得执行。

可执行闭环不变，只加一步：

```text
Need Gate：是否需要额外能力
-> Search：搜 1-3 个候选（包括"不调用额外工具"）
-> Describe：只读 Top-1 详情
-> Preflight：检查健康、权限、风险、回滚
-> Execute：执行最小有用步骤
-> Verify：验证结果
-> Write Back：只写回有意义的变化
-> Recycle：把临时启用的能力恢复到任务前状态
```

回收的边界：已经进入当前会话上下文的内容收不回来；配置级停用只对新会话生效。需要干净状态时，开新会话。

## 5. 截断安全写作规则

所有会常驻暴露给 Agent 的内容——一级路由条目、Registry 行、能力卡摘要、启用后仍然可见的 MCP server instructions——都必须经得起被裁剪：

1. 前 100 字左右能独立表达用途；
2. 触发场景和禁止场景在前 200 字内出现；
3. "不要用于……"永远不写在末尾；
4. 不靠问号、转折词、长条件句表达核心含义；
5. 不写"这个能力也可以……"式泛化描述；
6. 一条入口只服务一个明确任务类型。

边界：这**不是**全库硬规则。已经通过薄路由（而不是原生发现）被找到的能力，原始 description 不必逐条改写。需要截断安全的只有暴露层。

## 6. 总管型能力：识别路由权抢占

有一类能力不是"帮你做一件事"，而是"改变你的 Agent 做事的方式"。按机制识别，不问动机：

1. **启动型触发**：description 写成 "Use when starting any conversation" 这类，试图站到每段对话的开头；
2. **改默认流程**：要求 Agent 先找它、先按它的流程，再回答；
3. **自我强化**：调用后继续推动 Agent 调用它的同族能力；
4. **表面轻、实际重**：description 很短，但全文一旦加载就重塑行为策略；
5. **方法论接管**：不是帮你做一件事，而是"以后你做事先按我这套来"。

另外：**SessionStart Hook 注入本身就是第一层路由行为。**它完全绕过 description 竞争，直接把内容放进每次会话的开头。按定义就应当作总管型对待。

治理规则：

```text
1. 第三方能力默认没有资格常驻第一层路由。
2. 总管型能力必须显式 allowlist，并且拆包治理：
   只放行已验证的最小子能力，绝不因为包名放行整包。
3. Hook 注入内容计入常驻层预算，用干净新会话对照实测。
4. 评审总管型能力时，重点问它改写了 Agent 的哪些默认行为，
   而不只是它占多少 token。
```

对外表达时说机制、不说动机：

> 它不是一个普通能力，而是一个能力管理器。当一个第三方能力管理器默认站到第一层路由，它就不再只是工具，而是在重写 Agent 的工作习惯。

## 7. 默认机制 vs 薄路由

| | 默认机制 | 薄路由 |
| --- | --- | --- |
| 发现方式 | Agent 在全部 description 里自己找 | 先分类，再路由，再按需启用 |
| 入口归属 | 宽描述可能抢到模糊入口 | 路由表选择优先候选；实际原生可见性仍由 L0 决定 |
| 主要风险 | description 被截、关键工具被挤掉、泛化误触发、总管型抢入口、调用后污染会话、MCP 返回膨胀 | 维护成本；路由表过期会导错路 |
| 治理抓手 | 主要依赖 description 质量与客户端默认值 | L0 可见性控制 + L1 用户决策入口组合治理 |

两句收束整套设计的话：

```text
默认机制是把所有工具摆在桌上，让 Agent 自己挑；
薄路由是先给 Agent 一张极薄的地图，一次只开一个抽屉。
```

```text
真正要治理的不是能力数量，而是默认入口。
谁站在第一层路由，谁就在影响 Agent 的思考方式。
```

## 8. 引用数字前先复核

注入顺序、预算数值和截断行为随客户端和版本变化。本文档固化的是机制，不是数字。引用具体 token 预算或阈值前，先查当前官方文档，并在自己机器上用干净新会话实测。

最近核实于 2026-07-21：Codex 官方说明了 Skill metadata 优先、渐进加载、隐式调用控制和按 Skill 启停；Claude Code 官方说明了 Skill 调用控制，以及默认通过 MCP Tool Search 延迟加载工具定义。这些事实支撑 L0/L1 分层，但不代表本仓库能直接控制客户端配置。

- Claude Code Skills：<https://code.claude.com/docs/en/skills>
- Claude Code MCP：<https://code.claude.com/docs/en/mcp>
- Codex Skills：<https://learn.chatgpt.com/docs/build-skills>
- Codex 配置：<https://learn.chatgpt.com/docs/config-file/config-reference>
- Codex MCP：<https://developers.openai.com/codex/mcp>
