# Deterministic Write Protocol / 确定性写回协议

## Canonical sources / 唯一事实源

`projects/records/*.md`, `capabilities/records/*.md`, and `workflow.json` are canonical. Project indexes, semantic-reference tables, pools, and the capability router are generated. Never edit derived files manually.

项目记录、能力记录和 `workflow.json` 是唯一事实源；项目索引、语义表、候选池和能力路由均由 CLI 生成。

## Reviewed draft updates / 草稿写回

Optional `.workflow/lifecycle/<id>/runs/` and `evidence/` JSON files are canonical evidence sources, managed only by the [lifecycle commands](capability-lifecycle.md). A completed use receipt and its evidence commit together using the same lock, hash checks and protected rollback. Hook caches are disposable notices and do not contribute to health. Vault schema remains v3; extension contracts are independently versioned.

1. Read the current canonical record and run `record-hash --root <ROOT> --kind project --id <ID>` (use `--kind capability` for a capability).
2. Keep the returned `sha256`, copy the record to a separate draft, and edit only its body. Preserve all frontmatter, including `revision` and `updated_at`.
3. Run `update-project` or `update-capability` with `--from-file <DRAFT> --expected-sha256 <BASE_SHA256>`.
4. If the base hash, revision, or timestamp changed, reread the current record and merge the intervening changes into a fresh draft before retrying. Do not simply substitute today's hash on an old draft.

The hash covers exact file bytes, so even a manual body edit without a revision bump invalidates an old base. Missing hashes are rejected. This is a CLI compatibility change: existing update callers must capture and pass the base hash. Schema remains v3; no data migration is needed for a v3 vault. See [Agent Start](../AGENT-START.md) for complete commands.

先读取正式记录并用 `record-hash` 保存原始 `sha256`，再复制草稿，只改正文。写回必须带 `--expected-sha256`，并保留原版本号与时间戳。正式记录发生变化时，要先阅读并合并新内容，不能只换一个新 hash 强行提交旧稿。hash 按原始字节计算，正文被手工修改但未升版本也能拦截。已有调用脚本需要补参数；Schema 仍为 v3，无须迁移现有 v3 数据。

## Transaction order / 事务顺序

```text
Acquire .workflow/lock
-> check IDs, state transitions, approval gates and draft base
-> capture hashes of source reads and prepare target contents
-> verify sources and targets still match their observed hashes
-> back up exact target bytes and write an applying receipt
-> verify observed hashes before each atomic file replacement
-> validate the resulting workflow and recheck hashes
-> save committed receipt, then release lock
```

Each prepared transaction has `.workflow/transactions/<id>/manifest.json` and `before/` backups, with relative paths and before/after hashes. Writes stay inside the initialized root. Repeated canonical URLs/IDs reuse their records; repeating valid initialization returns `already_initialized`. Derived output ordering is deterministic. State/body updates increment the record revision.

If a write, post-write validation, or final receipt fails, rollback walks all applied targets in reverse order. It restores an original file only when the current bytes still match this transaction's output and the backup hash is intact. A newly created, unchanged transaction output is removed. A concurrent edit is preserved. One restore failure does not prevent attempts to restore the remaining files.

| Receipt status | Meaning and response |
| --- | --- |
| `applying` | Prepared or interrupted; inspect the lock, process, targets and backups before any recovery. |
| `committed` | All replacements and validation completed, and the final receipt was saved. |
| `rolled_back` | A caught failure occurred; all applied targets were restored or removed. |
| `recovery_required` | Concurrent changes or restore failures prevented full rollback. Preserve evidence and review each listed recovery item. |

If the receipt cannot be saved, the CLI reports the transaction directory and requires inspection; it does not claim successful rollback. Do not automatically restore a whole backup directory or remove an unknown lock. Any recovery affecting user data requires the applicable approval and a reviewed plan.

先加锁并验证草稿、状态和批准门；读取时记录 hash，写入前复核，按原始字节备份，再逐个替换。最终一致性校验通过后才记 `committed`。失败时逆序回滚；只有文件仍等于本事务刚写入的内容，才允许恢复或移除。其他进程的新修改会被保留，备份损坏或恢复失败会记为 `recovery_required`，且继续尝试恢复其余文件。回执也无法保存时会报告事务目录，不能当作已成功回滚。

## Concurrency and recovery limits / 并发与恢复边界

`.workflow/lock` serializes cooperating CLI writers. Hash checks detect observed file changes and reduce lost updates from other writers; they do not provide a filesystem-wide transaction against arbitrary editors. Each file replacement is atomic, but the whole multi-file operation is not. A hard process kill or power loss may leave `applying` and a stale lock; recovery is manual. Directory entry changes and a modification in the small check/replace window are outside the lock's protection when another writer bypasses the CLI.

CLI 锁约束遵守本协议的写入者，hash 复核补充检测其他修改。逐文件替换是原子的，多文件整体不是；强制杀进程或断电可能留下 `applying` 和锁，需要人工核对。绕过 CLI 的目录增删、hash 检查与替换之间的极短并发窗口，不属于强一致保证。

## State and deployment / 状态与部署

Deployment scope remains an independent fact: `not-installed / project / user / global / external-service`. Approved deployment commands record observed facts only. They never install, remove, enable, or configure a real capability. Active requires health plus an installed/deployed scope; reference requires `not-installed`. Semantic eligibility and generated-table consistency remain validated.

部署范围始终独立于等级、管理状态、健康和调用方式。部署命令只登记已获批且实际发生的事实；不会执行真实安装、卸载、启用或配置。active 必须健康且已部署，reference 必须为 `not-installed`。
