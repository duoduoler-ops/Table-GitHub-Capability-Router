# GitHub Intake + Capability Cold Storage + Agent Routing

Give a coding Agent this repository URL and ask it to establish the workflow. The Agent starts at `AGENT-START.md`, uses the dependency-free Python CLI for deterministic writes, and creates an isolated workflow root.

## Current verified hosts

The current maintained path is **Grok Build + Codex**. Both use the repo-scoped Skill at `.agents/skills/github-vault-router/`. Claude Code remains supported through the compatibility copy at `.claude/skills/github-vault-router/`, but it is no longer the current default host.

`AGENTS.md` is the single canonical rules file. Root `CLAUDE.md` is intentionally limited to a compatibility pointer: a 2026-08-09 local check with Grok Build 1.0.0 found that Grok still loaded the root file even when Claude compatibility import was disabled. The pointer is retained to avoid duplicate or drifting policy.

## Release focus

Every release adds one concise focus row here; implementation details stay in [CHANGELOG.md](CHANGELOG.md).

| Version | Focus | User-visible change |
| --- | --- | --- |
| Unreleased (planned v0.4.0) | Judge B-grade task increment, then settle first real use | Schema v3 separates grade from deployment scope; low-risk executable candidates use T0, approved project scope, and the current project's first real task as T1 |
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

## What's new in v0.2.0

| New capability | What it solves |
| --- | --- |
| Dependency-free deterministic Python CLI | Initializes, updates, transitions, rebuilds, validates, and rolls back without relying on prompt memory |
| Schema-driven canonical records | Prevents IDs, URLs, lifecycle state, approvals, and generated views from drifting apart |
| Semantic GitHub project references | Maps ordinary user wording to one relevant retained/reference project |
| Positive examples, negative routing, and trigger levels | Introduces `high_confidence`, `gated`, and explicit-only evidence as the source for later discovery behavior |
| Automatic consistency validation + optional pre-commit gate | Blocks missing metadata, duplicate examples, ineligible rows, and stale generated tables before release or, when explicitly enabled, before commit |
| Repo-scoped Codex and Claude Code Skills | Shares workflow facts while preserving client-specific invocation mechanisms |
| Optional read-only capability audit from PR #1 | Inventories Codex, Claude Code, Kimi Code, and generic agent capability visibility without configuration writes |
| Transactional writes | Adds locking, before backups, atomic replacement, rollback, and Git-history privacy scans |

> Historical note: v0.2.0 introduced trigger levels. v0.3.0 changed discovery so `gated` projects may be mentioned first while later reading or execution remains gated. The Unreleased line keeps that behavior and adds the B-grade settlement below.

## Unreleased (planned v0.4.0): B-grade first real use

- Grade, deployment scope, management state, health, and invocation are separate. A does not mean global installation.
- Method-only B projects remain reference and are not installed.
- Low-risk executable B candidates get T0, then explicit approval for `project` scope; the current project's first real task is T1.
- T1 pass settles to A/retained + active/project. Failure or an inconclusive result stays B/reference and recommends uninstall; deletion still requires confirmation.
- No durable `project-trial` state is introduced. Isolation is reserved for elevated permissions, real credentials, external writes, background services, heavy caches, unclear source/license/rollback, or no project-level installation path.

## Quick start

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
- New capabilities start `candidate / unverified / not-installed / explicit-only` and are not routed.
- Only `active`, `cold`, and `reference` records may appear in the thin router.
- Active capabilities require health evidence, a deployed scope, and explicit approval.
- Reference capabilities require `not-installed`; manager-type capabilities cannot use automatic invocation in schema v3.
- An unhealthy active capability is automatically quarantined, disabled, and removed from the router.

## Commands

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language en --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>
python scripts/workflow.py migrate-v3 --root <OUTPUT_DIR> `
  --deployment-scope "capability-id=project"
python scripts/workflow.py project-transition --root <OUTPUT_DIR> --id <PROJECT_ID> --to reference --grade B --approved `
  --capability-summary "Compare saved projects and produce one reusable reference recommendation" `
  --semantic-example "Help me find one reusable reference workflow" `
  --semantic-example "Which saved GitHub project can improve this task" `
  --trigger-level gated `
  --negative-routing "Do not route for a direct answer or when the implementation is already fixed"
python scripts/workflow.py capability-deployment --root <OUTPUT_DIR> --id <CAPABILITY_ID> --to project `
  --evidence "Approved project-local installation completed" --approved
python scripts/workflow.py rebuild --root <OUTPUT_DIR>
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

Grok Build and Codex share the repository Skill under `.agents/skills/`; Claude Code uses the compatibility Skill under `.claude/skills/`. Persistent wiring into another project or global client configuration remains an approval-gated configuration change.

## Optional read-only capability audit

PR #1 adds an independent audit entry for Grok Build, Codex, Claude Code, Kimi Code, and generic-agent Skill, Plugin, MCP, hook, and rule visibility. It does not write files or client configuration, and command discovery works without `sh` on native Windows, macOS, and Linux.

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

See the [generated demo](examples/generated-demo-v1/README.md), [state machine](docs/state-machine.md), [write protocol](docs/write-protocol.md), [Grok Build client profile](docs/client-profiles/grok-build.md), [optional capability audit](docs/optional-capability-optimizer.md), [optional pre-commit gate](docs/optional-pre-commit.md), [security policy](SECURITY.md), [v0.1 to v0.2 migration](docs/migrations/v0.1-to-v0.2.md), [v0.2 to v0.3 migration](docs/migrations/v0.2-to-v0.3.md), and [v0.3 to v0.4 migration](docs/migrations/v0.3-to-v0.4.md).

## Video walkthroughs

- [Part 1 · Are your saved GitHub tools actually worth installing?](https://www.youtube.com/watch?v=c4d23apzOEY)
- [Part 2 · The Agent capability cold-storage workflow behind this repository](https://www.youtube.com/watch?v=juIsuIy55mQ)
- [Advanced guide](https://www.youtube.com/watch?v=k7S5ewLaMVI&t=16s)

MIT licensed.
