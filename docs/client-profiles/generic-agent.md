# Generic Agent Profile

Use this profile when the coding agent does not document repo-scoped Skills.

1. Give the agent the repository URL and ask it to read `AGENT-START.md` only.
2. Let it use an existing Python 3 interpreter to initialize an isolated output directory.
3. Persist only the generated `AGENT-ROUTER.md` pointer in the user's chosen project after explicit approval.
4. Keep automatic invocation claims bounded: without a documented project Skill or durable rules surface, this is prompt-triggered automation, not guaranteed native auto-discovery.

The deterministic CLI and generated files remain client-independent; only discovery and invocation policy vary by client.
