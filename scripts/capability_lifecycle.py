"""Optional, record-only evidence and use receipts for existing schema-v3 vaults."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from lifecycle_contract import ContractError, timestamp, validate

STORE = ".workflow/lifecycle"
STATE_FIELDS = ("management_state", "health_state", "deployment_scope", "invocation", "revision")


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def project_key(root: Path) -> str:
    return digest(os.path.normcase(str(root.resolve())))


def safe_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,95}", value):
        raise ContractError("Use a stable lowercase ID, 2-96 letters/digits/hyphens.")
    return value


def beneath(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if not relative or "\\" in relative or ":" in relative or path.is_absolute() or any(p in {"..", ".", ""} for p in relative.split("/")):
        raise ContractError("Expected a relative path without traversal or drive names.")
    target = root.joinpath(*path.parts).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ContractError("Lifecycle path escapes its root.")
    return target


def store_path(root: Path, capability_id: str, folder: str, record_id: str) -> Path:
    return beneath(root, f"{STORE}/{safe_id(capability_id)}/{folder}/{safe_id(record_id)}.json")


def read_json(api, path: Path):
    if path.stat().st_size > 128 * 1024:
        raise ContractError("Lifecycle record exceeds the 128 KiB limit.")
    return json.loads(api.read_text(path))


def identity(api, args) -> dict:
    definition = read_json(api, Path(args.identity_file).resolve())
    validate(definition, "identity-definition", api.REPO_ROOT)
    if definition["capability_id"] != args.id:
        raise ContractError("Identity definition belongs to another capability.")
    artifact_root = Path(args.artifact_root).resolve()
    if not artifact_root.is_dir():
        raise ContractError("Artifact root must be an existing directory.")
    files = []
    for name in sorted(definition["files"]):
        path = beneath(artifact_root, name)
        if path.exists() and not path.is_file():
            raise ContractError("Identity entries must be files.")
        # Read bytes directly: scripts/assets are not necessarily UTF-8 text.
        checksum = api.file_hash(path)
        observed = api.OBSERVED_READS.get()
        if observed is not None:
            previous = observed.setdefault(path, checksum)
            if previous != checksum:
                raise ContractError("Identity changed during this operation.")
        files.append({"path": name, "sha256": checksum})
    value = {"capability_id": args.id, "host": definition["host"], "version": definition["version"],
             "artifact_root_key": project_key(artifact_root), "files": files,
             "metadata_source": "caller-declared", "file_source": "measured-sha256"}
    value["sha256"] = digest(value)
    validate(value, "identity", api.REPO_ROOT)
    return value


def validate_identity(value: dict) -> None:
    if value["sha256"] != digest({key: item for key, item in value.items() if key != "sha256"}):
        raise ContractError("Identity fingerprint does not match its components.")
    names = [entry["path"] for entry in value["files"]]
    if names != sorted(set(names)):
        raise ContractError("Identity file list must be sorted and unique.")
    for name in names:
        # Pure syntax check; historical records must not touch today's artifacts.
        if not name or "\\" in name or ":" in name or name.startswith("/") or any(p in {"..", ".", ""} for p in name.split("/")):
            raise ContractError("Invalid historical identity path.")


def validate_record(api, value: dict, kind: str, capability_id: str, record_id: str, schema_root: Path | None = None) -> None:
    validate(value, kind, schema_root or api.REPO_ROOT)
    if value["capability_id"] != capability_id or value["record_id"] != record_id:
        raise ContractError("Lifecycle record path and identity disagree.")
    validate_identity(value["identity"])
    if value["identity"]["capability_id"] != capability_id:
        raise ContractError("Nested identity belongs to another capability.")
    if kind == "receipt":
        before = value["before"]
        for field, choices in (("management_state", api.MANAGEMENT_STATES), ("health_state", api.HEALTH_STATES),
                               ("deployment_scope", api.DEPLOYMENT_SCOPES), ("invocation", api.INVOCATION_STATES)):
            if before[field] not in choices:
                raise ContractError("Receipt contains an invalid prior state.")
        state, invocation = before["management_state"], before["invocation"]
        if (state == "active" and (before["health_state"] != "healthy" or before["deployment_scope"] == "not-installed" or invocation == "disabled")
                or state == "reference" and before["deployment_scope"] != "not-installed"
                or state in {"candidate", "cold", "reference"} and invocation != "explicit-only"
                or state in {"disabled", "retired", "quarantine"} and invocation != "disabled"
                or invocation == "auto" and state != "active"):
            raise ContractError("Receipt contains an invalid prior state combination.")
        complete = value["validation"] != "pending" and value["settlement"] == "complete"
        if (value["status"] == "completed") != complete:
            raise ContractError("Receipt status and settlement disagree.")
        if complete:
            if not value["summary"].strip() or not value["ended_at"] or not value["end_identity_sha256"]:
                raise ContractError("Completed receipt requires evidence, time and end identity.")
            if timestamp(value["ended_at"]) < timestamp(value["started_at"]):
                raise ContractError("Receipt ends before it starts.")
        elif value["ended_at"]:
            raise ContractError("Pending receipt cannot have an end timestamp.")
        if value["validation"] == "pending" and value["settlement"] == "complete":
            raise ContractError("Pending validation cannot be completely settled.")
    else:
        if not value["summary"].strip():
            raise ContractError("Evidence summary must not be blank.")
        if (value["kind"] == "task") != bool(value["run_id"]):
            raise ContractError("Task evidence must reference exactly one use receipt.")
        expected_source = "caller-reported-use-receipt" if value["kind"] == "task" else "caller-reported-check"
        if value["source"] != expected_source or (value["kind"] != "task" and not value["identity_matches"]):
            raise ContractError("Evidence kind and source disagree.")


def records(api, root: Path, capability_id: str, folder: str, schema_root: Path | None = None) -> list[dict]:
    directory = beneath(root, f"{STORE}/{safe_id(capability_id)}/{folder}")
    result = []
    if not directory.exists():
        return result
    for path in sorted(directory.glob("*.json")):
        path = beneath(root, path.relative_to(root).as_posix())
        value = read_json(api, path)
        validate_record(api, value, "receipt" if folder == "runs" else "evidence", capability_id, path.stem, schema_root)
        result.append(value)
    return result


def validate_links(runs: list[dict], evidence: list[dict]) -> None:
    by_run = {run["record_id"]: run for run in runs}
    by_evidence = {item["record_id"]: item for item in evidence}
    for item in evidence:
        if item["kind"] != "task":
            continue
        run = by_run.get(item["run_id"])
        if not run or run["status"] != "completed":
            raise ContractError("Task evidence lacks a completed receipt.")
        expected = task_evidence(run)
        if item != expected:
            raise ContractError("Task evidence disagrees with its receipt.")
    for run in runs:
        if run["status"] == "completed" and by_evidence.get("task-" + run["record_id"]) != task_evidence(run):
            raise ContractError("Completed receipt lacks its matching evidence.")


def validate_store(api, root: Path, capability_ids: set[str], schema_root: Path | None = None) -> list[str]:
    errors = []
    directory = beneath(root, STORE)
    if not directory.exists():
        return errors
    for entry in directory.iterdir():
        if entry.name == "hook-cache":
            continue  # Disposable deduplication data, not evidence.
        try:
            if not entry.is_dir() or entry.name not in capability_ids:
                raise ContractError("Lifecycle directory has no canonical capability.")
            if any(child.name not in {"runs", "evidence"} or not child.is_dir() for child in entry.iterdir()):
                raise ContractError("Unexpected lifecycle entry; preserve it for review.")
            runs = records(api, root, entry.name, "runs", schema_root)
            evidence = records(api, root, entry.name, "evidence", schema_root)
            validate_links(runs, evidence)
        except (ValueError, OSError) as exc:
            errors.append(f"Lifecycle {entry.name}: {exc}")
    return errors


def context(api, args):
    root = Path(args.root).resolve()
    config = api.load_config(root)
    paths = api.resolve_paths(root, config)
    safe_id(args.id)
    target, manifest, _ = api.locate_record(paths["capability_records"], args.id, "capability")
    errors = api.validate_capability(manifest, target, {category["id"] for category in config["route_categories"]})
    if errors:
        raise ContractError("Invalid canonical capability: " + "; ".join(errors))
    if getattr(args, "mutates", False):
        validate_links(records(api, root, args.id, "runs"), records(api, root, args.id, "evidence"))
    return root, manifest


def write(api, root: Path, action: str, changes: list[tuple[Path, dict]]) -> None:
    transaction = api.Transaction(root, action)
    for path, value in changes:
        transaction.add(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    transaction.commit()


def task_evidence(run: dict) -> dict:
    return {"schema_version": 1, "record_type": "capability-evidence", "record_id": "task-" + run["record_id"],
            "capability_id": run["capability_id"], "project_key": run["project_key"], "identity": run["identity"],
            "kind": "task", "result": run["validation"], "observed_at": run["ended_at"],
            "summary": run["summary"], "run_id": run["record_id"],
            "identity_matches": run["identity"]["sha256"] == run["end_identity_sha256"],
            "source": "caller-reported-use-receipt"}


def begin(api, args) -> dict:
    root, manifest = context(api, args)
    current = identity(api, args)
    run_id = safe_id(args.request_id)
    if len(run_id) > 80:
        raise ContractError("Use request IDs of at most 80 characters; task evidence adds a prefix.")
    path = store_path(root, args.id, "runs", run_id)
    signature = {"identity": current, "session_id": args.session_id, "turn_id": args.turn_id,
                 "project_key": project_key(root)}
    if path.exists():
        existing = read_json(api, path)
        validate_record(api, existing, "receipt", args.id, run_id)
        if any(existing[key] != item for key, item in signature.items()):
            raise ContractError("Request ID was already used with a different context or identity.")
        return {"action": "use-begin", "result": "already_recorded", "run_id": run_id,
                "status": existing["status"], "authorized_execution": False}
    value = {"schema_version": 1, "record_type": "capability-use", "record_id": run_id, "capability_id": args.id,
             **signature, "before": {key: manifest[key] for key in STATE_FIELDS}, "started_at": utc(),
             "status": "pending", "validation": "pending", "settlement": "pending", "summary": "",
             "ended_at": "", "end_identity_sha256": ""}
    validate_record(api, value, "receipt", args.id, run_id)
    write(api, root, "use-begin", [(path, value)])
    return {"action": "use-begin", "result": "recorded", "run_id": run_id, "status": "pending", "authorized_execution": False}


def finish(api, args) -> dict:
    root, _ = context(api, args)
    run_id = safe_id(args.run_id)
    path = store_path(root, args.id, "runs", run_id)
    value = read_json(api, path)
    validate_record(api, value, "receipt", args.id, run_id)
    if value["project_key"] != project_key(root) or value["session_id"] != args.session_id or value["turn_id"] != args.turn_id:
        raise ContractError("Receipt is outside this project/session/turn.")
    outcome = {"validation": args.validation, "settlement": args.settlement, "summary": args.evidence.strip()}
    if not outcome["summary"]:
        raise ContractError("Provide a concise evidence summary.")
    if value["status"] == "completed":
        if any(value[key] != item for key, item in outcome.items()):
            raise ContractError("Completed receipt cannot be overwritten with a different outcome.")
        validate_links([value], [read_json(api, store_path(root, args.id, "evidence", "task-" + run_id))])
        return {"action": "use-finish", "result": "already_recorded", "run_id": run_id}
    current = identity(api, args)
    complete = args.validation != "pending" and args.settlement == "complete"
    value.update(outcome, status="completed" if complete else "pending", ended_at=utc() if complete else "",
                 end_identity_sha256=current["sha256"])
    validate_record(api, value, "receipt", args.id, run_id)
    changes = [(path, value)]
    if complete:
        evidence = task_evidence(value)
        changes.append((store_path(root, args.id, "evidence", evidence["record_id"]), evidence))
    write(api, root, "use-finish", changes)
    return {"action": "use-finish", "result": value["status"], "run_id": run_id,
            "identity_matches": current["sha256"] == value["identity"]["sha256"], "governance_changed": False}


def record_evidence(api, args) -> dict:
    root, _ = context(api, args)
    current = identity(api, args)
    record_id = safe_id(args.request_id)
    if record_id.startswith("task-"):
        raise ContractError("The task- prefix is reserved for completed use receipts.")
    path = store_path(root, args.id, "evidence", record_id)
    value = {"schema_version": 1, "record_type": "capability-evidence", "record_id": record_id,
             "capability_id": args.id, "project_key": project_key(root), "identity": current, "kind": args.kind,
             "result": args.result, "summary": args.evidence.strip(), "run_id": "", "identity_matches": True,
             "source": "caller-reported-check", "observed_at": utc()}
    validate_record(api, value, "evidence", args.id, record_id)
    if path.exists():
        existing = read_json(api, path)
        validate_record(api, existing, "evidence", args.id, record_id)
        value["observed_at"] = existing["observed_at"]
        if value != existing:
            raise ContractError("Evidence request ID is immutable; use a new ID for a new check.")
        return {"action": "record-evidence", "result": "already_recorded", "record_id": record_id}
    write(api, root, "record-evidence", [(path, value)])
    return {"action": "record-evidence", "result": "recorded", "record_id": record_id}


def _check_capability(api, args) -> dict:
    root, manifest = context(api, args)
    if not 1 <= args.max_age_days <= 365:
        raise ContractError("max-age-days must be between 1 and 365.")
    current = identity(api, args)
    runs = records(api, root, args.id, "runs")
    evidence = records(api, root, args.id, "evidence")
    validate_links(runs, evidence)
    now = timestamp(utc())
    scoped = [item for item in evidence if item["project_key"] == project_key(root)]
    matching = [item for item in scoped if item["identity"]["sha256"] == current["sha256"]]
    required_kinds = {"task"} if args.require == "task" else {"smoke", "task"}
    eligible = [item for item in matching if item["kind"] in required_kinds]
    reasons = []
    if any(entry["sha256"] == "absent" for entry in current["files"]):
        reasons.append("artifact_missing")
    if any(timestamp(item["observed_at"]) > now for item in matching):
        reasons.append("future_evidence")
    selected = max(eligible, key=lambda item: (timestamp(item["observed_at"]), item["result"] != "passed", item["record_id"]), default=None)
    if not selected:
        reasons.append("identity_changed" if scoped and not matching else "no_required_evidence")
    else:
        if now - timestamp(selected["observed_at"]) > timedelta(days=args.max_age_days):
            reasons.append("evidence_expired")
        if selected["result"] != "passed":
            reasons.append("validation_not_passed")
        if not selected["identity_matches"]:
            reasons.append("identity_changed_during_use")
        if any(item["result"] != "passed" and timestamp(item["observed_at"]) >= timestamp(selected["observed_at"]) for item in matching):
            reasons.append("newer_negative_evidence")
    pending = [run for run in runs if run["project_key"] == project_key(root) and run["status"] == "pending"]
    if pending:
        reasons.append("unsettled_use")
    evidence_ok = not reasons
    governance_ok = manifest["management_state"] == "active" and manifest["health_state"] == "healthy" and manifest["invocation"] != "disabled"
    return {"action": "capability-check", "result": "pass" if evidence_ok else "needs_review",
            "ledger": "consistent", "identity_sha256": current["sha256"], "evidence_usable": evidence_ok,
            "evidence_id": selected["record_id"] if selected else None, "required_scope": args.require,
            "reasons": sorted(set(reasons)), "pending_runs": [run["record_id"] for run in pending],
            "recorded_health": manifest["health_state"], "governance_allows_active": governance_ok,
            "authorized_execution": False, "_exit_code": 0 if evidence_ok else 1}


def check_capability(api, args) -> dict:
    root = Path(args.root).resolve()
    lock = beneath(root, ".workflow/lock")
    directory = beneath(root, f"{STORE}/{safe_id(args.id)}")
    def names():
        return {str(path) for folder in ("runs", "evidence") for path in (directory / folder).glob("*.json")}
    if lock.exists():
        raise ContractError("A writer is active; retry the read-only check after it finishes.")
    initial_names = names()
    token = api.OBSERVED_READS.set({})
    try:
        result = _check_capability(api, args)
        if lock.exists() or names() != initial_names or any(api.file_hash(path) != checksum for path, checksum in api.OBSERVED_READS.get().items()):
            raise ContractError("Inputs changed during the read-only check; retry.")
        return result
    finally:
        api.OBSERVED_READS.reset(token)


def pending_uses(api, root: Path, session_id: str | None = None, limit: int | None = None) -> list[dict]:
    """Return scope-bound unfinished work; never inspect transcripts or run tools."""
    api.load_config(root)
    directory = beneath(root, STORE)
    result = []
    for count, path in enumerate(directory.glob("*/runs/*.json"), 1):
        if limit is not None and count > limit:
            raise ContractError("Hook scan limit exceeded; use lifecycle-status explicitly.")
        path = beneath(root, path.relative_to(root).as_posix())
        capability_id = path.parent.parent.name
        value = read_json(api, path)
        validate_record(api, value, "receipt", capability_id, path.stem)
        if value["project_key"] == project_key(root) and value["status"] == "pending" and (session_id is None or value["session_id"] == session_id):
            result.append({"capability_id": capability_id, "run_id": value["record_id"],
                           "session_id": value["session_id"], "turn_id": value["turn_id"]})
    return sorted(result, key=lambda item: (item["capability_id"], item["run_id"]))


def register(sub, api) -> None:
    status = sub.add_parser("lifecycle-status", help="Read pending uses for recovery; no artifact access or mutation.")
    status.add_argument("--root", required=True)
    status.add_argument("--session-id")
    status.set_defaults(mutates=False, handler=lambda args: {"action": "lifecycle-status", "pending": pending_uses(api, Path(args.root).resolve(), args.session_id)})
    commands = (("use-begin", begin, True), ("use-finish", finish, True),
                ("record-evidence", record_evidence, True), ("capability-check", check_capability, False))
    for name, handler, mutates in commands:
        parser = sub.add_parser(name, help="Record/check identity-bound evidence; never execute or authorize a capability.")
        parser.add_argument("--root", required=True)
        parser.add_argument("--id", required=True)
        parser.add_argument("--identity-file", required=True)
        parser.add_argument("--artifact-root", required=True)
        parser.set_defaults(handler=lambda args, fn=handler: fn(api, args), mutates=mutates)
        if name in {"use-begin", "record-evidence"}:
            parser.add_argument("--request-id", required=True)
        if name in {"use-begin", "use-finish"}:
            parser.add_argument("--session-id", required=True)
            parser.add_argument("--turn-id", required=True)
        if name == "use-finish":
            parser.add_argument("--run-id", required=True)
            parser.add_argument("--validation", choices=("passed", "failed", "inconclusive", "pending"), required=True)
            parser.add_argument("--settlement", choices=("complete", "pending"), required=True)
            parser.add_argument("--evidence", required=True)
        if name == "record-evidence":
            parser.add_argument("--kind", choices=("discovery", "smoke"), required=True)
            parser.add_argument("--result", choices=("passed", "failed", "inconclusive"), required=True)
            parser.add_argument("--evidence", required=True)
        if name == "capability-check":
            parser.add_argument("--require", choices=("smoke", "task"), default="task")
            parser.add_argument("--max-age-days", type=int, default=30)
