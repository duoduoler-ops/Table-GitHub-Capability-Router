# Customization Guide / 自定义指南

English | [中文](#中文)

The defaults in this starter kit are personal examples. You should change them before using the workflow seriously.

## 1. Paths

Replace all placeholders:

| Placeholder | Meaning |
| --- | --- |
| `{{VAULT_PATH}}` | Your Obsidian vault |
| `{{EXTERNAL_REPO_ROOT}}` | Where full GitHub clones live |
| `{{CAPABILITY_LIBRARY}}` | Where manifests, cold assets, and catalog files live |
| `{{TEST_LOG_DIR}}` | Where raw command logs live |

Recommended rule:

```text
Obsidian vault = notes, rules, templates, decisions
External repo root = cloned source code
Test log dir = raw logs
Capability library = manifests and controlled reusable assets
```

## 2. Goals and Weights

The example scoring model uses five goals:

| Goal | Example weight |
| --- | ---: |
| Productivity / workflow leverage | 25 |
| Project-building value | 25 |
| Career value | 20 |
| AI agent learning value | 20 |
| Content-production value | 10 |

These weights came from one person's situation. Change them.

Examples:

| User type | Suggested adjustment |
| --- | --- |
| Researcher | increase learning and citation quality |
| Builder | increase project-building and deployment value |
| Content creator | increase content-production value |
| Job seeker | increase career evidence and portfolio value |
| Teacher | increase teaching workflow and reusable material value |
| Business operator | increase productivity, risk, and repeatability |

Important: scores are only for comparing similar candidates. They should not automatically create S/A/B/C/D grades.

## 3. Evidence Gates

Customize the evidence needed for each decision.

Example:

| Decision | Suggested evidence |
| --- | --- |
| Keep as B reference | online check + clear reusable idea |
| Promote to A component | online check + T0 + T1 |
| Replace current tool | T2 same-scenario comparison + rollback path |
| Promote to S | repeated T3 real workflow use |
| Reject as D | clear hard blocker or unacceptable risk |

If a tool touches accounts, cookies, private files, payments, publishing, deployment, or deletion, require stronger preflight.

## 4. Capability Slots

Capability slots should describe work, not brand names.

Prefer:

```text
transcribe audio and produce timestamped text
```

Instead of:

```text
Whisper slot
```

This makes replacement decisions easier.

## 5. Status Model

For cold-storage assets, keep management, health, and risk separate.

Management:

```text
active / cold / disabled / reference / retired
```

Health:

```text
healthy / unverified / degraded / broken / missing
```

Risk:

```text
low / medium / high
```

Do not write "installed" as if it means "healthy", "safe", or "should be routed".

## 6. Project Distillation Pages

Decide where extracted knowledge should live before you start importing many projects.

Recommended mapping:

| Extracted knowledge | Destination |
| --- | --- |
| Repeatable process, checklist, prompt, or review rubric | Workflow pages |
| General idea, architecture, or mental model | Concept pages |
| Project-specific implementation lesson | Your own project pages |
| Evidence about the GitHub source itself | GitHub project card |
| Agent read scope and routing boundary | Capability/reference manifest |

Avoid one-project-one-distillation-page by default. Update an existing page when the new project strengthens an existing method. Create a new page only when the project introduces a reusable method that does not have a natural home yet.

## 7. Registry Scope

Your registry should stay small. It answers:

```text
What should the agent consider for this task right now?
```

It should include:

- base/direct option;
- current healthy core tools;
- a few high-value explicit tools;
- high-risk or broken tools only as warnings or blocks.

It should not include every project you ever bookmarked.

## 8. Language

You can run the vault in:

- English;
- Chinese;
- bilingual mode;
- domain-specific mixed language.

Keep commands, paths, API names, model names, and library names exact.

## 中文

这个 starter kit 里的默认值只是个人示例。正式使用前应该按你自己的目标修改。

## 1. 路径

替换所有占位符：

| 占位符 | 含义 |
| --- | --- |
| `{{VAULT_PATH}}` | 你的 Obsidian vault |
| `{{EXTERNAL_REPO_ROOT}}` | 完整 GitHub clone 的位置 |
| `{{CAPABILITY_LIBRARY}}` | manifest、冷库资产和 catalog 的位置 |
| `{{TEST_LOG_DIR}}` | 原始命令日志的位置 |

推荐规则：

```text
Obsidian vault = 笔记、规则、模板、决策
外部 repo 目录 = 完整源码 clone
测试日志目录 = 原始日志
能力库目录 = manifest 和受控可复用资产
```

## 2. 目标和权重

示例评分模型使用五个目标：

| 目标 | 示例权重 |
| --- | ---: |
| 提效 / 工作流杠杆 | 25 |
| 项目构建价值 | 25 |
| 求职价值 | 20 |
| AI Agent 学习价值 | 20 |
| 内容生产价值 | 10 |

这些权重来自某个具体个人阶段。你应该改掉它们。

示例：

| 使用者类型 | 建议调整 |
| --- | --- |
| 研究者 | 提高学习价值和引用质量权重 |
| 项目构建者 | 提高项目构建和部署价值 |
| 内容创作者 | 提高内容生产价值 |
| 求职者 | 提高求职证据和作品集价值 |
| 教师 | 提高教学流程和可复用材料价值 |
| 业务经营者 | 提高提效、风险和可重复性权重 |

重要：分数只用于比较同类候选，不应该自动生成 S/A/B/C/D。

## 3. 证据门槛

你可以自定义每种决策需要什么证据。

示例：

| 决策 | 建议证据 |
| --- | --- |
| 保留为 B reference | 联网核查 + 明确可复用想法 |
| 升级为 A 组件 | 联网核查 + T0 + T1 |
| 替换当前工具 | T2 同场景比较 + 回滚方案 |
| 升级为 S | 真实 T3 工作流中反复产生价值 |
| 判为 D | 明确硬阻断或不可接受风险 |

如果工具会触碰账号、Cookie、私有文件、支付、发布、部署或删除，必须要求更强 preflight。

## 4. 能力槽

能力槽应该描述工作，而不是品牌名。

推荐：

```text
转录音频并输出带时间戳文本
```

不要写成：

```text
Whisper 槽
```

这样以后判断替换关系会更容易。

## 5. 状态模型

冷库资产要把管理状态、健康状态和风险分开。

管理状态：

```text
active / cold / disabled / reference / retired
```

健康状态：

```text
healthy / unverified / degraded / broken / missing
```

风险：

```text
low / medium / high
```

不要把“已安装”直接写成“健康、安全、应该调用”。

## 6. 项目提炼页

开始大量导入项目前，先决定提炼出来的知识应该放在哪里。

推荐映射：

| 提炼出的知识 | 放置位置 |
| --- | --- |
| 可重复流程、检查清单、提示词或审稿标准 | 工作流页 |
| 通用想法、架构或思维模型 | 概念页 |
| 只和某个自有项目有关的实现经验 | 你的项目页 |
| GitHub 来源本身的证据 | GitHub 项目卡 |
| Agent 的读取范围和路由边界 | 能力或 reference manifest |

默认不要变成“一个项目一个提炼页”。如果新项目只是强化已有方法，就更新已有页面。只有项目带来了一个没有自然归属的新方法，才新建提炼页。

## 7. Registry 范围

Registry 应该很薄。它回答：

```text
当前任务里，Agent 应该考虑什么？
```

它应该包含：

- 直接用模型 / 不调用额外能力；
- 当前健康的核心工具；
- 少量高价值显式工具；
- 高风险或异常工具只作为门禁或警告。

它不应该包含你收藏过的所有项目。

## 8. 语言

你的 vault 可以使用：

- 英文；
- 中文；
- 中英双语；
- 领域混合语言。

命令、路径、API 名、模型名和库名要保持精确。
