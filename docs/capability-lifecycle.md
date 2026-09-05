# Capability evidence and use receipts / 能力证据与使用回执

This optional extension keeps Vault schema v3. Its own JSON contracts use version 1. It records evidence and checks reuse conditions; it never executes a target capability, probes a remote service, installs software, or grants permission.

After updating the source checkout for an existing v3 Vault, run `rebuild --root <VAULT>` and `validate --root <VAULT>` through `scripts/workflow.py` to refresh generated instructions. Canonical project/capability records are not migrated or rewritten by that refresh.

本扩展保留 Vault Schema v3，独立证据/回执格式为 version 1。它把“哪次使用、哪个身份、什么验收结果、是否结算”接起来；评级、安装、部署范围和启用仍由原有流程批准。

## Three different checks / 三种检查

| Command | What a pass means | What it does not prove |
| --- | --- | --- |
| `validate` | Canonical records, generated views, extension field/state rules and receipt/evidence links are consistent | Today's environment or actual tool availability |
| `capability-check --require smoke` | A recent matching smoke/task report is reusable in this project; no newer negative evidence or unfinished use blocks it | Full task acceptance or permission to execute |
| `capability-check --require task` | A recent completed task report matches the declared current identity and project | A new task will succeed; the host really exposes the capability |
| `lifecycle-status` | Lists unfinished use receipts for recovery | An empty list does not prove unregistered tool use never happened |

`capability-check` exits **0** for reusable evidence, **1** for review needed, and **2** for invalid data, a writer lock or concurrent changes. JSON goes to stdout for 0/1; errors go to stderr. A caller must handle all three outcomes. It must also check current host availability, governance and the task's approval requirements. `authorized_execution` is always false: this recorder grants no permission. `governance_allows_active` describes only the current manifest.

一致性检查通过不等于能力健康；轻量探针通过不等于真实任务通过。旧 `health_state: healthy` 和文字依据只作为已有记录展示，不自动生成新的任务证据。`capability-check` 不修改账本或路由，也不会调用目标程序。

## Declare the identity / 声明需要跟踪的身份

Create a reviewed JSON input, for example `identity.json`:

```json
{
  "schema_version": 1,
  "capability_id": "sample-tool",
  "host": {"name": "generic-agent", "version": "reviewed-host-version"},
  "version": "reviewed-capability-version",
  "files": ["SKILL.md", "scripts/run.py"]
}
```

Each file is relative to the explicit `--artifact-root`. Include the capability's actual supporting scripts/assets/references that affect behavior, up to 64 files. Do not list credentials, an entire shared client config, unrelated files, directories, absolute paths or paths escaping that root. A capability represented only by a version may use an empty file list, with the weaker observation scope stated in its evidence.

The recorder measures exact file-byte SHA256 values; a missing file is `absent` and cannot pass reuse checks. Host/version metadata is **caller-declared**, not automatically discovered. Refresh that input from the current host/version observation before checking. The fingerprint includes those fields, the declared file set/content, and a hash of the resolved artifact-root path. File ordering is normalized; line-ending changes affect file hashes. A changed unrelated file has no effect.

身份输入由调用方提供并复核：宿主名、宿主版本和能力版本不会由脚本自动探测；文件哈希则由脚本实读计算。支持文件必须明确列出，否则其变化不会被发现。当前宿主是否真的暴露 Skill/Plugin/MCP，还要查看运行面，不能靠文件存在推断。

## Controlled use / 受控使用

Run commands from this source checkout using an existing Python interpreter. On Windows, `py -3` can replace `python`; on Unix use an existing `python3`. Placeholders below are reviewed, explicit values. Keep one stable request ID for retries, not for a second use.

```text
python scripts/workflow.py capability-check --root <VAULT> --id sample-tool --identity-file <IDENTITY_JSON> --artifact-root <ARTIFACT_ROOT>
python scripts/workflow.py use-begin --root <VAULT> --id sample-tool --identity-file <IDENTITY_JSON> --artifact-root <ARTIFACT_ROOT> --request-id first-use --session-id <SESSION> --turn-id <TURN>
```

The controlled operation calls `use-begin` immediately before the already-authorized real action. It records the project, session/turn, observed identity and prior governance state; it does not invoke the action. A first T1 may intentionally lack prior task evidence, but requires the existing T0 and project-use approval. A reuse check failure is not permission to run a new trial automatically.

After checking the actual result and settling temporary installation/activation facts, record:

```text
python scripts/workflow.py use-finish --root <VAULT> --id sample-tool --identity-file <IDENTITY_JSON> --artifact-root <ARTIFACT_ROOT> --run-id first-use --session-id <SESSION> --turn-id <TURN> --validation passed --settlement complete --evidence "Checked the requested output and completed the agreed settlement"
python scripts/workflow.py capability-check --root <VAULT> --id sample-tool --identity-file <IDENTITY_JSON> --artifact-root <ARTIFACT_ROOT> --require task --max-age-days 30
```

