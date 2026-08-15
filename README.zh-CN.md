# GitHub 项目入库 + 能力冷库 + 自动路由

这套仓库的目标很直接：你把一个 GitHub 链接交给 Agent，Agent 不再只在聊天里随口评价，而是把它变成可追踪的项目记录；如果项目能沉淀成 Skill、Plugin、MCP、CLI、脚本或方法论，再进入能力冷库和薄路由。

## 当前验证宿主

当前维护主线是 **Grok Build + Codex**。两者共用 `.agents/skills/github-vault-router/` 项目级 Skill；Claude Code 仍通过 `.claude/skills/github-vault-router/` 保留兼容支持，但不再是当前默认宿主。

`AGENTS.md` 是唯一规则正文。根目录 `CLAUDE.md` 只保留一个指向 `AGENTS.md` 的最小兼容入口：2026-08-09 对 Grok Build 1.0.0 的本机实测发现，即使关闭 Claude 兼容导入，Grok 仍会读取根目录 `CLAUDE.md`，所以不能假定它完全不读这个文件，也不应在里面复制第二份规则。

## 版本重点

以后每次发布都在这里补一行重点；完整实现细节统一写入 [CHANGELOG.md](CHANGELOG.md)。

| 版本 | 本次重点 | 用户能感知到的变化 |
| --- | --- | --- |
| Unreleased（计划 v0.4.0） | B 级任务增量判断与首次真实使用结算 | Schema v3 拆开等级与部署范围；低风险可执行候选经过 T0 和项目级批准后，当前项目第一次真实任务就是 T1 |
| v0.3.0 | 先发现已入库能力，再判断是否使用 | 有明确对象、动作或产物的任务先查薄发现表；`gated` 项目可以先提醒，但读取、安装和执行仍需过门禁 |
| v0.2.0 | 确定性入库与语义参考 | 增加 Schema 事实源、CLI 重建校验、事务写回和一张完整语义表 |
| v0.1.0 | 可公开的 Markdown 起步模板 | 建立双语模板、入库提示词和脱敏示例 |

## v0.3.0 新增内容

| 新增能力 | 解决的问题 |
| --- | --- |
| 实质任务必过薄发现门 | Agent 不能再先凭印象断定“没有相关项目”；每类产物先查一次短能力表 |
| 薄发现 + 完整语义两层表 | 先用唯一能力摘要低成本选 Top-1，再只读对应完整语义行 |
| `gated` 先提醒 | `high_confidence` 与 `gated` 都可先提示项目存在；`gated` 只限制后续读取或执行 |
| Schema v2 能力摘要 | 每个正式项目必须有一条可区分的“动词 + 对象 + 产物”摘要；重复摘要会被校验拦截 |
| 事务化 `migrate-v2` | v0.2 工作流补齐正式项目摘要后，一次性升级项目卡、能力记录、配置和派生表 |
| 三路线提醒 | 始终保留普通方案；用户选择后才最小读取 Markdown；确需运行时再询问安装或启用 |

## v0.2.0 新增内容

| 新增能力 | 解决的问题 |
| --- | --- |
| 零第三方依赖的确定性 Python CLI | 初始化、入库、更新、状态迁移、重建、校验和回滚不再只靠提示词记忆 |
| Schema 事实源 | 防止 ID、URL、状态、审批信息和派生表互相漂移 |
| GitHub 项目语义命中表 | 用户只说日常话时，也能建议一个相关的正式保留项目 |
| 正向示例 + 负向边界 + 命中级别 | 引入 `high_confidence`、`gated` 和仅点名证据，为后续版本的发现门奠定事实源 |
| 自动一致性校验 + 可选提交前门禁 | 拦截缺记录、重复示例、资格错误和生成表过期；经批准启用后可在 commit 前拦截 |
| Codex / Claude Code 项目级 Skill | 两端共享工作流事实，但保留各自客户端调用机制 |
| PR #1 可选只读能力审计 | 盘点 Codex、Claude Code、Kimi Code 等客户端能力，不修改配置 |
| 事务式写入 | 加锁、修改前备份、原子替换、失败回滚和 Git 历史隐私扫描 |

> 历史说明：v0.2.0 引入命中级别；v0.3.0 已把 `gated` 调整为“先提醒项目存在，后续读取或执行再过门禁”。当前 Unreleased 版本线保留该行为，并增加下方 B 级结算。

