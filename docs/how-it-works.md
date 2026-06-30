# How It Works / 运作方式

English | [中文](#中文)

This workflow connects three layers:

| Layer | Purpose | It does not do |
| --- | --- | --- |
| Obsidian LLM Wiki | Stores rules, notes, indexes, decisions, and summaries | Does not run tools or replace permissions |
| GitHub Project Intake | Decides whether a project is useful, redundant, risky, or worth testing | Does not prove runtime success by itself |
| Capability Inventory & Cold Storage | Screens existing Skills, Plugins, MCP servers, scripts, and CLIs; tracks manifests, health checks, risk, and rollback | Does not mean every tool is enabled by default |

The main design goal is to keep the hot context small. Full clones, raw logs, runtime folders, and long tool descriptions stay outside the Obsidian hot layer. The agent reads short indexes and manifests first, then opens only the minimum detail needed for the current task.

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
- capability-slot index;
- candidate pool or rejection log;
- cold-storage manifest;
- thin registry entry or explicit non-entry;
- maintenance log.

Keep raw logs, full clones, runtime files, and model caches outside the Obsidian vault.

## 中文

这套工作流把三层系统连起来：

| 层级 | 负责什么 | 不负责什么 |
| --- | --- | --- |
| Obsidian LLM Wiki | 保存规则、笔记、索引、决策和摘要 | 不直接运行工具，不替代权限控制 |
| GitHub 项目入库 | 判断项目是否有用、重复、风险高、值得测试 | 不单独证明项目能跑通 |
| 能力盘点与冷库 | 筛查已有 Skill、Plugin、MCP、脚本和 CLI；记录 manifest、健康检查、风险和回滚 | 不等于默认启用所有工具 |

核心设计目标是让热层上下文保持小而稳定。完整 clone、原始日志、运行时目录和很长的工具说明都留在 Obsidian 热层之外。Agent 先读取短索引和 manifest，再按当前任务打开最小必要详情。

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
- 能力槽索引；
- 候选池或否决记录；
- 冷库 manifest；
- 薄 Registry 条目，或明确不进入 Registry；
- 维护日志。

原始日志、完整 clone、运行时文件和模型缓存不要放进 Obsidian vault。
