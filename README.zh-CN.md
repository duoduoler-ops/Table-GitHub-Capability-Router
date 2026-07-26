# GitHub 项目入库 + 能力冷库 + 自动路由

这套仓库的目标很直接：你把一个 GitHub 链接交给 Agent，Agent 不再只在聊天里随口评价，而是把它变成可追踪的项目记录；如果项目能沉淀成 Skill、Plugin、MCP、CLI、脚本或方法论，再进入能力冷库和薄路由。

## v0.2.0 新增内容

| 新增能力 | 解决的问题 |
| --- | --- |
| 零第三方依赖的确定性 Python CLI | 初始化、入库、更新、状态迁移、重建、校验和回滚不再只靠提示词记忆 |
| Schema 事实源 | 防止 ID、URL、状态、审批信息和派生表互相漂移 |
| GitHub 项目语义命中表 | 用户只说日常话时，也能建议一个相关的正式保留项目 |
| 正向示例 + 负向边界 + 命中级别 | 区分自动建议、条件建议、仅点名建议，减少误命中 |
| 自动一致性校验 + 可选提交前门禁 | 拦截缺记录、重复示例、资格错误和生成表过期；经批准启用后可在 commit 前拦截 |
| Codex / Claude Code 项目级 Skill | 两端共享工作流事实，但保留各自客户端调用机制 |
| PR #1 可选只读能力审计 | 盘点 Codex、Claude Code、Kimi Code 等客户端能力，不修改配置 |
| 事务式写入 | 加锁、修改前备份、原子替换、失败回滚和 Git 历史隐私扫描 |

## 最短使用方式

把下面这段复制给 Codex、Claude Code 或其他能读 GitHub、能操作本地文件的 Agent：

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
├─ indexes/                     # 自动生成的项目索引和语义命中表
├─ router/level1-router.md      # 自动生成的 L1/L2 薄路由
├─ logs/maintenance-log.md      # 维护事件
└─ .workflow/transactions/      # 每次写入的事务、哈希和修改前备份
```

## 它自动做什么

- GitHub 地址规范化，稳定 ID，重复链接命中同一记录；
- 新项目固定从 `candidate / ungraded / unverified` 开始；
- 新能力固定从 `candidate / unverified / explicit-only` 开始；
- 项目晋级、能力启用和自动调用走机器校验的状态机；
- `candidate/disabled/quarantine/retired` 不进入薄路由；
- active 能力一旦健康降级，自动隔离、禁用调用并从路由消失；
- 总管型能力单独标记，schema v1 禁止自动调用；
- 所有写入先加锁，再生成事务清单和修改前备份，失败自动回滚；
- 索引、候选池、否决记录、L1/L2 路由从事实源重建；
- S/A/B 且为 `retained/reference` 的项目自动生成语义命中表，每个合格项目恰好一行；
- 每条语义记录要求至少两条日常说法、命中级别和禁止命中条件；
- 候选、否决、归档和 C/D 项目自动排除；命中只提供参考，不授权执行；
- 校验重复 ID、状态组合、派生文件漂移、相对链接、当前文件和 Git 历史中的敏感信息。

## 它故意不自动做什么

- 不替你决定证据是否可信；
- 不执行目标仓库 README、Issue、代码注释里的命令；
- 不自动 clone、安装或运行被评估项目；
- 不自动登录账号、发布内容、删除数据或修改 Codex/Claude 配置；
- 不把“记录为 active”冒充“客户端已经真的安装并启用”。

这些边界不是自动化不足，而是为了防止外部仓库通过提示词注入抢走 Agent 的执行权。

## 常用命令

```powershell
# 初始化隔离工作流
python scripts/workflow.py init --root <OUTPUT_DIR> --language zh-CN --client codex

# 创建或命中同一条 GitHub 项目记录
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>

# 晋级正式参考项目时原子写入语义命中信息
python scripts/workflow.py project-transition --root <OUTPUT_DIR> --id <PROJECT_ID> --to reference --grade B --approved `
  --semantic-example "帮我找一个可复用的参考工作流" `
  --semantic-example "现有哪个 GitHub 项目能改善这个任务" `
  --trigger-level gated `
  --negative-routing "普通直接回答或方案已经确定时不命中"

# 创建能力候选
python scripts/workflow.py new-capability --root <OUTPUT_DIR> --id <ID> --name <NAME> --type <TYPE> --route-category <CATEGORY>

# 从事实源重建索引和路由
python scripts/workflow.py rebuild --root <OUTPUT_DIR>

# 验证整个工作流
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

状态变更命令和审批参数见 [Agent 唯一入口](AGENT-START.md) 与 [状态机](docs/state-machine.md)。

## 项目语义命中的真实边界

生成的 `indexes/project-semantic-routing.md` 是只读候选层，不是可执行能力注册表。Agent 根据用户大概意思匹配，不要求用户说出专业关键词；最多建议一个相关项目，并同时保留“不调用额外项目”的普通方案。

- `high_confidence`：语义明确时可以自动建议；
- `gated`：只有满足项目卡里的前置条件才建议；
- `explicit_only`：仅在用户点名或明确要求时建议。

命中不会自动 clone、安装、登录、运行未知脚本、改配置或发布。

## 可选只读能力审计

PR #1 提供了独立的跨客户端盘点入口。它只读取 Skill、Plugin、MCP、Hook 和规则可见性，不改文件或客户端配置；命令发现已兼容原生 Windows、macOS 和 Linux。

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

## 自动调用的真实边界

本仓库同时提供：

- Codex 项目 Skill：`.agents/skills/github-vault-router/`；
- Claude Code 项目 Skill：`.claude/skills/github-vault-router/`；
- 通用规则入口：`AGENTS.md`、`CLAUDE.md`、`AGENT-START.md`。

当 Agent 打开这份仓库时，匹配“GitHub 项目入库、能力冷库、路由治理”的任务，可按客户端原生机制发现项目 Skill。但把生成后的路由永久接到另一个项目或全局配置，仍是配置变更，必须由使用者批准。

## 验证与演示

[自动生成演示](examples/generated-demo-v1/README.md) 不是手写效果图，而是 CLI 实际运行产物，包含 2 个虚构项目、3 个虚构能力、派生索引、路由、维护日志和事务记录。

```powershell
python -m unittest discover -s tests -v
node --test integrations/optimize-agent-capabilities/tests/audit.test.mjs
python scripts/workflow.py validate --root examples/generated-demo-v1
python scripts/workflow.py validate-repo
```

进一步阅读：[写回协议](docs/write-protocol.md)、[状态机](docs/state-machine.md)、[可选能力审计](docs/optional-capability-optimizer.md)、[可选提交前门禁](docs/optional-pre-commit.md)、[客户端配置边界](docs/client-profiles/generic-agent.md)、[安全策略](SECURITY.md)、[v0.1 → v0.2 迁移](docs/migrations/v0.1-to-v0.2.md)。
