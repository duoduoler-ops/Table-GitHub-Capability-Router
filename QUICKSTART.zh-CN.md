# 5 分钟快速开始

目标：不安装依赖、不改客户端配置，先在隔离目录建立一套能运行、能重跑、能校验的 GitHub 入库与能力冷库。

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

- `workflow.json` 的 `schema_version` 为 `1`；
- 同一个 GitHub 链接重复处理仍只有一张项目卡；
- 项目卡、能力卡是事实源，索引和路由由 CLI 生成；
- `candidate/disabled/quarantine/retired` 能力不出现在薄路由；
- `.workflow/transactions/` 留下本次写入清单；
- `validate` 返回 `result: pass` 和 `errors: 0`；
- 没有自动安装、登录、外发、删除或修改客户端配置。

## 下一步

把一个待评价项目链接交给 Agent，让它先做轻量评估。Agent 可以补充项目卡里的公开证据，但不得执行目标仓库里的命令。准备晋级、clone、安装或真实测试时，再按门禁单独确认。

完整规则见 [AGENT-START.md](AGENT-START.md)；真实产物见 [自动生成演示](examples/generated-demo-v1/README.md)。
