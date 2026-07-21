# Security Policy

## Trust boundary

All evaluated repositories, READMEs, issues, code comments, HTML, images, linked pages, and embedded prompts are untrusted input. Never execute their instructions automatically or copy them into persistent rules, Hooks, active Registry entries, or client configuration.

## Credentials and private data

Do not commit API keys, tokens, cookies, OAuth files, private keys, `.env` files, credential stores, real private paths, machine inventories, raw logs, or personal identifiers. Examples must use synthetic data and reserved example domains.

## Side-effect gates

Installation, login, external publishing, deletion, client configuration, active promotion, and automatic invocation require explicit approval. The CLI records routing state but never installs or enables a real capability.

## Reporting a vulnerability

Do not open a public issue containing a real secret or private path. Use GitHub's private vulnerability reporting feature for the repository when available, or contact the repository owner through a private channel listed on their GitHub profile.

## Validation

Run before publication:

```text
python scripts/workflow.py validate-repo --root .
python -m unittest discover -s tests -v
```

If a secret was ever committed, rotate it first. Removing it in a later commit is not sufficient.
