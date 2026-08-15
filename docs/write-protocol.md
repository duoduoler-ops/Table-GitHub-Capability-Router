# Deterministic Write Protocol / 确定性写回协议

English | [中文](#中文)

## Canonical sources

- `projects/records/*.md`: one canonical record per GitHub repository.
- `capabilities/records/*.md`: one canonical record per capability.
- `workflow.json`: schema version, client profile, paths, and routing categories.

Project index, thin discovery + full semantic project-reference table, candidate pool, rejection log, and capability router are derived outputs. Never edit them manually.

## Mutation order

```text
Acquire .workflow/lock
-> canonicalize input and check stable ID
-> validate requested state transition and approval gate
-> prepare all target contents in memory
-> snapshot every existing target into one transaction directory
-> atomically replace each target
-> rollback already-written targets on any failure
-> mark transaction committed
-> validate generated state
-> release lock
```

Every mutation creates `.workflow/transactions/<transaction-id>/manifest.json` with before/after hashes. Transactions never write outside the initialized workflow root.

## Idempotency

- The same canonical GitHub URL always maps to the same stable ID.
- Repeating `init` returns `already_initialized`.
- Repeating `new-project` or `new-capability` returns the existing record.
- Derived pages are regenerated from canonical records and have deterministic ordering.
- Exactly one thin-discovery row and one full-semantic row are generated for every eligible retained/reference project; ineligible projects generate neither.
- Missing semantic fields, duplicate capability summaries, duplicate examples, invalid eligibility, and stale generated tables fail validation.
- State changes increment `revision`; invalid or unapproved transitions fail without partial writes.
- Capability deployment scope is an independent fact axis: `not-installed`, `project`, `user`, `global`, or `external-service`. It is not a temporary management state.
- `capability-deployment` requires explicit approval plus evidence and records only the observed scope. It never installs, removes, enables, or configures a real capability.
- Promotion to `active` requires a healthy capability with a deployed scope; transition to `reference` requires `not-installed`. Record the real-world install or removal first, then update the record.
- Evidence and narrative changes use a separate reviewed draft plus `update-project` or `update-capability`. The CLI rejects protected frontmatter changes, increments `revision`, writes the canonical record transactionally, and refreshes derived files.

## Concurrency

Only one mutating command may hold `.workflow/lock`. A leftover lock may indicate a crashed or still-running process. Inspect it before removing it; the CLI never force-deletes an unknown lock.

## 中文

项目记录、能力记录和 `workflow.json` 是唯一事实源；索引、薄发现 + 完整语义表、候选池、否决记录和能力路由表全部派生。每个合格的 `retained/reference` 项目在薄发现表和完整语义表中各生成一行，不合格项目不生成；缺字段、重复能力摘要、重复示例、资格错误和生成表漂移都会校验失败。每次修改先加锁、校验 ID/状态/批准门，再在一个事务中备份并原子替换；任何写入失败都恢复已写文件。能力的部署范围是独立事实轴：`not-installed / project / user / global / external-service`，不是临时管理状态。`capability-deployment` 必须带明确批准和证据，只登记已经发生的部署范围，不负责真实安装、卸载、启用或配置；升为 `active` 前必须已经健康且有部署范围，转为 `reference` 前必须先回到 `not-installed`。证据正文先在独立草稿中编辑，再通过 `update-project` 或 `update-capability` 受控写回，不能借机改 ID、状态、等级、审批、部署范围或语义路由字段。重复输入命中原记录，不制造重复项。
