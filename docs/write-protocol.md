# Deterministic Write Protocol / 确定性写回协议

English | [中文](#中文)

## Canonical sources

- `projects/records/*.md`: one canonical record per GitHub repository.
- `capabilities/records/*.md`: one canonical record per capability.
- `workflow.json`: schema version, client profile, paths, and routing categories.

Project index, candidate pool, rejection log, and router are derived outputs. Never edit them manually.

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
- State changes increment `revision`; invalid or unapproved transitions fail without partial writes.
- Evidence and narrative changes use a separate reviewed draft plus `update-project` or `update-capability`. The CLI rejects protected frontmatter changes, increments `revision`, writes the canonical record transactionally, and refreshes derived files.

## Concurrency

Only one mutating command may hold `.workflow/lock`. A leftover lock may indicate a crashed or still-running process. Inspect it before removing it; the CLI never force-deletes an unknown lock.

## 中文

项目记录、能力记录和 `workflow.json` 是唯一事实源；索引、候选池、否决记录和路由表全部派生。每次修改先加锁、校验 ID/状态/批准门，再在一个事务中备份并原子替换；任何写入失败都恢复已写文件。证据正文先在独立草稿中编辑，再通过 `update-project` 或 `update-capability` 受控写回，不能借机改 ID、状态、等级或审批字段。重复输入命中原记录，不制造重复项。
