# 5 分钟快速开始

目标：不安装依赖、不改客户端配置，先在隔离目录建立一套能运行、能重跑、能校验的 GitHub 入库、项目语义参考与能力冷库。

## 最简单：把仓库链接交给 Agent

```text
请用这个工作流仓库帮我建立“GitHub 项目入库 + 能力冷库 + 自动路由”：
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

先只读 AGENT-START.md，不扫描全仓库。
产物写到一个新的隔离目录，使用本机已有 Python，不安装依赖。
先初始化并运行 validate；如果我还给了一个待评价 GitHub 链接，再创建唯一候选卡。
安装、登录、外发、删除、修改客户端配置，以及项目/能力晋级前必须先问我。
```

如果你没有指定输出目录，Agent 只需要追问这一项。需要本地执行时，Agent 可以 clone 这份公开源码，但不能借机安装 Python、包或其他工具。

## Agent 实际执行的 3 条命令

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language zh-CN --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

Windows 上如果 `python` 不可用，但本机已有 `py`，可改用 `py -3`。macOS/Linux 可使用已有的 `python3`。三种都没有时停止并如实说明，不自动安装。

## 成功标准

- `workflow.json` 的 `schema_version` 为 `3`；
- 同一个 GitHub 链接重复处理仍只有一张项目卡；
- 项目卡、能力卡是事实源，索引、薄发现 + 完整语义表和能力路由由 CLI 生成；
- 只有经批准的 S/A/B `retained/reference` 项目进入薄发现表和完整语义表，且在两张表中各一行；
- 每条正式记录有一条唯一能力摘要、至少两条日常说法、命中级别和禁止命中条件；
- 有明确对象、动作或产物的任务会先查薄发现表；`gated` 项目先提醒，读取或执行仍需过门禁；
- `candidate/disabled/quarantine/retired` 能力不出现在薄路由；
- 每条能力明确记录部署范围；active 不能是 `not-installed`，reference 必须是 `not-installed`；
- B 级低风险可执行候选把当前项目第一次真实任务作为 T1，不建立长期 `project-trial` 状态；
- `.workflow/transactions/` 留下本次写入清单；
- `validate` 返回 `result: pass` 和 `errors: 0`；
- 没有自动安装、登录、外发、删除或修改客户端配置。

## 下一步

把一个待评价项目链接交给 Agent，让它先做轻量评估。Agent 可以补充项目卡里的公开证据，但不得执行目标仓库里的命令。准备晋级时，要同时补充唯一能力摘要、日常语义示例、命中级别和禁止命中边界；B 级命中后先判断任务增量，只有方法价值就不安装，低风险可执行候选完成 T0 并获得项目级安装批准后，当前项目第一次真实任务就是 T1。已有 schema v1/v2 工作流按 [v0.3 → v0.4 迁移](docs/migrations/v0.3-to-v0.4.md) 升级。

完整规则见 [AGENT-START.md](AGENT-START.md)；真实产物见 [自动生成演示](examples/generated-demo-v1/README.md)。
