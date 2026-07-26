# Changelog

All notable changes are documented here. The project uses schema versions for record compatibility and Git tags for public releases.

## Unreleased

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
