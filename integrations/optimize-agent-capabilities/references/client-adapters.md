# Client adapter contract

The optimizer separates shared routing policy from client-specific configuration.

| Operation | Requirement |
| --- | --- |
| `detect` | Identify the client and version without changing state. |
| `inventory` | Enumerate rules, Skills, Plugins, MCP servers, hooks, and native visibility controls. |
| `plan` | Produce a reversible diff and identify unsupported assumptions. |
| `apply` | Require explicit approval, back up every changed file, and make idempotent writes. |
| `verify` | Start a clean client process or use an official diagnostic command. |

Support levels:

- `managed`: all five operations are implemented and tested.
- `audit-only`: detection and inventory are reliable; configuration remains advisory.
- `unknown`: only shared filesystem conventions are inspected.

Profiles describe evidence and discovery locations. They are not permission to write. A client moves
to `managed` only after its adapter has fixtures, idempotency tests, rollback coverage, and a clean
process verification method.

Do not create one monolithic adapter with branches for every product. Each write-capable client
adapter owns only its native settings and delegates shared L1-L4 artifacts to the core workflow.
