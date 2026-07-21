---
name: optimize-agent-capabilities
description: >-
  Explicitly audit and optimize Skill, Plugin, MCP, hook, and rules visibility across coding-agent
  clients. Use only when the user requests capability cleanup, routing optimization, or a repeat
  audit after client or extension updates. Never change client configuration implicitly.
---

# Optimize Agent Capabilities

Treat the repository's L0-L4 documents and templates as the source of truth. This Skill is an
optional execution entry, not a second routing specification.

## Workflow

1. Run the read-only inventory:

   ```bash
   node <skill-dir>/scripts/audit.mjs --json
   ```

2. Read only the matching profile in `profiles/`.
3. Classify every detected client:
   - `managed`: a tested adapter may apply reversible changes after explicit approval.
   - `audit-only`: report findings and a client-specific plan; do not edit client configuration.
   - `unknown`: use the generic profile and do not infer configuration keys or paths.
4. Build or update the shared L1-L4 router before changing L0 visibility.
5. For Codex, use the bundled adapter only after the user approves configuration changes:

   ```bash
   node <skill-dir>/scripts/reconcile-codex.mjs --check
   node <skill-dir>/scripts/reconcile-codex.mjs --apply
   node <skill-dir>/scripts/reconcile-codex.mjs --verify
   ```

6. Report changed files, backup paths, verification evidence, and restart requirements.

## Safety

- Start every run in audit mode.
- Never install, uninstall, enable, disable, or rewrite configuration without explicit approval.
- Do not edit extension caches directly.
- Do not claim support from format similarity alone; client discovery and invocation controls differ.
- Preserve explicit invocation wherever the client supports it.
- Unknown clients receive a plan, not guessed mutations.

## Extending Clients

Add a profile first. Add a write-capable adapter only when all five operations are deterministic and
tested: `detect`, `inventory`, `plan`, `apply`, and `verify`. See `references/client-adapters.md`.