`validation` is `passed / failed / inconclusive / pending`; `settlement` is `complete / pending`. `pending + complete` is invalid. A completed failed/inconclusive attempt is a fully recorded outcome, not successful health. Any pending use blocks evidence reuse for that capability/project. Start/finish must use the same session/turn; startup recovery can list older work, and an explicit recovery call must refer to the original receipt context.

If interrupted, use `inconclusive + pending` and describe unfinished checks and the proposed settlement. A process killed before `use-finish` leaves the begin receipt pending. Do not claim removal or acceptance happened without evidence. Settle later using the original run ID; a completed run cannot be changed into a different outcome. Another use needs a new request ID. Beginning the same request twice is idempotent only if its context and identity still match. Inspect the returned `status`: `already_recorded` with `completed` refers to a finished action and must not cause it to execute again.

完成时，回执和任务证据在同一事务中落盘。成功且完整结算的真实任务报告可供后续检查消费；使用期间身份改变、失败或结论不清时不能当作成功。记录器不会自动修改项目等级、`health_state`、`management_state`、部署范围或调用方式，也不会执行卸载。沿用原有获批命令记录这些实际事实。

## Discovery and smoke reports / 发现与轻量探针报告

```text
python scripts/workflow.py record-evidence --root <VAULT> --id sample-tool --identity-file <IDENTITY_JSON> --artifact-root <ARTIFACT_ROOT> --request-id smoke-001 --kind smoke --result passed --evidence "Caller ran the approved startup check and reviewed its result"
```

Allowed kinds are `discovery` and `smoke`; direct creation of `task` evidence is forbidden. Only a completed use receipt produces task evidence. Results are caller-reported, not a cryptographic attestation. A `discovery` success never satisfies a smoke/task requirement. A later negative observation blocks older positive evidence; equal timestamps resolve conservatively. The default reuse window is 30 days, adjustable to 1–365 days. Expired or future evidence requires review. Timestamp format validation does not rewrite historical dates.

## Storage, consistency and recovery / 保存与恢复

| Location inside the initialized Vault | Purpose |
| --- | --- |
| `.workflow/lifecycle/<capability-id>/runs/<request-id>.json` | Canonical use receipt; unfinished or completed |
| `.workflow/lifecycle/<capability-id>/evidence/<id>.json` | Immutable observation; `task-<request-id>` reserved for task outcomes |
| `.workflow/lifecycle/hook-cache/*.json` | Disposable deduplication/notice cache; never health evidence |
| `.workflow/transactions/<transaction-id>/` | Existing transactional receipt and before-file backups |

Versioned contracts live in [lifecycle.schema.json](../schemas/lifecycle.schema.json). The dependency-free validator supports only the vocabulary used there, rejects unknown keywords and adds cross-record identity/settlement rules. Existing state enums come from the v3 core rather than a second private catalog. See the [write protocol](write-protocol.md) for protected rollback and hard-interruption limits.

`capability-check` detects changed observed files, changed receipt/evidence directory entries and an active writer during its read. It remains a point-in-time check; nothing here locks an actual external tool between checking and execution. Multi-file writes retain the existing caught-error rollback, not power-loss atomicity.

Project scope is a hash of the resolved Vault path. Artifact scope is also path-bound. Copying/moving a Vault does not make old evidence current in its new environment: historical records remain structurally readable, but require new observations/use evidence at the new path. No bulk migration or history fabrication is performed. Existing v3 roots without extension data still work; older CLI versions cannot validate or consume the extension. Use the new CLI for extension-enabled roots.

本扩展不保存完整聊天、原始工具输出或文件正文；摘要由调用方脱敏，最多 2000 字符。项目/文件的名称、会话标识和摘要仍可能是私有信息，路径哈希也不等于匿名化。公开演示只使用虚构数据。不会自动改 `.gitignore`，对外提交前复核实际暂存内容。

## Reproducible synthetic example / 可复现虚构示例

```text
python examples/lifecycle-demo.py --root <NEW_EMPTY_DIRECTORY>
```

The example refuses non-empty roots. It creates a text fixture and demonstrates missing evidence, successful settlement, changed content, a failed attempt and an interrupted pending attempt. `demo-results.json` records the checkpoints. No real capability is installed or tested. This example also runs in the Python test suite on supported CI platforms.

For automatic reminders, see [optional lifecycle Hooks](optional-lifecycle-hooks.md). Hook reminders complement explicit registration; they cannot discover a use that was never recorded.
