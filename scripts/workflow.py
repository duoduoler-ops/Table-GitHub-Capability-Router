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
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = "3"
REPO_ROOT = Path(__file__).resolve().parents[1]
OBSERVED_READS: ContextVar[dict[Path, str] | None] = ContextVar("observed_reads", default=None)

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
SEMANTIC_TRIGGER_LEVELS = {"high_confidence", "gated", "explicit_only"}
SEMANTIC_ELIGIBLE_STATUSES = {"retained", "reference"}
SEMANTIC_EMPTY = "none"
SEMANTIC_EXAMPLE_SEPARATOR = " || "
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
DEPLOYMENT_SCOPES = {"not-installed", "project", "user", "global", "external-service"}
INVOCATION_STATES = {"auto", "conditional", "explicit-only", "disabled"}
ROUTABLE_MANAGEMENT_STATES = {"active", "cold", "reference"}
AUTHORIZATION_STATES = {"ordinary-record", "lifecycle-update", "routing-proposal", "configuration-change"}
CAPABILITY_TRANSITIONS = {
    "candidate": {"active", "cold", "disabled", "reference", "quarantine", "retired"},
    "active": {"cold", "disabled", "quarantine", "retired"},
    "cold": {"active", "disabled", "reference", "quarantine", "retired"},
    "disabled": {"active", "cold", "reference", "quarantine", "retired"},
    "reference": {"candidate", "active", "cold", "disabled", "quarantine", "retired"},
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
    "capability_summary",
    "semantic_examples",
    "trigger_level",
    "negative_routing",
    "updated_at",
}
REQUIRED_CAPABILITY_FIELDS = {
    "schema_version",
    "record_type",
    "id",
    "revision",
    "management_state",
    "health_state",
    "deployment_scope",
    "risk",
    "invocation",
    "authorization",
    "manager_type",
    "route_category",
    "updated_at",
}

REPOSITORY_SECRET_PATTERNS = {
    "private key": r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
    "GitHub token": r"gh[pousr]_[A-Za-z0-9]{20,}",
    "OpenAI key": r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}",
    "private home path": r"(?i)(?:[A-Z]:\\Users\\(?!example(?:\\|$))[^\\\s]+|/(?:Users|home)/(?!example(?:/|$))[^/\s]+)",
    "private Windows path": r"(?i)\b[A-Z]:\\(?!\\|example(?:\\|$)|Users(?:\\|$)|<)[^\s`\"'<>()]+",
}


class WorkflowError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "absent"


def read_text(path: Path) -> str:
    """Capture the first read in a mutation so later edits cannot be overwritten."""
    raw = path.read_bytes()
    observed = OBSERVED_READS.get()
    if observed is not None:
        observed.setdefault(path.resolve(), hashlib.sha256(raw).hexdigest())
    return raw.decode("utf-8").replace("\r\n", "\n")


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
    text = read_text(path)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", text)))
    if unresolved:
        raise WorkflowError(f"Template {path.name} has unresolved placeholders: {', '.join(unresolved)}")
    return text


def atomic_write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        with temp.open("wb") as handle:
            handle.write(content.encode("utf-8") if isinstance(content, str) else content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


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
    expected_sha256: str = ""


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
        if any(item.path == resolved for item in self.writes):
            raise WorkflowError(f"Duplicate transaction target: {resolved}")
        observed = OBSERVED_READS.get() or {}
        self.writes.append(PendingWrite(resolved, content, observed.get(resolved, file_hash(resolved))))

    def commit(self) -> None:
        if not self.writes:
            return
        observed = dict(OBSERVED_READS.get() or {})
        expected = observed | {item.path: item.expected_sha256 for item in self.writes}

        def assert_current(hashes: dict[Path, str]) -> None:
            for path, expected_hash in hashes.items():
                if file_hash(path) != expected_hash:
                    raise WorkflowError(f"Concurrent change detected; current file preserved: {path}")

        assert_current(expected)
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
            old_bytes = item.path.read_bytes() if existed else b""
            if (hashlib.sha256(old_bytes).hexdigest() if existed else "absent") != item.expected_sha256:
                raise WorkflowError(f"Concurrent change detected before backup: {item.path}")
            if existed:
                backup = self.before / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(old_bytes)
            manifest["files"].append(
                {
                    "path": relative,
                    "existed": existed,
                    "before_sha256": item.expected_sha256,
                    "after_sha256": sha256_text(item.content),
                }
            )
        manifest_path = self.dir / "manifest.json"
        def save_manifest() -> None:
            atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

        manifest["status"] = "applying"
        save_manifest()
        applied: list[PendingWrite] = []
        try:
            for item in self.writes:
                assert_current(expected)
                atomic_write(item.path, item.content)
                applied.append(item)
                expected[item.path] = sha256_text(item.content)
            assert_current(expected)
            errors, _ = collect_validation(self.root)
            if errors:
                raise WorkflowError("Post-write validation failed:\n" + "\n".join(errors))
            assert_current(expected)
            manifest["status"] = "committed"
            manifest["committed_at"] = now_utc()
            save_manifest()
        except BaseException as error:
            recovery: list[str] = []
            for item in reversed(applied):
                relative = item.path.relative_to(self.root)
                backup = self.before / relative
                try:
                    if file_hash(item.path) != sha256_text(item.content):
                        recovery.append(f"Concurrent edit preserved: {relative.as_posix()}")
                    elif item.expected_sha256 != "absent":
                        if file_hash(backup) != item.expected_sha256:
                            raise WorkflowError("Backup hash mismatch")
                        atomic_write(item.path, backup.read_bytes())
                    else:
                        item.path.unlink()
                except (OSError, WorkflowError):
                    recovery.append(f"Restore requires review: {relative.as_posix()}")
            manifest["status"] = "recovery_required" if recovery else "rolled_back"
            manifest["recovery"] = recovery
            manifest["error_type"] = type(error).__name__
            manifest.pop("committed_at", None)
            try:
                save_manifest()
            except OSError as receipt_error:
                raise WorkflowError(f"Inspect transaction backups and targets; receipt update failed: {self.dir}") from receipt_error
            raise


def config_path(root: Path) -> Path:
    return root / "workflow.json"


def load_config(root: Path) -> dict:
    path = config_path(root)
    if not path.exists():
        raise WorkflowError(f"Missing {path}. Run the init command first.")
    config = json.loads(read_text(path))
    missing = REQUIRED_CONFIG_KEYS - set(config)
    if missing:
        raise WorkflowError(f"workflow.json is missing: {', '.join(sorted(missing))}")
    if str(config["schema_version"]) != SCHEMA_VERSION:
        if str(config["schema_version"]) in {"1", "2"}:
            raise WorkflowError(
                f"Workflow schema version {config['schema_version']} requires migration. "
                "Run migrate-v3 before other commands."
            )
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
    if config["client_profile"] not in {"generic-agent", "codex", "claude-code", "grok-build"}:
        raise WorkflowError(f"Unsupported client profile: {config['client_profile']}")
    return config


def resolve_paths(root: Path, config: dict) -> dict[str, Path]:
    required = {
        "project_records",
        "capability_records",
        "project_index",
        "semantic_router",
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
        data, body = parse_frontmatter(read_text(path), path)
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


def project_semantic_examples(data: dict[str, str]) -> list[str]:
    raw = data.get("semantic_examples", "").strip()
    if not raw or raw == SEMANTIC_EMPTY:
        return []
    return [item.strip() for item in raw.split(SEMANTIC_EXAMPLE_SEPARATOR) if item.strip()]


def escape_markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def semantic_project_router(records: Iterable[tuple[Path, dict[str, str], str]]) -> str:
    trigger_labels = {
        "high_confidence": "remind / 先提醒",
        "gated": "remind; gate before read or run / 先提醒；读取或执行前过门槛",
        "explicit_only": "named only / 仅点名提醒",
    }
    discovery_rows = []
    detail_rows = []
    for path, data, _ in sorted(records, key=lambda item: item[1]["id"]):
        if data["status"] not in SEMANTIC_ELIGIBLE_STATUSES:
            continue
        examples = "<br>".join(escape_markdown_cell(item) for item in project_semantic_examples(data))
        trigger_level = data.get("trigger_level", "")
        trigger_label = trigger_labels.get(trigger_level, f"invalid: {escape_markdown_cell(trigger_level)}")
        discovery_rows.append(
            f"| [{data['id']}](../projects/records/{path.name}) | {data['grade']} / {data['status']} | "
            f"{escape_markdown_cell(data.get('capability_summary', ''))} | {trigger_label} |"
        )
        detail_rows.append(
            f"| [{data['id']}](../projects/records/{path.name}) | {data['grade']} / {data['status']} | "
            f"{examples} | {trigger_label} | "
            f"{escape_markdown_cell(data.get('negative_routing', ''))} |"
        )
    return "\n".join(
        [
            "<!-- generated by scripts/workflow.py; do not edit manually -->",
            "# GitHub Project Reference Routing / GitHub 项目参考路由",
            "",
            "> Read-only candidate layer: discovery is a reminder, not repository use or runtime activation.",
            "> 只读候选层：发现只代表提醒，不等于读取仓库或启用运行时。",
            "> A match does not authorize clone, installation, login, unknown script execution, configuration changes, or publishing.",
            "> 语义命中不授权 clone、安装、登录、运行未知脚本、修改配置或对外发布。",
            "",
            "## Level 0: Thin Discovery / 薄发现表（Agent 必读）",
            "",
            "> For every substantive task with a clear object, action, or deliverable, read this thin table once per deliverable type before concluding that no saved project is relevant.",
            "> 凡任务已有明确对象、动作或产物，在断定没有相关入库项目之前，每类产物先读一次本薄表。纯闲聊、情绪交流和无行动的一句话问答除外。",
            "> If meaning matches, select at most Top-1, then read only its row in the full table. Workflow and project reference are parallel: one explains how to work; the other identifies a saved project that may strengthen the work.",
            "> 语义命中时最多选择 Top-1，再只读下方完整表中对应行。工作流与项目参考并行：前者说明怎么做，后者提示库里已有谁可能补强。",
            "",
            "| Project | Grade / Status | Capability summary / 能力摘要 | Discovery behavior / 发现行为 |",
            "| --- | --- | --- | --- |",
            *discovery_rows,
            "",
            "## Level 1: Full Semantic Routing / 完整语义命中表",
            "",
            "> `high_confidence` and `gated` both allow a reminder. `gated` controls later reading or execution, not whether the project may be mentioned. `explicit_only` requires the user to name or clearly request the project.",
            "> `high_confidence` 与 `gated` 都允许先提醒；`gated` 只控制后续读取或执行，不控制是否可以提及项目。`explicit_only` 仍要求用户点名或明确要求。",
            "> A reminder keeps `no-extra-project` and offers three routes: continue normally, read the smallest relevant Markdown after the user chooses, or ask before installation/enablement only when runtime execution is truly required.",
            "> 提醒时保留 `no-extra-project`，并提供三条路：普通方案、用户选择后只读最小 Markdown、确需运行时再询问安装或启用。",
            "",
            "| Project | Grade / Status | Everyday wording / 用户日常说法 | Trigger | Do not route / 禁止命中或优先分流 |",
            "| --- | --- | --- | --- | --- |",
            *detail_rows,
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
            f"| {data['id']} | {data['deployment_scope']} | {data['management_state']} / {data['health_state']} | {data['invocation']} | "
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
            "| ID | Deployment scope | Management / Health | Invocation | Authorization | Risk | Card |",
            "| --- | --- | --- | --- | --- | --- | --- |",
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
    if data["trigger_level"] not in SEMANTIC_TRIGGER_LEVELS:
        errors.append(f"{path}: invalid trigger_level {data['trigger_level']}")
    capability_summary = data["capability_summary"].strip()
    if len(capability_summary) > 240:
        errors.append(f"{path}: capability_summary must be 240 characters or fewer")
    examples = project_semantic_examples(data)
    if data["status"] in SEMANTIC_ELIGIBLE_STATUSES:
        if not capability_summary or capability_summary == SEMANTIC_EMPTY:
            errors.append(f"{path}: retained/reference project requires capability_summary")
        if len(examples) < 2:
            errors.append(f"{path}: retained/reference project requires at least two semantic examples")
        if len({example.casefold() for example in examples}) != len(examples):
            errors.append(f"{path}: semantic examples must be unique within the project")
        if not data["negative_routing"].strip() or data["negative_routing"] == SEMANTIC_EMPTY:
            errors.append(f"{path}: retained/reference project requires negative_routing")
    elif (
        capability_summary != SEMANTIC_EMPTY
        or examples
        or data["semantic_examples"] != SEMANTIC_EMPTY
        or data["trigger_level"] != "explicit_only"
        or data["negative_routing"] != SEMANTIC_EMPTY
    ):
        errors.append(f"{path}: only retained/reference projects may contain semantic routing metadata")
    if not re.match(r"^gh-[a-z0-9-]+$", data["id"]):
        errors.append(f"{path}: invalid stable project id {data['id']}")
    try:
        canonical, expected_id = canonicalize_github_url(data["canonical_url"])
        if canonical != data["canonical_url"] or expected_id != data["id"]:
            errors.append(f"{path}: canonical URL and id do not agree")
    except WorkflowError as exc:
        errors.append(f"{path}: {exc}")
    return errors


def validate_semantic_uniqueness(
    records: Iterable[tuple[Path, dict[str, str], str]]
) -> list[str]:
    example_owners: dict[str, list[str]] = {}
    capability_owners: dict[str, list[str]] = {}
    for _, data, _ in records:
        if data.get("status") not in SEMANTIC_ELIGIBLE_STATUSES:
            continue
        capability = data.get("capability_summary", "").strip().casefold()
        if capability and capability != SEMANTIC_EMPTY:
            capability_owners.setdefault(capability, []).append(data.get("id", "<missing-id>"))
        for example in project_semantic_examples(data):
            example_owners.setdefault(example.casefold(), []).append(data.get("id", "<missing-id>"))
    errors = [
        f"Duplicate semantic example across projects: {example!r} -> {sorted(set(project_ids))}"
        for example, project_ids in sorted(example_owners.items())
        if len(set(project_ids)) > 1
    ]
    errors.extend(
        f"Duplicate capability summary across projects: {capability!r} -> {sorted(set(project_ids))}"
        for capability, project_ids in sorted(capability_owners.items())
        if len(set(project_ids)) > 1
    )
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
    if data["deployment_scope"] not in DEPLOYMENT_SCOPES:
        errors.append(f"{path}: invalid deployment_scope {data['deployment_scope']}")
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
    if data["management_state"] == "active" and data["deployment_scope"] == "not-installed":
        errors.append(f"{path}: active capability requires a deployed scope")
    if data["management_state"] == "reference" and data["deployment_scope"] != "not-installed":
        errors.append(f"{path}: reference capability must use not-installed deployment scope")
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


def collect_validation(root: Path, template_root: Path | None = None) -> tuple[list[str], dict]:
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
    errors.extend(validate_semantic_uniqueness(projects))
    expected: dict[Path, str] = {
        root / "AGENT-ROUTER.md": replace_template(
            (template_root or REPO_ROOT) / "templates" / "vault-rules.md",
            {
                "SCHEMA_VERSION": SCHEMA_VERSION,
                "CLIENT_PROFILE": config["client_profile"],
                "LANGUAGE": config["language"],
            },
        )
    }
    if all(REQUIRED_PROJECT_FIELDS <= set(data) for _, data, _ in projects):
        expected.update(
            {
                paths["project_index"]: project_index(projects),
                paths["semantic_router"]: semantic_project_router(projects),
                paths["candidate_pool"]: filtered_project_table(
                    "Candidate Pool / 候选池", projects, {"candidate", "evaluated"}
                ),
                paths["rejection_log"]: filtered_project_table(
                    "Rejection Log / 否决记录", projects, {"rejected"}
                ),
            }
        )
    if all(REQUIRED_CAPABILITY_FIELDS <= set(data) for _, data, _ in capabilities):
        expected[paths["router"]] = capability_router(config, capabilities)
    for path, content in expected.items():
        if not path.exists():
            errors.append(f"Missing generated file: {path}")
        elif read_text(path).replace("\r\n", "\n") != content:
            errors.append(f"Generated file is stale: {path}")
    summary = {
        "schema_version": int(SCHEMA_VERSION),
        "root": str(root.resolve()),
        "projects": len(projects),
        "semantic_projects": sum(
            1 for _, data, _ in projects if data.get("status") in SEMANTIC_ELIGIBLE_STATUSES
        ),
        "capabilities": len(capabilities),
        "errors": len(errors),
    }
    return errors, summary


def build_derived_writes(root: Path, config: dict) -> list[PendingWrite]:
    paths = resolve_paths(root, config)
    projects = read_records(paths["project_records"], "github-project")
    capabilities = read_records(paths["capability_records"], "capability")
    return [
        PendingWrite(
            root / "AGENT-ROUTER.md",
            replace_template(
                REPO_ROOT / "templates" / "vault-rules.md",
                {
                    "SCHEMA_VERSION": SCHEMA_VERSION,
                    "CLIENT_PROFILE": config["client_profile"],
                    "LANGUAGE": config["language"],
                },
            ),
        ),
        PendingWrite(paths["project_index"], project_index(projects)),
        PendingWrite(paths["semantic_router"], semantic_project_router(projects)),
        PendingWrite(
            paths["candidate_pool"],
            filtered_project_table("Candidate Pool / 候选池", projects, {"candidate", "evaluated"}),
        ),
        PendingWrite(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", projects, {"rejected"})),
        PendingWrite(paths["router"], capability_router(config, capabilities)),
    ]


def parse_capability_summary_specs(values: list[str] | None) -> dict[str, str]:
    summaries: dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            raise WorkflowError(
                "Each --capability-summary must use PROJECT_ID=SUMMARY, for example "
                "gh-owner-repo=Compare repository patterns and produce a reusable decision."
            )
        project_id, summary = (part.strip() for part in raw.split("=", 1))
        if not re.match(r"^gh-[a-z0-9-]+$", project_id):
            raise WorkflowError(f"Invalid project id in --capability-summary: {project_id}")
        if not summary or summary == SEMANTIC_EMPTY:
            raise WorkflowError(f"Capability summary for {project_id} must not be empty or 'none'.")
        if len(summary) > 240:
            raise WorkflowError(f"Capability summary for {project_id} must be 240 characters or fewer.")
        if project_id in summaries:
            raise WorkflowError(f"Duplicate --capability-summary for {project_id}.")
        summaries[project_id] = summary
    return summaries


def parse_deployment_scope_specs(values: list[str] | None) -> dict[str, str]:
    scopes: dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            raise WorkflowError(
                "Each --deployment-scope must use CAPABILITY_ID=SCOPE, for example "
                "public-doc-checker=project."
            )
        capability_id, scope = (part.strip() for part in raw.split("=", 1))
        if not re.match(r"^[a-z][a-z0-9-]+$", capability_id):
            raise WorkflowError(f"Invalid capability id in --deployment-scope: {capability_id}")
        if scope not in DEPLOYMENT_SCOPES:
            raise WorkflowError(
                f"Invalid deployment scope for {capability_id}: {scope}. "
                f"Choose one of {', '.join(sorted(DEPLOYMENT_SCOPES))}."
            )
        if capability_id in scopes:
            raise WorkflowError(f"Duplicate --deployment-scope for {capability_id}.")
        scopes[capability_id] = scope
    return scopes


def insert_frontmatter_field(
    data: dict[str, str], after_key: str, field: str, value: str
) -> dict[str, str]:
    updated: dict[str, str] = {}
    inserted = False
    for key, current in data.items():
        if key == field:
            continue
        updated[key] = current
        if key == after_key:
            updated[field] = value
            inserted = True
    if not inserted:
        updated[field] = value
    return updated


def command_migrate_v3(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    path = config_path(root)
    if not path.exists():
        raise WorkflowError(f"Missing {path}. Only initialized schema v1/v2 workflows can be migrated.")
    config = json.loads(read_text(path))
    missing_config = REQUIRED_CONFIG_KEYS - set(config)
    if missing_config:
        raise WorkflowError(f"workflow.json is missing: {', '.join(sorted(missing_config))}")
    current_version = str(config.get("schema_version", ""))
    if current_version == SCHEMA_VERSION:
        errors, summary = collect_validation(root)
        if errors:
            raise WorkflowError("Already schema v3 but invalid:\n" + "\n".join(errors))
        return {"action": "migrate-v3", "result": "already_migrated", **summary}
    if current_version not in {"1", "2"}:
        raise WorkflowError(
            f"migrate-v3 only accepts schema version 1 or 2, found {current_version or '<missing>'}."
        )
    category_ids_list = [entry.get("id") for entry in config["route_categories"]]
    if not 1 <= len(category_ids_list) <= 10 or len(category_ids_list) != len(set(category_ids_list)):
        raise WorkflowError("route_categories must contain unique non-empty ids.")
    for entry in config["route_categories"]:
        if not re.match(r"^[a-z][a-z0-9-]+$", str(entry.get("id", ""))):
            raise WorkflowError(f"Invalid route category id: {entry.get('id')}")
        if not str(entry.get("label", "")).strip() or not str(entry.get("boundary", "")).strip():
            raise WorkflowError(f"Route category requires non-empty label and boundary: {entry.get('id')}")
    if config["language"] not in {"zh-CN", "en"}:
        raise WorkflowError(f"Unsupported language: {config['language']}")
    if config["client_profile"] not in {"generic-agent", "codex", "claude-code", "grok-build"}:
        raise WorkflowError(f"Unsupported client profile: {config['client_profile']}")

    paths = resolve_paths(root, config)
    projects = read_records(paths["project_records"], "github-project")
    capabilities = read_records(paths["capability_records"], "capability")
    supplied_summaries = parse_capability_summary_specs(args.capability_summary)
    supplied_scopes = parse_deployment_scope_specs(args.deployment_scope)
    eligible_ids = {
        data["id"] for _, data, _ in projects if data.get("status") in SEMANTIC_ELIGIBLE_STATUSES
    }
    unknown_summaries = sorted(set(supplied_summaries) - eligible_ids)
    if unknown_summaries:
        raise WorkflowError(
            "Capability summaries may only target retained/reference projects: "
            + ", ".join(unknown_summaries)
        )
    if current_version == "1":
        missing_summaries = sorted(
            project_id for project_id in eligible_ids if not supplied_summaries.get(project_id)
        )
    else:
        missing_summaries = []
    if missing_summaries:
        raise WorkflowError(
            "Direct schema v1 -> v3 migration requires one --capability-summary "
            "PROJECT_ID=SUMMARY for each retained/reference project. Missing: "
            + ", ".join(missing_summaries)
        )
    capability_ids = {data["id"] for _, data, _ in capabilities}
    unknown_scopes = sorted(set(supplied_scopes) - capability_ids)
    if unknown_scopes:
        raise WorkflowError(
            "Deployment scopes target unknown capabilities: " + ", ".join(unknown_scopes)
        )
    missing_scopes = sorted(capability_ids - set(supplied_scopes))
    if missing_scopes:
        raise WorkflowError(
            "Schema v3 migration requires one --deployment-scope CAPABILITY_ID=SCOPE for each "
            "capability; scope is never inferred. Missing: " + ", ".join(missing_scopes)
        )

    timestamp = now_utc()
    migrated_projects: list[tuple[Path, dict[str, str], str]] = []
    for project_path, data, body in projects:
        if data.get("schema_version") != current_version:
            raise WorkflowError(f"Expected schema version {current_version} in {project_path}.")
        if current_version == "1":
            capability_summary = (
                supplied_summaries[data["id"]] if data["id"] in eligible_ids else SEMANTIC_EMPTY
            )
            updated = insert_frontmatter_field(
                data, "evidence_level", "capability_summary", capability_summary
            )
        else:
            updated = dict(data)
        updated["schema_version"] = SCHEMA_VERSION
        updated["revision"] = str(int(updated["revision"]) + 1)
        updated["updated_at"] = timestamp
        project_errors = validate_project(updated, project_path)
        if project_errors:
            raise WorkflowError("Project migration validation failed:\n" + "\n".join(project_errors))
        migrated_projects.append((project_path, updated, body))

    category_ids = {entry["id"] for entry in config["route_categories"]}
    migrated_capabilities: list[tuple[Path, dict[str, str], str]] = []
    for capability_path, data, body in capabilities:
        if data.get("schema_version") != current_version:
            raise WorkflowError(f"Expected schema version {current_version} in {capability_path}.")
        updated = insert_frontmatter_field(
            data,
            "health_state",
            "deployment_scope",
            supplied_scopes[data["id"]],
        )
        updated["schema_version"] = SCHEMA_VERSION
        updated["revision"] = str(int(updated["revision"]) + 1)
        updated["updated_at"] = timestamp
        capability_errors = validate_capability(updated, capability_path, category_ids)
        if capability_errors:
            raise WorkflowError("Capability migration validation failed:\n" + "\n".join(capability_errors))
        migrated_capabilities.append((capability_path, updated, body))

    uniqueness_errors = validate_semantic_uniqueness(migrated_projects)
    if uniqueness_errors:
        raise WorkflowError("Project migration validation failed:\n" + "\n".join(uniqueness_errors))
    project_ids = [data["id"] for _, data, _ in migrated_projects]
    project_urls = [data["canonical_url"] for _, data, _ in migrated_projects]
    migrated_capability_ids = [data["id"] for _, data, _ in migrated_capabilities]
    duplicate_errors = []
    for label, values in (
        ("project id", project_ids),
        ("project URL", project_urls),
        ("capability id", migrated_capability_ids),
    ):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            duplicate_errors.append(f"Duplicate {label}: {duplicates}")
    if duplicate_errors:
        raise WorkflowError("Migration duplicate validation failed:\n" + "\n".join(duplicate_errors))

    migrated_config = dict(config)
    migrated_config["schema_version"] = int(SCHEMA_VERSION)
    transaction = Transaction(root, "migrate-v3")
    transaction.add(path, json.dumps(migrated_config, ensure_ascii=False, indent=2) + "\n")
    for project_path, data, body in migrated_projects:
        transaction.add(project_path, render_frontmatter(data, body))
    for capability_path, data, body in migrated_capabilities:
        transaction.add(capability_path, render_frontmatter(data, body))
    transaction.add(
        root / "AGENT-ROUTER.md",
        replace_template(
            REPO_ROOT / "templates" / "vault-rules.md",
            {
                "SCHEMA_VERSION": SCHEMA_VERSION,
                "CLIENT_PROFILE": migrated_config["client_profile"],
                "LANGUAGE": migrated_config["language"],
            },
        ),
    )
    transaction.add(paths["project_index"], project_index(migrated_projects))
    transaction.add(paths["semantic_router"], semantic_project_router(migrated_projects))
    transaction.add(
        paths["candidate_pool"],
        filtered_project_table("Candidate Pool / 候选池", migrated_projects, {"candidate", "evaluated"}),
    )
    transaction.add(
        paths["rejection_log"],
        filtered_project_table("Rejection Log / 否决记录", migrated_projects, {"rejected"}),
    )
    transaction.add(paths["router"], capability_router(migrated_config, migrated_capabilities))
    current_log = read_text(paths["maintenance_log"])
    transaction.add(
        paths["maintenance_log"],
        append_log(
            current_log,
            f"Migrated workflow schema v{current_version} -> v3; recorded explicit deployment scope for every capability and rebuilt all derived views.",
        ),
    )
    transaction.commit()
    errors, summary = collect_validation(root)
    if errors:
        raise WorkflowError("Migration validation failed:\n" + "\n".join(errors))
    return {"action": "migrate-v3", "result": "migrated", **summary}


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
    config = json.loads(read_text(REPO_ROOT / "config" / "workflow.example.json"))
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
            {
                "SCHEMA_VERSION": SCHEMA_VERSION,
                "CLIENT_PROFILE": args.client,
                "LANGUAGE": args.language,
            },
        ),
    )
    transaction.add(paths["maintenance_log"], "# Maintenance Log / 维护日志\n")
    transaction.add(paths["project_index"], project_index([]))
    transaction.add(paths["semantic_router"], semantic_project_router([]))
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
            "CAPABILITY_SUMMARY": SEMANTIC_EMPTY,
            "SEMANTIC_EXAMPLES": SEMANTIC_EMPTY,
            "TRIGGER_LEVEL": "explicit_only",
            "NEGATIVE_ROUTING": SEMANTIC_EMPTY,
            "UPDATED_AT": now_utc(),
            "CHECK_DATE": today_utc(),
        },
    )
    target = paths["project_records"] / f"{record_id}.md"
    transaction = Transaction(root, "new-project")
    transaction.add(target, card)
    updated_records = [*records, (target, parse_frontmatter(card)[0], parse_frontmatter(card)[1])]
    transaction.add(paths["project_index"], project_index(updated_records))
    transaction.add(paths["semantic_router"], semantic_project_router(updated_records))
    transaction.add(
        paths["candidate_pool"],
        filtered_project_table("Candidate Pool / 候选池", updated_records, {"candidate", "evaluated"}),
    )
    transaction.add(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", updated_records, {"rejected"}))
    current_log = read_text(paths["maintenance_log"])
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
            "DEPLOYMENT_SCOPE": "not-installed",
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
    current_log = read_text(paths["maintenance_log"])
    transaction.add(
        paths["maintenance_log"],
        append_log(current_log, f"Created candidate capability `{capability_id}` as unverified, explicit-only, and not-installed; no capability was installed, enabled, or configured."),
    )
    transaction.commit()
    return {"action": "new-capability", "result": "created", "id": capability_id, "path": str(target)}


def locate_record(directory: Path, record_id: str, record_type: str) -> tuple[Path, dict[str, str], str]:
    target = directory / f"{record_id}.md"
    if not target.exists():
        raise WorkflowError(f"Unknown {record_type} id: {record_id}")
    data, body = parse_frontmatter(read_text(target), target)
    if data.get("record_type") != record_type:
        raise WorkflowError(f"Unexpected record_type in {target}")
    return target, data, body


def read_update_draft(draft_path: str, target: Path, current: dict[str, str], expected_sha256: str | None) -> tuple[dict[str, str], str]:
    if not expected_sha256 or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise WorkflowError("Body updates require --expected-sha256 from record-hash before drafting; reread the current record and review a fresh draft.")
    observed = OBSERVED_READS.get() or {}
    if expected_sha256.lower() != observed.get(target.resolve(), file_hash(target)):
        raise WorkflowError("Stale draft: original SHA256 no longer matches; current record preserved. Review the intervening changes before preparing a new draft.")
    draft = Path(draft_path).resolve()
    if draft == target.resolve():
        raise WorkflowError("--from-file must point to a separate reviewed draft, not the canonical record itself.")
    if not draft.is_file():
        raise WorkflowError(f"Update draft does not exist: {draft}")
    if draft.stat().st_size > 2 * 1024 * 1024:
        raise WorkflowError("Update draft exceeds the 2 MiB safety limit.")
    incoming, body = parse_frontmatter(read_text(draft), draft)
    if any(incoming.get(key) != current.get(key) for key in ("revision", "updated_at")):
        raise WorkflowError("Stale draft revision or timestamp; copy the current record and review the changes again.")
    for key in sorted(set(current) | set(incoming)):
        if incoming.get(key) != current.get(key):
            raise WorkflowError(
                f"Protected frontmatter change rejected for {key!r}; use the dedicated state, health, or approval command."
            )
    return incoming, body


def command_record_hash(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    paths = resolve_paths(root, load_config(root))
    record_type = "github-project" if args.kind == "project" else "capability"
    directory = paths["project_records" if args.kind == "project" else "capability_records"]
    target, _, _ = locate_record(directory, args.id, record_type)
    raw = target.read_bytes()
    data, _ = parse_frontmatter(raw.decode("utf-8"), target)
    return {"action": "record-hash", "id": data["id"], "revision": int(data["revision"]),
            "sha256": hashlib.sha256(raw).hexdigest(), "path": str(target)}


def command_update_project(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, _ = locate_record(paths["project_records"], args.id, "github-project")
    _, body = read_update_draft(args.from_file, target, data, args.expected_sha256)
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
    transaction.add(paths["semantic_router"], semantic_project_router(all_records))
    transaction.add(paths["candidate_pool"], filtered_project_table("Candidate Pool / 候选池", all_records, {"candidate", "evaluated"}))
    transaction.add(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", all_records, {"rejected"}))
    current_log = read_text(paths["maintenance_log"])
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Project `{args.id}` body updated from a reviewed draft at revision {data['revision']}; protected frontmatter was preserved."))
    transaction.commit()
    return {"action": "update-project", "id": args.id, "revision": int(data["revision"]), "evidence_level": data["evidence_level"]}


def command_update_capability(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, _ = locate_record(paths["capability_records"], args.id, "capability")
    _, body = read_update_draft(args.from_file, target, data, args.expected_sha256)
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
    current_log = read_text(paths["maintenance_log"])
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Capability `{args.id}` body updated from a reviewed draft at revision {data['revision']}; protected frontmatter was preserved."))
    transaction.commit()
    return {"action": "update-capability", "id": args.id, "revision": int(data["revision"])}


def normalized_semantic_metadata(
    capability_summary: str | None,
    examples: list[str] | None,
    trigger_level: str | None,
    negative_routing: str | None,
) -> tuple[str, str, str, str]:
    capability = (capability_summary or "").strip()
    if not capability or capability == SEMANTIC_EMPTY:
        raise WorkflowError("Semantic routing requires a non-empty --capability-summary value.")
    if len(capability) > 240:
        raise WorkflowError("Capability summary must be 240 characters or fewer.")
    cleaned = [item.strip() for item in (examples or []) if item.strip()]
    if len(cleaned) < 2:
        raise WorkflowError("Semantic routing requires at least two non-empty --semantic-example values.")
    if any("||" in item for item in cleaned):
        raise WorkflowError("Semantic examples must not contain the reserved separator '||'.")
    if len({item.casefold() for item in cleaned}) != len(cleaned):
        raise WorkflowError("Semantic examples must be unique within the project.")
    if trigger_level not in SEMANTIC_TRIGGER_LEVELS:
        raise WorkflowError("Semantic routing requires --trigger-level high_confidence, gated, or explicit_only.")
    negative = (negative_routing or "").strip()
    if not negative or negative == SEMANTIC_EMPTY:
        raise WorkflowError("Semantic routing requires a non-empty --negative-routing value.")
    return capability, SEMANTIC_EXAMPLE_SEPARATOR.join(cleaned), trigger_level, negative


def command_project_routing(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, body = locate_record(paths["project_records"], args.id, "github-project")
    if data["status"] not in SEMANTIC_ELIGIBLE_STATUSES:
        raise WorkflowError("Only retained/reference projects may receive semantic routing metadata.")
    capability_summary, examples, trigger_level, negative_routing = normalized_semantic_metadata(
        args.capability_summary, args.semantic_example, args.trigger_level, args.negative_routing
    )
    data["capability_summary"] = capability_summary
    data["semantic_examples"] = examples
    data["trigger_level"] = trigger_level
    data["negative_routing"] = negative_routing
    data["revision"] = str(int(data["revision"]) + 1)
    data["updated_at"] = now_utc()
    project_errors = validate_project(data, target)
    if project_errors:
        raise WorkflowError("Project routing validation failed:\n" + "\n".join(project_errors))
    changed = render_frontmatter(data, body)
    records = []
    for path, current, current_body in read_records(paths["project_records"], "github-project"):
        records.append((path, data, body) if path == target else (path, current, current_body))
    uniqueness_errors = validate_semantic_uniqueness(records)
    if uniqueness_errors:
        raise WorkflowError("Project routing validation failed:\n" + "\n".join(uniqueness_errors))
    transaction = Transaction(root, "project-routing")
    transaction.add(target, changed)
    transaction.add(paths["project_index"], project_index(records))
    transaction.add(paths["semantic_router"], semantic_project_router(records))
    current_log = read_text(paths["maintenance_log"])
    transaction.add(
        paths["maintenance_log"],
        append_log(
            current_log,
            f"Project `{args.id}` semantic routing updated at revision {data['revision']}; "
            "this is a read-only reference and grants no execution permission.",
        ),
    )
    transaction.commit()
    return {
        "action": "project-routing",
        "id": args.id,
        "trigger_level": trigger_level,
        "capability_summary": capability_summary,
        "semantic_examples": len(project_semantic_examples(data)),
        "revision": int(data["revision"]),
    }


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
    semantic_args_supplied = bool(
        args.capability_summary or args.semantic_example or args.trigger_level or args.negative_routing
    )
    if new in SEMANTIC_ELIGIBLE_STATUSES and (
        old not in SEMANTIC_ELIGIBLE_STATUSES or semantic_args_supplied
    ):
        capability_summary, semantic_examples, trigger_level, negative_routing = normalized_semantic_metadata(
            args.capability_summary, args.semantic_example, args.trigger_level, args.negative_routing
        )
        data["capability_summary"] = capability_summary
        data["semantic_examples"] = semantic_examples
        data["trigger_level"] = trigger_level
        data["negative_routing"] = negative_routing
    elif new not in SEMANTIC_ELIGIBLE_STATUSES:
        data["capability_summary"] = SEMANTIC_EMPTY
        data["semantic_examples"] = SEMANTIC_EMPTY
        data["trigger_level"] = "explicit_only"
        data["negative_routing"] = SEMANTIC_EMPTY
    data["revision"] = str(int(data["revision"]) + 1)
    data["status"] = new
    data["grade"] = grade
    data["updated_at"] = now_utc()
    if args.approved:
        data["approved_by"] = args.approved_by or "user"
    project_errors = validate_project(data, target)
    if project_errors:
        raise WorkflowError("Project transition validation failed:\n" + "\n".join(project_errors))
    changed = render_frontmatter(data, body)
    transaction = Transaction(root, "project-transition")
    transaction.add(target, changed)
    all_records = []
    for path, current, current_body in read_records(paths["project_records"], "github-project"):
        all_records.append((path, data, body) if path == target else (path, current, current_body))
    uniqueness_errors = validate_semantic_uniqueness(all_records)
    if uniqueness_errors:
        raise WorkflowError("Project transition validation failed:\n" + "\n".join(uniqueness_errors))
    transaction.add(paths["project_index"], project_index(all_records))
    transaction.add(paths["semantic_router"], semantic_project_router(all_records))
    transaction.add(paths["candidate_pool"], filtered_project_table("Candidate Pool / 候选池", all_records, {"candidate", "evaluated"}))
    transaction.add(paths["rejection_log"], filtered_project_table("Rejection Log / 否决记录", all_records, {"rejected"}))
    current_log = read_text(paths["maintenance_log"])
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
    current_log = read_text(paths["maintenance_log"])
    safety_note = f" Safety transition: {safety_transition}; invocation disabled." if safety_transition else ""
    transaction.add(paths["maintenance_log"], append_log(current_log, f"Capability `{args.id}` health changed {old} -> {args.to}; evidence summary recorded in the manifest frontmatter.{safety_note}"))
    transaction.commit()
    return {"action": "capability-health", "id": args.id, "from": old, "to": args.to, "revision": int(data["revision"])}


def command_capability_deployment(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    config = load_config(root)
    paths = resolve_paths(root, config)
    target, data, body = locate_record(paths["capability_records"], args.id, "capability")
    if not args.approved:
        raise WorkflowError("Deployment scope changes require explicit approval and --approved.")
    if not args.evidence.strip():
        raise WorkflowError("Deployment scope changes require a non-empty --evidence summary.")
    old = data["deployment_scope"]
    new = args.to
    if old == new:
        return {
            "action": "capability-deployment",
            "result": "unchanged",
            "id": args.id,
            "deployment_scope": new,
            "revision": int(data["revision"]),
        }
    if new == "not-installed" and data["management_state"] == "active":
        raise WorkflowError(
            "An active capability cannot be recorded as not-installed. "
            "Move it out of active first, then record confirmed removal."
        )
    if data["management_state"] == "reference" and new != "not-installed":
        raise WorkflowError(
            "A reference capability is method-only and cannot use an installed deployment scope."
        )
    data["deployment_scope"] = new
    data["deployment_evidence"] = args.evidence.strip()
    data["revision"] = str(int(data["revision"]) + 1)
    data["updated_at"] = now_utc()
    data["approved_by"] = args.approved_by or "user"
    category_ids = {entry["id"] for entry in config["route_categories"]}
    capability_errors = validate_capability(data, target, category_ids)
    if capability_errors:
        raise WorkflowError(
            "Capability deployment validation failed:\n" + "\n".join(capability_errors)
        )
    changed = render_frontmatter(data, body)
    transaction = Transaction(root, "capability-deployment")
    transaction.add(target, changed)
    records = []
    for path, current, current_body in read_records(paths["capability_records"], "capability"):
        records.append((path, data, body) if path == target else (path, current, current_body))
    transaction.add(paths["router"], capability_router(config, records))
    current_log = read_text(paths["maintenance_log"])
    transaction.add(
        paths["maintenance_log"],
        append_log(
            current_log,
            f"Capability `{args.id}` deployment scope changed {old} -> {new}; evidence recorded. "
            "This records an approved real-world fact and does not install or remove files.",
        ),
    )
    transaction.commit()
    return {
        "action": "capability-deployment",
        "id": args.id,
        "from": old,
        "to": new,
        "revision": int(data["revision"]),
    }


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
        if data["deployment_scope"] == "not-installed":
            raise WorkflowError("Promotion to active requires a deployed scope first.")
        if invocation == "disabled":
            invocation = "conditional"
    if new == "reference" and data["deployment_scope"] != "not-installed":
        raise WorkflowError(
            "Promotion to reference requires deployment_scope not-installed; "
            "record confirmed removal first."
        )
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
    current_log = read_text(paths["maintenance_log"])
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


def skill_identity_and_body(path: Path) -> tuple[dict[str, str], str]:
    normalized = read_text(path).replace("\r\n", "\n")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", normalized, flags=re.DOTALL)
    if not match:
        raise WorkflowError(f"Invalid Skill frontmatter in {path}")
    identity: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() in {"name", "description"}:
            identity[key.strip()] = value.strip().strip('"').strip("'")
    return identity, match.group(2)


def git_bytes(root: Path, *arguments: str, input_data: bytes | None = None) -> bytes:
    try:
        result = subprocess.run(["git", "-C", str(root), *arguments], input=input_data,
                                capture_output=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise WorkflowError("Git validation command unavailable or timed out.") from error
    if result.returncode:
        raise WorkflowError("Git validation failed: " + result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def scratch_path(path: Path) -> Path:
    """Use Windows extended paths for deeply nested, disposable index snapshots."""
    absolute = str(path.resolve())
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        absolute = "\\\\?\\UNC\\" + absolute[2:] if absolute.startswith("\\\\") else "\\\\?\\" + absolute
    return Path(absolute)


def repository_files(root: Path) -> list[Path]:
    if (root / ".git").exists():
        names = git_bytes(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        files = [root / name.decode("utf-8") for name in names.split(b"\0") if name]
    else:
        files = [path for path in root.rglob("*") if ".git" not in path.relative_to(root).parts]
    selected = []
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise WorkflowError(f"Repository validation cannot follow a linked path: {path.relative_to(root)}")
        if path.is_file():
            selected.append(path)
    return sorted(set(selected))


def validate_repository(root: Path, files: list[Path], history_root: Path | None = None) -> dict:
    required = [
        ".gitignore",
        "AGENT-START.md",
        "AGENTS.md",
        "CHANGELOG.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "README.md",
        "README.zh-CN.md",
        "README.en.md",
        "SECURITY.md",
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
        "examples/generated-demo-v1/indexes/project-semantic-routing.md",
        ".agents/skills/github-vault-router/SKILL.md",
        ".agents/skills/github-vault-router/agents/openai.yaml",
        ".claude/skills/github-vault-router/SKILL.md",
        ".githooks/pre-commit",
        "docs/migrations/v0.1-to-v0.2.md",
        "docs/migrations/v0.2-to-v0.3.md",
        "docs/migrations/v0.3-to-v0.4.md",
        "docs/client-profiles/claude-code.md",
        "docs/client-profiles/codex.md",
        "docs/client-profiles/generic-agent.md",
        "docs/client-profiles/grok-build.md",
        "docs/optional-pre-commit.md",
        "docs/optional-capability-optimizer.md",
        "integrations/optimize-agent-capabilities/SKILL.md",
        "integrations/optimize-agent-capabilities/agents/openai.yaml",
        "integrations/optimize-agent-capabilities/profiles/claude-code.json",
        "integrations/optimize-agent-capabilities/profiles/codex.json",
        "integrations/optimize-agent-capabilities/profiles/generic-agent.json",
        "integrations/optimize-agent-capabilities/profiles/grok-build.json",
        "integrations/optimize-agent-capabilities/profiles/kimi-code.json",
        "integrations/optimize-agent-capabilities/references/client-adapters.md",
        "integrations/optimize-agent-capabilities/scripts/audit.mjs",
        "integrations/optimize-agent-capabilities/tests/audit.test.mjs",
    ]
    errors = [f"Missing required repository file: {name}" for name in required if not (root / name).exists()]
    shared_skill = root / ".agents" / "skills" / "github-vault-router" / "SKILL.md"
    claude_skill = root / ".claude" / "skills" / "github-vault-router" / "SKILL.md"
    if shared_skill.exists() and claude_skill.exists():
        shared_data, shared_body = skill_identity_and_body(shared_skill)
        claude_data, claude_body = skill_identity_and_body(claude_skill)
        for field in ("name", "description"):
            if not shared_data.get(field) or not claude_data.get(field):
                errors.append(f"Repo-scoped Skills must both define non-empty {field}.")
                continue
            if shared_data.get(field) != claude_data.get(field):
                errors.append(f"Repo-scoped Skill {field} differs between shared Grok Build/Codex and Claude Code compatibility copies.")
        if shared_body != claude_body:
            errors.append("Repo-scoped Skill instructions differ between shared Grok Build/Codex and Claude Code compatibility copies.")
    openai_yaml = root / ".agents" / "skills" / "github-vault-router" / "agents" / "openai.yaml"
    if openai_yaml.exists() and "$github-vault-router" not in openai_yaml.read_text(encoding="utf-8"):
        errors.append("Repo-scoped Codex Skill default_prompt must mention $github-vault-router.")
    markdown = [path for path in files if path.suffix == ".md"]
    for path in markdown:
        if any(part in {".git", ".workflow"} for part in path.parts):
            continue
        text = read_text(path)
        for target in relative_markdown_links(path, text):
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"Broken relative link: {path.relative_to(root)} -> {target}")
    for path in (item for item in files if item.suffix == ".json"):
        try:
            json.loads(read_text(path))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"Invalid JSON: {path.relative_to(root)}: {exc}")
    demo_root = root / "examples" / "generated-demo-v1"
    if (demo_root / "workflow.json").exists():
        demo_errors, _ = collect_validation(demo_root, template_root=root)
        errors.extend(f"Generated demo: {error}" for error in demo_errors)
    for path in files:
        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        errors.extend(secret_findings(text, str(path.relative_to(root)), REPOSITORY_SECRET_PATTERNS))
    history_scanned = False
    if history_root is not None:
        history = git_bytes(history_root, "log", "-p", "--all", "--no-ext-diff", "--no-color", "--no-textconv")
        history_scanned = True
        errors.extend(secret_findings(history.decode("utf-8", errors="replace"), "Git history", REPOSITORY_SECRET_PATTERNS))
    if errors:
        raise WorkflowError("Repository validation failed:\n" + "\n".join(errors))
    return {
        "action": "validate-repo",
        "result": "pass",
        "markdown_files": len(markdown),
        "history_scanned": history_scanned,
        "errors": 0,
    }


def command_validate_repo(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    return validate_repository(root, repository_files(root), root if (root / ".git").exists() else None)


def command_validate_staged(args: argparse.Namespace) -> dict:
    """Read index blobs as data. Never execute the staged Python, hooks, or tests."""
    root = Path(args.root).resolve()
    if not Path(git_bytes(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).samefile(root):
        raise WorkflowError("--root must be the Git working tree root.")
    index = git_bytes(root, "ls-files", "--stage", "-z")
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in index.split(b"\0"):
        if not entry:
            continue
        header, raw_name = entry.split(b"\t", 1)
        mode, oid, stage = header.decode("ascii").split()
        name = raw_name.decode("utf-8")
        if stage != "0":
            raise WorkflowError(f"Unmerged index entry: {name}")
        if mode not in ("100644", "100755"):
            raise WorkflowError(f"Staged validation supports regular files only: {name}")
        parts = name.split("/")
        if any(part in ("", ".", "..") or part.casefold() == ".git" for part in parts) or "\\" in name or ":" in name:
            raise WorkflowError(f"Unsafe index path: {name}")
        key = name.casefold() if os.name == "nt" else name
        if key in seen:
            raise WorkflowError(f"Index path collision: {name}")
        seen.add(key)
        entries.append((name, oid))
    if not entries:
        raise WorkflowError("Index is empty; stage the public repository before checking it.")
    output = git_bytes(root, "cat-file", "--batch", input_data=("\n".join(oid for _, oid in entries) + "\n").encode("ascii"))
    temporary_root = root / "_test-logs"
    if temporary_root.is_symlink() or not temporary_root.resolve().is_relative_to(root):
        raise WorkflowError("Staged validation scratch directory must stay inside the repository.")
    temporary_root = scratch_path(temporary_root)
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="staged-validation-", dir=temporary_root) as directory:
        snapshot = Path(directory)
        files: list[Path] = []
        offset = 0
        for name, oid in entries:
            end = output.index(b"\n", offset)
            object_id, kind, size_text = output[offset:end].decode("ascii").split()
            size = int(size_text)
            offset = end + 1
            if object_id != oid or kind != "blob" or len(output) < offset + size + 1:
                raise WorkflowError("Invalid Git blob response.")
            target = snapshot / name
            if not target.resolve().is_relative_to(snapshot):
                raise WorkflowError(f"Index path escapes snapshot: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(output[offset:offset + size])
            offset += size + 1
            files.append(target)
        result = validate_repository(snapshot, files)
    if git_bytes(root, "ls-files", "--stage", "-z") != index:
        raise WorkflowError("Index changed during validation; check the newly staged content again.")
    return {**result, "action": "validate-staged", "source": "git-index", "index_files": len(entries)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap and maintain an Agent Vault workflow.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a new isolated workflow root.")
    init.add_argument("--root", required=True)
    init.add_argument("--language", choices=["zh-CN", "en"], default="zh-CN")
    init.add_argument(
        "--client",
        choices=["generic-agent", "codex", "claude-code", "grok-build"],
        default="generic-agent",
    )
    init.set_defaults(handler=command_init, mutates=True)

    migrate_v3 = sub.add_parser(
        "migrate-v3",
        help="Transactionally migrate an initialized schema v1/v2 workflow to v3.",
    )
    migrate_v3.add_argument("--root", required=True)
    migrate_v3.add_argument(
        "--capability-summary",
        action="append",
        help="For direct v1 migration, repeat PROJECT_ID=SUMMARY for retained/reference projects.",
    )
    migrate_v3.add_argument(
        "--deployment-scope",
        action="append",
        help="Repeat CAPABILITY_ID=SCOPE once for every capability; scope is never inferred.",
    )
    migrate_v3.set_defaults(handler=command_migrate_v3, mutates=True)

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
    update_project.add_argument("--expected-sha256", help="SHA256 captured before editing the draft with record-hash.")
    update_project.add_argument("--evidence-level", choices=sorted(EVIDENCE_LEVELS))
    update_project.set_defaults(handler=command_update_project, mutates=True)

    project_routing = sub.add_parser(
        "project-routing",
        help="Update semantic reference metadata for one retained/reference project.",
    )
    project_routing.add_argument("--root", required=True)
    project_routing.add_argument("--id", required=True)
    project_routing.add_argument("--capability-summary", required=True)
    project_routing.add_argument("--semantic-example", action="append", required=True)
    project_routing.add_argument("--trigger-level", choices=sorted(SEMANTIC_TRIGGER_LEVELS), required=True)
    project_routing.add_argument("--negative-routing", required=True)
    project_routing.set_defaults(handler=command_project_routing, mutates=True)

    update_capability = sub.add_parser("update-capability", help="Write a reviewed capability draft without bypassing protected state fields.")
    update_capability.add_argument("--root", required=True)
    update_capability.add_argument("--id", required=True)
    update_capability.add_argument("--from-file", required=True)
    update_capability.add_argument("--expected-sha256", help="SHA256 captured before editing the draft with record-hash.")
    update_capability.set_defaults(handler=command_update_capability, mutates=True)

    project_transition = sub.add_parser("project-transition", help="Apply a validated project state transition.")
    project_transition.add_argument("--root", required=True)
    project_transition.add_argument("--id", required=True)
    project_transition.add_argument("--to", choices=sorted(PROJECT_STATUSES), required=True)
    project_transition.add_argument("--grade", choices=sorted(PROJECT_GRADES))
    project_transition.add_argument("--approved", action="store_true")
    project_transition.add_argument("--approved-by")
    project_transition.add_argument("--capability-summary")
    project_transition.add_argument("--semantic-example", action="append")
    project_transition.add_argument("--trigger-level", choices=sorted(SEMANTIC_TRIGGER_LEVELS))
    project_transition.add_argument("--negative-routing")
    project_transition.set_defaults(handler=command_project_transition, mutates=True)

    health = sub.add_parser("capability-health", help="Record capability health evidence.")
    health.add_argument("--root", required=True)
    health.add_argument("--id", required=True)
    health.add_argument("--to", choices=sorted(HEALTH_STATES), required=True)
    health.add_argument("--evidence", default="")
    health.set_defaults(handler=command_capability_health, mutates=True)

    deployment = sub.add_parser(
        "capability-deployment",
        help="Record an explicitly approved deployment-scope fact without installing or removing files.",
    )
    deployment.add_argument("--root", required=True)
    deployment.add_argument("--id", required=True)
    deployment.add_argument("--to", choices=sorted(DEPLOYMENT_SCOPES), required=True)
    deployment.add_argument("--evidence", required=True)
    deployment.add_argument("--approved", action="store_true")
    deployment.add_argument("--approved-by")
    deployment.set_defaults(handler=command_capability_deployment, mutates=True)

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

    staged = sub.add_parser("validate-staged", help="Validate the actual Git index without running staged code or scanning history.")
    staged.add_argument("--root", default=str(REPO_ROOT))
    staged.set_defaults(handler=command_validate_staged, mutates=False)

    record_hash = sub.add_parser("record-hash", help="Read the base hash and revision before preparing a body-update draft.")
    record_hash.add_argument("--root", required=True)
    record_hash.add_argument("--kind", choices=("project", "capability"), required=True)
    record_hash.add_argument("--id", required=True)
    record_hash.set_defaults(handler=command_record_hash, mutates=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if getattr(args, "mutates", False):
            root = Path(args.root).resolve()
            root.mkdir(parents=True, exist_ok=True)
            with workflow_lock(root):
                token = OBSERVED_READS.set({})
                try:
                    result = args.handler(args)
                finally:
                    OBSERVED_READS.reset(token)
        else:
            result = args.handler(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (WorkflowError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"result": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
