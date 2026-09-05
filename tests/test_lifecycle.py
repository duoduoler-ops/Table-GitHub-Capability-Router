from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import test_workflow as baseline
import lifecycle_hook
from lifecycle_contract import ContractError, check as check_contract

workflow = baseline.workflow
core = workflow.lifecycle


class LifecycleFixture:
    initialize = baseline.WorkflowCLITests.initialize

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = workflow.main(list(args))
        return code, json.loads(stdout.getvalue() or stderr.getvalue())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lifecycle-")
        self.root = (Path(self.temp.name) / "中文 vault").resolve()
        self.initialize()
        self.assertEqual(self.invoke("new-capability", "--root", str(self.root), "--id", "sample-tool", "--name", "Sample",
                                     "--type", "CLI", "--route-category", "governance")[0], 0)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        self.asset = self.artifacts / "tool.txt"
        self.asset.write_text("fixture version 1\n", encoding="utf-8")
        self.definition = self.root / "identity.json"
        self.spec = {"schema_version": 1, "capability_id": "sample-tool", "host": {"name": "generic-agent", "version": "fixture-1"},
                     "version": "1.0", "files": ["tool.txt"]}
        self.save_spec()
        self.card = self.root / "capabilities/records/sample-tool.md"
        self.common = ("--root", str(self.root), "--id", "sample-tool", "--identity-file", str(self.definition), "--artifact-root", str(self.artifacts))

    def tearDown(self):
        self.temp.cleanup()

    def save_spec(self):
        self.definition.write_text(json.dumps(self.spec), encoding="utf-8")

    def begin(self, request="first-use", session="session-1", turn="turn-1"):
        return self.invoke("use-begin", *self.common, "--request-id", request, "--session-id", session, "--turn-id", turn)

    def finish(self, request="first-use", validation="passed", settlement="complete", session="session-1", turn="turn-1", summary="Fixture acceptance checked"):
        return self.invoke("use-finish", *self.common, "--run-id", request, "--session-id", session, "--turn-id", turn,
                           "--validation", validation, "--settlement", settlement, "--evidence", summary)

    def check(self, *extra):
        return self.invoke("capability-check", *self.common, *extra)

    def evidence(self, request="smoke-first", kind="smoke", result="passed"):
        return self.invoke("record-evidence", *self.common, "--request-id", request, "--kind", kind, "--result", result, "--evidence", "Fixture check result")

    def path(self, folder="runs", record_id="first-use"):
        return core.store_path(self.root, "sample-tool", folder, record_id)

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}


