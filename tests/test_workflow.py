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
        again = self.initialize("codex")
        self.assertEqual(again["result"], "already_initialized")

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
        )
        self.assertEqual(code, 0, promoted)
        code, validation = self.invoke("validate", "--root", str(self.root))
        self.assertEqual(code, 0, validation)

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

    def test_generated_demo_is_valid(self) -> None:
        demo = REPO_ROOT / "examples" / "generated-demo-v1"
        code, result = self.invoke("validate", "--root", str(demo))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["projects"], 2)
        self.assertEqual(result["capabilities"], 3)


if __name__ == "__main__":
    unittest.main()
