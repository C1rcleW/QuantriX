"""Contract tests for interpretation templates.

Every registered method must be able to render an interpretation from its
own StatResult without surfacing a template error.
"""

import pytest

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.interpreter.engine import ResultInterpreter
from quantrix.stats.registry import execute_analysis


def _make_dataset() -> Dataset:
    x = [float(v) for v in range(1, 19)]
    y = [2.0 * v + (0.5 if i % 2 else -0.5) for i, v in enumerate(x)]
    groups_2 = ["A"] * 9 + ["B"] * 9
    groups_3 = ["A"] * 6 + ["B"] * 6 + ["C"] * 6
    categories = ["P", "Q"] * 9
    variables = [
        VariableMetadata(name="x", variable_type=VariableType.CONTINUOUS, n_valid=18, n_unique=18),
        VariableMetadata(name="y", variable_type=VariableType.CONTINUOUS, n_valid=18, n_unique=18),
        VariableMetadata(name="g2", variable_type=VariableType.NOMINAL, n_valid=18, n_unique=2),
        VariableMetadata(name="g3", variable_type=VariableType.NOMINAL, n_valid=18, n_unique=3),
        VariableMetadata(name="cat", variable_type=VariableType.NOMINAL, n_valid=18, n_unique=2),
    ]
    import polars as pl

    df = pl.DataFrame(
        {"x": x, "y": y, "g2": groups_2, "g3": groups_3, "cat": categories}
    )
    return Dataset(name="template_contract", n_rows=18, n_columns=5, variables=variables, data=df)


def _stats_for(result: dict) -> dict:
    stats = {
        "dv_label": result.get("dv_label", ""),
        "iv_label": result.get("iv_label", ""),
    }
    stats.update(result.get("statistics") or {})
    effect_sizes = result.get("effect_sizes") or {}
    for key in ("cohens_d", "r", "rho", "r_squared", "eta_squared"):
        if key in effect_sizes:
            stats[key] = effect_sizes[key]
    if result.get("group_labels"):
        stats["group_labels"] = result["group_labels"]
    stats.update(result.get("misc") or {})
    if result.get("sig_text"):
        stats["sig_text"] = result["sig_text"]
    if result.get("effect_size_text"):
        stats["effect_size_text"] = result["effect_size_text"]
    return stats


CASES = [
    ("frequencies", "cat", [], "Frequency"),
    ("descriptives", "x", [], "Descriptive"),
    ("independent_ttest", "x", ["g2"], "t-test"),
    ("oneway_anova", "x", ["g3"], "ANOVA"),
    ("mann_whitney", "x", ["g2"], "Mann-Whitney"),
    ("kruskal_wallis", "x", ["g3"], "Kruskal-Wallis"),
    ("pearson_correlation", "y", ["x"], "Pearson"),
    ("spearman_correlation", "y", ["x"], "Spearman"),
    ("chi_square", "cat", ["g2"], "Chi-Square"),
    ("linear_regression", "y", ["x"], "Regression"),
]


@pytest.mark.parametrize(("method", "dv_name", "iv_names", "expected_text"), CASES)
def test_every_template_renders_from_real_result(method, dv_name, iv_names, expected_text):
    dataset = _make_dataset()
    dv = dataset.get_variable(dv_name)
    ivs = [dataset.get_variable(name) for name in iv_names]

    result = execute_analysis(method, dataset, dv, ivs)
    assert result["errors"] == []

    interpretation = ResultInterpreter().interpret(method, _stats_for(result))
    assert interpretation.summary
    assert interpretation.detailed
    assert "Template error" not in interpretation.detailed
    assert expected_text in interpretation.detailed


def test_frequency_template_includes_mode_percentage():
    dataset = _make_dataset()
    result = execute_analysis(
        "frequencies", dataset, dataset.get_variable("cat"), []
    )
    interpretation = ResultInterpreter().interpret("frequencies", _stats_for(result))
    assert "%" in interpretation.detailed


def test_interpretation_survives_none_and_nan_values():
    interpreter = ResultInterpreter()
    stats = {
        "dv_label": "score",
        "iv_label": "group",
        "group_labels": ["A", "B"],
        "means": [1.0, None],
        "sds": [None, 1.29],
        "ns": [1, 4],
        "p_value": float("nan"),
        "cohens_d": float("nan"),
        "sig_text": "p = nan",
        "effect_size_text": "",
    }

    interpretation = interpreter.interpret("independent_ttest", stats)
    assert interpretation.summary
    assert interpretation.detailed
    assert "Template error" not in interpretation.detailed
    assert "large effect" not in interpretation.summary
