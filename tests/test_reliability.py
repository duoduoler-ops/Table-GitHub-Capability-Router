from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_workflow as baseline

REPO_ROOT = baseline.REPO_ROOT
workflow = baseline.workflow


class ReliabilityTests(unittest.TestCase):
    invoke = baseline.WorkflowCLITests.invoke
    initialize = baseline.WorkflowCLITests.initialize

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-reliability-")
        self.root = Path(self.temp.name) / "vault"
        self.initialize()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def project(self) -> Path:
        code, result = self.invoke("new-project", "--root", str(self.root), "--url", "example/reliability")
        self.assertEqual(code, 0, result)
        return self.root / "projects/records/gh-example-reliability.md"

    def update(self, draft: Path, base_hash: str | None) -> tuple[int, dict]:
        args = ["update-project", "--root", str(self.root), "--id", "gh-example-reliability", "--from-file", str(draft)]
        if base_hash is not None:
            args.extend(["--expected-sha256", base_hash])
        return self.invoke(*args)

    def receipt(self, transaction) -> dict:
        return json.loads((transaction.dir / "manifest.json").read_text(encoding="utf-8"))

    def test_stale_draft_hash_and_revision_are_rejected(self) -> None:
        card = self.project()
        old_hash = workflow.file_hash(card)
        draft = self.root / "draft.md"
        original = card.read_text(encoding="utf-8")
        draft.write_text(original + "\nFirst review.\n", encoding="utf-8")
        self.assertEqual(self.update(draft, old_hash)[0], 0)
        current = card.read_bytes()
        code, result = self.update(draft, old_hash)
        self.assertEqual(code, 2)
        self.assertIn("Stale draft", result["error"])
        # Supplying today's hash must not make an old revision acceptable.
        code, result = self.update(draft, workflow.file_hash(card))
        self.assertEqual(code, 2)
        self.assertIn("revision", result["error"])
        self.assertEqual(card.read_bytes(), current)

    def test_body_change_without_revision_also_invalidates_draft(self) -> None:
        card = self.project()
        base_hash = workflow.file_hash(card)
        draft = self.root / "draft.md"
        draft.write_bytes(card.read_bytes() + b"\nReview.\n")
        card.write_bytes(card.read_bytes() + b"\nConcurrent manual evidence.\n")
        expected = card.read_bytes()
        self.assertEqual(self.update(draft, base_hash)[0], 2)
        self.assertEqual(card.read_bytes(), expected)

    def test_missing_hash_fails_without_business_writes(self) -> None:
        card = self.project()
        draft = self.root / "draft.md"
        draft.write_bytes(card.read_bytes())
        before = card.read_bytes()
        code, result = self.update(draft, None)
        self.assertEqual(code, 2)
        self.assertIn("--expected-sha256", result["error"])
        self.assertEqual(card.read_bytes(), before)

    def test_record_hash_is_read_only_and_matches_raw_bytes(self) -> None:
        card = self.project()
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        code, result = self.invoke("record-hash", "--root", str(self.root), "--kind", "project", "--id", "gh-example-reliability")
        self.assertEqual(code, 0, result)
        self.assertEqual(result["sha256"], hashlib.sha256(card.read_bytes()).hexdigest())
        self.assertEqual(result["revision"], 1)
        self.assertEqual(before, {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_edit_after_source_read_is_preserved(self) -> None:
        card = self.project()
        base_hash = workflow.file_hash(card)
        draft = self.root / "draft.md"
        draft.write_bytes(card.read_bytes() + b"\nReviewed draft.\n")
        original_add = workflow.Transaction.add
        concurrent = card.read_bytes() + b"\nAnother writer.\n"

        def change_before_add(transaction, path, content):
            if path == card:
                card.write_bytes(concurrent)
            return original_add(transaction, path, content)

        with patch.object(workflow.Transaction, "add", change_before_add):
            code, result = self.update(draft, base_hash)
        self.assertEqual(code, 2)
        self.assertIn("Concurrent change", result["error"])
        self.assertEqual(card.read_bytes(), concurrent)

    def test_write_failure_restores_exact_original_bytes(self) -> None:
        first, second = self.root / "first.txt", self.root / "second.txt"
        original = "before\r\n中文\r\n".encode("utf-8")
        first.write_bytes(original)
        second.write_bytes(b"unchanged")
        transaction = workflow.Transaction(self.root, "failure-fixture")
        transaction.add(first, "after\n")
        transaction.add(second, "new second")
        real_write = workflow.atomic_write

        def fail_second(path, content):
            if path == second:
                raise OSError("injected write failure")
            real_write(path, content)

        with patch.object(workflow, "atomic_write", fail_second):
            with self.assertRaises(OSError):
                transaction.commit()
        self.assertEqual(first.read_bytes(), original)
        self.assertEqual(second.read_bytes(), b"unchanged")
        self.assertEqual(self.receipt(transaction)["status"], "rolled_back")

    def test_rollback_preserves_concurrent_edit_and_continues_other_restores(self) -> None:
        paths = [self.root / name for name in ("first.txt", "second.txt", "third.txt")]
        for path in paths:
            path.write_bytes(b"before")
        transaction = workflow.Transaction(self.root, "conflict-fixture")
        for path in paths:
            transaction.add(path, "after")
        real_write = workflow.atomic_write

        def conflict(path, content):
            if path == paths[2]:
                paths[1].write_bytes(b"external edit")
                raise OSError("injected write failure")
            real_write(path, content)

        with patch.object(workflow, "atomic_write", conflict):
            with self.assertRaises(OSError):
                transaction.commit()
        self.assertEqual([path.read_bytes() for path in paths], [b"before", b"external edit", b"before"])
        receipt = self.receipt(transaction)
        self.assertEqual(receipt["status"], "recovery_required")
        self.assertIn("second.txt", receipt["recovery"][0])

    def test_post_write_validation_failure_rolls_back(self) -> None:
        path = self.root / "note.txt"
        path.write_bytes(b"before")
        transaction = workflow.Transaction(self.root, "validation-fixture")
        transaction.add(path, "after")
        with patch.object(workflow, "collect_validation", return_value=(["injected invalid state"], {})):
            with self.assertRaises(workflow.WorkflowError):
                transaction.commit()
        self.assertEqual(path.read_bytes(), b"before")
        self.assertEqual(self.receipt(transaction)["status"], "rolled_back")

    def test_failed_restore_is_recorded_and_other_restores_continue(self) -> None:
        first, second = self.root / "first.txt", self.root / "second.txt"
        for path in (first, second):
            path.write_bytes(b"before")
        transaction = workflow.Transaction(self.root, "restore-failure-fixture")
        transaction.add(first, "after")
        transaction.add(second, "after")
        real_write = workflow.atomic_write

        def fail_one_restore(path, content):
            if path == second and content == b"before":
                raise OSError("injected restore failure")
            real_write(path, content)

        with patch.object(workflow, "collect_validation", return_value=(["invalid state"], {})):
            with patch.object(workflow, "atomic_write", fail_one_restore):
                with self.assertRaises(workflow.WorkflowError):
                    transaction.commit()
        self.assertEqual(first.read_bytes(), b"before")
        self.assertEqual(second.read_bytes(), b"after")
        receipt = self.receipt(transaction)
        self.assertEqual(receipt["status"], "recovery_required")
        self.assertIn("second.txt", receipt["recovery"][0])

    def test_capability_draft_requires_unchanged_base(self) -> None:
        code, result = self.invoke("new-capability", "--root", str(self.root), "--id", "sample", "--name", "Sample",
                                   "--type", "Skill", "--route-category", "governance")
        self.assertEqual(code, 0, result)
        card = self.root / "capabilities/records/sample.md"
        draft = self.root / "capability-draft.md"
        draft.write_bytes(card.read_bytes() + b"\nReviewed evidence.\n")
        code, result = self.invoke("record-hash", "--root", str(self.root), "--kind", "capability", "--id", "sample")
        self.assertEqual(code, 0, result)
        args = ("update-capability", "--root", str(self.root), "--id", "sample", "--from-file", str(draft),
                "--expected-sha256", result["sha256"])
        self.assertEqual(self.invoke(*args)[0], 0)
        current = card.read_bytes()
        self.assertEqual(self.invoke(*args)[0], 2)
        self.assertEqual(card.read_bytes(), current)

    def test_final_receipt_failure_rolls_back(self) -> None:
        path = self.root / "note.txt"
        path.write_bytes(b"before")
        transaction = workflow.Transaction(self.root, "receipt-fixture")
        transaction.add(path, "after")
        real_write = workflow.atomic_write

        def fail_commit_receipt(path, content):
            if path == transaction.dir / "manifest.json" and json.loads(content)["status"] == "committed":
                raise OSError("injected receipt failure")
            real_write(path, content)

        with patch.object(workflow, "atomic_write", fail_commit_receipt):
            with self.assertRaises(OSError):
                transaction.commit()
        self.assertEqual(path.read_bytes(), b"before")
        self.assertEqual(self.receipt(transaction)["status"], "rolled_back")


@unittest.skipUnless(shutil.which("git"), "Git is required for index tests")
class StagedValidationTests(unittest.TestCase):
    invoke = baseline.WorkflowCLITests.invoke

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-index-", dir=workflow.scratch_path(Path(tempfile.gettempdir())))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "中文 repository"
        shutil.copytree(REPO_ROOT, self.root, ignore=shutil.ignore_patterns(".git", "_test-logs", "__pycache__"))
        self.git("init", "--quiet")
        # The compatibility Skill is tracked in the source despite its ignore rule.
        self.git("add", ".")
        self.git("add", "-f", ".claude/skills/github-vault-router")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *arguments: str, input_data: bytes | None = None) -> bytes:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        result = subprocess.run(["git", "-C", str(self.root), "-c", "core.autocrlf=false", "-c", "core.longpaths=true", *arguments],
                                input=input_data, capture_output=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        return result.stdout

    def test_unstaged_invalid_content_does_not_affect_valid_index(self) -> None:
        (self.root / "config/workflow.example.json").write_text("broken draft", encoding="utf-8")
        code, result = self.invoke("validate-staged", "--root", str(self.root))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["source"], "git-index")
        self.assertFalse(result["history_scanned"])

    def test_staged_invalid_json_is_not_hidden_by_working_tree_fix(self) -> None:
        path = self.root / "config/workflow.example.json"
        good = path.read_bytes()
        path.write_text("broken staged JSON", encoding="utf-8")
        self.git("add", "config/workflow.example.json")
        path.write_bytes(good)
        code, result = self.invoke("validate-staged", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("Invalid JSON", result["error"])

    def test_staged_template_is_used_for_generated_demo_validation(self) -> None:
        path = self.root / "templates/vault-rules.md"
        path.write_bytes(path.read_bytes() + b"\nA staged template change.\n")
        self.git("add", "templates/vault-rules.md")
        code, result = self.invoke("validate-staged", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("Generated file is stale", result["error"])

    def test_deleted_required_file_and_unicode_links_are_checked(self) -> None:
        unicode_file = self.root / "docs/中文.md"
        unicode_file.write_text("[Start](../AGENT-START.md)\n", encoding="utf-8")
        self.git("add", "docs/中文.md")
        self.assertEqual(self.invoke("validate-staged", "--root", str(self.root))[0], 0)
        self.git("update-index", "--force-remove", "AGENT-START.md")
        code, result = self.invoke("validate-staged", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("Missing required repository file: AGENT-START.md", result["error"])

    def test_staged_link_is_rejected_without_following_target(self) -> None:
        oid = self.git("hash-object", "-w", "--stdin", input_data=b"../outside").decode("ascii").strip()
        self.git("update-index", "--add", "--cacheinfo", f"120000,{oid},linked")
        code, result = self.invoke("validate-staged", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("regular files only", result["error"])

    def test_staged_python_is_never_executed(self) -> None:
        marker = self.root / "executed.txt"
        script = self.root / "scripts/workflow.py"
        script.write_text("raise RuntimeError('staged code must not run')\n", encoding="utf-8")
        self.git("add", "scripts/workflow.py")
        code, result = self.invoke("validate-staged", "--root", str(self.root))
        self.assertEqual(code, 0, result)
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