class LifecycleTests(LifecycleFixture, unittest.TestCase):
    def test_closed_loop_produces_bound_evidence_without_governance_change(self):
        card = self.card.read_bytes()
        self.assertEqual(self.begin()[0], 0)
        self.assertEqual(self.finish()[0], 0)
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["evidence_usable"])
        self.assertFalse(result["governance_allows_active"])
        self.assertFalse(result["authorized_execution"])
        self.assertEqual(self.card.read_bytes(), card)
        self.assertEqual(self.invoke("validate", "--root", str(self.root))[0], 0)

    def test_legacy_health_and_discovery_never_count_as_task_success(self):
        self.assertEqual(self.invoke("capability-health", "--root", str(self.root), "--id", "sample-tool", "--to", "healthy", "--evidence", "Old claim")[0], 0)
        self.assertEqual(self.check()[0], 1)
        self.assertEqual(self.evidence(kind="discovery")[0], 0)
        self.assertEqual(self.check("--require", "smoke")[0], 1)
        self.assertEqual(self.evidence("real-smoke")[0], 0)
        self.assertEqual(self.check("--require", "smoke")[0], 0)
        self.assertEqual(self.check()[0], 1)

    def test_idempotency_and_conflicting_retries(self):
        self.assertEqual(self.begin()[0], 0)
        first = self.snapshot()
        self.assertEqual(self.begin()[1]["result"], "already_recorded")
        self.assertEqual(first, self.snapshot())
        self.assertEqual(self.begin(session="different")[0], 2)
        self.assertEqual(self.finish()[0], 0)
        finished = self.snapshot()
        self.assertEqual(self.finish()[1]["result"], "already_recorded")
        self.assertEqual(finished, self.snapshot())
        self.assertEqual(self.begin()[1]["status"], "completed")
        self.assertEqual(self.finish(validation="failed")[0], 2)
        self.assertEqual(self.evidence()[0], 0)
        self.assertEqual(self.evidence()[1]["result"], "already_recorded")
        self.assertEqual(self.evidence(result="failed")[0], 2)

    def test_changes_to_declared_files_or_host_invalidate_only_this_identity(self):
        self.begin(); self.finish()
        (self.artifacts / "unrelated.txt").write_text("irrelevant", encoding="utf-8")
        self.assertEqual(self.check()[0], 0)
        original = self.asset.read_bytes()
        self.asset.write_bytes(b"version 2")
        self.assertIn("identity_changed", self.check()[1]["reasons"])
        self.asset.write_bytes(original)
        self.spec["host"]["version"] = "fixture-2"
        self.save_spec()
        self.assertEqual(self.check()[0], 1)

    def test_missing_artifact_cannot_be_healthy(self):
        self.spec["files"].append("not-present.txt")
        self.save_spec()
        self.begin(); self.finish()
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertIn("artifact_missing", result["reasons"])

    def test_identity_change_during_use_is_not_task_success(self):
        self.begin()
        self.asset.write_bytes(b"changed while working")
        result = self.finish()[1]
        self.assertFalse(result["identity_matches"])
        self.assertEqual(self.check()[0], 1)
        self.asset.write_text("fixture version 1\n", encoding="utf-8")
        self.assertIn("identity_changed_during_use", self.check()[1]["reasons"])

    def test_failure_inconclusive_and_interrupted_settlement(self):
        for number, validation in enumerate(("failed", "inconclusive")):
            request = f"run-{number}"
            self.begin(request)
            self.assertEqual(self.finish(request, validation=validation)[0], 0)
            self.assertEqual(self.check()[0], 1)
        self.begin("interrupted")
        self.assertEqual(self.finish("interrupted", validation="inconclusive", settlement="pending")[0], 0)
        status = self.invoke("lifecycle-status", "--root", str(self.root))[1]
        self.assertEqual(status["pending"][0]["run_id"], "interrupted")
        self.assertFalse(self.path("evidence", "task-interrupted").exists())
        self.assertEqual(self.finish("interrupted", validation="inconclusive", settlement="complete")[0], 0)

    def test_pending_use_prevents_silent_evidence_reuse(self):
        self.begin(); self.finish()
        self.begin("second-use")
        self.assertIn("unsettled_use", self.check()[1]["reasons"])

    def test_new_smoke_failure_overrides_older_task_success(self):
        self.begin(); self.finish()
        self.evidence(result="failed")
        self.assertIn("newer_negative_evidence", self.check()[1]["reasons"])

    def test_expired_future_and_invalid_clock_evidence(self):
        self.evidence()
        path = self.path("evidence", "smoke-first")
        value = json.loads(path.read_text(encoding="utf-8"))
        for days, reason in ((-31, "evidence_expired"), (1, "future_evidence")):
            value["observed_at"] = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn(reason, self.check("--require", "smoke")[1]["reasons"])
        value["observed_at"] = "2026-99-01T00:00:00Z"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.check()[0], 2)

    def test_read_only_check_has_no_writes_and_rejects_mid_read_changes(self):
        self.begin(); self.finish()
        before = self.snapshot()
        self.assertEqual(self.check()[0], 0)
        self.assertEqual(before, self.snapshot())
        original_records = core.records
        def change(api, root, capability_id, folder):
            values = original_records(api, root, capability_id, folder)
            self.asset.write_bytes(b"concurrent change")
            return values
        with patch.object(core, "records", side_effect=change):
            self.assertEqual(self.check()[0], 2)

    def test_invalid_enums_and_state_combinations_rejected(self):
        self.begin()
        path = self.path()
        original = json.loads(path.read_text(encoding="utf-8"))
        for bad in ({"management_state": "invalid-state"}, {"health_state": "invalid-health"}, {"management_state": "active"}):
            value = json.loads(json.dumps(original))
            value["before"].update(bad)
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(self.invoke("validate", "--root", str(self.root))[0], 2)
        self.assertRaises(ContractError, check_contract, {}, {"unknown-keyword": 1}, {})

    def test_fingerprint_tampering_and_cross_record_mismatch_rejected(self):
        self.begin(); self.finish()
        path = self.path("evidence", "task-first-use")
        value = json.loads(path.read_text(encoding="utf-8"))
        value["summary"] = "Mismatched record"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.check()[0], 2)
        value["identity"]["version"] = "invented"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.check()[0], 2)

    def test_scope_mismatch_and_oversized_request_rejected(self):
        self.begin()
        self.assertEqual(self.finish(session="other-session")[0], 2)
        self.assertEqual(self.finish(turn="other-turn")[0], 2)
        self.assertEqual(self.begin("a" * 81)[0], 2)
        self.assertEqual(self.evidence("task-forged")[0], 2)
        self.assertEqual(self.finish(validation="pending", settlement="complete")[0], 2)
        self.assertEqual(self.finish(summary=" ")[0], 2)

    def test_identity_paths_and_duplicate_files_are_rejected(self):
        for files in (["../outside"], ["tool.txt", "tool.txt"], ["folder//file"], ["/absolute"], ["C:/example/file"]):
            self.spec["files"] = files
            self.save_spec()
            self.assertEqual(self.begin()[0], 2, files)
        self.assertFalse(self.path().exists())

    def test_finish_transaction_rolls_back_both_records(self):
        self.begin()
        original = self.path().read_bytes()
        writer = workflow.atomic_write
        def fail_on_evidence(path, content):
            if path == self.path("evidence", "task-first-use"):
                raise OSError("injected evidence failure")
            writer(path, content)
        with patch.object(workflow, "atomic_write", side_effect=fail_on_evidence):
            self.assertEqual(self.finish()[0], 2)
        self.assertEqual(self.path().read_bytes(), original)
        self.assertFalse(self.path("evidence", "task-first-use").exists())
        self.assertEqual(self.invoke("validate", "--root", str(self.root))[0], 0)

    def test_external_artifact_change_during_transaction_is_preserved(self):
        writer = workflow.atomic_write
        def change_after_write(path, content):
            writer(path, content)
            if path == self.path():
                self.asset.write_bytes(b"external update")
        with patch.object(workflow, "atomic_write", side_effect=change_after_write):
            self.assertEqual(self.begin()[0], 2)
        self.assertEqual(self.asset.read_bytes(), b"external update")
        self.assertFalse(self.path().exists())

    def test_writer_lock_prevents_partial_reads_or_duplicate_writers(self):
        with workflow.workflow_lock(self.root):
            self.assertEqual(self.begin()[0], 2)
            self.assertEqual(self.check()[0], 2)
        self.assertEqual(self.begin()[0], 0)

    def test_real_cli_process_can_read_status(self):
        self.begin()
        process = subprocess.run([sys.executable, "-B", str(baseline.REPO_ROOT / "scripts/workflow.py"), "lifecycle-status", "--root", str(self.root)],
                                 capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(json.loads(process.stdout)["pending"]), 1)

    def test_moved_vault_keeps_history_without_reusing_foreign_evidence(self):
        self.begin(); self.finish()
        other = self.root.parent / "copied vault"
        shutil.copytree(self.root, other)
        common = ("--root", str(other), "--id", "sample-tool", "--identity-file", str(other / "identity.json"), "--artifact-root", str(self.artifacts))
        self.assertEqual(self.invoke("validate", "--root", str(other))[0], 0)
        self.assertEqual(self.invoke("capability-check", *common)[0], 1)
        self.assertEqual(self.invoke("use-finish", *common, "--run-id", "first-use", "--session-id", "session-1", "--turn-id", "turn-1", "--validation", "passed", "--settlement", "complete", "--evidence", "Fixture acceptance checked")[0], 2)

    def test_new_receipt_during_read_and_end_before_start_rejected(self):
        self.begin(); self.finish()
        reader = core.records
        def add_entry(api, root, capability_id, folder, schema_root=None):
            result = reader(api, root, capability_id, folder, schema_root)
            if folder == "evidence":
                self.path("evidence", "racing-file").write_text("{}", encoding="utf-8")
            return result
        with patch.object(core, "records", side_effect=add_entry):
            self.assertEqual(self.check()[0], 2)
        # Check the clock invariant on a decoded object without repairing the corrupt store.
        path = self.path()
        value = json.loads(path.read_text(encoding="utf-8"))
        value["ended_at"] = "2000-01-01T00:00:00Z"
        self.assertRaises(ContractError, core.validate_record, workflow, value, "receipt", "sample-tool", "first-use")

    def test_demonstration_runs_in_empty_root_and_refuses_overwrite(self):
        output = self.root.parent / "demo output"
        command = [sys.executable, "-B", str(baseline.REPO_ROOT / "examples/lifecycle-demo.py"), "--root", str(output)]
        result = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["after_success"], "pass")
        self.assertEqual(report["after_change"], ["identity_changed"])
        self.assertEqual(report["pending"][0]["run_id"], "demo-interrupted")
        before = (output / "demo-results.json").read_bytes()
        rerun = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(rerun.returncode, 2)
        self.assertEqual(before, (output / "demo-results.json").read_bytes())


