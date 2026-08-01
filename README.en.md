# GitHub Intake + Capability Cold Storage + Agent Routing

Give a coding Agent this repository URL and ask it to establish the workflow. The Agent starts at `AGENT-START.md`, uses the dependency-free Python CLI for deterministic writes, and creates an isolated workflow root.

## Release focus

Every release adds one concise focus row here; implementation details stay in [CHANGELOG.md](CHANGELOG.md).

| Version | Focus | User-visible change |
| --- | --- | --- |
| v0.3.0 | Discover saved capabilities before deciding they are irrelevant | Substantive tasks check a thin discovery table; `gated` projects may be mentioned before runtime approval while reading, installation, and execution remain gated |
| v0.2.0 | Deterministic intake and semantic references | Added schema-driven records, CLI rebuild/validation, transactions, and one full semantic routing table |
| v0.1.0 | Publish-safe Markdown starter | Established bilingual templates, intake prompts, and a sanitized example |

## What's new in v0.3.0

| New capability | What it solves |
| --- | --- |
| Mandatory thin discovery gate | Every substantive task checks one compact capability-summary table before the Agent may conclude that no saved project is relevant |
| Thin discovery + full semantic details | Cheap Top-1 discovery happens first; positive and negative routing details are read only after a match |
| Remind-first `gated` semantics | `high_confidence` and `gated` may both be mentioned; `gated` controls later reading or execution, not discovery |
| Schema v2 capability summaries | Every eligible project has one distinct verb + object + output summary; exact duplicates fail validation |
| Transactional `migrate-v2` | Upgrades v0.2 roots after summaries are supplied for retained/reference projects, then rebuilds and validates atomically |
| Three-route reminder | Keeps `no-extra-project`, offers minimum Markdown reading after the user chooses, and asks before installation or enablement only when runtime is required |

```text
Use this repository to establish a GitHub intake, capability cold-storage, and agent-routing workflow:
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

Read only AGENT-START.md first. Create the output in a new isolated directory and use an existing Python interpreter without installing packages. Initialize, create the first candidate, and validate. Ask before installation, login, external publishing, deletion, or client configuration changes.
```

## Output

The initialized root contains canonical project and capability records, a generated thin discovery + full semantic-reference table, generated indexes, a generated L1/L2 capability router, a maintenance log, and relative-path transaction manifests with pre-change backups.

The CLI owns stable IDs, URL canonicalization, deduplication, state transitions, approval gates, locks, atomic replacement, rollback, rebuilds, and validation. Markdown remains the human-readable interface.

## Routing eligibility

- Only approved S/A/B projects in `retained` or `reference` state enter the thin discovery + full semantic-reference table.
- Every eligible project requires one distinct capability summary, at least two ordinary-language examples, a trigger level, and negative routing; every ineligible project is excluded.
- Every substantive task checks the thin table once per deliverable type. A meaning match returns at most one project-informed reminder plus the `no-extra-project` route.
- `high_confidence` and `gated` both allow a reminder. `gated` controls later reading or execution; a reminder never grants execution permission.
- New capabilities start `candidate / unverified / explicit-only` and are not routed.
- Only `active`, `cold`, and `reference` records may appear in the thin router.
- Active capabilities require health evidence and explicit approval.
- Manager-type capabilities cannot use automatic invocation in schema v2.
- An unhealthy active capability is automatically quarantined, disabled, and removed from the router.

## Commands

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language en --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>
python scripts/workflow.py migrate-v2 --root <OUTPUT_DIR> `
  --capability-summary "gh-owner-repo=Compare saved projects and produce one reusable reference recommendation"
python scripts/workflow.py project-transition --root <OUTPUT_DIR> --id <PROJECT_ID> --to reference --grade B --approved `
  --capability-summary "Compare saved projects and produce one reusable reference recommendation" `
  --semantic-example "Help me find one reusable reference workflow" `
  --semantic-example "Which saved GitHub project can improve this task" `
  --trigger-level gated `
  --negative-routing "Do not route for a direct answer or when the implementation is already fixed"
python scripts/workflow.py rebuild --root <OUTPUT_DIR>
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

Repository-scoped Codex and Claude Code Skills are included. Persistent wiring into another project or global client configuration remains an approval-gated configuration change.

## Optional read-only capability audit

PR #1 adds an independent audit entry for Skill, Plugin, MCP, hook, and rule visibility. It does not write files or client configuration, and command discovery works without `sh` on native Windows, macOS, and Linux.

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

See the [generated demo](examples/generated-demo-v1/README.md), [state machine](docs/state-machine.md), [write protocol](docs/write-protocol.md), [optional capability audit](docs/optional-capability-optimizer.md), [optional pre-commit gate](docs/optional-pre-commit.md), [security policy](SECURITY.md), [v0.1 to v0.2 migration](docs/migrations/v0.1-to-v0.2.md), and [v0.2 to v0.3 migration](docs/migrations/v0.2-to-v0.3.md).

MIT licensed.