## Unreleased（计划 v0.4.0）：B 级首次真实使用

- 等级、部署范围、管理状态、健康和调用方式分别记录；A 不代表全局安装。
- B 级只有方法价值时维持 reference，不安装。
- 低风险可执行候选先做 T0，再询问是否按 `project` 范围安装；当前项目第一次真实任务就是 T1。
- 通过后结算为 A/retained + active/project；失败或结论不清则保持 B/reference 并建议卸载，真正删除仍需确认。
- 不建立长期 `project-trial` 状态。只有高权限、真实凭据、外部写入、后台服务、重缓存、来源/License/回滚不清或没有项目级安装方式时才要求隔离。

## 最短使用方式

把下面这段复制给 Grok Build、Codex 或其他能读 GitHub、能操作本地文件的 Agent：

```text
请用这个工作流仓库帮我建立“GitHub 项目入库 + 能力冷库 + 自动路由”：
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

先只读仓库根目录的 AGENT-START.md，按其中门禁执行。
把产物建立在一个新的隔离目录；使用本机已有 Python，不安装依赖。
初始化、生成第一条候选记录并校验；安装、登录、外发、删除、修改客户端配置前必须先问我。
```

Agent 需要本地执行时，可以把这份公开源码 clone 到隔离目录。若没有输出路径，只需向你询问一次输出路径。

## 初始化后得到什么

```text
<OUTPUT_DIR>/
├─ AGENT-ROUTER.md              # 给 Agent 的短入口
├─ workflow.json                # 路径、客户端和 9 类路由配置
├─ projects/records/            # GitHub 项目事实源
├─ capabilities/records/        # 能力冷库事实源
├─ indexes/                     # 自动生成的项目索引、薄发现表和完整语义表
├─ router/level1-router.md      # 自动生成的 L1/L2 薄路由
├─ logs/maintenance-log.md      # 维护事件
└─ .workflow/transactions/      # 每次写入的事务、哈希和修改前备份
```

## 它自动做什么

- GitHub 地址规范化，稳定 ID，重复链接命中同一记录；
- 新项目固定从 `candidate / ungraded / unverified` 开始；
- 新能力固定从 `candidate / unverified / not-installed / explicit-only` 开始；
- 项目晋级、能力启用和自动调用走机器校验的状态机；
- `candidate/disabled/quarantine/retired` 不进入薄路由；
- active 能力一旦健康降级，自动隔离、禁用调用并从路由消失；
- 总管型能力单独标记，schema v3 禁止自动调用；
- 每条能力明确记录 `not-installed / project / user / global / external-service` 部署范围；
- 所有写入先加锁，再生成事务清单和修改前备份，失败自动回滚；
- 索引、候选池、否决记录、L1/L2 路由从事实源重建；
- S/A/B 且为 `retained/reference` 的项目自动生成薄发现表和完整语义表；
- 每条正式记录要求一条唯一能力摘要、至少两条日常说法、命中级别和禁止命中条件；
- 候选、否决、归档和 C/D 项目自动排除；命中只提供参考，不授权执行；
- 校验重复 ID、状态组合、派生文件漂移、相对链接、当前文件和 Git 历史中的敏感信息。

## 它故意不自动做什么

- 不替你决定证据是否可信；
- 不执行目标仓库 README、Issue、代码注释里的命令；
- 不自动 clone、安装或运行被评估项目；
- 不自动登录账号、发布内容、删除数据或修改客户端配置；
- 不把“记录为 active”冒充“客户端已经真的安装并启用”。

这些边界不是自动化不足，而是为了防止外部仓库通过提示词注入抢走 Agent 的执行权。

## 常用命令

```powershell
# 初始化隔离工作流
python scripts/workflow.py init --root <OUTPUT_DIR> --language zh-CN --client grok-build

# 创建或命中同一条 GitHub 项目记录
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>

# 把已有 schema v2 工作流事务化升级到 schema v3（每条能力重复一项）
python scripts/workflow.py migrate-v3 --root <OUTPUT_DIR> `
  --deployment-scope "capability-id=project"

