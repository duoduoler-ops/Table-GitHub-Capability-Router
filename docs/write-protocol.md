# Deterministic Write Protocol / 确定性写回协议

English | [中文](#中文)

## Canonical sources

- `projects/records/*.md`: one canonical record per GitHub repository.
- `capabilities/records/*.md`: one canonical record per capability.
- `workflow.json`: schema version, client profile, paths, and routing categories.

Project index, semantic project-reference table, candidate pool, rejection log, and capability router are derived outputs. Never edit them manually.

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
- Exactly one semantic row is generated for every eligible retained/reference project; ineligible projects generate no row.
- Missing semantic fields, duplicate examples, invalid eligibility, and stale generated tables fail validation.
- State changes increment `revision`; invalid or unapproved transitions fail without partial writes.
- Evidence and narrative changes use a separate reviewed draft plus `update-project` or `update-capability`. The CLI rejects protected frontmatter changes, increments `revision`, writes the canonical record transactionally, and refreshes derived files.

## Concurrency

Only one mutating command may hold `.workflow/lock`. A leftover lock may indicate a crashed or still-running process. Inspect it before removing it; the CLI never force-deletes an unknown lock.

## 中文

项目记录、能力记录和 `workflow.json` 是唯一事实源；索引、项目语义命中表、候选池、否决记录和能力路由表全部派生。每个合格的 `retained/reference` 项目恰好生成一行语义记录，不合格项目不生成；缺字段、重复示例、资格错误和生成表漂移都会校验失败。每次修改先加锁、校验 ID/状态/批准门，再在一个事务中备份并原子替换；任何写入失败都恢复已写文件。证据正文先在独立草稿中编辑，再通过 `update-project` 或 `update-capability` 受控写回，不能借机改 ID、状态、等级、审批或语义路由字段。重复输入命中原记录，不制造重复项。
