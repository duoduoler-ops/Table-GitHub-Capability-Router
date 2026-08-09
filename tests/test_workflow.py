from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_vault_workflow", REPO_ROOT / "scripts" / "workflow.py")
workflow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = workflow
SPEC.loader.exec_module(workflow)


class WorkflowCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="agent-vault-test-")
        self.root = Path(self.temp.name) / "vault"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def invoke(self, *args: str) -> tuple[int, dict]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = workflow.main(list(args))
        stream = stdout.getvalue() if code == 0 else stderr.getvalue()
        return code, json.loads(stream)

    def initialize(self, client: str = "generic-agent") -> dict:
        code, result = self.invoke(
            "init",
            "--root",
            str(self.root),
            "--language",
            "zh-CN",
            "--client",
            client,
        )
        self.assertEqual(code, 0, result)
        return result

    def test_init_is_valid_and_idempotent(self) -> None:
        created = self.initialize("codex")
        self.assertEqual(created["result"], "created")
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)
        self.assertEqual(validation["projects"], 0)
        self.assertEqual(validation["capabilities"], 0)
        self.assertEqual(validation["schema_version"], 2)
        agent_router = (self.root / "AGENT-ROUTER.md").read_text(encoding="utf-8")
        self.assertIn("For every substantive task", agent_router)
        self.assertIn("high_confidence` and `gated` both allow a reminder", agent_router)
        again = self.initialize("codex")
        self.assertEqual(again["result"], "already_initialized")

    def test_init_accepts_grok_build_client_profile(self) -> None:
        created = self.initialize("grok-build")
        self.assertEqual(created["result"], "created")
        config = json.loads((self.root / "workflow.json").read_text(encoding="utf-8"))
        self.assertEqual(config["schema_version"], 2)
        self.assertEqual(config["client_profile"], "grok-build")
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

    def test_project_url_is_canonical_and_idempotent(self) -> None:
        self.initialize()
        code, first = self.invoke(
            "new-project",
            "--root",
            str(self.root),
            "--url",
            "https://github.com/Example-Org/Sample-Repo.git?tab=readme#top",
        )
        self.assertEqual(code, 0, first)
        self.assertEqual(first["id"], "gh-example-org-sample-repo")
        code, second = self.invoke(
            "new-project",
            "--root",
            str(self.root),
            "--url",
            "example-org/sample-repo",
        )
        self.assertEqual(code, 0, second)
        self.assertEqual(second["result"], "existing")
        cards = list((self.root / "projects" / "records").glob("*.md"))
        self.assertEqual(len(cards), 1)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

    def test_project_promotion_requires_approval_and_grade(self) -> None:
        self.initialize()
        self.invoke("new-project", "--root", str(self.root), "--url", "example/project")
        code, evaluated = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-project",
            "--to",
            "evaluated",
        )
        self.assertEqual(code, 0, evaluated)
        code, blocked = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-project",
            "--to",
            "retained",
            "--grade",
            "A",
        )
        self.assertEqual(code, 2)
        self.assertIn("approval", blocked["error"].lower())
        code, blocked = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-project",
            "--to",
            "retained",
            "--grade",
            "A",
            "--approved",
            "--approved-by",
            "demo-user",
        )
        self.assertEqual(code, 2)
        self.assertIn("semantic routing", blocked["error"].lower())
        code, promoted = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-project",
            "--to",
            "retained",
            "--grade",
            "A",
            "--approved",
            "--approved-by",
            "demo-user",
            "--capability-summary",
            "Compare repository patterns and produce one reusable reference decision",
            "--semantic-example",
            "Help me compare project patterns",
            "--semantic-example",
            "Suggest a reusable GitHub reference",
            "--trigger-level",
            "high_confidence",
            "--negative-routing",
            "Do not route when the user already selected an implementation",
        )
        self.assertEqual(code, 0, promoted)
        semantic_router = (self.root / "indexes" / "project-semantic-routing.md").read_text(encoding="utf-8")
        matching_rows = [
            line for line in semantic_router.splitlines() if line.startswith("| [gh-example-project]")
        ]
        self.assertEqual(len(matching_rows), 2)
        self.assertIn("Thin Discovery / 薄发现表", semantic_router)
        self.assertIn("Compare repository patterns and produce one reusable reference decision", semantic_router)
        self.assertIn("Help me compare project patterns", semantic_router)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)
        self.assertEqual(validation["semantic_projects"], 1)

    def test_semantic_routing_update_and_stale_table_rebuild(self) -> None:
        self.initialize()
        self.invoke("new-project", "--root", str(self.root), "--url", "example/reference")
        self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-reference",
            "--to",
            "evaluated",
        )
        code, promoted = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-reference",
            "--to",
            "reference",
            "--grade",
            "B",
            "--approved",
            "--capability-summary",
            "Compare workflow references and produce one reusable recommendation",
            "--semantic-example",
            "Make this workflow easier to reuse",
            "--semantic-example",
            "Show me one relevant reference project",
            "--trigger-level",
            "gated",
            "--negative-routing",
            "Do not route for a simple direct answer",
        )
        self.assertEqual(code, 0, promoted)
        code, updated = self.invoke(
            "project-routing",
            "--root",
            str(self.root),
            "--id",
            "gh-example-reference",
            "--capability-summary",
            "Compare saved projects and produce one workflow improvement reference",
            "--semantic-example",
            "Compare an ordinary approach with a project-informed approach",
            "--semantic-example",
            "Which saved project can improve this workflow",
            "--trigger-level",
            "high_confidence",
            "--negative-routing",
            "Do not route when no extra project is needed",
        )
        self.assertEqual(code, 0, updated)
        self.assertEqual(updated["semantic_examples"], 2)
        self.assertEqual(
            updated["capability_summary"],
            "Compare saved projects and produce one workflow improvement reference",
        )
        semantic_router = self.root / "indexes" / "project-semantic-routing.md"
        self.assertIn("Compare an ordinary approach", semantic_router.read_text(encoding="utf-8"))
        self.assertIn("remind / 先提醒", semantic_router.read_text(encoding="utf-8"))
        semantic_router.write_text(
            semantic_router.read_text(encoding="utf-8") + "manual drift\n",
            encoding="utf-8",
        )
        code, stale = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("stale", stale["error"].lower())
        code, rebuilt = self.invoke("rebuild", "--root", str(self.root))
        self.assertEqual(code, 0, rebuilt)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

    def test_ineligible_project_is_excluded_from_semantic_routing(self) -> None:
        self.initialize()
        self.invoke("new-project", "--root", str(self.root), "--url", "example/rejected")
        code, rejected = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-rejected",
            "--to",
            "rejected",
            "--grade",
            "D",
        )
        self.assertEqual(code, 0, rejected)
        semantic_router = (self.root / "indexes" / "project-semantic-routing.md").read_text(encoding="utf-8")
        self.assertNotIn("gh-example-rejected", semantic_router)
        code, blocked = self.invoke(
            "project-routing",
            "--root",
            str(self.root),
            "--id",
            "gh-example-rejected",
            "--capability-summary",
            "Route a rejected project and produce an invalid suggestion",
            "--semantic-example",
            "This should stay excluded",
            "--semantic-example",
            "Do not route a rejected project",
            "--trigger-level",
            "high_confidence",
            "--negative-routing",
            "Rejected projects are never eligible",
        )
        self.assertEqual(code, 2)
        self.assertIn("only retained/reference", blocked["error"].lower())

    def test_missing_semantic_metadata_is_reported_without_crashing(self) -> None:
        self.initialize()
        self.invoke("new-project", "--root", str(self.root), "--url", "example/missing-routing")
        card = self.root / "projects" / "records" / "gh-example-missing-routing.md"
        card.write_text(
            card.read_text(encoding="utf-8").replace("semantic_examples: none\n", ""),
            encoding="utf-8",
        )
        code, result = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("semantic_examples", result["error"])

    def test_duplicate_semantic_example_across_projects_is_blocked(self) -> None:
        self.initialize()
        shared = "Use the same everyday wording"
        for slug in ("first", "second"):
            self.invoke("new-project", "--root", str(self.root), "--url", f"example/{slug}")
            self.invoke(
                "project-transition",
                "--root",
                str(self.root),
                "--id",
                f"gh-example-{slug}",
                "--to",
                "evaluated",
            )
        code, first = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-first",
            "--to",
            "reference",
            "--grade",
            "B",
            "--approved",
            "--capability-summary",
            "Compare the first pattern and produce a bounded reference",
            "--semantic-example",
            shared,
            "--semantic-example",
            "First project specific wording",
            "--trigger-level",
            "gated",
            "--negative-routing",
            "Do not route outside the first project scope",
        )
        self.assertEqual(code, 0, first)
        code, duplicate = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-second",
            "--to",
            "reference",
            "--grade",
            "B",
            "--approved",
            "--capability-summary",
            "Compare the second pattern and produce a bounded reference",
            "--semantic-example",
            shared,
            "--semantic-example",
            "Second project specific wording",
            "--trigger-level",
            "gated",
            "--negative-routing",
            "Do not route outside the second project scope",
        )
        self.assertEqual(code, 2)
        self.assertIn("duplicate semantic example", duplicate["error"].lower())
        data, _ = workflow.parse_frontmatter(
            (self.root / "projects" / "records" / "gh-example-second.md").read_text(encoding="utf-8")
        )
        self.assertEqual(data["status"], "evaluated")

    def test_duplicate_capability_summary_across_projects_is_blocked(self) -> None:
        self.initialize()
        shared_summary = "Compare repository patterns and produce one reusable implementation guide"
        for slug in ("alpha", "beta"):
            self.invoke("new-project", "--root", str(self.root), "--url", f"example/{slug}")
            self.invoke(
                "project-transition",
                "--root",
                str(self.root),
                "--id",
                f"gh-example-{slug}",
                "--to",
                "evaluated",
            )
        code, first = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-alpha",
            "--to",
            "reference",
            "--grade",
            "B",
            "--approved",
            "--capability-summary",
            shared_summary,
            "--semantic-example",
            "Use the alpha pattern",
            "--semantic-example",
            "Compare the alpha reference",
            "--trigger-level",
            "gated",
            "--negative-routing",
            "Do not route outside alpha scope",
        )
        self.assertEqual(code, 0, first)
        code, duplicate = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-beta",
            "--to",
            "reference",
            "--grade",
            "B",
            "--approved",
            "--capability-summary",
            shared_summary,
            "--semantic-example",
            "Use the beta pattern",
            "--semantic-example",
            "Compare the beta reference",
            "--trigger-level",
            "gated",
            "--negative-routing",
            "Do not route outside beta scope",
        )
        self.assertEqual(code, 2)
        self.assertIn("duplicate capability summary", duplicate["error"].lower())

    def test_schema_v1_migration_requires_summaries_and_is_idempotent(self) -> None:
        self.initialize()
        self.invoke("new-project", "--root", str(self.root), "--url", "example/migrate-reference")
        self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-migrate-reference",
            "--to",
            "evaluated",
        )
        code, promoted = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-migrate-reference",
            "--to",
            "reference",
            "--grade",
            "B",
            "--approved",
            "--capability-summary",
            "Compare migration patterns and produce a reusable upgrade plan",
            "--semantic-example",
            "Help me migrate this routing vault",
            "--semantic-example",
            "Show one saved migration reference",
            "--trigger-level",
            "gated",
            "--negative-routing",
            "Do not route for an unrelated one-line answer",
        )
        self.assertEqual(code, 0, promoted)

        config_path = self.root / "workflow.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["schema_version"] = 1
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        card = self.root / "projects" / "records" / "gh-example-migrate-reference.md"
        card.write_text(
            card.read_text(encoding="utf-8")
            .replace("schema_version: 2", "schema_version: 1")
            .replace(
                "capability_summary: Compare migration patterns and produce a reusable upgrade plan\n",
                "",
            ),
            encoding="utf-8",
        )

        broken_config = dict(config)
        broken_config["route_categories"] = [*config["route_categories"], config["route_categories"][0]]
        config_path.write_text(
            json.dumps(broken_config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        code, broken = self.invoke(
            "migrate-v2",
            "--root",
            str(self.root),
            "--capability-summary",
            "gh-example-migrate-reference=Compare migration patterns and produce a reusable upgrade plan",
        )
        self.assertEqual(code, 2)
        self.assertIn("route_categories", broken["error"])
        self.assertEqual(json.loads(config_path.read_text(encoding="utf-8"))["schema_version"], 1)
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        code, blocked = self.invoke("migrate-v2", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("missing", blocked["error"].lower())
        self.assertEqual(json.loads(config_path.read_text(encoding="utf-8"))["schema_version"], 1)

        code, migrated = self.invoke(
            "migrate-v2",
            "--root",
            str(self.root),
            "--capability-summary",
            "gh-example-migrate-reference=Compare migration patterns and produce a reusable upgrade plan",
        )
        self.assertEqual(code, 0, migrated)
        self.assertEqual(migrated["result"], "migrated")
        self.assertEqual(migrated["schema_version"], 2)
        router = (self.root / "indexes" / "project-semantic-routing.md").read_text(encoding="utf-8")
        self.assertIn("Thin Discovery / 薄发现表", router)
        self.assertIn("gate before read or run", router)
        code, again = self.invoke("migrate-v2", "--root", str(self.root))
        self.assertEqual(code, 0, again)
        self.assertEqual(again["result"], "already_migrated")

    def test_invalid_semantic_trigger_is_reported_without_crashing(self) -> None:
        self.initialize()
        self.invoke("new-project", "--root", str(self.root), "--url", "example/invalid-trigger")
        self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-invalid-trigger",
            "--to",
            "evaluated",
        )
        code, promoted = self.invoke(
            "project-transition",
            "--root",
            str(self.root),
            "--id",
            "gh-example-invalid-trigger",
            "--to",
            "reference",
            "--grade",
            "B",
            "--approved",
            "--capability-summary",
            "Find one relevant project and produce a reference suggestion",
            "--semantic-example",
            "Find one relevant reference",
            "--semantic-example",
            "Use a saved project for this task",
            "--trigger-level",
            "high_confidence",
            "--negative-routing",
            "Do not route when the ordinary answer is enough",
        )
        self.assertEqual(code, 0, promoted)
        card = self.root / "projects" / "records" / "gh-example-invalid-trigger.md"
        card.write_text(
            card.read_text(encoding="utf-8").replace(
                "trigger_level: high_confidence",
                "trigger_level: invalid",
            ),
            encoding="utf-8",
        )
        code, result = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("invalid trigger_level", result["error"].lower())

    def test_reviewed_project_update_preserves_protected_state(self) -> None:
        self.initialize()
        self.invoke("new-project", "--root", str(self.root), "--url", "example/evidence-project")
        card = self.root / "projects" / "records" / "gh-example-evidence-project.md"
        draft = self.root.parent / "project-draft.md"
        original = card.read_text(encoding="utf-8")
        draft.write_text(original.replace("status: candidate", "status: retained") + "\nReviewed evidence.\n", encoding="utf-8")
        code, blocked = self.invoke(
            "update-project",
            "--root",
            str(self.root),
            "--id",
            "gh-example-evidence-project",
            "--from-file",
            str(draft),
        )
        self.assertEqual(code, 2)
        self.assertIn("protected frontmatter", blocked["error"].lower())
        draft.write_text(original + "\nReviewed evidence.\n", encoding="utf-8")
        code, updated = self.invoke(
            "update-project",
            "--root",
            str(self.root),
            "--id",
            "gh-example-evidence-project",
            "--from-file",
            str(draft),
            "--evidence-level",
            "online-check",
        )
        self.assertEqual(code, 0, updated)
        self.assertEqual(updated["revision"], 2)
        data, body = workflow.parse_frontmatter(card.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "candidate")
        self.assertEqual(data["evidence_level"], "online-check")
        self.assertIn("Reviewed evidence.", body)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

    def test_reviewed_capability_update_preserves_protected_state(self) -> None:
        self.initialize()
        self.invoke(
            "new-capability",
            "--root",
            str(self.root),
            "--id",
            "reviewed-tool",
            "--name",
            "Reviewed Tool",
            "--type",
            "CLI",
            "--route-category",
            "local-files",
        )
        card = self.root / "capabilities" / "records" / "reviewed-tool.md"
        draft = self.root.parent / "capability-draft.md"
        draft.write_text(card.read_text(encoding="utf-8") + "\nReviewed rollback notes.\n", encoding="utf-8")
        code, updated = self.invoke(
            "update-capability",
            "--root",
            str(self.root),
            "--id",
            "reviewed-tool",
            "--from-file",
            str(draft),
        )
        self.assertEqual(code, 0, updated)
        data, body = workflow.parse_frontmatter(card.read_text(encoding="utf-8"))
        self.assertEqual(data["management_state"], "candidate")
        self.assertEqual(data["revision"], "2")
        self.assertIn("Reviewed rollback notes.", body)

    def test_capability_active_and_auto_require_health_and_approval(self) -> None:
        self.initialize()
        code, created = self.invoke(
            "new-capability",
            "--root",
            str(self.root),
            "--id",
            "sample-search",
            "--name",
            "Sample Search",
            "--type",
            "Skill",
            "--route-category",
            "public-research",
            "--risk",
            "low",
        )
        self.assertEqual(code, 0, created)
        router = (self.root / "router" / "level1-router.md").read_text(encoding="utf-8")
        self.assertNotIn("sample-search", router)
        code, blocked = self.invoke(
            "capability-transition",
            "--root",
            str(self.root),
            "--id",
            "sample-search",
            "--to",
            "active",
            "--approved",
        )
        self.assertEqual(code, 2)
        self.assertIn("healthy", blocked["error"].lower())
        code, health = self.invoke(
            "capability-health",
            "--root",
            str(self.root),
            "--id",
            "sample-search",
            "--to",
            "healthy",
            "--evidence",
            "Synthetic T0 check passed",
        )
        self.assertEqual(code, 0, health)
        code, blocked = self.invoke(
            "capability-transition",
            "--root",
            str(self.root),
            "--id",
            "sample-search",
            "--to",
            "active",
            "--invocation",
            "auto",
        )
        self.assertEqual(code, 2)
        self.assertIn("approval", blocked["error"].lower())
        code, active = self.invoke(
            "capability-transition",
            "--root",
            str(self.root),
            "--id",
            "sample-search",
            "--to",
            "active",
            "--invocation",
            "auto",
            "--approved",
        )
        self.assertEqual(code, 0, active)
        router = (self.root / "router" / "level1-router.md").read_text(encoding="utf-8")
        self.assertIn("sample-search", router)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

    def test_manager_type_cannot_auto_route_and_disabled_is_absent(self) -> None:
        self.initialize()
        code, created = self.invoke(
            "new-capability",
            "--root",
            str(self.root),
            "--id",
            "session-manager",
            "--name",
            "Session Manager",
            "--type",
            "Plugin",
            "--route-category",
            "governance",
            "--risk",
            "high",
            "--manager-type",
        )
        self.assertEqual(code, 0, created)
        code, health = self.invoke(
            "capability-health",
            "--root",
            str(self.root),
            "--id",
            "session-manager",
            "--to",
            "healthy",
            "--evidence",
            "Synthetic isolated check",
        )
        self.assertEqual(code, 0, health)
        code, blocked = self.invoke(
            "capability-transition",
            "--root",
            str(self.root),
            "--id",
            "session-manager",
            "--to",
            "active",
            "--invocation",
            "auto",
            "--approved",
        )
        self.assertEqual(code, 2)
        self.assertIn("manager-type", blocked["error"].lower())
        code, disabled = self.invoke(
            "capability-transition",
            "--root",
            str(self.root),
            "--id",
            "session-manager",
            "--to",
            "disabled",
        )
        self.assertEqual(code, 0, disabled)
        router = (self.root / "router" / "level1-router.md").read_text(encoding="utf-8")
        self.assertNotIn("session-manager", router)

    def test_active_health_failure_auto_quarantines(self) -> None:
        self.initialize()
        self.invoke(
            "new-capability",
            "--root",
            str(self.root),
            "--id",
            "fragile-tool",
            "--name",
            "Fragile Tool",
            "--type",
            "CLI",
            "--route-category",
            "local-files",
        )
        self.invoke(
            "capability-health",
            "--root",
            str(self.root),
            "--id",
            "fragile-tool",
            "--to",
            "healthy",
            "--evidence",
            "Synthetic isolated check",
        )
        code, active = self.invoke(
            "capability-transition",
            "--root",
            str(self.root),
            "--id",
            "fragile-tool",
            "--to",
            "active",
            "--approved",
        )
        self.assertEqual(code, 0, active)
        code, degraded = self.invoke(
            "capability-health",
            "--root",
            str(self.root),
            "--id",
            "fragile-tool",
            "--to",
            "degraded",
            "--evidence",
            "Synthetic health check failed",
        )
        self.assertEqual(code, 0, degraded)
        card = (self.root / "capabilities" / "records" / "fragile-tool.md").read_text(encoding="utf-8")
        data, _ = workflow.parse_frontmatter(card)
        self.assertEqual(data["management_state"], "quarantine")
        self.assertEqual(data["invocation"], "disabled")
        router = (self.root / "router" / "level1-router.md").read_text(encoding="utf-8")
        self.assertNotIn("fragile-tool", router)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

    def test_stale_generated_router_fails_then_rebuilds(self) -> None:
        self.initialize()
        router = self.root / "router" / "level1-router.md"
        router.write_text(router.read_text(encoding="utf-8") + "manual drift\n", encoding="utf-8")
        code, result = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("stale", result["error"].lower())
        code, rebuilt = self.invoke("rebuild", "--root", str(self.root))
        self.assertEqual(code, 0, rebuilt)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

    def test_existing_lock_blocks_mutation(self) -> None:
        self.initialize()
        lock = self.root / ".workflow" / "lock"
        lock.write_text('{"pid": 99999}', encoding="utf-8")
        code, result = self.invoke(
            "new-project",
            "--root",
            str(self.root),
            "--url",
            "example/locked",
        )
        self.assertEqual(code, 2)
        self.assertIn("locked", result["error"].lower())
        lock.unlink()

    def test_invalid_non_github_url_is_rejected(self) -> None:
        self.initialize()
        code, result = self.invoke(
            "new-project",
            "--root",
            str(self.root),
            "--url",
            "https://example.com/not-github/project",
        )
        self.assertEqual(code, 2)
        self.assertIn("github.com", result["error"])

    def test_public_repository_validation(self) -> None:
        code, result = self.invoke("validate-repo", "--root", str(REPO_ROOT))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["errors"], 0)
        if (REPO_ROOT / ".git").exists() and workflow.shutil.which("git"):
            self.assertTrue(result["history_scanned"])

    def test_repository_secret_scan_detects_private_windows_paths(self) -> None:
        findings = workflow.secret_findings(
            "Private vault: " + "D:" + r"\AI-Knowledge\notes.md",
            "fixture",
            workflow.REPOSITORY_SECRET_PATTERNS,
        )
        self.assertTrue(any("private Windows path" in item for item in findings))
        self.assertEqual(
            workflow.secret_findings(
                "Public fixture: " + "D:" + r"\example\demo.md",
                "fixture",
                workflow.REPOSITORY_SECRET_PATTERNS,
            ),
            [],
        )
        self.assertEqual(
            workflow.secret_findings(
                r'rg -n "C:\\Users|D:\\" .',
                "escaped documentation example",
                workflow.REPOSITORY_SECRET_PATTERNS,
            ),
            [],
        )

    def test_generated_demo_is_valid(self) -> None:
        demo = REPO_ROOT / "examples" / "generated-demo-v1"
        code, result = self.invoke("validate", "--root", str(demo))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["projects"], 2)
        self.assertEqual(result["capabilities"], 3)


if __name__ == "__main__":
    unittest.main()
