#!/usr/bin/env python3
"""Run a synthetic lifecycle in a new empty root, without installing any capability."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    root = parser.parse_args().root.resolve()
    if root.exists() and any(root.iterdir()):
        parser.error("Choose a new or empty output directory; existing work is never overwritten.")
    cli = Path(__file__).resolve().parents[1] / "scripts/workflow.py"
    def run(*arguments, expected=0):
        result = subprocess.run([sys.executable, "-B", str(cli), *arguments, "--root", str(root)],
                                capture_output=True, encoding="utf-8", timeout=30)
        if result.returncode != expected:
            raise RuntimeError(result.stderr or result.stdout)
        return json.loads(result.stdout)
    run("init", "--client", "generic-agent", "--language", "zh-CN")
    run("new-capability", "--id", "sample-tool", "--name", "Synthetic text fixture", "--type", "Reference", "--route-category", "governance")
    artifacts = root / "demo-artifacts"
    artifacts.mkdir()
    (artifacts / "version.txt").write_text("synthetic version 1\n", encoding="utf-8")
    definition = root / "demo-identity.json"
    definition.write_text(json.dumps({"schema_version": 1, "capability_id": "sample-tool", "host": {"name": "generic-agent", "version": "synthetic-1"},
                                     "version": "1.0", "files": ["version.txt"]}, indent=2) + "\n", encoding="utf-8")
    common = ("--id", "sample-tool", "--identity-file", str(definition), "--artifact-root", str(artifacts))
    session = ("--session-id", "demo-session", "--turn-id", "demo-turn")
    checks = {"before_use": run("capability-check", *common, expected=1)["result"]}
    run("use-begin", *common, *session, "--request-id", "demo-success")
    run("use-finish", *common, *session, "--run-id", "demo-success", "--validation", "passed", "--settlement", "complete", "--evidence", "Synthetic fixture content matched expected text; no real capability executed")
    checks["after_success"] = run("capability-check", *common)["result"]
    (artifacts / "version.txt").write_text("synthetic version 2\n", encoding="utf-8")
    checks["after_change"] = run("capability-check", *common, expected=1)["reasons"]
    run("use-begin", *common, *session, "--request-id", "demo-failure")
    run("use-finish", *common, *session, "--run-id", "demo-failure", "--validation", "failed", "--settlement", "complete", "--evidence", "Synthetic failure case reviewed; no install or removal required")
    checks["after_failure"] = run("capability-check", *common, expected=1)["reasons"]
    run("use-begin", *common, *session, "--request-id", "demo-interrupted")
    run("use-finish", *common, *session, "--run-id", "demo-interrupted", "--validation", "inconclusive", "--settlement", "pending", "--evidence", "Synthetic interruption: acceptance and settlement still require review")
    checks["pending"] = run("lifecycle-status")["pending"]
    run("validate")
    (root / "demo-results.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
