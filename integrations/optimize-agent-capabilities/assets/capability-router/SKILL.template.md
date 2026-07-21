---
name: capability-router
description: "Route natural-language requests to one explicit-only capability without loading the full catalog."
---

# Capability Router

1. First decide whether the task can be completed without an extra capability.
2. When an extra capability is needed, read `$CODEX_HOME/capability-optimizer/capability-index.json`.
3. Select one best candidate from its name, description, type, and source.
4. Read only that candidate's `SKILL.md` before execution.
5. For Plugin wrappers, invoke or read the wrapper; it resolves the current Plugin implementation.
6. Check permissions, external effects, health, and rollback before acting.
7. Do not scan the complete Skill or Plugin directories during ordinary tasks.
