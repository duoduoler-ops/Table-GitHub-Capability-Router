---
schema_version: {{SCHEMA_VERSION}}
record_type: github-project
id: {{PROJECT_ID}}
revision: {{REVISION}}
status: {{PROJECT_STATUS}}
grade: {{PROJECT_GRADE}}
canonical_url: {{CANONICAL_URL}}
evidence_level: {{EVIDENCE_LEVEL}}
capability_summary: {{CAPABILITY_SUMMARY}}
semantic_examples: {{SEMANTIC_EXAMPLES}}
trigger_level: {{TRIGGER_LEVEL}}
negative_routing: {{NEGATIVE_ROUTING}}
updated_at: {{UPDATED_AT}}
---

# GitHub Project Card / GitHub 项目卡

## Basic Info / 基本信息

- Stable ID / 稳定 ID: {{PROJECT_ID}}
- GitHub: {{CANONICAL_URL}}
- Check date / 核查日期: {{CHECK_DATE}}
- Version or commit / 版本或 commit:
- Evaluation mode / 评价模式: lightweight / full / install test
- Project type / 项目类型:
- Asset role / 资产角色: method-reference / executable-candidate / retained-component
- Capability chain / 能力链:
- Capability summary / 能力摘要: see `capability_summary` in frontmatter; use one distinct verb + object + output sentence / 见 frontmatter；使用一条可区分的“动词 + 对象 + 产物”句子
- Distillation page / 提炼页:
- Canonical status, grade, and evidence / 权威状态、等级与证据: see frontmatter; do not duplicate mutable state here / 见 frontmatter，不在正文重复可变状态

## Semantic Reference Routing / 项目语义命中

Only `retained` and `reference` projects with grade S/A/B may enter the generated discovery and semantic tables. Supply one distinct capability summary, at least two ordinary-language examples, one trigger level, and a clear negative-routing boundary during promotion. Candidate, rejected, archived, C, and D projects remain `none / none / explicit_only / none`.

只有 S/A/B 且状态为 `retained` 或 `reference` 的项目可以进入生成的薄发现表与完整语义表。晋级时必须填写一条可区分的能力摘要、至少两条日常说法、一个命中级别和明确的禁止命中边界。候选、否决、归档、C/D 项目保持 `none / none / explicit_only / none`。

- Capability summary / 能力摘要（唯一一句话，动词 + 对象 + 产物）:
- Everyday wording / 用户日常说法（至少两条）:
- Trigger level / 命中级别: high_confidence / gated / explicit_only（high_confidence 与 gated 都先提醒；gated 只限制后续读取或执行）
- Do not route or prefer another path / 禁止命中或优先分流:
- Visible increment over the normal approach / 相比普通方案的可见增量:
- When matched, propose normal vs project-informed routes / 命中后是否提供普通方案与项目方案对比:

## B-Grade Task Increment Gate / B 级任务增量闸门

Use this section whenever a B-grade project matches a real task. Judge the increment from this card first; refresh only the current facts needed for safety or compatibility. Do not repeat a full repository survey by default.

B 级项目命中真实任务时填写本节。先根据项目卡判断增量；只有安全、版本或兼容性可能变化时才补充当前核查，不默认重做完整联网调研。

- Ordinary route / 不调用额外项目的普通方案:
- Expected increment / 预计增量:
- Evidence source / 判断依据: current card / targeted current check
- Decision / 判断: method-only reference / executable candidate / no useful increment
- Minimum files to read / 最小读取范围:
- T0 safety result / T0 安全结论: no obvious risk found in checked scope / isolation required / stop
- Isolation reason if required / 如需隔离，原因:

## First Real Use Settlement / 第一次真实使用结算

For a low-risk executable B candidate, ask before project-level installation. The current project's first real task is T1; do not create a separate demo or durable `project-trial` state by default.

低风险 B 级可执行候选先询问是否安装到当前项目。当前项目里的第一次真实任务就是 T1；默认不额外制作 Demo，也不建立长期 `project-trial` 状态。

- Capability record / 对应能力记录:
- Approved deployment scope / 已批准部署范围: not-installed / project / user / global / external-service
- T1 real task / T1 真实任务:
- Outcome / 结果: passed / failed / inconclusive / not-run
- Success settlement / 成功结算: grade A + retained project + active capability at project scope
- Failure settlement / 失败结算: remain B/reference; recommend uninstall and wait for deletion confirmation
- Actual removal confirmed / 是否已确认并完成删除: yes / no / not applicable

## 30-Second Positioning / 30 秒定位

- It replaces / 它替代:
- It enhances / 它增强:
- It produces / 它产出:
- Next 30-day use case / 未来 30 天使用场景:
- If B reference, reusable takeaway / 若为 B reference，提炼产物:
- Distillation destination / 提炼落点: workflow / concept / own project / none

