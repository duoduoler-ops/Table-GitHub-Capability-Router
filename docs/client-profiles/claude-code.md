# Claude Code Profile

Verified against the current official Claude Code documentation on 2026-07-21.

- Project Skills live under `.claude/skills/<skill-name>/SKILL.md`.
- Claude can load a Skill automatically when the request matches its description.
- `disable-model-invocation: true` disables automatic invocation; this repository intentionally leaves it `false`.
- A newly created top-level skills directory may require restarting Claude Code if it did not exist when the session started.
- Project Skill discovery is separate from real capability enablement and client settings.

This repository ships a project Skill and `CLAUDE.md`. It does not modify `settings.json`, install a Plugin, pre-approve tools, or change Hooks.

Official source: [Extend Claude with skills](https://code.claude.com/docs/en/skills).
