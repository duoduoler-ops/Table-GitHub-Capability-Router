# Changelog

All notable changes are documented here. The project uses schema versions for record compatibility and Git tags for public releases.

## Unreleased

- Add optional version-1 lifecycle sidecars while preserving Vault schema v3: identity-bound discovery/smoke reports, transactional use receipts and task evidence.
- Add `use-begin`, `use-finish`, `record-evidence`, `capability-check` and `lifecycle-status`; detect stale/changed evidence, negative outcomes, unfinished use and read-time changes without granting execution permission.
- Add shared optional Hook adapters with scoped deduplication and fail-open behavior. Codex can display warnings; Grok defaults to a notice file and only requests continuation with explicit opt-in. No real client configuration is installed.
- Add synthetic lifecycle demonstrations and fault-oriented tests for evidence scope, concurrency, settlement and recovery.

- Require the original SHA256 for `update-project` and `update-capability`; add read-only `record-hash` and reject stale revision/timestamp values. Existing update callers must add `--expected-sha256`; schema remains v3.
- Verify observed file hashes during writes, preserve exact backup bytes, validate before committing, and preserve concurrent edits during rollback. Incomplete rollback is recorded as `recovery_required`.
- Make the optional pre-commit hook validate the actual Git index without executing staged code. Keep working-tree and local-history checks in `validate-repo`.
- Add pinned, read-only GitHub Actions checks for Windows/Python 3.14 and Linux/Python 3.10, including tests and an isolated CLI quickstart.
- Clarify B-grade interrupted T1 settlement and reuse of previous evidence; keep Grok Build + Codex as the maintained path and Claude Code as compatibility support.

## 0.4.0 - 2026-08-15

### Focus: settle B-grade first real use at project scope

- Introduce schema v3 with required `deployment_scope`, keeping project grade, deployment scope, management state, health, and invocation as separate axes.
- Add transactional `migrate-v3` for schema v1/v2 roots; deployment scope is explicit and never inferred.
- Add `capability-deployment` to record an approved deployment or removal fact without installing or deleting files.
- Add the B-grade task-increment gate: method-only projects remain reference; low-risk executable candidates use T0, approval for project scope, and the current project's first real task as T1.
- Settle T1 success to A/retained + active/project; keep failure or inconclusive results at B/reference and recommend uninstall without creating a `project-trial` state.
- Update schemas, templates, generated routers, state-machine documentation, bilingual guides, repo-scoped Skills, demo records, and tests for scope-aware routing.
- Add first-class `grok-build` client support; this work landed before the schema v3 scope update in the same v0.4.0 release.
- Treat `.agents/skills/github-vault-router/` as the shared Grok Build/Codex project Skill and retain `.claude/skills/github-vault-router/` as a Claude Code compatibility entry.
- Make `AGENTS.md` the single canonical rule body and reduce root `CLAUDE.md` to a compatibility pointer; document the Grok Build 1.0.0 observation that the root file is still loaded when Claude compatibility import is disabled.
- Add Grok Build to the read-only client audit and document host-neutral capability comparisons.
- Ignore `.grok/` local state and expand the privacy checklist for Grok inspect, authentication/session, and machine-specific snapshots.
- Strengthen `validate-repo` to require the public rules, security, changelog, ignore, and client-profile files; detect non-example Windows absolute paths; and refresh the generated demo platform labels.
- Add the third, advanced video walkthrough to all README language entry points.

## 0.3.0 - 2026-07-31

### Focus: discover first, activate only when chosen

- Replace the single-stage semantic suggestion flow with one generated file containing a mandatory thin discovery table and a full semantic-routing table.
- Require each substantive task with a clear object, action, or deliverable to check the thin table once per deliverable type before concluding that no saved project is relevant.
- Let both `high_confidence` and `gated` projects be mentioned during discovery; keep `gated` as the boundary for later repository reading or runtime execution.
- Keep workflow guidance and GitHub project references parallel, return at most Top-1, and preserve `no-extra-project` as the ordinary route.
- Add schema v2 `capability_summary` to canonical project records and block exact duplicate summaries across eligible projects.
- Add the transactional `migrate-v2` command. It requires one explicit capability summary for every retained/reference project, migrates project and capability records, rebuilds derived files, and validates the result atomically.
- Update repository-scoped Codex and Claude Code Skills, templates, schemas, bilingual guides, quickstart, generated demo, and migration documentation.
- Expand the Python suite from 18 to 20 tests with duplicate-summary and v1-to-v2 migration coverage.
- Scan Git history in both normal clones and linked Git worktrees during repository validation.

## 0.2.0 - 2026-07-26

### New in v0.2.0

- Add one-link Agent bootstrap entry.
- Add repo-scoped Codex and Claude Code Skills.
- Add dependency-free deterministic workflow CLI.
- Add versioned project/capability schemas, state machines, transactions, generated router/indexes, validation, and client profiles.
- Add generated semantic project-reference routing for approved S/A/B `retained/reference` projects.
- Require at least two ordinary-language examples, one trigger level, and negative routing for every eligible project.
- Block missing semantic metadata, duplicate examples, ineligible routing, and stale generated semantic tables.
- Add an optional, approval-gated local pre-commit hook for repository consistency checks.
- Keep semantic project references separate from the executable capability router and preserve `no-extra-project`.
- Add complete templates, a CLI-generated demo with five Golden Examples, and cross-platform-ready tests.
- Add protected draft write-back, manager-type marking, router eligibility filtering, automatic health quarantine, and full-history sensitive-data scanning.
- Preserve PR #1's optional read-only cross-client capability audit and make command discovery native on Windows, macOS, and Linux.

## 0.1.0 - 2026-07-20

- Initial bilingual documentation, intake prompts, project card, capability manifest, routing template, and sanitized minimal demo.
- Prompt-triggered, Markdown-first workflow without the deterministic v0.2.0 CLI and semantic project-reference generator.
