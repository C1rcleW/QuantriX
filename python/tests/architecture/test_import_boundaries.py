"""Stage 0 architecture ratchet: known edges are allowed, new ones fail.

The allowlist records the coupling that Stage 1/2 will remove. When an edge is
fixed, delete it here; the stale-allowlist test will fail until you do.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "quantrix"

LAYERS = {
    "core",
    "data",
    "stats",
    "safety",
    "planner",
    "interpreter",
    "report",
    "dag",
    "viz",
    "server",
}

# Higher layers may import these lower layers. server is the composition edge.
ALLOWED_IMPORTS: dict[str, set[str]] = {
    "core": {"core"},
    "data": {"core", "data"},
    "safety": {"core", "safety"},
    "stats": {"core", "stats"},
    "planner": {"core", "planner"},
    "interpreter": {"core", "interpreter"},
    "report": {"core", "report"},
    "dag": {"core", "dag"},
    "viz": {"core", "viz"},
    "server": set(LAYERS),
}

# Current violations, frozen for Stage 0. Remove entries after Stage 1/2.
KNOWN_VIOLATIONS = {
    ("quantrix.stats.descriptive", "quantrix.viz"),
    ("quantrix.stats.comparison", "quantrix.viz"),
    ("quantrix.stats.correlation", "quantrix.viz"),
    ("quantrix.stats.regression", "quantrix.viz"),
    ("quantrix.planner.recommendation", "quantrix.stats.registry"),
}


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return "quantrix" + ("." + ".".join(parts) if parts else "")


def _layer(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) < 2:
        return None
    return parts[1] if parts[1] in LAYERS else "unknown"


def _imports(path: Path) -> Iterator[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                yield "<relative>"
                continue
            if node.module and (
                node.module == "quantrix" or node.module.startswith("quantrix.")
            ):
                yield node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "quantrix" or alias.name.startswith("quantrix."):
                    yield alias.name


def _edges() -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for path in ROOT.rglob("*.py"):
        source = _module_name(path)
        for target in _imports(path):
            if target != source:
                edges.add((source, target))
    return edges


def test_no_new_cross_layer_import_violations() -> None:
    violations: list[str] = []
    for source, target in sorted(_edges()):
        source_layer = _layer(source)
        target_layer = _layer(target)
        if source_layer is None:
            continue
        if target == "<relative>":
            violations.append(f"{source} uses a relative import")
            continue
        if target_layer is None or target_layer == "unknown":
            violations.append(f"{source} imports unclassified module {target}")
            continue
        if source_layer == target_layer:
            continue
        if target_layer in ALLOWED_IMPORTS.get(source_layer, set()):
            continue
        if (source, target) in KNOWN_VIOLATIONS:
            continue
        violations.append(f"{source} -> {target} ({source_layer} -> {target_layer})")
    assert not violations, "New architecture violations:\n" + "\n".join(violations)


def test_known_violations_are_not_stale() -> None:
    observed = _edges()
    stale = sorted(KNOWN_VIOLATIONS - observed)
    assert not stale, (
        "These allowlisted violations no longer exist; remove them from "
        f"KNOWN_VIOLATIONS: {stale}"
    )


def test_all_top_level_packages_are_classified() -> None:
    packages = {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }
    assert packages == LAYERS, (
        f"Classify new top-level packages in LAYERS: {packages - LAYERS}"
    )


if __name__ == "__main__":
    pytest.main([__file__])
