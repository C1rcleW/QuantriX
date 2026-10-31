"""Golden snapshot helpers for behavior-freeze tests.

Regenerate snapshots intentionally with:

    UPDATE_GOLDEN=1 pytest tests/golden
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

SNAPSHOT_ROOT = Path(__file__).resolve().parent / "snapshots"
_UPDATE_ENV = "UPDATE_GOLDEN"


def to_jsonable(value: Any) -> Any:
    """Convert numpy/polars scalars and arrays into JSON-stable values."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [to_jsonable(item) for item in sorted(value, key=str)]
    if hasattr(value, "tolist"):
        return to_jsonable(value.tolist())
    if hasattr(value, "item"):
        return to_jsonable(value.item())
    return str(value)


def _normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _compare(expected: Any, actual: Any, path: str, diffs: list[str], limit: int) -> None:
    if len(diffs) >= limit:
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        if expected_keys != actual_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            diffs.append(f"{path}: keys differ; missing={missing}, extra={extra}")
        for key in sorted(expected_keys & actual_keys):
            _compare(expected[key], actual[key], f"{path}.{key}", diffs, limit)
        return
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            diffs.append(f"{path}: length {len(expected)} != {len(actual)}")
            return
        for index, (expected_item, actual_item) in enumerate(
            zip(expected, actual, strict=True)
        ):
            _compare(expected_item, actual_item, f"{path}[{index}]", diffs, limit)
        return
    if _is_number(expected) and _is_number(actual):
        if not math.isclose(
            float(expected), float(actual), rel_tol=1e-6, abs_tol=1e-9
        ):
            diffs.append(f"{path}: {expected!r} != {actual!r}")
        return
    if expected != actual:
        diffs.append(f"{path}: {expected!r} != {actual!r}")


def _load(filename: str) -> dict[str, Any]:
    path = SNAPSHOT_ROOT / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(filename: str, data: dict[str, Any]) -> None:
    path = SNAPSHOT_ROOT / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def assert_snapshot(actual: Any, filename: str, key: str) -> None:
    """Compare actual against a named golden entry, or update it if requested."""
    data = _load(filename)
    actual_json = to_jsonable(actual)
    if os.environ.get(_UPDATE_ENV) == "1":
        data[key] = actual_json
        _save(filename, data)
        return
    if key not in data:
        raise AssertionError(
            f"Missing golden key {key!r} in {filename}. "
            f"Run UPDATE_GOLDEN=1 pytest tests/golden to create it."
        )
    diffs: list[str] = []
    _compare(data[key], actual_json, key, diffs, limit=20)
    if diffs:
        raise AssertionError(
            f"Golden snapshot mismatch in {filename}:\n" + "\n".join(diffs)
        )


def assert_text_snapshot(text: str, filename: str, key: str) -> None:
    """Compare normalized text against a golden entry."""
    assert_snapshot(_normalize_text(text), filename, key)
