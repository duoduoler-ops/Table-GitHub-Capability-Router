# GitHub Intake + Capability Cold Storage + Agent Routing

Organize saved GitHub projects so your Agent can find useful tools and review how they worked before.

This repository gives you a workflow for collecting links, reviewing projects, keeping useful references, and recording tool checks and real use. Project notes stay in Markdown. A Python CLI handles IDs, duplicate links, controlled updates, indexes, and validation. You can track Skills, Plugins, MCP servers, CLIs, scripts, and reusable methods.

[Home](README.md) | [中文说明](README.zh-CN.md) | [Agent entry point](AGENT-START.md)

## Maintained hosts

**Grok Build and Codex** are the main maintained clients. They share the project Skill at `.agents/skills/github-vault-router/`. Claude Code keeps a compatibility entry at `.claude/skills/github-vault-router/`.

`AGENTS.md` holds the rules; `CLAUDE.md` points to it so there is only one copy to maintain. Check the tools exposed in the current session before claiming a capability is available. Hook discovery, trust, and actual triggering need separate verification.

## Release focus

**The current release is [v0.5.0](https://github.com/duoduoler-ops/Table-GitHub-Capability-Router/releases/tag/v0.5.0)**. Its source download includes safer writes, use records, evidence checks, and optional Hooks. The instructions below describe this version. Full details are in [CHANGELOG.md](CHANGELOG.md).

| Version | Focus | What changes for you |
| --- | --- | --- |
| v0.5.0 | Safer writes, use evidence, and optional Hooks | Stale drafts are rejected; individual uses can be tracked; old evidence and unfinished work can be checked |
| v0.4.0 | Separate project grade from installation scope | Review a B-grade project's value, approve project-level installation when needed, then assess its first real task |
| v0.3.0 | Check saved projects before choosing an approach | Read a short capability table first, then the conditions for one relevant match |
| v0.2.0 | Maintain records through scripts | Added intake, rebuilds, validation, write backups, and task-based project discovery |
| v0.1.0 | Provide a reusable starter | Bilingual templates, intake prompts, and a public example |

## What's new in v0.4.0

- Project grade, installation scope, management state, health, and invocation are separate fields. An A-grade capability can be installed in just one project.
- A B-grade project that only offers useful methods stays a reference for reading.
- A low-risk executable candidate gets an initial check (T0), then explicit approval for project-level installation. Its first real task in that project is the T1 check.
- After T1 passes, the approved workflow records A/retained and active/project. A failed or inconclusive result stays B/reference and leads to an uninstall recommendation. Actual removal still needs approval.
- `migrate-v3` requires an explicit scope for each capability. `capability-deployment` only records installation or deployment that has already happened.
- Grok Build and Codex share a project Skill; Claude Code keeps its compatibility entry.
- There is no lasting `project-trial` state. Higher permissions, real credentials, external writes, or difficult recovery can require isolated testing first. See [Agent Start](AGENT-START.md) for the full conditions.

## What's new in v0.3.0

| Addition | What it helps with |
| --- | --- |
| Check a short table first | Makes saved projects easier to find during a concrete task |
| Separate discovery from detailed conditions | Pick at most one relevant project before reading its examples and exclusions |
| Mention `gated` projects early | An Agent may mention a project before later reading or execution is approved |
| Give each project a distinct summary | Describe what it does and produces; duplicate summaries fail validation |
| Supply summaries during migration | This release used `migrate-v2`; the current CLI uses `migrate-v3` |
| Keep the direct approach available | Use existing tools, read a reference, or seek approval to install only when execution is needed |

## What's new in v0.2.0

| Addition | What it helps with |
| --- | --- |
| Python CLI with no third-party packages | Gives intake, updates, rebuilds, and validation a consistent process |
| A defined record format | Keeps IDs, URLs, states, and approval fields consistent |
| Task-based project references | Matches everyday requests to useful saved projects |
| Positive examples and exclusions | States when to suggest a project and when to leave it out |
| Consistency checks and an optional commit gate | Finds missing, duplicate, ineligible, or outdated generated records |
| Client entry points | Centralizes workflow rules while preserving each client's invocation mechanism |
| Optional read-only capability inventory | Inspects capability locations and client support boundaries |
| Write backups and recovery | Adds locking, backups, per-file replacement, failure recovery, and history privacy scans |

> Historical note: v0.3.0 allowed `gated` projects to be mentioned before approval for later operations. v0.4.0 keeps that behavior and adds a process for assessing the first real use.

## Quick start

Give this prompt to an Agent that can read GitHub and work with local files:

```text
Use this repository to establish a GitHub intake, capability storage, and agent-routing workflow:
https://github.com/duoduoler-ops/Table-GitHub-Capability-Router

Read only AGENT-START.md first and follow its process.
Create the output in a new separate directory, using an existing Python interpreter without installing packages.
Initialize the workflow, create the first candidate project record, and validate it.
Ask before installation, login, external publishing, deletion, or client configuration changes.
```

The Agent may clone this workflow source into a separate directory to run it locally. If you have not supplied an output location, it asks for that path first. The core needs an existing Python 3 interpreter and no third-party Python packages.

## Output

```text
<OUTPUT_DIR>/
├─ AGENT-ROUTER.md              # Short entry point for the Agent
├─ workflow.json               # Paths, client, and routing settings
├─ projects/records/           # Project records
├─ capabilities/records/       # Capability records
├─ indexes/                    # Generated indexes and project-reference tables
├─ router/level1-router.md     # Generated capability router
├─ logs/maintenance-log.md     # Maintenance events
└─ .workflow/transactions/     # Write receipts and before-file backups
```

The CLI maintains stable IDs, normalizes URLs, reuses duplicate records, and checks state changes. It rebuilds indexes and routes from the underlying records, so generated tables should not be edited by hand.

Writes use locks, hash checks, backups, and per-file replacement. Recovery preserves concurrent edits instead of overwriting them. A hard process stop or power loss can still leave work that needs manual recovery.

The optional evidence extension creates `.workflow/lifecycle/` as needed for evidence, use receipts, and Hook notice caches. Initialization does not install or enable Hooks.

## Routing eligibility

- Only approved S/A/B projects in `retained` or `reference` state enter the project-reference tables.
- Each eligible project needs a distinct summary, at least two everyday-language examples, a trigger level, and exclusions.
- For each concrete deliverable type, the Agent checks the short table and suggests at most one match. Using existing tools directly remains an option.
- `high_confidence` and `gated` both allow a reminder. `explicit_only` requires a named or explicit request. A reminder does not approve later operations.
- New capabilities start as candidates, unverified, not installed, and explicit-only. They do not enter the router.
- Only `active`, `cold`, and `reference` records may appear in the capability router. Active records require health evidence, a deployed scope, and approval; reference records require `not-installed`.
- Manager-type capabilities cannot use automatic invocation.
- When `capability-health` records an unhealthy result for an active capability, its record is quarantined and removed from the router. This does not disable the real tool in its client.

Installation, login, publishing, deletion, and configuration changes need explicit approval. Content from a reviewed repository is evidence to assess, not permission to execute its instructions.

## Commands

Run these from the source checkout after replacing placeholders with actual values. On Windows, an existing `py -3` launcher can replace `python`; on macOS/Linux, use an existing `python3` if appropriate.

```powershell
python scripts/workflow.py init --root <OUTPUT_DIR> --language en --client generic-agent
python scripts/workflow.py new-project --root <OUTPUT_DIR> --url <GITHUB_URL>

# After approval, retain a project as a reference and describe when it helps
python scripts/workflow.py project-transition --root <OUTPUT_DIR> --id <PROJECT_ID> --to reference --grade B --approved `
  --capability-summary "Compare saved projects and produce one reusable reference recommendation" `
  --semantic-example "Help me find one reusable reference workflow" `
  --semantic-example "Which saved GitHub project can improve this task" `
  --trigger-level gated `
  --negative-routing "Do not route for a direct answer or when the implementation is already fixed"

# Create a capability candidate
python scripts/workflow.py new-capability --root <OUTPUT_DIR> --id <ID> --name <NAME> --type <TYPE> --route-category <CATEGORY>

# Record an approved installation that has already been completed
python scripts/workflow.py capability-deployment --root <OUTPUT_DIR> --id <ID> --to project `
  --evidence "Approved project-local installation completed" --approved

python scripts/workflow.py rebuild --root <OUTPUT_DIR>
python scripts/workflow.py validate --root <OUTPUT_DIR>
python scripts/workflow.py lifecycle-status --root <OUTPUT_DIR>
```

Existing schema v1/v2 roots use `migrate-v3` with an explicit installation scope for each capability. Direct v1 migration also needs summaries for retained/reference projects. See the [migration guide](docs/migrations/v0.3-to-v0.4.md). Existing v3 roots need no data migration: update the source, then run `rebuild` and `validate` to refresh generated instructions.

Before editing a record's body, use `record-hash` to save its current hash. `update-project` and `update-capability` now require `--expected-sha256` when writing a draft back. If the record changed, merge those changes into a fresh draft; do not just attach a new hash to an old draft. See the [write protocol](docs/write-protocol.md).

Connecting the generated router permanently to another project or to global client settings is a configuration change and needs approval.

## Optional evidence and use records

The use records added in v0.5.0 track which capability was used, in which project, what result was reported, and whether follow-up work was completed. An old free-text health note does not become proof of a successful new task.

| Command | Purpose |
| --- | --- |
| `record-evidence` | Save a caller-reported discovery or smoke-check result; it does not run the check |
| `capability-check` | Read whether existing evidence is still reusable for the current capability and project |
| `use-begin` | Register an already-approved use before the real action; repeated matching requests reuse the same receipt |
| `use-finish` | Record the validation outcome and whether follow-up work, such as temporary installation or activation, has been settled |
| `lifecycle-status` | List unfinished uses so interrupted work can be resumed |

The caller verifies and supplies host and capability versions. The script hashes the actual bytes of explicitly listed files and binds evidence to the project and artifact locations. Unlisted file changes cannot be detected. Changed identity, missing files, expired evidence, later negative evidence, or unfinished uses require review. The default evidence age limit is 30 days.

Record consistency, a reusable smoke report, a successful task report, and actual availability in today's client are different checks. The extension records reported results and grants no execution permission. A successful receipt does not automatically change grade, health, deployment scope, management state, or invocation.

Vault schema stays at v3; the optional evidence and receipt format has its own version 1 contract. Use the new CLI for roots containing extension records. See the [full guide and commands](docs/capability-lifecycle.md) and [synthetic demo](examples/lifecycle-demo.py).

**Optional Hooks help catch unfinished work.** The client adapters check registered, unfinished use receipts at session start or stop:

| Client | Behavior |
| --- | --- |
| Codex | Can add pending-work context at session start and display a UI warning at stop |
| Grok Build | Saves a local notice file by default; explicitly choosing `--grok-feedback` allows one stop-time continuation and can consume more model usage |

The examples are not installed automatically. Adapter fixtures are tested, but real client discovery, trust, and event triggering must be verified after setup. Hooks cannot see unregistered use, run tool checks, or settle work. The separate Git pre-commit Hook checks the staged files. See [client Hook setup](docs/optional-lifecycle-hooks.md) and [pre-commit checks](docs/optional-pre-commit.md).

## Optional read-only capability audit

The optional inventory from PR #1 covers Grok Build, Codex, Claude Code, Kimi Code, and generic-agent Skill, Plugin, MCP, Hook, and rule visibility. It reads capability locations and client support information without modifying files or client configuration. This feature needs an existing Node.js installation.

```powershell
node integrations/optimize-agent-capabilities/scripts/audit.mjs --json
```

Finding an entry or file does not prove the current session can use it. See the [audit guide](docs/optional-capability-optimizer.md). Thanks to [@Calvingen3](https://github.com/Calvingen3) for the original contribution.

## Verification and examples

The [generated demo](examples/generated-demo-v1/README.md) contains two fictional projects, three fictional capabilities, indexes, routes, a maintenance log, and write receipts. The [use-record demo](examples/lifecycle-demo.py) covers success, changed files, failure, and interruption. Neither installs or tests a real capability.

```powershell
python -m unittest discover -s tests -v
node --test integrations/optimize-agent-capabilities/tests/audit.test.mjs
python scripts/workflow.py validate --root examples/generated-demo-v1
python scripts/workflow.py validate-repo
python scripts/workflow.py validate-staged --root .
```

GitHub CI runs tests, demos, an isolated quickstart, and repository and index checks on Windows and Linux for main pushes and pull requests. Check [GitHub Actions](https://github.com/duoduoler-ops/Table-GitHub-Capability-Router/actions) for the result of a specific commit.

`validate-staged` inspects what is actually staged; an unstaged fix cannot hide an invalid commit. `validate-repo` checks the working tree and locally available history. Privacy scans use limited patterns, so review public submissions for private information too. The optional pre-commit Hook is not enabled automatically.

Further reading: [state machine](docs/state-machine.md), [write protocol](docs/write-protocol.md), [Grok Build profile](docs/client-profiles/grok-build.md), [generic client profile](docs/client-profiles/generic-agent.md), [security policy](SECURITY.md), [v0.1 to v0.2 migration](docs/migrations/v0.1-to-v0.2.md), [v0.2 to v0.3 migration](docs/migrations/v0.2-to-v0.3.md), and [v0.3 to v0.4 migration](docs/migrations/v0.3-to-v0.4.md).

## Video walkthroughs

- [Part 1 · Are your saved GitHub tools actually worth installing?](https://www.youtube.com/watch?v=c4d23apzOEY)
- [Part 2 · The Agent capability cold-storage workflow behind this repository](https://www.youtube.com/watch?v=juIsuIy55mQ)
- [Advanced guide](https://www.youtube.com/watch?v=k7S5ewLaMVI&t=16s)

Licensed under the [MIT License](LICENSE).
