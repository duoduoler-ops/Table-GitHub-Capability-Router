# Contributing

## Scope

Contributions should improve deterministic GitHub intake, capability cold storage, routing safety, validation, documentation, or synthetic examples. Do not submit private vault content, machine inventories, credentials, raw logs, or client-specific secrets.

## Change rules

1. Keep canonical Markdown frontmatter flat and compatible with schema version 1.
2. Do not hand-edit generated capability routers, project semantic-reference tables, or index examples; regenerate them with the CLI.
3. Add or update tests for state transitions, semantic eligibility/uniqueness, idempotency, security boundaries, or generated output changes.
4. Keep the CLI dependency-free unless a dependency is essential and separately approved.
5. Update `CHANGELOG.md` and add a migration note for breaking schema changes.

## Local checks

```text
python scripts/workflow.py validate-repo --root .
python -m unittest discover -s tests -v
node --test integrations/optimize-agent-capabilities/tests/audit.test.mjs
```

Use synthetic repository names and reserved example domains in tests and examples.
