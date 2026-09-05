"""Small validator for the explicitly supported lifecycle JSON Schema vocabulary.

Schema defines field types/enums; cross-record and lifecycle rules live in the core.
This is deliberately not a general-purpose JSON Schema implementation.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


class ContractError(ValueError):
    pass


def timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value):
        raise ContractError("Expected an explicit UTC timestamp.")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check(value, schema: dict, document: dict, location: str = "record") -> None:
    supported = {"$schema", "$id", "$defs", "$ref", "title", "description", "type", "required",
                 "properties", "additionalProperties", "const", "enum", "pattern", "format",
                 "minLength", "maxLength", "minItems", "maxItems", "uniqueItems", "items"}
    if set(schema) - supported:
        raise ContractError("Unsupported lifecycle schema keyword.")
    if "$ref" in schema:
        prefix = "#/$defs/"
        ref = schema["$ref"]
        if not ref.startswith(prefix) or ref[len(prefix):] not in document["$defs"]:
            raise ContractError("Only local lifecycle schema references are supported.")
        check(value, document["$defs"][ref[len(prefix):]], document, location)
        return
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    if "type" in schema and type(value) is not types[schema["type"]]:
        raise ContractError(f"{location}: wrong type")
    if "const" in schema and value != schema["const"]:
        raise ContractError(f"{location}: wrong constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{location}: invalid enum")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        if set(schema.get("required", [])) - set(value):
            raise ContractError(f"{location}: missing required fields")
        if schema.get("additionalProperties") is False and set(value) - set(props):
            raise ContractError(f"{location}: unexpected fields")
        for key, item in value.items():
            if key in props:
                check(item, props[key], document, f"{location}.{key}")
    if isinstance(value, str):
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 100000):
            raise ContractError(f"{location}: invalid length")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ContractError(f"{location}: invalid format")
        if schema.get("format") == "date-time":
            timestamp(value)
    if isinstance(value, list):
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 100000):
            raise ContractError(f"{location}: invalid item count")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            raise ContractError(f"{location}: duplicate items")
        for item in value:
            check(item, schema.get("items", {}), document, location + "[]")


def validate(value, kind: str, schema_root: Path) -> None:
    document = json.loads((schema_root / "schemas/lifecycle.schema.json").read_text(encoding="utf-8"))
    check(value, document["$defs"][kind], document, kind)
