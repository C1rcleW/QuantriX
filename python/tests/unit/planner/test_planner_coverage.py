"""Coverage tests for the research planner's goal × variable-type matrix."""

import polars as pl
import pytest

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.planner.recommendation import ResearchPlanner
from quantrix.stats.registry import execute_analysis, get_registry

ROWS = 24


def _dataset() -> Dataset:
    data = {
        "cont_dv": [float(i) for i in range(ROWS)],
        "nom_dv": ["yes", "no"] * (ROWS // 2),
        "ord_dv": [1, 2, 3] * (ROWS // 3),
        "cont_iv": [float(i % 7) for i in range(ROWS)],
        "nom_iv": ["A", "B", "C"] * (ROWS // 3),
        "ord_iv": [1, 2, 3] * (ROWS // 3),
        "text_iv": [f"text_{i}" for i in range(ROWS)],
    }
    variables = [
        VariableMetadata(name="cont_dv", variable_type=VariableType.CONTINUOUS, n_valid=ROWS, n_unique=ROWS),
        VariableMetadata(name="nom_dv", variable_type=VariableType.NOMINAL, n_valid=ROWS, n_unique=2),
        VariableMetadata(name="ord_dv", variable_type=VariableType.ORDINAL, n_valid=ROWS, n_unique=3),
        VariableMetadata(name="cont_iv", variable_type=VariableType.CONTINUOUS, n_valid=ROWS, n_unique=7),
        VariableMetadata(name="nom_iv", variable_type=VariableType.NOMINAL, n_valid=ROWS, n_unique=3),
        VariableMetadata(name="ord_iv", variable_type=VariableType.ORDINAL, n_valid=ROWS, n_unique=3),
        VariableMetadata(name="text_iv", variable_type=VariableType.STRING, n_valid=ROWS, n_unique=ROWS),
    ]
    return Dataset(
        name="planner_matrix",
        n_rows=ROWS,
        n_columns=len(data),
        variables=variables,
        data=pl.DataFrame(data),
    )


DV_NAMES = ["cont_dv", "nom_dv", "ord_dv"]
IV_NAMES = ["cont_iv", "nom_iv", "ord_iv", "text_iv"]
GOALS = ["describe", "compare_groups", "find_association", "predict"]


@pytest.mark.parametrize("goal", GOALS)
@pytest.mark.parametrize("dv_name", DV_NAMES)
@pytest.mark.parametrize("iv_name", IV_NAMES)
def test_every_goal_and_type_combination_has_recommendation_or_note(
    goal, dv_name, iv_name
):
    planner = ResearchPlanner()
    ivs = [] if goal == "describe" else [iv_name]
    plan = planner.plan_structured(goal, dv_name, ivs, _dataset())

    assert plan["recommendations"] or plan["notes"]
    supported = set(get_registry())
    assert all(rec["method_name"] in supported for rec in plan["recommendations"])


def test_compare_with_continuous_grouping_variable_is_explained():
    plan = ResearchPlanner().plan_structured(
        "compare_groups", "cont_dv", ["cont_iv"], _dataset()
    )
    assert plan["recommendations"] == []
    assert any("categorical grouping" in note for note in plan["notes"])


def test_association_continuous_by_categorical_is_executable():
    plan = ResearchPlanner().plan_structured(
        "find_association", "cont_dv", ["nom_iv"], _dataset()
    )
    names = [rec["method_name"] for rec in plan["recommendations"]]
    assert "oneway_anova" in names
    assert any("Eta-Squared" in note for note in plan["notes"])


def test_association_nominal_by_continuous_is_explained():
    plan = ResearchPlanner().plan_structured(
        "find_association", "nom_dv", ["cont_iv"], _dataset()
    )
    assert plan["recommendations"] == []
    assert any("logistic" in note.lower() for note in plan["notes"])


def test_predict_nominal_outcome_is_explained():
    plan = ResearchPlanner().plan_structured(
        "predict", "nom_dv", ["cont_iv"], _dataset()
    )
    assert plan["recommendations"] == []
    assert any("logistic" in note.lower() for note in plan["notes"])


def test_predict_ordinal_outcome_is_explained():
    plan = ResearchPlanner().plan_structured(
        "predict", "ord_dv", ["cont_iv"], _dataset()
    )
    assert plan["recommendations"] == []
    assert any("ordinal" in note.lower() for note in plan["notes"])


def test_predict_continuous_outcome_with_nominal_predictor_is_executable():
    dataset = _dataset()
    plan = ResearchPlanner().plan_structured(
        "predict", "cont_dv", ["nom_iv"], dataset
    )
    assert plan["recommendations"]
    recommendation = plan["recommendations"][0]
    assert recommendation["method_name"] == "linear_regression"

    dv = dataset.get_variable("cont_dv")
    ivs = [dataset.get_variable(name) for name in recommendation["matched_variables"]["independents"]]
    result = execute_analysis(recommendation["method_name"], dataset, dv, ivs)
    assert result["errors"] == []


def test_predict_with_free_text_predictor_is_explained():
    plan = ResearchPlanner().plan_structured(
        "predict", "cont_dv", ["text_iv"], _dataset()
    )
    assert plan["recommendations"] == []
    assert any("free text" in note.lower() for note in plan["notes"])
