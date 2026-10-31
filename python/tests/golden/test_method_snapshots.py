"""Golden snapshots for every registered statistical method."""

from __future__ import annotations

import pytest

from quantrix.stats.registry import execute_analysis, get_registry
from tests.golden._snapshot import assert_snapshot
from tests.golden.data import METHOD_CASES, MethodCase, make_dataset


def _canonicalize(case: MethodCase, result: dict) -> dict:
    """Remove order that is semantically irrelevant from crosstab output."""
    if case.method != "chi_square" or not result.get("tables"):
        return result

    table = result["tables"][0]
    columns = table.get("columns", [])
    if columns:
        ordered = [columns[0], *sorted(columns[1:])]
        positions = {column: index for index, column in enumerate(columns)}
        table["columns"] = ordered
        table["rows"] = sorted(
            (
                [row[0], *[row[positions[column]] for column in ordered[1:]]]
                for row in table.get("rows", [])
            ),
            key=lambda row: str(row[0]),
        )
    for chart in result.get("charts", []):
        if chart.get("chart_type") == "bar":
            chart["data"] = sorted(
                chart.get("data", []), key=lambda item: str(item.get("name", ""))
            )
    return result


def test_method_cases_cover_all_registered_methods() -> None:
    assert {case.method for case in METHOD_CASES} == set(get_registry())


@pytest.mark.parametrize("case", METHOD_CASES, ids=lambda case: case.name)
def test_method_snapshot(case) -> None:
    dataset = make_dataset()
    result = execute_analysis(
        case.method,
        dataset,
        dataset.get_variable(case.dv),
        [dataset.get_variable(name) for name in case.ivs],
    )
    assert result["errors"] == []
    assert_snapshot(_canonicalize(case, result), "methods.json", case.name)
