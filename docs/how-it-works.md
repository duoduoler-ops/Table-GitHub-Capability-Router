# How It Works / 运作方式

English | [中文](#中文)

This workflow connects three layers:

| Layer | Purpose | It does not do |
| --- | --- | --- |
| Obsidian LLM Wiki | Stores rules, notes, indexes, decisions, and summaries | Does not run tools or replace permissions |
| GitHub Project Intake | Decides whether a project is useful, redundant, risky, or worth testing | Does not prove runtime success by itself |
| Capability Inventory & Cold Storage | Screens existing Skills, Plugins, MCP servers, scripts, and CLIs; tracks manifests, health checks, risk, and rollback | Does not mean every tool is enabled by default |

The main design goal is to keep the hot context small. Full clones, raw logs, runtime folders, and long tool descriptions stay outside the Obsidian hot layer. The agent reads short indexes and manifests first, then opens only the minimum detail needed for the current task.

## Routing Layers

Capability discovery is layered instead of flat. The agent never scans the whole library:

```text
Level-0 native visibility policy + short rules pointer
-> Level-1 thin router: task categories, truncation-safe one-liners
-> Level-2 registry rows: triggers and do-not-use conditions
-> Level-3 capability card: full detail of one capability
-> Level-4 the capability itself: loaded only when enabled
```

Level 1 guides routing but does not replace native discovery by itself. Actual visibility and automatic invocation remain controlled by Level 0 client settings. Every entry that stays exposed to the agent must be truncation-safe: purpose first, do-not-use conditions early, nothing critical at the end of the line. After a task, temporarily enabled capabilities are recycled back to their pre-task state.

Why the layers exist — context injection, truncation behavior, and manager-type capabilities — is explained in [What Your Agent Actually Sees](context-and-routing.md). The concrete template is [Capability Router](../templates/capability-router.md).

## Knowledge Placement

Do not put every retained GitHub project into a separate standalone knowledge page. Put the extracted knowledge where it will actually be reused:

| Extracted value | Best location |
| --- | --- |
| Reusable SOP, checklist, prompt pattern, or workflow | Workflow page |
| General architecture, concept, or decision model | Concept page |
| Notes that only matter inside one of your own projects | That project page |
| Source evidence, grade, risk, and test decision | GitHub project card |
| Agent-readable rediscovery and read-scope metadata | Reference manifest |
| Executable routing option | Thin registry, only if eligible |

The common pattern is:

```text
GitHub project card
-> update or create the smallest useful distillation page
-> reference manifest points to that page and its read scope
-> capability-slot index records the relationship to current options
-> thin registry only includes executable and eligible capabilities
```

One distillation page can absorb ideas from multiple projects. A new page is needed only when the project produces a genuinely new reusable method.

## Core Loop

```text
Capture
-> Position
-> Compare
-> Verify
-> Decide
-> Write back
```

## 1. Capture

Put rough material into an inbox folder first. Examples:

- A GitHub URL.
- A copied README.
- A paper, article, or product note.
- A tool or agent capability you may want to test later.

The inbox preserves raw evidence. Do not overwrite source material unless you intentionally clean it.

## 2. Position

For a GitHub project, answer in 30 seconds:

- What does it replace?
- What does it enhance?
- What does it produce?
- What capability slot does it belong to?
- Is the value already covered by the base model, the current agent, local tools, or existing notes?

For an existing capability, answer:

- What task can it actually do?
- Is it already installed, merely downloaded, or only a reference?
- What permissions, accounts, files, or external services can it touch?
- Is it healthy, unverified, degraded, broken, or missing?
- Should it be active, cold, disabled, reference, or retired?

Capability slots should use this shape:

```text
verb + object + output
```

Examples:

- search web pages and produce cited summaries
- transcribe audio and produce timestamped text
- evaluate GitHub projects and produce project cards

## 3. Compare

A project is not evaluated in isolation. Compare it against:

- doing nothing extra;
- the base model;
- current Codex or Claude Code capabilities;
- local CLI tools;
- existing projects in your vault;
- one or two similar alternatives.

The goal is not to collect more tools. The goal is to decide:

```text
keep current / combine / test as challenger / replace / use lightweight fallback
```

For existing capabilities, the goal is to reduce routing noise:

```text
active only when it is useful and safe by default
cold when useful but should be activated deliberately
disabled when installed but should not be routed
reference when it is method knowledge, not an executable tool
retired when it should no longer be used
```

## 4. Verify

Use evidence levels:

| Level | Meaning |
| --- | --- |
| Author claim | README, docs, demo, or marketing statement |
| Online check | Current repo status, release, issues, license, docs |
| Static check | Read code/config without running it |
| T0 | Minimal static or install-boundary check |
| T1 | One-sample smoke test |
| T2 | Same-scenario comparison against the current solution |
| T3 | Real recurring task with repeatable value |

Do not let a score override missing evidence.

## 5. Decide

Use simple retention states:

| Grade | Meaning |
| --- | --- |
| S | Core workflow asset proven by real work |
| A | Verified component or strong backup |
| B | Useful reference, method, architecture, or bounded tool |
| C | Candidate to watch or test later |
| D | Do not keep beyond a short rejection note |

Scores can help sort similar candidates, but they should not automatically produce S/A/B/C/D.

## 6. Write Back

Write useful conclusions back into:

- project card;
- workflow, concept, or project distillation page;
- capability-slot index;
- candidate pool or rejection log;
- cold-storage manifest;
- thin registry entry or explicit non-entry;
- maintenance log.

Keep raw logs, full clones, runtime files, and model caches outside the Obsidian vault.

### Minimum write protocol

1. Normalize the GitHub URL and resolve a canonical project/capability ID before creating files.
2. Search for existing records and re-read every target file immediately before editing. Existing records are updated; equivalent duplicates are not created.
3. Build a change set that separates ordinary records from protected routing or configuration changes. Project cards, evidence, candidate/rejection records, and maintenance logs are ordinary write-back; Registry/L1 promotion, automatic invocation, Hooks, and client configuration require explicit approval.
4. Apply source records first, then rebuild or check derived indexes, then append one maintenance event. Do not treat a partially updated index as the source of truth.
5. Validate duplicate IDs, links, state combinations, intended file scope, and `git diff`. If a conflict or partial failure appears, stop and report the exact completed and incomplete files instead of continuing blindly.

Idempotency rule: running the same canonical URL twice must update the same record, keep the same ID, and avoid duplicate evidence or Registry rows.

## 中文

这套工作流把三层系统连起来：

| 层级 | 负责什么 | 不负责什么 |
| --- | --- | --- |
| Obsidian LLM Wiki | 保存规则、笔记、索引、决策和摘要 | 不直接运行工具，不替代权限控制 |
| GitHub 项目入库 | 判断项目是否有用、重复、风险高、值得测试 | 不单独证明项目能跑通 |
| 能力盘点与冷库 | 筛查已有 Skill、Plugin、MCP、脚本和 CLI；记录 manifest、健康检查、风险和回滚 | 不等于默认启用所有工具 |

核心设计目标是让热层上下文保持小而稳定。完整 clone、原始日志、运行时目录和很长的工具说明都留在 Obsidian 热层之外。Agent 先读取短索引和 manifest，再按当前任务打开最小必要详情。

## 路由分层

能力发现是分层的，不是平铺的。Agent 从不扫描整库：

```text
L0 客户端原生可见性策略 + 常驻规则里的短指针
-> L1 一级薄路由：任务分类，每项截断安全的一句话
-> 二级 Registry 行：触发与禁用条件
-> 三级能力卡：单个能力的完整说明
-> 四级能力本体：启用时才进入上下文
```

L1 负责引导路由，但本身不会替代原生发现；实际可见性和自动调用仍由 L0 客户端设置控制。所有常驻暴露给 Agent 的条目必须截断安全：用途先行，禁止场景前置，关键限制不放行尾。任务结束后，临时启用的能力回收到任务前状态。

为什么要这样分层——上下文注入、截断行为、总管型能力——见 [Agent 实际看到什么](context-and-routing.md)；具体模板见 [能力路由模板](../templates/capability-router.md)。

## 知识放在哪里

不要把每个正式保留的 GitHub 项目都单独写成一页重复知识。提炼出来的内容应该放到以后真正会复用的位置：

| 提炼出的价值 | 推荐位置 |
| --- | --- |
| 可复用 SOP、检查清单、提示词模式或工作流程 | 工作流页 |
| 通用架构、概念或决策模型 | 概念页 |
| 只服务某个自有项目的笔记 | 对应项目页 |
| 来源证据、等级、风险和测试决策 | GitHub 项目卡 |
| 给 Agent 以后重新发现和限定读取范围的 metadata | reference manifest |
| 可执行路由选项 | 薄 Registry，仅限符合条件的能力 |

常见联动是：

```text
GitHub 项目卡
-> 更新或创建最小有用提炼页
-> reference manifest 指向该提炼页和最小读取范围
-> 能力槽索引记录它与当前方案的关系
-> 薄 Registry 只收可执行且符合条件的能力
```

一个提炼页可以吸收多个项目的想法。只有项目真的产出新方法时，才需要新建提炼页。

## 核心循环

```text
捕获
-> 定位
-> 比较
-> 验证
-> 决策
-> 写回
```

## 1. 捕获

先把粗糙资料放进收件箱。例如：

- 一个 GitHub URL；
- 复制下来的 README；
- 论文、文章或产品笔记；
- 以后可能测试的工具或 Agent 能力。

收件箱负责保留原始证据。除非你明确清洗资料，不要随手覆盖源内容。

## 2. 定位

对 GitHub 项目先做 30 秒定位：

- 它替代什么？
- 它增强什么？
- 它产出什么？
- 它属于哪个能力槽？
- 模型本身、当前 Agent、本机工具或已有笔记是否已经覆盖？

对已有能力则回答：

- 它到底能完成什么任务？
- 它是已经安装、只是下载过，还是只适合作 reference？
- 它会触碰哪些权限、账号、文件或外部服务？
- 它是 healthy、unverified、degraded、broken 还是 missing？
- 它应该是 active、cold、disabled、reference 还是 retired？

能力槽建议使用：

```text
动词 + 对象 + 产物
```

示例：

- 搜索网页并生成带来源摘要；
- 转录音频并输出带时间戳文本；
- 评价 GitHub 项目并生成项目卡。

## 3. 比较

不要孤立评价一个项目。至少和这些对象比较：

- 不调用额外能力；
- 模型本身；
- 当前 Codex 或 Claude Code 能力；
- 本机 CLI 工具；
- vault 里已有项目；
- 1-2 个同类方案。

目标不是收藏更多工具，而是判断：

```text
保留现有 / 互补组合 / 挑战者测试 / 替换现有 / 回退轻量方案
```

对已有能力，目标是减少路由噪声：

```text
active：默认有用且安全
cold：有用，但需要显式激活
disabled：已经安装，但不应该参与路由
reference：只是方法知识，不是可执行工具
retired：不再使用
```

## 4. 验证

推荐证据层级：

| 层级 | 含义 |
| --- | --- |
| 作者声明 | README、文档、demo 或营销说明 |
| 联网核查 | 当前仓库状态、Release、Issue、License、文档 |
| 静态检查 | 只读代码和配置，不运行 |
| T0 | 最小静态或安装边界检查 |
| T1 | 单样本冒烟测试 |
| T2 | 和当前方案做同场景比较 |
| T3 | 真实重复任务中产生稳定价值 |

不要让分数绕过证据门槛。

## 5. 决策

推荐保留等级：

| 等级 | 含义 |
| --- | --- |
| S | 已由真实工作流证明的核心资产 |
| A | 已验证组件或强备用方案 |
| B | 有用的 reference、方法、架构或边界明确的工具 |
| C | 候选观察，等待触发条件或测试 |
| D | 不保留，只写一句可复核否决理由 |

评分可以帮助同类候选排序，但不要自动生成 S/A/B/C/D。

## 6. 写回

有用结论应该写回：

- 项目卡；
- 工作流、概念或项目提炼页；
- 能力槽索引；
- 候选池或否决记录；
- 冷库 manifest；
- 薄 Registry 条目，或明确不进入 Registry；
- 维护日志。

原始日志、完整 clone、运行时文件和模型缓存不要放进 Obsidian vault。

### 最小写回协议

1. 新建文件前先规范化 GitHub URL，并解析唯一的项目/能力 canonical ID。
2. 查找已有记录，编辑前立即重读所有目标文件；已有记录只更新，不创建等价重复项。
3. 先列变更清单，并把普通记录与受保护的路由/配置修改分开。项目卡、证据、候选/否决记录和维护日志可普通写回；Registry/L1 晋升、自动调用、Hook 和客户端配置必须先获得明确批准。
4. 先改源记录，再重建或校验派生索引，最后追加一条维护事件；半更新的索引不能反过来充当事实源。
5. 检查重复 ID、链接、状态组合、文件范围和 `git diff`。发现冲突或半完成状态就停止，明确报告哪些文件已完成、哪些未完成，不盲目继续。

幂等规则：同一个 canonical URL 连续执行两次，必须更新同一份记录、保持同一个 ID，并避免重复证据或重复 Registry 行。
