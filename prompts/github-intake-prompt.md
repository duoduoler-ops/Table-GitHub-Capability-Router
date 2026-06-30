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

