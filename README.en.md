# GitHub Intake + Capability Cold Storage + Agent Routing

Give a coding Agent this repository URL and ask it to establish the workflow. The Agent starts at `AGENT-START.md`, uses the dependency-free Python CLI for deterministic writes, and creates an isolated workflow root.

## What's new in v0.2.0

| New capability | What it solves |
| --- | --- |
| Dependency-free deterministic Python CLI | Initializes, updates, transitions, rebuilds, validates, and rolls back without relying on prompt memory |
| Schema-driven canonical records | Prevents IDs, URLs, lifecycle state, approvals, and generated views from drifting apart |
| Semantic GitHub project references | Maps ordinary user wording to one relevant retained/reference project |
| Positive examples, negative routing, and trigger levels | Separates automatic suggestions, gated suggestions, and explicit-only references |
| Automatic consistency validation + optional pre-commit gate | Blocks missing metadata, duplicate examples, ineligible rows, and stale generated tables before release or, when explicitly enabled, before commit |
| Repo-scoped Codex and Claude Code Skills | Shares workflow facts while preserving client-specific invocation mechanisms |
| Optional read-only capability audit from PR #1 | Inventories Codex, Claude Code, Kimi Code, and generic agent capability visibility without configuration writes |
| Transactional writes | Adds locking, before backups, atomic replacement, rollback, and Git-history privacy scans |

```text
Use this repository to establish a GitHub intake, capability cold-storage, and agent-routing workflow:
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

Read only AGENT-START.md first. Create the output in a new isolated directory and use an existing Python interpreter without installing packages. Initialize, create the first candidate, and validate. Ask before installation, login, external publishing, deletion, or client configuration changes.
```

## Output

The initialized root contains canonical project and capability records, a generated project semantic-reference table, generated indexes, a generated L1/L2 capability router, a maintenance log, and relative-path transaction manifests with pre-change backups.

The CLI owns stable IDs, URL canonicalization, deduplication, state transitions, approval gates, locks, atomic replacement, rollback, rebuilds, and validation. Markdown remains the human-readable interface.

## Routing eligibility

- Only approved S/A/B projects in `retained` or `reference` state enter the semantic project-reference table.
- Every eligible project requires at least two ordinary-language examples, a trigger level, and negative routing; every ineligible project is excluded.
- A semantic match returns at most one project-informed reference plus the `no-extra-project` route. It never grants execution permission.
- New capabilities start `candidate / unverified / explicit-only` and are not routed.
- Only `active`, `cold`, and `reference` records may appear in the thin router.
- Active capabilities require health evidence and explicit approval.
- Manager-type capabilities cannot use automatic invocation in schema v1.
- An unhealthy active capability is automatically quarantined, disabled, and removed from the router.

## Commands

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language en --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>
python scripts/workflow.py project-transition --root <OUTPUT_DIR> --id <PROJECT_ID> --to reference --grade B --approved `
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

See the [generated demo](examples/generated-demo-v1/README.md), [state machine](docs/state-machine.md), [write protocol](docs/write-protocol.md), [optional capability audit](docs/optional-capability-optimizer.md), [optional pre-commit gate](docs/optional-pre-commit.md), [security policy](SECURITY.md), and [v0.1 to v0.2 migration](docs/migrations/v0.1-to-v0.2.md).

MIT licensed.
