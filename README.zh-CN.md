# GitHub 项目入库 + 能力冷库 + 自动路由

这套仓库的目标很直接：你把一个 GitHub 链接交给 Agent，Agent 不再只在聊天里随口评价，而是把它变成可追踪的项目记录；如果项目能沉淀成 Skill、Plugin、MCP、CLI、脚本或方法论，再进入能力冷库和薄路由。

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
├─ indexes/                     # 自动生成的项目索引
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

# 创建能力候选
python scripts/workflow.py new-capability --root <OUTPUT_DIR> --id <ID> --name <NAME> --type <TYPE> --route-category <CATEGORY>

# 从事实源重建索引和路由
python scripts/workflow.py rebuild --root <OUTPUT_DIR>

# 验证整个工作流
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

状态变更命令和审批参数见 [Agent 唯一入口](AGENT-START.md) 与 [状态机](docs/state-machine.md)。

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
python scripts/workflow.py validate --root examples/generated-demo-v1
python scripts/workflow.py validate-repo
```

进一步阅读：[写回协议](docs/write-protocol.md)、[客户端配置边界](docs/client-profiles/generic-agent.md)、[安全策略](SECURITY.md)、[迁移说明](docs/migrations/0001-initial-schema.md)。