## Quick Rejection / 快速否决

| Check / 检查项 | Result / 结果 | Evidence / 证据 |
| --- | --- | --- |
| Clear input and output / 输入输出是否清楚 |  |  |
| Unacceptable duplication / 是否不可接受重复 |  |  |
| License acceptable / License 是否可接受 |  |  |
| Only vision, no verifiable output / 是否只有愿景 |  |  |
| Security and privacy acceptable / 安全和隐私是否可接受 |  |  |
| Cost higher than value / 成本是否高于价值 |  |  |

## Current Alternatives / 当前替代方案

- Base model / 模型本身:
- Current agent capability / 当前 Agent 能力:
- Local tools / 本机工具:
- Existing vault project / vault 已有项目:
- No-extra-tool option / 不调用额外工具:

## Comparison / 同类比较

| Candidate / 候选 | Advantage / 优势 | Limitation / 限制 | Evidence / 证据 | Fit / 适配判断 |
| --- | --- | --- | --- | --- |
| Current solution / 当前方案 |  |  |  |  |
| This project / 本项目 |  |  |  |  |
| Alternative 1 / 同类方案 1 |  |  |  |  |
| Alternative 2 / 同类方案 2 |  |  |  |  |

## Evidence / 证据

| ID | Type / 类型 | Fact / 事实 | Source / 来源 | Supports / 支撑 |
| --- | --- | --- | --- | --- |
| E1 | author claim / online check / static check / T0 / T1 / T2 / T3 |  |  |  |

## Optional Scoring / 可选评分

Change these weights for your own goals. Do not let the total score automatically decide S/A/B/C/D.

根据你自己的目标修改权重。不要让总分自动决定 S/A/B/C/D。

| Dimension / 维度 | Weight / 权重 | Score 0-5 / 评分 | Evidence / 证据 |
| --- | ---: | ---: | --- |
| Productivity / 提效 | 25 |  |  |
| Project building / 项目构建 | 25 |  |  |
| Career / 求职 | 20 |  |  |
| Agent learning / Agent 学习 | 20 |  |  |
| Content production / 内容生产 | 10 |  |  |

## Test Plan / 测试计划

- Stage / 阶段: T0 / T1 / T2 / T3
- Timebox / 时间盒:
- Test sample / 测试样本:
- Current baseline / 当前基线:
- Metrics / 指标:
- Pass criteria / 通过标准:
- Exit plan / 失败退出方式:
- Rollback / 回滚方式:
- Summary path / 摘要路径:
- Raw log path / 原始日志路径:

T1 means the first real task in the approved current project, not an isolated one-sample smoke test. Use isolation only for elevated permissions, real credentials, external writes, background services, heavy caches, unclear source/license/rollback, or tools with no project-level installation path.

T1 指获批当前项目里的第一次真实任务，不是隔离目录中的单样本冒烟。只有涉及高权限、真实凭据、外部写入、后台服务、重缓存、来源/License/回滚不清，或根本没有项目级安装方式时才要求隔离。

## Knowledge Distillation / 知识提炼

Use this section only when the project creates reusable knowledge. Prefer updating an existing workflow, concept, or project page. Create a new distillation page only when the method has no natural home yet.

仅当项目产出可复用知识时填写本节。优先更新已有工作流页、概念页或项目页。只有方法没有自然归属时，才新建提炼页。

- Reusable method / 可复用方法:
- Existing page to update / 优先更新页面:
- New page if needed / 必要时新建页面:
- Backlink from project card / 项目卡反链:
- Backlink from distillation page / 提炼页反链:
- Related capability-slot row / 相关能力槽行:
- Reference manifest / reference manifest:
- Do not duplicate here / 不在此处重复:

## Cold-Storage Decision / 冷库处置

- Asset type / 资产形态: runtime / skill / plugin / mcp-config / script / reference / source-pointer
- Deployment scope / 部署范围: not-installed / project / user / global / external-service（写入能力记录，不拼进等级或管理状态）
- Management / 管理状态: active / cold / disabled / reference / retired
- Health / 健康状态: healthy / unverified / degraded / broken / missing
- Risk / 风险: low / medium / high
- Manifest / manifest:
- Activation / 激活方式:
- Health check / 健康检查:
- Disable and rollback / 停用和回滚:
- Registry eligibility / Registry 资格:
- If reference, read scope / 若为 reference，最小读取范围:

## Decision / 结论

- Grade / 等级:
- Why / 理由:
- Keep, combine, challenge, replace, or reject / 保留、互补、挑战、替换或否决:
- Review trigger / 复查触发条件:
- Next smallest step / 最小下一步:
