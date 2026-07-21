#!/usr/bin/env python3
"""Deterministic, dependency-free bootstrap and maintenance CLI.

The Markdown files remain the human-readable interface. This script owns only
the mechanical parts: stable IDs, flat frontmatter, state transitions, derived
indexes/routers, locking, rollback-on-error, and validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = "1"
REPO_ROOT = Path(__file__).resolve().parents[1]

PROJECT_STATUSES = {
    "candidate",
    "evaluated",
    "retained",
    "reference",
    "rejected",
    "archived",
}
PROJECT_GRADES = {"ungraded", "S", "A", "B", "C", "D"}
EVIDENCE_LEVELS = {"unverified", "author-claim", "online-check", "static-check", "T0", "T1", "T2", "T3"}
PROJECT_TRANSITIONS = {
    "candidate": {"evaluated", "rejected", "archived"},
    "evaluated": {"retained", "reference", "rejected", "archived"},
    "retained": {"reference", "archived"},
    "reference": {"retained", "archived"},
    "rejected": {"candidate", "archived"},
    "archived": {"candidate"},
}

MANAGEMENT_STATES = {
    "candidate",
    "active",
    "cold",
    "disabled",
    "reference",
    "retired",
    "quarantine",
}
HEALTH_STATES = {"healthy", "unverified", "degraded", "broken", "missing"}
INVOCATION_STATES = {"auto", "conditional", "explicit-only", "disabled"}
ROUTABLE_MANAGEMENT_STATES = {"active", "cold", "reference"}
AUTHORIZATION_STATES = {"ordinary-record", "lifecycle-update", "routing-proposal", "configuration-change"}
CAPABILITY_TRANSITIONS = {
    "candidate": {"active", "cold", "disabled", "reference", "quarantine", "retired"},
    "active": {"cold", "disabled", "quarantine", "retired"},
    "cold": {"active", "disabled", "reference", "quarantine", "retired"},
    "disabled": {"active", "cold", "reference", "quarantine", "retired"},
    "reference": {"active", "cold", "disabled", "quarantine", "retired"},
    "quarantine": {"cold", "disabled", "retired"},
    "retired": {"candidate"},
}

REQUIRED_CONFIG_KEYS = {"schema_version", "language", "client_profile", "paths", "route_categories"}
REQUIRED_PROJECT_FIELDS = {
    "schema_version",
    "record_type",
    "id",
    "revision",
    "status",
    "grade",
    "canonical_url",
    "evidence_level",
    "updated_at",
}
REQUIRED_CAPABILITY_FIELDS = {
    "schema_version",
    "record_type",
    "id",
    "revision",
    "management_state",
    "health_state",
    "risk",
    "invocation",
    "authorization",
    "manager_type",
    "route_category",
    "updated_at",
}


class WorkflowError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def canonicalize_github_url(value: str) -> tuple[str, str]:
    raw = value.strip()
    if re.match(r"^[\w.-]+/[\w.-]+$", raw):
        raw = f"https://github.com/{raw}"
    parts = urlsplit(raw)
    if parts.scheme not in {"http", "https"} or parts.netloc.lower() not in {"github.com", "www.github.com"}:
        raise WorkflowError("Only public github.com repository URLs are accepted.")
    path_parts = [part for part in parts.path.strip("/").split("/") if part]
    if len(path_parts) != 2:
        raise WorkflowError("Expected a repository URL in the form https://github.com/owner/repo.")
    owner = path_parts[0].lower()
    repo = re.sub(r"\.git$", "", path_parts[1], flags=re.IGNORECASE).lower()
    if not owner or not repo:
        raise WorkflowError("GitHub owner and repository name must not be empty.")
    canonical = urlunsplit(("https", "github.com", f"/{owner}/{repo}", "", ""))
    return canonical, f"gh-{slugify(owner)}-{slugify(repo)}"


def parse_frontmatter(text: str, path: Path | None = None) -> tuple[dict[str, str], str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        where = f" in {path}" if path else ""
        raise WorkflowError(f"Missing flat YAML frontmatter{where}.")
    end = normalized.find("\n---\n", 4)
    if end < 0:
        raise WorkflowError(f"Unclosed frontmatter in {path or '<text>'}.")
    data: dict[str, str] = {}
    for line in normalized[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise WorkflowError(f"Unsupported frontmatter line in {path or '<text>'}: {line}")
        key, raw = line.split(":", 1)
        key = key.strip()
        value = raw.strip().strip('"').strip("'")
        if not re.match(r"^[a-z][a-z0-9_]*$", key):
            raise WorkflowError(f"Invalid frontmatter key {key!r} in {path or '<text>'}.")
        if key in data:
            raise WorkflowError(f"Duplicate frontmatter key {key!r} in {path or '<text>'}.")
        data[key] = value
    return data, normalized[end + 5 :]


def render_frontmatter(data: dict[str, str], body: str) -> str:
    lines = ["---"]
    for key, value in data.items():
        safe = str(value).replace("\n", " ").strip()
        lines.append(f"{key}: {safe}")
    lines.extend(["---", "", body.lstrip("\n")])
    return "\n".join(lines).rstrip() + "\n"


def replace_template(path: Path, values: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", text)))
    if unresolved:
        raise WorkflowError(f"Template {path.name} has unresolved placeholders: {', '.join(unresolved)}")
    return text


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    temp.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temp, path)


@contextmanager
def workflow_lock(root: Path):
    state_dir = root / ".workflow"
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise WorkflowError(
            f"Workflow is locked by {lock_path}. Inspect the file and the running process before removing it."
        ) from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"pid": os.getpid(), "created_at": now_utc()}, handle)
        yield
    finally:
        if lock_path.exists():
            lock_path.unlink()


@dataclass
class PendingWrite:
    path: Path
    content: str


class Transaction:
    def __init__(self, root: Path, action: str):
        self.root = root.resolve()
        self.action = action
        self.id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        self.dir = self.root / ".workflow" / "transactions" / self.id
        self.before = self.dir / "before"
        self.writes: list[PendingWrite] = []

    def add(self, path: Path, content: str) -> None:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise WorkflowError(f"Transaction target escapes workflow root: {resolved}") from exc
        self.writes.append(PendingWrite(resolved, content))

    def commit(self) -> None:
        if not self.writes:
            return
        self.before.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, object] = {
            "schema_version": 1,
            "transaction_id": self.id,
            "action": self.action,
            "created_at": now_utc(),
            "status": "prepared",
            "files": [],
        }
        for item in self.writes:
            relative = item.path.relative_to(self.root).as_posix()
            existed = item.path.exists()
            old_text = item.path.read_text(encoding="utf-8") if existed else ""
            if existed:
                backup = self.before / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item.path, backup)
            manifest["files"].append(
                {
                    "path": relative,
                    "existed": existed,
                    "before_sha256": sha256_text(old_text) if existed else None,
                    "after_sha256": sha256_text(item.content),
                }
            )
        atomic_write(self.dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        applied: list[PendingWrite] = []
        try:
            for item in self.writes:
                atomic_write(item.path, item.content)
                applied.append(item)
        except Exception:
            for item in reversed(applied):
                relative = item.path.relative_to(self.root)
                backup = self.before / relative
                if backup.exists():
                    atomic_write(item.path, backup.read_text(encoding="utf-8"))
                elif item.path.exists():
                    item.path.unlink()
            manifest["status"] = "rolled_back"
            atomic_write(self.dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            raise
        manifest["status"] = "committed"
        manifest["committed_at"] = now_utc()
        atomic_write(self.dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def config_path(root: Path) -> Path:
    return root / "workflow.json"


def load_config(root: Path) -> dict:
    path = config_path(root)
    if not path.exists():
        raise WorkflowError(f"Missing {path}. Run the init command first.")
    config = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED_CONFIG_KEYS - set(config)
    if missing:
        raise WorkflowError(f"workflow.json is missing: {', '.join(sorted(missing))}")
    if str(config["schema_version"]) != SCHEMA_VERSION:
        raise WorkflowError(f"Unsupported workflow schema version: {config['schema_version']}")
    category_ids = [entry.get("id") for entry in config["route_categories"]]
    if not 1 <= len(category_ids) <= 10 or len(category_ids) != len(set(category_ids)):
        raise WorkflowError("route_categories must contain unique non-empty ids.")
    for entry in config["route_categories"]:
        if not re.match(r"^[a-z][a-z0-9-]+$", str(entry.get("id", ""))):
            raise WorkflowError(f"Invalid route category id: {entry.get('id')}")
        if not str(entry.get("label", "")).strip() or not str(entry.get("boundary", "")).strip():
            raise WorkflowError(f"Route category requires non-empty label and boundary: {entry.get('id')}")
    if config["language"] not in {"zh-CN", "en"}:
        raise WorkflowError(f"Unsupported language: {config['language']}")
    if config["client_profile"] not in {"generic-agent", "codex", "claude-code"}:
        raise WorkflowError(f"Unsupported client profile: {config['client_profile']}")
    return config


def resolve_paths(root: Path, config: dict) -> dict[str, Path]:
    required = {
        "project_records",
        "capability_records",
        "project_index",
        "candidate_pool",
        "rejection_log",
        "router",
        "maintenance_log",
        "distillations",
        "inbox",
    }
    missing = required - set(config["paths"])
    if missing:
        raise WorkflowError(f"workflow.json paths missing: {', '.join(sorted(missing))}")
    output: dict[str, Path] = {}
    for key, value in config["paths"].items():
        candidate = Path(value)
        resolved = candidate if candidate.is_absolute() else root / candidate
        resolved = resolved.resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise WorkflowError(f"Public workflow paths must stay under the initialized root: {key}={resolved}") from exc
        output[key] = resolved
    return output


def read_records(directory: Path, record_type: str) -> list[tuple[Path, dict[str, str], str]]:
    records: list[tuple[Path, dict[str, str], str]] = []
    if not directory.exists():
        return records
    for path in sorted(directory.glob("*.md")):
        data, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
        if data.get("record_type") != record_type:
            raise WorkflowError(f"Unexpected record_type in {path}: {data.get('record_type')}")
        records.append((path, data, body))
    return records


def project_index(records: Iterable[tuple[Path, dict[str, str], str]]) -> str:
    rows = []
    for path, data, _ in sorted(records, key=lambda item: item[1]["id"]):
        rows.append(
            f"| {data['id']} | {data['status']} | {data['grade']} | "
            f"[{data['canonical_url']}]({data['canonical_url']}) | [{path.name}](../projects/records/{path.name}) | {data['updated_at']} |"
        )
    content = [
        "<!-- generated by scripts/workflow.py; do not edit manually -->",
        "# GitHub Project Index / GitHub 项目索引",
        "",
        "| ID | Status | Grade | Canonical URL | Card | Updated |",
        "| --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
    ]
    return "\n".join(content)


def filtered_project_table(
    title: str, records: Iterable[tuple[Path, dict[str, str], str]], statuses: set[str]
) -> str:
    rows = []
    for path, data, _ in sorted(records, key=lambda item: item[1]["id"]):
        if data["status"] in statuses:
            rows.append(f"| {data['id']} | {data['status']} | {data['grade']} | [{path.name}](records/{path.name}) |")
    return "\n".join(
        [
            "<!-- generated by scripts/workflow.py; do not edit manually -->",
            f"# {title}",
            "",
            "| ID | Status | Grade | Card |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def capability_router(config: dict, records: Iterable[tuple[Path, dict[str, str], str]]) -> str:
    records_list = sorted(records, key=lambda item: item[1]["id"])
    categories = []
    for category in config["route_categories"]:
        candidates = [
            data["id"]
            for _, data, _ in records_list
            if data["route_category"] == category["id"]
            and data["management_state"] in ROUTABLE_MANAGEMENT_STATES
        ]
        if category["id"] == "direct-answer" and "no-extra-tool" not in candidates:
            candidates.insert(0, "no-extra-tool")
        categories.append(
            f"| {category['label']} | {category['boundary']} | {', '.join(candidates) if candidates else 'no-extra-tool'} |"
        )
    registry = []
    for path, data, _ in records_list:
        if data["management_state"] not in ROUTABLE_MANAGEMENT_STATES:
            continue
        registry.append(
            f"| {data['id']} | {data['management_state']} / {data['health_state']} | {data['invocation']} | "
            f"{data['authorization']} | {data['risk']} | [{path.name}](../capabilities/records/{path.name}) |"
        )
    return "\n".join(
        [
            "<!-- generated by scripts/workflow.py; do not edit manually -->",
            "# Capability Router / 能力路由",
            "",
            "> L0 boundary: this file guides decisions but does not hide, disable, install, or configure client capabilities.",
            "> L0 边界：本文件只引导决策，不会隐藏、禁用、安装或配置客户端能力。",
            "",
            "## Level 1",
            "",
            "| Task type | Boundary | Candidates |",
            "| --- | --- | --- |",
            *categories,
            "",
            "## Level 2 Registry",
            "",
            "| ID | Management / Health | Invocation | Authorization | Risk | Card |",
            "| --- | --- | --- | --- | --- | --- |",
            *registry,
            "",
            "If nothing matches, use `no-extra-tool`; never scan the whole capability directory.",
            "未命中时使用 `no-extra-tool`，不要扫描整个能力目录。",
            "",
        ]
    )


def append_log(current: str, message: str) -> str:
    current = current.rstrip() if current else "# Maintenance Log / 维护日志"
    return f"{current}\n\n## {today_utc()}\n\n- {message}\n"


def validate_project(data: dict[str, str], path: Path) -> list[str]:
    errors = []
    missing = REQUIRED_PROJECT_FIELDS - set(data)
    if missing:
        errors.append(f"{path}: missing project fields {sorted(missing)}")
        return errors
    if data["schema_version"] != SCHEMA_VERSION:
        errors.append(f"{path}: unsupported schema_version {data['schema_version']}")
    if data["record_type"] != "github-project":
        errors.append(f"{path}: invalid record_type {data['record_type']}")
    if not data["revision"].isdigit() or int(data["revision"]) < 1:
        errors.append(f"{path}: revision must be a positive integer")
    if data["status"] not in PROJECT_STATUSES:
        errors.append(f"{path}: invalid status {data['status']}")
    if data["grade"] not in PROJECT_GRADES:
        errors.append(f"{path}: invalid grade {data['grade']}")
    if data["status"] == "retained" and data["grade"] not in {"S", "A", "B"}:
        errors.append(f"{path}: retained projects require S/A/B grade")
    if data["status"] == "reference" and data["grade"] not in {"S", "A", "B"}:
        errors.append(f"{path}: reference projects require S/A/B grade")
    if data["status"] == "rejected" and data["grade"] not in {"C", "D"}:
        errors.append(f"{path}: rejected projects require C/D grade")
    if data["status"] in {"retained", "reference"} and not data.get("approved_by"):
        errors.append(f"{path}: retained/reference project requires approved_by")
    if data["evidence_level"] not in EVIDENCE_LEVELS:
        errors.append(f"{path}: invalid evidence_level {data['evidence_level']}")
    if not re.match(r"^gh-[a-z0-9-]+$", data["id"]):
        errors.append(f"{path}: invalid stable project id {data['id']}")
    try:
        canonical, expected_id = canonicalize_github_url(data["canonical_url"])
        if canonical != data["canonical_url"] or expected_id != data["id"]:
            errors.append(f"{path}: canonical URL and id do not agree")
    except WorkflowError as exc:
        errors.append(f"{path}: {exc}")
    return errors


def validate_capability(data: dict[str, str], path: Path, category_ids: set[str]) -> list[str]:
    errors = []
    missing = REQUIRED_CAPABILITY_FIELDS - set(data)
    if missing:
        errors.append(f"{path}: missing capability fields {sorted(missing)}")
        return errors
    if data["schema_version"] != SCHEMA_VERSION:
        errors.append(f"{path}: unsupported schema_version {data['schema_version']}")
    if data["record_type"] != "capability":
        errors.append(f"{path}: invalid record_type {data['record_type']}")
    if not data["revision"].isdigit() or int(data["revision"]) < 1:
        errors.append(f"{path}: revision must be a positive integer")
    if data["management_state"] not in MANAGEMENT_STATES:
        errors.append(f"{path}: invalid management_state {data['management_state']}")
    if data["health_state"] not in HEALTH_STATES:
        errors.append(f"{path}: invalid health_state {data['health_state']}")
    if data["invocation"] not in INVOCATION_STATES:
        errors.append(f"{path}: invalid invocation {data['invocation']}")
    if data["risk"] not in {"low", "medium", "high"}:
        errors.append(f"{path}: invalid risk {data['risk']}")
    if data["authorization"] not in AUTHORIZATION_STATES:
        errors.append(f"{path}: invalid authorization {data['authorization']}")
    if data["manager_type"] not in {"true", "false"}:
        errors.append(f"{path}: manager_type must be true or false")
    if data["route_category"] not in category_ids:
        errors.append(f"{path}: unknown route_category {data['route_category']}")
    if data["management_state"] == "active" and data["health_state"] != "healthy":
        errors.append(f"{path}: active capability must be healthy")
    if data["management_state"] == "active" and not data.get("approved_by"):
        errors.append(f"{path}: active capability requires approved_by")
    if data["management_state"] == "active" and data["invocation"] == "disabled":
        errors.append(f"{path}: active capability cannot have disabled invocation")
    if data["management_state"] in {"candidate", "cold", "reference"} and data["invocation"] != "explicit-only":
        errors.append(f"{path}: candidate/cold/reference capability requires explicit-only invocation")
    if data["invocation"] == "auto" and data["management_state"] != "active":
        errors.append(f"{path}: auto invocation requires active state")
    if data["invocation"] == "auto" and data["manager_type"] == "true":
        errors.append(f"{path}: manager-type capability cannot use automatic invocation")
    if data["management_state"] in {"disabled", "retired", "quarantine"} and data["invocation"] != "disabled":
        errors.append(f"{path}: non-routable state requires disabled invocation")
    if not re.match(r"^[a-z][a-z0-9-]+$", data["id"]):
        errors.append(f"{path}: invalid capability id {data['id']}")
    return errors


def collect_validation(root: Path) -> tuple[list[str], dict]:
    config = load_config(root)
    paths = resolve_paths(root, config)
    projects = read_records(paths["project_records"], "github-project")
    capabilities = read_records(paths["capability_records"], "capability")
    errors: list[str] = []
    for path, data, _ in projects:
        errors.extend(validate_project(data, path))
    category_ids = {entry["id"] for entry in config["route_categories"]}
    for path, data, _ in capabilities:
        errors.extend(validate_capability(data, path, category_ids))
    project_ids = [data.get("id") for _, data, _ in projects]
    project_urls = [data.get("canonical_url") for _, data, _ in projects]
    capability_ids = [data.get("id") for _, data, _ in capabilities]
    for label, values in (("project id", project_ids), ("project URL", project_urls), ("capability id", capability_ids)):
        duplicates = sorted({value for value in values if value and values.count(value) > 1})
        if duplicates:
            errors.append(f"Duplicate {label}: {duplicates}")
    expected = {
        paths["project_index"]: project_index(projects),
        paths["candidate_pool"]: filtered_project_table(
            "Candidate Pool / 候选池", projects, {"candidate", "evaluated"}
        ),
        paths["rejection_log"]: filtered_project_table("Rejection Log / 否决记录", projects, {"rejected"}),
        paths["router"]: capability_router(config, capabilities),
    }
    for path, content in expected.items():
        if not path.exists():
            errors.append(f"Missing generated file: {path}")
        elif path.read_text(encoding="utf-8").replace("\r\n", "\n") != content:
            errors.append(f"Generated file is stale: {path}")
    summary = {
        "schema_version": 1,
        "root": str(root.resolve()),
        "projects": len(projects),
        "capabilities": len(capabilities),
        "errors": len(errors),
    }
    return errors, summary


def build_derived_writes(root: Path, config: dict) -> list[PendingWrite]:
    paths = resolve_paths(root, config)
    projects = read_records(paths["project_records"], "github-project")
    capabilities = read_records(paths["capability_records"], "capability")
    return [
        PendingWrite(paths["project_index"], project_index(projects)),
        PendingWrite(
            paths["candidate_pool"],
            filtered_project_table("Candidate Pool / 候选池", projects, {"candidate", "evaluated"}),
        ),
        PendingWrite(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", projects, {"rejected"})),
        PendingWrite(paths["router"], capability_router(config, capabilities)),
    ]


def command_init(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    existing = [item for item in root.iterdir() if item.name != ".workflow"]
    if existing and not config_path(root).exists():
        raise WorkflowError("Initialization target is not empty. Use a new directory to avoid mixing unrelated files.")
    if config_path(root).exists():
        errors, summary = collect_validation(root)
        if errors:
            raise WorkflowError("Already initialized but invalid:\n" + "\n".join(errors))
        return {"action": "init", "result": "already_initialized", **summary}
    config = json.loads((REPO_ROOT / "config" / "workflow.example.json").read_text(encoding="utf-8"))
    config["language"] = args.language
    config["client_profile"] = args.client
    paths = resolve_paths(root, config)
    for key in ("project_records", "capability_records", "distillations", "inbox"):
        paths[key].mkdir(parents=True, exist_ok=True)
    transaction = Transaction(root, "init")
    transaction.add(config_path(root), json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    transaction.add(
        root / "AGENT-ROUTER.md",
        replace_template(
            REPO_ROOT / "templates" / "vault-rules.md",
            {"CLIENT_PROFILE": args.client, "LANGUAGE": args.language},
        ),
    )
    transaction.add(paths["maintenance_log"], "# Maintenance Log / 维护日志\n")
    transaction.add(paths["project_index"], project_index([]))
    transaction.add(paths["candidate_pool"], filtered_project_table("Candidate Pool / 候选池", [], {"candidate", "evaluated"}))
    transaction.add(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", [], {"rejected"}))
    transaction.add(paths["router"], capability_router(config, []))
    transaction.commit()
    errors, summary = collect_validation(root)
    if errors:
        raise WorkflowError("Initialization validation failed:\n" + "\n".join(errors))
    return {"action": "init", "result": "created", **summary}


def command_new_project(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    canonical, record_id = canonicalize_github_url(args.url)
    records = read_records(paths["project_records"], "github-project")
    for path, data, _ in records:
        if data.get("id") == record_id or data.get("canonical_url") == canonical:
            return {
                "action": "new-project",
                "result": "existing",
                "id": data["id"],
                "path": str(path),
                "canonical_url": data["canonical_url"],
            }
    card = replace_template(
        REPO_ROOT / "templates" / "github-project-card.md",
        {
            "SCHEMA_VERSION": SCHEMA_VERSION,
            "PROJECT_ID": record_id,
            "REVISION": "1",
            "PROJECT_STATUS": "candidate",
            "PROJECT_GRADE": "ungraded",
            "CANONICAL_URL": canonical,
            "EVIDENCE_LEVEL": "unverified",
            "UPDATED_AT": now_utc(),
            "CHECK_DATE": today_utc(),
        },
    )
    target = paths["project_records"] / f"{record_id}.md"
    transaction = Transaction(root, "new-project")
    transaction.add(target, card)
    updated_records = [*records, (target, parse_frontmatter(card)[0], parse_frontmatter(card)[1])]
    transaction.add(paths["project_index"], project_index(updated_records))
    transaction.add(
        paths["candidate_pool"],
        filtered_project_table("Candidate Pool / 候选池", updated_records, {"candidate", "evaluated"}),
    )
    transaction.add(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", updated_records, {"rejected"}))
    current_log = paths["maintenance_log"].read_text(encoding="utf-8")
    transaction.add(
        paths["maintenance_log"],
        append_log(current_log, f"Created candidate `{record_id}` for {canonical}; no clone, install, login, publishing, deletion, or client configuration change was performed."),
    )
    transaction.commit()
    return {"action": "new-project", "result": "created", "id": record_id, "path": str(target), "canonical_url": canonical}


def command_new_capability(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    category_ids = {entry["id"] for entry in config["route_categories"]}
    capability_id = slugify(args.id)
    if not capability_id or not re.match(r"^[a-z][a-z0-9-]+$", capability_id):
        raise WorkflowError("Capability id must start with a letter and contain only letters, digits, and hyphens.")
    if args.route_category not in category_ids:
        raise WorkflowError(f"Unknown route category: {args.route_category}")
    records = read_records(paths["capability_records"], "capability")
    for path, data, _ in records:
        if data.get("id") == capability_id:
            return {"action": "new-capability", "result": "existing", "id": capability_id, "path": str(path)}
    card = replace_template(
        REPO_ROOT / "templates" / "capability-manifest.md",
        {
            "SCHEMA_VERSION": SCHEMA_VERSION,
            "CAPABILITY_ID": capability_id,
            "REVISION": "1",
            "MANAGEMENT_STATE": "candidate",
            "HEALTH_STATE": "unverified",
            "RISK": args.risk,
            "INVOCATION": "explicit-only",
            "AUTHORIZATION": "routing-proposal",
            "MANAGER_TYPE": "true" if args.manager_type else "false",
            "ROUTE_CATEGORY": args.route_category,
            "UPDATED_AT": now_utc(),
            "CAPABILITY_NAME": args.name,
            "CAPABILITY_TYPE": args.type,
        },
    )
    target = paths["capability_records"] / f"{capability_id}.md"
    transaction = Transaction(root, "new-capability")
    transaction.add(target, card)
    updated_records = [*records, (target, parse_frontmatter(card)[0], parse_frontmatter(card)[1])]
    transaction.add(paths["router"], capability_router(config, updated_records))
    current_log = paths["maintenance_log"].read_text(encoding="utf-8")
    transaction.add(
        paths["maintenance_log"],
        append_log(current_log, f"Created candidate capability `{capability_id}` as unverified and explicit-only; no capability was installed, enabled, or configured."),
    )
    transaction.commit()
    return {"action": "new-capability", "result": "created", "id": capability_id, "path": str(target)}


def locate_record(directory: Path, record_id: str, record_type: str) -> tuple[Path, dict[str, str], str]:
    target = directory / f"{record_id}.md"
    if not target.exists():
        raise WorkflowError(f"Unknown {record_type} id: {record_id}")
    data, body = parse_frontmatter(target.read_text(encoding="utf-8"), target)
    if data.get("record_type") != record_type:
        raise WorkflowError(f"Unexpected record_type in {target}")
    return target, data, body


def read_update_draft(draft_path: str, target: Path, current: dict[str, str]) -> tuple[dict[str, str], str]:
    draft = Path(draft_path).resolve()
    if draft == target.resolve():
        raise WorkflowError("--from-file must point to a separate reviewed draft, not the canonical record itself.")
    if not draft.is_file():
        raise WorkflowError(f"Update draft does not exist: {draft}")
    if draft.stat().st_size > 2 * 1024 * 1024:
        raise WorkflowError("Update draft exceeds the 2 MiB safety limit.")
    incoming, body = parse_frontmatter(draft.read_text(encoding="utf-8"), draft)
    ignored = {"revision", "updated_at"}
    for key in sorted((set(current) | set(incoming)) - ignored):
        if incoming.get(key) != current.get(key):
            raise WorkflowError(
                f"Protected frontmatter change rejected for {key!r}; use the dedicated state, health, or approval command."
            )
    return incoming, body


def command_update_project(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, _ = locate_record(paths["project_records"], args.id, "github-project")
    _, body = read_update_draft(args.from_file, target, data)
    if args.evidence_level:
        data["evidence_level"] = args.evidence_level
    data["revision"] = str(int(data["revision"]) + 1)
    data["updated_at"] = now_utc()
    changed = render_frontmatter(data, body)
    project_errors = validate_project(data, target)
    if project_errors:
        raise WorkflowError("Project update validation failed:\n" + "\n".join(project_errors))
    all_records = []
    for path, current, current_body in read_records(paths["project_records"], "github-project"):
        all_records.append((path, data, body) if path == target else (path, current, current_body))
    transaction = Transaction(root, "update-project")
    transaction.add(target, changed)
    transaction.add(paths["project_index"], project_index(all_records))
    transaction.add(paths["candidate_pool"], filtered_project_table("Candidate Pool / 候选池", all_records, {"candidate", "evaluated"}))
    transaction.add(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", all_records, {"rejected"}))
    current_log = paths["maintenance_log"].read_text(encoding="utf-8")
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Project `{args.id}` body updated from a reviewed draft at revision {data['revision']}; protected frontmatter was preserved."))
    transaction.commit()
    return {"action": "update-project", "id": args.id, "revision": int(data["revision"]), "evidence_level": data["evidence_level"]}


def command_update_capability(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, _ = locate_record(paths["capability_records"], args.id, "capability")
    _, body = read_update_draft(args.from_file, target, data)
    data["revision"] = str(int(data["revision"]) + 1)
    data["updated_at"] = now_utc()
    changed = render_frontmatter(data, body)
    category_ids = {entry["id"] for entry in config["route_categories"]}
    capability_errors = validate_capability(data, target, category_ids)
    if capability_errors:
        raise WorkflowError("Capability update validation failed:\n" + "\n".join(capability_errors))
    records = []
    for path, current, current_body in read_records(paths["capability_records"], "capability"):
        records.append((path, data, body) if path == target else (path, current, current_body))
    transaction = Transaction(root, "update-capability")
    transaction.add(target, changed)
    transaction.add(paths["router"], capability_router(config, records))
    current_log = paths["maintenance_log"].read_text(encoding="utf-8")
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Capability `{args.id}` body updated from a reviewed draft at revision {data['revision']}; protected frontmatter was preserved."))
    transaction.commit()
    return {"action": "update-capability", "id": args.id, "revision": int(data["revision"])}


def command_project_transition(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, body = locate_record(paths["project_records"], args.id, "github-project")
    old = data["status"]
    new = args.to
    if new not in PROJECT_TRANSITIONS.get(old, set()):
        raise WorkflowError(f"Invalid project transition: {old} -> {new}")
    if new in {"retained", "reference"} and not args.approved:
        raise WorkflowError("Promotion to retained/reference requires explicit approval and --approved.")
    grade = args.grade or data["grade"]
    if new in {"retained", "reference"} and grade not in {"S", "A", "B"}:
        raise WorkflowError("Retained/reference projects require --grade S, A, or B.")
    if new == "rejected" and grade not in {"C", "D"}:
        raise WorkflowError("Rejected projects require --grade C or D.")
    data["revision"] = str(int(data["revision"]) + 1)
    data["status"] = new
    data["grade"] = grade
    data["updated_at"] = now_utc()
    if args.approved:
        data["approved_by"] = args.approved_by or "user"
    changed = render_frontmatter(data, body)
    transaction = Transaction(root, "project-transition")
    transaction.add(target, changed)
    all_records = []
    for path, current, current_body in read_records(paths["project_records"], "github-project"):
        all_records.append((path, data, body) if path == target else (path, current, current_body))
    transaction.add(paths["project_index"], project_index(all_records))
    transaction.add(paths["candidate_pool"], filtered_project_table("Candidate Pool / 候选池", all_records, {"candidate", "evaluated"}))
    transaction.add(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", all_records, {"rejected"}))
    current_log = paths["maintenance_log"].read_text(encoding="utf-8")
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Project `{args.id}` transitioned {old} -> {new} at revision {data['revision']}."))
    transaction.commit()
    return {"action": "project-transition", "id": args.id, "from": old, "to": new, "revision": int(data["revision"])}


def command_capability_health(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, body = locate_record(paths["capability_records"], args.id, "capability")
    if args.to not in HEALTH_STATES:
        raise WorkflowError(f"Invalid health state: {args.to}")
    if args.to == "healthy" and not args.evidence.strip():
        raise WorkflowError("Healthy status requires a non-empty --evidence summary.")
    old = data["health_state"]
    data["health_state"] = args.to
    data["health_evidence"] = args.evidence.strip() or "none"
    safety_transition = None
    if data["management_state"] == "active" and args.to != "healthy":
        safety_transition = "active -> quarantine"
        data["management_state"] = "quarantine"
        data["invocation"] = "disabled"
    data["revision"] = str(int(data["revision"]) + 1)
    data["updated_at"] = now_utc()
    changed = render_frontmatter(data, body)
    transaction = Transaction(root, "capability-health")
    transaction.add(target, changed)
    records = []
    for path, current, current_body in read_records(paths["capability_records"], "capability"):
        records.append((path, data, body) if path == target else (path, current, current_body))
    transaction.add(paths["router"], capability_router(config, records))
    current_log = paths["maintenance_log"].read_text(encoding="utf-8")
    safety_note = f" Safety transition: {safety_transition}; invocation disabled." if safety_transition else ""
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Capability `{args.id}` health changed {old} -> {args.to}; evidence summary recorded in the manifest frontmatter.{safety_note}"))
    transaction.commit()
    return {"action": "capability-health", "id": args.id, "from": old, "to": args.to, "revision": int(data["revision"])}


def command_capability_transition(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, body = locate_record(paths["capability_records"], args.id, "capability")
    old = data["management_state"]
    new = args.to
    if new not in CAPABILITY_TRANSITIONS.get(old, set()):
        raise WorkflowError(f"Invalid capability transition: {old} -> {new}")
    invocation = args.invocation or data["invocation"]
    if new == "active":
        if not args.approved:
            raise WorkflowError("Promotion to active requires explicit approval and --approved.")
        if data["health_state"] != "healthy":
            raise WorkflowError("Promotion to active requires healthy evidence first.")
        if invocation == "disabled":
            invocation = "conditional"
    if data["manager_type"] == "true" and invocation == "auto":
        raise WorkflowError("Manager-type capabilities cannot use automatic invocation; use conditional or explicit-only.")
    if invocation == "auto" and (new != "active" or not args.approved):
        raise WorkflowError("Automatic invocation requires active state and explicit approval.")
    if new in {"candidate", "cold", "reference"}:
        invocation = "explicit-only"
    if new in {"disabled", "retired", "quarantine"}:
        invocation = "disabled"
    data["management_state"] = new
    data["invocation"] = invocation
    data["revision"] = str(int(data["revision"]) + 1)
    data["updated_at"] = now_utc()
    if args.approved:
        data["approved_by"] = args.approved_by or "user"
    changed = render_frontmatter(data, body)
    transaction = Transaction(root, "capability-transition")
    transaction.add(target, changed)
    records = []
    for path, current, current_body in read_records(paths["capability_records"], "capability"):
        records.append((path, data, body) if path == target else (path, current, current_body))
    transaction.add(paths["router"], capability_router(config, records))
    current_log = paths["maintenance_log"].read_text(encoding="utf-8")
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Capability `{args.id}` transitioned {old} -> {new}; invocation={invocation}. This records routing state only and does not alter client configuration."))
    transaction.commit()
    return {"action": "capability-transition", "id": args.id, "from": old, "to": new, "invocation": invocation, "revision": int(data["revision"])}


def command_rebuild(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    transaction = Transaction(root, "rebuild")
    for item in build_derived_writes(root, config):
        transaction.add(item.path, item.content)
    transaction.commit()
    errors, summary = collect_validation(root)
    if errors:
        raise WorkflowError("Rebuild validation failed:\n" + "\n".join(errors))
    return {"action": "rebuild", "result": "updated", **summary}


def command_validate(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    errors, summary = collect_validation(root)
    if errors:
        raise WorkflowError("Validation failed:\n" + "\n".join(errors))
    return {"action": "validate", "result": "pass", **summary}


def relative_markdown_links(path: Path, text: str) -> Iterable[str]:
    for match in re.finditer(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)", text):
        target = match.group(1).split("#", 1)[0].strip()
        if target:
            yield target


def secret_findings(text: str, location: str, patterns: dict[str, str]) -> list[str]:
    return [f"Potential {label} in {location}" for label, pattern in patterns.items() if re.search(pattern, text)]


def command_validate_repo(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    required = [
        "AGENT-START.md",
        "README.md",
        "README.zh-CN.md",
        "README.en.md",
        "config/workflow.example.json",
        "scripts/workflow.py",
        "tests/test_workflow.py",
        "templates/github-project-card.md",
        "templates/capability-manifest.md",
        "templates/vault-rules.md",
        "schemas/workflow-config.schema.json",
        "schemas/project-card.schema.json",
        "schemas/capability-manifest.schema.json",
        "examples/generated-demo-v1/README.md",
        ".agents/skills/github-vault-router/SKILL.md",
        ".claude/skills/github-vault-router/SKILL.md",
    ]
    errors = [f"Missing required repository file: {name}" for name in required if not (root / name).exists()]
    markdown = sorted(root.rglob("*.md"))
    for path in markdown:
        if any(part in {".git", ".workflow"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for target in relative_markdown_links(path, text):
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"Broken relative link: {path.relative_to(root)} -> {target}")
    for path in sorted([*(root / "config").glob("*.json"), *(root / "schemas").glob("*.json")]):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"Invalid JSON: {path.relative_to(root)}: {exc}")
    demo_root = root / "examples" / "generated-demo-v1"
    if (demo_root / "workflow.json").exists():
        demo_errors, _ = collect_validation(demo_root)
        errors.extend(f"Generated demo: {error}" for error in demo_errors)
    secret_patterns = {
        "private key": r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
        "GitHub token": r"gh[pousr]_[A-Za-z0-9]{20,}",
        "OpenAI key": r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}",
        "private home path": r"(?i)(?:[A-Z]:\\Users\\(?!example(?:\\|$))[^\\\s]+|/(?:Users|home)/(?!example(?:/|$))[^/\s]+)",
    }
    for path in sorted(item for item in root.rglob("*") if item.is_file() and ".git" not in item.parts):
        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        errors.extend(secret_findings(text, str(path.relative_to(root)), secret_patterns))
    history_scanned = False
    if (root / ".git").is_dir() and shutil.which("git"):
        history = subprocess.run(
            ["git", "-C", str(root), "log", "-p", "--all", "--no-ext-diff", "--no-color"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if history.returncode != 0:
            errors.append(f"Git history scan failed: {history.stderr.strip() or 'unknown git error'}")
        else:
            history_scanned = True
            errors.extend(secret_findings(history.stdout, "Git history", secret_patterns))
    if errors:
        raise WorkflowError("Repository validation failed:\n" + "\n".join(errors))
    return {
        "action": "validate-repo",
        "result": "pass",
        "markdown_files": len(markdown),
        "history_scanned": history_scanned,
        "errors": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap and maintain an Agent Vault workflow.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a new isolated workflow root.")
    init.add_argument("--root", required=True)
    init.add_argument("--language", choices=["zh-CN", "en"], default="zh-CN")
    init.add_argument("--client", choices=["generic-agent", "codex", "claude-code"], default="generic-agent")
    init.set_defaults(handler=command_init, mutates=True)

    new_project = sub.add_parser("new-project", help="Create one idempotent GitHub project candidate record.")
    new_project.add_argument("--root", required=True)
    new_project.add_argument("--url", required=True)
    new_project.set_defaults(handler=command_new_project, mutates=True)

    new_capability = sub.add_parser("new-capability", help="Create one idempotent capability candidate record.")
    new_capability.add_argument("--root", required=True)
    new_capability.add_argument("--id", required=True)
    new_capability.add_argument("--name", required=True)
    new_capability.add_argument("--type", required=True)
    new_capability.add_argument("--route-category", required=True)
    new_capability.add_argument("--risk", choices=["low", "medium", "high"], default="medium")
    new_capability.add_argument("--manager-type", action="store_true")
    new_capability.set_defaults(handler=command_new_capability, mutates=True)

    update_project = sub.add_parser("update-project", help="Write a reviewed project-card draft without bypassing protected state fields.")
    update_project.add_argument("--root", required=True)
    update_project.add_argument("--id", required=True)
    update_project.add_argument("--from-file", required=True)
    update_project.add_argument("--evidence-level", choices=sorted(EVIDENCE_LEVELS))
    update_project.set_defaults(handler=command_update_project, mutates=True)

    update_capability = sub.add_parser("update-capability", help="Write a reviewed capability draft without bypassing protected state fields.")
    update_capability.add_argument("--root", required=True)
    update_capability.add_argument("--id", required=True)
    update_capability.add_argument("--from-file", required=True)
    update_capability.set_defaults(handler=command_update_capability, mutates=True)

    project_transition = sub.add_parser("project-transition", help="Apply a validated project state transition.")
    project_transition.add_argument("--root", required=True)
    project_transition.add_argument("--id", required=True)
    project_transition.add_argument("--to", choices=sorted(PROJECT_STATUSES), required=True)
    project_transition.add_argument("--grade", choices=sorted(PROJECT_GRADES))
    project_transition.add_argument("--approved", action="store_true")
    project_transition.add_argument("--approved-by")
    project_transition.set_defaults(handler=command_project_transition, mutates=True)

    health = sub.add_parser("capability-health", help="Record capability health evidence.")
    health.add_argument("--root", required=True)
    health.add_argument("--id", required=True)
    health.add_argument("--to", choices=sorted(HEALTH_STATES), required=True)
    health.add_argument("--evidence", default="")
    health.set_defaults(handler=command_capability_health, mutates=True)

    capability_transition = sub.add_parser("capability-transition", help="Apply a validated capability state transition.")
    capability_transition.add_argument("--root", required=True)
    capability_transition.add_argument("--id", required=True)
    capability_transition.add_argument("--to", choices=sorted(MANAGEMENT_STATES), required=True)
    capability_transition.add_argument("--invocation", choices=sorted(INVOCATION_STATES))
    capability_transition.add_argument("--approved", action="store_true")
    capability_transition.add_argument("--approved-by")
    capability_transition.set_defaults(handler=command_capability_transition, mutates=True)

    rebuild = sub.add_parser("rebuild", help="Regenerate indexes and router from canonical records.")
    rebuild.add_argument("--root", required=True)
    rebuild.set_defaults(handler=command_rebuild, mutates=True)

    validate = sub.add_parser("validate", help="Validate an initialized workflow root.")
    validate.add_argument("--root", required=True)
    validate.set_defaults(handler=command_validate, mutates=False)

    validate_repo = sub.add_parser("validate-repo", help="Validate this public repository.")
    validate_repo.add_argument("--root", default=str(REPO_ROOT))
    validate_repo.set_defaults(handler=command_validate_repo, mutates=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if getattr(args, "mutates", False):
            root = Path(args.root).resolve()
            root.mkdir(parents=True, exist_ok=True)
            with workflow_lock(root):
                result = args.handler(args)
        else:
            result = args.handler(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (WorkflowError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"result": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
