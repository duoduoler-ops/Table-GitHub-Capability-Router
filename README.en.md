# GitHub Intake + Capability Cold Storage + Agent Routing

Give a coding Agent this repository URL and ask it to establish the workflow. The Agent starts at `AGENT-START.md`, uses the dependency-free Python CLI for deterministic writes, and creates an isolated workflow root.

```text
Use this repository to establish a GitHub intake, capability cold-storage, and agent-routing workflow:
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

Read only AGENT-START.md first. Create the output in a new isolated directory and use an existing Python interpreter without installing packages. Initialize, create the first candidate, and validate. Ask before installation, login, external publishing, deletion, or client configuration changes.
```

## Output

The initialized root contains canonical project and capability records, generated indexes, a generated L1/L2 router, a maintenance log, and relative-path transaction manifests with pre-change backups.

The CLI owns stable IDs, URL canonicalization, deduplication, state transitions, approval gates, locks, atomic replacement, rollback, rebuilds, and validation. Markdown remains the human-readable interface.

## Routing eligibility

- New capabilities start `candidate / unverified / explicit-only` and are not routed.
- Only `active`, `cold`, and `reference` records may appear in the thin router.
- Active capabilities require health evidence and explicit approval.
- Manager-type capabilities cannot use automatic invocation in schema v1.
- An unhealthy active capability is automatically quarantined, disabled, and removed from the router.

## Commands

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language en --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>
python scripts/workflow.py rebuild --root <OUTPUT_DIR>
python scripts/workflow.py validate --root <OUTPUT_DIR>
```

Repository-scoped Codex and Claude Code Skills are included. Persistent wiring into another project or global client configuration remains an approval-gated configuration change.

See the [generated demo](examples/generated-demo-v1/README.md), [state machine](docs/state-machine.md), [write protocol](docs/write-protocol.md), [security policy](SECURITY.md), and [migration 0001](docs/migrations/0001-initial-schema.md).

MIT licensed.