# 晋级正式参考项目时原子写入语义命中信息
python scripts/workflow.py project-transition --root <OUTPUT_DIR> --id <PROJECT_ID> --to reference --grade B --approved `
  --capability-summary "比较已保存的项目并输出一份可复用参考建议" `
  --semantic-example "帮我找一个可复用的参考工作流" `
  --semantic-example "现有哪个 GitHub 项目能改善这个任务" `
  --trigger-level gated `
  --negative-routing "普通直接回答或方案已经确定时不命中"

# 创建能力候选
python scripts/workflow.py new-capability --root <OUTPUT_DIR> --id <ID> --name <NAME> --type <TYPE> --route-category <CATEGORY>

# 真实安装已另行获批并完成后，只记录部署事实；本命令不会执行安装
python scripts/workflow.py capability-deployment --root <OUTPUT_DIR> --id <ID> --to project --evidence "已批准并完成当前项目安装" --approved

# 从事实源重建索引和路由
python scripts/workflow.py rebuild --root <OUTPUT_DIR>

# 验证整个工作流
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

状态变更命令和审批参数见 [Agent 唯一入口](AGENT-START.md) 与 [状态机](docs/state-machine.md)。

## 项目语义命中的真实边界

生成的 `indexes/project-semantic-routing.md` 先放薄发现表，再放完整语义表。凡任务已有明确对象、动作或产物，Agent 每类产物先查一次薄表；语义命中最多选 Top-1，再只读对应完整行。工作流负责“怎么做”，项目 reference 负责“库里已有谁能补强”，二者并行。

- `high_confidence`：语义明确时先提醒；
- `gated`：也先提醒，门禁只限制后续读取或执行；
- `explicit_only`：仅在用户点名或明确要求时建议。

提醒时同时给普通方案、用户选择后只读最小 Markdown、确需运行时再询问安装或启用。命中不会自动读取仓库、clone、安装、登录、运行未知脚本、改配置或发布。

## 可选只读能力审计

PR #1 提供了独立的跨客户端盘点入口，当前覆盖 Grok Build、Codex、Claude Code、Kimi Code 和通用 Agent。它只读取 Skill、Plugin、MCP、Hook 和规则可见性，不改文件或客户端配置；命令发现已兼容原生 Windows、macOS 和 Linux。

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

## 自动调用的真实边界

本仓库同时提供：

- Grok Build / Codex 共用项目 Skill：`.agents/skills/github-vault-router/`；
- Claude Code 兼容项目 Skill：`.claude/skills/github-vault-router/`；
- 唯一规则正文：`AGENTS.md`；
- 兼容指针与启动入口：`CLAUDE.md`、`AGENT-START.md`。

当 Agent 打开这份仓库时，匹配“GitHub 项目入库、能力冷库、路由治理”的任务，可按客户端原生机制发现项目 Skill。但把生成后的路由永久接到另一个项目或全局配置，仍是配置变更，必须由使用者批准。

## 视频教程

- [上集 · 你收藏的 GitHub 神器，真的值得装吗](https://www.youtube.com/watch?v=c4d23apzOEY)
- [下集 · 这个仓库背后的 Agent 能力冷库工作流](https://www.youtube.com/watch?v=juIsuIy55mQ)
- [进阶篇](https://www.youtube.com/watch?v=k7S5ewLaMVI&t=16s)

## 验证与演示

[自动生成演示](examples/generated-demo-v1/README.md) 不是手写效果图，而是 CLI 实际运行产物，包含 2 个虚构项目、3 个虚构能力、派生索引、路由、维护日志和事务记录。

```powershell
python -m unittest discover -s tests -v
node --test integrations/optimize-agent-capabilities/tests/audit.test.mjs
python scripts/workflow.py validate --root examples/generated-demo-v1
python scripts/workflow.py validate-repo
```

进一步阅读：[写回协议](docs/write-protocol.md)、[状态机](docs/state-machine.md)、[可选能力审计](docs/optional-capability-optimizer.md)、[可选提交前门禁](docs/optional-pre-commit.md)、[客户端配置边界](docs/client-profiles/generic-agent.md)、[安全策略](SECURITY.md)、[v0.1 → v0.2 迁移](docs/migrations/v0.1-to-v0.2.md)、[v0.2 → v0.3 迁移](docs/migrations/v0.2-to-v0.3.md)。
