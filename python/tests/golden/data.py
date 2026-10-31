"""Deterministic data and method cases shared by golden tests."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType

ROWS = 24


@dataclass(frozen=True)
class MethodCase:
    name: str
    method: str
    dv: str
    ivs: tuple[str, ...]


METHOD_CASES: tuple[MethodCase, ...] = (
    MethodCase("frequencies", "frequencies", "cat", ()),
    MethodCase("descriptives", "descriptives", "x", ()),
    MethodCase("independent_ttest", "independent_ttest", "x", ("g2",)),
    MethodCase("oneway_anova", "oneway_anova", "x", ("g3",)),
    MethodCase("mann_whitney", "mann_whitney", "x", ("g2",)),
    MethodCase("kruskal_wallis", "kruskal_wallis", "x", ("g3",)),
    MethodCase("pearson_correlation", "pearson_correlation", "y", ("x",)),
    MethodCase("spearman_correlation", "spearman_correlation", "y", ("x",)),
    MethodCase("chi_square", "chi_square", "cat", ("g2",)),
    MethodCase("linear_regression", "linear_regression", "y", ("x",)),
    MethodCase("linear_regression_categorical", "linear_regression", "y", ("g2",)),
    MethodCase("linear_regression_multi", "linear_regression", "y", ("x", "x2")),
    MethodCase("linear_regression_mixed", "linear_regression", "y", ("g2", "x")),
)


def make_dataset() -> Dataset:
    """Well-conditioned deterministic dataset for all 10 methods."""
    x = [float(value) for value in range(1, ROWS + 1)]
    x2 = [float((index * 7) % 13 + 1) for index in range(ROWS)]
    y = [
        2.0 * x[index] + 0.3 * x2[index] + ((index % 3) - 1) * 0.75
        for index in range(ROWS)
    ]
    g2 = ["A"] * 12 + ["B"] * 12
    g3 = ["A", "B", "C"] * 8
    cat = ["P"] * 10 + ["Q"] * 2 + ["P"] * 4 + ["Q"] * 8

    variables = [
        VariableMetadata(
            name="x",
            variable_type=VariableType.CONTINUOUS,
            n_valid=ROWS,
            n_unique=ROWS,
        ),
        VariableMetadata(
            name="x2",
            variable_type=VariableType.CONTINUOUS,
            n_valid=ROWS,
            n_unique=len(set(x2)),
        ),
        VariableMetadata(
            name="y",
            variable_type=VariableType.CONTINUOUS,
            n_valid=ROWS,
            n_unique=ROWS,
        ),
        VariableMetadata(
            name="g2",
            variable_type=VariableType.NOMINAL,
            n_valid=ROWS,
            n_unique=2,
        ),
        VariableMetadata(
            name="g3",
            variable_type=VariableType.NOMINAL,
            n_valid=ROWS,
            n_unique=3,
        ),
        VariableMetadata(
            name="cat",
            variable_type=VariableType.NOMINAL,
            n_valid=ROWS,
            n_unique=2,
        ),
    ]
    data = pl.DataFrame(
        {"x": x, "x2": x2, "y": y, "g2": g2, "g3": g3, "cat": cat}
    )
    return Dataset(
        name="golden",
        n_rows=ROWS,
        n_columns=len(data.columns),
        variables=variables,
        data=data,
    )


def make_small_group_dataset() -> Dataset:
    """Five cases with one single-observation group; safety must block it."""
    data = pl.DataFrame(
        {
            "score": [1.0, 2.0, 3.0, 4.0, 5.0],
            "group": ["A", "B", "B", "B", "B"],
        }
    )
    variables = [
        VariableMetadata(
            name="score",
            variable_type=VariableType.CONTINUOUS,
            n_valid=5,
            n_unique=5,
        ),
        VariableMetadata(
            name="group",
            variable_type=VariableType.NOMINAL,
            n_valid=5,
            n_unique=2,
        ),
    ]
    return Dataset(
        name="small_group",
        n_rows=5,
        n_columns=2,
        variables=variables,
        data=data,
    )
