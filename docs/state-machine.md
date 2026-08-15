# State Machine / 状态机

English | [中文](#中文)

## Project records

Canonical project records use a stable `gh-owner-repo` ID and one of these states:

```text
candidate -> evaluated -> retained -> reference -> archived
    |            |            |          |
    +----------> rejected      +----------+
rejected -> candidate (re-evaluation)
archived -> candidate (re-open)
```

Invariants:

- `retained` requires grade S/A/B and explicit approval.
- `rejected` requires grade C/D.
- `reference` promotion requires explicit approval.
- Every `retained` or `reference` project requires one distinct capability summary, at least two ordinary-language semantic examples, one `high_confidence/gated/explicit_only` trigger level, and non-empty negative routing.
- Candidate, evaluated, rejected, archived, C, and D projects cannot carry semantic routing metadata and never enter either generated project-reference section.
- The generated file contains one thin-discovery row and one full-semantic row per eligible project. It is a read-only reminder layer, separate from the executable capability router.
- `high_confidence` and `gated` both allow discovery reminders; `gated` controls later reading or execution. `explicit_only` requires naming or a clear request.
- Re-evaluation updates the same canonical record and increments `revision`.
- Canonical GitHub URL and stable ID must agree.

## Capability records

Capability records have separate axes. Project grade does not imply deployment scope, and deployment scope does not imply routing state:

```text
project grade: S / A / B / C / D
deployment scope: not-installed / project / user / global / external-service
management state: candidate / active / cold / disabled / reference / quarantine / retired
health: healthy / unverified / degraded / broken / missing
invocation: auto / conditional / explicit-only / disabled
```

```text
candidate -> cold/reference/disabled/quarantine/retired
candidate/cold/reference/disabled -> active (healthy evidence + approval)
reference -> candidate (re-enter task-level evaluation)
active -> cold/disabled/quarantine/retired
retired -> candidate (new evaluation)
```

Invariants:

- Every new capability is `candidate / unverified / explicit-only`.
- Every new capability starts with `deployment_scope: not-installed`; deployment changes require explicit approval and evidence.
- `active` requires `healthy` evidence and explicit approval.
- `active` cannot be `not-installed`; `reference` must be `not-installed`.
- `auto` invocation requires `active` plus explicit approval.
- Only `active`, `cold`, and `reference` records are eligible for the generated L1/L2 router.
- `candidate`, `disabled`, `quarantine`, and `retired` records are excluded from generated routing.
- Manager-type capabilities cannot use `auto` invocation in schema v3.
- If an active capability becomes unhealthy, it automatically moves to `quarantine`, its invocation becomes `disabled`, and it disappears from the router.
- `disabled`, `retired`, and `quarantine` require `invocation: disabled`.
- A routing-state change does not install, enable, disable, or configure a real client capability.
- `capability-deployment` records an approved real-world fact but does not install or remove files.

## B-grade first-use path

```text
B/reference method value -> read only -> remain B/reference
B/reference executable value -> T0 -> approval -> candidate + project scope -> T1 real task
T1 pass -> A/retained project + healthy active capability at project scope
T1 fail/inconclusive -> remain B/reference + non-active capability -> recommend uninstall
confirmed removal -> deployment_scope: not-installed
```

There is no `project-trial` management state. The temporary fact “installed in this project but not yet retained” is represented by `candidate + deployment_scope: project` and should be settled in the same real task whenever possible.

## 中文

项目使用稳定 `gh-owner-repo` ID。`retained/reference` 必须是 S/A/B、经人工批准，并包含一条唯一能力摘要、至少两条日常语义示例、合法命中级别和非空禁止命中条件；候选、评价中、否决、归档和 C/D 项目不得进入生成的项目参考路由。每个合格项目在薄发现表和完整语义表中各一行；`high_confidence` 与 `gated` 都允许先提醒，`gated` 只限制后续读取或执行。该文件只是只读提醒层，不进入可执行能力路由。重新评价更新同一记录并递增 `revision`。

能力初始状态固定为 `candidate / unverified / explicit-only`，部署范围固定为 `not-installed`。只有 `active/cold/reference` 能进入派生路由；`candidate/disabled/quarantine/retired` 不进入。晋升 `active` 必须先有 `healthy` 证据、明确部署范围和人工批准；`active` 不能是 `not-installed`，`reference` 必须是 `not-installed`。schema v3 禁止总管型能力自动调用。active 能力健康降级时会自动隔离并移出路由。记录状态变化不等于真实客户端已经安装、启用或改配置；`capability-deployment` 也只记录已经批准并发生的事实。

B 级只有方法价值时维持 B/reference，不安装；存在低风险可执行增量时，T0 和安装批准后用 `candidate + deployment_scope: project` 记录“已装入当前项目但尚未结算”，当前项目第一次真实任务就是 T1。通过后结算为 A/retained + active/project；失败或结论不清就保持 B/reference、能力不进入 active，并建议卸载。这里没有 `project-trial` 管理状态。
