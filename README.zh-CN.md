# GitHub 项目入库 + 能力冷库 + 自动路由

这套工具帮你整理收藏的 GitHub 项目，让 Agent 做任务时能找到合适的工具，并查到它们之前的使用结果。

收藏链接后，Agent 按流程补充公开资料、判断项目价值，再决定留作参考还是申请安装。脚本负责把这些决定和使用结果记下来，更新索引，并检查记录是否一致。Skill、Plugin、MCP、CLI、脚本和方法参考都可以纳入这套流程。

[仓库首页](README.md) | [English](README.en.md) | [5 分钟开始](QUICKSTART.zh-CN.md)

## v0.5.0 新增：证据与使用闭环

**当前版本为 [v0.5.0](https://github.com/duoduoler-ops/Table-GitHub-Capability-Router/releases/tag/v0.5.0)**。下载这个版本的源码，即可使用下面介绍的新增功能：

- **写入更稳**：写草稿时记录原文件哈希，正式记录变了就先合并，避免旧稿盖掉新内容。失败恢复会保留其他人的并发修改。
- **每次使用有记录**：开始前登记，结束后写明验收结果，以及临时安装、启用等后续事项是否处理完。中途停下也能查到待办。
- **旧证据可以复核**：把检查结果关联到客户端、版本、明确列出的文件和项目。版本或文件变化、证据过期、出现后续失败或未完成使用时，要求重新确认。
- **补上检查和提醒**：Git Hook 检查真正暂存的内容；可选客户端 Hook 检查未完成使用。Windows 和 Linux CI 负责运行测试和仓库检查。

证据扩展保留 Vault schema v3，新增 JSON 记录用独立的 version 1 格式。它记录调用方报告的结果，不替你测试或自动启用工具。详见 [使用说明](docs/capability-lifecycle.md)、[虚构演示](examples/lifecycle-demo.py)和 [Hook 接入说明](docs/optional-lifecycle-hooks.md)。

## 当前维护宿主

当前主要维护 **Grok Build 和 Codex**，共用 `.agents/skills/github-vault-router/` 项目 Skill。Claude Code 保留 `.claude/skills/github-vault-router/` 兼容入口。

`AGENTS.md` 保存规则正文，`CLAUDE.md` 只指向它，维护时不用同步两份规则。项目 Skill 能否被发现、工具能否调用，要查看当前会话实际提供的能力；不能只看文件是否存在。

## 版本重点

这里保留每版重点，完整变更见 [CHANGELOG.md](CHANGELOG.md)。

| 版本 | 重点 | 用起来有什么变化 |
| --- | --- | --- |
| v0.5.0 | 写入保护、使用证据和可选 Hook | 旧稿覆盖会被拦截；每次使用可追踪，旧证据可复核，未完成事项可检查 |
| v0.4.0 | 分开记录等级和安装范围 | B 级项目先判断是否有帮助，获批后在当前项目验证，完成真实任务后再决定是否保留 |
| v0.3.0 | 先查已有项目 | 先看简短能力表，命中后再读使用条件 |
| v0.2.0 | 用脚本维护资料 | 增加入库、重建、校验、备份和按任务找项目的规则 |
| v0.1.0 | 提供起步模板 | 双语模板、入库提示词和公开示例 |

## v0.4.0 新增内容

- 项目等级、安装范围、管理状态、健康情况和调用方式分别记录。A 级能力也可以只装在当前项目里。
- B 级项目只有方法价值时，保留为 `reference`，供阅读参考。
- 低风险可执行项目先做初步检查（T0），取得项目级安装批准后，用当前项目的第一次真实任务验证（T1）。
- T1 通过后，按审批流程登记为 A/retained 和 active/project；失败或结论不清时保持 B/reference，并提出卸载建议。真正卸载仍需确认。
- `migrate-v3` 要求说明每项能力装在哪里；`capability-deployment` 只记录已经发生的部署事实。
- Grok Build 和 Codex 共用项目 Skill，Claude Code 保留兼容入口。
- 不增加长期挂着的 `project-trial` 状态。涉及高权限、真实凭据、外部写入或难以回退等情况时，先隔离验证；完整条件见 [Agent 入口](AGENT-START.md)。

## v0.3.0 新增内容

| 新增内容 | 解决什么问题 |
| --- | --- |
| 具体任务先查简表 | 先看看库里有什么，减少收藏后忘记使用 |
| 简表和详细表分开 | 先选最相关的一项，再读适用示例和排除条件 |
| `gated` 项目先提醒 | 可以先知道项目存在，后续读取和执行再按权限处理 |
| 独立能力摘要 | 用一句“做什么、得到什么”区分项目，重复摘要会被拦截 |
| 升级时补齐摘要 | 当时通过 `migrate-v2` 升级；当前 CLI 统一使用 `migrate-v3` |
| 保留直接完成的方案 | 可以用现有工具直接做，也可以只参考资料，确需运行时再决定是否安装 |

## v0.2.0 新增内容

| 新增内容 | 解决什么问题 |
| --- | --- |
| 无第三方依赖的 Python 命令 | 入库、更新、重建和校验有统一做法 |
| 固定记录格式 | ID、地址、状态和批准信息可以相互核对 |
| 按任务找参考项目 | 日常说法也能对应到相关的已保留项目 |
| 适用示例和排除条件 | 说明什么时候推荐、什么时候不该推荐 |
| 一致性校验和可选提交检查 | 找出遗漏、重复、资格错误和过期生成表 |
| 客户端接入入口 | 规则集中管理，保留不同客户端的调用方式 |
| 可选只读能力盘点 | 查看能力目录和客户端支持情况 |
| 写入备份与恢复 | 增加锁、备份、逐文件替换、失败恢复和历史隐私扫描 |

> 历史说明：v0.3.0 允许先提醒 `gated` 项目存在，后续操作仍需按权限处理。v0.4.0 延续这一做法，增加首次真实使用后的处理流程。

## 最短使用方式

把下面这段复制给 Grok Build、Codex，或其他能读 GitHub、能操作本地文件的 Agent：

```text
请用这个仓库帮我建立“GitHub 项目入库 + 能力冷库 + 自动路由”：
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

先只读仓库根目录的 AGENT-START.md，按其中流程执行。
把产物放在一个新的独立目录；使用本机已有 Python，不安装依赖。
初始化工作流，生成第一条候选项目记录，再运行校验。
安装、登录、对外发布、删除、修改客户端配置前，必须先问我。
```

Agent 可以把这份工作流源码 clone 到独立目录，在本地执行命令。缺少输出位置时，它会先询问产物放在哪里。

## 初始化后得到什么

```text
<OUTPUT_DIR>/
├─ AGENT-ROUTER.md              # 给 Agent 看的简短入口
├─ workflow.json               # 路径、客户端和路由配置
├─ projects/records/           # GitHub 项目卡
├─ capabilities/records/       # 能力记录
├─ indexes/                    # 自动生成的索引和项目推荐表
├─ router/level1-router.md     # 自动生成的能力路由
├─ logs/maintenance-log.md     # 维护事件
└─ .workflow/transactions/     # 写入记录和修改前备份
```

启用可选使用记录后，会按需增加 `.workflow/lifecycle/`，保存证据、使用回执和 Hook 提醒缓存。初始化本身不会安装或启用客户端 Hook。

## 它自动做什么

- 同一个 GitHub 地址对应同一条记录，重复入库不会再建一份。
- 新项目先标为候选、未评级、未验证；新能力先标为候选、未验证、未安装、仅点名调用。
- 状态变更按固定规则检查。等级、安装范围、健康和调用方式各自记录，避免混为一谈。
- 候选、禁用、隔离和退役能力不进入路由。通过 `capability-health` 登记 active 能力健康降级后，该记录会被隔离并移出路由；客户端中的真实工具仍需另行处理。
- 总管型能力有单独标记，不能设置为自动调用。
- 写入前加锁、检查文件、备份，再逐个替换；失败时尝试恢复。发现并发修改或备份异常时保留现场，标记为需要恢复。
- 索引、候选池、否决记录和路由从原始记录重建。
- 经批准保留为 `retained/reference` 的 S/A/B 项目进入推荐表；每项要求独立摘要、至少两条日常说法、触发条件和不适用情况。
- 按命令检查重复 ID、状态组合、生成表是否过期、相对链接，以及当前文件和本地 Git 历史中的敏感信息模式。
- 可选使用记录支持重复请求去重、未完成事项查询，以及旧证据是否仍适用的只读检查。

断电或强制结束进程可能留下未完成写入，需要人工核对。完整规则见 [写回协议](docs/write-protocol.md)。

## 它故意不自动做什么

- 不替你判断外部证据是否可信，也不把目标仓库里的文字当成执行指令。
- 不自动 clone、安装或运行被评估项目；按权限和明确批准执行实际操作。
- 不自动登录账号、对外发布、删除数据或修改客户端配置。
- 不把记录中的 `active` 当作客户端已启用，也不把旧的“健康”描述当成新任务通过。
- 不从一次成功记录直接升级等级、修改健康状态或扩大安装范围。
- 不靠 Hook 发现从未登记的工具使用，也不自动完成验收和后续处置。

## 常用命令

在源码目录执行，将占位符换成实际值。核心命令需要已有 Python 3；Windows 可用 `py -3` 替换 `python`，macOS/Linux 可用已有的 `python3`。

```powershell
# 建立独立的工作流目录
python scripts/workflow.py init --root <OUTPUT_DIR> --language zh-CN --client grok-build

# 创建项目记录；同一个地址不会重复入库
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>

# 经批准后，把项目留作参考，并说明适用情况
python scripts/workflow.py project-transition --root <OUTPUT_DIR> --id <PROJECT_ID> --to reference --grade B --approved `
  --capability-summary "比较已保存的项目并输出一份可复用参考建议" `
  --semantic-example "帮我找一个可复用的参考工作流" `
  --semantic-example "现有哪个 GitHub 项目能改善这个任务" `
  --trigger-level gated `
  --negative-routing "普通直接回答或方案已经确定时不命中"

# 创建能力候选
python scripts/workflow.py new-capability --root <OUTPUT_DIR> --id <ID> --name <NAME> --type <TYPE> --route-category <CATEGORY>

# 已另行获批并完成安装后，登记实际安装范围
python scripts/workflow.py capability-deployment --root <OUTPUT_DIR> --id <ID> --to project --evidence "已批准并完成当前项目安装" --approved

# 重建索引和路由，再检查记录
python scripts/workflow.py rebuild --root <OUTPUT_DIR>
python scripts/workflow.py validate --root <OUTPUT_DIR>

# 只读查看未完成的使用记录
python scripts/workflow.py lifecycle-status --root <OUTPUT_DIR>
```

已有 schema v1/v2 数据使用 `migrate-v3`，为每项能力提供真实安装范围；从 v1 直接升级还需补齐正式项目摘要。示例和参数见 [迁移说明](docs/migrations/v0.3-to-v0.4.md)。已有 v3 数据更新源码后运行 `rebuild` 和 `validate` 即可刷新指引。

修改正文前，先运行 `record-hash` 保存原记录哈希；`update-project` 和 `update-capability` 写回时必须带 `--expected-sha256`。旧脚本需要补这个参数，不能直接用新哈希提交旧稿。完整步骤见 [写回协议](docs/write-protocol.md)。

新增使用命令按这个顺序配合实际任务：

| 命令 | 作用 |
| --- | --- |
| `record-evidence` | 记录调用方已完成的发现或轻量检查结果 |
| `capability-check` | 使用前只读检查已有证据是否适用 |
| `use-begin` | 在已经获批的实际使用前登记一次使用 |
| `use-finish` | 写明验收是否通过，后续事项是否处理完 |
| `lifecycle-status` | 查找未完成记录，中断后从原记录继续处理 |

客户端和能力版本由调用方核实后提供；脚本实读明确列出的文件并计算哈希。未列出的文件变化不会被发现。复核还会检查项目与文件位置、证据时效、后续失败记录和未完成使用，默认有效期 30 天。轻量检查通过不等于真实任务验收通过；两者都不替代当前客户端可用性检查和操作批准。详见 [身份文件与完整命令](docs/capability-lifecycle.md)。

## 项目语义命中的真实边界

“语义命中”就是用任务的意思找项目，不要求用户说出项目名。`indexes/project-semantic-routing.md` 前面是简表，后面是详细条件。Agent 每开始一种具体产物，先查一次简表，最多选择一个相关项目，再读它的详细行。

- `high_confidence`：任务明显相关时可以先提醒。
- `gated`：也可以先提醒；后续读取和执行受权限约束。
- `explicit_only`：用户点名或明确要求时才建议。

推荐时保留用现有工具直接完成的方案。用户选择参考项目后再按权限读取最少的资料，确需运行时再决定是否安装或启用。一次推荐不会自动授权后续操作。

## 可选只读能力审计

PR #1 提供独立的能力盘点入口，当前覆盖 Grok Build、Codex、Claude Code、Kimi Code 和通用 Agent。它查看 Skill、Plugin、MCP、Hook 和规则的可见情况，不修改文件或配置。此功能需要已有 Node.js。

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

盘点到入口不等于当前会话能调用。感谢 [@Calvingen3](https://github.com/Calvingen3) 的最初贡献。详见 [能力盘点说明](docs/optional-capability-optimizer.md)。

## 自动调用的真实边界

仓库提供 Grok Build / Codex 的共享项目 Skill、Claude Code 兼容入口，以及生成后的路由。Agent 打开仓库后，能否按任务发现这些入口，取决于客户端机制。把路由长期接入其他项目或全局配置，需要使用者批准。

新增 Hook 分两类，默认都不自动安装或启用：

| 类型 | 适合放在这里做的事 | 接入边界 |
| --- | --- | --- |
| Git pre-commit | 提交前检查实际暂存的文件，拦截遗漏、无效链接等问题 | 启用会修改 Git 配置，需要批准；完整测试由 CI 补充 |
| 客户端 SessionStart / Stop | 开始或结束时检查已登记的未完成使用 | 接入前确认项目范围、配置和信任状态，接入后验证真实触发 |

Codex 可以在开始时加入待办上下文，结束时显示界面提醒。Grok Build 默认只保存本地待办文件，不能说模型已经收到提醒；显式选择 `--grok-feedback` 后，结束时才会请求一次继续处理，并增加模型用量。

适配器和输入样例已有测试，实际客户端中的启用、信任和触发尚需接入验证。Hook 不执行目标工具、不做后台体检、不自动结算，也看不到从未登记的使用。恢复时可主动运行 `lifecycle-status`。见 [提交前 Hook](docs/optional-pre-commit.md)与 [客户端 Hook](docs/optional-lifecycle-hooks.md)。

## 视频教程

- [上集 · 你收藏的 GitHub 神器，真的值得装吗](https://www.youtube.com/watch?v=c4d23apzOEY)
- [下集 · 这个仓库背后的 Agent 能力冷库工作流](https://www.youtube.com/watch?v=juIsuIy55mQ)
- [进阶篇](https://www.youtube.com/watch?v=k7S5ewLaMVI&t=16s)

## 验证与演示

[自动生成演示](examples/generated-demo-v1/README.md)由 CLI 生成，包含 2 个虚构项目、3 个虚构能力，以及索引、路由、维护日志和写入记录。[使用记录演示](examples/lifecycle-demo.py)展示成功、文件变化、失败和中断。这些示例不安装或测试真实工具。

```powershell
python -m unittest discover -s tests -v
node --test integrations/optimize-agent-capabilities/tests/audit.test.mjs
python scripts/workflow.py validate --root examples/generated-demo-v1
python scripts/workflow.py validate-repo
python scripts/workflow.py validate-staged --root .
```

Windows 和 Linux CI 会运行测试、演示、独立目录中的入门流程，以及仓库和暂存区检查。结果以 [GitHub Actions](https://github.com/duoduoler-ops/Table-GitHub-Capability-Router/actions) 对应提交为准。`validate` 通过说明资料结构和关联一致；实际工具今天能否工作，需要另外验证。

进一步阅读：[状态机](docs/state-machine.md)、[写回协议](docs/write-protocol.md)、[客户端配置边界](docs/client-profiles/generic-agent.md)、[安全策略](SECURITY.md)、[v0.1 → v0.2 迁移](docs/migrations/v0.1-to-v0.2.md)、[v0.2 → v0.3 迁移](docs/migrations/v0.2-to-v0.3.md)、[v0.3 → v0.4 迁移](docs/migrations/v0.3-to-v0.4.md)。采用 [MIT License](LICENSE)。
