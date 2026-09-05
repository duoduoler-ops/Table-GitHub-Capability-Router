#!/usr/bin/env python3
"""Optional bounded reminder adapter. Errors always fail open; never runs tools."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import workflow
from capability_lifecycle import beneath, digest, pending_uses, project_key, read_json, utc
from lifecycle_contract import ContractError


def normalize(payload: dict, host: str) -> dict:
    if not isinstance(payload, dict):
        raise ContractError("Expected a hook object.")
    if host == "grok-build":
        event = {"session_start": "SessionStart", "stop": "Stop"}.get(payload.get("hookEventName"))
        session, turn = payload.get("sessionId"), payload.get("promptId")
        active = payload.get("stopHookActive", False)
        if event == "Stop" and payload.get("reason") != "end_turn":
            event = None
    else:
        event = payload.get("hook_event_name")
        session, turn = payload.get("session_id"), payload.get("turn_id")
        active = payload.get("stop_hook_active", False)
    if event not in {"SessionStart", "Stop"}:
        raise ContractError("Unsupported hook event.")
    for value in (session, payload.get("cwd")):
        if not isinstance(value, str) or not value.strip() or len(value) > 1024:
            raise ContractError("Missing hook scope.")
    if turn is not None and (not isinstance(turn, str) or not turn.strip() or len(turn) > 160):
        raise ContractError("Invalid turn ID.")
    if type(active) is not bool:
        raise ContractError("Invalid stop guard.")
    return {"event": event, "session": session, "turn": turn, "cwd": payload["cwd"], "active": active}


def handle(root: Path, host: str, payload: dict, grok_feedback: bool = False) -> dict | None:
    event = normalize(payload, host)
    if Path(event["cwd"]).resolve() != root or event["active"]:
        return None
    workflow.load_config(root)
    beneath(root, ".workflow/lock")  # Reject escaping state directories before acquiring a lock.
    with workflow.workflow_lock(root):
        pending = pending_uses(workflow, root, event["session"] if event["event"] == "Stop" else None, limit=256)
        if not pending:
            return None
        # Stop includes earlier unfinished turns in this session, not other sessions.
        key = digest([project_key(root), host, event["session"], event["event"], event["turn"] or "session"])
        cache = beneath(root, f".workflow/lifecycle/hook-cache/{key}.json")
        if cache.exists():
            # Corrupted caches do not cause a repeat warning or automatic overwrite.
            state = read_json(workflow, cache)
            if state.get("key") != key:
                raise ContractError("Hook cache is invalid.")
            return None
        notice = f"Capability lifecycle: {len(pending)} unfinished use record(s). Run lifecycle-status and review validation/settlement before reusing evidence."
        state = {"schema_version": 1, "key": key, "created_at": utc(), "pending": pending,
                 "notice": notice, "delivery": "file" if host == "grok-build" and (event["event"] == "SessionStart" or not grok_feedback) else "stdout"}
        workflow.atomic_write(cache, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        if host == "grok-build":
            # Passive Grok stdout is ignored. A Stop feedback opt-in requests one continuation.
            if event["event"] == "Stop" and grok_feedback:
                return {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": notice}}
            return None
        if event["event"] == "SessionStart":
            return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": notice}}
        return {"systemMessage": notice}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--host", choices=("generic-agent", "codex", "grok-build"), required=True)
    parser.add_argument("--grok-feedback", action="store_true", help="Opt in to one Grok Stop continuation; can consume model usage.")
    try:
        args = parser.parse_args(argv)
        # Native hosts send UTF-8 JSON, regardless of the Windows Python locale.
        raw = getattr(sys.stdin, "buffer", sys.stdin).read(65537)
        if len(raw) > 65536:
            return 0
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig")
        value = handle(Path(args.root).resolve(), args.host, json.loads(raw), args.grok_feedback)
        if value:
            print(json.dumps(value, ensure_ascii=False))
    except (Exception, SystemExit):
        # Never log event payloads (they may include user text); explicit CLI checks report errors.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
