# Migration 0001: Initial deterministic schema

Schema version 1 introduces flat YAML frontmatter for canonical project and capability records, plus `workflow.json` for routing categories and output paths. Because the deterministic schema first ships with v0.2.0, semantic project-reference fields are included in schema v1 rather than requiring an immediate schema bump.

## New canonical rules

- One GitHub repository maps to one `gh-owner-repo` project ID.
- One capability maps to one lowercase hyphenated capability ID.
- Project and capability records carry `revision` and `updated_at`.
- Indexes, semantic project references, candidate/rejection views, and the capability router are generated outputs.
- Approved S/A/B `retained/reference` projects require at least two semantic examples, one trigger level, and negative routing.
- Candidate, evaluated, rejected, archived, C, and D projects use `none / explicit_only / none` and never enter semantic routing.
- Old Markdown without versioned frontmatter remains reference material until explicitly migrated; the CLI never rewrites it automatically.

## Migration procedure

1. Initialize a new isolated workflow root.
2. Add old projects one at a time through `new-project` using their canonical URLs.
3. Copy only reviewed evidence into the new canonical card.
4. Add capabilities as `candidate / unverified / explicit-only`.
5. Record health evidence and request approval before promotion.
6. Run `rebuild` and `validate`.

Use `update-project --from-file` and `update-capability --from-file` for reviewed body migrations. Do not paste old frontmatter over schema v1 records; protected metadata is preserved by the CLI.

This page describes the historical schema v1 baseline. With the current CLI, first migrate the vault to schema v3 and follow the [current write protocol](../write-protocol.md), including `record-hash` and `--expected-sha256` for reviewed drafts.

Do not bulk-copy a private vault, raw logs, client settings, credentials, or machine-specific inventory into a public or newly initialized workflow.
