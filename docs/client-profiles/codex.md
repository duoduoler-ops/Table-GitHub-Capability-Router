# Codex Profile

Verified against the current official Codex documentation on 2026-07-21.

- Repo-scoped Skills live under `.agents/skills/<skill-name>/SKILL.md`.
- Codex starts with Skill name, description, and path, then loads the full body only when selected.
- Implicit invocation is enabled by default and can be disabled with `agents/openai.yaml` policy.
- `AGENTS.md` is the durable repository guidance surface.
- `.codex/config.toml` is a project configuration surface and is loaded only for trusted projects. This repository does not create or edit it automatically.

This repository ships both a small repo-scoped Skill and `AGENTS.md`, so a cloned repository has an automatic routing entry without global installation. If the user only gives a web URL during an existing session, read `AGENT-START.md` directly; persistent discovery begins after the repository is cloned/opened and the client discovers project files.

Official sources: [Build skills](https://learn.chatgpt.com/docs/build-skills) and [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
