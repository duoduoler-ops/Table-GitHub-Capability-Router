---
schema_version: {{SCHEMA_VERSION}}
record_type: capability
id: {{CAPABILITY_ID}}
revision: {{REVISION}}
management_state: {{MANAGEMENT_STATE}}
health_state: {{HEALTH_STATE}}
deployment_scope: {{DEPLOYMENT_SCOPE}}
risk: {{RISK}}
invocation: {{INVOCATION}}
authorization: {{AUTHORIZATION}}
manager_type: {{MANAGER_TYPE}}
route_category: {{ROUTE_CATEGORY}}
updated_at: {{UPDATED_AT}}
---

# Capability Manifest / 能力冷库 Manifest

## Basic Info / 基本信息

- Capability ID / 能力 ID: {{CAPABILITY_ID}}
- Name / 名称: {{CAPABILITY_NAME}}
- Type / 类型: {{CAPABILITY_TYPE}}
- Platform / 平台: Grok Build / Codex / Claude Code / Shared / Other
- Source / 来源:
- Version or commit / 版本或 commit:
- Related project grade / 相关项目等级: S / A / B / C / N/A
- Related project card / 相关项目卡:
- Distillation page / 提炼页:
- Capability slot / 能力槽:

## Storage Decision / 冷库处置

- Asset form / 资产形态: runtime / skill / plugin / mcp-config / script / reference / source-pointer
- Canonical state / 权威状态: see frontmatter; do not duplicate mutable state here / 见 frontmatter，不在正文重复可变状态
- Deployment scope / 部署范围: see `deployment_scope` in frontmatter: not-installed / project / user / global / external-service
- Risk / 风险: {{RISK}}
- Manager type / 是否总管型: see `manager_type` in frontmatter / 见 frontmatter 的 `manager_type`
- Quarantine / 隔离: true / false
- Canonical path / canonical 路径:
- Source pointer / 源码指针:
- Dependencies / 依赖:
- Duplicate group / 重复组:

## Routing / 路由

- Trigger condition / 触发条件:
- Do-not-use condition / 禁用条件:
- Need gate / 是否必须额外能力:
- Alternatives / 替代方案:
- Registry entry / Registry 条目:
- If reference, minimum read scope / 若为 reference，最小读取范围:
- If reference, pages to read first / 若为 reference，优先读取页面:
- If reference, pages not to read by default / 若为 reference，默认不读取页面:

## Activation / 激活

- B-candidate gate / B 级候选闸门: method-only reference / executable candidate
- T0 safety boundary / T0 安全边界:
- Approved first-use project / 已批准首次使用项目:
- T1 real-task outcome / T1 真实任务结果: not-run / passed / failed / inconclusive
- Settlement / 结算: retain as A + project / stay B and recommend uninstall / not applicable
- Activation method / 激活方式:
- Refresh, new session, or restart / 刷新、新会话或重启要求:
- Health check / 健康检查:
- Disable method / 停用方式:
- Rollback method / 回滚方式:

## Verification / 验证

- Test summary / 测试摘要:
- Raw log / 原始日志:
- Latest verification / 最近验证:
- Recheck trigger / 复查条件:
- Lifecycle note / 生命周期说明: grade, deployment scope, management state, health, and invocation are separate axes; never create a `project-trial` state / 等级、部署范围、管理状态、健康和调用方式相互独立；不创建 `project-trial` 状态

## Security / 安全

- License / License:
- Permission scope / 权限范围:
- Credentials involved / 是否涉及凭据:
- Privacy check / 脱敏检查:
- Side effects / 外部副作用:

## Notes / 备注
