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
- Re-evaluation updates the same canonical record and increments `revision`.
- Canonical GitHub URL and stable ID must agree.

## Capability records

```text
candidate -> cold/reference/disabled/quarantine/retired
candidate/cold/reference/disabled -> active (healthy evidence + approval)
active -> cold/disabled/quarantine/retired
retired -> candidate (new evaluation)
```

Invariants:

- Every new capability is `candidate / unverified / explicit-only`.
- `active` requires `healthy` evidence and explicit approval.
- `auto` invocation requires `active` plus explicit approval.
- Only `active`, `cold`, and `reference` records are eligible for the generated L1/L2 router.
- `candidate`, `disabled`, `quarantine`, and `retired` records are excluded from generated routing.
- Manager-type capabilities cannot use `auto` invocation in schema v1.
- If an active capability becomes unhealthy, it automatically moves to `quarantine`, its invocation becomes `disabled`, and it disappears from the router.
- `disabled`, `retired`, and `quarantine` require `invocation: disabled`.
- A routing-state change does not install, enable, disable, or configure a real client capability.

## 中文

项目使用稳定 `gh-owner-repo` ID。`retained` 必须是 S/A/B 且经人工批准；`rejected` 必须是 C/D；重新评价更新同一记录并递增 `revision`。

能力初始状态固定为 `candidate / unverified / explicit-only`。只有 `active/cold/reference` 能进入派生路由；`candidate/disabled/quarantine/retired` 不进入。晋升 `active` 必须先有 `healthy` 证据并获得批准；schema v1 禁止总管型能力自动调用。active 能力健康降级时会自动隔离并移出路由。记录状态变化不等于真实客户端已经安装、启用或改配置。
