# GitHub Intake Prompt / GitHub 项目入库提示词

## English

```text
Open {{VAULT_PATH}}.

Read:
- the vault rules;
- the GitHub project-intake workflow;
- the capability-slot index;
- the GitHub project-card template.

Evaluate the GitHub project below in lightweight mode.

Rules:
- Use current online evidence.
- Compare it with the base model, current agent capabilities, local tools, existing vault projects, and 1-2 similar alternatives.
- Do not clone, install, run scripts, import cookies, use API keys, or modify global config.
- Do not give S/A in lightweight mode unless the vault rules explicitly allow it.
- Capability duplication is not an automatic rejection. Decide whether the project keeps, complements, challenges, replaces, or falls back from the current solution.
- Scores are optional and only compare similar candidates. They do not automatically decide S/A/B/C/D.

Write back:
- create or update the project card;
- update the candidate/rejection/index page as needed;
- add a short maintenance-log entry;
- if it becomes S/A/B, write the cold-storage decision.

Project URL:
<paste URL here>
```

## Existing Capability Intake / 已有能力筛查入库

```text
Open {{VAULT_PATH}}.

Read:
- the capability cold-storage workflow;
- the capability manifest template;
- the registry rules;
- the capability-slot index.

Screen the existing capability below.

Rules:
- Do not enable new permissions.
- Do not modify global configuration.
- Do not install, update, or run unknown scripts.
- Treat "do not use extra capability" as a valid routing option.
- Separate management status, health status, and risk.
- Do not mark an installed capability as healthy unless a real health check supports it.
- Keep large logs, runtimes, caches, and full source clones outside the Obsidian vault.

Write back:
- create or update the capability manifest;
- decide whether it is active, cold, disabled, reference, or retired;
- decide whether it should enter the thin registry;
- update the relevant index;
- add a short maintenance-log entry if the status changed.

Capability name or path:
<paste Skill / Plugin / MCP / script / CLI name or path here>
```

## 中文

```text
打开 {{VAULT_PATH}}。

先阅读：
- vault 使用规则；
- GitHub 项目入库流程；
- 能力槽索引；
- GitHub 项目卡模板。

请对下面这个 GitHub 项目做轻量评估。

规则：
- 使用当前联网证据。
- 和模型本身、当前 Agent 能力、本机工具、vault 已有项目、1-2 个同类方案比较。
- 不要 clone，不要安装，不要运行脚本，不要导入 Cookie，不要使用 API Key，不要修改全局配置。
- 轻量评估阶段不要直接给 S/A，除非 vault 规则明确允许。
- 能力重复不等于自动淘汰。必须判断它是保留现有、互补组合、挑战者测试、替换现有，还是回退轻量方案。
- 评分是可选项，只用于同类候选比较，不能自动决定 S/A/B/C/D。

写回：
- 创建或更新项目卡；
- 按需要更新候选池、否决记录或索引页；
- 追加一条简短维护日志；
- 如果成为 S/A/B，写明冷库处置。

项目 URL：
<在这里粘贴 URL>
```

## 已有能力筛查入库

```text
打开 {{VAULT_PATH}}。

先阅读：
- 能力冷库流程；
- 能力 manifest 模板；
- Registry 规则；
- 能力槽索引。

请筛查下面这个已有能力。

规则：
- 不要启用新权限。
- 不要修改全局配置。
- 不要安装、更新或运行未知脚本。
- “不调用额外能力”也是合法路由候选。
- 管理状态、健康状态和风险要分开记录。
- 不能因为某个能力“已安装”就把它写成 healthy，必须有真实健康检查证据。
- 大体积日志、运行时、缓存和完整源码 clone 不要放进 Obsidian vault。

写回：
- 创建或更新能力 manifest；
- 判断它应该是 active、cold、disabled、reference 还是 retired；
- 判断它是否应该进入薄 Registry；
- 更新相关索引；
- 如果状态发生变化，追加一条简短维护日志。

能力名称或路径：
<粘贴 Skill / Plugin / MCP / 脚本 / CLI 名称或路径>
```