class HookBehaviorTests(LifecycleFixture, unittest.TestCase):
    def hook(self, payload=None, host="codex", **changes):
        event = {"hook_event_name": "Stop", "cwd": str(self.root), "session_id": "session-1", "turn_id": "turn-1", "stop_hook_active": False}
        event.update(changes)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("sys.stdin", io.StringIO(payload if payload is not None else json.dumps(event))), redirect_stdout(stdout), redirect_stderr(stderr):
            code = lifecycle_hook.main(["--root", str(self.root), "--host", host])
        self.assertEqual(code, 0)
        return stdout.getvalue(), stderr.getvalue()

    def test_normal_quiet_cross_project_and_cross_session(self):
        self.assertEqual(self.hook(), ("", ""))
        self.begin()
        self.assertEqual(self.hook(cwd=str(self.root.parent)), ("", ""))
        self.assertEqual(self.hook(session_id="another-session"), ("", ""))
        self.assertIn("systemMessage", self.hook()[0])

    def test_once_per_turn_and_stop_guard(self):
        self.begin()
        self.assertEqual(self.hook(stop_hook_active=True), ("", ""))
        self.assertTrue(self.hook()[0])
        self.assertEqual(self.hook(), ("", ""))
        self.assertTrue(self.hook(turn_id="turn-2")[0])

    def test_startup_finds_previous_session_and_missing_turn_falls_back_to_session(self):
        self.begin(session="old-session")
        self.assertIn("additionalContext", self.hook(hook_event_name="SessionStart", turn_id=None)[0])
        self.assertEqual(self.hook(hook_event_name="SessionStart", turn_id=None), ("", ""))

    def test_malformed_oversized_unknown_events_and_timeout_fail_open(self):
        for value in ("not json", "[]", "x" * 70000, "{}"):
            self.assertEqual(self.hook(payload=value), ("", ""))
        self.assertEqual(self.hook(hook_event_name="PostToolUse"), ("", ""))
        self.begin()
        with patch.object(lifecycle_hook, "pending_uses", side_effect=TimeoutError("timeout")):
            self.assertEqual(self.hook(), ("", ""))
        self.assertTrue(self.hook()[0])

    def test_corrupt_receipt_and_writer_lock_fail_open(self):
        self.begin()
        with workflow.workflow_lock(self.root):
            self.assertEqual(self.hook(), ("", ""))
        self.path().write_text("corrupt", encoding="utf-8")
        self.assertEqual(self.hook(), ("", ""))

    def test_corrupt_cache_is_not_overwritten_or_repeated(self):
        self.begin()
        self.assertTrue(self.hook()[0])
        cache = next((self.root / ".workflow/lifecycle/hook-cache").glob("*.json"))
        cache.write_text("corrupt", encoding="utf-8")
        self.assertEqual(self.hook(), ("", ""))
        self.assertEqual(cache.read_text(encoding="utf-8"), "corrupt")

    def test_grok_camelcase_mapping_file_mode_and_explicit_feedback(self):
        self.begin()
        payload = {"hookEventName": "stop", "sessionId": "session-1", "promptId": "turn-1", "cwd": str(self.root),
                   "stopHookActive": False, "reason": "end_turn"}
        self.assertEqual(self.hook(payload=json.dumps(payload), host="grok-build"), ("", ""))
        payload["promptId"] = "turn-2"
        feedback = lifecycle_hook.handle(self.root, "grok-build", payload, grok_feedback=True)
        self.assertEqual(feedback["hookSpecificOutput"]["hookEventName"], "Stop")
        self.assertIsNone(lifecycle_hook.handle(self.root, "grok-build", payload, grok_feedback=True))
        payload["hookEventName"] = "session_start"
        self.assertIsNone(lifecycle_hook.handle(self.root, "grok-build", payload, grok_feedback=True))

    def test_concurrent_hook_processes_emit_at_most_once(self):
        self.begin()
        event = json.dumps({"hook_event_name": "Stop", "cwd": str(self.root), "session_id": "session-1", "turn_id": "concurrent"}, ensure_ascii=False)
        command = [sys.executable, "-B", str(baseline.REPO_ROOT / "scripts/lifecycle_hook.py"), "--root", str(self.root), "--host", "codex"]
        environment = dict(os.environ, PYTHONUTF8="0", PYTHONIOENCODING="ascii")
        processes = [subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", env=environment) for _ in range(2)]
        for process in processes:
            process.stdin.write(event)
            process.stdin.close()
            process.stdin = None
        outputs = [process.communicate(timeout=20) for process in processes]
        self.assertEqual(sum(bool(stdout) for stdout, _ in outputs), 1, outputs)
        self.assertTrue(all(process.returncode == 0 for process in processes))
        self.assertTrue(all(not stderr for _, stderr in outputs))


if __name__ == "__main__":
    unittest.main()
