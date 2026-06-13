"""Local JSON store for student and assignment seed data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_json(filename: str) -> list[dict[str, Any]]:
    path = _DATA_DIR / filename
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"{filename} must contain a JSON array")
    return payload


def list_students() -> list[dict[str, Any]]:
    return _load_json("students.seed.json")


def list_assignments() -> list[dict[str, Any]]:
    return _load_json("assignments.seed.json")


def boot_status() -> str:
    students = list_students()
    assignments = list_assignments()
    return (
        f"ok: source=local path=\"data/students.seed.json\" "
        f"students={len(students)} assignments={len(assignments)}"
    )
