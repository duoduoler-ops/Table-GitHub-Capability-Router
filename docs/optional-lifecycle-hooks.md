# Optional lifecycle Hooks / 可选生命周期 Hook

The adapter is `scripts/lifecycle_hook.py`. It consumes the [shared receipt core](capability-lifecycle.md), filters by an explicit initialized Vault root and emits at most one notice per host/session/event/turn. With no turn ID it falls back to once per session/event. It never installs, probes, settles records, reads a transcript or executes another tool.

## Delivery depends on the host / 宿主差异

| Host/event | Adapter behavior |
| --- | --- |
| Codex SessionStart | Checks this project's unfinished receipts, including previous sessions, and adds a short recovery notice to context |
| Codex Stop | Checks only this session's unfinished receipts and returns a UI warning; never requests continuation |
| Grok SessionStart | Saves a local notice file; passive stdout is ignored by Grok |
| Grok Stop, default | Saves a local notice file, permits completion |
| Grok Stop with explicit `--grok-feedback` | Requests one feedback continuation, then deduplicates; may consume additional model usage |

Reviewed against the [official Codex Hook contract](https://learn.chatgpt.com/docs/hooks) on 2026-09-05: JSON input uses `hook_event_name`, `session_id`, `turn_id`, `cwd` and `stop_hook_active`. Startup context and Stop UI warnings have different output shapes; non-managed Hook definitions require review/trust.

The [official Grok Hook guide](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/10-hooks.md) uses `hookEventName`, `sessionId`, `promptId` and `stopHookActive`. The adapter accepts `session_start` and `stop`, and filters Stop to `reason: end_turn`. Startup stdout does not provide a model reminder; Stop feedback continues the agent. The input `promptId` maps to the receipt turn ID.

Grok 默认模式只保留本地待办检查记录，不能宣称用户或模型已收到启动提醒。需要恢复检查时，主动运行 `lifecycle-status`。选择 `--grok-feedback` 才会在结束时请求一次续接；这会增加模型用量，因此样例默认不带该选项。两个宿主的适配器测试通过，不等于两个宿主已经安装、信任或真实触发这些 Hook。

## Reviewable examples / 接入示例

Examples are inert files, outside client configuration directories:

- [Codex example](../integrations/lifecycle-hooks/codex.example.json)
- [Grok Unix example](../integrations/lifecycle-hooks/grok-build.example.json) / [Grok Windows example](../integrations/lifecycle-hooks/grok-build.windows.example.json)

After approval, replace `<PYTHON>`, `<SOURCE_ROOT>` and `<VAULT_ROOT>` with explicit absolute paths. Use an existing interpreter; quote paths with spaces and preserve valid JSON escaping. The root must be the initialized Vault whose receipts are being checked. The adapter ignores events from other directories, including subdirectories, by design. Each project requires an explicit integration decision.

The Windows entries use an already-installed `py -3` launcher; Codex selects `commandWindows`, while Grok has a separate Windows example. If that launcher is unavailable, review a command for the existing interpreter and actual host shell before enabling it. Quoting an executable path alone is not a PowerShell invocation; do not blindly paste the Unix command into a PowerShell runner.

A configuration file and its actual enablement/trust are separate facts. Do not copy examples into `.codex/` or `.grok/`, change project trust, or overwrite existing Hook definitions without approval. Merge the reviewed entries into the user's chosen scope. Then inspect the host's actual discovery and trigger tests. These examples are not installed by `init` and do not alter global settings.

## Failure and recovery / 异常与恢复

- Ordinary sessions without unfinished receipts are quiet.
- Stop never includes another session's receipts; SessionStart intentionally finds earlier unfinished sessions in this project.
- The stop-active guard avoids feedback loops. A shared workflow lock serializes cache writes; simultaneous invocations do not duplicate a notice.
- The input is capped at 64 KiB, individual records at 128 KiB, and the Hook scans at most 256 receipts. Examples set a five-second process timeout.
- Malformed/unsupported input, invalid scope, an active writer, corrupted records/cache or a timeout fail open. They do not constitute health success. Use `lifecycle-status` and `validate` for explicit diagnosis.
- No stdout/stderr payload log is saved. Cache files contain only scope identifiers, pending record IDs and a fixed notice, never the last assistant message or transcript.
- A crash after recording a notice but before displaying it can suppress a later reminder. This is best-effort notification; explicit status checking remains the recovery path.

运行安装后的最低验收：正常静默、存在待结算记录、同轮重复、跨项目、跨会话、损坏输入，以及宿主实际触发结果。测试记录必须分别列出“输入样例适配通过”“宿主发现/信任状态”“真实事件触发是否验证”。本仓库不把后两项从文件存在推断出来。
