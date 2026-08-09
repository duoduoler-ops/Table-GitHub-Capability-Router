# Grok Build Profile

Verified locally against Grok Build CLI 1.0.0 on 2026-08-09.

- User Skills live under `~/.grok/skills/<skill-name>/SKILL.md`.
- Repo-scoped Skills are discovered under `.agents/skills/<skill-name>/SKILL.md`; this repository does not create a duplicate `.grok/skills` tree.
- User rules live in `~/.grok/AGENTS.md`, and `AGENTS.md` is this repository's canonical project-rules surface.
- `grok --cwd <repo> inspect --json` is the verification entry point for discovered project rules and Skills.
- In the verified 1.0.0 environment, inspection also listed the repository-root `CLAUDE.md` even when Claude external compatibility was disabled. This repository therefore keeps `CLAUDE.md` as a compatibility pointer, not as a second canonical rules document.

The capability optimizer treats this profile as `audit-only`. It inventories visible commands, Skill roots, and rule files, but does not infer or apply a write-capable configuration adapter.
